"""
Configuration and command-line processing.

Attributes include SYS_TYPE, MACHINE_TYPE, MACHINE_DIR, BATCH_TYPE, usage,
options, defaultExecutable, inputFiles, timelimit, machine, batchmachine,
ATSROOT, cuttime, log.

The log object is created by importing log, but it can't write to a file
until we process the options and get the desired properties.
"""
from argparse import ArgumentParser
from glob import glob
import importlib
import os
import re
import sys
from ats import version
from ats.atsut import debug, abspath
from ats.log import log, terminal
from ats.times import atsStartTime, Duration
from ats import machines
from ats import executables

SYS_TYPE    = os.environ.get("SYS_TYPE", sys.platform)
my_host     = os.environ.get("HOST", "unset")
my_hostname = os.environ.get("HOSTNAME", "unset")

#print "SAD DEBUG configuration SYS_TYPE, my_host, my_hostname follow"
#print SYS_TYPE
#print my_host
#print my_hostname


# Set MACHINE_DIR by priority
#
# 1) MACHINE_OVERRIDE_DIR env var.
# 2) MACHINE_DIR env var
# 3) atsMachines.__path__
#
#  HACK: MACHINE_DIR and MACHINE__OVERRIDE_DIR used until discussion with dependent projects 

from ats import atsMachines
MACHINE_DIR = []
if "MACHINE_OVERRIDE_DIR" in os.environ.keys():
    MACHINE_DIR.append(abspath(os.environ.get('MACHINE_OVERRIDE_DIR')))

if "MACHINE_DIR" in os.environ.keys():
    MACHINE_DIR.append(abspath(os.environ.get('MACHINE_DIR')))

MACHINE_DIR.append(atsMachines.__path__[0])

#print "DEBUG 100"
#print MACHINE_DIR
#print "DEBUG 200"


#MACHINE_OVERRIDE_DIR = os.environ.get('MACHINE_OVERRIDE_DIR')
#if MACHINE_OVERRIDE_DIR:
#    MACHINE_OVERRIDE_DIR = abspath(MACHINE_OVERRIDE_DIR)

MACHINE_TYPE = os.environ.get('MACHINE_TYPE', SYS_TYPE)
BATCH_TYPE   = os.environ.get('BATCH_TYPE', SYS_TYPE)

class OptionParserWrapper(ArgumentParser):
    """ArgumentParser wrapper to help transition away from OptionParser."""

    _TYPES = {
        "complex": complex,
        "float": float,
        "int": int,
        "string": str,
    }

    """Handles arguments/options during 'optparse' --> 'argparse' upgrade."""
    def __init__(self, version, *args, **kwargs):
        super().__init__(*args, **kwargs)
        super().add_argument('--version', action='version', version=version)

    def add_option(self, *args, **kwargs):
        if 'type' in kwargs:
            kwargs['type'] = self._TYPES[kwargs['type']]
        super().add_argument(*args, **kwargs)


def addOptions(parser):
    """If not specified:
* default type is string
* default action is store
* default dest is long option name else short option name
"""
    parser.set_defaults(
        exclusive=True,
        blueos_ngpu=0,
        blueos_np=-1,
        cuttime=None,
    )

    # Platform agnostic options
    add_starting_options(parser)

    # Toss specific options
    if SYS_TYPE.startswith('toss'):
        add_toss3_only_options(parser)

    # Sierra Specific options
    if SYS_TYPE.startswith('blueos_3_ppc64le_ib'):
        add_blueos_only_options(parser)

    add_more_options(parser)


def add_starting_options(parser):
    # TODO: group SYS_TYPE specific options
    parser.add_option('--allInteractive', action='store_true',
                      help='Run every test in interactive mode.')
    parser.add_option('--combineOutErr', action='store_true',
                      help='For each test, combine its log and err files.')
    parser.add_option('--strict_nn', action='store_true',
                      help='''Strictly observe test "nn" options, this may
                      result in reduced througput or even slurm srun hangs.''')
    parser.add_option('--m_gpu', action='store_true', dest='mpi_um',
                      help='''Blueos option: Deprecated option. --smpiargs=-gpu
                      will be added by default to support MPI access to unified
                      memory. Synonym with --smpi_gpu''')
    parser.add_option('--smpi_gpu', action='store_true', dest='mpi_um',
                      help='''Blueos option: Deprecated option. --smpiargs=-gpu
                      will be added by default to support MPI access to unified
                      memory. Synonym with --m_gpu''')
    parser.add_option('--bypassSerialMachineCheck', action='store_true',
                      help='''Bypass check which prohibits ATS from running on
                      serial machines such as rztrona or borax.''')
    parser.add_option('--share', action='store_false', dest='exclusive',
                      help='''Toss 3 option: Use --share rather than the
                      default --exclusive on srun commands''')
    parser.add_option('--exclusive', action='store_true', dest='exclusive',
                      help='Toss 3 option: Use --exclusive on srun commands')


def add_blueos_only_options(parser):
    parser.add_option('--old_defaults', action='store_true',
                      dest='blueos_old_defaults', help='''Blueos option: Use
                      older default (prior to ATS version 5.9.98) settings
                      for enviroment vars and binding.''')
    parser.add_option('--jsrun_exclusive', action='store_true',
                      help='''Blueos option: Run each test exclusively on a
                      node(s). Do not share the node(s) with other tests.''')
    parser.add_option('--mpibind', action='store_true', dest='blueos_mpibind',
                      help='''Blueos option: Run the application under the
                      mpibind executable. Applicable to either lrun or jsrun.
                      Default to off.''')
    parser.add_option('--mpibind_executable', default='unset',
                      help='Specify path to mpibind.')
    parser.add_option('--lrun', action='store_true', dest='blueos_lrun',
                      help='''Blueos option: Use lrun to schedule jobs. To use
                      mpibind under lrun, also specify --mpibind''')
    parser.add_option('--lrun_pack', action='store_true',
                      dest='blueos_lrun_pack', help='''Blueos option: Use
                      lrun --pack. Needed to run multiple jobs concurrently
                      under lrun.  Not compatible with GPU codes without
                      additional flags (see -c and -g option with lrun
                      --help6)''')
    parser.add_option('--lrun_jsrun_args', dest='blueos_lrun_jsrun_args',
                      default='unset',
                      help='''Blueos option: lrun/jsrun args. Additional args
                      to pass to lrun or jsrun line.  Will be appended to
                      other args supplied by ATS. String is not checked for
                      validity.  Quotes in the string may need to be escaped
                      or otherwise specified''')
    parser.add_option('--lrun_np', dest='blueos_np', type='int',
                      help='''Blueos option: Over-rides test specific
                      settings of np (number of processors).  Useful for GPU
                      tests where the 4 MPI and 4 GPU devices are a common
                      testing scenario''')
    parser.add_option('--ompDisplayEnv', action='store_true',
                      help='''Blueos option: Set OMP_DISPLAY_ENV=True to see
                      detailed OMP settings at run time''')
    parser.add_option('--ompProcBind', default='unset',
                      help='''Blueos option: Set OMP_PROC_BIND to the given
                      string.''')
    parser.add_option('--jsrun', action='store_true', dest='blueos_jsrun',
                      help='''Blueos option: Use jsrun to schedule jobs. This
                      is also the default unless lrun is specified.''')
    parser.add_option('--jsrun_omp', action='store_true',
                      dest='blueos_jsrun_omp',
                      help='''Blueos option: Use jsrun with special options for
                      OMP built codes.''')
    parser.add_option('--jsrun_np', dest='blueos_np', type='int',
                      help='''Blueos option: Over-rides test specific settings
                      of np (number of processors).  Useful for GPU tests where
                      the 4 MPI and 4 GPU devices are a common testing
                      scenario''')
    parser.add_option('--jsrun_bind', dest='blueos_jsrun_bind',
                      default='unset',
                      help='''Blueos option: jsrun --bind option. "none",
                      "rs" or "packed" may be useful for some projects. Use
                      "jsrun --help" to see other -b, --bind options.  If
                      running with --mpibind this will be "none" and the
                      mpibind application will manage the binding''')
    parser.add_option('--jsrun_ngpu', dest='blueos_ngpu',
                      type='int', help='''Blueos option: Sets of orver-rides
                      test specific settings of ngpu (number of gpu devices
                      per resource/test case). Maps to jsrun --gpu_per_rs
                      option.  Default is 0. Number of GPU devices to use for
                      the test.''')
    parser.add_option('--lrun_ngpu', dest='blueos_ngpu',
                      type='int', help='''Blueos option: Sets of orver-rides
                      test specific settings of ngpu (number of gpu devices
                      per MPI process)) Maps to lrun -g option. Default is 0.
                      Number of GPU devices for each MPI rank in each test.
                      ''')


def add_toss3_only_options(parser):
    parser.add_option('--unbuffered', action='store_true',
                      help='Toss3 option: Pass srun the --unbuffered option.')
    parser.add_option('--mpibind', default='off',
                      help='''Toss3 option: Specify slurm --mpibind plugin
                      options to use. By default, ATS specifies --mpibind=off
                      on Toss 3 systems, but projects may want other options.
                      Common options are none, on, off.  srun --mpibind=help
                      will show further options.''')
    parser.add_option('--kmpAffinity', default='granularity=core',
                      help='''Toss3 option: Specify KMP_AFFINITY env var on
                      Toss3. By default ATS sets this to "granularity=core",
                      but end users may provide an arbitrary string''')
    parser.add_option('--nn', dest='toss_nn', type='int', default=-1,
                      help='''Toss3 option: -nn option. Over-rides test
                      specific settings of nn (number of nodes). Setting this
                      to 0 will allow multiple jobs to run per node
                      concurrently, even when nn is specified for individual
                      test cases.''')


def add_more_options(parser):
    # TODO: Review options for better organization
    parser.add_option('--sleepBeforeSrun', type='int', default=0,
                      help='''Number of seconds to sleep before each srun.
                      Default is 0 on all systems.''')
    parser.add_option('--continueFreq', type='float', default=None,
                      help='''Frequency in minutes to write a continuation
                      file. The default is to only write a continuation file at
                      the end of the run, and only if any tests failed.''')
    parser.add_option('--cutoff',
                      help='''Set the HALTED halt time limit on each test.
                      Over-rides job timelimit. All jobs will be HALTED at this
                      time. The value may be given as a digit followed by an s,
                      m, or h to give the time in seconds, minutes (the
                      default), or hours. This value if given causes jobs to
                      fail with status HALTED if they run this long and have
                      not already timed out or finished.''')
    parser.add_option('--debug', action='store_true',
                      help='''debug ; turn on debugging flag for detailed
                      debugging output during the run''')
    parser.add_option('-e', '--exec', dest='executable', metavar='EXEC',
                      default=sys.executable, help='Set code to be tested.')
    parser.add_option('-f', '--filter', action='append', dest='filter',
                      default=[],
                      help="""add a filter; may be repeated. Be sure to use
                      quotes if the filter contains spaces and remember that
                      the shell will remove one level of quotes. Example:
                      --filter 'np>2' would run only jobs needing more than 2
                      processors.""")
    parser.add_option('-g', '--glue', action='append', dest='glue',
                      default=[],
                      help="""set the default value for a test option; may be
                      repeated. Be sure to use quotes if the value contains
                      spaces and remember that the shell will remove one level
                      of quotes. Equivalent to using a glue statement at the
                      start of the input.""")
    parser.add_option('--hideOutput', action='store_true',
                      help='Do not print "magic" output lines in log.')
    parser.add_option('-i', '--info', action='store_true', dest='info',
                      help='''Show extra information about options and
                      machines.''')
    parser.add_option('-k', '--keep', action='store_true', dest='keep',
                      help='keep the output files')
    parser.add_option('--logs', dest='logdir', default='',
                      help='''sets the directory of the log file. Default is
                      arch.time.logs, where arch will be an
                      architecture-dependent name, and time will be digits of
                      the form yymmddhhmmss.''')
    parser.add_option('--level', type="int", default=0,
                      help='''Set the maximum level of test to run; zero for no
                      limit.''')
    parser.add_option('-n', '--npMax', dest='npMax', type="int", default=0,
                      help='''Max number of cores per node to utilize.
                      Overrides default ATS detection of cores per node.''')
    parser.add_option('--noUsageLogging', action='store_false',
                      dest='logUsage',
                      help='''Turn off logging ATS usage. (Code and test names
                      are never logged.)''')
    parser.add_option('--okInvalid', action='store_true',
                      help='Run tests even if there is an invalid test.')
    parser.add_option('--oneFailure', action='store_true',
                      help='Stop if a test fails.')
    parser.add_option('--reportFreq', type='int', default=1,
                      help='Number of minutes between periodic reports.')
    parser.add_option('--ompNumThreads', type='int', default=0,
                      help='''OMP_NUM_THREADS env setting ATS will set before
                      test run.''')
    parser.add_option('--cpusPerTask', type='int', default=-1,
                      help='''Slurm set -cpus_per_task option. Lrun set -c
                      option. Jsrun ignored.''')
    parser.add_option('--sequential', action='store_true',
                       help='''Run each test consecutively. Do not run
                       concurrent test jobs.''')
    parser.add_option('--nosrun', action='store_true',
                      help='Run the code without srun.')
    parser.add_option('--salloc', action='store_true',
                      help='Run the code with salloc rather than srun.')
    parser.add_option('--showGroupStartOnly', action='store_true',
                      help='''Only show start of first test in group, not
                      subsequent steps.''')
    parser.add_option('--checkForAtsProc', action='store_true',
                      help='''Attempt to determine if slurm thinks 1 processor
                      should be reserved for ATS -- may reduce total number of
                      MPI processes by 1.''')
    parser.add_option('--skip', action='store_true',
                      help='''skip actual execution of the tests, but show
                      filtering results and missing test files.''')
    # "terminal" will send the standard output and stderr to the
    # screen/terminal in real time as the test progresses.
    # "both" will send it to the screen and to a log file, but the
    #     output happens at the end of each test's run.
    parser.add_option('--testStdout', default='file',
                      help="""Redirect a test's stdout/stderr to a 'file'
                      (default), the 'terminal', 'both'. ote that 'terminal
                      sends the output in real time as the test progresses, but
                      'both' sends the output at the end of each test's run.
                      """)
    parser.add_option('--prerunScript', dest='globalPrerunScript',
                      default='unset',
                      help='Script to run before start of each test.')
    parser.add_option('--postrunScript', dest='globalPostrunScript',
                      default='unset',
                      help='Script to run after completion of each test.')
    parser.add_option('-t', '--timelimit', dest='timelimit', default='29m',
                      help='''Set the TIMEOUT default time limit on each test.
                      This may be over-ridden for specific tests.  Jobs will
                      TIMEOUT at this time.  The value may be given as a digit
                      followed by an s, m, or h to give the time in seconds,
                      minutes (the default), or hours.''')
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
                      help='''verbose mode; increased level of terminal output
                      ''')


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
    for opt_dest, opt_value in vars(options).items():
        log(f"{opt_dest}: {opt_value!r}")
    log.dedent()
    log.dedent()

def get_machine_factory(module_name, machine_class,
                        machine_package='ats.atsMachines'):
    """
    Get factory of type "machine_class" found in "module_name".

    Programmatically import and return definition of machine_class from
    module_name. "machine_package" tells Python where module_name can be found if
    not in the project's root directory.
    """
    machine_module = importlib.import_module(f'.{module_name}',
                                             package=machine_package)
    machine_factory = getattr(machine_module, machine_class)
    return machine_factory

def get_machine(file_text, file_name, is_batch=False):
    header = '#BATS:' if is_batch else '#ATS:'
    machine_type = BATCH_TYPE if is_batch else MACHINE_TYPE
    ats_lines = (ats_line for ats_line in file_text.splitlines()
                 if ats_line.startswith(header))
    for line in ats_lines:
        items = line[len(header):].split()
        machine_name, module_name, machine_class, npMaxH = items
        if machine_name == machine_type:
            if module_name == "SELF":
                module_name = os.path.splitext(file_name)[0]
            try:
                machine_factory = get_machine_factory(module_name,
                                                      machine_class)
                print(f"from ats.atsMachines.{module_name} "
                      f"import {machine_class} as Machine")
            except ModuleNotFoundError:
                machine_factory = get_machine_factory(module_name,
                                                      machine_class,
                                                      machine_package='atsMachines')
                print(f"from atsMachines.{module_name} "
                      f"import {machine_class} as Machine")
            machine = machine_factory(machine_name, int(npMaxH))
            break
    else:
        machine = None

    return machine


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
    machineDirs = MACHINE_DIR

    machineList = []
    for machineDir in machineDirs:
       log('machineDir', machineDir)
       py_files = os.path.join(machineDir, "*.py")
       machineList.extend([py_file for py_file in glob(py_files)
                           if not py_file.endswith('__init__.py')])
       sys.path.insert(0, machineDir)

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

    # Regex patterns looking for text at beginning of each line.
    ATS_PATTERN = re.compile(f'^#ATS:', re.MULTILINE)
    BATS_PATTERN = re.compile(f'^#BATS:', re.MULTILINE)
    BOTH_PATTERN = re.compile(f'^#B?ATS:', re.MULTILINE)

    for full_path in machineList:
        with open(full_path) as _file:
            file_text = _file.read()

        # Skip to next file if both '#ATS:' and '#BATS:' are not found.
        if not re.search(BOTH_PATTERN, file_text):
            continue

        file_name = os.path.basename(full_path)
        if not machine and re.search(ATS_PATTERN, file_text):
            machine = get_machine(file_text, file_name)
            specFoundIn = full_path

        if not batchmachine and re.search(BATS_PATTERN, file_text):
            batchmachine = get_machine(file_text, file_name, is_batch=True)
            bspecFoundIn = full_path

        if machine and batchmachine:
            break

    if machine is None:
        terminal("No machine specifications for", SYS_TYPE, "found, using generic.")
        machine = machines.Machine('generic', -1)

# create the option set
    usage = "usage: %(prog)s [options] [input files]"
    parser = OptionParserWrapper(
        usage=usage,
        version="%(prog)s " + version.version
    )
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
    options, inputFiles = parser.parse_known_args(argv)

# set up the test default options so the machine(s) can add to it
    options.testDefaults = {
        "np": 1,
        "batch": 0,
        "level": 1,
        "keep": options.keep,
        "hideOutput": options.hideOutput,
        "verbose": options.verbose,
        "testStdout": options.testStdout,
        "globalPrerunScript": options.globalPrerunScript,
        "globalPostrunScript": options.globalPostrunScript,
        "sequential": options.sequential,
        "nosrun": options.nosrun,
        "salloc": options.salloc
    }

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
    if 'ATSROOT' in os.environ:
        ATSROOT = os.environ['ATSROOT']
    else:
        ATSROOT = os.path.dirname(defaultExecutable.path)
