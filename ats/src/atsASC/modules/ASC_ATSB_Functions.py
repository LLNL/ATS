import sys
import os
import time
import re

try:
  
  from ats import *
  
except ImportError:
    print 'Executing ats script', sys.argv[0], 'with', sys.executable
    print >>sys.stderr, "ats module cannot be imported; check Python path."
    print >>sys.stderr, sys.path
    raise SystemExit, 1

##########################################################################
# Functions copied from ats.times
##########################################################################

def datestamp (long=0):
    "Return formatted date and time. Shorter version is just time."
    if long:
        return time.strftime('%B %d, %Y %H:%M:%S')
    else:
        return time.strftime('%H:%M:%S')

##########################################################################
# Functions copied from ats.management.AtsManager.
#
# Changed self to manager.
#
##########################################################################

def report (manager):
  "Log a report, showing each test."
  for test in manager.testlist:
    reportMe = test.options.get('report', True) or test.notes 
    if (not reportMe) and test.status in [SKIPPED, PASSED, FILTERED]:
      continue
    log(test.serialNumber, test.status, test.name, test.message)
    #log.indent()
    #if test.notes:
    #  for line in test.notes:
    #    log("NOTE:", line)
    #if test.output and not configuration.options.hideOutput:
    #  log("NOTE:", "Captured output, see log.", echo=True,
    #     logging = False)
    #log.dedent()

##########################################################################

def summary (manager, alog, short=False):
  "Log summary of the results."
  tlist = [t for t in manager.testlist if t.options.get('report', True)]
  failed = [test.name for test in manager.testlist if (test.status is FAILED)]
  timedout = [test.name for test in manager.testlist if (test.status is TIMEDOUT)]
  ncs = [test for test in manager.testlist \
       if (test.status is PASSED and test.options.get('check', False))]
  passed = [test.name for test in tlist \
            if (test.status is PASSED and test not in ncs)]
  running = [test.name for test in manager.testlist if (test.status is RUNNING)]
  halted = [test.name for test in manager.testlist if (test.status is HALTED)]
  lsferror = [test.name for test in manager.testlist if (test.status is LSFERROR)]
  if running:
    alog("""\
RUNNING: %d %s""" % (len(running), ', '.join(running)))

  if ncs: 
    alog("""\
CHECK:    %d %s""" % (len(ncs), ', '.join([test.name for test in ncs])))

  alog("FAILED:   %d %s" % (len(failed), ', '.join(failed)))
  if timedout:
    alog("TIMEOUT:  %d %s" % (len(timedout), ', '.join(timedout)))
  if halted:
    alog("HALTED:   %d" % len(halted))
  if lsferror:
    alog("LSFERROR: %d" % len(halted))
  alog("PASSED:   %d" % len(passed))

  notrun = [test.name for test in manager.testlist if (test.status is CREATED)]
  lnr = len(notrun)
  if notrun:
    alog("""NOTRUN:   %d""" % len(notrun))

  if short: 
    return
  invalid = [test.name for test in manager.testlist if (test.status is INVALID)]
  batched = [test.name for test in tlist if (test.status is BATCHED)]
  skipped = [test.name for test in tlist if (test.status is SKIPPED)]
  filtered = [test.name for test in tlist if (test.status is FILTERED)]
  bad = manager.badlist

  if invalid:
    alog("INVALID:  %d %s" % (len(invalid) + len(bad), ', '.join(bad + invalid)))
  if batched:
    alog("BATCHED:  %d" % len(batched)) 
  if filtered:
    alog("FILTERED: %d" % len(filtered))
  if skipped:
    alog("SKIPPED:  %d" % len(skipped))

##########################################################################

def finalReport(manager):
  "Write the final report."
  log.reset()
  log.logging = 1
  log.echo = True
  if manager.testlist:
    log("""
=========================================================
ATS RESULTS %s""" % datestamp(long=1))
  log('-------------------------------------------------')
  report(manager)
  log('-------------------------------------------------') 
  log("""
ATS SUMMARY %s
""" % datestamp(long=1))
  summary(manager, log, short=False)
            
##########################################################################
# Functions and classes to rebuild manager-like object
##########################################################################

class ASC_AtsTest( AtsTest ):

  def __init__(self, test_dict):
    self.commandLine    = test_dict.commandLine 
    self.commandList    = test_dict.commandList 
    self.directory      = test_dict.directory 
    self.elapsedTime    = test_dict.elapsedTime 
    self.endDateTime    = test_dict.endDateTime 
    self.executable     = test_dict.executable 
    self.expectedResult = test_dict.expectedResult 
    self.message        = test_dict.message 
    self.name           = test_dict.name 
    self.notes          = test_dict.notes 
    self.options        = test_dict.options
    self.priority       = test_dict.priority
    self.runOrder       = test_dict.runOrder 
    self.serialNumber   = test_dict.serialNumber
    self.startDateTime  = test_dict.startDateTime 
    self.status         = test_dict.status 
    self.timelimit      = test_dict.timelimit 
    self.waitUntil      = test_dict.waitUntil 

    self.depends_on_txt = test_dict.depends_on
    self.dependent_ids  = test_dict.dependents
    
    if self.options.np:
      self.np = self.options.np
    else:
      self.np = 1

    # Set startTime and endTime from startDateTime and endDateTime respectively
    self.startTime = time.mktime(time.strptime( test_dict.startDateTime, '%Y-%m-%d %H:%M:%S'))
    self.endTime   = time.mktime(time.strptime( test_dict.endDateTime,   '%Y-%m-%d %H:%M:%S'))


  def fix_names( self, dir):
    self.namebase = re.sub('\W', '_', self.name)
    fileName      = ("%04d" % self.serialNumber) + "." + self.namebase +'.log'

    self.shortoutname = fileName
    self.outname      = os.path.join(dir, fileName)
    self.errname      = self.outname+'.err'


  def fix_depends_on( self, test_list ):
    if self.depends_on_txt != 'None':
      parent_serialNumber = int((self.depends_on_txt.split()[1])[1:])
      self.depends_on = test_list[parent_serialNumber-1]
    else:
      self.depends_on = None
  

  def fix_dependents( self, test_list, verbose=False ):
    self.dependents = []
    for serial_num in self.dependent_ids:
      self.dependents.append( test_list[serial_num -1] )
    if verbose:
      log( 'DEBUG: dependents = %s' % self.dependents, echo=True)
      
##########################################################################
# Functions to update tests for new (version 5.4) atsb
##########################################################################

def fixTest( test ):
  if test.options.np:
    test.np = test.options.np
  else:
    test.np = 1

  # Set startTime and endTime from startDateTime and endDateTime respectively
  test.startTime = time.mktime(time.strptime( test.startDateTime, '%Y-%m-%d %H:%M:%S'))
  test.endTime   = time.mktime(time.strptime( test.endDateTime,   '%Y-%m-%d %H:%M:%S'))
  

def fixTestNames( test, dir):
  test.namebase = re.sub('\W', '_', test.name)
  fileName      = ("%04d" % test.serialNumber) + "." + test.namebase +'.log'

  test.shortoutname = fileName
  test.outname      = os.path.join(dir, fileName)
  test.errname      = test.outname + '.err'
      
##########################################################################

def loadManagerFromStateFile( state_file, log=None ):

  try:
      my_globals = globals()
      execfile( state_file, my_globals )
      manager = my_globals['state']

  except Exception, error:
      print 'ERROR reading ATSB manager state file'
      print '  %s' % error
      raise SystemExit, 1
      
  if hasattr(manager, 'groups'):
    
    for test in manager.testlist:
      fixTest( test )
      fixTestNames( test, os.path.dirname( state_file ) )
    
  else:
    test_list = []
    for test_dict in manager.testlist:
      test = ASC_AtsTest( test_dict )
      test_list.append( test )
      test.fix_depends_on( test_list )
      test.fix_names( os.path.dirname( state_file ) )
    
    for test in test_list:
      test.fix_dependents( test_list )

    manager.read_testlist = manager.testlist
    manager.testlist      = test_list

  if log:
    log('\nRead manager state from %s:\n' % state_file, echo=True)
    log('Manager state saved at %s\n'   % manager.savedTime, echo=True)
  
  return manager
    
    
