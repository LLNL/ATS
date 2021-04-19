import os, sys
from datetime import date
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
#import configuration
from ats import CREATED,PASSED,FAILED,TIMEDOUT,SKIPPED,BATCHED,RUNNING,\
  FILTERED,INVALID
from ats import log, AtsError, SYS_TYPE
import shelve

class emailResults(object):
	"""emailResults Class, generates and emails a test report after an atsb test run.

Usage:
	There are currently two options for sending reports of the test execution.
	The report type is determined by the value of EMAIL_TYPE.
 	
	EMAIL_TYPE = 1:  Send an email after every atsb run containing the results 
	of the tests.  This is the default behavior.  
	
	EMAIL_TYPE = 0:    Send an email only after the continue file has been executed 
	(if there are no failures an email will be sent at the end of the current run).
	In this case a shelf file will be generated containing all of the test objects 
	from the initial execution.  This shelf file will be used to generate a 
	table in the report that contains both the initial test results and the 
	results of the continue file test run.

	To generate an email report from an ats test run, add the following to 
	the ats file. (mail.llnl.gov is the OCF email server).

		from ats import emailReport
		email = emailReport.emailResults()
		email.host="mail.llnl.gov"
		email.fromEmail="you@youraddress"
		email.toEmail="yourTeam@work"
		email.EMAIL_TYPE=0 
		email.subject="Description of the test"
		manager.onExit(email.sendReport)

Attributes:
	host  -- identifies the mail server host
	fromEmail  -- email address of the sender
	toEmail  -- identifies the recipients of the email
	subject -- the subject of the email message
	EMAIL_TYPE -- 0 or 1 determines the contents and timing of the email (see usage)  

Methods:
	sendReport (manager) -- creates the message body and emails the report
	init () -- initializes the default values for the email
	createStatusLists(testlist) -- separates the atsb testlist into individual test lists
		according to each tests status
	createSummary -- creates a table that sumarizes all test results
	createTable (status)-- creates a table of tests of a given status along
		with their scripts. by default the tests that FAILED will be 
		included in this table
	createMultiRunTable -- if EMAIL_TYPE is 0 this will create a table containing the failed
		tests and a column of PASS/FAIL status for the initial execution and 
		the results of the execution of the continue file.
	createShelf -- if EMAIL_TYPE is 0, this will create a shelve file containing
		the test object attributes from the first run instead of sending an email
	parseShelf -- if EMAIL_TYPE is 0, this will parse the original run's shelve file 
		to determine which tests will be included in the report
	"""

	def __init__(self, domainName="", host=" ", subject=" ", type=1, label=" ",
		     addressDict=None, code_version="Unknown", report_url=''):
		" initializes the default values for the email"	
		self.domainName   = domainName
		self.host         = host
		self.subject      = subject
		self.EMAIL_TYPE   = type
		self.runlabel     = label
		self.code_version = code_version
		self.report_url   = report_url
		self.addressDict  = addressDict
		self.toEmail      = []
                self.msg          = MIMEMultipart()

		self.setFromAddress()
		#log('emailResults.__init__:\n%s' % self, echo=True)

	def __repr__(self):
	  val  = 'domainName = %s\n' % self.domainName
	  val += 'host       = %s\n' % self.host
	  val += 'subject    = %s\n' % self.subject
	  val += 'EMAIL_TYPE = %d\n' % self.EMAIL_TYPE
	  val += 'runlabel   = %s\n' % self.runlabel
	  val += 'fromEmail  = %s\n' % self.fromEmail
	  val += 'toEmail    = %s\n' % self.toEmail
	  
	  return val


        def setFromAddress(self):
	  logname = os.environ['LOGNAME']
	  self.fromEmail = logname
	  
	  if self.addressDict is not None:
	    self.fromEmail = self.addressDict.get(logname, logname)
	    
	  elif self.domainName:
	    self.fromEmail = "%s@%s" % ( logname, self.domainName )


        def setToAddresses(self, to_list=[]):
          if self.addressDict is not None:
	    if to_list:
	      for name in to_list:
	        self.toEmail.append(self.addressDict.get(name, name))
	    else:
	      self.toEmail = self.addressDict.values()
	  else:
	    self.toEmail = to_list

	def addHTMLPart( self, html_txt ):
  	    html_msg = MIMEText(html_txt, 'html')
	    self.msg.attach(html_msg)

	def sendReport(self, manager):
		" creates the message body and emails the report"
		try:
		  subject = manager.get('email_subject')
		  self.subject = subject 
		except AtsError:
		  # It's not an error if email_subject has not been set
		  pass

		try:
		  to_list = manager.get('email_to_list')
		  self.setToAddresses( to_list )
		except AtsError:
		  # It's not an error if To: list has not been set
		  pass

		testDate = str(date.today())
		subjectDate = self.subject + " " + testDate	

		self.testlist = manager.testlist
		self.createStatusLists(self.testlist)

		self.addHTMLPart( self.createSummary() )
		
		self.msg['Subject'] = subjectDate
		self.msg['From']    = self.fromEmail
		self.msg['To']      = ', '.join(self.toEmail)
		
		s = smtplib.SMTP(self.host)

		# If there is a continuation file and a report file
		# Create the rest of the table and send the email
		if len(self.failed) > 0 and self.EMAIL_TYPE == 0: 
			lastarg = len(sys.argv)
			# Assume the continue file will always be the last arguement
			# See if this is the continue file execution
			contpath, contfn =  os.path.split(sys.argv[lastarg-1]) 
			if contfn=='continue.ats': 
			# Need to get the unique directory of the previous execution
				reportfn = 'report.' + contfn
				fn = os.path.join(contpath,reportfn)
			else:
				contpath,contfn = os.path.split(manager.continuationFileName) 
				reportfn = 'report.' + contfn
				fn = os.path.join(contpath,reportfn)
			
			if os.path.isfile(fn):
				print "Shelf file already exists.  Send Report."
				self.addHTMLPart( self.createMultiRunTable(fn) )
				s.sendmail(self.fromEmail, self.toEmail, self.msg.as_string())
			else: 
				#self.createReportFile(fn)
				print "Create the Shelf File. The report will be sent after the continue file is run."
				self.createShelf(fn)

		elif len(self.failed) > 0:
		# create the failed test table
			self.addHTMLPart( self.createTable('FAIL') )
			s.sendmail(self.fromEmail, self.toEmail, self.msg.as_string())
		else:
		# just send the summary
			s.sendmail(self.fromEmail, self.toEmail, self.msg.as_string())

		s.quit()

	def createStatusLists(self, testlist):
		"""separates the atsb testlist into individual test lists
                according to each tests status"""

		self.passed   = [test for test in testlist if (test.status is PASSED)]
		self.failed   = [test for test in testlist if (test.status is FAILED)]
		self.created  = [test for test in testlist if (test.status is CREATED)]
		self.timeout  = [test for test in testlist if (test.status is TIMEDOUT)]
		#self.notrun   = [test for test in testlist if (test.status is NOTRUN)]
		self.invalid  = [test for test in testlist if (test.status is INVALID)]
		self.batched  = [test for test in testlist if (test.status is BATCHED)]
		self.filtered = [test for test in testlist if (test.status is FILTERED)]
		self.skipped  = [test for test in testlist if (test.status is SKIPPED)]


	def createSummary(self):
		"""Creates the header of the html email containing system type,
		the subject, date, and result summary table"""

		systype = SYS_TYPE
		platform = '<html><p><h><b>Platform Tested:</b> %s</h><p> ' % systype
		version   = '<p><h><b>Code Version:</b> %s</h><p> ' % self.code_version
		title =  '<p><h><b><font size="4"> %s </font></b></h></p>' % self.subject
		if self.report_url:
		  url = '<p><b>See full report at <a href="%s"> %s </a>.</b></p>' % (self.report_url, self.report_url)
		else:
		  url = ''

		#create a dictionary of status types and results to make formatting easier
		testSums = {'total': str(len(self.testlist)), 'passed':str(len(self.passed)),
                    'failed':str(len(self.failed)) , 'timeout': str(len(self.timeout)),
                    'invalid':str(len(self.invalid)), 'filtered': str(len(self.filtered)),
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
        				<tr><td width="75"> Timedout </td>
					<td align="right" width="60"> %(timeout)s </td></tr>
        				<tr><td width="75"> Invalid </td>
					<td align="right" width="60"> %(invalid)s </td></tr>
        				<tr><td width="75"> Filtered </td>
					<td align="right" width="60"> %(filtered)s </td></tr>
        				<tr><td width="75"> Skipped </td>
					<td align="right" width="60"> %(skipped)s </td></tr>
        				<tr><td width="75"> Total </td>
					<td align="right" width="60"> %(total)s </td></tr>
        				</table></p><br> '''
		summary = title + version + platform + url
		summary += sumTemplate % testSums

		return summary


	def createTable(self, status): 
		"""creates a table of tests of a given status along
                with their scripts. by default the tests that FAILED will be
                included in this table"""
		tableBody= ' '
		#s = status
		tableTitle = '<b>Tests that %s on at least one platform <br>' % status
		tableHeader = '<table border><tr><th> Test Label </th><th> Test Script </th></tr>'
		tableBody += tableTitle
		tableBody += tableHeader
		for t in self.failed:
			details = {'testName': t.name, 'testScript': t.options['script']}
			print t
			testDetails = '<tr><td> %(testName)s </td><td> %(testScript)s </td></tr>' % details
			tableBody += testDetails
		tableBody += '</table></html>'
		return tableBody


	def createMultiRunTable(self, reportFile):
		tableBody= ' '
		tableTitle = '<b>Tests that FAILED on at least one platform <br>'
		tableHeader = '<table border><tr><th> Test Label </th><th> %s \
				</th><th> Continue File </th> <th> Test Script </th></tr>' \
				 % SYS_TYPE
		tableBody += tableTitle
		tableBody += tableHeader
		self.parseShelf(reportFile)
		for t in self.failed:
			if t.name in self.firstRunResults['FAIL']:
				details = {'testName': t.name, 'testScript': t.options['script'],\
					 'firstrun':'FAILED', 'continueFile':'FAILED'}
				testDetails = '<tr><td> %(testName)s </td><td> %(firstrun)s \
					</td><td> %(continueFile)s </td><td> %(testScript)s \
					</td></tr>' % details
				tableBody += testDetails

		for t in self.passed:
			if t.name in self.firstRunResults['FAIL']:
				details = {'testName': t.name, 'testScript': t.options['script'],\
					'firstrun':'FAILED', 'continueFile':'PASSED'}
				testDetails = '<tr><td> %(testName)s </td><td> %(firstrun)s \
					</td><td> %(continueFile)s </td> <td> %(testScript)s \
					</td></tr>' % details
				tableBody += testDetails
		tableBody += '</table></html>'
		return tableBody


	def createShelf(self, fname):
		shelf = shelve.open(fname)
		tid = 0
		for t in self.testlist:
			shelf[t.name] = {'status':t.status, 'runStartTime':t.runStartTime, \
					'testScript': t.options['script'], 'options':t.options}
		shelf.close()

 
	def parseShelf(self, fname):
		self.firstRunResults = {'PASS':[], 'FAIL':[], 'TIME':[], 'INVALID':[],'FILT':[],'SKIP':[]}
		db = shelve.open(fname, 'r')
		#db = shelve.open('testShelf.dat', 'r')
		self.totalFirstRun = len(db)
		# Append every test in the shelf file to the corresponding list
		for key in db.keys():
			status = db[key]['status']
			self.firstRunResults[str(status)].append(key)
			#opts = db[key]['options']
			#print 'options in the shelf are ',opts
		db.close()
