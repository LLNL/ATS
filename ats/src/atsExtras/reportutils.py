#
#  These are report / ats specific methods that use the atsr.py state file.
#  The methods were intended to be used for reporting, but can be used to look at test results  
#  in general.
#
import os,sys 
#sys.path.append("/usr/apps/atsnew/lib/python2.7/site-packages")
from ats import *
from ats.atsut import PASSED,FAILED,TIMEDOUT,SKIPPED,BATCHED,RUNNING,\
        FILTERED,INVALID
from ats import log

def getStateFromFile(atsrFile):
    '''Gets the ats state out of the atsr.py file.'''
    # input: a file (atsr.py)
    # output: the state dict
    # use case: We may want to grab something other than the test list, or 
    #  make a list of state files to process
    # To get the state I'm using the example from the ats pdf, page 24 that says
    # to use execfile and rename the state, then appending it's testlist
    # to our list using the filename as it's key
    d = {}
    if os.path.exists(atsrFile):
        print "Taking state from ",atsrFile 
        execfile(atsrFile, d)
        state = d['state']
        state['logDirectory'] = d['logDirectory'] # We want access to the run's logs, but they're not stored as part of the test object
        state['atsMachineName'] = d['machineName']   # Not sure how useful this will be, but it's available.
        for test in state.testlist:
            pass
    else:  
        print "Path does not exist.  Can't get the state for:",atsrFile
        return None
    return state
    
def findAtsrFile(testDir):
    '''Uses python glob to find the atsr.py file.
    If no atsr is found in a directory, returns None.'''
    # input: path to the test directory 
    # output: path to the atsr.py file in the form of a glob list.  
    #  If multiple files are found, the glob list is sorted then returned.   
    print "looking at ", testDir
    import glob
    globList = glob.glob(testDir + '/*.logs/atsr.py')
    if len(globList)>0:
        globList.sort()
        return globList
    else:
        return None

def getTestListFromState(stateDict):
    '''Gets the entire test list from the state object.'''
    # input: State Dict from the atsr.py file
    # output: testlist
    # use case:  may want to act on the entire test list rather than rely on status lists
    #  such as see which test took the longest, check walltimes, or some other test attribute
    #  other than STATUS.
    #  Could also be used to determine which tests have been run (create a master test list from
    #  multiple test lists as we do in the test reports for comparisons).
    return stateDict.testlist

def getTestStatusLists(testlist):
    '''Returns multiple lists of test objects, according to ats test status results. '''
    # input: state or testlist...not sure if I should accept either/or or specify one.
    # output: Lists of tests according to status (passed, failed, timedout,etc.) 
    passed = [test for test in testlist if (test.status is PASSED)]
    failed = [test for test in testlist if (test.status is FAILED)]
    timedout = [test for test in testlist if (test.status is TIMEDOUT)]
    skipped = [test for test in testlist if (test.status is SKIPPED)]
    filtered = [test for test in testlist if (test.status is FILTERED)]
    invalid = [test for test in testlist if (test.status is INVALID)]
    running = [test for test in testlist if (test.status is RUNNING)] # Shouldn't be any in this state because atsr.py is written after execution is done...but that may change so it's here.
    return passed,failed,timedout,skipped,filtered,invalid,running

def getWallTime(state):
    '''Walltime in the ats logs is calculated when the test is run, then logged.
    To get it from the atsr file, subtract the start time (state['started'] from the end time
    state['savedTime']. 
    This method is included to add the walltime of an ats run  to the reports.
    '''
    import datetime
    format = '%B %d, %Y %H:%M:%S'
    started = datetime.datetime.strptime(state['started'],format )
    ended = datetime.datetime.strptime(state['savedTime'],format)
    walltime = ended - started
    return walltime

def getListRuntimeAndLogs(testList, status=None):
    '''Return a list sorted by testName, includes runtime for each test and lists ats logs for each specific
    each test, if any.
    Could be used to sort the failed tests and provide their run time and paths for links to logs.
    '''
    pass

def sortListByTestName(testList):
    '''Lists are too large and not in order, it's a pain to search through. '''
    pass

def createHtmlSummaryFromState(stateList):
    '''Uses a list of ats test run States ( entire state including test list & machine info, not the status separated lists).
     NOTE: The list of states NEEDS a name associated with the list. I've used setattr to add the machine.hcs
     to the state in order to use it in the summary tables.  I think this is probably SUPER fragile and needs a better solution.
     Calls getStatusLists() for each testlist in the List. 
     Returns a text string with an html tag formated table of results.'''   
    # Table header row
    summary = ''
    summary += '''<table border="1"><caption><b>Report Summary</b></caption>
                  <tr><td>Platforms Tested</td>
                  <td>Passed</td>
                  <td>Failed</td> 
                  <td>Timedout</td>
                  <td>Invalid</td>
                  <td>Filtered</td>
                  <td>Skipped</td>
                  <td>Total</td></tr>'''
    sumTemplate =  ''' <tr><td> %(filename)s</td>
                       <td align="right" width="60"> %(passed)s </td>
                       <td align="right" width="60"> %(failed)s </td>
                       <td align="right" width="60"> %(timedout)s </td>
                       <td align="right" width="60"> %(invalid)s </td>
                       <td align="right" width="60"> %(filtered)s </td>
                       <td align="right" width="60"> %(skipped)s </td>
                       <td align="right" width="60"> %(total)s </td></tr> '''
    # Add the summary for each of the test jobs in the list 
    for state in stateList:
        passed,failed,timedout,skipped,filtered,invalid,running = getTestStatusLists(state.testlist)
        # Table body template
        testSums = {'filename':state.machineName, 
                    'total': str(len(state.testlist)), 
                    'passed':str(len(passed)),
                    'failed':str(len(failed)) , 
                    'timedout': str(len(timedout)),
                    'invalid':str(len(invalid)), 
                    'filtered': str(len(filtered)),
                    'skipped': str(len(skipped))}
        summary += sumTemplate % testSums
    summary+='''  </table></p><br> '''
    return summary
    
# <a href="url">Link text</a> 
tableErrLogsTemplate =  ''' <tr><td> %(testname)s</td>
                   <td align="right" width="60"><a href=" %(log)s ">log</a> </td>
                   <td align="right" width="60"><a href=" %(errlog)s ">errlog</a></td></tr> '''
def createFailedTestTable(state):
    '''Create a table of the failed tests, add links to the error files.'''
    pass

def createFailedTestMultiTable(stateList):
    '''Create a table of the failed tests for multiple runs.  Add links to the error files.'''
    pass

def createTableFromTestList(testList,logDirectory,tableName='',relativeTo=None):
    '''Creates an html table from the test list and adds links to the error files, if any.'''
    # Don't constrain the input list, just create a table
    # How are we going to find the error files?
    #    - need the log directory - the log information isn't stored in the test object,it's in state.logDirectory
    # useful test attributes:  i.name, i.serialNumber
    table = '<table border="1"><caption><b>%s</b></caption>'%tableName
    for i in testList:
        print i.name,i.serialNumber
        # find logfile
        import glob 
        errorfiles = logDirectory + '/*'+ str(i.serialNumber)+'*'
        files = glob.glob(errorfiles)
        if files:
            if relativeTo: # Make the links relative so the logs can be archived w/out ruining the table
                index = logDirectory.index(relativeTo)+len(relativeTo) #we want to remove part of the path including the relativeTo directory... 
                loglink = './'+files[0][index:]
                errlink = './'+files[1][index:]
            else:
                loglink = files[0]
                errlink = files[1]
            testLogs = {'testname':i.name, 
                        'log': loglink, 
                        'errlog':errlink}
            t = tableErrLogsTemplate % testLogs
            table+= t
    table += '</table></br>'
    return table

#
#  END  OF THE ATS SPECIFIC REPORT METHODS
#  Next are the build specific utilities like finding machine logs
#   and appending failures to the reports.
def findBuildLog(machine=None, buildlog=None):
    ''' This will use the machines build_dir to find the background-build log when the machine is passed in,
        Otherwise it will look for the user defined buildlog.
        Note that the report utils are using the testutils machine object which doesn't contain a build log attribute.
    '''
    pass


