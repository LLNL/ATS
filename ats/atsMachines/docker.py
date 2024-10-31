#ATS:docker SELF Docker 1

import os
from ats import machines, terminal
from ats.atsut import RUNNING, TIMEDOUT

class Docker (machines.Machine):
    "Typical Linux machine."
    def init (self) :
        self.npMax = 1

        self.numberTestsRunningMax = 1
        self.numProcsAvailable = 1
        self.nompi = False

    def getNumberOfProcessors(self) :
        return self.npMax

    def split(self, clas):
        return [clas]

    def addOptions(self, parser):
        " General purpose machine file. Useful for testing in Linux containers."

        parser.add_option("--nompi", action="store_true",
                          default = False,
                          help="Run executables on nompi processor")

        parser.add_option("--mpiexe", type=str,
                          default = None,
                          help="Location to mpiexe")

        parser.add_option("--launchCmds", type=str,
                          default = None,
                          help="""
                          Any additional flags to add when launching a test.
                          For example,
                          --launchCmds '--affinity' --mpiexe mpirun
                          would launch each test as
                          mpirun --affinity ...
                          """


    def examineOptions(self, options):
        "Examine options from command line, possibly override command line choices."
        # Grab option values.
        super(Docker, self).examineOptions(options)
        # machines.py sets this
        self.npMax = self.numberTestsRunningMax
        self.mpiexe = options.mpiexe
        self.mpiexe = options.mpiexe
        self.nompi = options.nompi
        if (self.npMax < 2 and self.mpiexe):
            terminal("WARNING: npMax should be > 1 to use mpiexe")
        if (self.mpiexe and self.nompi):
            terminal("WARNING: Setting --nompi and --mpiexe contradicts")

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
            mpiCommmand = [mpiexe, "-n", str(test.np)]
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
        if len(self.running):
            terminal("CURRENTLY RUNNING %d tests:" % len(self.running),
                     " ".join([t.name for t in self.running]) )
        terminal("-"*80)
        terminal("CURRENTLY UTILIZING %d of %d processors." % (
            self.npMax - self.numProcsAvailable, self.npMax))
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
