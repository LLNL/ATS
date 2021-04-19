import os
import sys

try:
  
  from ats import log, AtsError
  from ats import CREATED, INVALID, PASSED, FAILED, \
                  SKIPPED, BATCHED, RUNNING, FILTERED, TIMEDOUT

except ImportError:
  print 'Executing ats script', sys.argv[0], 'with', sys.executable
  print >>sys.stderr, "ats module cannot be imported; check Python path."
  print >>sys.stderr, sys.path
  raise SystemExit, 1


from   ASC_utils   import getProjectFunction
import ASC_State
import ASC_defaults
import ASC_onSave
from   ASC_Reports import createEnvironmentReport, TapestryReport11


addProjectOptions     = getProjectFunction( 'addProjectOptions',     ASC_defaults.addProjectOptions )
buildExecutable       = getProjectFunction( 'buildExecutable',       ASC_defaults.buildExecutable )
examineProjectOptions = getProjectFunction( 'examineProjectOptions', ASC_defaults.examineProjectOptions )
getDecksVersion       = getProjectFunction( 'getDecksVersion',       ASC_defaults.getDecksVersion )
getExecutableVersion  = getProjectFunction( 'getExecutableVersion',  ASC_defaults.getExecutableVersion )
getLogInfo            = getProjectFunction( 'getLogInfo',            ASC_defaults.getLogInfo )
getTestFiles          = getProjectFunction( 'getTestFiles',          ASC_defaults.getTestFiles )
getTestVersion        = getProjectFunction( 'getTestVersion',        ASC_defaults.getTestVersion )
setProjectDefines     = getProjectFunction( 'setProjectDefines',     ASC_defaults.setProjectDefines )
setProjectOnExitHooks = getProjectFunction( 'setProjectOnExitHooks', ASC_defaults.setProjectOnExitHooks )
setProjectOnSaveHooks = getProjectFunction( 'setProjectOnSaveHooks', ASC_defaults.setProjectOnSaveHooks )
updateTestingTree     = getProjectFunction( 'updateTestingTree',     ASC_defaults.updateTestingTree )

executable_version = ""

#####################################################################
#  Functions to setup testing
#####################################################################

def createDirectory( path ):
  """
  Create the directory specified by path.
  """
  try:
    
    if not os.path.exists(path):
      os.makedirs( path )
    elif not os.path.isdir(path):
      raise OSError
    
  except OSError:
    print 'Failed to create directory %s for testing' % path
    print 'Make sure it does not already exist'
    raise SystemExit, 1
    
      
def createTestingDirectory( options ):
  """
  Function to create testing directory and populate it with testing files. 
  """
  createDirectory( options.testingDirectory )
  os.chdir( options.testingDirectory )
  
  if not options.logdir:
    
    print "Log directory: %s" % log.directory
    old_log_dir = log.directory
    log_dirname = os.path.basename(log.directory)
    if hasattr(log, 'set_directory'):
      log.set_directory( log_dirname )
    else:
      log.set( log_dirname )
    log("Changed log directory from %s to %s" % ( old_log_dir, log.directory), echo = True)
  
  else:
    log("log directory is :%s:" % options.logdir,
        echo = True)
  

#####################################################################
#
# Functions called by ATSB or used in input decks
#
#####################################################################

def addOptions( parser ):
  """
  Adds project specific options to command line parsing
  """
  # Currently atsb has the following command line options
  #
  # Single letter: -e:, -f:, -g:, -h, -i, -k:, -n:, -t:, -v
  #
  # Long options: --version,  --help, --allInteractive, --checktime=TIME,
  #    --debug, --exec=EXEC, --filter=FILTER, --glue=GLUE, --hideOutput,
  #    --info, --keep=KEEP, --logs=LOGDIR, --level=LEVEL, --npMax=NPMAX,
  #    --okInvalid, --oneFailure, --quiet, --serial, --skip, --timelimit=TIMELIMIT,
  #    --verbose, --partition=PARTITION, --srunOnlyWhenNecessary,
  #    --nobatch
  #
  # So we cannot use them in our set of options.
  #
  
  parser.add_option('--abs', '--absTolerance', action='store', type='float', dest='abs_override',
                    default=-1.0,
                    help='absolute difference criteria, overrides per curve value')

  parser.add_option('--buildDirectory', action='store', dest='buildDirectory',
                    default="",
                    help='directory in which to build the executable')
  
  parser.add_option('--buildExecutable', action='store_true', dest='buildExecutable',
                    default=False,
                    help='build the executable used to run the tests')
  
  parser.add_option('--buildOptions', action='store', dest='buildOptions',
                    default="",
                    help='options used to build the executable')
  
  parser.add_option('--codeVersion', action='store', dest='codeVersion',
                    default="",
                    help='version of the code to build.')
  
  parser.add_option('--htmlDirectory', action='store', dest='htmlDirectory',
                    default="",
                    help='directory in which to put HTML files')
  
  parser.add_option('--makePrivateBaseline', action='store_true', dest='makePrivateBaseline',
                    default=False,
                    help='Make testing tree into a private baseline.')

  parser.add_option('--message', action='store', dest='message',
                    default="",
                    help='Message string to identify run')
  
  parser.add_option('--rebuildExecutable', action='store_true', dest='rebuildExecutable',
                    default=False,
                    help='rebuild the executable used to run the tests')
  
  parser.add_option('--regression', action='store_true', dest='regressionTest',
                    default=False,
                    help='run script in regression test mode')
  
  parser.add_option('--rel', '--relTolerance', action='store', type='float', dest='rel_override',
                    default=-1.0,
                    help='relative difference criteria, overrides per curve value')
    
  parser.add_option('--stateFile', action='store',
                    dest='stateFile',
                    default="",
                    help='file where ASC State is stored.')
  
  parser.add_option('--sourceDirectory', action='store', dest='sourceDirectory',
                    default='',
                    help='directory containing source code to build the executable')
  
  parser.add_option('--testingDirectory', action='store',
                    dest='testingDirectory',
                    default="",
                    help='directory in which to run tests')
  
  parser.add_option('--ultraChecker', action='store',
                    dest='ultraChecker',
                    default='',
                    help='script to be used to compare Ultra files.')
  
  parser.add_option('--ultraCheckerOpts', action='store',
                    dest='ultraCheckerOpts',
                    default='',
                    help='directory in which to run tests')

  parser.add_option('--updateBaseline', action='store_true', dest='updateBaseline',
                    default=False,
                    help='update baseline files for tests which fail')
  
  parser.add_option('--updateCode', action='store_true', dest='updateCodeVersion',
                    default=False,
                    help='update source code files')

  parser.add_option('--updateTests', action='store_true', dest='updateTests',
                    default=False,
                    help='Update the files in the testing tree tests')
  
  parser.add_option('--useJavaScript', action='store_true', dest='useJavaScript',
                    default=False,
                    help='Use JavaScript to create dynamic HTML pages')
  
  parser.add_option('--withoutHTML', action='store_false', dest='withHTML',
                    default=True,
                    help='Do not build HTML results pages.')

  addProjectOptions( parser )

  

def examineOptions( options ):
  """
  Checks for project specific command line options
  """
  global executable_version
  
  if ( ( options.buildExecutable or options.rebuildExecutable )  and
       options.executable != sys.executable ) :
    print 'Cannot use -e or --exec with --buildExecutable or --rebuildExecutable options'
    raise SystemExit, 1
  
  if options.testingDirectory:
    createTestingDirectory( options )

  # Set the HTML directory
  if not options.htmlDirectory:
    options.htmlDirectory = os.path.join(log.directory, 'html')
    
  examineProjectOptions( options )
  
  if options.testingDirectory:
    getTestFiles( options )
    
  if options.updateTests:
    updateTestingTree( options )
  
  if options.buildExecutable or options.rebuildExecutable:
    buildExecutable( options )
  
  executable_version = getExecutableVersion( options.executable )

  if options.message:
    log('Message: %s' % options.message, echo=True)

  log('Running tests for version: %s' % executable_version, echo=True)

  if options.regressionTest:
    ASC_State.state_file = ASC_State.openStateFile( getTestVersion, options=options  )
  
    if ASC_State.state_file.last_run_version:
      getLogInfo(options, ASC_State.state_file.last_run_version, executable_version)
    
    decks_version = getDecksVersion()

    ASC_State.state_file.setVersions( executable_version, decks_version )


def setDefines( manager ):
  """
  Define variables in the ATSB environment.
  """
  if log:
    log('Set ASC defines', echo = True)
  
  setProjectDefines( manager )
  

def setOnExitHooks( manager ):
  """
  Add functions to be called on exit of ATSB.
  """
  global executable_version

  # Add calls to manager.onExit here...
  manager.onExit(createEnvironmentReport)

  if log:
    log('Set ASC onExit hooks', echo = True)
  
  setProjectOnExitHooks( manager )

  report11 = TapestryReport11( executable_version, getTestVersion)
  manager.onExit( report11.createReport11 )

  # Call state file update after project onExit hooks are called,
  # so that baseline file can be updated first.
  if ASC_State.state_file:
    manager.onExit(ASC_State.state_file.update)
  

def setOnSaveHooks( manager ):
  """
  Add functions to be called when manager.saveResults is called.  The functions
  modify (add/change/delete) entries in the AttributeDictionary created by saveResults call
  """
  manager.onSave( ASC_onSave.addMachineInfo )
  
  setProjectOnSaveHooks( manager )
  


