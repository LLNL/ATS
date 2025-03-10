import os
import sys

import grp
import re
import shlex
import shutil
import stat

from ats import log
import subprocess
from subprocess import Popen, PIPE, CalledProcessError, STDOUT

# Define module variables to hold names of ASC and project modules
# for dynamic loading of module members.

ASCModuleName        = 'ASC_atsb'
baseASCPATH          = ''
projectATSModuleName = None

#####################################################################
#  Utility Functions
#####################################################################

# Coding to load module found in Python Cookbook, Section 15.3, pg 456
def importName( moduleName, name, default_func=None, verbose=False ):
    """
    At run time, dynamically import 'name' from 'moduleName'.
    """
    if verbose:
        print("Loading %s from %s." % (name, moduleName))
    func = default_func
    try:
        print("ATS WARNING: VERY SUSPICIOUS WAY OF IMPORTING")
        my_mod = __import__( moduleName, globals(), locals(), [name] )
        func   =  vars(my_mod)[name]
    except ImportError as value:
        print("Import of function %s from %s failed: %s" % (name, moduleName, value))
        raise Exception
    except KeyError as value:
        print("ATS ERROR: KeyError during import of function %s from %s failed: %s" % (name, moduleName, value))
        pass

    return func

# --------------------------------------------------------------------------
#
# Short cut function to simpify loading project functions.
#
# --------------------------------------------------------------------------
def getProjectFunction( name, default_func=None, verbose=False ):
    return importName( projectATSModuleName, name, default_func, verbose )

#####################################################################

def runCommand( cmd_line, file_name=None, exit=True, verbose=False):
    """
    Function to run a command and capture its output.
    """
    popen_args = shlex.split( cmd_line )

    log('runCommand command line: %s' % cmd_line, echo = verbose)

    try:

        if file_name is not None:
            if os.path.exists( file_name ):
                stdout_pipe = open( file_name, 'a')
                stderr_pipe = open( '%s.err' % file_name, 'a')
            else:
                stdout_pipe = open( file_name, 'w')
                stderr_pipe = open( '%s.err' % file_name, 'w')
        else:
            stdout_pipe = PIPE
            stderr_pipe = PIPE

        (stdout_txt, stderr_txt) = Popen(popen_args, stdout=stdout_pipe, stderr=stderr_pipe, text=True).communicate()

        if file_name is not None:
            stdout_pipe.close()
            stderr_pipe.close()

    except CalledProcessError as error:
        log('ATS ERROR: Command failed: error code %d' % error.returncode, echo=True)
        log('Failed Command: %s' % cmd_line, echo=True)
        if exit:
            raise SystemExit(1)
    except OSError as error:
        log('ATS ERROR: Command failed with OSError: traceback %s' % error.child_traceback, echo=True)
        log('Failed Command: %s' % cmd_line, echo=True)
        if exit:
            raise SystemExit(1)

    return ( stdout_txt, stderr_txt )


# --------------------------------------------------------------------------
#
# Alternative to runCommand.
# Sends output to screen AND file.
# Run with '-v' to set optionsVerbose and see data sent to the screen.
# Returns a single file, with stdout and stderr in it.
#
# --------------------------------------------------------------------------
def execute(cmd_line, file_name=None, verbose=False):
    """
    Function to run a command and display output to screen.
    """
    log(f'Execute command line: {cmd_line}', echo=verbose)
    completed_process = subprocess.run(cmd_line.split(), text=True,
                                       stdout=PIPE, stderr=STDOUT)
    if verbose:
        # Writes to ats.log
        log(completed_process.stdout, echo=True)
    if file_name:
        with open(file_name, 'w') as log_file:
            log_file.write(f'Command: {cmd_line}\n{completed_process.stdout}')
            if completed_process.returncode:
                log_file('ATS ERROR: Command failed: error code '
                         f'{completed_process.returncode}')
    if completed_process.returncode:
        log(f'ATS ERROR: Command failed: error code {completed_process.returncode}',
            echo=True)

    return completed_process.returncode


####################################################################################
#
#  List just the directories within a directory
#  List just the dated directories within a directory which look like '2010_09'
#  List just the files within a directory
#  List just html files within a directory that look like '2010_09_28.html'
#
####################################################################################
def listdirs(folder):
    try:
        dir_list = [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]
    except OSError as error:
        log("ATS WARNING - listdirs: %s" % error.strerror, echo=True)
        dir_list = []
    return dir_list

def listDatedDirs(folder):
    try:
        dir_list = [d for d in os.listdir(folder) \
                      if re.search('2[0-9][0-9][0-9]_[0-9][0-9]$', d) \
                      if os.path.isdir(os.path.join(folder, d))]
    except OSError as error:
        log("ATS WARNING - listDatedDirs: %s" % error.strerror, echo=True)
        dir_list = []
    return dir_list

def listfiles(folder):
    try:
        file_list = [d for d in os.listdir(folder) if os.path.isfile(os.path.join(folder, d))]
    except OSError as error:
        log("ATS WARNING - listfiles: %s" % error.strerror, echo=True)
        file_list = []
    return file_list

####################################################################################

def copyFile(filename, srcdir, destdir, groupID):
    srcfile = os.path.join( srcdir, filename)
    if os.path.isfile(srcfile):
        shutil.copy(srcfile, destdir)
        destfile = os.path.join(destdir, os.path.basename(filename))
        try:
            os.chown( destfile, -1, groupID)
            os.chmod( destfile, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP )
        except OSError as error:
            log('ATS WARNING - failed to set permissions on %s: %s' % ( destfile, error.strerror),
                echo=True)
        return destfile
    else:
        log("ATS WARNING - copyFile: %s file does not exist in %s." % (filename, srcdir),
            echo=True )
        # raise Exception("\n\n\t%s file does not exist in %s." % (filename, srcdir) )

def copyAndRenameFile(filename, newfilename, srcdir, destdir, groupID):
    srcfile = os.path.join( srcdir, filename)
    if os.path.isfile(srcfile):
        destfile = os.path.join(destdir, os.path.basename(newfilename) )
        shutil.copyfile(srcfile, destfile)
        try:
            os.chown( destfile, -1, groupID)
            os.chmod( destfile, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP )
        except OSError as error:
            log('ATS WARNING - failed to set permissions on %s: %s' % ( destfile, error.strerror),
                echo=True)
        return destfile
    else:
        log("ATS WARNING - copyAndRenameFile: %s file does not exist in %s." % (filename, srcdir),
            echo=True )
        #raise Exception("\n\n\t%s file does not exist." % (srcfile) )

####################################################################################

def makeDir( new_dir ):
    if not os.path.exists(new_dir):
        try:
            os.mkdir( new_dir )

        except OSError as error:
            log('ATS ERROR: making %s: %s' %( new_dir, error.strerror), echo=True)
            raise SystemExit(1)

    elif not os.path.isdir(new_dir):
        log('ATS ERROR: %s exists and is NOT a directory' % new_dir, echo=True)
        raise SystemExit(1)

def makeSymLink( path, target ):
    if not os.path.exists(target):
        try:
            os.symlink( path, target )

        except OSError as error:
            log('ATS ERROR: making link to %s: %s' %( target, error.strerror), echo=True)
            raise SystemExit(1)

    elif os.path.islink(target):
        try:
            os.unlink( target)
            os.symlink( path, target )

        except OSError as error:
            log('ATS ERROR: making link to %s: %s' %( target, error.strerror), echo=True)
            raise SystemExit(1)

    else:
        log('ATS ERROR: %s exists and is NOT a symlink' % target, echo=True)
        raise SystemExit(1)




####################################################################################

def getGroupID( group_name ):
    gid = grp.getgrnam( group_name )[2]
    return gid

####################################################################################

def readFile(filename):
    lines = []
    if os.path.isfile(filename):
        ifp = open(filename,  'r')
        lines = ifp.readlines()
        ifp.close()
#    else:
#        raise Exception("\n\n\t%s file does not exist." % (filename) )
    return lines

def findKeyVal(lines, key, sep):
    value = ""
    for line in lines:
        if (line.find(key) >= 0) :
            toks = line.partition(sep)
            value  = toks[2]
            value2 = value.lstrip()
            value  = value2.rstrip()
            break

    return value

####################################################################################
def setUrlFromPath( path ):
    lc_server_path = '/usr/global/web-pages/lc/www/'
    if path.startswith( lc_server_path ):
        url = path.replace( lc_server_path, 'https://rzlc.llnl.gov/')
    else:
        url = 'file://' + os.path.abspath(path)

    return url

####################################################################################
def setDirectoryPermissions( dir, groupID):
    try:
        os.chown( dir, -1, groupID)
        os.chmod( dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_ISUID | stat.S_ISGID )
    except:
        log('ATS WARNING - failed to set permissions on directory ' + dir, echo=True)


def setFilePermissions( file, groupID):
    try:
        os.chown( file, -1, groupID)
        os.chmod( file, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP )
    except:
        log('ATS WARNING - failed to set permissions on file ' + file, echo=True)

####################################################################################
# Routine to delete sandbox dirs in the current dir
####################################################################################
def clean_old_sandboxes():
    names = os.listdir(".")
    for name in names:
        if name.startswith("sandbox"):
            if os.path.isdir(name):
                print("Removing %s" % (name))
                shutil.rmtree(name)

####################################################################################
# Routine to delete ats log  in the current dir
####################################################################################
def clean_old_ats_log_dirs():
    names = os.listdir(".")
    for name in names:
        if name.startswith("blueos_3") or name.startswith("toss_4_x86_64_ib") or name.startswith("toss_3_x86_64_ib"):
            if name.endswith("logs"):
                if os.path.isdir(name):
                    print("Removing %s" % (name))
                    shutil.rmtree(name)

####################################################################################
# Set the interactive partition, which may vary across machines
####################################################################################
def get_interactive_partition():
    temp_uname   = os.uname()
    host         = temp_uname[1]
    interactive_partition = "pdebug"
    if 'muir' in host:
        interactive_partition = "views"
    elif 'rzwhamo' in host:
        interactive_partition = "nvidia"

    return interactive_partition

####################################################################################
# set command MACHINT_TYPES based on SYS_TYPE
####################################################################################
def set_machine_type_based_on_sys_type():
    temp_uname   = os.uname()
    host         = temp_uname[1]

    print(host)

    try:
        if host.startswith('rzzeus'):
            os.environ['MACHINE_TYPE'] = 'slurm8'

        elif host.startswith('sierra') or host.startswith('aztec'):
            os.environ['MACHINE_TYPE'] = 'slurm12'

        elif host.startswith('rzmerl') or host.startswith('cab') or host.startswith('surface') or \
             host.startswith('syrah') or host.startswith('max') or host.startswith('pinot') or \
             host.startswith('zin'):
            os.environ['MACHINE_TYPE'] = 'slurm16'

        elif host.startswith('rzalastor'):
            os.environ['MACHINE_TYPE'] = 'slurm20'

        elif host.startswith('catalyst'):
            os.environ['MACHINE_TYPE'] = 'slurm24'

        elif host.startswith('herd'):
            os.environ['MACHINE_TYPE'] = 'slurm32'

        elif host.startswith('rzgenie') or host.startswith('rztrona') or \
             host.startswith('borax') or host.startswith('quartz') or host.startswith('agate') or \
             host.startswith('pascal') or host.startswith('jade') or host.startswith('mica'):
            os.environ['MACHINE_TYPE'] = 'slurm36'

        elif host.startswith('corona'):
            os.environ['MACHINE_TYPE'] = 'slurm48'

        elif host.startswith('poodle') or host.startswith('rzwhippet'):
            os.environ['MACHINE_TYPE'] = 'slurm112'

        elif host.startswith('mammoth'):
            os.environ['MACHINE_TYPE'] = 'slurm128'

        elif host.startswith('tioga') or host.startswith('rzadams') or \
             host.startswith('rzvernal') or host.startswith('tuolumne'):
            os.environ['MACHINE_TYPE'] = 'flux00'

        elif os.environ['SYS_TYPE'] in ['bgqos_0']:
            os.environ['MACHINE_TYPE'] = 'bgqos_0_ASQ'

        elif os.environ['SYS_TYPE'] in ['blueos_3_ppc64le_ib']:
            os.environ['MACHINE_TYPE'] = 'blueos_3_ppc64le_ib'

    except KeyError:
        pass


####################################################################################
# Routine to create test.ats type files based on generic input
# This first one is created for Bob Anderson's code, but this or variations on
# this could be used by many projects
#
# Inputs:
#     independent- single value
#     checker   - single value
#     test_ats  - single value
#     nprocs    - array of numbers
#  ** codes     - array of values (1 for each test, allows for different executables per test)
#     args      - array of args   (1 for each test, same length as codes array)
#     sandbox   - array of values (1 for each test, same length as codes array)
#
####################################################################################
def create_ats_file_version_001(independent, checker, test_ats, nprocs, codes, args, sandbox):

    if len(codes) != len(args):
        sys.exit("Bummer! length of codes array (%d) must be same as length of args array (%d)" % (len(codes), len(args)))

    if len(codes) != len(sandbox):
        sys.exit("Bummer! length of codes array (%d) must be same as length of sandbox array (%d)" % (len(codes), len(args)))

    ofp = open(test_ats, 'w')

    ofp.write("import os\n")

    if independent:
        ofp.write("glue(independent=True)\n")
    else:
        ofp.write("glue(independent=False)\n")

    ofp.write("glue(keep=True)\n")

    if (checker.startswith('/')):
        ofp.write("my_checker = '%s'\n" % (checker))                  # Handle absolute path
    else:
        ofp.write("my_checker = '%s/%s'\n" % (os.getcwd(), checker))  # Hancle checker in current dir

    test_num = 1

    for nproc in nprocs:
        args_ndx = 0
        for code in codes:
            ofp.write("t%d=test  (executable = '%s', clas = '%s', label='%s_%d', np=%d, sandbox=%s)\n" % \
                (test_num,code,args[args_ndx],code,test_num,nproc,sandbox[args_ndx]))
            test_num = test_num + 1
            ofp.write("t%d=testif(t%d, executable = %s, clas = t%d.outname)\n" % (test_num,test_num - 1, 'my_checker',test_num - 1))
            test_num = test_num + 1
            args_ndx = args_ndx + 1

    ofp.close()

    print("Most Excellent! Created ats test file %s\n" % test_ats)

####################################################################################
# Routine to create test.ats type files based on generic input
#
# Same as above, but do not prepend srun to the checker (required for some project)
#
# Inputs:
#     independent- single value
#     checker   - single value
#     test_ats  - single value
#     nprocs    - array of numbers
#  ** codes     - array of values (1 for each test, allows for different executables per test)
#     args      - array of args   (1 for each test, same length as codes array)
#     sandbox   - array of values (1 for each test, same length as codes array)
#
####################################################################################
def create_ats_file_version_001_nosrun_on_checker(independent, checker, test_ats, nprocs, codes, args, sandbox):

    if len(codes) != len(args):
        sys.exit("Bummer! length of codes array (%d) must be same as length of args array (%d)" % (len(codes), len(args)))

    if len(codes) != len(sandbox):
        sys.exit("Bummer! length of codes array (%d) must be same as length of sandbox array (%d)" % (len(codes), len(args)))

    ofp = open(test_ats, 'w')

    ofp.write("import os\n")

    if independent:
        ofp.write("glue(independent=True)\n")
    else:
        ofp.write("glue(independent=False)\n")

    ofp.write("glue(keep=True)\n")

    if (checker.startswith('/')):
        ofp.write("my_checker = '%s'\n" % (checker))                  # Handle absolute path
    else:
        ofp.write("my_checker = '%s/%s'\n" % (os.getcwd(), checker))  # Hancle checker in current dir

    test_num = 1

    for nproc in nprocs:
        args_ndx = 0
        for code in codes:
            ofp.write("t%d=test  (executable = '%s', clas = '%s', label='%s_%d', np=%d, sandbox=%s)\n" % \
                (test_num,code,args[args_ndx],code,test_num,nproc,sandbox[args_ndx]))
            test_num = test_num + 1
            ofp.write("t%d=testif(t%d, executable = %s, clas = t%d.outname, nosrun=True)\n" % (test_num,test_num - 1, 'my_checker',test_num - 1))
            test_num = test_num + 1
            args_ndx = args_ndx + 1

    ofp.close()

    print("Most Excellent! Created ats test file %s\n" % test_ats)

####################################################################################
# Routine to create test.ats type files based on generic input
# This one is created for Steve Langer code, but this or variations on
# this could be used by many projects
#
# This one does not have a checker, just run the tests.
# This one has a 'stdin' file argument
####################################################################################
def create_ats_file_version_002(independent, test_ats, nprocs, codes, args, stdin_file, sandbox):

    if len(codes) != len(args):
        sys.exit("Bummer! length of codes array (%d) must be same as length of args array (%d)" % (len(codes), len(args)))

    if len(codes) != len(sandbox):
        sys.exit("Bummer! length of codes array (%d) must be same as length of sandbox array (%d)" % (len(codes), len(args)))

    if len(codes) != len(stdin_file):
        sys.exit("Bummer! length of codes array (%d) must be same as length of stdin_file  array (%d)" % (len(codes), len(stdin_file)))

    ofp = open(test_ats, 'w')

    ofp.write("import os\n")

    if independent:
        ofp.write("glue(independent=True)\n")
    else:
        ofp.write("glue(independent=False)\n")

    ofp.write("glue(keep=True)\n")

    test_num = 0

    for nproc in nprocs:
        args_ndx = 0
        for code in codes:
            ofp.write("t%d=test  (executable = '%s', clas = '%s', stdin='%s', label='%d', np=%d, sandbox=%s)\n" % \
                (test_num,code,args[args_ndx],stdin_file[args_ndx],test_num,nproc,sandbox[args_ndx]))
            test_num = test_num + 1
            args_ndx = args_ndx + 1

    ofp.close()

    print("Most Excellent! Created ats test file %s\n" % test_ats)


####################################################################################
# Routine to create test.ats type files based on generic input
#
# Same as the 001 versions, but
# *) just use a single value for the 'codes' argument.
# *) same executable is used for all tests.
# *) same sandbox option is used for all tests.
# *) no srun on checker is the default
#
# Inputs:
#     independent- single value
#     checker   - single value
#     test_ats  - single value
#     nprocs    - array of number
#  ** code      - single value (same code for all tests)
#     args      - array of args   (1 for each test)
#  ** sandbox   - single value
#
####################################################################################
def create_ats_file_version_003(independent, checker, test_ats, nprocs, code, args, sandbox):

    ofp = open(test_ats, 'w')

    ofp.write("import os\n")

    if independent:
        ofp.write("glue(independent=True)\n")
    else:
        ofp.write("glue(independent=False)\n")

    ofp.write("glue(keep=True)\n")

    if (checker.startswith('/')):
        ofp.write("my_checker = '%s'\n" % (checker))                  # Handle absolute path
    else:
        ofp.write("my_checker = '%s/%s'\n" % (os.getcwd(), checker))  # Hancle checker in current dir

    test_num = 1

    for nproc in nprocs:
        args_ndx = 0
        for arg in args:
            ofp.write("t%d=test  (executable = '%s', clas = '%s', label='%s_%d', np=%d, sandbox=%s)\n" % \
                (test_num,code,arg,code,test_num,nproc,sandbox))
            test_num = test_num + 1
            ofp.write("t%d=testif(t%d, executable = %s, clas = t%d.outname, nosrun=True)\n" % (test_num,test_num - 1, 'my_checker',test_num - 1))
            test_num = test_num + 1
            args_ndx = args_ndx + 1

    ofp.close()

    print("Most Excellent! Created ats test file %s\n" % test_ats)

####################################################################################
# Routine to create test.ats type files based on generic input
#
# This one may be called multiple times, with an optional 'init_test_num' argument.
# The first time, called without this argument (or with it set to 0), the file
# will be created and the header info printed.
# Subsequent calls will append more test to the call.  The returned test_num should
# be passed back in on subsequent calls so that the test numbers will be ordered
# correctly.
#
# *) nprocs and nprocs_code_args must be the same length.
# *) same executable is used for all tests.
# *) same sandbox option is used for all tests.
# *) no srun on checker is the default
#
# Inputs:
#     independent       - single value
#     checker          - single value
#     test_ats         - single value
#     nprocs           - array of number
#     nprocs_code_args - array of same length as nprocs
#     code             - single value (same code for all tests)
#     args             - array of args   (1 for each test)
#     sandbox          - single value
#     init_test_num    - optional argument
#
####################################################################################
def create_ats_file_version_004(independent, checker, test_ats, nprocs, nprocs_code_args, code, args, sandbox, init_test_num=0):

    if len(nprocs) != len(nprocs_code_args):
        sys.exit("Bummer! length of nprocs array (%d) must be same as length of nprocs_code_args array (%d)" % (len(nprocs), len(nprocs_code_args)))

    test_num = 1

    if (init_test_num < 1):

        ofp = open(test_ats, 'w')

        ofp.write("import os\n")

        if independent:
            ofp.write("glue(independent=True)\n")
        else:
            ofp.write("glue(independent=False)\n")

        ofp.write("glue(keep=True)\n")

        if (checker.startswith('/')):
            ofp.write("my_checker = '%s'\n" % (checker))                  # Handle absolute path
        else:
            ofp.write("my_checker = '%s/%s'\n" % (os.getcwd(), checker))  # Hancle checker in current dir
    else:
        ofp = open(test_ats, 'a')
        test_num = init_test_num

    nprocs_ndx = 0

    for nproc in nprocs:
        args_ndx = 0
        nprocs_code_arg = nprocs_code_args[nprocs_ndx]
        for arg in args:
            ofp.write("t%d=test  (executable = '%s', clas = '%s %s', label='%s_%d', np=%d, sandbox=%s)\n" % \
                (test_num,code,nprocs_code_arg, arg,code,test_num,nproc,sandbox))
            test_num = test_num + 1
            ofp.write("t%d=testif(t%d, executable = %s, clas = t%d.outname, nosrun=True)\n" % (test_num,test_num - 1, 'my_checker',test_num - 1))
            test_num = test_num + 1
            args_ndx = args_ndx + 1

        nprocs_ndx = nprocs_ndx + 1

    ofp.close()

    print("Most Excellent! Created ats test file %s\n" % test_ats)

    return test_num


####################################################################################
# Routine to create test.ats type files based on generic input
# This first one is created for Spike  and Jerome
#
# Inputs:
#     independent      - single value -- applied to code not checkers
#     sandbox          - single value -- applied to code not checkers
#     ignoreReturnCode - single value -- applied to code not checkers
#     nosrun           - single value -- applied to code not checkers
#     test_ats         - single value -- file to create
#     checker1         - single value (checker executable)
#     checker2         - single value (checker executable)
#     code             - single value (test executable)
#     code_args        - array of args for the code      (1 for each test)
#     tobedeleted      - array of tobedeleted file names (1 for each test)
#     checker_out_logs - array of args for the checker   (1 for each test, same length as code args)
#     checker_err_logs - array of args for the checker   (1 for each test, same length as code args)
#
####################################################################################
def create_ats_file_version_005(independent, sandbox, ignoreReturnCode, nosrun, test_ats, checker1, checker2, code, code_args, tobedeleted, checker_out_logs, checker_err_logs):

    if len(code_args) != len(checker_out_logs):
        sys.exit("Bummer! length of code_args array (%d) must be same as length of checker_out_logs array (%d)" % (len(code_args), len(checker_out_logs)))

    if len(code_args) != len(checker_err_logs):
        sys.exit("Bummer! length of code_args array (%d) must be same as length of checker_err_logs array (%d)" % (len(code_args), len(checker_err_logs)))

    ofp = open(test_ats, 'w')

    ofp.write("import os\n")

    ofp.write("glue(independent=%s)\n" % (independent))

    ofp.write("glue(keep=True)\n")

    if (checker1.startswith('/')):
        ofp.write("my_checker1 = '%s'\n" % (checker1))                  # Handle absolute path to code
        my_checker1= checker1                                           # Handle absolute path to code
    else:
        ofp.write("my_checker1 = '%s/%s'\n" % (os.getcwd(), checker1))  # Handle path relative to current dir
        my_checker1 = '%s/%s' % (os.getcwd(), checker1)                 # Handle path relative to current dir

    if (checker2.startswith('/')):
        ofp.write("my_checker2 = '%s'\n" % (checker2))                  # Handle absolute path to code
        my_checker2= checker2                                           # Handle absolute path to code
    else:
        ofp.write("my_checker2 = '%s/%s'\n" % (os.getcwd(), checker2))  # Handle path relative to current dir
        my_checker2 = '%s/%s' % (os.getcwd(), checker2)                 # Handle path relative to current dir

    if (code.startswith('/')):
        my_code = code                                                # Handle absolute path to code
    else:
        my_code = '%s/%s' % (os.getcwd(), code)                       # Handle parth relative to current dir

    test_num = 1
    args_ndx = 0

    for code_arg in code_args:

        ofp.write("t%d=test  (executable = '%s', clas = '%s %s', label='%s', np=%d, sandbox=%s, nosrun=%s, ignoreReturnCode=%s)\n" % \
            (test_num, my_code, code_args[args_ndx], tobedeleted[args_ndx], code_args[args_ndx], 1, sandbox, nosrun, ignoreReturnCode) )
        test_num = test_num + 1

        ofp.write("t%d=testif(t%d, executable = %s, clas = t%d.outname + ' %s', label='%s_out_checker', np=1, nosrun=True)\n" % \
            (test_num, test_num - 1, 'my_checker1', test_num - 1, checker_out_logs[args_ndx], code_args[args_ndx]) )
        test_num = test_num + 1

        ofp.write("t%d=testif(t%d, executable = %s, clas = t%d.errname + ' %s', label='%s_err_checker', np=1, nosrun=True)\n\n" % \
            (test_num, test_num - 2, 'my_checker1', test_num - 2, checker_err_logs[args_ndx], code_args[args_ndx]) )
        test_num = test_num + 1

        ofp.write("t%d=testif(t%d, executable = %s, clas =  '%s', label='%s_inp_checker', np=1, nosrun=True)\n\n" % \
            (test_num, test_num - 3, 'my_checker2', tobedeleted[args_ndx], code_args[args_ndx]) )
        test_num = test_num + 1

        args_ndx = args_ndx + 1

    ofp.close()

    print("Most Excellent! Created ats test file %s\n" % test_ats)

    return test_num

####################################################################################
# end of file
####################################################################################
