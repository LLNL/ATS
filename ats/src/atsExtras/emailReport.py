import os, sys
from datetime import date
#from times import datestamp
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEImage import MIMEImage
from email.utils import COMMASPACE
import ats.configuration
from ats.atsut import PASSED,FAILED,TIMEDOUT,SKIPPED,BATCHED,RUNNING,\
        FILTERED,INVALID
from ats import log

class emailResults(object):
        '''     Usage:

                Provide a list of atsb result files (atsr.py) to include in the report, a list of 
                email addresses to send the report to, and call sendReport via the manager.onExit function.
                Text and images can be added to ANY email type using the precedeReport(str), 
                appendReport(str), and addMsgImages(img) directly from the calling file.

                from ats import emailReport
                address = {'users name':'yourname@llnl.gov','yourGroupList':'group@lists.llnl.gov'}
                dbList = ['compare_these_results_atsr.py','other_platform_results_atsr.py']
                email = emailReport.emailResults(
                                domainName="llnl.gov",
                                subject="Only using atsr.py Files for this report", 
                                addressDict=address, host='nospam.llnl.gov', 
                                dbList=dbList,
                                type=1,
                                code_version=vx.y
                                )
                manager.onExit(email.sendReport)

                msg = "<p> Add a banner before the report - use html tags"
                email.msgPrecedeReport.append(msg)

                msg = "<br> Add a footer or other text after the table results"
                email.msgAppendReport.append(endmsg)


        EMAIL_TYPE 0:  Send a report of the current test run only (use type=0). 

        EMAIL_TYPE 1: This method will ignore the current run and just generate a table using the
                ats result files provided in dbList. This is useful if you want a table of results
                from previously executed tests without having to rerun them.  

        EMAIL_TYPE 2:  This is used in exactly the same as EMAIL_TYPE 1 but will include the 
                results from the current run in addition to the results from the listed
                ats result files.

        '''



        def __init__(self, domainName="", host="", subject="", type=1, label=" ",
                        addressDict=None, code_version="Unknown", dbList=None):
                ''' initializes the default values for the email'''
                self.domainName = domainName
                self.host       = host
                self.subject    = subject
                self.EMAIL_TYPE = type
                self.runlabel   = label
                self.code_version = code_version
                self.addressDict  = addressDict
                self.dbList     = dbList
                self.dbTestLists = {}
                self.toEmail    = []
                self.msgPrecedeReport = []
                self.msgAppendReport = []
                self.msgImages = []
                self.tableHeaders = None # Can be assigned a list of strings to be used as headers

                if addressDict is not None:
                        logname = os.environ['LOGNAME']
                        if logname in addressDict.keys():
                                self.fromEmail = addressDict[logname]
                        elif domainName:
                                self.fromEmail = "%s@%s" % (logname, domainName)
                        else:
                                self.fromEmail = logname
                #       self.toEmail = ', '.join(addressDict.values())
                        for key in addressDict.keys():
                                #I'm making this change to use the email.utils COMMASPACE utility
                                #Which appears to be required to send to multiple addresses
                                self.toEmail.append(addressDict[key])
                else:
                        self.fromEmail = " "
                        self.toEmail = " "

                if dbList is not None:
                        self.dbList = dbList

        def __repr__(self):
                val = 'domainName = %s\n' % self.domainName
                val += 'host    = %s\n' % self.host
                val += 'subject = %s\n' % self.subject
                val += 'EMAIL_TYPE  = %d\n' % self.EMAIL_TYPE
                val += 'runlabel  = %s\n' % self.runlabel
                val += 'fromEmail  = %s\n' % self.fromEmail
                val += 'toEmail  = %s\n' % self.toEmail
        #       val += 'dbList  = %s\n' % ','.join(self.dbList)
                return val

        def sendReport(self, manager):
                 '''Creates the message body from multiple manager.db files and emails the report'''
                 # If the user never defined the runlabel, set it to the SYS_TYPE
                 # or it will remain blank in the summary table
                 if self.runlabel: pass
                 else:
                        self.runlabel = ats.configuration.SYS_TYPE
                 if not self.dbList:
                         self.dbList = None

                 if self.EMAIL_TYPE == 0: # Create a report from the current run only
                         pass
                 else:                    # Include atsb results from other runs in this report
                         if self.dbList is None:
                                print "There are no files in the list. Use type=0 or provide a dbList when calling sendReport"
                         else:
                                self.readResultFiles(manager.testlist)
                 # General test info
                 testDate = str(date.today())
                 subjectDate = self.subject + " " + testDate

                 emailBody = ' '
                 # Create the message
                 #msg = MIMEMultipart('alternative')
                 msg = MIMEMultipart(_subtype='related')
                 msg['Subject'] = subjectDate
                 msg['From'] = self.fromEmail
                 #msg['To'] = self.toEmail
                 msg['To'] = COMMASPACE.join(self.toEmail)
                 s = smtplib.SMTP(self.host)

                 # If the user has defined any messages that should be included BEFORE
                 # the report text such as banners, they need to be added here before the report
                 # text is added.
                 if self.msgPrecedeReport:
                         for usrmsg in self.msgPrecedeReport:
                                 emailBody += usrmsg


                 # Email type=0 simply sends a report for every run.  No comparisons to any other results.
                 # If type=1 or type=2 but a list of files to compare to aren't provided, the type=0 report
                 # will be sent.
 
                 if self.EMAIL_TYPE == 0 or self.dbList is None:
                                 emailBody += self.createSummary(manager)
                                 if len(self.failed) > 0:
                                        emailBody += self.createTable('FAIL')
                 else:
                                 emailBody += self.createSummary2(manager)
                                 emailBody += self.buildMasterTable()

                 # If the user has defined any messages that should be included AFTER
                 # the report text such as banners, they need to be added here before the report
                 # text is added.
                 if self.msgAppendReport:
                         for usrmsg in self.msgAppendReport:
                                 emailBody += usrmsg

                                 

                 htmlBody = MIMEText(emailBody, 'html')
                 msg.attach(htmlBody)

                 # If the user has defined any images that should be included in the message
                 # they are added here.
                 if self.msgImages:
                         print "msgImages is not empty.  It contains ", self.msgImages
                         for usrImage in self.msgImages:
                                 # The following is supposed to open the image in binary mode
                                 # and lets MIMEImage guess the image type
                                 #fp = open(usrImage,'rb')
                                 fp = open(usrImage, 'rb')
                                 # add the html to the message so the image is inlined
                                 # is not working so I'll have to figure this out later
                                 #html = MIMEText('<p> Attachments <img src="cid:tulip" /></p>', _subtype='html')
                                 #msg.attach(html)
                                 img = MIMEImage(fp.read(), _subtype="jpg")
                                 #img.add_header('Content-Id', '<usrImage>')
                                 fp.close()
                                 msg.attach(img)

                 s.sendmail(self.fromEmail, self.toEmail, msg.as_string())
                 s.quit()


        def createStatusLists(self, testlist):
                """Separates the atsb testlist into individual test lists
                according to each tests status"""
                self.passed = [test for test in testlist if (test.status is PASSED)]
                self.failed = [test for test in testlist if (test.status is FAILED)]
                self.timeout = [test for test in testlist if (test.status is TIMEDOUT)]
                self.invalid = [test for test in testlist if (test.status is INVALID)]
                self.batched = [test for test in testlist if (test.status is BATCHED)]
                self.filtered = [test for test in testlist if (test.status is FILTERED)]
                self.skipped = [test for test in testlist if (test.status is SKIPPED)]

        def createSummary2(self, manager):
                '''Uses the dbList to generate a summary of the current run and all db files'''
                systype = ats.configuration.SYS_TYPE
                #platforms = '<html><p><h><b>Platforms Tested:</b> %s</h><p> ' % systype
                version = '<p><h><b> Code Version: </b> %s </h><p> ' % self.code_version
                title =  '<p><h><b><font size="4"> %s </font></b></h></p>' % self.subject
                summary = title + version # + platforms
                #First write the header row
                summary += '''<table border="1"><caption><b>Report Summary</b></caption>
                                <tr><td>Platforms Tested</td><td>Passed</td><td>Failed</td> 
                                <td>Timedout</td><td>Invalid</td><td>Filtered</td>
                                <td>Skipped</td><td>Total</td></tr>'''
                #for key in self.dbTestLists:
                for key in sorted(self.dbTestLists.iterkeys()):
                        #first create the status lists for the summary
                        self.createStatusLists(self.dbTestLists[key])
                        # Create a dictionary of status types and results to make formatting easier.
                        # First strip the filename out of the key so the tables don't contain
                        # the full path. 
                        path,filename = os.path.split(key)
                        
                        testSums = {'filename':filename, 'total': str(len(self.dbTestLists[key])), 'passed':str(len(self.passed)),
                                    'failed':str(len(self.failed)) , 'timeout': str(len(self.timeout)),
                                        'invalid':str(len(self.invalid)), 'filtered': str(len(self.filtered)),
                                        'skipped': str(len(self.skipped))}
                        sumTemplate =  ''' <tr><td> %(filename)s</td>
                                        <td align="right" width="60"> %(passed)s </td>
                                        <td align="right" width="60"> %(failed)s </td>
                                        <td align="right" width="60"> %(timeout)s </td>
                                        <td align="right" width="60"> %(invalid)s </td>
                                        <td align="right" width="60"> %(filtered)s </td>
                                        <td align="right" width="60"> %(skipped)s </td>
                                        <td align="right" width="60"> %(total)s </td></tr> '''
                        summary += sumTemplate % testSums
                summary+='''  </table></p><br> '''
                return summary


        def masterTestList(self, testlist):
                '''This function will create a master test list from the lists found in the database files'''
                self.mTestList ={}
                #for each db file
                if self.EMAIL_TYPE == 2: 
                        #include the current test results in the table
                        self.dbTestLists[self.runlabel] = testlist
                        self.dbList.append(self.runlabel)
                row = 0
                for fn in sorted(self.dbTestLists.iterkeys()):
                        print 'looking at %s ' % fn
                        #see if the test is already in the master list
                        for test in self.dbTestLists[fn]:
                                if test.name in self.mTestList:
                                        self.mTestList[test.name].append(test.status)
                                else:
                                        self.mTestList[test.name] = []
                                        # put dashes in for tests not run
                                        if len(self.mTestList[test.name]) < row:
                                                counter = 0
                                                while counter < row:
                                                        self.mTestList[test.name].append('  -  ')
                                                        counter +=1

                                        #now append the status of the test
                                        self.mTestList[test.name].append(test.status)
                        row += 1
                # now we need to fill in a dash for any rows that are too short so the table
                # prints as expected.
                for key in self.mTestList:
                        if len(self.mTestList[key]) < len(self.dbTestLists):
                                filler = len(self.dbTestLists) - len(self.mTestList[key])
                                while filler > 0:
                                        self.mTestList[key].append('  -  ')
                                        filler -= 1


        def buildMasterTable(self):
                '''This function will build a report using the master test list '''
                tableBody= ' '
                failed = 0
                tableTitle = '<table border="1"><caption><b>Tests that failed or timed out  </b></caption>'
                tableHeader = '<tr><td> Test Label </td>'
                #Add the headers
                #for key in self.dbTestLists.keys():
                for key in sorted(self.dbTestLists.iterkeys()):
                         # split out the filename to avoid putting paths in the table
                         path,filename = os.path.split(key)
                         tableHeader += '<td> %s  </td>' % filename

                tableHeader += '</tr>'

                tableBody += tableTitle
                tableBody += tableHeader

                for t in self.mTestList:
                         statusString = " "
                         #convert the status object to a string
                         #so it's easier to count number of passes.
                         # if all status's in a row are PASS the row will be skipped from the report
                         for status in self.mTestList[t]:
                                 statusString += str(status)
                         tableRow = '<tr><td> %s' % t
                         tableRow += '</td>'
                         # for each row write out the cell
                         # if all status's in a row are PASS the row will be skipped from the report
                         # (this would indicate that the status was pass in all shelf files)
                         if statusString.count('PASS') == len(self.dbList):
                                 pass
                         elif statusString.count('FILT') == len(self.dbList):
                                 pass
                         elif 'FAIL' in statusString:
                                 print "Found a failure"
                                 tableRow = '<tr><td> %s' % t
                                 tableRow += '</td>'
                                 for i in self.mTestList[t]:
                                         tableRow += '<td> %s </td>' % i
                                 tableBody += tableRow
                                 tableBody += '</tr>'
                               #  appendRows += tableRow
                               #  appendRows += '</tr>'
                                 failed += 1
                         elif 'TIME' in statusString:
                                 print "Found a Timeout"
                                # appendRows = '<tr><td> %s' % t
                                # appendRows += '</td>'
                                 for i in self.mTestList[t]:
                                         tableRow += '<td> %s </td>' % i
                                 tableBody += tableRow
                                 tableBody += '</tr>'
                                # appendRows += tableRow
                                # appendRows += '</tr>'
                                 failed += 1
                         else:
                                 pass

                if failed > 0:
                        tableBody += '</table></html>'
                        return tableBody
                else:
                        return '<b> All tests passed </b> <br>'


        def createSummary(self, manager):
                """Creates the header of the html email containing system type,
                the subject, date, and result summary table"""
                self.testlist = manager.testlist
                self.createStatusLists(self.testlist)
                systype = ats.configuration.SYS_TYPE
                platforms = '<html><p><h><b>Platforms Tested:</b> %s</h><p> ' % systype
                version = '<p><h><b> Code Version: </b> %s </h><p> ' % self.code_version
                title =  '<p><h><b><font size="4"> %s </font></b></h></p>' % self.subject

                #create a dictionary of status types and results to make formatting easier
                testSums = {'total': str(len(self.testlist)), 'passed':str(len(self.passed)),
                    'failed':str(len(self.failed)) , 'timeout': str(len(self.timeout)),
                    'invalid':str(len(self.invalid)), 'filtered': str(len(self.filtered)),
                    'skipped': str(len(self.skipped))}
                #NEED TO ADD MORE TAGS TO FORMAT THIS AS A TABLE.  PUT TOTAL AT 
                #THE BOTTOM
                sumTemplate =  ''' <table border="1"><caption><b>Test Summary</b></caption>
                                        <tr><td width="75"> Passed </td>
                                        <td align="right" width="60"> %(passed)s </td></tr>
                                        <tr><td width="75"> Failed </td> 
                                        <td align="right" width="60"> %(failed)s </td></tr>
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
                summary = title + version + platforms
                summary += sumTemplate % testSums

                return summary


        def createTable(self, status):
                """creates a table of tests of a given status along
                with their scripts. by default the tests that FAILED will be
                included in this table"""
                tableBody= ' '
                #s = status
                tableTitle = '<table border="1"><caption><b>Tests that %s on at least one platform </b></caption>' % status
                tableHeader = '<tr><th> Test Label </th><th> Test Script </th></tr>'
                tableBody += tableTitle
                tableBody += tableHeader
                for t in self.failed:
                        details = {'testName': t.name, 'testScript': t.options['script']}
                        print t
                        testDetails = '<tr><td> %(testName)s </td><td> %(testScript)s </td></tr>' % details
                        tableBody += testDetails
                tableBody += '</table></html>'
                return tableBody

        def precedeReport(self, message):
                ''' This function will take a string and add it to the email report BEFORE
                the report content is added.  This would include things like banners or 
                environment / configuration notes not captured by the generic details of the report
                '''
                self.msgPrecedeReport.append(message)

        def appendReport(self, message):
                ''' This function will take a string and add it to the email report AFTER
                the report content is added.  Such as errors, user messages about the test execution,
                or additional details or tables produced by tools outside of the report module.
                '''  
                self.msgAppendReport.append(message)

        def addMsgImages(self, image):
                ''' This function will appends images to a list to be added to the body of the message
                 before sending. '''
                print "attaching %s to the list of images" % image
                self.msgImages.append(image)

        def readResultFiles(self, testlist):
                '''this function reads in a list of atsr.py files and adds their test lists to the report dict
                NOTE:  The dbList (change that) will be populated by the ats file calling the emailReport.
                Use that file to find all of the files you want to include here.
                '''

                if self.dbList is None:
                        print 'There are no result files provided'
                else:
                        for file in self.dbList:
                                print 'the file name is %s'% file 
                                if os.path.isfile(file):
                                # execfile and add it's state.testlist to our self.dbTestLists
                                # 
                                # I'm using the example from the ats pdf, page 24 that says
                                # to use execfile and rename the state, then appending it's testlist
                                # to our list using the filename as it's key
                                        d = {}
                                        execfile(file, d)
                                        state1 = d['state']
                                        self.dbTestLists[file] = state1.testlist
                                        for test in state1.testlist:
                                                print test.name
                                else:
                                        print "The file %s doesn't exist" % file
                self.masterTestList(testlist)

        def topPriorityResults(self, searchString):

                searchFor = searchString
                msg = None
                testlist = None
                failed = []
                if searchFor == None: return ''

                priorityFilename = None
                for file in self.dbList:
                # Use the continue file if it's available
                        if searchFor and 'continue' in file:
                                priorityFilename = file
                                break
                        elif searchFor in file:
                                priorityFilename = file
                                print 'Priority Filename is %s' % file
                        else:
                                pass

                if priorityFilename != None:
                        d = {}
                        execfile(priorityFilename,d)
                        state = d['state']
                        testlist = state.testlist
                        failed = [test for test in testlist if (test.status is FAILED)]
                        if len(failed) > 0:
                                msg = '<br><b>Chaos Failures </b><br>'
                                for test in failed:
                                        msg += test.name + '<br>'
                                        print 'appending %s' % test.name
                return msg

