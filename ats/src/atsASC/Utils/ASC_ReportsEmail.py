import commands
import sys
import os
import re
import time

sys.dont_write_bytecode = True

from ats         import log, AtsError

from ASC_utils   import runCommand, readFile, setUrlFromPath
import ASC_State

import emailReport2

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
from ats import SYS_TYPE, CREATED, PASSED, FAILED, TIMEDOUT, SKIPPED, HALTED, LSFERROR, \
     BATCHED, RUNNING, FILTERED, INVALID

######################################################################
#
######################################################################
class EmailReportNew(emailReport2.emailResults):
  def __init__( self, id='Unknown',
                domainName="", 
                host="", 
                subject=" ", 
                manager_emailTo="unset", 
                type=1, 
                label=" ",
                addressDict=None, 
                project_name="Project",
                code_version="Unknown",
                default_emailTo="unset",
                default_from="unset",
                dbList=None ):

    emailReport2.emailResults.__init__(self,
                                       domainName, host, subject, type,
                                       label, None,code_version,
                                       dbList )
    
    self.id = id

    self.addressDict = addressDict
    
    self.email_to_list = set()

    if not manager_emailTo == "unset":
        names = manager_emailTo.split()
        for name in names:
            self.email_to_list.add( name )
    else:
        if not default_emailTo == "unset":
            names = default_emailTo.split(',')
            for name in names:
                self.email_to_list.add( name )
        else:
            self.email_to_list.add( 'mmouse1' )

    if not default_from == "unset":
        self.fromEmail  = self.makeEmailAddress(default_from)
    else:
        self.fromEmail  = self.makeEmailAddress('mmouse1')



    self.toEmail = []
  
    self.msg        = MIMEMultipart()      
    self.msgHeader  = ''
    self.msgFooter  = ''
      
  ######################################################################
  def setHeader(self, header_txt):
    self.msgHeader = header_txt
      
  ######################################################################
  def setFooter(self, footer_txt):
    self.msgFooter = footer_txt

  ######################################################################
  def makeEmailAddress(self, name):

    if ( ( self.addressDict is not None ) and
         ( name in self.addressDict.keys() ) ):

      address = self.addressDict.get(name)

    elif self.domainName:
      address = "%s@%s" % ( name, self.domainName )

    else:
      address = name

    return address

  ######################################################################
  def setToAddresses(self, to_list=[]):
    if to_list:
      for name in to_list:
        self.toEmail.append(self.makeEmailAddress( name ))
    else:
      self.toEmail = self.addressDict.values()

  ######################################################################
  def addHTMLPart( self, html_txt ):
    html_msg = MIMEText(html_txt, 'html')
    self.msg.attach(html_msg)

  ######################################################################
  def precedeReportText(self, message, heading=''):
    ''' This function will take a string and add it to the email report
    as preformatted text BEFORE the report content is added.  This would
    include things like banners or environment / configuration notes not
    captured by the generic details of the report
    '''
    html_text = ''

    if heading:
      html_text += '<p><h><b>' + heading + '</b></h><p>'

    html_text += '<pre>' + message + '</pre>'
    
    self.precedeReport( html_text )

  ######################################################################
  def appendReportText(self, message, heading=''):
    ''' This function will take a string and add it to the email report
    as preformatted text AFTER the report content is added.  Such as errors,
    user messages about the test execution, or additional details or tables
    produced by tools outside of the report module.
    '''  
    html_text = ''

    if heading:
      html_text += '<p><h><b><font color = "red" size="3">' + heading + '</font></b></h><p>'

    html_text += '<pre>' + message + '</pre>'

    self.appendReport( html_text )

  ######################################################################
  def createStatusLists(self, testlist):
    """separates the atsb testlist into individual test lists
    according to each tests status"""

    self.passed   = [test for test in testlist if (test.status is PASSED)]
    self.failed   = [test for test in testlist if (test.status is FAILED)]
    self.halted   = [test for test in testlist if (test.status is HALTED)]
    self.lsferror = [test for test in testlist if (test.status is LSFERROR)]
    self.created  = [test for test in testlist if (test.status is CREATED)]
    self.timedout = [test for test in testlist if (test.status is TIMEDOUT)]
    #self.notrun   = [test for test in testlist if (test.status is NOTRUN)]
    self.invalid  = [test for test in testlist if (test.status is INVALID)]
    self.batched  = [test for test in testlist if (test.status is BATCHED)]
    self.filtered = [test for test in testlist if (test.status is FILTERED)]
    self.skipped  = [test for test in testlist if (test.status is SKIPPED)]

  ######################################################################
  def createFirstPart(self):
    first_part  = '<html>'
    if self.msgHeader:
      first_part += '<header><h2><b>%s</b></h2></header>' % self.msgHeader

    first_part +=  '<p><h><b><font size="4"> %s </font></b></h></p>' % self.subject
    first_part += '<p><h><b>Platform Tested:</b> %s</h><p> ' % self.id
    first_part += '<p><h><b>Code Version:</b> %s</h><p> ' % self.code_version

    for usrmsg in self.msgPrecedeReport:
      first_part += usrmsg

    return first_part

  ######################################################################
  def createLastPart(self):
    last_part = ''

    for usrmsg in self.msgAppendReport:
      last_part += usrmsg

    if self.msgFooter:
      last_part += '<footer><h2><b>%s</b></h2></footer>' % self.msgFooter

    last_part += '</html>'

    return last_part

  ######################################################################
  def createSummary(self):
    """Creates result summary table"""
    #create a dictionary of status types and results to make formatting easier
    testSums = {'total': str(len(self.testlist)), 'passed':str(len(self.passed)),
        'failed':str(len(self.failed)) , 'timedout': str(len(self.timedout)),
        'invalid':str(len(self.invalid)), 'filtered': str(len(self.filtered)),
        'halted':str(len(self.halted)), 'lsferror': str(len(self.lsferror)),
        'skipped': str(len(self.skipped)), 'created': str(len(self.created))}

    #NEED TO ADD MORE TAGS TO FORMAT THIS AS A TABLE.  PUT TOTAL AT 
    #THE BOTTOM
    sumTemplate =  ''' <b>Test Summary</b>
      <table border="1">
      <tr><td width="75"> Passed </td>
      <td align="right" width="60"> %(passed)s </td></tr>
      <tr><td width="75"> Failed </td> 
      <td align="right" width="60"> %(failed)s </td></tr>
      <tr><td width="75"> Created </td> 
      <td align="right" width="60"> %(created)s </td></tr>
      <tr><td width="75"> Timed out </td>
      <td align="right" width="60"> %(timedout)s </td></tr>
      <tr><td width="75"> Invalid </td>
      <td align="right" width="60"> %(invalid)s </td></tr>
      <tr><td width="75"> Filtered </td>
      <td align="right" width="60"> %(filtered)s </td></tr>
      <tr><td width="75"> Skipped </td>
      <td align="right" width="60"> %(skipped)s </td></tr>
      <tr><td width="75"> Halted </td>
      <td align="right" width="60"> %(halted)s </td></tr>
      <tr><td width="75"> LSF Error </td>
      <td align="right" width="60"> %(lsferror)s </td></tr>
      <tr><td width="75"> Total </td>
      <td align="right" width="60"> %(total)s </td></tr>
      </table></p><br> '''

    summary = sumTemplate % testSums

    return summary

  ######################################################################
  def createTable(self, status, test_list, col_name, col_var_name):
    """creates a table of tests of a given status along
    with extra information specified by col_name an col_var_name arguments."""
    tableBody= ' '
    tableTitle = '<table border="1"><caption><b>Tests that %s on at least one platform <br></caption>' % status
    tableHeader = '<tr><th> %s Test Label </th></tr>' % status
    tableBody += tableTitle
    tableBody += tableHeader
    for t in test_list:
      testDetails = '<tr><td> %s </td></tr>' % t.name
      tableBody  += testDetails
    tableBody += '</table></html>'
    return tableBody


  ######################################################################
  def createLastPassedTable(self, status, test_list):
    """creates a table of tests of a given status along
    with extra information from the ASC_State object.
    
    NOTE: status_file will not have been updated yet
          for the results of this run.
    """
    # SAD We do not have this state_file currently.
    # not sure of the format.  Talk with Burl if
    # we want to create and use it.
    tableBody= ' '
    #s = status
    if ASC_State.state_file:
      tableTitle = '<table border="1"><caption><b>Tests that %s on at least one platform <br></caption>' % status
      tableHeader = '<tr><th> Test Label </th><th>Last Passed Version</th><th>First Passed Version</th></tr>'
      tableBody += tableTitle
      tableBody += tableHeader
      for t in test_list:
        kernel = t.options.get('kernel')
        last_passed  = ASC_State.state_file.last_passed_dict[kernel]
        first_passed = ASC_State.state_file.first_passed_dict[kernel]
        details     = {'testName': t.name, 'last': last_passed, 'first':first_passed}
        testDetails = '<tr><td> %(testName)s </td><td> %(last)s </td><td> %(first)s </td></tr>' % details
        tableBody  += testDetails
      tableBody += '</table></html>'
      
    return tableBody

  ######################################################################
  def sendReport(self):
    " creates the message body and emails the report"
    testDate = str(date.today())
    subjectDate = self.subject + " " + testDate	

    self.msg['Subject'] = subjectDate
    self.msg['Date']    = time.ctime() + ' -0700'
    self.msg['From']    = self.fromEmail
    self.msg['To']      = ', '.join(self.toEmail)

    html_txt  = self.createFirstPart()
    html_txt += self.createSummary()
    html_txt += self.createLastPart()

    self.addHTMLPart( html_txt )

    # --------------------------------------------------------------------------------------------------
    # Alternative to ATS built in email, I used it when ats was broken
    # but believe that ATS is all better now.
    # --------------------------------------------------------------------------------------------------
    try:
      s = smtplib.SMTP('nospam.llnl.gov')
      s.sendmail(self.fromEmail, self.toEmail, self.msg.as_string())
      s.quit()
    except Exception, error:
      log('ERROR - problem sending email', echo=True)
      log('  %s' % error, echo=True)
      

######################################################################
#
######################################################################
class EmailReport( EmailReportNew ):
    
  def __init__( self, currentID, manager, 
                my_code_version,
                my_project_name,
                to_list,
                from_user ):


    if not manager.options.emailSubject == "":
        subject_msg = manager.options.emailSubject
    else:
        subject_msg = "%s ATSB Report" % my_project_name

    EmailReportNew.__init__(self, currentID,
                            domainName='llnl.gov',
                            host='nospam.llnl.gov',
                            subject=subject_msg,
                            manager_emailTo=manager.options.emailTo,
                            code_version=my_code_version,
                            project_name=my_project_name,
                            default_emailTo=to_list,
                            default_from=from_user)

    if manager.options.sendEmail:
      report_url = setUrlFromPath( manager.options.htmlDirectory )
      self.precedeReport('<p><b>See full report at <a href="%s"> %s </a>.</b></p>' % \
                         (report_url, report_url ) )

  ######################################################################


  def updateEmailToList( self, extra_set, manager ):
    """
    Update the set of user names to receive email about this test.
    """
    default_email_set = manager.get('default_email_set')

    # Use update rather than union so that we don't have to redefine
    # email_to_list in the ATSB Python enviroment.
    self.email_to_list.update( default_email_set.union( extra_set ) )

    if manager.options.verbose:
      log( 'Email to list:', echo=True)
      for name in self.email_to_list:
        log('  user: %-12s  email: %s' %( name, self.makeEmailAddress(name)),
            echo=True)
        
  ######################################################################

  def appendFileAsText( self, file, heading='' ):
    if os.path.exists( file ):
      lines = readFile( file )
      self.appendReportText(''.join(lines), heading )

  ######################################################################

  def createBasicEmail( self, manager ):
    options = manager.options

    self.testlist = manager.testlist
    self.createStatusLists(self.testlist)

    if options.sendEmail:

      #
      # Add tests which FAILED to the email
      #
      t_lines = []
      for test in manager.testlist:
        if test.status == FAILED:
            #for k,v in test.options.iteritems():
            #    print "\tOPT %s = %s" % (k, v)
            if test.options['checker_test'] == False:
                t_lines.append ( '%s %s \n' % (test.options['label'], test.options['clas']) )
            else:
                t_lines.append ( '%s \n' % (test.options['label'] ) )
      if t_lines:
        self.appendReportText(''.join(t_lines), 'Failed Tests' )

      #
      # Add tests which TIMEDOUT to the email
      #
      t_lines = []
      for test in manager.testlist:
        if test.status == TIMEDOUT:
            if test.options['checker_test'] == False:
                t_lines.append ( '%s %s \n' % (test.options['label'], test.options['clas']) )
            else:
                t_lines.append ( '%s \n' % (test.options['label'] ) )
      if t_lines:
        self.appendReportText(''.join(t_lines), 'Timed OutTests' )


      #
      # Add tests which PASSED to the email
      #
      t_lines = []
      for test in manager.testlist:
        if test.status == PASSED:
            if test.options['checker_test'] == False:
                t_lines.append ( '%s %s \n' % (test.options['label'], test.options['clas']) )
            else:
                t_lines.append ( '%s \n' % (test.options['label'] ) )
      if t_lines:
        self.appendReportText(''.join(t_lines), 'Passed Tests' )



        
  ######################################################################

  def sendEmail( self, manager ):
    #print "DEBUG sendEmail called"
    try:
      subject = manager.get('email_subject')
      self.subject = subject 
    except AtsError:
      # It's not an error if email_subject has not been set
      pass

    try:
      header = manager.get('email_header')
      if len(self.failed) > 0:
        self.msgHeader = '<font color="red">'   + header + '</font>'
      else:
        self.msgHeader = '<font color="green">' + header + '</font>'
        
    except AtsError:
      # It's not an error if email_header has not been set
      pass

    try:
      footer = manager.get('email_footer')
      self.msgFooter = footer
    except AtsError:
      # It's not an error if email_footer has not been set
      pass

    self.setToAddresses( self.email_to_list )
    self.sendReport()
    
######################################################################
#
######################################################################


