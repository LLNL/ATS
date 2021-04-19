import os
import sys

try:
  
  from ats import log, AtsError
  from ats import manager as ats_manager

except ImportError:
  print 'Executing ats script', sys.argv[0], 'with', sys.executable
  print >>sys.stderr, "ats module cannot be imported; check Python path."
  print >>sys.stderr, sys.path
  raise SystemExit, 1


from   atsASC.modules.ASC_utils import makeDir
import atsASC.modules.ASC_State
import atsASC.modules.ASC_onSave
from   atsASC.modules.ASC_Reports import createEnvironmentReport, TapestryReport11
from   atsASC.modules.ASC_ATSB_Functions import finalReport, summary

#####################################################################

class ASCManager:

  def __init__(self, base_ASC_path):
    self.basePath           = base_ASC_path
    self.executable_version = ''
    self.delayedLogMessage  = ''
    self.verbose            = False
    self.HTML_report        = None

  #####################################################################
  #  Default Project Functions - these should be overridden by
  #  project class inheriting from ASCManager
  #####################################################################

  def addProjectOptions( self, parser ):
    '''
    Add project specific options to the parser.
    '''
    pass


  def buildProjectExecutable( self, options ):
    '''
    Build executable(s) needed to run the tests.
    '''
    raise SystemExit, 'ERROR - no project specific build function set!  Exiting...'


  def createProjectHTMLObject( self, options ):
    '''
    Create an object to control HTML reporting.
    '''
    return ( None )

  
  def examineProjectOptions( self, options ):
    '''
    Examine the project specific options set on the command line.
    '''
    pass


  def executeProjectPreRunChecks( self, manager ):
    """
    Check that everything for the project is set up properly before running tests.
    """
    pass


  def getProjectDecksVersion( self, path_to_decks='' ):
    '''
    Get the version associated with the input decks being used for the tests.
    '''
    return 'Unknown'


  def getProjectExecutableVersion( self, executable ):
    '''
    Get the version of the executable(s) being used for the tests.
    '''
    return 'Unknown'


  def getProjectLogInfo( self, options, last_run_version, executable_version ):
    '''
    Get the log information about the commits to the revision control system from
    last_run_version to executable_version.  Add link on HTML testing page, if HTML
    is being generated.
    '''
    pass


  def getProjectTestFiles( self, options ):
    '''
    Checks for needed test files.  If not present, check them out of testing repository
    '''
    raise SystemExit, 'ERROR - no project specific function set to get test files!  Exiting...'


  def getProjectTestVersion( self, test ):
    '''
    Get the version of the executable used to create the baseline files.
    '''
    return 'Unknown'


  def setProjectDefines( self, manager ):
    '''
    Define project variables in the ATSB environment.
    '''
    pass


  def setProjectOnExitHooks( self, manager ):
    '''
    Add functions to be called on exit of ATSB.
    '''
    pass


  def setProjectOnSaveHooks( self, manager ):
    '''
    Add functions to be called by the manager when the saveResults function is called.
    '''
    pass


  def updateProjectTestingTree( self, options ):
    '''
    Update the files needed to run the tests.
    '''
    raise SystemExit, 'ERROR - no project specific function set to update tests!  Exiting...'


  #####################################################################

  def createTestingDirectory( self, options ):
    """
    Function to create testing directory and put log files there.
    """
    makeDir( options.testingDirectory )
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
  # Functions called by run() or used in input decks
  #
  #####################################################################

  def addOptions( self, parser ):
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

    parser.add_option('--listTests', action='store_true', dest='listTests',
                      default=False,
                      help='List tests which would be run.')

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

    parser.add_option('--sortBy', action='append', dest='sortList',
                      help='Add attribute to list used to sort list of tests. Multiple ' + \
                            '--sortBy options are allowed and results are sorted in order' + \
                            'given. Default order is by name' )

    parser.add_option('--sourceDirectory', action='store', dest='sourceDirectory',
                      default='',
                      help='directory containing source code to build the executable')

    parser.add_option('--stateFile', action='store',
                      dest='stateFile',
                      default="",
                      help='file where ASC State is stored.')

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

    self.addProjectOptions( parser )


  def examineOptions( self, options ):
    """
    Checks for project specific command line options
    """
    if ( ( options.buildExecutable or options.rebuildExecutable )  and
         options.executable != sys.executable ) :
      print 'Cannot use -e or --exec with --buildExecutable or --rebuildExecutable options'
      raise SystemExit, 1

    if options.testingDirectory:
      self.createTestingDirectory( options )

    # Print out delayed log messages.  Needs to be done after possible call
    # of createTestingDirectory which changes the log directory.
    if self.delayedLogMessage:
      log( '------- Delayed Log Messages ------\n%s' % self.delayedLogMessage,
           echo=options.verbose)
      log( '------- End of Delayed Log Messages ------\n', echo=options.verbose)

    self.verbose = options.verbose
      
    # Set the HTML directory
    if not options.htmlDirectory:
      options.htmlDirectory = os.path.join(log.directory, 'html')

    self.examineProjectOptions( options )

    if options.withHTML:
      self.HTML_report = self.createProjectHTMLObject( options )

    if options.testingDirectory:
      self.getProjectTestFiles( options )

    if options.updateTests:
      self.updateProjectTestingTree( options )

    if options.buildExecutable or options.rebuildExecutable:
      self.buildProjectExecutable( options )

    self.executable_version = self.getProjectExecutableVersion( options.executable )

    if options.message:
      log('Message: %s' % options.message, echo=True)

    log('Running tests for version: %s' % self.executable_version, echo=True)

    if options.regressionTest:
      ASC_State.state_file = ASC_State.openStateFile( self.getProjectTestVersion,
                                                      options=options  )

      if ASC_State.state_file.last_run_version:
        self.getProjectLogInfo(options, ASC_State.state_file.last_run_version,
                        self.executable_version)

      decks_version = self.getProjectDecksVersion()

      ASC_State.state_file.setVersions( self.executable_version, decks_version )


  def setDefines( self, manager ):
    """
    Define variables in the ATSB environment.
    """
    if log:
      log('Set ASC defines', echo = True)

    self.setProjectDefines( manager )


  def setOnExitHooks( self, manager ):
    """
    Add functions to be called on exit of ATSB.
    """
    # Add calls to manager.onExit here...
    manager.onExit(createEnvironmentReport)

    report11 = TapestryReport11( self.executable_version, self.getProjectTestVersion)
    manager.onExit( report11.createReport11 )

    self.setProjectOnExitHooks( manager )

    # Call state file update after project onExit hooks are called,
    # so that baseline file can be updated first.
    if ASC_State.state_file:
      manager.onExit(ASC_State.state_file.update)

    if log:
      log('Set ASC onExit hooks', echo = True)


  def setOnSaveHooks( self, manager ):
    """
    Add functions to be called when manager.saveResults is called.  The functions
    modify (add/change/delete) entries in the AttributeDictionary created by saveResults call
    """
    manager.onSave( ASC_onSave.addMachineInfo )

    self.setProjectOnSaveHooks( manager )

    if log:
      log('Set ASC onSave hooks', echo = True)


  def reportTests ( self, test_list, sort_list ):

    for test in test_list:
      test.level = test.options.level
      if not test.np:
        test.np = 1

    test_list.sort(key=attrgetter(*sort_list))
    
    log('  %-30s  %4s  %4s' % ('Name', 'NP', 'Level'),
        echo=True)
    log('  %-30s  %4s  %4s' % ('-----------', '----', '-----'),
        echo=True)
    for test in test_list:
      log( '  %-30s  %4s  %4s' % ( test.name, test.np, test.level),
           echo=True)

    log('\n  %s tests found' % len(test_list), echo=True)


  def selectTests( self, testlist ):
    '''
    Select real tests.
    '''
    available_tests = [ t for t in testlist if t.status in [ INIT ] ]
    return available_tests

  def listTests(self):
    '''
    List the available tests
    '''
    # The following coding try block was lifted from manager.core()  
    # Collect the tests
    try:   # surround with keyboard interrupt, AtsError handlers

      ats_manager.collectTests()

    except AtsError:
      log("ATS error while collecting tests.", echo=True)
      log(traceback.format_exc(), echo=True)

    except KeyboardInterrupt:
      log("Keyboard interrupt while collecting tests, terminating.", echo=True)

    if ats_manager.options.verbose:
      finalReport( ats_manager )
    else:
      summary( ats_manager, log )

    available_tests = self.selectTests( ats_manager.testlist)

    if ats_manager.options.sortList is not None:
      self.reportTests( available_tests, ats_manager.options.sortList )
    else:
      self.reportTests( available_tests, ['name'] )

    return 0


  def executeTests( self ):
    '''
    This is most of an extended version of ats_manager.main().
    '''
    # Add functions to call on exit.
    self.setOnExitHooks( ats_manager )

    # Add functions to call when ats_manager.saveResults is called.
    self.setOnSaveHooks( ats_manager )

    # Run the tests
    ats_manager.firstBanner()

    result = ats_manager.core()

    ats_manager.finalReport()

    ats_manager.saveResults()

    for r in ats_manager.onExitRoutines:
      log("Calling %s" % r.__name__, echo=True)
      try:
        r(ats_manager)
      except Exception, error:
        log('  ERROR - unhandled exception calling %s' % r.__name__, echo=True)
        log('    %s' % error, echo=True)

    ats_manager.finalBanner()
    
    return result
  

  def executePreRunChecks( self, manager ):
    """
    Check that everything is set up properly before running tests.
    """
    if log:
      log('Executing pre-run checks', echo = True)

    self.executeProjectPreRunChecks( manager )


  def init(self):
    ats_manager.init( adder=self.addOptions, examiner=self.examineOptions )

    # Set project specific variables in the environment.
    self.setDefines( ats_manager )
    

##############################################################################

  def run( self ):
    '''
    This, combined with executeTests is an extended version of ats_manager.main().
    '''
    self.init()

    self.executePreRunChecks( ats_manager )

    if ats_manager.options.listTests:
      result = self.listTests()
    else:
      result = self.executeTests()

    return result
