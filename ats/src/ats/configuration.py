"""
Configuration and command-line processing.

Attributes include SYS_TYPE, MACHINE_TYPE, MACHINE_DIR, BATCH_TYPE, usage,
options, defaultExecutable, inputFiles, timelimit, machine, batchmachine,
ATSROOT, cuttime, log.

The log object is created by importing log, but it can't write to a file
until we process the options and get the desired properties.
"""
import os, sys, socket
import version, atsut
from optparse import OptionParser
from atsut import debug, AttributeDict, abspath
from log import log, terminal
from times import atsStartTime, Duration
import machines
import executables

SYS_TYPE    = os.environ.get("SYS_TYPE", sys.platform)
my_host     = os.environ.get("HOST", "unset")
my_hostname = os.environ.get("HOSTNAME", "unset")

#print "SAD DEBUG configuration SYS_TYPE, my_host, my_hostname follow"
#print SYS_TYPE
#print my_host
#print my_hostname

#if SYS_TYPE is None or SYS_TYPE.startswith('linux'):
#    if my_host.startswith('tt') or my_host.startswith('tr'):
#        SYS_TYPE = "trinity_knl"

import atsMachines
MACHINE_DIR = atsMachines.__path__
#MACHINE_DIR = abspath(os.environ.get('MACHINE_DIR',
#                             os.path.join(sys.prefix, 'atsMachines')))
MACHINE_OVERRIDE_DIR = os.environ.get('MACHINE_OVERRIDE_DIR')
if MACHINE_OVERRIDE_DIR:
    MACHINE_OVERRIDE_DIR = abspath(MACHINE_OVERRIDE_DIR)

MACHINE_TYPE = os.environ.get('MACHINE_TYPE', SYS_TYPE)
BATCH_TYPE   = os.environ.get('BATCH_TYPE', SYS_TYPE)

def addOptions(parser):
    """If not specified:
* default type is string
* default action is store
* default dest is long option name else short option name
"""
    if SYS_TYPE.startswith('toss'):
        sleepBeforeSrunDefault=0
    else:
        sleepBeforeSrunDefault=0

    parser.set_defaults(
        allInteractive=False,
        combineOutErr=False,
        strict_nn=False,
        mpi_um=False,
        bypassSerialMachineCheck=False,
        exclusive=True,
        mpibind='off',
        mpibind_executable="unset",
        blueos_old_defaults=False,
        jsrun_exclusive=False,
        blueos_mpibind=False,
        blueos_lrun=False,
        blueos_lrun_pack=False,
        blueos_lrun_jsrun_args="unset",
        blueos_jsrun=False,
        blueos_jsrun_omp=False,
        blueos_jsrun_bind="unset",
        ompProcBind="unset",
        blueos_ngpu=0,
        # blueos_jsrun_nn=-1,
        blueos_np=-1,
        toss_nn=-1,
        kmpAffinity='granularity=core',
        bindToCore=False,
        bindToSocket=False,
        bindToHwthread=False,
        bindToL1cache=False,
        bindToL2cache=False,
        bindToL3cache=False,
        bindToNuma=False,
        bindToNone=False,
        bindToBoard=False,
        continueFreq=None,
        cuttime=None,
        debug=False,
        filter=[],
        glue=[],
        hideOutput=False,
        info=False,
        keep=False,
        logdir='',
        level=0,
        npMax=0,
        logUsage=False,
        okInvalid=False,
        oneFailure=False,
        reportFreq=1,
        ompNumThreads=0,
        cpusPerTask=-1,
        ompDisplayEnv=False,
        sleepBeforeSrun=sleepBeforeSrunDefault,
        sequential=False,
        nosrun=False,
        showGroupStartOnly=False,
        checkForAtsProc=False,
        skip=False,
        testStdout='file',
        globalPrerunScript='unset',
        globalPostrunScript='unset',
        timelimit='29m',
        verbose=False,
    )

    parser.add_option('--allInteractive', action='store_true', dest='allInteractive',
        help='Run every test in interactive mode.')

    parser.add_option('--combineOutErr', action='store_true', dest='combineOutErr',
        help='For each test, combine its log and err files.')

    parser.add_option('--strict_nn', action='store_true', dest='strict_nn',
        help='Strictly observe test "nn" options, this may result in reduced througput or even slurm srun hangs.')

    parser.add_option('--m_gpu', action='store_true', dest='mpi_um',
        help='Blueos option: Adds LSF option --smpiargs="-gpu" to enable CUDA aware MPI with unified or device memory. Synonym with --smpi_gpu option')

    parser.add_option('--smpi_gpu', action='store_true', dest='mpi_um',
        help='Blueos option: Adds LSF option --smpiargs="-gpu" to enable CUDA aware MPI with unified or device memory. Synonym with --m_gpu option')

    parser.add_option('--bypassSerialMachineCheck', action='store_true', dest='bypassSerialMachineCheck',
        help='Bypass check which prohibits ATS from running on serial machines such as rztrona or borax.')

    parser.add_option('--share', action='store_false', dest='exclusive',
        help='Toss 3 option: Use --share rather than the default --exclusive on srun commands')

    parser.add_option('--exclusive', action='store_true', dest='exclusive',
        help='Toss 3 option: Use --exclusive on srun commands')

    # Toss specific options
    if SYS_TYPE.startswith('toss'):
        parser.add_option('--mpibind', action='store', type='string', dest='mpibind',
            help='Toss3 option: Specify slurm --mpibind plugin options to use. By default, ATS specifies --mpibind=off on Toss 3 systems, but projects may want other options.  Common options are none, on, off.  srun --mpibind=help will show further options.')

        parser.add_option('--kmpAffinity', action='store', type='string', dest='kmpAffinity',
            help='Toss3 option: Specify KMP_AFFINITY env var on Toss3.  By default ATS sets this to "granularity=core", but end users may provide an arbitrary string')

        parser.add_option('--nn', dest='toss_nn', type='int',
            help='Toss3 option: -nn option. Over-rides test specific settings of nn (number of nodes).  Setting this to 0 will allow multiple jobs to run per node concurrently, even when nn is specified for individual test cases.')

    # Sierra Specific options
    if SYS_TYPE.startswith('blueos_3_ppc64le_ib'):

        parser.add_option('--old_defaults', action='store_true', dest='blueos_old_defaults',
            help='Blueos option: Use older default (prior to ATS version 5.9.98) settings for enviroment vars and binding.')

        parser.add_option('--jsrun_exclusive', action='store_true', dest='jsrun_exclusive',
            help='Blueos option: Run each test exclusively on a node(s). Do not share the node(s) with other tests.')

        parser.add_option('--mpibind', action='store_true', dest='blueos_mpibind',
            help='Blueos option: Run the application under the mpibind executable. Applicable to either lrun or jsrun.  Default to off.')

        parser.add_option('--mpibind_executable', action='store', type='string', dest='mpibind_executable',
            help='Specify path to mpibind.')

        parser.add_option('--lrun', action='store_true', dest='blueos_lrun',
            help='Blueos option: Use lrun to schedule jobs. To use mpibind under lrun, also specify --mpibind')

        parser.add_option('--lrun_pack', action='store_true', dest='blueos_lrun_pack',
            help='Blueos option: Use lrun --pack. Needed to run multiple jobs concurrently under lrun.  Not compatible with GPU codes without additional flags (see -c and -g option with lrun --help6)')

        parser.add_option('--lrun_jsrun_args', action='store', type='string', dest='blueos_lrun_jsrun_args',
            help='Blueos option: lrun/jsrun args. Additional args to pass to lrun or jsrun line.  Will be appendedto other args supplied by ATS. String is not checked for validity.  Quotes in the string may need to be escaped or otherwise specified')

        parser.add_option('--lrun_np', dest='blueos_np', type='int',
            help='Blueos option: Over-rides test specific settings of np (number of processors).  Useful for GPU tests where the 4 MPI and 4 GPU devices are a common testing scenario')

        parser.add_option('--ompDisplayEnv', action='store_true', dest='ompDisplayEnv',
            help='Blueos option: Set OMP_DISPLAY_ENV=True to see detailed OMP settings at run time')

        parser.add_option('--ompProcBind', action='store', type='string', dest='ompProcBind',
            help='Blueos option: Set OMP_PROC_BIND to the given string.')

        parser.add_option('--jsrun', action='store_true', dest='blueos_jsrun',
            help='Blueos option: Use jsrun to schedule jobs. This is also the default unless lrun is specified.')

        parser.add_option('--jsrun_omp', action='store_true', dest='blueos_jsrun_omp',
            help='Blueos option: Use jsrun with special options for OMP built codes.')

        # parser.add_option('--jsrun_nn', dest='blueos_jsrun_nn', type='int',
        #     help='Blueos option: Sets or over-rides test specific settings of nn (number of nodes).  Setting this to 0 will allow multiple jobs to run per node concurrently, even when nn is specified for individual test cases. Synonym with --nn option.')

        parser.add_option('--jsrun_np', dest='blueos_np', type='int',
            help='Blueos option: Over-rides test specific settings of np (number of processors).  Useful for GPU tests where the 4 MPI and 4 GPU devices are a common testing scenario')

        # parser.add_option('--nn', dest='blueos_jsrun_nn', type='int',
        #     help='Blueos option: Sets of over-rides test specific settings of nn (number of nodes).  Setting this to 0 will allow multiple jobs to run per node concurrently, even when nn is specified for individual test cases. Synonym with --jsrun_nn option.')

        parser.add_option('--jsrun_bind', action='store', type='string', dest='blueos_jsrun_bind',
            help='Blueos option: jsrun --bind option. "none", "rs" or "packed" may be useful for some projects. Use  "jsrun --help" to see other -b, --bind options.  If running with --mpibind this will be "none" and the mpibind application will manage the binding')

        parser.add_option('--jsrun_ngpu', dest='blueos_ngpu', type='int',
            help='Blueos option: Sets of orver-rides test specific settings of ngpu (number of gpu devices per resource/test case). Maps to jsrun --gpu_per_rs option.  Default is 0. Number of GPU devices to use for the test.')

        parser.add_option('--lrun_ngpu', dest='blueos_ngpu', type='int',
            help='Blueos option: Sets of orver-rides test specific settings of ngpu (number of gpu devices per MPI process)) Maps to lrun -g option. Default is 0. Number of GPU devices for each MPI rank in each test.')

    # Old Power8 MPI run options
    #if SYS_TYPE == "blueos_3_ppc64le_ib":
#
#        parser.add_option('--bind-to-core', action='store_true', dest='bindToCore',
#            help='Blueos option: Specify mpirun --bind-to core. By default, ATS uses --bind-to none')
#
#        parser.add_option('--bind-to-socket', action='store_true', dest='bindToSocket',
#            help='Blueos option: Specify mpirun --bind-to core. By default, ATS uses --bind-to none')
#
#        parser.add_option('--bind-to-hwthread', action='store_true',dest='bindToHwthread',
#            help='Blueos option: Specify mpirun --bind-to core. By default, ATS uses --bind-to none')
#
#        parser.add_option('--bind-to-l1cache', action='store_true', dest='bindToL1cache',
#            help='Blueos option: Specify mpirun --bind-to core. By default, ATS uses --bind-to none')
#
#        parser.add_option('--bind-to-l2cache', action='store_true', dest='bindToL2cache',
#            help='Blueos option: Specify mpirun --bind-to core. By default, ATS uses --bind-to none')
#
#        parser.add_option('--bind-to-l3cache', action='store_true', dest='bindToL3cache',
#            help='Blueos option: Specify mpirun --bind-to core. By default, ATS uses --bind-to none')
#
#        parser.add_option('--bind-to-numa', action='store_true', dest='bindToNuma',
#            help='Blueos option: Specify mpirun --bind-to core. By default, ATS uses --bind-to none')
#
#        parser.add_option('--bind-to-none', action='store_true', dest='bindToNone',
#            help='Blueos option: Specify mpirun --bind-to core. By default, ATS uses --bind-to none')
#
#        parser.add_option('--bind-to-board', action='store_true', dest='bindToBoard',
#            help='Blueos option: Specify mpirun --bind-to core. By default, ATS uses --bind-to none')
#
#        parser.add_option('--mpibind', action='store_true', dest='blueos_mpibind',
#            help='Blueos option: Run the application under the mpibind executable. This is necessary to access GPU device on Power8 (rzmanta) using mpirun. Default to off.')
#
    parser.add_option('--sleepBeforeSrun', dest='sleepBeforeSrun', type='int',
        help='Number of seconds to sleep before each srun. Default is 0 on all systems.')

    parser.add_option('--continueFreq', dest='continueFreq', type='float',
        help="""Frequency in minutes to write a continuation file. The default
is to only write a continuation file at the end of the run, and only if any
tests failed."""
        )

    parser.add_option('--cutoff', dest='cuttime',
        help="""Set the HALTED halt time limit on each test. Over-rides job timelimit.
All jobs will be HALTED at this time.
The value may be given as a digit followed by an s, m, or h to give the time in
seconds, minutes (the default), or hours. This value if
given causes jobs to fail with status HALTED if they
run this long and have not already timed out or finished."""
        )

    parser.add_option('--debug', action='store_true', dest='debug',
        help='debug ; turn on debugging flag for detailed debugging output during the run')

    parser.add_option('-e', '--exec', dest='executable', metavar='EXEC', default=sys.executable,
        help='Set code to be tested.')

    parser.add_option('-f', '--filter', action='append', dest='filter',
        help="""add a filter; may be repeated. Be sure to use quotes if the filter contains spaces and remember that the shell will remove one level of quotes.
Example: --filter 'np>2'
would run only jobs needing more than 2 processors.""")

    parser.add_option('-g', '--glue', action='append', dest='glue',
        help="""set the default value for a test option; may be repeated. Be sure to use quotes if the value contains spaces and remember that the shell will remove one level of quotes. Equivalent to using a glue
statement at the start of the input.""")

    parser.add_option('--hideOutput', action='store_true', dest='hideOutput',
        help = 'Do not print "magic" output lines in log.')

    parser.add_option('-i', '--info', action='store_true', dest='info',
        help='Show extra information about options and machines.')

    parser.add_option('-k', '--keep', action='store_true', dest='keep',
        help='keep the output files')

    parser.add_option('--logs', dest='logdir',
        help='sets the directory of the log file. Default is arch.time.logs, where arch will be an architecture-dependent name, and time will be digits of the form yymmddhhmmss.')

    parser.add_option('--level', dest='level', type="int",
        help='Set the maximum level of test to run; zero for no limit.')

    parser.add_option('-n', '--npMax', dest = 'npMax', type="int",
        help="Max number of cores per node to utilize. Overrides default ATS detection of cores per node.")

    parser.add_option('--noUsageLogging', action='store_false',
                      dest = 'logUsage',
        help='Turn off logging ATS usage.  (Code and '
             'test names are never logged.)')

    parser.add_option('--usageLogging', action='store_true',
                      dest = 'logUsage',
        help='Turn on logging ATS usage.  (Code and '
             'test names are never logged.)')

    parser.add_option('--okInvalid', action='store_true', dest='okInvalid',
        help='Run tests even if there is an invalid test.')

    parser.add_option('--oneFailure', action='store_true', dest='oneFailure',
        help='Stop if a test fails.')

    parser.add_option('--reportFreq', dest='reportFreq', type='int',
        help='Number of minutes between periodic reports.')

    parser.add_option('--ompNumThreads', dest='ompNumThreads', type='int',
        help='OMP_NUM_THREADS env setting ATS will set before test run.')

    parser.add_option('--cpusPerTask', dest='cpusPerTask', type='int',
        help='Slurm set -cpus_per_task option. Lrun set -c option. Jsrun ignored.')

    parser.add_option('--sequential', action='store_true', dest='sequential',
        help='Run each test consecutively.  Do not run concurrent test jobs.')

    parser.add_option('--nosrun', action='store_true', dest='nosrun',
        help='Run the code without srun.')

    parser.add_option('--showGroupStartOnly', action='store_true', dest='showGroupStartOnly',
        help='Only show start of first test in group, not subsequent steps.')

    parser.add_option('--checkForAtsProc', action='store_true', dest='checkForAtsProc',
        help='Attempt to determine if slurm thinks 1 processor should be reserved for ATS -- may reduce total number of MPI processes by 1.')

    parser.add_option('--skip', action='store_true', dest='skip',
        help='skip actual execution of the tests, but show filtering results and missing test files.')

    # "terminal" will send the standard output and stderr to the
    # screen/terminal in real time as the test progresses.
    # "both" will send it to the screen and to a log file, but the
    #     output happens at the end of each test's run.
    parser.add_option('--testStdout', action='store', type='string', dest='testStdout',
        help="""Redirect a test's stdout/stderr to a 'file' (default), the 'terminal', 'both'.
Note that 'terminal sends the output in real time as the test progresses,
but 'both' sends the output at the end of each test's run."""
        )

    parser.add_option('--prerunScript', action='store', type='string', dest='globalPrerunScript',
        help="""Script to run before start of each test."""
        )

    parser.add_option('--postrunScript', action='store', type='string', dest='globalPostrunScript',
        help="""Script to run after completion of each test."""
        )

    parser.add_option('-t', '--timelimit', dest='timelimit',
        help="""Set the TIMEOUT default time limit on each test. This may be over-ridden for specific tests.
Jobs will TIMEOUT at this time.  The value may be given
as a digit followed by an s, m, or h to give the time in seconds, minutes
(the default), or hours."""
        )

    parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
        help='verbose mode; increased level of terminal output')

def documentConfiguration():
    """Write the configuration to the log."""
    log('Configuration:')
    log.indent()
    log('Input files:',  inputFiles)
    log('Python path:', sys.executable)
    log('ATS from ', os.path.dirname(__file__))
    log('ATS version:', version.version)
    log('Options:')
    log.indent()
    olist = options.keys()
    olist.sort()
    for k in olist:
        log(k + ":", repr(getattr(options, k)))
    log.dedent()
    log.dedent()

def init(clas = '', adder = None, examiner=None):
    """Called by manager.init(class, adder, examiner)
       Initialize configuration and process command-line options; create log,
       options, inputFiles, timelimit, machine, and batchmatchine.
       Call backs to machine and to adder/examiner for options.
    """
    global log, options, inputFiles, timelimit, machine, batchmachine,\
           defaultExecutable, ATSROOT, cuttime

    init_debugClass = False

    if init_debugClass:
        print("DEBUG init entered clas=%s " % (clas))

    # get the machine and possible batch facility
#    machineDirs = [MACHINE_DIR]
    machineDirs = MACHINE_DIR

    if MACHINE_OVERRIDE_DIR:
        machineDirs.append(MACHINE_OVERRIDE_DIR)

    machineList = []
    for machineDir in machineDirs:
        machineList.extend(
            [os.path.join(machineDir,x) for x in os.listdir(machineDir)
             if x.endswith('.py') and not x.endswith('__init__.py')])

    machine = None
    batchmachine = None
    specFoundIn = ''
    bspecFoundIn = ''

    if init_debugClass:
        print("DEBUG init 100")
        print(machineDirs)
        print(machineList)
        print(MACHINE_TYPE)
        print("DEBUG init 200")

    for full_path in machineList:
        moduleName = ''
        fname = os.path.basename(full_path)
        # print "DEBUG 000 fname = %s" % fname
        f = open(full_path, 'r')
        for line in f:
            if line.startswith('#ATS:') and not machine:
                items = line[5:-1].split()
                machineName, moduleName, machineClass, npMaxH = items
                if init_debugClass:
                    print("DEBUG init machineName=%s moduleName=%s machineClass=%s npMaxH=%s" %
                          (machineName, moduleName, machineClass, npMaxH))

                # print "DEBUG init MACHINE_TYPE=%s machineName=%s moduleName=%s machineClass=%s npMaxH=%s" % (MACHINE_TYPE, machineName, moduleName, machineClass, npMaxH)

                if machineName == MACHINE_TYPE:
                    if moduleName == "SELF":
                        moduleName, junk = os.path.splitext(fname)
                    specFoundIn = full_path
                    print("from atsMachines.%s import %s as Machine" % (moduleName, machineClass))
                    exec('from atsMachines.%s import %s as Machine' % (moduleName, machineClass))
                    machine = Machine(machineName, int(npMaxH))

            elif line.startswith('#BATS:') and not batchmachine:
                items = line[6:-1].split()
                machineName, moduleName, machineClass, npMaxH = items

                if machineName == BATCH_TYPE:
                    if moduleName == "SELF":
                        moduleName, junk = os.path.splitext(fname)
                    bspecFoundIn = full_path
                    exec('from atsMachines.%s import %s as BMachine' % (moduleName, machineClass))
                    batchmachine = BMachine(moduleName, int(npMaxH))

        f.close()

        if machine and batchmachine:
            break

    if machine is None:
        terminal("No machine specifications for", SYS_TYPE, "found, using generic.")
        machine = machines.Machine('generic', -1)

# create the option set
    usage = "usage: %prog [options] [input files]"
    parser = OptionParser(usage=usage, version="%prog " + version.version)
    addOptions(parser)
    machine.addOptions(parser)
# add the --nobatch option but force it true if no batch facility here.
    parser.add_option('--nobatch', action='store_true', dest='nobatch', default=(batchmachine is None),
        help = 'Do not run batch jobs.')
    if batchmachine:
        batchmachine.addOptions(parser)
# user callback?
    if adder is not None:
        adder(parser)
# parse the command line
    if clas:
        import shlex
        argv = shlex.split(clas)
    else:
        argv = sys.argv[1:]
    (toptions, inputFiles) = parser.parse_args(argv)

# immediately make the options a real dictionary -- the way optparse leaves it
# is misleading.
    options = AttributeDict()
    for k in vars(toptions).keys():
        options[k] = getattr(toptions, k)

# set up the test default options so the machine(s) can add to it
    options['testDefaults'] = AttributeDict(np=1,
        batch=0,
        level=1,
        keep = options.keep,
        hideOutput = options.hideOutput,
        verbose = options.verbose,
        testStdout = options.testStdout,
        globalPrerunScript = options.globalPrerunScript,
        globalPostrunScript = options.globalPostrunScript,
        sequential = options.sequential,
        nosrun = options.nosrun
        )

# let the machine(s) modify the results or act upon them in other ways.
    machine.examineOptions(options)
    if batchmachine:
        batchmachine.examineOptions(options)
# unpack basic options
    debug(options.debug)
    if options.logdir:
        log.set(directory = options.logdir)
    else:
        dirname = SYS_TYPE + "." + atsStartTime + ".logs"
        log.set(directory = dirname)
    log.mode="w"
    log.logging = 1
# user callback?
    if examiner is not None:
        examiner(options)

    if specFoundIn:
        log("Found specification for", MACHINE_TYPE, "in", specFoundIn)
    else:
        log("No specification found for", MACHINE_TYPE, ', using generic')
    if bspecFoundIn:
        log("Batch specification for ", BATCH_TYPE, "in", bspecFoundIn)

# unpack other options
    cuttime = options.cuttime
    if cuttime is not None:
        cuttime = Duration(cuttime)
    timelimit = Duration(options.timelimit)
    defaultExecutable = executables.Executable(abspath(options.executable))
    # ATSROOT is used in tests.py to allow paths pointed at the executable's directory
    commandList = machine.split(repr(defaultExecutable))
    if 'ATSROOT' in os.environ:
        ATSROOT = os.environ['ATSROOT']
    else:
        ATSROOT = os.path.dirname(defaultExecutable.path)
