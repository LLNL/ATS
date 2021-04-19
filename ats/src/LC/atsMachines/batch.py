#BATS:batch SELF BatchMachine 1
from ats import machines, configuration, log, terminal, atsut, times
import subprocess, sys, os, shlex, time
import utils, batchTemplate, lcBatch

debug = configuration.debug

class BatchMachine (machines.Machine):
    """The batch machine
    """
    def init (self): 
        self.npMax= self.numberTestsRunningMax
        self.timelimit= 30 # minutes
        
        
    def addOptions(self, parser): 
        "Add options needed on this machine."

        parser.add_option("--batchHostName", action="store", type="string", dest='hostname', default = '',  help = "host for msub")

        parser.add_option("--batchPartition", action="store", type="string", dest='batchPartition', default = 'pbatch',  help = "Partition in which to run jobs with np > 0")


        parser.add_option("--batchNumNodes", action="store", type="int", dest='batchNumNodes', default = 8, help="Batch using this max number of nodes.")
        parser.add_option("--constraints", action="store", type="string", dest='constraints', default = None, help = "Batch on this machine.")

        parser.add_option("--batchBank", action="store", type='string', dest='batchBank', default='wbronze', help="Batch using this bank")

        parser.add_option( '--gres', action='store', type='string', dest='gres', default=None, help="Job requires the specified parallel Lustre file system(s). Valid labels are lscratcha, lscratchb, lscratch1 ... The ignore descriptor can be used for jobs that don't require a parallel file system, enabling them to be scheduled even if there are parallel file system problems. -BATCH")

	parser.add_option('--standby', action='store_true', dest='standby', help='The job will be submitted as a standby job. -BATCH')


    def examineOptions(self, options): 
        "Examine options from command line, possibly override command line choices."
        # Grab option values.    
        super(BatchMachine, self).examineOptions(options)

        self.numNodes = options.batchNumNodes
        self.partition = options.batchPartition

        self.hostname = options.hostname
        self.constraints = options.constraints
        self.bank = options.batchBank
        self.gres = options.gres
        self.standby = options.standby

        self.constraints = options.constraints
        # constraints - get non-digit part of node name
        if self.constraints is None:
            import socket, re
            nodeName = socket.gethostname()
            wordpat = re.compile('(^[a-zA-Z_]*)(\d*)').search
            self.constraints = wordpat(nodeName).group(1)

        self.timelimit= options.timelimit


