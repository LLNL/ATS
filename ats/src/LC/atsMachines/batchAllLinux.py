#BATS:batchAllZeus  batchAllLinux BatchAllMachine 8
#BATS:batchAllChaos  batchAllLinux BatchAllMachine 16
#BATS:batchAllAlastor  batchAllLinux BatchAllMachine 12

#BATS:chaos_3_x86_64_ib batchAllLinux BatchAllMachine 8
#BATS:chaos_4_x86_64_ib batchAllLinux BatchAllMachine 8
#BATS:chaos_3_x86_elan3 batchAllLinux BatchAllMachine 2

from ats import machines, configuration, log, atsut, times
from ats.times import Duration

import subprocess, sys, os, shlex, time, socket, re
import utils, batchTemplate
from batch import BatchMachine


debug = configuration.debug

class BatchAllMachine (BatchMachine):
    """The batch machine
    """
    def init (self): 
        super(BatchAllMachine, self).init()

    def addOptions(self, parser): 
        "Add options needed on this machine."
        super(BatchAllMachine, self).addOptions(parser)
        
        parser.add_option("--batchTimeLimit", action="store", type="string", dest='batchTimeLimit', default = "2h",  help = "Set the batch time limit. The value may be given as a digit followed by an s, m, or h to give the time in seconds, minutes (the default), or hours.")



    def examineOptions(self, options): 
        "Examine options from command line, possibly override command line choices."
        # Grab option values.    
        super(BatchAllMachine, self).examineOptions(options)
        self.npMax= self.numberTestsRunningMax

        if self.npMax == 1: self.numNodes = 1
        self.numberTestsRunningMax = self.npMax * self.numNodes

        self.timelimit= Duration( options.batchTimeLimit )

    def load(self, testlist): 
        """Receive a list of tests to possibly run.
           Submit the set of tests to batch.
        """

        self.testlist = testlist
        batchFilename= 'allbatch.ats'
        
        # Let's write out a batch continue file... with these tests
        self.batchAtsFilename= os.path.join(log.directory, batchFilename)
        fc = open(self.batchAtsFilename, 'w')
        for t in testlist:
            t.batchDic = {}
            print >> fc, "# Write test "
            print >> fc, self.continuation(t)
            for d in t.dependents: 
                if d in testlist:
                    continue
                print >> fc, "# Write dependents.. "
                print >> fc, self.continuation(d)
                np= max(self.npMax, d.np)
                d.submitted= True     # change the status 

            #print >>fc, t.continuation()
        fc.close()

        # Figure args for atsb call
        finalArgs= self.getFinalAtsArgs()
        theCommand= finalArgs + " " + batchFilename
        # Add env info
        envCommand= ""
        if os.environ.has_key('MACHINE_TYPE'):
           envCommand += "setenv MACHINE_TYPE " +  os.environ['MACHINE_TYPE'] 
        if os.environ.has_key('BATCH_TYPE'):
           envCommand += "; setenv BATCH_TYPE " +  os.environ['BATCH_TYPE'] 
        theCommand=  envCommand + " ; " + theCommand

        # Then submit ats under batch to run these tests
	# Setup some batch related values first.

        # quality of service, ie. 
        # MSUB -l qos=standby
        # MSUB -l qos=expedite
        qosLine= ""
        if self.standby:
            qosLine= "#MSUB -l qos=standby"

        # Specifies parallel Lustre file system.
        gresLine= ""
        if self.gres is not None:
            gresLine= "#MSUB -l gres=" + self.gres

        fromBatchDic= {'jobname': batchFilename,
                      'bank': self.bank,
                      'partition': self.partition,
                      'constraints':  self.constraints,
                      'nodes': self.numNodes,
                      'numprocs': self.npMax,
                      'totalnumprocs': (self.npMax * self.numNodes),        # total MPI tasks count
                      'timelimit': times.timeSpecToSec(self.timelimit),  # in seconds
                      'errorFilename': os.path.join(log.directory, 'batch.out2'),
                      'outputFilename': os.path.join(log.directory, 'batch.out1'),
                      'hostname':self.hostname,
                      'gres':gresLine,
                      'qos': qosLine,
                      'startTime':'date +"Start Time: %Y/%m/%d %T"',
                      'testPath':log.directory,
                      'command': theCommand,
                      'statusFilename':os.path.join(log.directory, 'batch.status'),
                      'endTime':'date +"End Time: %Y/%m/%d %T"' }

        batchSubmitText= batchTemplate.template % fromBatchDic

        batchFilenameToUse= os.path.join(log.directory, 'batchToSubmit' + ".bat")
        batchTemplate.writeLines(batchFilenameToUse, batchSubmitText)

        self.jobid= batchTemplate.submitBatchScript(batchFilenameToUse)

        # Once submitted... save the jobid... display later.
 
        return len(self.testlist)

    def label(self):
        return " batchAllLinux: Max %d nodes (%d processors per node)." % (self.numNodes, self.npMax)

    def getFinalAtsArgs(self):
        # init values before checking original argv line
        newAtsLine= ""
        pos= 0

        batchOptionsToIgnore= ['partition', 'batchPartition', 'maxBatchAllowed',  'constraints', 'gres', 'batchPartition', 'batchTimeLimit', 'batchNumNodes', 'bank', 'srunOnlyWhenNecessary', 'numNodes', 'n', 'removeSrunStep']

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


    def continuation(self, test):
        #representation for the continuation file
        if test.depends_on is None:
            result = 'test%d = test( ' % test.serialNumber
        else:
            result = 'test%d = testif(test%d,\n    ' \
               %(test.serialNumber, test.depends_on.serialNumber)
        result += "executable = " + \
                  repr(test.executable.path) 
        #result += ",\n   " + "clas = " + repr(test.clas)
        for k in test.options.keys():
            #if k in ["executable", "script", "clas"]:
            #if k in ["executable", "clas"]:
            if k in ["executable"]:
                continue
            else:
                if k == 'script':
                   if test.directory not in test.options[k]:
                      test.options[k]= os.path.join(test.directory, test.options[k])
                result += (",\n   " + k + " = " + repr(test.options[k]))
        return result + ')'


