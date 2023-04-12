import os, sys, subprocess
from ats import debug, SYS_TYPE

_myDebugLevel= 10

def utilDebugLevel(value=None):
    "Return the _myDebugLevel flag; if value given, set it."
    global _myDebugLevel
    if value is None:
        return _myDebugLevel
    else:
        _myDebugLevel = int(value)

#--------------------------------------------------------------------------

def tryint(s):
    try:
        return int(s)
    except:
        return s

def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    import re
    return [ tryint(c) for c in re.split('([0-9]+)', s) ]

# Used by getAllHostnames()
def sort_nicely(l):

    """ Sort the given list in the way that humans expect.
    """
    l.sort(key=alphanum_key)


#--------------------------------------------------------------------------

def getAllHostnames():

    cmd= "srun hostname"
    if SYS_TYPE.startswith('aix'):
        cmd= "poe hostname"
    elif SYS_TYPE.startswith('bgqos'):
        cmd= "hostname"

    if debug() >= utilDebugLevel():
        print("in getAllHostnames() ---- running command:  %s" % cmd)
    allHostname= []
    try:
        import subprocess
        import getpass

        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, text=True)
        stdout_value = proc.communicate()[0]

        if (len(stdout_value)==0):
            return allHostname

        theLines = stdout_value.split('\n')

        for aline in theLines:
            aline= "spacer:" + aline
            oneHostname = aline.split(":")[-1]
            if oneHostname != '':
                if oneHostname not in allHostname:
                    allHostname.append(oneHostname)


        if debug() >= utilDebugLevel():
            print("DEBUG: before sort %s" % allHostname)
        sort_nicely(allHostname)
        if debug() >= utilDebugLevel():
            print("DEBUG: after sort %s" % allHostname)

    except:
        print("ATS ERROR: in utils.py getAllHostnames:%s" % sys.exc_info()[0])
        return allHostname
    return allHostname



#------------------------------------------------------------------------------
def setStepNumWithNode(inMaxStepNum):
# inMaxStepNum - For a group of nodes, the max step number is the max number of nodes minus 1.
# Returns:  The stepid used to obtain the nodes and for each step, the node assoicated with it.
#           returns --> stepid, nodeStepDic[node]=stepNum

    return  getNodeAndStepIdAssociatedWithStepNumberLinux(inMaxStepNum)

#------------------------------------------------------------------------------

def getUnusedNode(inNodeAvailTotalDic, inNodeList, desiredAmount, maxProcsPerNode, inNodeStepNumDic, inOldStep):
# inNodeList - List of nodes available to use.
# desiredAmount - The number of processors needed.
# inNodeStepNumDic - Dic of (stepNum, node) association.
# inStepId - The step id used.
#
# Returns the step number that is qualified to provide the desired number of processors needed.
# If no steps are valid, None is returned.
#         returns -> stepNum
#
    import subprocess
    import getpass

    #print "DEBUG SAD 107"
    #print inNodeAvailTotalDic
    #print inNodeList
    #print desiredAmount
    #print maxProcsPerNode
    #print inNodeStepNumDic
    #print inOldStep
    #sys.exit(0)

    maxCount= len(inNodeList)

    stepNodeDic= {v: k for k, v in inNodeStepNumDic.items()}

    nodeAvailDic= inNodeAvailTotalDic


    stepNum= 0 #start with first node
    import math
    desiredAmount= max(desiredAmount, 1)  # should desire at least 1 processor
    numNodesToUse= max(1, int(math.ceil(float(desiredAmount)/float(maxProcsPerNode))) )

    #
    # Start by requesting the minimum number of nodes.  Then if a set of those which
    # has enough processors is not available, bump up the number of nodes by 1 and
    # try again.
    #
    # IE, this helps when the machine has resources like:
    #    rzalastor10=3 rzalastor11=3 rzalastor12=3 rzalastor13=3
    # And you are trying to see if you can run a job with more than 3 processors
    #

    while numNodesToUse <= maxCount:

        #-------------------------------------------
        # Find all the combinations
        #-------------------------------------------
        if debug() >= utilDebugLevel():
            print("DEBUG: in utils::getUnusedNode() -- numNodesToUse= %s" % numNodesToUse)

        comboList= []

        for ii in range (stepNum, maxCount):
            totalValue= ii
            tempCombo= []
            for jj in range(numNodesToUse):
                tempCombo.append(totalValue)
                if totalValue < maxCount-1:
                    totalValue += 1
                else:
                    break
            if len(tempCombo)==numNodesToUse:
                comboList.append(tempCombo)

        if debug() >= utilDebugLevel():
            print("DEBUG: in utils::getUnusedNode() -- desiredAmount= %s" % desiredAmount)
            print("DEBUG: in utils::getUnusedNode() -- comboList= %s" % comboList)

        #-------------------------------sum all the combo
        allSavedStep= []
        for eachCombo in comboList:
            totalAvail= 0
            savedStep= -1

            for astep in eachCombo:
                if savedStep==-1:
                    savedStep= astep    # note the first step
                totalAvail= totalAvail + nodeAvailDic[ stepNodeDic[str(astep)] ]
                if debug() >= utilDebugLevel():
                    print("eachCombo= %s astep=%s totalAvail=%s" % (eachCombo, astep, totalAvail))
                sys.stdout.flush()
                if totalAvail >= desiredAmount:
                    if savedStep != inOldStep:     # Do not submit to the same node twice in a row
                        if debug() >= utilDebugLevel():
                            print("returned savedStep= %s" % savedStep)
                            print("returned numNodesToUse= %s" % numNodesToUse)
                        return nodeAvailDic, savedStep, numNodesToUse
                    else:
                        allSavedStep.append(savedStep)


        if len(allSavedStep) > 0:
            if debug() >= utilDebugLevel():
                print(" ---- allSavedStep= %s" % allSavedStep)
                print(" ---- returned savedStep= %s" % savedStep)
                print(" ---- returned numNodesToUse= %s" % numNodesToUse)
            return nodeAvailDic, allSavedStep[0], numNodesToUse

        stepNum = 0
        numNodesToUse += 1

    return nodeAvailDic, None, 0



#------------------------------------------------------------------------------
#
# Use this one if not using -N and -r option and letting slurm round
# robin the processes as needed
#
# 2012/11/20 SAD Modified to avoid assumptions about how processes are mapped
#                to nodes.  This may overdelete the cpus when > 1 node is
#                needed for a test, but will avoid over-subscribing nodes.
#
#------------------------------------------------------------------------------
def removeFromUsedTotalDicNoSrun(inNodeAvailDic, inNodeStepNumDic, inMaxProcsPerNode, inAmountToDelete, inNodeList):

    #print "SAD DEBUG removeFromUsedTotalDicNoSrun Begin inNodeAvailDic follows"
    #print inNodeAvailDic

    stepNodeDic= {v: k for k, v in inNodeStepNumDic.items()}

    amountLeft= max(inAmountToDelete, 1)

    aLen = len(inNodeAvailDic)

    while amountLeft > 0:
        aStep= 0
        for ii in range(0, aLen):
            tempToDelete= min(1, inNodeAvailDic[ stepNodeDic[str( aStep )] ])
            inNodeAvailDic[ stepNodeDic[str( aStep )] ] -= tempToDelete
            amountLeft -= tempToDelete
            aStep = (aStep + 1) % aLen
            if amountLeft<=0:
                break

    #print "SAD DEBUG removeFromUsedTotalDicNoSrun End inNodeAvailDic follows"
    #print inNodeAvailDic

    return inNodeAvailDic


#------------------------------------------------------------------------------
#
# Used if the -N and -r options are being used
#
#------------------------------------------------------------------------------
def removeFromUsedTotalDic (inNodeAvailDic, inNodeStepNumDic, inMaxProcsPerNode, inFirstStep, inAmountToDelete, inNumberOfNodesNeeded, inNumNodesToUse, inSrunRelativeNode, inStepId, inNodeList):

    stepNodeDic= {v: k for k, v in inNodeStepNumDic.items()}

    amountLeft= max(inAmountToDelete, 1)

    while amountLeft > 0:
        aStep= inFirstStep
        for ii in range(0, inNumNodesToUse):
            tempToDelete= min(1, inNodeAvailDic[ stepNodeDic[str( aStep )] ])
            inNodeAvailDic[ stepNodeDic[str( aStep )] ] -= tempToDelete
            amountLeft -= tempToDelete
            aStep = (aStep + 1) % len(inNodeStepNumDic)
            if amountLeft<=0:
                break

    return inNodeAvailDic


#------------------------------------------------------------------------------

def findAvailableStep(inNodeList, inNodeAvailTotalDic, inNodeStepNumDic,
                      inMaxProcsPerNode, inDesiredAmount,  oldStep=0):

    newStep= None

    # SAD DEBUGGING,
    nodeAvailTotalDic, newStep, numNodesToUse= getUnusedNode(inNodeAvailTotalDic, inNodeList, inDesiredAmount, inMaxProcsPerNode, inNodeStepNumDic, oldStep)

    if newStep is None:
            # update nodeAvailTotalDic then call getUnusedNode
        nodeAvailTotalDic= usingRshFindTotalProcessorsAvail(inNodeAvailTotalDic, inNodeStepNumDic, inMaxProcsPerNode)
        nodeAvailTotalDic, newStep, numNodesToUse= getUnusedNode(nodeAvailTotalDic, inNodeList, inDesiredAmount, inMaxProcsPerNode, inNodeStepNumDic, oldStep)

    return nodeAvailTotalDic, newStep, numNodesToUse


#------------------------------------------------------------------------------
def checkForSrunDefunct(anode):
    rshCommand= 'rsh ' +  anode + ' ps u'
    returnCode, runOutput= runThisCommand(rshCommand)

    theLines = runOutput.split('\n')
    for aline in theLines:
        if 'srun' in aline and 'defunct' in aline:
            return 1

    return 0

#------------------------------------------------------------------------------
#
# This is the routine which queries the system to find which nodes
# have processors which are not being used.
#
# The 'rsh' command looks something like:
#
# rsh rzalastor8 ps -ef | grep $USER | grep -v "ps -ef"| wc
#
# This command needs to filter out tasks which are not testing jobs, such as
#
# user@rzalastor3/ > rsh rzalastor34 ps -ef | grep $USER | grep -v "ps -ef"
# user    3647 14041  0 16:43 pts/0    00:00:00 /usr/gapps/ats/Python-2.7.3/chaos_5_x86_64_ib/bin/python /g/g16/user/Project/wrapper_ats/atswrapper_front_end --exec=code.nightly deck.inp
# user    3648  3647  0 16:43 pts/0    00:00:00 /usr/gapps/ats/Python-2.7.3/chaos_5_x86_64_ib/bin/python /g/g16/user/Project/wrapper_ats/atswrapper_back_end --exec=code.nightly deck.inp
# user   14041 14037  0 15:47 pts/0    00:00:00 /bin/bash
#
# In addition, a simple 'wc' of these does not work, as the command returns empty lines
# which are counted as processes if justing doing a 'wc'o
#
# So save the output and then loop through them, which will help us fine
# tune this routine in the future as well.
#
#------------------------------------------------------------------------------
def usingRshFindTotalProcessorsAvail (inNodeList, inStepNumNodeNameDic, maxProcsPerNode):
    taskTotal= {}
    for anode in inNodeList:
        taskTotal[anode]= 0
    import time
    time.sleep(1)
    for anode in inNodeList:

        rshCommand= 'rsh ' +  anode + ' ps -ef | grep $USER | grep -v "ps -ef" | grep -v "/usr/apps/ats.*exec" | grep -v "/usr/gapps/ats.*exec" | grep -v "/bin/csh" | grep -v "/bin/bash" | grep -v " bash" | grep -v "/usr/bin/xterm" | grep -v "/bin/ksh" | grep -v "grep $USER" | grep -v "srun .*label" | grep -v "srun.*defunct" | grep -v "pts/0.*-sh" | grep -v "tee temp" '
        returnCode, runOutput= runThisCommand(rshCommand)
        runLines = (line for line in runOutput.split(os.linesep))
        numProcsUsed = 0
        for aLine in runLines:
            #print "DEBUG SAD 346: '%s'" % aLine
            if (len(aLine) > 10):
                # print "DEBUG SAD 304 usingRshFindTotalProcessorsAvail I think the following is a test process: \n\t%s" % aLine
                numProcsUsed += 1
        taskTotal[anode]= max(0, maxProcsPerNode - numProcsUsed)

    # SAD DEBUGGING LINES FOLLOW
    #msg = "Processors Available by rsh:"
    #for key, val in sorted(taskTotal.items()):
    #    msg = msg + " " + key + "=" + str(val)
    #print "            %s" % msg
    #sys.exit(0)

    return taskTotal

#------------------------------------------------------------------------------
def getNodeAndStepIdAssociatedWithStepNumberLinux(inMaxStep):
#
# Returns the node and step id associated with the step number.
#       returns -> node, stepid
    #--------------------------------------------------
    # Determine who the user is..
    #--------------------------------------------------
    cmd= "whoami"
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, text=True)

    return taskTotal

#------------------------------------------------------------------------------
def getNodeAndStepIdAssociatedWithStepNumberLinux(inMaxStep):
#
# Returns the node and step id associated with the step number.
#       returns -> node, stepid
    #--------------------------------------------------
    # Determine who the user is..
    #--------------------------------------------------
    cmd= "whoami"
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, text=True)

    stdout_value = proc.communicate()[0]
    if (len(stdout_value)==0):

        if debug() >= utilDebugLevel():
            print("DEBUG: in utils::getNodeAndStepIdAssociatedWithStepNumberLinux() -- whoami ")
        userName= os.environ['LOGNAME']
    else:
        theLines = stdout_value.split('\n')
        if len(theLines) >= 1:
            userName= theLines[0]

    #--------------------------------------------------
    # Gather any stepids for the user first
    # "squeue -s -u userName"
    #--------------------------------------------------
    #
    #  unset SQUEUE_FORMAT before using "squeue -s"
    #--------------------------------------------------
    if 'SQUEUE_FORMAT' in os.environ:
        oldSqueueFormatValue= os.environ['SQUEUE_FORMAT']
        os.unsetenv('SQUEUE_FORMAT')

    squeueCmd= "squeue -s -u " + userName
    proc = subprocess.Popen(squeueCmd, shell=True, stdout=subprocess.PIPE, text=True)
    stdout_value = proc.communicate()[0]

    if (len(stdout_value)==0):          # no return values
        return inStepNum

    stepList= []
    nameList= []

    theLines = stdout_value.split('\n')
    for aline in theLines:
        if "STEPID" in aline:
            continue
        else:
            splitVals= aline.split()
            if len(splitVals) > 4:
                stepList.append(splitVals[0])
            if len(splitVals) > 4:
                nameList.append(splitVals[1])

    if debug() >= utilDebugLevel():
        print("stepList= %s" % stepList)
        print("nameList= %s" % nameList)

    #--------------------------------------------------
    # For the step number, determine the node assoicated with it.
    #--------------------------------------------------
    # Using "sleep" check which node is used.
    #
    stepToCheck= 0
    for ii in range(inMaxStep):
        # embed the process id into the job name to distinguish between invocation of the ats.
        cmd= "srun -N1 -J %d_%d -n 1 -r %d sleep 5" % ( ii, os.getpid(), ii )
        sleepProc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, text=True)

    #--------------------------------------------------
    # "squeue -s -u userName " --- again to check which node corresponds to the step
    #--------------------------------------------------

    # continue issuing the squeueCmd until all the nodes corresponding to the step are found.
    stepIdToCheck= None
    while 1:
        proc = subprocess.Popen(squeueCmd, shell=True, stdout=subprocess.PIPE, text=True)
        stdout_value = proc.communicate()[0]
        if (len(stdout_value)==0):
            return None

        theLines= stdout_value.split('\n')

        if debug() >= utilDebugLevel():
            for aline in theLines:
                print("LINES READ: %s" % aline)

        nodeToCheck= ""
        newStep= '0'
        nodeStepDic= {}
        for aline in theLines:
            if "STEPID" in aline:
                continue
            else:
                splitVals= aline.split()
                if len(splitVals) > 5:
                    newStep=  splitVals[0]
                    newName=   splitVals[1]
                    #checking newStep value is not enough because the user may have the step used to run something else.
                    if newStep not in stepList or newName not in nameList:
                        nodeToCheck= splitVals[5]
                        stepLink, pid = splitVals[1].split("_")      # part of the pid may get cut off!

                        if str(pid) in str(os.getpid()):
                            nodeStepDic[nodeToCheck]= stepLink
                        else:
                            continue

        if (len(nodeStepDic) > 0):
            stepIdToCheck= newStep.split(".")[0]

        if debug() >= utilDebugLevel():
            print("nodeStepDic= %s" % nodeStepDic)
            print("stepIdToCheck= %s" % stepIdToCheck)

        if (len(nodeStepDic) == inMaxStep ):
            break
        # end while loop


    #  re-set SQUEUE_FORMAT after using "squeue -s"
    #--------------------------------------------------
    if 'SQUEUE_FORMAT' in os.environ:
        os.environ['SQUEUE_FORMAT']=  oldSqueueFormatValue

    if nodeToCheck == '' or newStep== '':
        return None, None

    return stepIdToCheck, nodeStepDic


#---------------------------------------------------------------------------
def getNumberOfProcessorsPerNode(useNode=None):
    # Assume all nodes on this machine has the same number of processors

    if 'SYS_TYPE' in os.environ:
        SYS_TYPE= os.environ['SYS_TYPE']
    else:
        SYS_TYPE= ''
    try:
        import subprocess
        stdout_value = '0'
        catCmd= 'lsdev -C -c processor | wc -l'

        if SYS_TYPE.startswith('aix'):

            cmd = 'scontrol show node | head -2 '

            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, text=True)
            stdout_value = proc.communicate()[0]

            cmdVal= repr(stdout_value)

            # Expect value to be similar to this format
            #
            # ["'NodeName", 'alc36 State', 'ALLOCATED CPUs', '2 AllocCPUs', '2 RealMemory', '3300 TmpDisk',"0\\n'"]
            #
            # grab cpu information

            allVals = cmdVal.split()

            numCPU= '0'
            for val in allVals:
                if val.startswith('CPUTot'):
                    numCPU= val.split('=')[-1]
                    break

            return  int(numCPU)

        else: #if SYS_TYPE.startswith('linux'):
            catCmd= 'cat /proc/cpuinfo | grep processor | wc -l'

        # grab cpu information
        if useNode==None:
            cmdToUse= catCmd
        else:
            sshCmd= 'ssh ' + useNode + ' '
            cmdToUse= sshCmd + '"' + catCmd + '"'

        proc = subprocess.Popen(cmdToUse, shell=True, stdout=subprocess.PIPE, text=True)
        stdout_value = proc.communicate()[0]
        numCpu = stdout_value.split()[0]   # another way of getting CPUs
        return  int(numCpu)
    except KeyboardInterrupt:
        raise
    except:
        print("ATS ERROR: in getNumberOfProcsPerNode:%s" % sys.exc_info())
        return 0


#---------------------------------------------------------------------------

def runThisCommand(cmd):
    import subprocess
    aProcess = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, text=True)
    aProcess.wait()
    output = aProcess.communicate()[0]
    returnCode= aProcess.returncode

    return returnCode, output

#---------------------------------------------------------------------------
def getAllSlurmStepIds():
    import subprocess
    # get username
    import getpass, os

    envUser= None
    if 'USER' not in os.environ:
        envUser= getpass.getuser()
    else:
        envUser= os.environ['USER']


    try:
        squeueCommand= "squeue  -s -u " + envUser + " -o '%.50i %.9P %.220j %.8u %.10M'"

        returnCode, stdOutput= runThisCommand(squeueCommand)

        theLines = stdOutput.split('\n')

    except OSError as e:
        theLines= "---- killUsingSlurmStepId, execution of command failed :  %s----" %  (squeueCommand)

    return theLines

#---------------------------------------------------------------------------
