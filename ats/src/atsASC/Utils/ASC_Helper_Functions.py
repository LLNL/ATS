import os
import sys
import re
import stat

from socket import gethostname

sys.dont_write_bytecode = True

from ats import log, SYS_TYPE
from ats import CREATED, INVALID, PASSED, FAILED, \
                SKIPPED, BATCHED, RUNNING, FILTERED, TIMEDOUT

from ASC_utils import findKeyVal, runCommand, importName, projectATSModuleName
import ASC_State
import ASC_defaults
import ASC_HTML


getExecutableVersion    = importName( projectATSModuleName, 'getExecutableVersion' )
my_project_name = importName( projectATSModuleName, 'my_project_name')
my_project_gid  = importName( projectATSModuleName, 'my_project_gid')

my_project_executable_version = "unset"

# -------------------------------------------------------------------------------------------------
#
# -------------------------------------------------------------------------------------------------
def getCPUInfo():
  cpu_vendor = ''
  cpu_model  = ''

  if 'toss' in SYS_TYPE:
    cmd = 'cat /proc/cpuinfo'
    (stdout_txt, stderr_txt) = runCommand(cmd, exit=False, verbose=True)
    lines = stdout_txt.splitlines()
    cpu_vendor = findKeyVal( lines, 'vendor_id', ':')
    if cpu_vendor.startswith('Authentic'):
      cpu_vendor = cpu_vendor[9:]
    elif cpu_vendor.startswith('Genuine'):
      cpu_vendor = cpu_vendor[7:]
    cpu_model = findKeyVal(lines, 'model name', ':')
  elif 'blueos' in SYS_TYPE:
    cmd = 'cat /proc/cpuinfo'
    (stdout_txt, stderr_txt) = runCommand(cmd, exit=False, verbose=True)
    lines = stdout_txt.splitlines()
    cpu_vendor = findKeyVal( lines, 'machine', ':')
    cpu_vendor = cpu_vendor[5:99]
    cpu_model  = findKeyVal(lines, 'cpu', ':')
    cpu_model  = cpu_model[0:]
  else:
    log('SYS_TYPE %s not supported' % SYS_TYPE, echo=True)

  return ( cpu_vendor, cpu_model)

# -------------------------------------------------------------------------------------------------
#
# -------------------------------------------------------------------------------------------------
def getBaselineID():
  host_name = re.split('(\d+)', gethostname() )[0]

  (cpu_vendor, cpu_model) = getCPUInfo()

  log('Host name:  %s  SYS_TYPE:  %s' % (host_name, SYS_TYPE), echo=True)
  log('CPU vendor: %s  CPU model: %s' % (cpu_vendor, cpu_model), echo=True)

  id = SYS_TYPE + '_' + cpu_vendor.lower()

  return ( id )

# -------------------------------------------------------------------------------------------------
#
# -------------------------------------------------------------------------------------------------
currentID = getBaselineID()


# -------------------------------------------------------------------------------------------------
# Helper function
# -------------------------------------------------------------------------------------------------
def listfilesWithKernel(folder, kernel):
    kernel_string = "^%s" % kernel
    return [d for d in os.listdir(folder) if re.search(kernel_string, d) \
                                          if os.path.isfile(os.path.join(folder, d))]


# -------------------------------------------------------------------------------------------------
# Grok the kernel from the cwd.  Visit runs in a directory which will include the name of 
# the test case, use this fact to grok the name of the test being run.                        
# -------------------------------------------------------------------------------------------------
def getKernelNameFromDir(directory, results_suffix):
    tempstr = directory
    tempi = tempstr.find(results_suffix)
    tempstr = tempstr[0:tempi]
    tempi = tempstr.rfind("/") + 1
    kernel = tempstr[tempi:999]
    return kernel

# --------------------------------------------------------------------------------------------------
# Walk a tree, returning a list of all files in the tree
#
# The filter function makes for a more efficient walk by filtering out files and directories
# we will never want to traverse. Currently this is the 'svn' directories
# --------------------------------------------------------------------------------------------------
def walktree_filter(name):
    if name == ".svn":
        return False
    elif name == ".git":
        return False
    return True

def walktree (top = ".", depthfirst = True, my_project_runs_dir="."):
    names = os.listdir(top)
    filtered_names = filter(walktree_filter, names)
    if not depthfirst:
        yield top, filtered_names
    for name in filtered_names:
        try:
            st = os.lstat(os.path.join(top, name))
        except os.error:
            continue
        if stat.S_ISDIR(st.st_mode):
            for (newtop, children) in walktree (os.path.join(top, name), depthfirst):
                yield newtop, children
        if stat.S_ISLNK(st.st_mode) and (name == my_project_runs_dir):
            for (newtop, children) in walktree (os.path.join(top, name), depthfirst):
                yield newtop, children
    if depthfirst:
        yield top, filtered_names

# --------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------
def listfilesWithKernel(folder, kernel):
    kernel_string = "^%s" % kernel
    return [d for d in os.listdir(folder) if re.search(kernel_string, d) \
                                          if os.path.isfile(os.path.join(folder, d))]
# --------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------
def listfilesOrDirsWithKernel(folder, kernel):
    kernel_string = "^%s" % kernel
    return [d for d in os.listdir(folder) if re.search(kernel_string, d)]

# --------------------------------------------------------------------------------------------------
# run a command.  
# If given a file, it creates two files (one for stdout and one for stderr).  
# It also returns two strings (one for stdout and one for stderr)
# --------------------------------------------------------------------------------------------------
def runCommand( cmd_line, file_name=None, exit=True, verbose=True):
    """
    Function to run a command and capture its output.
    """

    popen_args = shlex.split( cmd_line )

    if verbose:
        log('%s runCommand: %s' % (my_project_info_text, cmd_line), echo = True)
  
    try:
    
        if file_name is not None:
            stdout_pipe = open( file_name, 'w')
            stderr_pipe = open( '%s.err' % file_name, 'w')
        else:
            stdout_pipe = PIPE
            stderr_pipe = PIPE
    
        (stdout_txt, stderr_txt) = Popen(popen_args, stdout=stdout_pipe, stderr=stderr_pipe).communicate()
    
        if file_name is not None:
            stdout_pipe.close()
            stderr_pipe.close()
      
    except CalledProcessError, error:
        log('%s Command failed: error code %d' % (my_project_info_text, error.returncode), echo=True)
        log('%s Failed Command: %s' % (my_project_info_text, cmd_line), echo=True)
        if exit:
            raise SystemExit, 1
    except OSError, error:
        log('%s Command failed with OSError: traceback %s' % (my_project_info_text, error.child_traceback), echo=True)
        log('%s Failed Command: %s' % (my_project_info_text, cmd_line), echo=True)
        if exit:
            raise SystemExit, 1
  
    return ( stdout_txt, stderr_txt )


# --------------------------------------------------------------------------------------------------
#
# Alternative to runCommand.  
# Sends output to screen AND file.
# Run with '-v' to set optionsVerbose and see data sent to the screen.
# Returns a single file, with stdout and stderr in it.
#
# --------------------------------------------------------------------------------------------------
def execute(cmd_line, file_name=None, verbose=True, exit=True):
    """
    Function to run a command and display output to screen.
    """

    if verbose:
        log('%s execute: %s' % (my_project_info_text, cmd_line), echo = True)

    if file_name is not None:
        execute_ofp = open(file_name, 'w')

    process = Popen(cmd_line, shell=True, stdout=PIPE, stderr=STDOUT)

    # Poll process for new output until finished
    while True:
        nextline = process.stdout.readline()
        if (nextline == '' and process.poll() != None):
            break
        if (verbose == True):
            sys.stdout.write(nextline)
            # sys.stdout.flush()
        if file_name is not None:
            execute_ofp.write(nextline)


    output = process.communicate()[0]
    exitCode = process.returncode

    if file_name is not None:
        execute_ofp.close()

    if (exitCode == 0):
        pass
        # return output
    else:
        if exit:
            log('%s FATAL RETURN CODE %d Command: %s' % (my_project_info_text, exitCode, cmd_line), echo=True)
            raise SystemExit, 1

    return exitCode

# --------------------------------------------------------------------------------------------------
#
# Create a status file for each test so that we can post process the directory with scripts
# without the user having to deal with manager objects.  This also allows for work to be done
# across multiple runs of ats, which would require the user to have to deal with multiple
# manager objects.
#
# Basically, each test has a STATUS file (each checker does as well) and post processing
# to commit new baseline tar files can check for the existence of a status file to help
# determine if it should create and commit a new tar file.
#
# Also, create a METADATA file for each test, with some info from the manager object,
# such as the input deck name, command line args, etc.  The input deck name in particular
# is useful, so that I can add it to the baeline tar file.  The command line args may 
# be useful for users, as some have said that they like to know this so they can
# rerun a test by hand outside of ats
#
# --------------------------------------------------------------------------------------------------
def createStatusFileOnExit(manager):

    #
    # Get the executable version, to put in the STATUS file
    # Only do this once, since we run the same code version for all tests.
    #
    global my_project_executable_version

    if my_project_executable_version == "unset":
        my_project_executable_version = getExecutableVersion( manager.options.executable ) 

    #
    # For each test, create a STATUS file which indicates PASS or FAIL or
    # other status code.  Differentiate checker tests from the code run itself.
    #
    for test in manager.testlist:

        if test.options['checker_test'] == False:
            #
            # Do not write status files for filtered or skipped tests
            #
            if test.status == FILTERED or test.status == SKIPPED or test.directory == "":
                continue
            #
            # If running the dummy, do not change the status file from the real run
            #
            if manager.options.executable.endswith("dummy.py"):
                continue

            statusfile = "%s/%s.STATUS" %  (test.directory, test.options['kernel'])

            splitsville = test.options['clas'].split()   # grok deck from clas string
            deck = splitsville[0]
            ofp = open(statusfile, 'w')
            ofp.write("executable = %s\n" %  manager.options.executable)
            ofp.write("deck = %s\n" % deck)
        else:

            #
            # Do not write status files for filtered or skipped tests
            #
            if test.status == FILTERED or test.status == SKIPPED:
                continue


            statusfile = "%s/%s.STATUS.CHECKER" %  (test.directory, test.options['label'])
            ofp = open(statusfile, 'w')
            ofp.write("executable = %s\n" %  test.options['executable'])

        ofp.write("clas = %s\n" %  test.options['clas'])
        ofp.write("np = %s\n" %  test.options['np'])
        ofp.write("status = %s\n" %  test.status)
        ofp.write("version = %s\n" %  my_project_executable_version)
        ofp.close()

# --------------------------------------------------------------------------------------------------
# Inspect ats log and add a summary entry to the HTML page
# --------------------------------------------------------------------------------------------------
def addHTMLATSLogOnExit(manager):

    #
    # The default is that we will create HTML pages, but we can turn it off
    # with the --withoutHTML option passed to ats
    #
    if not manager.options.withHTML:
        return


    #
    # Set empty lists, default results value of success, and the 
    # name of the ats log file.
    #
    artLists = []
    msgLists = []

    result = "Success"

    #
    # create the command line used to run ats
    #
    # cmd_line = sys.argv[0]
    cmd_line = ""
    for arg in sys.argv:
        cmd_line += " " + arg

    #
    # the name of the main ats log
    #
    log_file = "%s/ats.log" %( log.directory )

    #
    # Loop over the tests, count num passed, failed, etc.
    # 
    numPassed  = 0
    numFailed  = 0
    numInvalid = 0
    numTimeout = 0

    #
    # For each test, setup string about it's status
    #
    for test in manager.testlist:

        if test.status == PASSED:
            numPassed = numPassed + 1
        else:
            #
            # If the --debug option was given, add more artifacts to the
            # html page.
            #
            if manager.options.debug:
                if 'testout' in test.options:
                    testout = test.options['testout']
                    if os.path.isfile(testout):
                        str = "%s Output Log" % test.options['label']
                        art = [ testout, str ]
                        artLists.append(art)
                if 'testerr' in test.options:
                    testerr = test.options['testerr']
                    if os.path.isfile(testerr):
                        str = "%s Error Log" % test.options['label']
                        art = [ testerr, str ]
                        artLists.append(art)

            if test.status == FAILED:
                numFailed = numFailed + 1
            elif test.status == INVALID:
                numInvalid = numInvalid + 1
            elif test.status == TIMEDOUT:
                numTimeout = numTimeout + 1

    if (numFailed > 0):
        result = "Failure"
        msg = "numFailed = %d" % numFailed
        msgLists.append(msg)
    elif (numTimeout > 0):
        result = "Warning"
        msg = "numTimeout = %d" % numTimeout
        msgLists.append(msg)
    elif (numInvalid > 0):
        result = "Warning"
        msg = "numInvalid = %d" % numInvalid
        msgLists.append(msg)

    msg = "numPassed = %d" % numPassed
    msgLists.append(msg)

    # Call ASC_HTML routine to add a line to the HTML page
    #
    list1 = [ log_file, 'ATS Log' ]
    logLists = [ list1 ]

    if (manager.options.htmlMainPageDescription != ""):
        mainPageTaskDescription = "%s ATS Run" % manager.options.htmlMainPageDescription
    else:
        mainPageTaskDescription = "ATS Run"

    #print "DEBUG 111a"
    #print msgLists
    #print logLists
    #print artLists
    #print "DEBUG 111b"

    ASC_HTML.addGenericResults(manager.options.htmlDirectory,
                             my_project_name,
                             my_project_gid,
                             mainPageTaskDescription,   # Task Attempted 
                             result,                    # Success, Failure, or Warning
                             cmd_line,                  # Command attempted 
                             msgLists,                  # list of msgs for front html page
                             logLists,                  # list of log files and descriptions
                             artLists)                  # list of artifacts and descriptions

# -------------------------------------------------------------------------------------------------
# End of File
# -------------------------------------------------------------------------------------------------
