#ATS:flux00             SELF FluxScheduled 2

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
from ats import log


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

        # coresPerGPU is needed to get the -c option correct
        # when running with GPUs.
        if not self.numGPUs is 0:
            self.coresPerGPU = int(self.numCores / self.numGPUs)
        else:
            self.coresPerGPU = 0

        if FluxScheduled.debug:
            print("DEBUG: FluxScheduled init : self.numNodes    =%i" % (self.numNodes))
            print("DEBUG: FluxScheduled init : self.maxCores    =%i" % (self.maxCores))
            print("DEBUG: FluxScheduled init : self.numCores    =%i" % (self.numCores))
            print("DEBUG: FluxScheduled init : self.numGPUs     =%i" % (self.numGPUs))
            print("DEBUG: FluxScheduled init : self.coresPerGPU =%i" % (self.coresPerGPU))

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
        self.timelimit = options.timelimit
        self.toss_nn   = options.toss_nn
        self.cuttime   = options.cuttime
        self.flux_run_args = options.flux_run_args
        self.gpus_per_task = options.gpus_per_task
        self.test_np_max = options.test_np_max

        if FluxScheduled.debug:
            print("DEBUG: FluxScheduled examineOptions : self.timelimit=%s" % (self.timelimit))
            print("DEBUG: FluxScheduled examineOptions : self.cuttime=%s" % (self.cuttime))
            print("DEBUG: FluxScheduled examineOptions : self.flux_run_args=%s" % (self.flux_run_args))
            print("DEBUG: FluxScheduled examineOptions : self.gpus_per_task=%s" % (self.gpus_per_task))
            print("DEBUG: FluxScheduled examineOptions : self.test_np_max=%s" % (self.test_np_max))

    def set_nt_num_nodes(self, test):
        """
        Set the test options test.num_nodes (nn), test.nt (number of threads), and 
        test.ngpu (number of gpus), and test.cpus_per_task (number of cores per task)
        """

        # Command line option nt over-rides what is in the deck.
        test.nt = 1
        if configuration.options.ompNumThreads > 0:
            test.nt = configuration.options.ompNumThreads
        else:
            if 'nt' in test.options:
                test.nt = test.options.get('nt', 1)

        # set ngpu_per_task based on 
        test.gpus_per_task = 0                                          # Default to 0
        if self.gpus_per_task is not None:                              # Command line gpus_per_task is highest priority
            test.gpus_per_task = self.gpus_per_task
        elif 'gpus_per_task' in test.options:                           # Per test option 'gpus_per_task' is second priority
            test.gpus_per_task = test.options.get('gpus_per_task', 1)
        elif 'ngpu' in test.options:                                    # Per test option 'ngpu' is third priority
            test.gpus_per_task = test.options.get('ngpu', 1)            # and is here for backwards compatability with existing decks.

        test.ngpu = test.gpus_per_task                                  # So that the schedulers.py file will print ngpu
                                                                        # maintains backwards compatibility

        # cpus per task is related to num threads and num_gpus_per_task , but 
        # it is also meaningful for non threaded and non GPU runs
        # where we want to reserve more than 1 core per mpi rank
        # So default it to 'nt' which was set above, but
        # allow it to be set separately as well. 
        test.cpus_per_task = test.nt
        if configuration.options.cpusPerTask > -1:
            test.cpus_per_task = configuration.options.cpusPerTask
        else:
            if 'cpus_per_task' in test.options:
                test.cpus_per_task = test.options.get('cpus_per_task', 1)

        # The above set cpus_per_task based on the number of threads requested.
        # Now see if we need to increase it for the number of gpus per task as well.
        # This can only increase this setting, so we will take the max of this 
        # calculation and the cpus_per_task that was just set above.
        cpus_per_task_based_on_gpus = test.gpus_per_task * self.coresPerGPU

        if (cpus_per_task_based_on_gpus > test.cpus_per_task):
            test.cpus_per_task = cpus_per_task_based_on_gpus

        # Command line option toss_nn over-rides what is in the deck.
        if (self.toss_nn < 0):
            test.num_nodes = test.options.get('nn', 0)
        else:
            test.num_nodes = self.toss_nn

        # Command line option test_np_max over-rides limits the max np in the test deck
        test.np = test.options.get("np", 1)
        if self.test_np_max is not None:                              
            if test.np > self.test_np_max:      # If test np is greater than the command line max 
                test.np = self.test_np_max      # then set the test np to the maxd

    def calculateCommandList(self, test):
        """
        Generates a list of commands to run a test in ATS on a
        flux instance.

        :param test: the test to be run, of type ATSTest. Defined in /ats/tests.py.
        """
        # ret = "flux run -o cpu-affinity=per-task -o mpibind=off".split()
        ret = "flux run ".split()

        FluxScheduled.set_nt_num_nodes(self, test)
        np = max(test.np, 1)

        # set max_time based on time limit priorities
        # 1) cuttime is highest priority.  This will have been copied from options.cuttime into self.cuttime
        # 2) deck timelmit is 2nd priority. Check if 'timelimit' is in the test options
        # 3) --timelimit (or default timelmit) is last
        if self.cuttime is not None:
            max_time = self.cuttime
        elif 'timelimit' in test.options:
            max_time = test.options.get("timelimit")
        else:
            max_time = self.timelimit

        ret.append(f"-t{max_time}")

        #if np > self.coresPerNode:
        #    nn = ceil(np / self.coresPerNode)

        # SAD 2023 June 21
        #   Removing 'flux exclusive for now'  If users want it, they can specify it 
        #   with the flux_run_args option.
        # if test.num_nodes > 0:
        #    ret.append(f"-N{test.num_nodes}")
        #    """Node-exclusive job scheduling: even if a job does not use the entire resources."""
        #    """Requires use of -N. """
        #    if test.options.get("exclusive", False) or self.flux_exclusive:
        #        ret.append("--exclusive")
        #elif test.options.get("exclusive", False) or self.flux_exclusive:
        #    log(f"ATS WARNING: --exclusive requires use of 'nn' option to specify the number of nodes needed.", echo=True)

        #"""Thread subscription - Flux does not oversubscribe cores by default."""
        #nt = test.options.get("nt", 1)
        #"""
        #In order to marry ATS's description of threading with Flux's understanding, Flux will
        #request 1 core per thread
        #"""
        # ret.append(f"-n{np}")  # Need to comment these out if we are using per-resource options like tasks-per-node
        # ret.append(f"-c{test.cpus_per_task}")

        # SAD comment out for now 2023 June 20
        # if gpus_per_task:
        #     ret.append(f"--gpus-per-task={gpus_per_task}")

        # Let's punt on gpus_per_node or gpus_per_job or gpus_per_resource in LSF speak for now.
        # Let's get gpus_per_task working correctly first.  This will also be synonymous with 
        # the historical 'ngpu' option that was used on BlueOS.
        # But commenting out gpus_per_node for now.
        # gpus_per_node = test.options.get("gpus_per_node", 0)
        # if gpus_per_node:
        #     if gpus_per_node > (self.numGPUs / self.numNodes):
        #         log(f"ATS WARNING: Number of gpus_per_node requested is higher than this machine can support. This machine allows for a max of: {self.numGPUs // self.numNodes}", echo=True)
        #     ret.append(f"--gpus-per-node={gpus_per_node}")
        #     if not test.num_nodes:
        #         log("ATS WARNING: number of nodes not set when using gpus_per_node, defaulting to nodes=1", echo=True)
        #         ret.append(f"--nodes=1")
        # else:
        #     ret.append(f"-n{np}")  # Cannot use these options if we are using per-resource options like tasks-per-node
        #     ret.append(f"-c{test.cpus_per_task}")

        """
        Need to set -n{np} and -c{test.cpus_per_task}.  But we also need to account for accessing
        GPUS using flux.  In testing flux outside of ATS it is evident that one needs to increase the -c option
        in order to access the GPUS.   The -g option alone does not suffice.
        In a test platform which has 64 CPUs and 8 GPUS, then there are 1 GPU for every 8 CPUS and the 
        -c option must be used to ensure GPU access as follows:
       
        8 MPI 1 GPU each: -n 8 -c 8   <-- each MPI rank reserves the 8 CPUS neede to get the 1 GPU
        4 MPI 2 GPU each: -n 4 -c 16  <-- each MPI rank reserves 16 CPUs to get the 2 GPUS.
        2 MPI 4 GPU each: -n 2 -c 32
        1 MPI 8 GPU each: -n 1 -c 64 
        
        Thus we need to find the 'c_multiplier' needed for each GPU.  In this case we can divide 
        the number of CPUs by the number of GPUS  (64 / 8) and get 8 as the factor. 
        And we can use this to set the -c option.

        The above is accounted for now in routine set_nt_num_nodes which was already called
        """

        # Cannot use these options if we are using per-resource options like tasks-per-node
        ret.append(f"-n{np}")               
        ret.append(f"-c{test.cpus_per_task}")   # Needs to be set properly for threaded or gpu runs

        # Pass any arbitrary string provided by the user here.  This could be any of the -o options for affinity
        # preferences, or any other valid 'flux run' option
        if self.flux_run_args != "unset":
            ret.append(self.flux_run_args)

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
        FluxScheduled.set_nt_num_nodes(self, test)
        np = max(test.np, 1)
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
        FluxScheduled.set_nt_num_nodes(self, test)
        np = max(test.np, 1)

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
        FluxScheduled.set_nt_num_nodes(self, test)
        np = max(test.np, 1)
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
