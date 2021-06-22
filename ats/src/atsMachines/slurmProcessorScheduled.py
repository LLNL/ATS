#ATS:SlurmProcessorScheduled SELF SlurmProcessorScheduled 12
#ATS:slurm8                  SELF SlurmProcessorScheduled  8
#ATS:slurm12                 SELF SlurmProcessorScheduled 12
#ATS:slurm16                 SELF SlurmProcessorScheduled 16
#ATS:slurm20                 SELF SlurmProcessorScheduled 20
#ATS:slurm24                 SELF SlurmProcessorScheduled 24
#ATS:slurm32                 SELF SlurmProcessorScheduled 32
#ATS:slurm36                 SELF SlurmProcessorScheduled 36
#ATS:chaos_5_x86_64_ib       SELF SlurmProcessorScheduled 20
#ATS:toss_3_x86_64_ib        SELF SlurmProcessorScheduled 36
#ATS:toss_3_x86_64           SELF SlurmProcessorScheduled 36
#ATS:toss_4_x86_64_ib_cray   SELF SlurmProcessorScheduled 64

import inspect

from ats import machines, debug, atsut
from ats import log, terminal
from ats import configuration
from ats.atsut import RUNNING, TIMEDOUT, PASSED, FAILED, CREATED, SKIPPED, HALTED, EXPECTED, statuses
import utils, math
import lcMachines
import sys, os, time


MY_SYS_TYPE = os.environ.get('SYS_TYPE', sys.platform)

class SlurmProcessorScheduled (lcMachines.LCMachineCore):

    lastMessageLine = 0
    remainingCapacity_numNodesReported = -1
    remainingCapacity_numProcsReported = -1
    remainingCapacity_numTestsReported = -1
    canRunNow_numProcsAvailableReported = -1
    canRunNow_saved_string = ""
    checkForAtsProcNumRemovedProcs = 0
    debugClass = False
    canRunNow_debugClass = False

    def init (self):

        self.runningWithinSalloc = True

        if "SLURM_JOB_NUM_NODES" in os.environ.keys():
            self.numNodes= int(os.getenv("SLURM_JOB_NUM_NODES"))
            self.npMax= int(os.getenv("SLURM_JOB_CPUS_PER_NODE", "1").split("(")[0])
        elif "SLURM_NNODES" in os.environ.keys():
            self.numNodes= int(os.getenv("SLURM_NNODES"))
            self.npMax= int(os.getenv("SLURM_JOB_CPUS_PER_NODE", "1").split("(")[0])
        else:
            self.runningWithinSalloc = False
            self.npMax= self.numberTestsRunningMax
            # If on alastor, and the default 36 cores is assumed, set it to 20 cores.
            if "HOSTNAME" in os.environ.keys():
                self.hostname= os.getenv("HOSTNAME")
                if self.hostname.startswith('rzalastor'):
                    if self.npMax == 36:
                        print "Setting npMax to 20 on alastor"
                        self.npMax = 20
                        self.npMaxH = 20

        # Does slurm see the ATS process itself as utilizing a core?
        self.slurmSeesATSProcessAsUsingACore = False
        if "SLURM_PTY_PORT" in os.environ.keys() or "SLURM_STEP_ID" in os.environ.keys():
            self.slurmSeesATSProcessAsUsingACore = True
            print ""
            print "ATS NOTICE: Slurm sees ATS or Shell as itself using a CPU. "
            print "            ATS Will ignore 'nn' (number of noes) test options and allow processes."
            print "            to span multiple nodes for better throughput and to help prevent srun hangs"
            print ""
            print "            NOTE: This feature may not fix possible hangs resulting from a single test "
            print "                  case which utilizes all allocated cores. Slurm may not see all "
            print "                  the cores as usable and accept the job but not schedule it, resulting in a hang"
            print ""
            print "            The node spanning behavior may be overridden with the --strict_nn ATS option."
            print ""
            print "            CAUTION: Use of --strict_nn may result in slurm/srun hangs which are "
            print "                      beyond the control of ATS, depending on how the nodes were allocated"
            print ""

        super(SlurmProcessorScheduled, self).init()

    #
    # Slurm subtracts one node from the script itself which is running if an salloc is done beforehand.
    # original coding looked for 'bin/ats' process, which does not work with all the wrappers that
    # projects put around ats.  We need another method to determine if the ats wrapper or binary
    # will be taking up one of the cores.
    #
    # Let's try and do this with ENV VARS instead
    #
    def checkForAtsProc(self):
        if self.checkForAtsProcFlag == True:
            if "SLURM_PTY_PORT" in os.environ.keys() or "SLURM_STEP_ID" in os.environ.keys():
                if SlurmProcessorScheduled.debugClass:
                    print "DEBUG checkForAtsProc returning 1 (TRUE)"
                return 1
            else:
                if SlurmProcessorScheduled.debugClass:
                    print "DEBUG checkForAtsProc returning 0 (FALSE)"
                return 0
        else:
            if SlurmProcessorScheduled.debugClass:
                print "DEBUG (checkForAtsProc is False) checkForAtsProc returning 0 (FALSE)"
            return 0


    def getNumberOfProcessors(self):
        return self.numberMaxProcessors

    def examineOptions(self, options):
        "Examine options from command line, possibly override command line choices."
        # Grab option values.
        # Note, this machines.Machine.examineOptions call will reset self.numberTestsRunningMax
        # self.numberTestsRunningMax is set in init(), not need to call machines.Machine.examineOptions
        # machines.Machine.examineOptions(self, options)

        self.distribution        = options.distribution
        self.checkForAtsProcFlag = options.checkForAtsProc

        if SlurmProcessorScheduled.debugClass:
            print "DEBUG SlurmProcessorScheduled Class options.cuttime             = %s " % options.cuttime
            print "DEBUG SlurmProcessorScheduled Class options.timelimit           = %s " % options.timelimit
            print "DEBUG SlurmProcessorScheduled Class options.globalPostrunScript = %s " % options.globalPostrunScript
            print "DEBUG SlurmProcessorScheduled Class options.globalPrerunScript  = %s " % options.globalPrerunScript
            print "DEBUG SlurmProcessorScheduled Class options.testStdout          = %s " % options.testStdout
            print "DEBUG SlurmProcessorScheduled Class options.logdir              = %s " % options.logdir
            print "DEBUG SlurmProcessorScheduled Class options.level               = %s " % options.level
            print "DEBUG SlurmProcessorScheduled Class options.npMax               = %s " % options.npMax
            print "DEBUG SlurmProcessorScheduled Class options.reportFreq          = %s " % options.reportFreq
            print "DEBUG SlurmProcessorScheduled Class options.ompNumThreads       = %s " % options.ompNumThreads
            print "DEBUG SlurmProcessorScheduled Class options.cpusPerTask         = %s " % options.cpusPerTask
            print "DEBUG SlurmProcessorScheduled Class options.sleepBeforeSrun     = %s " % options.sleepBeforeSrun
            print "DEBUG SlurmProcessorScheduled Class options.continueFreq        = %s " % options.continueFreq
            print "DEBUG SlurmProcessorScheduled Class options.verbose             = %s " % options.verbose
            print "DEBUG SlurmProcessorScheduled Class options.debug               = %s " % options.debug
            print "DEBUG SlurmProcessorScheduled Class options.info                = %s " % options.info
            print "DEBUG SlurmProcessorScheduled Class options.hideOutput          = %s " % options.hideOutput
            print "DEBUG SlurmProcessorScheduled Class options.keep                = %s " % options.keep
            print "DEBUG SlurmProcessorScheduled Class options.logUsage            = %s " % options.logUsage
            print "DEBUG SlurmProcessorScheduled Class options.okInvalid           = %s " % options.okInvalid
            print "DEBUG SlurmProcessorScheduled Class options.oneFailure          = %s " % options.oneFailure
            print "DEBUG SlurmProcessorScheduled Class options.sequential          = %s " % options.sequential
            print "DEBUG SlurmProcessorScheduled Class options.nosrun              = %s " % options.nosrun
            print "DEBUG SlurmProcessorScheduled Class options.checkForAtsProc     = %s " % options.checkForAtsProc
            print "DEBUG SlurmProcessorScheduled Class options.showGroupStartOnly  = %s " % options.showGroupStartOnly
            print "DEBUG SlurmProcessorScheduled Class options.skip                = %s " % options.skip
            print "DEBUG SlurmProcessorScheduled Class options.exclusive           = %s " % options.exclusive
            print "DEBUG SlurmProcessorScheduled Class options.mpibind             = %s " % options.mpibind
            print "DEBUG SlurmProcessorScheduled Class options.combineOutErr       = %s " % options.combineOutErr
            print "DEBUG SlurmProcessorScheduled Class options.allInteractive      = %s " % options.allInteractive
            print "DEBUG SlurmProcessorScheduled Class options.filter              = %s " % options.filter
            print "DEBUG SlurmProcessorScheduled Class options.glue                = %s " % options.glue

        if options.npMax > 0:
            self.npMax = options.npMax
        else:
            if self.runningWithinSalloc:
                self.npMax = min(self.npMaxH, self.npMax)
            else:
                self.npMax = self.npMaxH

        if self.runningWithinSalloc:
            options.numNodes = self.numNodes

        if not self.runningWithinSalloc:
            super(SlurmProcessorScheduled, self).examineOptions(options)
            self.numNodes  = options.numNodes
            self.partition = options.partition

        self.numberMaxProcessors   = self.npMax * self.numNodes

        # If the user did not set npMax by hand
        # AND if we running within an salloc partition
        # AND if one cpu is being used already for our shell or whatever
        # Then subtract one core from the max number of processors (across all nodes)
        if options.npMax <= 0:
            if self.runningWithinSalloc==True:
                if self.checkForAtsProc():
                    self.numberMaxProcessors -= 1
                    SlurmProcessorScheduled.checkForAtsProcNumRemovedProcs = 1

        self.numProcsAvailable     = self.numberMaxProcessors
        self.numberTestsRunningMax = self.numberMaxProcessors

        self.exclusive = options.exclusive
        self.mpibind   = options.mpibind
        self.toss_nn   = options.toss_nn
        self.strict_nn = options.strict_nn
        self.timelimit = options.timelimit

        #print "DEBUG self.test_nn = %d " % self.toss_nn

        if SlurmProcessorScheduled.debugClass:
            print "DEBUG examineOptions leaving self.npMax = %d " % self.npMax
            print "DEBUG examineOptions leaving self.npMaxH = %d " % self.npMaxH
            print "DEBUG examineOptions leaving self.numberMaxProcessors = %d " % self.numberMaxProcessors
            print "DEBUG examineOptions leaving self.numberTestsRunningMax = %d " % self.numberTestsRunningMax

    def addOptions(self, parser):
        """Add options needed on this machine."""

        temp_uname = os.uname()
        host = temp_uname[1]

        the_partition = 'pdebug'
        if host.startswith('rzwhamo'):
            the_partition = 'nvidia'

        parser.add_option("--partition", action="store", type="string", dest='partition',
            default = the_partition,
            help = "Partition in which to run jobs with np > 0")

        parser.add_option("--numNodes", action="store", type="int", dest='numNodes',
           default = 2,
           help="Number of nodes to use")

        parser.add_option("--distribution", action="store", type="string", dest='distribution',
           default = 'unset',
           help="srun distribution of mpi processes across nodes")


    def getResults(self):
        """I'm not sure what this function is supposed to do"""
        return machines.Machine.getResults(self)

    def label(self):
        return "SlurmProcessorScheduled: %d nodes, %d processors per node." % (
            self.numNodes, self.npMax)

    def set_nt_num_nodes(self,test):

        # Command line option nt over-rides what is in the deck.
        test.nt = 1
        if configuration.options.ompNumThreads > 0:
            test.nt = configuration.options.ompNumThreads
        else:
            if test.options.has_key('nt'):
                test.nt = test.options.get('nt', 1)

        test.cpus_per_task = -1
        if configuration.options.cpusPerTask > -1:
            test.cpus_per_task = configuration.options.cpusPerTask
        else:
            if test.options.has_key('cpus_per_task'):
                test.cpus_per_task = test.options.get('cpus_per_task', 1)

        # Command line option toss_nn over-rides what is in the deck.
        if (self.toss_nn < 0):
            test.num_nodes = test.options.get('nn', 0)
        else:
            test.num_nodes = self.toss_nn

        # If num_nodes not specified check to see if we are running more than 40 MPI processes, if so we need
        # multiple nodes (hosts)
        if ((test.np * test.nt) > self.npMax):
            if test.num_nodes < 1:
                if (self.toss_nn < 0):
                    test.num_nodes = math.ceil( (float(test.np) * float(test.nt)) / float(self.npMax))
                    test.nn = test.num_nodes
                    if configuration.options.verbose:
                        print "ATS setting test.nn to %i for test %s based on test.np = %i and test.nt=%i (%i x %i = %i) which spans 2 or more nodes." % (test.num_nodes, test.name, test.np, test.nt, test.np, test.nt, test.np * test.nt)

    def calculateCommandList(self, test):
        """Prepare for run of executable using a suitable command. First we get the plain command
         line that would be executed on a vanilla machine, then we modify it if necessary
         for use on this machines.
        """

        import os

        np                 = max(test.np, 1)
        distribution       = self.distribution        # default is cyclic, by can be overridden with --distribution=xxx
        test.runningWithinSalloc = self.runningWithinSalloc
        commandList        = self.calculateBasicCommandList(test)
        timeNow            = time.strftime('%H%M%S',time.localtime())
        test.jobname       = "t%d_%d%s%s" % (np, test.serialNumber, test.namebase[0:50], timeNow)
        minNodes           = np / self.npMax + (np % self.npMax != 0 )
        test_time          = test.options.get('time',0);

        SlurmProcessorScheduled.set_nt_num_nodes(self, test)
        num_nodes   = test.num_nodes
        num_threads = test.nt

        #
        # --exclusive is the default, but it can be switched via the --share ats argument
        #
        if self.exclusive == True:
            ex_or_sh = "--exclusive"
        else:
            ex_or_sh = "--share"

        temp_uname = os.uname()
        host = temp_uname[1]

        the_mpi_type='-v'
        if host.startswith('rznevaxxx'):
            the_mpi_type='--mpi=pmi2'


        if MY_SYS_TYPE.startswith('toss'):
            # none means to not spcify mpibind at all
            if self.mpibind == "none":
                mpibind = "--epilog=none"
            else:
                mpibind = "--mpibind=%s" % self.mpibind
        else:
            mpibind = "--epilog=none"

        #
        # If the distribution is unset, then set it to cyclic
        #
        if distribution == 'unset':
            distribution='cyclic'

        # ----------------------------------------------------------------------------------------------------------------------------
        # ----------------------------------------------------------------------------------------------------------------------------
        # Discussion on use of the nn option to specify the number of nodes to run a test on.
        # This option is used in conjunction with np.  When specified together, they mean to use exactly the specified number of
        # nodes to run the specified number of processes.  In this mode, other mpi jobs should not share the node.  This allows
        # the user to undersubscribe the number of cores on the node so that they can do one or both of the following:
        #
        # 1) access more memory per mpi process
        # 2) use threads to access multiple cores per mpi process
        #
        #
        # Testing on rzzeus (8 cores per node)
        #
        # srun --exclusive --nodes=3-3 --ntasks=3 --cpus-per-task=8 <- good, puts 1 mpi task on each of 3 nodes
        # srun --exclusive --nodes=3-3 --ntasks=4 --cpus-per-task=2 <- kinda works, but mixes and matches several mpi jobs
        #                                                              on the same node, so that if the user is trying
        #                                                              to fit in memory, or use threads, the mixing of multiple
        #                                                              jobs on 1 node will confuse things.
        # srun --exclusive --nodes=3-3 --ntasks=6 --cpus-per-task=1 <- will still put 6 tasks on 1 node --ignoring the -nodes option
        #
        # And many other runs, result in the only predictable behavior for srun will require that
        #
        # BOTH THE FOLLOWING CONDITIONS ARE MET
        #
        # The number of processes requested (np in ATS speak, and --ntasks in slurm speak) evenly
        #     divides into the number of nodes requested (nn in ATS speak, and --nodes=9-9 in slurm speak)
        #     Valid examples are: 3 nodes requested and 3, 6, 9, 12 processors.
        #     This division will give us our tasks-per-node value.
        #
        # AND
        #
        # The tasks-per-node calculated above must divide evenly into the number of cores on a node. Thus
        #     Valid example of tasks-per-node on zeus    (8 cores per node)  are 1, 2, 4, 8
        #     Valid example "" ""             "" alastor (12 cores per node) are 1, 2, 4, 6, 12
        #     Valid example "" ""             "" alastor (20 cores per node) are 1, 2, 4, 5, 10
        #     Valid example "" ""             "' merl    (16 cores per node) are 1, 2, 4, 8, 16
        #
        #       examples        requested   requested    calculated     calculated
        #             cores-    --nodes     --ntasks     (inferred)     --cpus-per-task
        #     machine per-node  nn         np            tasks-per-node cpus-per-task
        #                                                np / nn        cores-per-node / tasks-per-node
        #     zeus    8         1           1            1 / 1 = 1      8 / 1 = 8
        #     zeus    8         1           2            2 / 1 = 2      8 / 2 = 4
        #     zeus    8         1           4            4 / 1 = 4      8 / 4 = 2
        #     zeus    8         1           8            8 / 1 = 8      8 / 8 = 1
        #
        #     zeus    8         2           2            2 / 2 = 1      8 / 2 = 8
        #     zeus    8         2           4            4 / 2 = 2      8 / 4 = 4
        #     zeus    8         2           8            8 / 2 = 4      8 / 8 = 2
        #     zeus    8         2          16            16/ 2 = 8      8 /16 = 1
        #
        #     zeus    8         3           2            2 / 3 = INV
        #     zeus    8         3           3            3 / 3 = 1      8 / 1 = 8
        #     zeus    8         3           4            4 / 3 = INV                (cannot evenly distribute 4 tasks on 3 nodes)
        #     zeus    8         3           6            6 / 3 = 2      8 / 2 = 4
        #     zeus    8         3           8            8 / 3 = INV                (cannot evenly distribute 8 tasks on 3 nodes
        #     zeus    8         3           9            9 / 3 = 3      8 / 3 = INV (cannot evenly distribute 9 tasks on 24 cores)
        #     zeus    8         3          12            12/ 3 = 4      8 / 4 = 2
        #     zeus    8         3          24            24/ 3 = 8      8 / 8 = 1
        #
        #  alastor   12         2           2            2 / 2 = 1     12 / 1 = 12
        #  alastor   12         2           3            3 / 2 = INV                (cannot evenly distribute 3 tasks on 2 nodes)
        #  alastor   12         2           4            4 / 2 = 2     12 / 2 = 6
        #  alastor   12         2           6            6 / 2 = 3     12 / 3 = 4
        #  alastor   12         2           8            8 / 2 = 4     12 / 4 = 3
        #  alastor   12         2          12           12 / 2 = 6     12 / 6 = 2
        #  alastor   12         2          16           16 / 2 = 8     12 / 8 = INV (cannot evenly distrubute 16 tasks across 24 cores)
        #  alastor   12         2          24           24 / 2 = 12    12 /12 = 1
        #
        #
        # This is all calculated using the "nn=1" ATS option.  If it is present, then we go into
        # this extra set of calculations and accept or reject the test case.  There is no need for the user
        # to tell ATS about the number of threads.  If the code can use threads it may do so by specifying command
        # line arguments.
        # ----------------------------------------------------------------------------------------------------------------------------
        # ----------------------------------------------------------------------------------------------------------------------------
        if num_nodes > 0:
            #print "DEBUG slurmProcessorScheduled AAA"

            test.numNodesToUse = num_nodes

            if   "SLURM_NNODES" in os.environ.keys():
                self.slurm_nnodes = int(os.getenv("SLURM_NNODES"))
            elif "SLURM_JOB_NUM_NODES" in os.environ.keys():
                self.slurm_nnodes = int(os.getenv("SLURM_JOB_NUM_NODES"))
            elif self.numNodes > 0:
                self.slurm_nnodes = self.numNodes
            else:
                print "ERROR 'nn' specified but neither SLURM_NNODES nor self.numNodes is set."
                sys.exit(1)

            if     "SLURM_JOB_CPUS_PER_NODE" in os.environ.keys():
                self.slurm_cpus_on_node = int(os.getenv("SLURM_JOB_CPUS_PER_NODE", "1").split("(")[0])
            elif   "SLURM_CPUS_ON_NODE" in os.environ.keys():
                self.slurm_cpus_on_node = int(os.getenv("SLURM_CPUS_ON_NODE"))
            elif self.npMax > 0:
                self.slurm_cpus_on_node = self.npMax
            else:
                print "ERROR 'nn' specified neither SLURM_JOB_CPUS_PER_NODE nor SLURM_CPUS_ON_NODE nor self.npMax is set."
                sys.exit(1)

            tasks_per_node        = np / num_nodes
            tasks_per_node_modulo = np % num_nodes
            if (tasks_per_node < 1) :
                tasks_per_node = 1

            if not tasks_per_node_modulo == 0:

                #  Bump up the tasks per node by 1 as at least 1 node will have extra tasks.
                tasks_per_node +=1

                print test
                print "ATS Warning: np=%i nn=%i" % (np, num_nodes)
                print "             number_of_processes (%i) is not evenly divisible by number_of_nodes (%i)"  % (np, num_nodes)
                print "             %i modulo %i = %i " % (np, num_nodes, tasks_per_node_modulo)
                print " "
                print "             %s " % test.name
                print " "

            # print "DEBUG slurmProcessorScheduled 000 user set nt = %d" % num_threads
            if test.cpus_per_task > -1:

                cpus_per_task = int(test.cpus_per_task)

            else:
                if (num_threads > 1):

                    cpus_per_task = int(num_threads)

                    # If ATS is running in such a way that slurm sees all the cores AND
                    # nn is > 1 and nt > 1 then the user wants a dedicated node.
                    # In this case, bump up the cpus_per_task to achieve this under slurm.
                    # Do not let slurm pack a partial set of nodes and let other nodes sit idle.
                    if self.slurmSeesATSProcessAsUsingACore == False:
                        all_the_cpus_per_task = int(self.slurm_cpus_on_node / tasks_per_node)
                        if all_the_cpus_per_task > cpus_per_task:
                            cpus_per_task = all_the_cpus_per_task
                            #print "DEBUG slurmProcessorScheduled 005 tasks_per_node=%d, self.slurm_cpus_on_node=%d, cpus_per_task=%d, all_the_cpus_per_task=%d\n" % (tasks_per_node, self.slurm_cpus_on_node, cpus_per_task, all_the_cpus_per_task)

                    #print "DEBUG slurmProcessorScheduled 010 cpus_per_task = %d\n" % (cpus_per_task)

                else:
                    #print "DEBUG slurmProcessorScheduled 020 self.slurm_cpus_on_node=%d tasks_per_node=%d\n" % (self.slurm_cpus_on_node, tasks_per_node)
                    cpus_per_task = int(self.slurm_cpus_on_node / tasks_per_node)


                # NOTE 123 SAD 2012-12-12
                # If the user has specified a job which will utilize all the nodes and cpus_per_task is > 1
                # we can get slurm to run the test by bumping down the cpus_per_task. Do not do this if
                # the cpus_per_task was explicitly set.  But it will allow the test to run if cpus_per_task
                # was set based on the openmp number of threads.  It may be less efficient, depending on how
                # the threads are bound to cores, but it will run.
                if self.slurmSeesATSProcessAsUsingACore:
                    while (cpus_per_task > 1) and ((np * cpus_per_task) >= self.numberMaxProcessors):
                        cpus_per_task -= 1

                        # print "DEBUG slurmProcessorScheduled 040 cpus_per_task = %d" % cpus_per_task
                #print "DEBUG slurmProcessorScheduled 050 cpus_per_task = %d" % cpus_per_task

                test.cpus_per_task  = cpus_per_task

            # print "DEBUG slurmProcessorScheduled 040 test.cpus_per_task = %d cpus_per_task = %d" % (test.cpus_per_task, cpus_per_task)
            test.tasks_per_node = tasks_per_node

            if self.slurmSeesATSProcessAsUsingACore:
                if cpus_per_task > 1:
                    if (np * cpus_per_task) >= self.numberMaxProcessors:
                        print "ATS WARNING: Test %s May Hang! " % test.name
                        print "             User requested %d MPI Processes and %d cpus_per_task" % (np, cpus_per_task)
                        print "             This allocation has %d max processors " % self.numberMaxProcessors
                        print "             Slurm may see your shell as utilizing a process and never"
                        print "             schedule this job to run, resulting in a hang."
                        print "ATS ADVICE:  Consider setting cpus_per_task to %d " % (cpus_per_task - 1)
                else:
                    if np >= self.numberMaxProcessors:
                        print "ATS WARNING: Test %s May Hang! " % test.name
                        print "             User requested %d MPI Processes and %d cpus_per_task" % (np, cpus_per_task)
                        print "             This allocation has %d max processors on %d nodes " % (self.numberMaxProcessors, self.numNodes)
                        print "             Slurm may see your shell as utilizing a process and never"
                        print "             schedule this job to run, resulting in a hang."
                        print "ATS ADVICE:  Consider allocating %d nodes for testing" % (self.numNodes + 1)

            if self.runningWithinSalloc == False:

                if SlurmProcessorScheduled.debugClass:
                    print "SAD DEBUG SRUN100 "

                return ["srun", the_mpi_type, "--label", "-J", test.jobname,
                    "-p", self.partition,
                    ex_or_sh,
                    mpibind,
                    "--distribution=%s" % distribution,
                    "--nodes=%i-%i" % (num_nodes, num_nodes),
                    "--ntasks=%i" % np \
                   ] + commandList
            else:
                #print "SAD DEBUG runningWithinSalloc is True"

                if SlurmProcessorScheduled.debugClass:
                    print "SAD DEBUG SRUN200 "

                # If the user has pre-allocated a node in such a manner that their shell or their ats script counts
                # as a job step, then srun has severe troubles with the --nodes=1 type option.  It will attempt to put
                # all jobs on node 1, and the running shell counts against it as using a core.
                # If running a wrapper  this is not the scenario, as those scripts.
                # do something like:
                #
                #    salloc -N 4 -p pdebug --exclusive ezats ...
                #
                # But if the user does something like 'salloc -N4 -p pdebug --exclusive" without specifying the script,
                # this will invoke a shell for the user, which confuses slurm terribly, causing poor performance
                #
                # Bottom line is that if slurm thinks there are ATS processes using nodes, the codes run best
                # by setting --nodes=1-4 or (min, max nodes) rather than strict --nodes.
                #
                # By default ATS should 'do the best thing'  But if the user wants a strict interpretation of the nn
                # option, then they may over-ride this default.
                #
                #my_nodes="--nodes=%i" % (num_nodes) SAD TESTING
                my_nodes="--epilog=none"
                if (self.strict_nn == False):
                    if self.slurmSeesATSProcessAsUsingACore == True:
                        my_nodes="--nodes=%i-%i" % (num_nodes, self.numNodes)

                #
                # Exclusive command without distribution specified
                #
                if test.cpus_per_task > 0:

                    if self.distribution == 'unset':
                        return ["srun", the_mpi_type, "--label", "-J", test.jobname,
                            ex_or_sh,
                            mpibind,
                            my_nodes,
                            "--cpus-per-task=%i" % cpus_per_task,
                            "--ntasks=%i" % np \
                        ] + commandList
                    else:
                        return ["srun", the_mpi_type, "--label", "-J", test.jobname,
                            ex_or_sh,
                            mpibind,
                            my_nodes,
                            "--distribution=%s" % distribution,
                            "--cpus-per-task=%i" % cpus_per_task,
                            "--ntasks=%i" % np \
                        ] + commandList
                else:
                    if self.distribution == 'unset':
                        return ["srun", the_mpi_type, "--label", "-J", test.jobname,
                            ex_or_sh,
                            mpibind,
                            my_nodes,
                            "--ntasks=%i" % np \
                        ] + commandList
                    else:
                        return ["srun", the_mpi_type, "--label", "-J", test.jobname,
                            ex_or_sh,
                            mpibind,
                            my_nodes,
                            "--distribution=%s" % distribution,
                            "--ntasks=%i" % np \
                        ] + commandList


        # We are running on the login node, not within an salloc allocation
        #
        if self.runningWithinSalloc == False:

            #
            # If we are exclusive, then add the -N2-2 type option to exclusively
            # reserve a set of nodes.
            #
            if self.exclusive == True:
                #
                # Exclusive command without distribution specified
                #
                if self.distribution == 'unset':
                    if SlurmProcessorScheduled.debugClass:
                        print "SAD DEBUG SRUN300 "

                    test.numNodesToUse = minNodes
                    return ["srun", the_mpi_type, "--label", "-J", test.jobname,
                            ex_or_sh,
                            mpibind,
                            "-N%i-%i" % (minNodes, minNodes),
                            "-n", str(np),
                            "-p", self.partition] + commandList
                #
                # Exclusive command with distribution specified
                #
                else:
                    if SlurmProcessorScheduled.debugClass:
                        print "SAD DEBUG SRUN350 "

                    test.numNodesToUse = minNodes
                    return ["srun", the_mpi_type, "--label", "-J", test.jobname,
                            ex_or_sh,
                            mpibind,
                            "--distribution=%s" % distribution,
                            "-N%i-%i" % (minNodes, minNodes),
                            "-n", str(np),
                            "-p", self.partition] + commandList
            #
            # If running shared, then do not specify a -N option and let the mpi
            # processes be mapped at will by slurm.  Note that this will use more than the
            # 4 nodes say, as it is not based on total number of MPI processes, which may be
            # spread across more nodes.  For example, if 4 nodes is our limit, then this
            # really means we have 64 processes (on rzmerl), which may be spread across more
            # than 4 nodes as we are sharing.
            #
            else:
                #
                # Exclusive command without distribution specified
                #
                if self.distribution == 'unset':
                    if SlurmProcessorScheduled.debugClass:
                        print "SAD DEBUG SRUN400 "
                    return ["srun", the_mpi_type, "--label", "-J", test.jobname,
                            mpibind,
                            ex_or_sh,
                            "-n", str(np),
                            "-p", self.partition] + commandList
                #
                # Exclusive command with distribution specified
                #
                else:
                    if SlurmProcessorScheduled.debugClass:
                        print "SAD DEBUG SRUN450 "
                    return ["srun", the_mpi_type, "--label", "-J", test.jobname,
                            mpibind,
                            "--distribution=%s" % distribution,
                            ex_or_sh,
                            "-n", str(np),
                            "-p", self.partition] + commandList

        # ----------------------------------------------------------------------------------------------------------------------------
        #
        # SAD Notes: 2014-03-36
        #
        # Specifying -NminNodes (such as -N1) sets both the min and max nodes to 1.  This would not be so bad if slurm worked
        # properly, but in my testing, after the first set of test is pushed through, it tries to map all the remaining
        # jobs onto the same node, and thus the jobs are serialized on 1 node, while other nodes are empty!!
        #
        # Leaving off the -N gets throughput, but it results in striping of mpi processes across nodes unnecessarily.
        # As noted in this 2 jobs test case, where they ran simultaneously, 2 jobs striped across 2 nodes
        #
        # job6: Master process reports that I am running 8 mpi processes on 3 nodes
        # job6: MPI Process  0 reporting that it is on node 14
        # job6: MPI Process  1 reporting that it is on node 14
        # job6: MPI Process  2 reporting that it is on node 14
        # job6: MPI Process  3 reporting that it is on node 15
        # job6: MPI Process  4 reporting that it is on node 15
        # job6: MPI Process  5 reporting that it is on node 15
        # job6: MPI Process  6 reporting that it is on node 16
        # job6: MPI Process  7 reporting that it is on node 16
        # job3: Master process reports that I am running 8 mpi processes on 3 nodes
        # job3: MPI Process  0 reporting that it is on node 14
        # job3: MPI Process  1 reporting that it is on node 14
        # job3: MPI Process  2 reporting that it is on node 14
        # job3: MPI Process  3 reporting that it is on node 15
        # job3: MPI Process  4 reporting that it is on node 15
        # job3: MPI Process  5 reporting that it is on node 15
        # job3: MPI Process  6 reporting that it is on node 16
        # job3: MPI Process  7 reporting that it is on node 16
        #
        #
        # Specifying -NminNodes-totNodes seems to do something better, in that it pushes all the MPI processes onto one node
        # til it is full, and then spills processes onto another node when necessary, but it does not stripe the processes
        # Adding --distribution=block further enforces this notion.
        #
        # I'm going with this option to see how it works out
        # 40mins on rzmerl
        #
        # ----------------------------------------------------------------------------------------------------------------------------
        #
        # 2014-Sep-18 Notes:
        #
        # In the following, if "--exclusive -N1" is used on a pre-allocated xterm, this winds up serializing all jobs on Node 1
        # of a 4 node allocation.
        #
        # On the other hand, if submitted from the front end, where atswrapper does the salloc it does the correct thing.
        # and will put each job an any of the available nodes.
        #
        # So detect existing of a SLURM env to tell the difference and use -N1 or -N1-4 as is needed.
        #
        # ----------------------------------------------------------------------------------------------------------------------------
        else:
            # at this point num_nodes is <= 0
            #print "DEBUG slurmProcessorScheduled BBB"

            #
            # We are on a pre-allocated node
            #
            if self.npMaxH != self.npMax:
                distribution = 'cyclic'             # If npMax is < npMaxH, then we MUST use a cyclic distribution

            if test.cpus_per_task > -1:

                cpus_per_task = int(test.cpus_per_task)

            else:
                # default cpus_per_task to 1 if not specified
                cpus_per_task = int(1)

                # if set to num_threads if specified (and if test.cpus_per_task is not specified)
                if (num_threads > 1):
                    cpus_per_task = int(num_threads)

                # see NOTE 123 above for explanation here
                if self.slurmSeesATSProcessAsUsingACore:
                    while (cpus_per_task > 1) and ((np * cpus_per_task) >= self.numberMaxProcessors):
                        cpus_per_task -= 1

                test.cpus_per_task  = cpus_per_task

            if self.slurmSeesATSProcessAsUsingACore:
                if cpus_per_task > 1:
                    if (np * cpus_per_task) >= self.numberMaxProcessors:
                        print "ATS WARNING: Test %s May Hang! " % test.name
                        print "             User requested %d MPI Processes and %d cpus_per_task" % (np, cpus_per_task)
                        print "             This allocation has %d max processors " % self.numberMaxProcessors
                        print "             Slurm may see your shell as utilizing a process and never"
                        print "             schedule this job to run, resulting in a hang."
                        print "ATS ADVICE:  Consider setting cpus_per_task to %d " % (cpus_per_task - 1)
                else:
                    if np >= self.numberMaxProcessors:
                        print "ATS WARNING: Test %s May Hang! " % test.name
                        print "             User requested %d MPI Processes and %d cpus_per_task" % (np, cpus_per_task)
                        print "             This allocation has %d max processors on %d nodes " % (self.numberMaxProcessors, self.numNodes)
                        print "             Slurm may see your shell as utilizing a process and never"
                        print "             schedule this job to run, resulting in a hang."
                        print "ATS ADVICE:  Consider allocating %d nodes for testing" % (self.numNodes + 1)

            if test.cpus_per_task > 0:
                #
                # I'm not sure exactly how we get into here, this may be dead code, it is untested at of 2014-Oct-7
                # The case where there is no SLURM_JOBID should be handled above from the login node.
                #
                if self.exclusive == True and not "SLURM_JOBID" in os.environ.keys():
                    test.numNodesToUse = minNodes
                    if SlurmProcessorScheduled.debugClass:
                        print "SAD DEBUG SRUN600 "

                    return ["srun", the_mpi_type, "--label", "-J", test.jobname,
                        ex_or_sh,
                        mpibind,
                        "--distribution=%s" % distribution,
                        "-N%i" % (minNodes),
                        "--cpus-per-task=%i" % test.cpus_per_task,
                        "-n", str(np) ] + commandList

                #
                # If distribution is unset, then trust slurm to do
                # the right thing.  No need to specify -N in order to make slurm work, or to
                # specify cyclic as it is the default anyway.
                #
                elif self.distribution == 'unset':

                    if SlurmProcessorScheduled.debugClass:
                        print "SAD DEBUG SRUN700 "

                    return ["srun", the_mpi_type, "--label", "-J", test.jobname,
                            ex_or_sh,
                            mpibind,
                            "--cpus-per-task=%i" % test.cpus_per_task,
                            "-n", str(np) ] + commandList
                #
                # If distribution is set to cyclic, then passit on, but do not specify an -N option.
                #
                elif distribution == 'cyclic':
                    if SlurmProcessorScheduled.debugClass:
                        print "SAD DEBUG SRUN800 "

                    return ["srun", the_mpi_type, "--label", "-J", test.jobname,
                            ex_or_sh,
                            mpibind,
                            "--distribution=%s" % distribution,
                            "--cpus-per-task=%i" % test.cpus_per_task,
                            "-n", str(np) ] + commandList
                #
                # If distribution is block, then do a 'packed block' distribution, filling up all of node 1
                # before moving onto node two.  This can be achieved by adding the -NminNodes-TotalNodes
                # to the srun line.  Note that this will not pack if the --share option is chosen.
                #
                else:
                    if SlurmProcessorScheduled.debugClass:
                        print "SAD DEBUG SRUN900 "

                    return ["srun", the_mpi_type, "--label", "-J", test.jobname,
                            ex_or_sh,
                            mpibind,
                            "--distribution=%s" % distribution,
                            "-N%i-%i" % (minNodes, self.numNodes),
                            "--cpus-per-task=%i" % test.cpus_per_task,
                            "-n", str(np) ] + commandList
            else:
                if self.exclusive == True and not "SLURM_JOBID" in os.environ.keys():
                    test.numNodesToUse = minNodes
                    if SlurmProcessorScheduled.debugClass:
                        print "SAD DEBUG SRUN600 "

                    return ["srun", the_mpi_type, "--label", "-J", test.jobname,
                        ex_or_sh,
                        mpibind,
                        "--distribution=%s" % distribution,
                        "-N%i" % (minNodes),
                        "-n", str(np) ] + commandList

                elif self.distribution == 'unset':

                    if SlurmProcessorScheduled.debugClass:
                        print "SAD DEBUG SRUN700 "

                    return ["srun", the_mpi_type, "--label", "-J", test.jobname,
                            ex_or_sh,
                            mpibind,
                            "-n", str(np) ] + commandList
                elif distribution == 'cyclic':
                    if SlurmProcessorScheduled.debugClass:
                        print "SAD DEBUG SRUN800 "

                    return ["srun", the_mpi_type, "--label", "-J", test.jobname,
                            ex_or_sh,
                            mpibind,
                            "--distribution=%s" % distribution,
                            "-n", str(np) ] + commandList
                else:
                    if SlurmProcessorScheduled.debugClass:
                        print "SAD DEBUG SRUN900 "

                    return ["srun", the_mpi_type, "--label", "-J", test.jobname,
                            ex_or_sh,
                            mpibind,
                            "--distribution=%s" % distribution,
                            "-N%i-%i" % (minNodes, self.numNodes),
                            "-n", str(np) ] + commandList


    def canRun(self, test):
        """Is this machine able to run the test interactively when resources become available?
           If so return ''.  Otherwise return the reason it cannot be run here.
        """
        np = max(test.np, 1)
        if np > self.numberMaxProcessors:
            return "Too many processors needed (%d)" % np

        return ''

    def canRunNow(self, test):
        "Is this machine able to run this test now? Return True/False"

        #
        # Print Debug method used by just this class
        #
        def printDebug(self, numberNodesRemaining, num_nodes, np):
            #if SlurmProcessorScheduled.debugClass or SlurmProcessorScheduled.canRunNow_debugClass:
            if SlurmProcessorScheduled.debugClass:
                print "DEBUG canRunNow ================================================================================================"
                print "DEBUG canRunNow self.numNodes                    =%d" % (self.numNodes)
                print "DEBUG canRunNow self.numberNodesExclusivelyUsed  =%d" % (self.numberNodesExclusivelyUsed)
                print "DEBUG canRunNow self.npMax                       =%d" % (self.npMax)
                print "DEBUG canRunNow numberNodesRemaining             =%d" % (numberNodesRemaining)
                print "DEBUG canRunNow num_nodes                        =%d" % (num_nodes)
                print "DEBUG canRunNow self.numProcsAvailable           =%d" % (self.numProcsAvailable)
                print "DEBUG canRunNow self.numberMaxProcessors         =%d" % (self.numberMaxProcessors)
                print "DEBUG canRunNow np                               =%d" % (np)
                print "DEBUG canRunNow self.numberTestsRunningMax       =%d" % (self.numberTestsRunningMax)
                sequential = test.options.get('sequential', False)
                print "DEBUG canRunNow sequential                       =", sequential

        # Get the number of processors needed and the number of nodes needed for this test
        # if specified.  Get the number of nodes remaining for exclusive use.
        #
        numberNodesRemaining = self.numNodes - self.numberNodesExclusivelyUsed
        np        = max(test.np, 1)
        num_nodes = test.options.get('nn', -1)

        # how many nodes are needed?  The test case may have specified -nn, or if a user
        # is running with --exclusive, we will calculate this based on the np option.
        # and the number of processors on each node
        #
        if (num_nodes <= 0):
            if self.exclusive == True and not "SLURM_JOBID" in os.environ.keys():
                num_nodes = np / self.npMax + (np % self.npMax != 0 )

        sequential = test.options.get('sequential', False)
        if sequential == True:
            if (self.numProcsAvailable < self.numberMaxProcessors):
                if configuration.options.verbose or SlurmProcessorScheduled.canRunNow_debugClass:
                    string = "%d_%d" % (self.numProcsAvailable, self.numberMaxProcessors)
                    if string != SlurmProcessorScheduled.canRunNow_saved_string:
                        SlurmProcessorScheduled.canRunNow_saved_string = string
                        printDebug(self, numberNodesRemaining, num_nodes, np)
                        if SlurmProcessorScheduled.debugClass or SlurmProcessorScheduled.canRunNow_debugClass:
                            print "DEBUG canRunNow returning FALSE based on sequential option: numProcsAvailable = %d < numberMaxProcessors = %d" % (self.numProcsAvailable, self.numberMaxProcessors)

                return False

        # if the test object has nn defined, then see if we have enuf nodes available
        # In this case, since nn has been specified, set np to be the number of nodes
        #   requested x the max number of processors per node
        if num_nodes > 0:
            np = num_nodes * self.npMax
            my_numProcsAvailable = self.numProcsAvailable + SlurmProcessorScheduled.checkForAtsProcNumRemovedProcs

            if configuration.options.verbose or SlurmProcessorScheduled.canRunNow_debugClass:
                string = "%d_%d" % (numberNodesRemaining, my_numProcsAvailable)
                if string != SlurmProcessorScheduled.canRunNow_saved_string:
                    SlurmProcessorScheduled.canRunNow_saved_string = string
                    if numberNodesRemaining >= num_nodes and my_numProcsAvailable >= np:
                        printDebug(self, numberNodesRemaining, num_nodes, np)
                        if SlurmProcessorScheduled.debugClass or SlurmProcessorScheduled.canRunNow_debugClass:
                            print "DEBUG canRunNow returning TRUE  based on node avail: %d is  >= %d and proc avail : %d is  >= %d" % (numberNodesRemaining, num_nodes, my_numProcsAvailable, np)
                    else:
                        printDebug(self, numberNodesRemaining, num_nodes, np)
                        if SlurmProcessorScheduled.debugClass or SlurmProcessorScheduled.canRunNow_debugClass:
                            print "DEBUG canRunNow returning FALSE based on node avail: %d not >= %d or proc avail : %d not >= %d" % (numberNodesRemaining, num_nodes, my_numProcsAvailable, np)

            return numberNodesRemaining >= num_nodes and my_numProcsAvailable >= np

        # else, back to our original programming, see if there are enuf procs available
        else:
            if configuration.options.verbose or SlurmProcessorScheduled.canRunNow_debugClass:
                if self.numProcsAvailable != SlurmProcessorScheduled.canRunNow_numProcsAvailableReported:
                    SlurmProcessorScheduled.canRunNow_numProcsAvailableReported = self.numProcsAvailable
                    if self.numProcsAvailable >= np:
                        printDebug(self, numberNodesRemaining, num_nodes, np)
                        if SlurmProcessorScheduled.debugClass or SlurmProcessorScheduled.canRunNow_debugClass:
                            print "DEBUG canRunNow returning TRUE  based on proc avail: %d is  >= %d " % (self.numProcsAvailable, np)
                    else:
                        printDebug(self, numberNodesRemaining, num_nodes, np)
                        if SlurmProcessorScheduled.debugClass or SlurmProcessorScheduled.canRunNow_debugClass:
                            print "DEBUG canRunNow returning FALSE based on proc avail: %d not >= %d " % (self.numProcsAvailable, np)

            return self.numProcsAvailable >= np

    def noteLaunch(self, test):
        """A test has been launched."""
        np = max(test.np, 1)
        self.numProcsAvailable -= (np * test.cpus_per_task)
        test.cpus_per_task_for_noteEnd = test.cpus_per_task
        if SlurmProcessorScheduled.debugClass or SlurmProcessorScheduled.canRunNow_debugClass:
            print "DEBUG noteLaunch decreased self.numProcsAvailable by (%d x %d) to %d " % (np,  test.cpus_per_task, self.numProcsAvailable)

    def noteEnd(self, test):
        """A test has finished running. """

        SlurmProcessorScheduled.set_nt_num_nodes(self, test)
        my_np = max(test.np, 1)
        my_nt = max(test.nt, 1)
        my_nn = max(test.num_nodes, 0)

        self.numProcsAvailable += (my_np * test.cpus_per_task_for_noteEnd)
        if SlurmProcessorScheduled.debugClass or SlurmProcessorScheduled.canRunNow_debugClass:
            print "DEBUG noteEnd increased self.numProcsAvailable by (%d x %d) to %d " % (my_np, test.cpus_per_task_for_noteEnd, self.numProcsAvailable)

        msg = '%s #%4d %s,  nn=%d, np=%d, nt=%d, ngpu=0 %s' % \
            ("Stop ", test.serialNumber, test.name, my_nn, my_np, my_nt, time.asctime())

        print msg

    def periodicReport(self):
        "Report on current status of tasks"
        if len(self.running):
            terminal("CURRENTLY RUNNING %d tests:" % len(self.running),
                     " ".join([t.name for t in self.running]) )
        terminal("-"*80)
        terminal("CURRENTLY UTILIZING %d of %d processors." % (
            self.numberMaxProcessors - self.numProcsAvailable, self.numberMaxProcessors) )
        terminal("-"*80)

    def remainingCapacity(self):
        """How many nodes or processors are free? ?"""
        numberNodesRemaining = self.numNodes              - self.numberNodesExclusivelyUsed
        numberTestsRemaining = self.numberTestsRunningMax - self.numberTestsRunning

        #if SlurmProcessorScheduled.debugClass:
        #    print "DEBUG remainingCapacity ================================================================================================"
        #    print "DEBUG remainingCapacity self.numNodes                    =%d" % (self.numNodes)
        #    print "DEBUG remainingCapacity self.numberNodesExclusivelyUsed  =%d" % (self.numberNodesExclusivelyUsed)
        #    print "DEBUG remainingCapacity self.numProcsAvailable           =%d" % (self.numProcsAvailable)
        #    print "DEBUG remainingCapacity self.numberTestsRunningMax       =%d" % (self.numberTestsRunningMax)
        #    print "DEBUG remainingCapacity self.numberTestsRunning          =%d" % (self.numberTestsRunning)
        #    print "DEBUG remainingCapacity numberNodesRemaining             =%d" % (numberNodesRemaining)
        #    print "DEBUG remainingCapacity numberTestsRemaining             =%d" % (numberTestsRemaining)

        if self.exclusive == True and not "SLURM_JOBID" in os.environ.keys():
            if numberNodesRemaining != SlurmProcessorScheduled.remainingCapacity_numNodesReported:
                SlurmProcessorScheduled.remainingCapacity_numNodesReported = numberNodesRemaining

            if numberNodesRemaining < 1:
                if SlurmProcessorScheduled.canRunNow_debugClass:
                    if inspect.getframeinfo(inspect.currentframe()).lineno != SlurmProcessorScheduled.lastMessageLine:
                        SlurmProcessorScheduled.lastMessageLine = inspect.getframeinfo(inspect.currentframe()).lineno - 1
                        print "DEBUG remainingCapacity returning %d nodes available (A)" % 0
                return 0
            else:
                if SlurmProcessorScheduled.canRunNow_debugClass:
                    if inspect.getframeinfo(inspect.currentframe()).lineno != SlurmProcessorScheduled.lastMessageLine:
                        SlurmProcessorScheduled.lastMessageLine = inspect.getframeinfo(inspect.currentframe()).lineno - 1
                        print "DEBUG remainingCapacity returning %d nodes available (A)" % numberNodesRemaining
                return numberNodesRemaining
        else:
            if numberNodesRemaining < 1:
                if numberNodesRemaining != SlurmProcessorScheduled.remainingCapacity_numNodesReported:
                    SlurmProcessorScheduled.remainingCapacity_numNodesReported = numberNodesRemaining

                if numberNodesRemaining < 1:
                    if SlurmProcessorScheduled.canRunNow_debugClass:
                        if inspect.getframeinfo(inspect.currentframe()).lineno != SlurmProcessorScheduled.lastMessageLine:
                            SlurmProcessorScheduled.lastMessageLine = inspect.getframeinfo(inspect.currentframe()).lineno - 1
                            print "DEBUG remainingCapacity returning %d nodes available (B)" % 0
                    return 0
                else:
                    if SlurmProcessorScheduled.canRunNow_debugClass:
                        if inspect.getframeinfo(inspect.currentframe()).lineno != SlurmProcessorScheduled.lastMessageLine:
                            SlurmProcessorScheduled.lastMessageLine = inspect.getframeinfo(inspect.currentframe()).lineno - 1
                            print "DEBUG remainingCapacity returning %d nodes available (B)" % numberNodesRemaining
                    return numberNodesRemaining
            else:
                if self.numProcsAvailable != SlurmProcessorScheduled.remainingCapacity_numProcsReported:
                    SlurmProcessorScheduled.remainingCapacity_numProcsReported = self.numProcsAvailable

                if self.numProcsAvailable < 1:
                    if SlurmProcessorScheduled.canRunNow_debugClass:
                        if inspect.getframeinfo(inspect.currentframe()).lineno != SlurmProcessorScheduled.lastMessageLine:
                            SlurmProcessorScheduled.lastMessageLine = inspect.getframeinfo(inspect.currentframe()).lineno - 1
                            print "DEBUG remainingCapacity returning %d numProcsAvailable available (C)"%  0
                    return 0
                else:
                    if SlurmProcessorScheduled.canRunNow_debugClass:
                        if inspect.getframeinfo(inspect.currentframe()).lineno != SlurmProcessorScheduled.lastMessageLine:
                            SlurmProcessorScheduled.lastMessageLine = inspect.getframeinfo(inspect.currentframe()).lineno - 1
                            print "DEBUG remainingCapacity returning %d numProcsAvailable available (C)" % self.numProcsAvailable
                    return self.numProcsAvailable

# ################################################################################################################### #
#                                               End of File                                                           #
# ################################################################################################################### #
