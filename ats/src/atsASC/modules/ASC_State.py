import os
import sys
import shelve

from ats import log, PASSED, FAILED, TIMEDOUT

state_file = None

#####################################################################
#  Functions to create and manage State objects
#####################################################################

class ASC_StateFile:

  def __init__(self, file_name, getTestVersion):
    self.file_name              = file_name
    self.getBaselineTestVersion = getTestVersion
    
    self.db                = None
    self.decks_version     = ''
    self.last_run_version  = ''
    self.exec_version      = ''
    self.first_passed_dict = {}
    self.last_passed_dict  = {}
    self.kernel_list       = []

    status_file_existed = os.path.exists( file_name )

    try:
      self.db = shelve.open(file_name)
      if status_file_existed:
        self.decks_version     = self.db['decks_version']
        self.exec_version      = self.db['executable_version']
        self.first_passed_dict = self.db['first_passed_dict']
        self.last_passed_dict  = self.db['last_passed_dict']
        self.last_run_version  = self.exec_version
        
    except IOError, error:
      log('WARNING: problem opening ASC ATSB state file: %s' % file_name, echo=True)
      log('  Error: %s' % error.args, echo=True)
    

  def __del__(self):
    try:
      self.db.close()
      
    except IOError, error:
      log('Failed to close ASC ATSB state file: %s' % file_name, echo=True)
      log('  Error: %s' % error.args, echo=True)
      

  def __str__(self):
    header = """
ATSB Status Information

Last Executable Version Run: %s
Last Decks Version:          %s
                                                last        first
                                                passed      passed
test name(label)                                version     version
----+----1----+----2----+----3----+----4----+  ----+----   ----+----
"""
    
    mesg = header % (self.exec_version, self.decks_version )
    
    if self.kernel_list:
      kernels = self.kernel_list

    else:
      kernels = self.first_passed_dict.keys()
      kernels.sort()

    for kernel in kernels:
      mesg+= "%-45s  %8s    %8s\n" % ( kernel, self.last_passed_dict[kernel],
                                       self.first_passed_dict[kernel] )
    return mesg
  

  def extendKernelList(self, kernel_list):
    self.kernel_list.extend(kernel_list)
    

  def setVersions(self, exec_version, decks_version):
    self.exec_version  = exec_version
    self.decks_version = decks_version


  def update(self, manager):
    """
    Function to update the 'state' shelf file.
    """
    if manager.options.regressionTest:
      for test in manager.testlist:
        checker_test = test.options.get('checker_test')
        if checker_test:
          kernel       = test.options.get('kernel')
          test_version = self.getBaselineTestVersion(test)
          if test_version: 
            if test.status in [PASSED, FAILED, TIMEDOUT]:
              self.first_passed_dict[kernel] = test_version
              if kernel not in self.last_passed_dict.keys():
                self.last_passed_dict[kernel]  = ""
          else:
            if ( test.status in [PASSED] and 
                 kernel not in self.first_passed_dict.keys() ):
              self.first_passed_dict[kernel] = self.exec_version

          if test.status in [PASSED]:
            self.last_passed_dict[kernel]  = self.exec_version

      if manager.options.verbose:
        log("%s" % self, echo=True)
        
      self.db['executable_version'] = self.exec_version
      self.db['decks_version']      = self.decks_version
      self.db['first_passed_dict']  = self.first_passed_dict
      self.db['last_passed_dict']   = self.last_passed_dict
    
      log("Updated status shelf file.", echo=True)

#####################################################################

def openStateFile( getTestVersion, options=None):
  global state_file
  
  if options and options.stateFile:
    full_file_name = os.path.abspath( options.stateFile )
  else:
    full_file_name = os.path.join( os.getcwd(), "ASC_ATSB_State.db")

  if ( state_file is None or
       state_file.file_name != full_file_name ):
    state_file = ASC_StateFile(full_file_name, getTestVersion)

  return state_file
