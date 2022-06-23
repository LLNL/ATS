#ATS:flux00             SELF FluxScheduled 3

"""
This module defines the ``FluxScheduled`` class.
Allocation and flux session managed by `atsflux`. See /bin/atsflux.py for more details.

Author: William Hobbs
        <hobbs17@llnl.gov>

"""

import time
from math import ceil

import flux
import flux.job

from ats import terminal
from ats.tests import AtsTest
from ats.atsMachines import lcMachines

class FluxScheduled(lcMachines.LCMachineCore):
    """
    A class to initialize Flux if necessary and return job statements
    from ATS tests.
    """

    def init(self):
        """
        Sets ceiling on number of nodes and cores in the allocation.
        Defines a persistent handle to use to connect to the broker.
        """
        # import pdb
        # pdb.set_trace()
        self.fluxHandle = flux.Flux()
        self.numNodes = int(flux.resource.list.resource_list(self.fluxHandle).get().up.nnodes)
        self.maxCores = int(flux.resource.list.resource_list(self.fluxHandle).get().up.ncores)
        self.coresPerNode = self.maxCores // self.numNodes
        self.numberTestsRunningMax = self.maxCores

    def examineOptions(self, options):
        """
        Optparse (soon argparse) parameters from command-line options
        for ATS users. Needed for functionality with .ats files.
        
        :param options: The options available to a user in test.ats files.
        """
        self.exclusive = options.exclusive
        self.timelimit = options.timelimit

    def calculateCommandList(self, test):
        """
        Generates a list of commands to run a test in ATS on a 
        flux instance.
        
        :param test: the test to be run, of type ATSTest. Defined in /ats/tests.py.
        """
        ret = "flux mini run".split()
        np = test.options.get('np', 1)
        nn = test.options.get('nn', 1)

        # David/Shawn: Time limit compatibility -- how do ATS users specify time limits?
        # with flux, you have to specify a number, and then m, s, or h, and only one can be specified
        max_time = test.options.get('timelimit', '29m')
        ret.append(f"-t{max_time}")

        if np > self.coresPerNode:
            nn = ceil(np / self.coresPerNode)
        if nn > 0:
            ret.append(f"-N{nn}")

        """Thread subscription interface. Flux does not oversubscribe cores by default."""
        nt = test.options.get('nt', 1)
        """
        In order to marry ATS's description of threading with Flux's understanding, Flux will
        request 1 core per thread
        """
        ret.append(f"-n{np}")
        ret.append(f"-c{nt}")

        """GPU scheduling interface"""
        ngpu = test.options.get('ngpu',0)
        if ngpu:
            ret.append(f"-g{ngpu}")

        """Node-exclusive job scheduling: even if a job does not use the entire resources."""
        if test.options.get('exclusive', False):
            ret.append("--exclusive")
        
        """Verbose mode, set to output to stdlog. Really outputs to logfile."""
        ret.append("-vvv")

        """Set job name. Follows convention for ATS in Slurm and LSF schedulers."""
        test.jobname = f"{np}_{test.serialNumber}{test.namebase[0:50]}{time.strftime('%H%M%S',time.localtime())}"
        ret.append("--job-name")
        ret.append(test.jobname)
        
        return ret + self.calculateBasicCommandList(test)
    
    def canRun(self, test):
        """
        Method required for integration with current ATS codebase.
        Usually, this would check if free resources are available to submit a job,
        however, that doesn't need to be considered when submitting a Flux job to the queue,
        so canRun is always true.

        :param test: Required for integration to overwrite method in parent class.
        """
        return ''
    
    def canRunNow(self, test):
        """
        See above. This is maintained for integration with the current ATS codebase.
        
        :param test: Required for integration to overwrite method in parent class.
        """
        return True

    def periodicReport(self):
        """
        Report on current status of tasks and processor availability.
        Utilizes Flux accessors for resource_list and flux job monitoring capabilities.
        """
        # TODO: reconcile ATS's notion of "running" with Flux
        # ATS says anything that it has submitted to the queue is "running" but with Flux
        # jobs that have been submitted to the queue may not have necessarily been allocated resources yet
        
        if self.running:
            terminal("CURRENTLY RUNNING %d tests:" % len(self.running),
                     " ".join([t.name for t in self.running]) )
        terminal("-"*80)

        ## Flux specific accessors for number of nodes
        resource_list = flux.resource.list.resource_list(self.fluxHandle).get()
        procs = resource_list.allocated.nnodes
        total = resource_list.up.nnodes
        terminal(f"CURRENTLY UTILIZING {procs} of {total} processors.")
        terminal("-"*80)
        
    def remainingCapacity(self):
        """Returns the number of free cores in the flux instance."""
        return flux.resource.list.resource_list(self.fluxHandle).get().free.ncores
