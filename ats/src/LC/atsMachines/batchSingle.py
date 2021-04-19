#BATS:batchSingleStyleAlastor  batchSingle BatchSingleMachine 12
#BATS:batchSingle16            batchSingle BatchSingleMachine 16
#BATS:batchSingleStyleZeus     batchSingle BatchSingleMachine 8

from ats import machines, configuration, log, terminal, atsut, times 
import subprocess, sys, os, shlex, time
import utils, batchTemplate, lcBatch
from batch import BatchMachine

debug = configuration.debug

class BatchSingleMachine (BatchMachine):
    """The batch machine
    """
    def init (self): 
        super(BatchSingleMachine, self).init()
        
        self.maxBatchAllowed = 80
        self.batchContinueFilename = None
        self.timeNow= time.time()
        self.timeLastGetStatus= time.time()

    def addOptions(self, parser): 
        "Add options needed on this machine."

        super(BatchSingleMachine, self).addOptions(parser)

        parser.add_option("--maxBatchAllowed", action="store", type="int", dest='maxBatchAllowed', default = self.maxBatchAllowed, help="Batch only this many jobs at one time.")


    def examineOptions(self, options): 
        "Examine options from command line, possibly override command line choices."
        # Grab option values.    
        super(BatchSingleMachine, self).examineOptions(options)
        self.npMax= self.numberTestsRunningMax

        if self.npMax == 1: self.numNodes = 1
        self.numberTestsRunningMax = self.npMax * self.numNodes

        self.maxBatchAllowed = options.maxBatchAllowed
        self.batchFp = None

    def load(self, testlist): 
        """Receive a list of tests to possibly run."
           Assumes that status is already not CREATED if test could never run.
        """
        log("Start submitting batch jobs ........ Note, only a max of %s jobs will be submitted at a time. " % (self.maxBatchAllowed), echo=True)

        self.testlist = testlist
        
        self.running= []
        self.numberTestsRunning = 0
        for t in testlist:
            t.batchDic = {}
            t.batchDic['depends_on'] = None
            t.submitted = False
            t.batchstatus = "UNKNOWN"
            for d in t.dependents:
                d.batchDic = {}
                d.batchDic['depends_on'] = None
                d.submitted = False
                d.batchstatus = "UNKNOWN"

        self.run()

        return len(self.testlist)

    def run(self):
        """Run the tests in self.testlist. """
        timeStatusReport = time.time()        
        unfinished= self.testlist
        self.counterForCheckRunning = 0
        
        while unfinished:
            if not configuration.options.skip:
                time.sleep(3)
            unfinished= self.step() 

    def step(self):
        """Do one step of the loop, checking for tests that have finished and
           starting new ones. Return True until all tests done."""
# Did at least one running job finish? If so it changes the eligible list, both up and down.
# Resources may have been freed, and children of failures SKIPPED.
        
        self.timeNow= time.time()
        # batch system is slow... let's not check too often.  
        if (self.timeNow - self.timeLastGetStatus > 60):
            self.checkRunning()
            self.counterForCheckRunning += 1
            if (self.counterForCheckRunning==3):
                self.checkRunning(usePstat=1)
                self.counterForCheckRunning = 0
            self.periodicReport()
            self.timeLastGetStatus= time.time()

        
# It is possible that a job can be started. Try to do so.
# Note that this is not certain; for example all waiting jobs have np = 2 but only one
# processor available, so eligible is None.

        chosenTest = self.findNextTest()
        if chosenTest is None:
            mustStepAgain = False  #doesn't mean there are not "waiters"
        else:
            # We have a winner! Start it.
            mustStepAgain = True
            if self.startRun(chosenTest):
                self.running.append(chosenTest)
        
        return mustStepAgain or self.testlist
    # Explanation:
    #   It should be true that if nothing running we were able to start one if any left
    #   however, could have a system error that failed the launch of chosenTest so 
    #   we need to go around again and try others that are  waiting.
#### end of MachineCore

    def checkRunning(self, usePstat=0):
        "Find those tests still running. Check for timeout.Record finished tests."
        "Updates self.numberTestsRunning value.... step() checks this value later "
        "Should also update self.running"

        stillRunning = []
        N = 0
        for test in self.running:
             if usePstat==1:
                 done = self.getStatusUsingPstat(test)
             else:
                 done = self.getStatus(test)
             if not done:
                 stillRunning.append(test)
                 N += 1
             else:
                 test.recordOutput(test.hasFailed())
                    
        self.running = stillRunning
        self.numberTestsRunning = N

    def getStatus (self, test): #override if not using subprocess
        """
           Returns True if test done.
        """
        assert test.submitted is True

        try:
            testId= test.batchDic['jobid']
            # overtime is handled by the batch system...
            #        time is set during test submission.

# note next call may return None if status file inaccessible
            newStatus= lcBatch.checkStatusFile(test.batchDic['statusFilename'])

            if newStatus is not None and newStatus in [atsut.PASSED, atsut.FAILED]:
                self.testEnded(test, newStatus, "batch completed.")
                return True

        except KeyError:
            pass
        return False

    def getStatusUsingPstat (self, test): 
        """
           Returns True if test done.
        """
        assert test.submitted is True

        try:
            testId= test.batchDic['jobid']
            # overtime is handled by the batch system...
            #        time is set during test submission.

# note next call may return None if status file inaccessible
            cmdReturnCode, cmdOutput= utils.runThisCommand('pstat')

            if cmdReturnCode==0:
                if len(cmdOutput) > 1:
                    if testId not in cmdOutput:
                        newStatus= atsut.FAILED  # really the status is unknown... since the test ended without a status file created.
                        self.testEnded(test, newStatus, "batch unknown end status. Job may have been killed.")
                        return True
        except KeyError:
            pass
        return False

    def testEnded(self, test, status, message=None):
# job has exited
        #self.numberTestsRunning -= 1
        test.setEndDateTime()
        if message is None:
            message = test.elapsedTime()
        test.set(status, message)
        
        test.exited = True
        test.errname= test.batchDic['errorFilename']
        test.outname= test.batchDic['outputFilename']
        
        self.noteEnd(test)  #to be defined in children
        return True
    
    

        
    def findNextTest(self): 
        """Return the next test to run, or None if none can be run now. Called by step
           Check for resource conflicts with running tests.
           Using canRunNow and your own logic in prioritize, this probably need not be overwritten.
        """
        testToRun = None
        # First, remove submitted tests from the list
         
        newList= [t for t in self.testlist if t.submitted==False and t.status!=atsut.SKIPPED]
        self.testlist= newList

        if len(self.testlist)==0:
            if self.batchFp:
                self.batchFp.close()
            return None

          
        for t in self.testlist:
            if self.canRunNow(t):
                testToRun= t
                break
            
        return testToRun

    def startRun(self, test):
        """For interactive test object, launch the test object.
           Return True if able to start the test.
        """
        log('Batching #%d' % test.serialNumber,
                test.name, time.asctime(), echo=True)
        log.indent()
        if debug():
            log('For test #%d'% (test.serialNumber), ' in test directory', test.directory, echo=True)
        log.dedent()
        return self.launch(test)

    def launch (self, test): 
        """Start executable using a suitable command. Return True if able to do so.
           Call noteLaunch if launch succeeded."""        
        test.commandLine = self.calculateCommandLine(test)
        test.commandList = test.commandLine.split()[:]

        if debug() or configuration.options.skip:
            log.indent()
            log(test.commandLine, echo=True)
            log.dedent()
        if configuration.options.skip:
            test.set(atsut.SKIPPED, "--skip option")
            return False
        test.setStartDateTime()
        return self._launch(test)

    def _launch(self, test): #replace if not using subprocess
        "The subprocess part of launch."

        # submit this batch command.... uses popen
        resultFlag= batchTemplate.submit(test, test.commandLine)
        
        if self.batchContinueFilename is None:
            self.batchContinueFilename= os.path.join(log.directory, 'batch.log')
            self.batchFp = open(self.batchContinueFilename, 'w')
            
	if resultFlag:

            self.noteLaunch(test)

            # submit dependents...
            for d in test.dependents: 
                d.batchDic['depends_on']= ' -l depend=' + test.batchDic['jobid']
                self.startRun(d)

        else:
           test.set(atsut.SKIPPED, 'Error in submitting batch job.')

        return resultFlag
        

    def label(self):
        return " batchMachine: Max %d nodes (%d processors per node)." % (self.numNodes, self.npMax)

    def getSrunCommand(self, test): 
        commandList = self.calculateBasicCommandList(test)
        
        test.jobname = "t%d_%d%s" % (test.np, test.serialNumber, test.namebase)   #namebase is a space-free version of the name
        np = max(test.np, 1)
        numberOfNodesNeeded, r = divmod(np, self.npMax)
        if r: numberOfNodesNeeded += 1

        newCommand= ["srun", "--label", "-J", test.jobname, "--exclusive", "-N", "".join([str(numberOfNodesNeeded), "-", str(numberOfNodesNeeded)]), "-n", str(np), "-p", self.partition] + commandList
        return " ".join(newCommand)



    def calculateCommandLine(self, test): 
        """Prepare for run of executable using a suitable command. First we get the plain command
         line that would be executed on a vanilla serial machine, then we modify it if necessary
         for use on this machines.
        """
        np = max(test.np, 1)
        numberOfNodesNeeded, r = divmod(np, self.npMax)
        if r: numberOfNodesNeeded += 1

        # Write batch continue type file
        import tempfile
        
        import os
        batchDir= os.path.join(log.directory, "batchFiles")
        try:
            os.makedirs(batchDir)
        except OSError:
            pass


        commandForBatch= self.getSrunCommand(test)

        if not hasattr(test, 'batchDic'):
            test.batchDic= {}   


        test.batchDic['testPath']= test.directory
        test.batchDic['logPath']= log.directory
        test.batchDic['nodes']= numberOfNodesNeeded
        test.batchDic['numprocs']= self.npMax
        test.batchDic['command']= commandForBatch
        test.batchDic['bank']= self.bank
        test.batchDic['partition']= self.partition

        batchTemplate.buildBatchDic(test=test, 
                                    maxtime=test.timelimit, 
                                    constraints=self.constraints, 
                                    gres=self.gres, 
                                    standby=self.standby,
                                    hostname= self.hostname)

        
        test.batchDic['errorFilename']= os.path.join(batchDir, test.batchDic['jobname'] + '.err')
        test.batchDic['outputFilename']= os.path.join(batchDir, test.batchDic['jobname'] + '.out')
        test.batchDic['statusFilename']= os.path.join(batchDir,  test.batchDic['jobname'] + '.status')

        
        batchText= batchTemplate.template % test.batchDic

        batchFilenameToUse= os.path.join(batchDir, test.batchDic['jobname'] + ".bat")

        test.batchDic['scriptFilename']= batchFilenameToUse
        batchTemplate.writeLines(batchFilenameToUse, batchText)

        batchCommand = 'msub ' + batchFilenameToUse              # msub
        if test.batchDic['depends_on'] is not None:
           batchCommand= 'msub ' + test.batchDic['depends_on'] + " " + batchFilenameToUse

        return batchCommand

    #------------------------------------------------------------------------------
    def getFinalAtsArgs(self, numberOfNodesNeeded):
        # init values before checking original argv line
        newAtsLine= ""
        pos= 0

        batchOptionsToIgnore= ['partition', 'batchPartition', 'maxBatchAllowed', 'constraints', 'gres', 'batchPartition', 'batchTimeLimit', 'batchNumNodes', 'bank', 'srunOnlyWhenNecessary', 'numNodes', 'n']

        # Use and fix ats line to work with new batch ats file
        passNextArg = 0
        for thisOp in sys.argv[:-1]:
            if passNextArg==1:
                passNextArg= 0
                if not thisOp.startswith('-'):
                    continue
            tempOp= thisOp
            try:
                opVal= thisOp.split('=')[0].split()[0]
                opVal= opVal.lstrip('-')
            except:
                opVal= thisOp
            if opVal in batchOptionsToIgnore:
                tempOp= ''
                if "=" not in thisOp:
                    passNextArg= 1

            # Add this to the options
            if pos==1:
                newAtsLine= newAtsLine + " --allInteractive "
                newAtsLine= newAtsLine + " --numNodes " + str(numberOfNodesNeeded) + " "
            pos += 1

            newAtsLine= newAtsLine + " " + tempOp
        
        return newAtsLine

    
    def canRun(self, test):
        """Is this machine able to run the test interactively when resources become available? 
           If so return ''.  Otherwise return the reason it cannot be run here.
        """
        # Comment out, filtering will be used instead.

        #test.requiredNP= max(test.np,1)
        #test.numberOfNodesNeeded, r = divmod(test.requiredNP, self.npMax)
        #if r: test.numberOfNodesNeeded += 1
        
        #if test.requiredNP > (self.npMax*self.numNodes):
        #    return "Batch max num nodes set to %d. Too many nodes required, %d." % (self.numNodes, test.numberOfNodesNeeded)

	return ''

    def canRunNow(self, test): 
        "Is this machine able to run this test now? Return True/False"
        
	if self.maxBatchAllowed <= self.numberTestsRunning:   
	    return False
        return True

    def noteLaunch(self, test):
        """A test has been launched."""

        test.set(atsut.BATCHED, " batch job submitted ")
        test.submitted = True
        self.numberTestsRunning += 1

        fromTestDic= {'testNp': test.np, 'testName': test.name, 'testLevel': test.level, 'testPath':test.directory, 'testNameBase': test.namebase}
        fromTestAndBatchDic= dict( fromTestDic.items() + test.batchDic.items() )
        summaryText= batchTemplate.summaryTemplate % fromTestAndBatchDic
        
        print >>self.batchFp, summaryText
        print >>self.batchFp, "# BEGIN test continuation info "
        print >>self.batchFp, self.continuation(test)
        print >>self.batchFp, "# END test continuation info "


        
    def continuation(self, test):
        #representation for the continuation file
        if test.depends_on is None:
            result = 'test%d = test( ' % test.serialNumber
        else:
            result = 'test%d = testif(test%d,\n    ' \
               %(test.serialNumber, test.depends_on.serialNumber)
        result += "executable = " + \
                  repr(test.executable.path) 
        result += ",\n   " + "clas = " + repr(test.clas)
        for k in test.options.keys():
            if k in ["executable", "clas", "script"]:
                continue

            result += (",\n   " + k + " = " + repr(test.options[k]))
        return result + ')'


    def noteEnd(self, test):
        """A test has finished running. """
        if debug():
            log("Finished %s, now running %d tests" % \
                (test.name, self.numberTestsRunning), echo=True)

        self.numberTestsRunning -= 1



    def periodicReport(self): 
        "Report on current status of tasks"
        # Let's also write out the tests that are waiting ....
        super(BatchSingleMachine, self).periodicReport()
        
        currentEligible=  [ t.name for t in self.testlist if not t.submitted ]
        lenEl= len(currentEligible)
        if lenEl > 1:
            msg= "WAITING TO BATCH (" + str(lenEl) +  "): " + " ".join(currentEligible[:5])
            if lenEl > 5:
                msg= msg + "..."
            msg= msg + "  [note: all batch tests need to be batched before interactive tests can preceed]"
            terminal(msg)
        

