import time
from ats import debug, log, machines
from ats.atsMachines import utils

class LCMachineCore (machines.Machine):

    def init (self):
        # let's not call squeue too often..
        self.lastTimeSqueueCalled= time.time() # note the time when 'squeue -s' command used
        self.lastSqueueResult= None


    def kill(self, test):
        "Final cleanup if any."

        if not hasattr(test, 'jobname'):
            return

        for killTimes in range(0,1):

            if self.lastSqueueResult is None or ( (time.time() - self.lastTimeSqueueCalled) > 60):   # in seconds
                self.lastSqueueResult= utils.getAllSlurmStepIds()
                self.lastTimeSqueueCalled= time.time()    # set time
                #if debug():
                #    log("---- LCMachineCore::kill(), stepIdLines  %s ----\n" %  (self.lastSqueueResult) )

            killAttempted= False
            for line in self.lastSqueueResult:
                if test.jobname in line:
                    scancelCommand= 'scancel ' + line.split()[0]
                    if debug():
                        log("---- LCMachineCore::kill: %s" %  (scancelCommand), echo=True)
                        #log("---- LCMachineCore::kill, test name: %s using: %s" %  (test.jobname, scancelCommand), echo=True)
                        #log("---- LCMachineCore::kill, line: %s" %  (line), echo=True)
                    utils.runThisCommand(scancelCommand)
                    #time.sleep(2)
                    killAttempted= True
                    break

            if not killAttempted:
                break

            if debug():
                log("---- LCMachineCore::kill, CALLED AGAIN %s test name: %s %s" %  ((killTimes+1), test.jobname, test.serialNumber), echo=True)
            time.sleep(1)

            self.lastSqueueResult= None
            time.sleep(2)
            #log("---- LCMachineCore::kill(), check line: %s" %  (line), echo=True)
