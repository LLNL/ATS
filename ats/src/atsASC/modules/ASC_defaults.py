#########################################################################################
#
# Module to hold default functions which should be replaced by project specific functions.
#
#########################################################################################

def addProjectOptions( parser ):
  '''
  Add project specific options to the parser.
  '''
  pass

#########################################################################################

def buildExecutable( options ):
  '''
  Build executable(s) needed to run the tests.
  '''
  raise SystemExit, 'ERROR - no project specific build function set!  Exiting...'

#########################################################################################

def examineProjectOptions( options ):
  '''
  Examine the project specific options set on the command line.
  '''
  pass

#########################################################################################

def getDecksVersion( path_to_decks='' ):
  '''
  Get the version associated with the input decks being used for the tests.
  '''
  return 'Unknown'

#########################################################################################

def getExecutableVersion( executable ):
  '''
  Get the version of the executable(s) being used for the tests.
  '''
  return 'Unknown'

#########################################################################################

def getLogInfo( options, last_run_version, executable_version ):
  '''
  Get the log information about the commits to the revision control system from
  last_run_version to executable_version.  Add link on HTML testing page, if HTML
  is being generated.
  '''
  pass

#########################################################################################

def getTestFiles( options ):
  '''
  Checks for needed test files.  If not present, check them out of testing repository
  '''
  raise SystemExit, 'ERROR - no project specific function set to get test files!  Exiting...'

#########################################################################################

def getTestVersion( test ):
  '''
  Get the version of the executable used to create the baseline files.
  '''
  return 'Unknown'

#########################################################################################


def setProjectDefines( manager ):
  '''
  Define project variables in the ATSB environment.
  '''
  pass

#########################################################################################

def setProjectOnExitHooks( manager ):
  '''
  Add functions to be called on exit of ATSB.
  '''
  pass

#########################################################################################

def setProjectOnSaveHooks( manager ):
  '''
  Add functions to be called by the manager when the saveResults function is called.
  '''
  pass

#########################################################################################

def updateTestingTree( options ):
  '''
  Update the files needed to run the tests.
  '''
  raise SystemExit, 'ERROR - no project specific function set to update tests!  Exiting...'

#########################################################################################
