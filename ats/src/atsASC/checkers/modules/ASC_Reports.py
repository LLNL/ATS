import os
import sys
import shelve
from   operator import attrgetter

try:
  
  from ats import log, CREATED, INVALID, PASSED, FAILED, \
       SKIPPED, BATCHED, RUNNING, FILTERED, TIMEDOUT

except ImportError:
  print 'Executing ats script', sys.argv[0], 'with', sys.executable
  print >>sys.stderr, "ats module cannot be imported; check Python path."
  print >>sys.stderr, sys.path
  raise SystemExit, 1

#####################################################################
#  Functions to create test output reports
#####################################################################

def create_master_HTML_page( manager ):
  "Creates master page for HTML report of test results"
  #global version_text
  #print "%s\n" % version_text
  #log('\nCalled function to create HTML page test results from manager object\n',
  #    echo = True)
  pass

#####################################################################

class TapestryReport11:

  def __init__(self, exec_version, getTestVersion):
    self.executable_version = exec_version
    self.getTestVersion = getTestVersion
    
  def createReport11( self, manager ):
    """
    Function to create simple pass/fail report like the Tapestry 11.txt
    file.
    """
    header = """

Simple Pass/Fail Log based on ATSB status

                                                           exec        test
name(label)                                     status    version     version
----+----1----+----2----+----3----+----4----+  ----+---  ----+----   ----+----

"""
    
    fileName = "%s/report11.txt" % log.directory
    f = open(fileName, "w")
    f.write(header)
    
    test_list = manager.testlist
    test_list.sort(key=attrgetter("name"))
    
    for test in test_list:
      reportMe = test.options.get('report', True) or test.notes
    
      if test.status in [SKIPPED, FILTERED]:
        continue
    
      if (not reportMe) and test.status in [PASSED]:
        continue
    
      base_version = self.getTestVersion(test)
  
      f.write("%-45s  %-8s  %-10s  %-10s\n" % (test.name, test.status,
                                               self.executable_version, base_version))
  
    f.close()
  
#####################################################################

def createEnvironmentReport( manager, file_name="Environment.txt" ):
  header = """
Values of environment variables at end of testing.
---------------------------------------------------------------------
"""
  footer = """
---------------------------------------------------------------------
"""
  fileName = os.path.join( log.directory, file_name)
  f = open(fileName, "w")
  
  f.write(header)
  
  keys = os.environ.keys()
  keys.sort()
  for key in keys:
    f.write("%s = %s\n"%(key, os.environ[key]))
    
  f.write(footer)
  f.close()

#####################################################################
