import os, socket
import re, sys, time

from ats import log, atsut, times, configuration

debug = configuration.debug


template = """\
#!/bin/csh
%(hostname)s
#MSUB -N %(jobname)s     # name of the job
#MSUB -A %(bank)s             # the bank account to charge
#MSUB -q %(partition)s               # run in the specified queue (pdebug,pbatch,etc)
#MSUB -l resfailpolicy=cancel # cancel the job if a node fails
#MSUB -V                      # all environment variables are exported
#MSUB -l partition=%(constraints)s # run job on host cluster
#MSUB -l nodes=%(nodes)s:ppn=%(numprocs)s      # number of nodes , number of processors
#MSUB -l ttc=%(totalnumprocs)s      # number of total processors (total MPI tasks count)
#MSUB -l walltime=%(timelimit)s     # max runtime in seconds

#MSUB -e %(errorFilename)s          # send stderr to errfile
#MSUB -o %(outputFilename)s          # send stdout to outfile
%(gres)s
%(qos)s
#MSUB                         # end of msub

set echo

###echo jobID=$SLURM_JOB_ID
echo nodeName=`hostname`

%(startTime)s
limit coredumpsize 0
umask 027

cd %(testPath)s
%(command)s

set statusCode = $status
echo $statusCode >&! %(statusFilename)s
%(endTime)s




"""

summaryTemplate= """\

== Test Case:      %(testNameBase)s
    test label:    %(testName)s
    test path:     %(testPath)s
    procs:         %(testNp)s
    level:         %(testLevel)s

    batch script:  %(scriptFilename)s
    output file:   %(outputFilename)s
    status file:   %(statusFilename)s
    execute line:  %(command)s
    job ID:        %(jobid)s
    timelimit:     %(timelimit)s
    test status:   %(status)s

"""



def buildBatchDic(test, maxtime, constraints, gres, standby, hostname):
    # maxtime is in minutes

    batchDic = test.batchDic

    jobname= "t%d%s%s%s" % (test.serialNumber, test.namebase, os.environ['SYS_TYPE'], time.strftime('%H%M%S',time.localtime())
) 
    batchDic['jobname']= jobname
    batchDic['totalnumprocs']= str( int(batchDic['numprocs']) * int(batchDic['nodes']))
    
    batchDic['timelimit']= times.timeSpecToSec(maxtime)

    # constraints - get non-digit part of node name
    if constraints is None:
        nodeName = socket.gethostname()
        wordpat = re.compile('(^[a-zA-Z_]*)(\d*)').search
        constraints = wordpat(nodeName).group(1)
    #test.constraints= constraints
    batchDic['constraints']= constraints

    # gres = lscratch[a|b|c|d|...] or ignore (default)
    hwname = os.uname()[1]
    if hwname.startswith('purple') or hwname.startswith('um'):
        # um and purple do not use lustre parallel system
        batchDic['gres'] = ''
    else:
        #Linux platform and other AIX systems
        if gres is None:
            batchDic['gres'] = ''
        else:
            batchDic['gres'] = '#MSUB -l gres=%s'%gres

    # qos: quality of service - standby only for now
    if standby:
        batchDic['qos'] = '#MSUB -l qos=standby'
    else:
        batchDic['qos'] = ''

    if hostname != '':
        batchDic['hostname'] = '#MSUB -l partition=%s'%hostname
    else:
        batchDic['hostname'] = ''

    batchDic['startTime'] = 'date +"Start Time: %Y/%m/%d %T"'
    batchDic['endTime'] = 'date +"End Time: %Y/%m/%d %T"'

    return batchDic



def hms (t):
    "Returns t seconds in h:m:s.xx"
    h = int(t/3600.)
    m = int((t-h*3600)/60.)
    s = int((t-h*3600-m*60))
    return "%d:%02d:%02d" %(h,m,s)

def writeLines(filename,lines):
    fp = open(filename,'w')
    fp.write(lines)
    fp.close()
    return filename


def submit(testObj,command):
    "submit job to moab system"

    resultFlag= False
    
    batchDic= testObj.batchDic
    
    batchDic['note']= ""
    batchDic['error']= ""
    batchDic['status' ]= ""

    
    if debug():
        log('batch command:  %s'%command, echo=True)
    p= os.popen(command)
    output= p.read()
    status= p.close()
    if debug():
        log('batch output:  %s'%output, echo=True)


    jobname= batchDic['jobname']
    if status is not None:
        log('Error submitting job %s'%jobname, echo=True)
        log('status=%d; output=|%s|'%(status,output), echo=True)
        
    if status==256:
        msg= 'ERROR: rejected by moab system upon submission'
        batchDic['note']= msg
        batchDic['error']= output
        batchDic['status']= "REJECTED"
        testObj.set(atsut.INVALID,msg)

        log(msg, echo=True)
    elif status is not None:
        msg= 'ERROR: investigate further'
        batchDic['note']= msg
        batchDic['error']= output
        batchDic['status']= 'UNKNOWN'
        testObj.set(atsut.INVALID,msg)

        log(msg, echo=True)
    else:
        output = output.strip()
        #log('output=%s*'%output, echo=True)
        pat = re.compile('^(\d+)').search
        if pat(output):
            jobID = pat(output).group(0)
            if len(jobID) == len(output):
                batchDic['jobid']= jobID
                
                batchDic['status'] = 'SUBMITTED'
                timeNow= time.strftime('%H%M%S',time.localtime())
                #msg = 'Batch submitted at ' + datestamp()
                msg = 'Batch submitted at ' + timeNow
                msg= 'Submitted job %s. (jobid= %s)'%(jobname, jobID)
                batchDic['note'] = msg
                testObj.set(atsut.BATCHED,msg)
                resultFlag= True

            else:
                msg= 'ERROR: jobID=%s and output=%s different.'%(jobID,output)
                batchDic['note']= msg
                batchDic['error']= output
                testObj.set(atsut.INVALID,msg)

                log(msg, echo=True)

    testObj.batchDic= batchDic
    return resultFlag

def submitBatchScript(scriptName):
    "submit job script to moab system.  Returns the jobid afterward."

    jobID= None
    resultFlag= False
    
    command= "msub " + scriptName
    print "command= ", command
    p= os.popen(command)
    output= p.read()
    status= p.close()

    if status is not None:
        log('Batch: Error submitting script %s'%scriptName, echo=True)
        log('Batch: status=%d; output=|%s|'%(status,output), echo=True)
        
    if status==256:
        msg= 'Batch: ERROR: %s rejected by moab system upon submission' %scriptName
        log(msg)
    elif status is not None:
        msg= 'Batch: ERROR: Script not submitted. Reason unknown.'
        log(msg)
    else:
        output = output.strip()
        pat = re.compile('^(\d+)').search
        if pat(output):
            jobID = pat(output).group(0)
            if len(jobID) == len(output):
                timeNow= time.strftime('%H%M%S',time.localtime())
                msg = 'Batch submitted at ' + timeNow
                log(msg)
                msg= 'Batch jobid %s'%jobID
                log(msg)
            else:
                msg= 'Batch: ERROR: jobID=%s and output=%s different.'%(jobID,output)
                log(msg)

    return jobID


def batchLogSummary(fileToWrite, outputList):
    fp = open(fileToWrite,"w")
    #print >>fp, "Created Batch Info File"
    for line in outputList:
        print >>fp, line
    fp.close()


def writeSummaryBatchJob(jobDict,longest):
    " return the summary output of batch jobs"

    output = []
    #testcase = jobDict['testcase']
    #testpath = jobDict['testpath']
    #script   = jobDict['batchScriptName']
    #outfile  = jobDict['outfile']
    #execline = jobDict['execline']
    jobID    = jobDict['jobID']
    #reason   = jobDict['reason']
    #errMsg   = jobDict['errMsg']
    testlabel = jobDict['testlabel']
    status   = jobDict['status']
    #output.append(status + " "*(longest-len(status)+1) + execline)
    output.append(status + " "*(longest-len(status)+1) + testlabel)
    return output


def summaryBatchStatistics(submittedJobList,badBatchJobList):
    "return the summary of batch runs"

    longestG = 0
    longestB = 0
    separator = "--------------------------------------------"
    output = []
    if submittedJobList == [] and badBatchJobList == []:
        return output

    # write submitted batch info
    firstTime = 1
    for jobDict in submittedJobList:
        if firstTime:
            firstTime = 0
            msg = "\n----- Problems Submitted To Batch System --------"
            output.append(msg)

        if len(jobDict['status']) > longestG: longestG = len(jobDict['status'])
        output = output + writeBatchJob(jobDict)

    # write bad batch info
    firstTime = 1
    for jobDict in badBatchJobList:
        if firstTime:
            firstTime = 0
            msg = "\n----- Problems Not Accepted By Batch System --------"
            output.append(msg)

        if len(jobDict['status']) > longestB: longestB = len(jobDict['status'])
        output = output + writeBatchJob(jobDict,type='badJob')

    # write summary of submitted batch info
    firstTime = 1
    for jobDict in submittedJobList:
        if firstTime:
            firstTime = 0
            msg = "Summary of Executed Problems %s"%datestamp(long=1)
            output.append(msg)
            output.append(separator)
        output = output + writeSummaryBatchJob(jobDict,longestG)

    # write summary of failed batch info
    firstTime = 1
    for jobDict in badBatchJobList:
        if firstTime:
            firstTime = 0
            msg = "Summary of Rejected Problems %s"%datestamp(long=1)
            output.append(msg)
            output.append(separator)
        output = output + writeSummaryBatchJob(jobDict,longestB)

    output.append(separator)
    return output




