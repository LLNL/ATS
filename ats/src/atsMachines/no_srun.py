#ATS:SequentialMachine  SELF noSrunMachine  1
#ATS:no_srun1           SELF noSrunMachine   1
#ATS:no_srun2           SELF noSrunMachine   2
#ATS:no_srun4           SELF noSrunMachine   4
#ATS:no_srun6           SELF noSrunMachine   6
#ATS:no_srun8           SELF noSrunMachine   8


import sys
import utils
from ats import machines, debug, atsut
from ats import log, terminal
from ats import configuration
from ats.atsut import RUNNING, TIMEDOUT

class noSrunMachine (machines.Machine):
    """
    Run without srun or batch.
    """

    def checkForAtsProc(self):
        rshCommand= 'ps uwww'
        returnCode, runOutput= utils.runThisCommand(rshCommand)
        theLines= runOutput.split('\n')
        foundAts= False
        for aline in theLines:
            #if 'srun' in aline and 'defunct' in aline:
            if 'salloc ' in aline:
                # NO ats running.
                return 0
            if 'bin/ats ' in aline:
                foundAts= True

        if foundAts:
            # Found ats running.
            return 1
        # NO ats running.
        return 0


    def getNumberOfProcessors(self):
        # Maximum number of processors available. Number of nodes times
        # number of procs per node.
        return self.numberMaxProcessors


    def examineOptions(self, options):
        "Examine options from command line, possibly override command line choices."
        # Grab option values.
        super(noSrunMachine, self).examineOptions(options)

        self.is_sequential = options.sequential

        if self.is_sequential:
            # Max number of tests to run at once, or max on a node, if multinode
            self.npMax = 1

            # Number of nodes to use
            self.numNodes = 1

        else:
            # Max number of tests to run at once, or max on a node, if multinode
            self.npMax = self.numberTestsRunningMax

            # Number of nodes to use
            self.numNodes = options.numNodes


        # Maximum number of processors available
        self.numberMaxProcessors = self.npMax * self.numNodes

        # Number of processors currently available
        self.numProcsAvailable = self.numberMaxProcessors

        # Maximum number of tests allowed to run at the same time.
        # This needs to be set for the manager for filter the jobs correctly.
        self.numberTestsRunningMax = self.numberMaxProcessors


    def addOptions(self, parser):

        "Add options needed on this machine."
        parser.add_option("--numNodes", action="store", type="int", dest='numNodes',
            default = 1,
            help="Number of nodes to use")
        pass

    def getResults(self):
        """I'm not sure what this function is supposed to do"""
        return machines.Machine.getResults(self)

    def label(self):
        return "noSrunMachine: %d nodes, %d processors per node." % (
            self.numNodes, self.npMax)

    def calculateCommandList(self, test):

        # Number of processors needed by one job.
        test.np = 1
        np = 1

        commandList = self.calculateBasicCommandList(test)

        if self.is_sequential:
            num_nodes = 1
        else:
            num_nodes = test.options.get('nn', -1)
        test.num_nodes = num_nodes

        tasks_per_node      = np / num_nodes
        test.tasks_per_node = tasks_per_node

        tasks_per_node_modulo = np % num_nodes
        if not tasks_per_node_modulo == 0:
            print test
            print "ERROR np=%i nn=%i" % (np, num_nodes)
            print "      Number_of_processes (%i) is not evenly divisible by number_of_nodes (%i)"  % (np, num_nodes)
            print "      %i modulo %i = %i " % (np, num_nodes, tasks_per_node_modulo)
            sys.exit(1)

        cpus_per_task_modulo = self.npMax % tasks_per_node
        if not cpus_per_task_modulo == 0:
            print test
            print "ERROR np=%i nn=%i tasks_per_node=%i cpus_on_node=%i" % (np, num_nodes, tasks_per_node, self.npMax)
            print "      Number of cpus_on_node (%i) is not evenly divisible by tasks_per_node (%i)" % (self.npMax, tasks_per_node)
            print "      %i modulo %i = %i " % (self.npMax, tasks_per_node, cpus_per_task_modulo)
            sys.exit(1)

#         test.cpus_per_task = 1

        return commandList


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
        np = max(test.np, 1)
        return self.numProcsAvailable >= np

    def noteLaunch(self, test):
        """A test has been launched."""
        np = max(test.np, 1)
        self.numProcsAvailable -= np


    def noteEnd(self, test):
        """A test has finished running. """
        np = max(test.np, 1)
        self.numProcsAvailable += np

    def periodicReport(self):
        "Report on current status of tasks"
        if len(self.running):
            terminal("CURRENTLY RUNNING %d tests:" % len(self.running),
                     " ".join([t.name for t in self.running]) )
        terminal("-"*80)
        terminal("CURRENTLY UTILIZING %d of %d processors." % (
            self.numberMaxProcessors - self.numProcsAvailable, self.numberMaxProcessors) )
        terminal("-"*80)
