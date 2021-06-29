#ATS:winParallel SELF WinMachine 8
#ATS:darwin machines Machine -2
#ATS:win32 SELF WinMachine 1
#BATS:batchsimulator machines BatchSimulator 1200

import os
from ats import machines, terminal
from ats.atsut import RUNNING, TIMEDOUT

class WinMachine (machines.Machine):
    "Windows machine."
    def init (self) :
        self.npMax = 1
        self.numNodes = 1

        self.numberMaxProcessors = 1
        self.numberTestsRunningMax = 1
        self.numProcsAvailable = 1
        self.nompi = False

    def getNumberOfProcessors(self) :
        return self.numberMaxProcessors

    def split(self, clas):
        return [clas]

    def addOptions(self, parser):
        " Not used by Windows but added just for compatability."
        parser.add_option("--partition", action="store", type="string", dest='partition',
            default = 'pdebug',
            help = "Partition in which to run jobs with np > 0")

        parser.add_option("--numNodes", action="store", type="int", dest='numNodes',
           default = -1,
           help="Number of nodes to use")

        parser.add_option("--nompi", action="store_true", dest='nompi',
           default = False,
           help="Run executables on nompi processor")

        parser.add_option("--oversubscribe", action="store", type='int', dest='oversubscribe',
           default = 1,
           help="Multiplier to number of processors to allow oversubscription of processors")

        parser.add_option("--mpiexe", action="store", type='string', dest='mpiexe',
                          default = "",
                          help="Location to mpiexe")


    def examineOptions(self, options):
        "Examine options from command line, possibly override command line choices."
        # Grab option values.
        super(WinMachine, self).examineOptions(options)
        self.npMax= self.numberTestsRunningMax

        if options.numNodes==-1:
            if 'NUMBER_OF_PROCESSORS' in os.environ:
                options.numNodes= int(os.environ['NUMBER_OF_PROCESSORS'])

            else:
                options.numNodes= 1
        self.numNodes= options.numNodes
        self.npMax = options.oversubscribe

        # subtract
        if self.numNodes > 1 :
            self.numberMaxProcessors = self.npMax*self.numNodes - 1
        else :
            self.numberMaxProcessors = self.npMax
        self.numberTestsRunningMax = self.numberMaxProcessors
        self.numProcsAvailable = self.numberMaxProcessors
        self.mpiexe = options.mpiexe
        self.nompi = options.nompi


    def calculateCommandList(self, test):
        """Prepare for run of executable using a suitable command. First we get the plain command
         line that would be executed on a vanilla serial machine, then we modify it if necessary
         for use on this machines.
        """
        # Will call machines's calculateBasicCommandList().
        commandList = self.calculateBasicCommandList(test)

        if self.nompi : test.np = 1
        if test.np > 1 :
            mpiexe = self.mpiexe
            if self.npMax > 1 :
                mpiCommand = [mpiexe, "-affinity", "-env", "MPICH_PROGRESS_SPIN_LIMIT", "16", "-n", "%d" % test.np]
            else :
                mpiCommand = [mpiexe, "-affinity", "-n", "%d" % test.np]
            commandList =  mpiCommand + commandList

        return commandList

    def canRun(self, test):
        return ''

    def canRunNow(self, test):
        "Is this machine able to run this test now? Return True/False"
        if self.nompi : test.np = 1
        np = max(test.np, 1)
        if self.nompi : return self.numProcsAvailable >= 1
        else : return self.numProcsAvailable >= np


    def noteLaunch(self, test):
        """A test has been launched."""
        if self.nompi : self.numProcsAvailable -= 1
        else :
            np = max(test.np, 1)
            self.numProcsAvailable -= np



    def noteEnd(self, test):
        """A test has finished running. """
        if self.nompi : self.numProcsAvailable += 1
        else :
            np = max(test.np, 1)
            self.numProcsAvailable += np

    def periodicReport(self):
        "Report on current status of tasks"
        terminal("-"*80)
        terminal("CURRENTLY UTILIZING %d of %d processors." % (
            self.numberMaxProcessors - self.numProcsAvailable, self.numberMaxProcessors))
        terminal("-"*80)

    def kill(self, test):
        "Final cleanup if any."
        import subprocess

        if test.status is RUNNING or test.status is TIMEDOUT:
            # It is possible that the job stopped on its own
            # so OK
            try:
                test.child.terminate()
            except:
                pass
