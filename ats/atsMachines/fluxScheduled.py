#ATS:flux00             SELF FluxScheduled 3

"""
This module defines the ``FluxScheduled`` class.
Allocation and flux session managed by `atsflux`. See /bin/atsflux.py for more details.

Author: William Hobbs
        <hobbs17@llnl.gov>

"""

import os
import time
from math import ceil

import flux
import flux.job
import multiprocessing


from ats import terminal
from ats.atsMachines import lcMachines
from ats.tests import AtsTest
from ats import configuration


class FluxScheduled(lcMachines.LCMachineCore):
    """
    A class to initialize Flux if necessary and return job statements
    from ATS tests.
    """

    debug = False
    debug_canRunNow = False
    debug_noteLaunch = False

    def init(self):
        """
        Sets ceiling on number of nodes and cores in the allocation.
        Defines a persistent handle to use to connect to the broker.
        """
        self.fluxHandle = flux.Flux()
        self.numNodes = int(
            flux.resource.list.resource_list(self.fluxHandle).get().up.nnodes
        )
        self.maxCores = int(
            flux.resource.list.resource_list(self.fluxHandle).get().up.ncores
        )
        self.numCores = int(
            flux.resource.list.resource_list(self.fluxHandle).get().up.ncores
        )
        self.numGPUs= int(
            flux.resource.list.resource_list(self.fluxHandle).get().up.ngpus
        )
        self.numberNodesExclusivelyUsed = 0

        # self.coresPerNode = self.maxCores // self.numNodes
        self.npMax  = multiprocessing.cpu_count()

        if "NP_MAX" in os.environ.keys():
            self.npMax = int(os.getenv("NP_MAX"))
            self.maxCores = self.npMax * self.numNodes

        self.npMaxH = self.npMax
        self.coresPerNode = self.npMax
        self.numberTestsRunningMax = self.maxCores
        self.numProcsAvailable = self.maxCores

        super(FluxScheduled, self).init()

    def kill(self, test):
        """
        Final cleanup if any. Not implemented for Flux yet.
        """

    def examineOptions(self, options):
        """
        Optparse (soon argparse) parameters from command-line options
        for ATS users. Needed for functionality with .ats files.

        :param options: The options available to a user in test.ats files.
        """
        self.exclusive = options.exclusive
        self.timelimit = options.timelimit
        self.toss_nn   = options.toss_nn


    def set_nt_num_nodes(self,test):

        # Command line option nt over-rides what is in the deck.
        test.nt = 1
        if configuration.options.ompNumThreads > 0:
            test.nt = configuration.options.ompNumThreads
        else:
            if 'nt' in test.options:
                test.nt = test.options.get('nt', 1)

        # cpus per task is related to num threads, but 
        # it is also meaningful for non threaded runs
        # where we want to reserve more than 1 core per mpi rank
        # So default it to 'nt' which was set above, but
        # allow it to be set separately as well. 
        test.cpus_per_task = test.nt
        if configuration.options.cpusPerTask > -1:
            test.cpus_per_task = configuration.options.cpusPerTask
        else:
            if 'cpus_per_task' in test.options:
                test.cpus_per_task = test.options.get('cpus_per_task', 1)

        # Command line option toss_nn over-rides what is in the deck.
        if (self.toss_nn < 0):
            test.num_nodes = test.options.get('nn', 0)
        else:
            test.num_nodes = self.toss_nn

    def calculateCommandList(self, test):
        """
        Generates a list of commands to run a test in ATS on a
        flux instance.

        :param test: the test to be run, of type ATSTest. Defined in /ats/tests.py.
        """
        ret = "flux mini run -o cpu-affinity=per-task -o mpibind=off".split()
        np = test.options.get("np", 1)

        FluxScheduled.set_nt_num_nodes(self, test)
        # nn = test.options.get("nn", 0)

        max_time = self.timelimit
        ret.append(f"-t{max_time}")

        #if np > self.coresPerNode:
        #    nn = ceil(np / self.coresPerNode)

        if test.num_nodes > 0:
            ret.append(f"-N{test.num_nodes}")
            """Node-exclusive job scheduling: even if a job does not use the entire resources."""
            """Requires use of -N. """
            if test.options.get("exclusive", True) or self.exclusive:
                ret.append("--exclusive")

        #"""Thread subscription - Flux does not oversubscribe cores by default."""
        #nt = test.options.get("nt", 1)
        #"""
        #In order to marry ATS's description of threading with Flux's understanding, Flux will
        #request 1 core per thread
        #"""
        ret.append(f"-n{np}")
        ret.append(f"-c{test.cpus_per_task}")

        """GPU scheduling interface"""
        ngpu = test.options.get("ngpu", 0)
        if ngpu:
            ret.append(f"-g{ngpu}")


        """
        CPU affinity enabled settings will go here. These are applicable 
        to an entire test run, not just to one test.
        """
        # ret.append('-o\"cpu-affinity=per-task\"')

        """Verbose mode, set to output to stdlog. Really outputs to logfile."""
        # ret.append("-vvv")

        """output option. """
        # ret.append("--output=flux-{{id}}.stdout")
        # ret.append("--output=none")
        # ret.append("--log=job{cc}.id")

        """error option. """
        # ret.append("--error=flux-{{id}}.stderr")
        # ret.append("--error=none")

        """Set job name. Follows convention for ATS in Slurm and LSF schedulers."""
        test.jobname = f"{np}_{test.serialNumber}{test.namebase[0:50]}{time.strftime('%H%M%S',time.localtime())}"
        ret.append("--job-name")
        ret.append(test.jobname)
        return ret + self.calculateBasicCommandList(test)

    def canRun(self, test):
        """
        Is this machine able to run the test interactively when resources become available?
           If so return ''.  Otherwise return the reason it cannot be run here.
        """
        np = max(test.np, 1)
        FluxScheduled.set_nt_num_nodes(self, test)
        if (np * test.cpus_per_task) > self.maxCores:
            return "Too many cores needed (%d > %d)" % (np * test.cpus_per_task, self.maxCores)

        if test.num_nodes > self.numNodes:
            return "Too many nodes needed (%d)" % (test.num_nodes)

        return ""

    def canRunNow(self, test):
        "Is this machine able to run this test now? Return True/False"
        sequential = test.options.get('sequential', False)
        if sequential == True:
            if self.numProcsAvailable < self.maxCores:
                return False

        if self.remainingCapacity() >= test.np:
            if FluxScheduled.debug_canRunNow:
                print("FluxScheduled DEBUG: canRunNow returning True. capacity=%i >= test.np=%i" % (self.remainingCapacity(), test.np))
            return True
        else:
            if FluxScheduled.debug_canRunNow:
                print("FluxScheduled DEBUG: canRunNow returning False. capacity=%i < test.np=%i" % (self.remainingCapacity(), test.np))
            return False

    # ##############################################################################################################################
    #
    # SAD : 2022 Nov 1 Comment
    #
    # The remainingCapacity() makes a call to Flux to see how many cores are available.
    # As there is a delay between ATS giving the jobs to Flux, and the actual start of the job
    # the remainingCapacity() does not reflect the jobs submitted to Flux by ATS, but rather the jobs
    # currently running.  Hence, while noteLaunch mentions that 10 cores will be requested
    # that is not immediately reflected in the return from the remainingCapacity() call. 
    #
    # ##############################################################################################################################
    def noteLaunch(self, test):
        """A test has been launched."""
        np = max(test.np, 1)
        FluxScheduled.set_nt_num_nodes(self, test)

        if FluxScheduled.debug_noteLaunch:
            print("FluxScheduled DEBUG: Before Job Launch remainingCores=%i remainingNodes=%i test.num_nodes=%i test.np=%i " % 
                (self.numProcsAvailable, self.numNodes - self.numberNodesExclusivelyUsed, test.num_nodes, np))

        self.numProcsAvailable -= (np * test.cpus_per_task)
        if test.num_nodes > 0:
            self.numberNodesExclusivelyUsed += test.num_nodes

        if FluxScheduled.debug_noteLaunch:
            print("FluxScheduled DEBUG: After  Job Launch remainingCores=%i remainingNodes=%i test.num_nodes=%i test.np=%i " % 
                (self.numProcsAvailable, self.numNodes - self.numberNodesExclusivelyUsed, test.num_nodes, np))

    def noteEnd(self, test):
        """A test has finished running. """
        np = max(test.np, 1)
        FluxScheduled.set_nt_num_nodes(self, test)
        self.numProcsAvailable += (np * test.cpus_per_task)
        if test.num_nodes > 0:
            self.numberNodesExclusivelyUsed -= test.num_nodes
        if FluxScheduled.debug_noteLaunch:
            print("FluxScheduled DEBUG: After  Job Finished remainingCores=%i remainingNodes=%i test.num_nodes=%i test.np=%i " % 
                (self.numProcsAvailable, self.numNodes - self.numberNodesExclusivelyUsed, test.num_nodes, np))

    def periodicReport(self):
        """
        Report on current status of tasks and processor availability.
        Utilizes Flux accessors for resource_list and flux job monitoring capabilities.
        """
        # TODO: reconcile ATS's notion of "running" with Flux
        # ATS says anything that it has submitted to the queue is "running" but with Flux
        # jobs that have been submitted to the queue may not have necessarily been allocated resources yet

        if self.running:
            terminal(
                "CURRENTLY RUNNING %d tests:" % len(self.running),
                " ".join([t.name for t in self.running]),
            )
        terminal("-" * 80)

        ## Flux specific accessors for number of nodes
        # resource_list = flux.resource.list.resource_list(self.fluxHandle).get()
        # procs = resource_list.allocated.ncores
        # total = resource_list.up.ncores
        # terminal(f"CURRENTLY UTILIZING {procs} of {total} processors.")

        numProcsUsed = min(self.maxCores, self.maxCores - self.numProcsAvailable)
        terminal(f"CURRENTLY UTILIZING {numProcsUsed} of {self.maxCores} processors.")
        terminal("-" * 80)


    # ##############################################################################################################################
    #
    # SAD : 2022 Nov 1 Comment
    #
    # Let's go ahead and add some throttling to Flux.  Primarily to keep down the number of open pipes used
    # to monitor jobs.
    #
    # First look at the ATS tallies for number of nodes and cores. 
    # If those indicate none letft, return 0.
    # If ATS thinks there are some left, then check and return the FLUX values for number of nodes or cores
    #
    # ##############################################################################################################################

    def remainingCapacity(self):
        """Returns the number of free cores in the flux instance."""

        if self.numProcsAvailable < 1:
            return 0
        else:
            if self.numberNodesExclusivelyUsed >= self.numNodes:
                return 0
            else:
                if (flux.resource.list.resource_list(self.fluxHandle).get().free.nnodes < 1):
                    return 0
                else:
                    return flux.resource.list.resource_list(self.fluxHandle).get().free.ncores
              







