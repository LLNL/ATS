# ASC_HTML.py

import os
import sys
import stat
import time
import datetime
import platform
import shutil
import re
from urlparse import urljoin

from ats import log, SYS_TYPE

from ASC_utils import copyFile, copyAndRenameFile, findKeyVal, getGroupID, \
     listdirs, listDatedDirs, listfiles, readFile, \
     setDirectoryPermissions, setFilePermissions

# #################################################################################################
#
# Module Static Variables used across routines in this file.
#
# #################################################################################################

asc_html_yyyymm_str                      = "Unset"
asc_html_date_pretty_str                 = "Unset"
asc_html_yyyymm_dd_str                   = "Unset"
asc_html_yyyymm_dd_hhmmss_str            = "Unset"
asc_html_yyyymm_path                     = "Unset"
asc_html_yyyymm_dd_html_file             = "Unset"
asc_html_yyyymm_dd_hhmmss_base           = "Unset"
asc_html_yyyymm_dd_hhmmss_base_relative  = "Unset"
asc_html_sys_type                        = "Unset"
asc_html_lock_file                       = "Unset"
asc_html_node                            = "Unset"
asc_html_time_string                     = "Unset"
asc_html_date_string                     = "Unset"

asc_html_months_list = ["Zero", "January", "February", "March", "April", "May", "June", "July", \
                       "August", "September", "October", "November", "December"]

asc_html_link_lines = []

asc_html_info_text = "ASC_HTML Info:"


# #################################################################################################
#
#  This is far, far from sufficient.  It will break when more than 1
#  person or process is updating the html files.  See the tapestry perl version
#  of this routine for what this routine needs to look like
#
# #################################################################################################

def lockFile(asc_html_lock_file_base):
    
    me = "ASC_HTML.lockFile"

    #
    # Loop while lock file exists on disk
    #
    while (os.path.isfile(asc_html_lock_file_base)):
        ftime = os.path.getmtime(asc_html_lock_file_base)
        curtime = time.time()
        difftime = curtime - ftime
        if difftime > 600:                      # Delete locks that are more than 10 minutes old
            os.unlink(asc_html_lock_file_base)
            print "%s Deleted Lock File %s which was %d seconds old " % (me, asc_html_lock_file_base, difftime )
            continue
    
        print "%s Lock File %s exists, waiting for its removal " % (me, asc_html_lock_file_base )
        time.sleep(2)
        continue

    
    fp = open(asc_html_lock_file_base, 'w')
    fp.close()

    return

# #################################################################################################
#
#  Remove the lock file
#
# #################################################################################################

def unlockFile(asc_html_lock_file_base):

    me = "ASC_HTML.unlockFile"

    os.unlink( asc_html_lock_file_base )


# #################################################################################################
#
# Create global date and time string and other variables used across functions in this file.
# 
# #################################################################################################

def createDateAndTimeStrings( dir, sys_type='' ):

    me = "ASC_HTML.createDateAndTimeStrings"

    #-----------------------------------------------------------------------------------------------
    # This routine will set the following global vars, so tell python that these are globals
    # not local scope
    #-----------------------------------------------------------------------------------------------
    global asc_html_yyyymm_str    
    global asc_html_date_pretty_str
    global asc_html_yyyymm_dd_str     
    global asc_html_yyyymm_dd_hhmmss_str  
    global asc_html_yyyymm_path        
    global asc_html_yyyymm_dd_html_file   
    global asc_html_yyyymm_dd_hhmmss_base
    global asc_html_yyyymm_dd_hhmmss_base_relative
    global asc_html_sys_type       
    global asc_html_lock_file
    global asc_html_node
    global asc_html_date_string
    global asc_html_time_string

    #-----------------------------------------------------------------------------------------------
    # Create various strings which are paths to the html area
    #
    # Create a string such as YYYY_MM            such as 2010_09 
    # Create a string such as YYYY_MM_DD         such as 2010_09_28
    # Create a string such as YYYY_MM_DD_HHMMSS  such as 2010_09_28
    #
    # Also get other various bits of system information
    #-----------------------------------------------------------------------------------------------
    today = datetime.datetime.today()

    user_requested_time_shift = os.getenv("ATS_SHIFT_TIME_FORWARD_HOURS")
    if user_requested_time_shift is not None:
        new_today = today + datetime.timedelta(hours=int(user_requested_time_shift))
        today = new_today

    asc_html_date_pretty_str      = "%04d, %s %02d" % (today.year, asc_html_months_list[today.month],
                                                       today.day)

    asc_html_yyyymm_str           = "%04d_%02d" % (today.year, today.month)

    asc_html_yyyymm_dd_str        = "%04d_%02d_%02d" % (today.year, today.month, today.day)

    asc_html_yyyymm_dd_hhmmss_str = "%04d_%02d_%02d_%02d%02d%02d" % (today.year, today.month, 
                                    today.day, today.hour, today.minute, today.second)

    asc_html_yyyymm_path          = dir +  '/'  + asc_html_yyyymm_str

    asc_html_yyyymm_dd_html_file  = asc_html_yyyymm_path + '/' + asc_html_yyyymm_dd_str + '.html'

    asc_html_date_string          = "%04d/%02d/%02d" % (today.year, today.month, today.day)
    asc_html_time_string          = "%02d:%02d:%02d" % (today.hour, today.minute, today.second)

    if sys_type:
        asc_html_sys_type = sys_type
        
    else:
        asc_html_sys_type = os.getenv("SYS_TYPE")

        if asc_html_sys_type is None: 
            asc_html_sys_type = SYS_TYPE
            #print "%s WARNING Could not find environment variable SYS_TYPE, using " \
            #     "ats SYS_TYPE '%s' as a substitue" % (me, SYS_TYPE)
            # asc_html_sys_type = platform.system()

    asc_html_yyyymm_dd_hhmmss_base = asc_html_yyyymm_path + '/' + asc_html_yyyymm_dd_hhmmss_str +  \
                                    '_' + asc_html_sys_type

    asc_html_yyyymm_dd_hhmmss_base_relative = asc_html_yyyymm_dd_hhmmss_str +  '_' + asc_html_sys_type

    asc_html_lock_file = asc_html_yyyymm_path + '/' + "html_update_lock"

    temp_uname = os.uname()

    asc_html_node = temp_uname[1]

#
# Cleanup ALL files created by Check100 comparison
#
def cleanupAllCheck100Files(folder, kernel):
    files = listfiles(folder)
    for a_file in files:
        the_file = folder + '/' + a_file
        if re.match( kernel + '.*\.png$', a_file):
            os.remove(the_file)
        elif re.match( kernel + '.*\.curves$', a_file):
            os.remove(the_file)
        elif re.match( kernel + '.*\.curves\.', a_file):
            os.remove(the_file)
        elif re.match( kernel + '.*\.comparison.results$', a_file):
            os.remove(the_file)

#
# Cleanup Unneeded files created by Check100 comparison, leaving those such as
# png files which will be used for HTML pages and other reporting.
#
def cleanupCheck100Files(folder, kernel):
    files = listfiles(folder)
    for a_file in files:
        the_file = folder + '/' + a_file
        if re.match( kernel + '.*\.curves$', a_file):
            os.remove(the_file)
        elif re.match( kernel + '.*\.curves\.', a_file):
            os.remove(the_file)


def listDatedHtmlFiles(folder):
    return [d for d in os.listdir(folder) if re.search('2[0-9][0-9][0-9]_[0-9][0-9]_[0-9][0-9].html$', d) \
                                          if os.path.isfile(os.path.join(folder, d))]

def readFileKeyVal(filename, key, sep):
    if os.path.isfile(filename):
        value = ""
        ifp = open(filename,  'r')
        while True:
            line = ifp.readline()            
            if not line: break                      # break while loop when no more lines
            if (line.find(key) >= 0) :
                toks = line.partition(sep)
                value  = toks[2]
                value2 = value.lstrip()
                value  = value2.rstrip()
                break
        ifp.close()
        return value
    else:
        raise Exception("\n\n\t%s file does not exist." % (filename) )

def argumentKeyVal(arg):
    """
    Process arguments like '-key=val' and returns the key and val
    """
    toks = arg.partition('=')
    key = toks[0]
    val = toks[2]
    return (key, val)

def insert(original, new, pos):
    '''Inserts new inside original at pos.'''
    return original[:pos] + new + original[pos:]

def format_label(label):
    '''Inserts <br> into string every 20 chars.'''

    new_label = " ".join(label.split())         # remove double spaces
    #new_label = new_label.replace(" ","<br>")   # replace spaces with line breaks

    # print "DEBUG 100 format_label label=%s new_label=%s" % (label, new_label)

    #
    # break before and after the "_vs_" in the label if there is one
    vs_start = new_label.find('_vs_')
    if (vs_start > 0):
        new_label = insert(new_label, "<br>", vs_start+4)
        new_label = insert(new_label, "<br>", vs_start)

    #
    # break before and after the 99_VS_99 in the label if there is one
    m = re.search(r'(\d+)' + "_VS_" + r'(\d+)' + "_", new_label)
    if m:
        beg_i = m.start()
        end_i = m.end()

        new_label = insert(new_label, "<br>", end_i)
        new_label = insert(new_label, "<br>", beg_i)

    #
    # Next, put a <br> break at least ever 20 characters between 
    # the already exiting <br> breaks.
    #

    # print "DEBUG 500 format_label new_label='%s'" % new_label

    count = 0
    break_index = 9999
    while count == 0:
        for i, c in enumerate(new_label):
            count = count + 1
            if c == '<':            # '<' implies a <br>
                count = 0           # reset count to 0 at each <br>
            if count > 23:
                if break_index == 9999:
                    break_index = i
        if break_index < 9999:
            new_label = insert(new_label, "<br>", break_index) 
            count = 0
            break_index = 9999

    #print "DEBUG 600 format_label new_label='%s'" % new_label
        
    return new_label


# #################################################################################################
# 
# Rebuilds the past-link sections of the HTML page.
# 
# #################################################################################################
def addPastResultsLinks(dir, project, groupID, subdir_html_file):

    me = "ASC_HTML.addPastResultsLinks"

    temp_file_name = "%s_%d" % (subdir_html_file, os.getpid())

    #-----------------------------------------------------------------------------------------------
    # Open the current HTML file as input and a temp file for output
    #-----------------------------------------------------------------------------------------------
    ifp = open(subdir_html_file, 'r')
    ofp = open(temp_file_name,   'w')

    im_in_the_links_section = False
    my_last_year = "Unset"

                        #---------------------------------------------------------------------------
                        # Loop over all lines in the input html file
                        #---------------------------------------------------------------------------
    while True:

        line = ifp.readline()                   # read an input line


        if not line: break                      # break while loop when no more lines

        if (line.find("end past links entries") >= 0) :

            ofp.write(line)                     # write out 'end past links entries' line

            im_in_the_links_section = False     # Set flat to indicate we are out of section

        elif (im_in_the_links_section == True): # When we are in the links section
                                                # Do not wirte out links from old html file, we 
                                                # remove them and replace them with new links
            pass

        elif (line.find("begin past links entries") >= 0) :

            im_in_the_links_section = True

            ofp.write(line)                     # write out 'begin past links entries' line


            # The proces of creating the index links is disk intensive.
            # So just do it once for the first html file  and save the lines in the list 
            # asc_html_link_lines. And reuse this list for all subsequent html files.

            if (len(asc_html_link_lines) < 1):

                dirs = listDatedDirs( dir )

                dirs.sort( reverse=True )

                for adir in dirs:
    
                    my_year  = adir[0:4]
                    my_month = (int)(adir[5:7])
    
                    my_month_name = asc_html_months_list[my_month]
    
                    subdir = "%s/%s" % (dir, adir)
    
                    # ----------------------------------------------
                    # print the 1st two columns in the table 
                    # year and month
                    # ----------------------------------------------
                    my_str = "     <TR> <!-- %s %d prior links -->" % (my_year, my_month)
    
                    if (not my_year == my_last_year):
    
                        my_str = "%s <TD>%s</TD>"  % (my_str, my_year)
    
                    else:
    
                        my_str = "%s     <TD>  </TD>" % (my_str)
    
                    my_last_year = my_year
    
                    my_str = "%s     <TD>%s</TD>     <TD>" % (my_str, my_month_name)
    
                    # ----------------------------------------------
                    # loop over each file, looking for html
                    # files with past results.
                    # Add the link to the html file into the string
                    # ----------------------------------------------
                    htmlfiles = listDatedHtmlFiles ( subdir )

                    htmlfiles.sort( reverse=False )
    
                    for htmlfile in htmlfiles:
    
                        my_day     = htmlfile[8:10]
                        my_day_int = (int)(my_day)
    
                        my_str = "%s <A HREF=\"../%s/%s\">%d</A> ." % \
                                 (my_str, adir, htmlfile, my_day_int)
    
                    # ----------------------------------------------
                    # After looping over the html files for one month
                    # end the line and write it out
                    # ----------------------------------------------
                    my_str = "%s     </TD>     </TR>\n" % (my_str)
    
                    asc_html_link_lines.append(my_str)
    
                    ofp.write(my_str)

            #
            # Else (len(asc_html_link_lines) >= 1):
            #
            # Write out the link lines already saved
            #
            else:
    
                for my_str in asc_html_link_lines:
        
                     ofp.write(my_str)
        else:

            ofp.write(line)                     # write out the line
        

                        #---------------------------------------------------------------------------
                        # close the files
                        #---------------------------------------------------------------------------
    ifp.close()
    ofp.close()

    #-----------------------------------------------------------------------------------------------
    # Remove old HTML file
    # Replace with new HTML file
    # Set group and permissions appropriately
    #-----------------------------------------------------------------------------------------------
    os.unlink( subdir_html_file )

    os.rename( temp_file_name, subdir_html_file )

    setFilePermissions( subdir_html_file, groupID)

# #################################################################################################
#
# This is called when a new html page is created, it updates the date links in all the HTML pages
# 
# #################################################################################################

def updatePastResultsLinks(dir, project, groupID):

    me = "ASC_HTML.updatePastResultsLinks"

                        #---------------------------------------------------------------------------
                        #
                        #---------------------------------------------------------------------------
    lockFile(asc_html_lock_file)

    print "%s Updating links in all HTML files" % (asc_html_info_text)

                        #---------------------------------------------------------------------------
                        # Get list of dated subdirs in main dir, those which look like '2010_09'
                        # and loop over them.
                        #---------------------------------------------------------------------------
    dirs = listDatedDirs( dir )

    for adir in dirs:
                        #---------------------------------------------------------------------------
                        # For each subdir such as 'html_nightly/2009_09'
                        #   get the list of dated html files such as '2009_09_28.html' within it
                        #---------------------------------------------------------------------------
        subdir = "%s/%s" % (dir, adir)
        htmlfiles = listDatedHtmlFiles ( subdir )

                        #---------------------------------------------------------------------------
                        # Now loop over each html file
                        #   Call the routine to update the links within each file.
                        #---------------------------------------------------------------------------
        for htmlfile in htmlfiles:

            subdir_html_file = "%s/%s" % (subdir, htmlfile)

            addPastResultsLinks(dir, project, groupID, subdir_html_file)

                        #---------------------------------------------------------------------------
                        #
                        #---------------------------------------------------------------------------
    unlockFile(asc_html_lock_file)

# #################################################################################################
#
# #################################################################################################

def writeSectionBegin(ofp):

    me = "ASC_HTML.writeSectionBegin"

    ofp.write(  "\n" \
                "     <!-- %s section --> \n" \
                "     <TR> \n" \
                "     <TH colspan=\"6\" scope=\"colgroup\"><p><p><strong><br> %s <p></strong><p></TH> \n" \
                "     </TR> \n" \
                "     <TR> \n" \
                "       <TH scope=\"col\">Machine</TH> \n" \
                "       <TH scope=\"col\">Code Task</TH> \n" \
                "       <TH scope=\"col\">Result</TH> \n" \
                "       <TH scope=\"col\">Finish Time</TH> \n" \
                "       <TH scope=\"col\">Task Log Links & Reports</TH> \n" \
                "       <TH scope=\"col\">Test Artifacts</TH> \n" \
                "     </TR> \n" \
                "\n" %
                (asc_html_sys_type, asc_html_sys_type) )

# #################################################################################################
#
# #################################################################################################

def writeSectionEnd(ofp):

    me = "ASC_HTML.writeSectionEnd"

    ofp.write("     <!-- %s end section -->\n" % (asc_html_sys_type))

# #################################################################################################
#
# #################################################################################################
def writeGenericLine(ofp, groupID, taskDescription, taskResult, taskCommand,
                     taskMsgLists, taskLogLists, taskArtLists):

    me = "ASC_HTML.writeGenericLine"

    debug = False
    if debug:
      log( "DEBUG %s groupID= %s "         % (me, groupID),         echo=True)
      log( "DEBUG %s taskDescription= %s " % (me, taskDescription), echo=True)
      log( "DEBUG %s taskResult= %s "      % (me, taskResult),      echo=True)
      log( "DEBUG %s taskCommand= %s "     % (me, taskCommand),     echo=True)
      log( "DEBUG %s taskMsgLists= %s "    % (me, taskMsgLists),    echo=True)
      log( "DEBUG %s taskLogLists= %s "    % (me, taskLogLists),    echo=True)
      log( "DEBUG %s taskArtLists= %s "    % (me, taskArtLists),    echo=True)

    ofp.write( "     <TR> <!-- %s %s -->" % (asc_html_sys_type, taskDescription) )

    #-----------------------------------------------------------------------------------------------
    # Write 1st column of html page
    #-----------------------------------------------------------------------------------------------
    ofp.write( "     <TD>%s</TD>" % (asc_html_node) )

    #-----------------------------------------------------------------------------------------------
    # Write 2nd column of html page
    #-----------------------------------------------------------------------------------------------
    ofp.write( "     <TD>%s<br><br>cmd = <br>%s<br>" % (taskDescription, taskCommand) )

    msgLists = []                       # The pop will modify the list, so create a working
    msgLists = taskMsgLists[:]          # copy and do not modify the original

    while len(msgLists) > 0 :
        msg = msgLists.pop()
        ofp.write( "     <br>%s<br>" % (msg) )

    ofp.write( "     </TD>" )
        
    #-----------------------------------------------------------------------------------------------
    # Write 3rd column of html page
    #-----------------------------------------------------------------------------------------------
    if   (taskResult == "Success"):

        ofp.write( "     <TD> %s </TD>" % (taskResult) )

    elif (taskResult == "Warning"):

        ofp.write( "     <TD BGCOLOR=yellow> <span style=\"color: black background: yellow\"> <h3> %s </h3> </TD>" % (taskResult) )

    else:

        ofp.write( "     <TD BGCOLOR=red>    <span style=\"color: white; background: red\">    <h3> %s </h3> </TD>" % (taskResult) )

        # ofp.write( "     <TD BGCOLOR=#FFFF99 ><span style=\"color: white; background: red\">%s</TD>" % (taskResult) )
        #<TD BGCOLOR=red > <span style="color: white; background: red"> <h3>Error</h3></TD>


    ofp.write( "     <TD>%s<br>%s</TD>" % (asc_html_date_string, asc_html_time_string) )

                        #---------------------------------------------------------------------------
                        # Loop over the list of files and file descriptions in the taskLogLists
                        # list and put links to all of them in the next column
                        # This includes copying over the log files to the HTML directory, 
                        # and ensuring permissions are correct
                        #---------------------------------------------------------------------------
    ofp.write( "     <TD>" )

    modLists = []                       # The pop will modify the list, so create a working
    modLists = taskLogLists[:]          # copy and do not modify the original

    while len(modLists) > 0 :

        log_list = modLists.pop()
        log_filename = log_list[0]
        (log_filename_head, log_filename_tail) = os.path.split(log_filename)
        log_description = log_list[1]

        debug = False
        if debug:
            log( "DEBUG %s file name =   %s " % (me, log_filename),    echo=True)
            log( "DEBUG %s description = %s " % (me, log_description), echo=True)

        if os.path.isfile(log_filename):

            ofp.write(  "        <A HREF=\"../%s/%s/%s\">%s </A><br>" \
                         % (asc_html_yyyymm_str, asc_html_yyyymm_dd_hhmmss_base_relative, log_filename_tail, log_description) )

            shutil.copy(log_filename, asc_html_yyyymm_dd_hhmmss_base)

            temp_file_name = "%s/%s" % (asc_html_yyyymm_dd_hhmmss_base, log_filename_tail)

            setFilePermissions( temp_file_name, groupID)

        elif log_filename.startswith("http"):
            ofp.write(  "        <A HREF=\"%s\">%s </A><br>" \
                         % (log_filename, log_description) )
        else:
            raise Exception("\n\n\t%s file %s does not exist." % (me, log_filename) )

    ofp.write( "     </TD>" )

                        #---------------------------------------------------------------------------
                        # If there are any taskArtifactLists, then do the same for them
                        #---------------------------------------------------------------------------

    ofp.write( "     <TD>" )

    modLists = []                       # The pop will modify the list, so create a working
    modLists = taskArtLists[:]          # copy and do not modify the original

    while len(modLists) > 0 :

        art_list = modLists.pop()
        art_filename = art_list[0]
        (art_filename_head, art_filename_tail) = os.path.split(art_filename)
        art_description = art_list[1]

        if os.path.isfile(art_filename):

            ofp.write(  "        <A HREF=\"../%s/%s/%s\">%s </A><br>" \
                         % (asc_html_yyyymm_str, asc_html_yyyymm_dd_hhmmss_base_relative, art_filename_tail, art_description) )

            shutil.copy(art_filename, asc_html_yyyymm_dd_hhmmss_base)

            temp_file_name = "%s/%s" % (asc_html_yyyymm_dd_hhmmss_base, art_filename_tail)

            setFilePermissions( temp_file_name, groupID)

        elif os.path.isdir(art_filename):
            dest = asc_html_yyyymm_dd_hhmmss_base + "/" + art_filename_tail
            if os.path.isdir( dest):
                shutil.rmtree(dest)
            ofp.write(  "        <A HREF=\"../%s/%s/%s/index.html\">%s </A><br>" \
                         % (asc_html_yyyymm_str, asc_html_yyyymm_dd_hhmmss_base_relative, art_filename_tail, art_filename_tail) )
            shutil.copytree(art_filename, dest)

        elif art_filename.startswith("http"):
            ofp.write(  "        <A HREF=\"%s\">%s </A><br>" \
                         % (art_filename, art_description) )

        else:
            raise Exception("\n\n\t%s file %s does not exist." % (me, art_filename) )



    ofp.write( "     </TD>" )

                        #---------------------------------------------------------------------------
                        #
                        #---------------------------------------------------------------------------
    ofp.write( "     </TR>\n" )


# #################################################################################################
# Add results of any generic task to the HTML file.
# #################################################################################################

def addGenericResults(  dir, project, groupID,
                        taskDescription,            # Short Description of Task Attempted \
                        taskResult,                 # This must be "Succes" or "Failure" \
                        taskCommand,                # Command line for task attempted \
                        taskMsgLists,               # List of message to put on front html page
                        taskLogLists,               # List of log files and file descriptions \
                        taskArtLists,               # List of further artifacts and descriptions
                        sys_type=''):
    
    me = "ASC_HTML.addGenericResults"

    debug = False
    if debug:
      log( "DEBUG %s dir = %s " % (me, dir ), echo=True)
      log( "DEBUG %s project= %s " % (me, project), echo=True)
      log( "DEBUG %s groupID= %s " % (me, groupID), echo=True)
      log( "DEBUG %s taskDescription= %s " % (me, taskDescription), echo=True)
      log( "DEBUG %s taskResult= %s " % (me, taskResult), echo=True)
      log( "DEBUG %s taskCommand= %s " % (me, taskCommand), echo=True)
      log( "DEBUG %s taskMsgLists= %s " % (me, taskMsgLists), echo=True)
      log( "DEBUG %s taskLogLists= %s " % (me, taskLogLists), echo=True)
      log( "DEBUG %s taskArtLists= %s " % (me, taskArtLists), echo=True)

    #-----------------------------------------------------------------------------------------------
    # Error Checking
    #-----------------------------------------------------------------------------------------------
    if (taskResult == "Success") or (taskResult == "Failure") or (taskResult == "Warning") :
        pass
    else:
        raise Exception("\n\n\t%s taskResult %s is invalid - must be Success, Warning, or Failure." \
                        % (me, taskResult) )
        
    #-----------------------------------------------------------------------------------------------
    # Call routine to create various date and time strings, which includes the path to todays
    # html file based on the current date.
    #-----------------------------------------------------------------------------------------------
    createDateAndTimeStrings( dir, sys_type )

    #-----------------------------------------------------------------------------------------------
    # Create the body html file (it it already exists, this will be a functional no-op)
    #-----------------------------------------------------------------------------------------------
    createBody( dir, project, groupID, sys_type )

    #-----------------------------------------------------------------------------------------------
    # Create the subdir into which the files associated with this event will be placed
    #-----------------------------------------------------------------------------------------------
    if (not os.path.isdir( asc_html_yyyymm_dd_hhmmss_base )) :
        os.makedirs( asc_html_yyyymm_dd_hhmmss_base )

    setDirectoryPermissions( asc_html_yyyymm_dd_hhmmss_base, groupID)
 
    #-----------------------------------------------------------------------------------------------
    # Create a lock file before messing with the html files
    #-----------------------------------------------------------------------------------------------
    lockFile(asc_html_lock_file)

    #-----------------------------------------------------------------------------------------------
    # This large section reads the existing HTML file, adds lines to it, and writes it out again.
    #-----------------------------------------------------------------------------------------------

                        #---------------------------------------------------------------------------
                        # Create a temporaray file name to hold the new HTML file
                        #---------------------------------------------------------------------------

    temp_file_name = "%s_%d" % (asc_html_yyyymm_dd_html_file, os.getpid()) 

                        #---------------------------------------------------------------------------
                        # Open the current HTML file as input and a temp file for output
                        #---------------------------------------------------------------------------
    ifp = open(asc_html_yyyymm_dd_html_file, 'r')
    ofp = open(temp_file_name, 'w')


    im_done          = False

    begin_section_string = "%s begin section" % (asc_html_sys_type)
    end_section_string   = "%s end section" % (asc_html_sys_type)


                        #---------------------------------------------------------------------------
                        # Loop over all lines in the input html file
                        #---------------------------------------------------------------------------
    while True:

        line = ifp.readline()           # read an input line
    
        if not line: break              # break while loop when no more lines

        if (im_done == True):           # If we are done, simply write out the line

            ofp.write(line)

        elif (line.find(begin_section_string) >= 0) :

            ofp.write(line)

        elif (line.find(end_section_string) >= 0) :

            writeGenericLine(ofp, groupID, taskDescription, taskResult, taskCommand, \
                             taskMsgLists, taskLogLists, taskArtLists)

            im_done = True

            ofp.write(line)

        elif (line.find("end nightly table") >= 0) :

            writeSectionBegin(ofp)

            writeGenericLine(ofp, groupID, taskDescription, taskResult, taskCommand, \
                             taskMsgLists, taskLogLists, taskArtLists)

            im_done = True

            writeSectionEnd(ofp)

            ofp.write(line)

        else:
            ofp.write(line)             # no other match so write out the line
        

    ifp.close()
    ofp.close()

    #-----------------------------------------------------------------------------------------------
    # Remove old HTML file
    # Replace with new HTML file
    # Set group and permissions appropriately
    #-----------------------------------------------------------------------------------------------
    os.unlink( asc_html_yyyymm_dd_html_file )

    os.rename( temp_file_name, asc_html_yyyymm_dd_html_file )

    setFilePermissions( asc_html_yyyymm_dd_html_file, groupID)

    #-----------------------------------------------------------------------------------------------
    # Unlock the html files after updating
    #-----------------------------------------------------------------------------------------------
    unlockFile(asc_html_lock_file)

    #-----------------------------------------------------------------------------------------------
    # Update the main index page after each line is added to the dated html
    #-----------------------------------------------------------------------------------------------
    createIndex(dir, project, groupID, sys_type)

    #-----------------------------------------------------------------------------------------------
    # Success, so we return now
    #-----------------------------------------------------------------------------------------------
    return

# #################################################################################################
#
#  Create an empty HTML file for todays date
#
# #################################################################################################

def createBody( dir, project, groupID, sys_type='' ):

    me = "ASC_HTML.createBody"

    #-----------------------------------------------------------------------------------------------
    # Call routine to create various date and time strings, which includes the path to todays
    # html file based on the current date.
    #-----------------------------------------------------------------------------------------------
    createDateAndTimeStrings( dir, sys_type )

    #-----------------------------------------------------------------------------------------------
    # Create directory if it doesn't exist 
    # Ensure the group on the directory is correct by setting it.
    # Ensure directory has rwxs permissions for group and user by setting them.
    #-----------------------------------------------------------------------------------------------
    if (not os.path.isdir( asc_html_yyyymm_path )) :
        os.makedirs( asc_html_yyyymm_path )

    setDirectoryPermissions( dir, groupID)
    setDirectoryPermissions( asc_html_yyyymm_path, groupID)

    #-----------------------------------------------------------------------------------------------
    # If the main body html file already exists then simply return
    #-----------------------------------------------------------------------------------------------
    if (os.path.isfile( asc_html_yyyymm_dd_html_file )) :

        return

    #-----------------------------------------------------------------------------------------------
    # Create a lock file before messing with the html files
    # only 1 script at a time should be manipulating the files.
    #-----------------------------------------------------------------------------------------------
    lockFile(asc_html_lock_file)

    #-----------------------------------------------------------------------------------------------
    # Create the HTML file
    #-----------------------------------------------------------------------------------------------

                        #---------------------------------------------------------------------------
                        # Open the file
                        # redirect prints to file
                        #---------------------------------------------------------------------------
    fp = open(asc_html_yyyymm_dd_html_file, 'w')       

    sys.stdout = fp                           
                        #---------------------------------------------------------------------------
                        # Print html file header info
                        #---------------------------------------------------------------------------
    print   "\n" \
            "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01//EN\"> \n" \
            "\n"  \
            "<HTML> \n" \
            "\n"  \
            "<HEAD> \n" \
            "<TITLE>%s Testing</TITLE> \n" \
            "</HEAD> \n" \
            "<BODY> \n" \
            "\n"  \
            "<CENTER> \n" \
            "<H2> \n" \
            "  <strong>%s Testing</strong> \n" \
            "  <p>%s \n" \
            "</H2> \n" \
            "</CENTER> \n" \
            "\n" \
            % (project, project, asc_html_yyyymm_dd_str)

                        #---------------------------------------------------------------------------
                        # Print links at top of the page
                        #---------------------------------------------------------------------------
    print   "\n" \
            "<!--  --> \n" \
            "<!--             TABLE 0 PRESENTS LINKS TO PRIOR RESULTS                 --> \n" \
            "<!--  --> \n" \
            " \n" \
            "  <TABLE border=\"1\" cellpadding=\"3\" cellspacing=\"2\"> \n" \
            " \n" \
            "     <!-- begin past links table --> \n" \
            " \n" \
            "     <TR> \n" \
            "     <TH colspan=\"3\" scope=\"colgroup\">Past Results </TH> \n" \
            "     </TR> \n" \
            "     <TR> \n" \
            "       <TH scope=\"col\" abbr=\"Name\">Year</TH> \n" \
            "       <TH scope=\"col\" abbr=\"Name\">Month</TH> \n" \
            "       <TH scope=\"col\" abbr=\"Name\">Date</TH> \n" \
            "     </TR> \n" \
            " \n" \
            "     <!-- begin past links entries --> \n" \
            " \n" \
            "     <!-- end past links entries --> \n" \
            " \n" \
            "     <!-- end past links table --> \n" \
            " \n" \
            "   </TABLE> \n" \
            " \n" \
            "   <P> \n" \
            "   <P> \n" \
            "\n";

                        #---------------------------------------------------------------------------
                        # Print table body of the html file
                        #---------------------------------------------------------------------------

    print   " \n" \
            "<!--  --> \n" \
            "<!--             TABLE 1 PRESENTS RESULTS FOR A SINGLE DAY               --> \n" \
            "<!--  --> \n" \
            " \n" \
            " \n" \
            "  <TABLE border=\"1\" cellpadding=\"6\" cellspacing=\"2\" \n" \
            "     summary=\"Nightly Testing\"> \n" \
            " \n" \
            "     <!-- begin nightly table --> \n" \
            " \n" \
            " \n" \
            "     <!-- end nightly table --> \n" \
            " \n" \
            "   </TABLE> \n" \
            " \n" \
            "\n";
                        #---------------------------------------------------------------------------
                        # print links at bottom of the page
                        #---------------------------------------------------------------------------

    print   " \n" \
            "<!-- --> \n" \
            "<!--             TABLE 2 PRESENTS LINKS TO PRIOR RESULTS                 --> \n" \
            "<!-- --> \n" \
            " \n" \
            "  <br> \n" \
            "  <br> \n" \
            " \n" \
            "  <TABLE border=\"1\" cellpadding=\"3\" cellspacing=\"2\"> \n" \
            " \n" \
            "     <!-- begin past links table --> \n" \
            " \n" \
            "     <P> \n" \
            "     <P> \n" \
            " \n" \
            "     <TR> \n" \
            "     <TH colspan=\"3\" scope=\"colgroup\">Past Results </TH> \n" \
            "     </TR> \n" \
            "     <TR> \n" \
            "       <TH scope=\"col\" abbr=\"Name\">Year</TH> \n" \
            "       <TH scope=\"col\" abbr=\"Name\">Month</TH> \n" \
            "       <TH scope=\"col\" abbr=\"Name\">Date</TH> \n" \
            "     </TR> \n" \
            " \n" \
            "     <!-- begin past links entries --> \n" \
            " \n" \
            "     <!-- end past links entries --> \n" \
            " \n" \
            "     <!-- end past links table --> \n" \
            " \n" \
            "   </TABLE> \n" \
            " \n" \
            "   </BODY> \n" \
            " \n" \
            "</HTML> \n" \
            "\n";

                        #---------------------------------------------------------------------------
                        # restore printing to stdout
                        # close the file
                        #---------------------------------------------------------------------------

    sys.stdout = sys.__stdout__                     

    fp.close()                                      

    #-----------------------------------------------------------------------------------------------
    # Set the groups and permissions on the file we just created
    #-----------------------------------------------------------------------------------------------
    setFilePermissions( asc_html_yyyymm_dd_html_file, groupID)

    #-----------------------------------------------------------------------------------------------
    # Now that we have created the html file, remove the lock file
    #-----------------------------------------------------------------------------------------------
    unlockFile(asc_html_lock_file)

    #-----------------------------------------------------------------------------------------------
    # Since we just added a file, we now need to update the links in all other static pages
    #-----------------------------------------------------------------------------------------------
    updatePastResultsLinks(dir, project, groupID)
    
    #-----------------------------------------------------------------------------------------------
    # Update the main index page after each line is added to the dated html
    #-----------------------------------------------------------------------------------------------
    createIndex(dir, project, groupID, sys_type)

    #-----------------------------------------------------------------------------------------------
    # Success, so we return now
    #-----------------------------------------------------------------------------------------------
    return


# #################################################################################################
#
#  Create 'index.html' to reflect today's html page, some links need changed to reflect the
#  moving of the file up one directory.
#
# #################################################################################################

def createIndex( dir, project, groupID, sys_type='' ):

    me = "ASC_HTML.createIndex"

    #-----------------------------------------------------------------------------------------------
    # Call routine to create various date and time strings, which includes the path to todays
    # html file based on the current date.
    #-----------------------------------------------------------------------------------------------
    createDateAndTimeStrings( dir, sys_type )

    index_html_file = "%s/index.html" % dir

    if ( not os.path.isfile( asc_html_yyyymm_dd_html_file ) ) :
        print "%s: WARNING file %s does not exist" % ( me,  asc_html_yyyymm_dd_html_file )
        return

    #-----------------------------------------------------------------------------------------------
    # Lock files
    #-----------------------------------------------------------------------------------------------
    lockFile(asc_html_lock_file)

    #-----------------------------------------------------------------------------------------------
    # Remove existing index file
    #-----------------------------------------------------------------------------------------------
    if ( os.path.isfile( index_html_file ) ) : 
        os.unlink( index_html_file )

    #-----------------------------------------------------------------------------------------------
    # Open the current HTML file as input and a temp file for output
    #-----------------------------------------------------------------------------------------------
    ifp = open(asc_html_yyyymm_dd_html_file, 'r')
    ofp = open(index_html_file,   'w')

    im_in_the_links_section = False
    my_last_year = "Unset"

                        #---------------------------------------------------------------------------
                        # Loop over all lines in todays html file
                        #---------------------------------------------------------------------------
    while True:

        line = ifp.readline()                   # read an input line

        if not line: break                      # break while loop when no more lines


        ofp.write(line.replace("../", "", 9999))

    ifp.close()
    ofp.close()

    #-----------------------------------------------------------------------------------------------
    # Set the groups and permissions on the file we just created
    #-----------------------------------------------------------------------------------------------
    setFilePermissions( index_html_file, groupID)

    #-----------------------------------------------------------------------------------------------
    #
    #-----------------------------------------------------------------------------------------------
    unlockFile(asc_html_lock_file)

    #-----------------------------------------------------------------------------------------------
    #
    #-----------------------------------------------------------------------------------------------
    return 



# #################################################################################################
#
# Create a page for one test failure, with images and artifacts
#
#   ARG             TYPE    EXPLANATION
#   testdir         string  Directory containing testing artifacts to be used for building
#                           html page
#   htmldir         string  Directory to be created, will contain html page and artifact
#                           files.
#   project         string
#   groupID         number
#   baseVersion     string
#   testVersion     string
#   testRuntime     string  num of minutes
#   system          string
#   testCase        string  name of test case
#   testSteps       list    list of strings, one for each test step with exact
#   baseUltraCurves string  name of baseline ultra curves file WITHIN the testdir
#   testUltraCurves string  name of test ultra curves file WITHIN the testdir
#   artifactLists   list of tuples (to actual files)
#   metadataList    list of tuples (metadata desc and metadata value)
#   oldNewList      list of threeples (desc, old val, new val)
#
#
# #################################################################################################

# Helper functions
def addJavaScript(js_base_url, local_html_install, js_graphics, js_curve_file):
    if js_graphics:
        print '<link href="' + js_base_url + 'atsb_layout.css" rel="stylesheet" type="text/css">' 

        addJScriptTag( js_base_url, 'jquery.js' )
        addJScriptTag( js_base_url, 'flot/jquery.flot.js' )
        addJScriptTag( js_base_url, 'flot/jquery.flot.navigate.js' )
        addJScriptTag( js_base_url, 'flot/jquery.flot.selection.js' )
        addJScriptTag( js_base_url, 'flot/jquery.flot.symbol.js' )

        addJScriptTag( js_base_url, 'asc_plot.js' )
        addJScriptTag('', js_curve_file)


    if js_graphics: # SAD June 30, 2011 If not using js graphics don't embed any java in the html
        if not local_html_install:
            addJScriptTag( js_base_url, 'prettydiff/pd.js' )
            addJScriptTag( js_base_url, 'prettydiff/prettydiff.js' )
            addJScriptTag( js_base_url, 'asc_diff.js' )

    # print   '<script language="javascript">\n'
    # print   '</script>\n'

# ###########################################################

def createBeginningHTML(testCase, project, js_base_url, local_html_install,
                        js_graphics, js_curve_file):
    print   "\n" \
            "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01//EN\"> \n" \
            "\n"  \
            "<HTML> \n" \
            "\n"  \
            "<HEAD> \n"
    #---------------------------------------------------------------------------------------
    # Add Javascript
    #---------------------------------------------------------------------------------------
    addJavaScript( js_base_url, local_html_install, js_graphics, js_curve_file)

    print   "<TITLE>%s</TITLE> \n" \
            "</HEAD> \n" \
            "<BODY> \n" \
            "\n"  \
            "<CENTER> \n" \
            "<H2> \n" \
            "  <strong>%s <p> %s </strong> \n" \
            "</H2> \n" \
            "</CENTER> \n" \
            "\n" \
            % (testCase, project, testCase)

# ###########################################################

def createEndingHTML( local_html_install, file_load_list=[], js_graphics=False, curve_name_list=[]):
    print   " \n"
    print   "</BODY> \n"

    #----------------------------------------------------------------------------------------------
    # Add the javascript calls to plot curves
    #----------------------------------------------------------------------------------------------
    if js_graphics and curve_name_list:
        print '<SCRIPT type="text/javascript">\n'
        print '$(function () {\n'
        for curve_id in curve_name_list:
            print '   plot_family("%s", %s_baseline_x, %s_baseline_y, %s_new_x, %s_new_y, options);\n' % \
                  ( curve_id, curve_id, curve_id, curve_id, curve_id)
        print '});\n'
        print '</SCRIPT>\n'

    if (not local_html_install) and file_load_list:
        print '''
<script>
function init() {
'''
        for file in file_load_list:
            print '  loadXMLDoc("' + file + '", "' + file + '");'

        print '''
}
window.onload = init;
</script>
'''
    print   "</HTML> \n"

    

# ###########################################################
    
def createTableEntryHTML_JS( curve_id, plot_type ):
    html_string = """
    <TH>
       <DIV id=\"%s\" class=\"small_plot_area\"></DIV>
       <DIV id = \"%s_container\" class=\"big_plot_container hide_big_plot_container\" >
	 <DIV id=\"%s_closer\" class=\"plot_area_closer\">CLOSE</DIV>
	 <DIV id=\"%s_large\"  class=\"plot_area\"></DIV>
	 <P class=\"message\"></P>
       </DIV>
    </TH>
"""
    plot_base_id = curve_id + '_' + plot_type
    print html_string % ( plot_base_id, plot_base_id, plot_base_id, plot_base_id )

# ###########################################################

def createTableEntryHTML_PNG( my_cur_num, prefix, cur_data_small, cur_data_large,
                              testdir, htmldir, groupID ):

    print "       <TH> \n"

    if ( (os.path.isfile( os.path.join( testdir, cur_data_small ))) and
         (os.path.isfile( os.path.join( testdir, cur_data_large )))):

        temp_name_large = "%05d-%s_data_large.png" % (my_cur_num,  prefix)
        temp_name_small = "%05d-%s_data_small.png" % (my_cur_num,  prefix)

        copyAndRenameFile(cur_data_large, temp_name_large, testdir, htmldir, groupID)
        copyAndRenameFile(cur_data_small, temp_name_small, testdir, htmldir, groupID)
        
        print "           <a href=\"%s\"> \n" % (temp_name_large)
        print "           <img src=%s>    \n" % (temp_name_small)
        print "           </a> \n"

    else:
        print "           Image %s or %s not found \n" % (cur_data_small, cur_data_large)
    print "       </TH> \n"
    print " \n"
    
# ###########################################################

def addJScriptTag( base_url, js_file):
    url = base_url + js_file
    print '<script language="javascript" type="text/javascript" src="' + url + '"></script>'

# ###########################################################

def addDivForFile( file ):
    div_id = file + '_div'
    format = '''
<div id="%s" class="wide" style="display:none";>
  <p> 
    <textarea id="%s" rows="10" cols="80"></textarea>
  </p>
</div>
'''
    print format % (div_id, file )
    
# ###########################################################
           
def createFirstTable( metadataList, testSteps, artifactList, testdir, htmldir, groupID):

    #---------------------------------------------------------------------------
    # Print the start of the first table
    #---------------------------------------------------------------------------
    print   " \n" \
            "<!--  --> \n" \
            "<!--  TABLE 1 --> \n" \
            "<!--  --> \n" \
            " \n" \
            " <H3 align=LEFT>\n" \
            " \n" \
            "  <TABLE border=\"1\" cellpadding=\"3\" cellspacing=\"2\" \n" \
            "     summary=\"Header Info Table\"> \n" \
            " \n"

    #---------------------------------------------------------------------------
    # Print all the metadata the user wants to print in the firs table.
    #---------------------------------------------------------------------------
    metaLists = []                      # The pop will modify the list, so create a working
    metaLists = metadataList[:]         # copy and do not modify the original

    while len(metaLists) > 0 :

        meta_list = metaLists.pop()
        meta_data = meta_list[0]
        meta_desc = meta_list[1]

        if (meta_data != ""):

            if os.path.isfile( meta_data):

                copyFile(os.path.basename(meta_data), os.path.dirname(meta_data),
                         htmldir, groupID)

                print "  <TR> \n" \
                      "  <TH ALIGN=left>%s</TH>\n" \
                      "  <TH ALIGN=left><a href=\"%s\">%s</a></TH> \n" \
                      " </TR>\n" \
                      " \n" \
                      % (meta_desc, os.path.basename(meta_data), os.path.basename(meta_data) )
            else:

                print "  <TR> \n" \
                      "  <TH ALIGN=left>%s</TH>\n" \
                      "  <TH ALIGN=left>%s</TH> \n" \
                      " </TR>\n" \
                      " \n" \
                      % (meta_desc, meta_data)


    #---------------------------------------------------------------------------
    # Print the test steps, with links to any files used in the steps.
    #---------------------------------------------------------------------------
    modtestSteps = []                    # The pop will modify the list, so create a working
    modtestSteps = testSteps[:]          # copy and do not modify the original

    step = 0

    while len(modtestSteps) > 0 :

        step = step + 1

        args_list = modtestSteps.pop()

        print "  <TR> \n" \
              "  <TH ALIGN=left>Test Step %d </TH>\n" \
              "  <TH ALIGN=left>" \
              % (step)

        for word in args_list.split(' '):

            if os.path.isfile(testdir + '/' + word):

                copyFile(word, testdir, htmldir, groupID)

                print " <a href=\"%s\">%s</a>" % (word, word)
            else:
                print " " + word


        print " </TH> \n" \
              " </TR>\n" \
              " \n"

    #---------------------------------------------------------------------------
    # print the artifact list of files
    #---------------------------------------------------------------------------
    artList = []                      # The pop will modify the list, so create a working
    artList = artifactList[:]         # copy and do not modify the original

    while len(artList) > 0 :

        art_list = artList.pop()
        art_file = art_list[0]
        art_desc = art_list[1]

        if os.path.isfile(testdir + '/' + art_file):

            copyFile(art_file, testdir, htmldir, groupID)

            print "  <TR> \n" \
                  "  <TH ALIGN=left>%s</TH>\n" \
                  "  <TH ALIGN=left><a href=\"%s\">%s</a></TH> \n" \
                  " </TR>\n" \
                  " \n" \
                  % (art_desc, art_file, art_file)

        elif os.path.isfile( art_file):

            copyFile(art_file, testdir, htmldir, groupID)

            print "  <TR> \n" \
                  "  <TH ALIGN=left>%s</TH>\n" \
                  "  <TH ALIGN=left><a href=\"%s\">%s</a></TH> \n" \
                  " </TR>\n" \
                  " \n" \
                  % (art_desc, os.path.basename(art_file), os.path.basename(art_file) )

        else:
            print "  <TR> \n" \
                  "  <TH ALIGN=left>Baseline Ultra Curves </TH>\n" \
                  "  <TH ALIGN=left>Error! Did Not Find File <br> %s/%s </TH> \n" \
                  " </TR>\n" \
                  " \n" \
                  % (testdir, art_file)

    #---------------------------------------------------------------------------
    # Print the end of the first table
    #---------------------------------------------------------------------------
    print   " \n" \
            "  </TABLE> \n" \
            " </H3> \n" \
            " \n" \
            " \n"

# ###########################################################

def createSecondTable( oldNewList, testdir, htmldir, groupID, local_html_install ):
    """
    Print all the old/new data pairs the user wants to print in the second table.
    """
    oldNewLists = []                    # The pop will modify the list, so create a working
    oldNewLists = oldNewList[:]         # copy and do not modify the original
    buttonFileNameList = []
    
    print   " \n" \
            "<!--  --> \n" \
            "<!--  TABLE 2 --> \n" \
            "<!--  --> \n" \
            " \n" \
            " <H3 align=LEFT>\n" \
            " \n" \
            "    <TABLE border=\"1\" cellpadding=\"3\" cellspacing=\"2\" \n" \
            "       summary=\"Header Info Table\"> \n" \
            " \n"

    print "  <TR> \n"
    print "  <TH ALIGN=left>%s</TH>\n"  % "Data Description"
    print "  <TH ALIGN=left>%s</TH>\n"  % "Baseline Data"
    print "  <TH ALIGN=left>%s</TH> \n" % "Tested Data"
    print " </TR>\n"
    print "\n" 

    while len(oldNewLists) > 0 :

        oldNew_list = oldNewLists.pop()
        old_data = oldNew_list[0]
        new_data = oldNew_list[1]
        desc     = oldNew_list[2]
        if len(oldNew_list) == 4:
            add_button  = True
            button_name = oldNew_list[3]
            button_oldName = os.path.basename(old_data)
            button_newName = os.path.basename(new_data)
            buttonFileNameList.append( button_oldName )
            buttonFileNameList.append( button_newName )
        else:
            add_button = False

        if (desc != ""):

            #
            # If there is no data for both fields, then do not print a table entry
            #
            if (old_data == "") and (new_data == ""):
                continue

            print "  <TR> \n"
            if add_button:
                txt  = '<TH ALIGN=left>' + desc
                txt += '<button value="diff"'
                txt += ' onclick=\'popUpDiffWindow("' + \
                       button_oldName + '","' + button_newName + '");\''
                txt += ' type=button>' + button_name + '</button></TH>\n'
                print  txt
            else:
                print "  <TH ALIGN=left>%s</TH>\n"  % desc

            if os.path.isfile(testdir + '/' + old_data):
                old_name = os.path.basename( old_data)
                copyFile(old_data, testdir, htmldir, groupID)
                print "  <TH ALIGN=left><a href=\"%s\">%s</a></TH> \n" % (old_name, old_name)
            elif os.path.isfile( old_data ):
                old_name = os.path.basename( old_data)
                copyFile(old_data, testdir, htmldir, groupID)
                print "  <TH ALIGN=left><a href=\"%s\">%s</a></TH> \n" % (old_name, old_name)
            else:
                print "  <TH ALIGN=left>%s</TH> \n" % old_data

            if os.path.isfile(testdir + '/' + new_data):
                new_name = os.path.basename( new_data)
                copyFile(new_data, testdir, htmldir, groupID)
                print "  <TH ALIGN=left><a href=\"%s\">%s</a></TH> \n" % (new_name, new_name)
            elif os.path.isfile( new_data ):
                new_name = os.path.basename( new_data)
                copyFile(new_data, testdir, htmldir, groupID)
                print "  <TH ALIGN=left><a href=\"%s\">%s</a></TH> \n" % (new_name, new_name)
            else:
                print "  <TH ALIGN=left>%s</TH> \n" % new_data

            print " </TR>\n"
            print "\n" 

    #---------------------------------------------------------------------------
    # Print the end of the second table
    #---------------------------------------------------------------------------
    print   " \n" \
            "    </TABLE> \n" \
            " </H3> \n" \
            " \n" \
            " \n"

    if not  local_html_install:
        for file in buttonFileNameList:
            addDivForFile( file )

    return buttonFileNameList    

# ###########################################################

def createThirdTable( curveList, testdir, htmldir, groupID, js_graphics, js_curve_file ):
    curve_name_list = []
    
    if js_graphics:
        if os.path.isfile(testdir + '/' + js_curve_file):
            copyFile(js_curve_file, testdir, htmldir, groupID)
                
    #---------------------------------------------------------------------------
    # Print the THIRD table if there are curves
    #---------------------------------------------------------------------------
    if (len(curveList) > 0) :

        #---------------------------------------------------------------------------
        # Print the start of the third table
        #---------------------------------------------------------------------------
        print   " \n" \
                "<!--  --> \n" \
                "<!--  TABLE 3 --> \n" \
                "<!--  --> \n" \
                " \n" \
                "  <TABLE border=\"1\" cellpadding=\"2\" cellspacing=\"2\" \n" \
                "     summary=\"Detailed Curve Table\"> \n" \
                " \n" \
                "     <br> \n" \
                "     <br> \n" \
                " \n" \
                "     <TR> \n" \
                "       <TH>Curve Description</TH> \n" \
                "       <TH>Code Curves \n" \
                "          <br><font color=\"purple\">Purple = New Curve </font> \n" \
                " \n" \
                "          <br><font color=\"green\">Green = Baseline Curve </font> \n" \
                "       </TH> \n" \
                "       <TH>Absolute Difference Curve </TH> \n" \
                "       <TH>Relative Difference Curve </TH> \n" \
                "     </TR> \n" \
                " \n" \
                " \n"
    
    
    
        #---------------------------------------------------------------------------
        # Print all the curve images the user wants to print in the third table.
        #---------------------------------------------------------------------------
        curList = []                   # The pop will modify the list, so create a working
        curList = curveList[:]         # copy and do not modify the original
        my_cur_num = 0
    
        while len(curList) > 0 :

            cur_list       = curList.pop()
            cur_num        = cur_list[0]
            cur_desc       = cur_list[1]
            cur_data_small = cur_list[2]
            cur_data_large = cur_list[3]
            abs_data_small = cur_list[4]
            abs_data_large = cur_list[5]
            rel_data_small = cur_list[6]
            rel_data_large = cur_list[7]
            if len(cur_list) > 8:
              abs_tolerance = cur_list[8]
              rel_tolerance = cur_list[9]
            else:
              abs_tolerance = ""
              rel_tolerance = ""
            
            #
            # We were getting an empty item in the curve list for some reason
            # bypass this if it happens
            #
            if cur_num == "" and cur_desc == "" :
                continue

            my_cur_num = my_cur_num + 1

            debug = False
            if debug:
                log("DEBUG ASC_HTML 202 cur_data_small = %s" % (cur_data_small), echo=True)
                log("DEBUG ASC_HTML 202 cur_data_large = %s" % (cur_data_large), echo=True)
                log("DEBUG ASC_HTML 202 abs_data_small = %s" % (abs_data_small), echo=True)
                log("DEBUG ASC_HTML 202 abs_data_large = %s" % (abs_data_large), echo=True)
                log("DEBUG ASC_HTML 202 rel_data_small = %s" % (rel_data_small), echo=True)
                log("DEBUG ASC_HTML 202 rel_data_large = %s" % (rel_data_large), echo=True)

            formatted_desc = format_label(cur_desc)
    
            print "     <TR> \n"
            if abs_tolerance:
                print "       <TH AlIGN=LEFT><CODE><FONT SIZE=5> Curve %s <br><br> %s <br><br>Tolerances<br> abs: %s <br> rel: %s\n" % (cur_num, formatted_desc, abs_tolerance, rel_tolerance)
            else:
                print "       <TH AlIGN=LEFT><CODE><FONT SIZE=5> Curve %s <br><br> %s \n" % (cur_num, formatted_desc)
            print "       </CODE></FONT></TH> \n"
            print " \n"

            if js_graphics:
                
                temp_name = "curve" + cur_num
                createTableEntryHTML_JS( temp_name, "actual"  )
                createTableEntryHTML_JS( temp_name, "abs_diff")
                createTableEntryHTML_JS( temp_name, "rel_diff")
                curve_name_list.append( temp_name )

            else:

                createTableEntryHTML_PNG( my_cur_num, "cur", cur_data_small, cur_data_large,
                                      testdir, htmldir, groupID )
                createTableEntryHTML_PNG( my_cur_num, "abs", abs_data_small, abs_data_large,
                                      testdir, htmldir, groupID )
                createTableEntryHTML_PNG( my_cur_num, "rel",rel_data_small, rel_data_large,
                                          testdir, htmldir, groupID )
                
            print "     </TR> \n"

        #---------------------------------------------------------------------------
        # Print the end of the third table
        #---------------------------------------------------------------------------

        print " \n" \
              " \n" \
              "   </TABLE> \n"


    return curve_name_list

# ###########################################################

def createOneTestFailureHtmlPage( testdir, 
                                  htmldir,      
                                  groupID,      
                                  project,
                                  testCase,
                                  testSteps,    
                                  metadataList,
                                  oldNewList,
                                  artifactList,
                                  curveList,
                                  html_install_dir='',
                                  js_graphics=False,
                                  sys_type=''):

    me = "ASC_HTML.createOneTestFailureHtmlPage"

    if html_install_dir.startswith('file:///'):
      local_html_install = True
      js_base_url = 'file:///usr/gapps/bdiv/python/ATSB/www/'
    else:
      local_html_install = True
      js_base_url = 'file:///usr/gapps/bdiv/python/ATSB/www/'
    
    js_curve_file = testCase + ".pdl.curves.js"

    #print "oldNew LIST"
    #while len(oldNewList) > 0 :
    #    list = oldNewList.pop()
    #    print list

    #print curveList
    #sys.exit("debugging")


    #-----------------------------------------------------------------------------------------------
    # Call routine to create various date and time strings
    #-----------------------------------------------------------------------------------------------
    createDateAndTimeStrings( htmldir, sys_type )

    #-----------------------------------------------------------------------------------------------
    # Remove dir if it exists
    # Create directory
    # Ensure the group on the directory is correct by setting it.
    # Ensure directory has rwxs permissions for group and user by setting them.
    #-----------------------------------------------------------------------------------------------
    if (os.path.isdir( htmldir )) :
        shutil.rmtree(htmldir, ignore_errors=1)

    os.makedirs( htmldir)
    setDirectoryPermissions( htmldir, groupID)

    index_html_file = htmldir + '/' + 'index.html' 

    #-----------------------------------------------------------------------------------------------
    # Create a lock file before messing with the html files
    # only 1 script at a time should be manipulating the files.
    #-----------------------------------------------------------------------------------------------
    asc_html_lock_file = index_html_file + "_update_lock"
    lockFile(asc_html_lock_file)

    #-----------------------------------------------------------------------------------------------
    # Create the HTML file
    # Print the start of the HTML file
    #-----------------------------------------------------------------------------------------------

    #---------------------------------------------------------------------------
    # Open the file
    # redirect prints to file
    #---------------------------------------------------------------------------
    fp = open(index_html_file, 'w')       

    sys.stdout = fp                           
    #---------------------------------------------------------------------------
    # Print html file header info
    #---------------------------------------------------------------------------
    createBeginningHTML(testCase, project, js_base_url, local_html_install,
                        js_graphics, js_curve_file)

    #-------------------------------------------------------------------------------------------
    # Print the first table
    #-------------------------------------------------------------------------------------------
    createFirstTable( metadataList, testSteps, artifactList, testdir, htmldir, groupID)
    
    #-------------------------------------------------------------------------------------------
    # Print the second table
    #-------------------------------------------------------------------------------------------
    file_load_list = createSecondTable( oldNewList, testdir, htmldir, groupID, local_html_install)
    
    #-------------------------------------------------------------------------------------------
    # Print the third table if there are curves
    #-------------------------------------------------------------------------------------------
    curve_name_list = createThirdTable( curveList, testdir, htmldir, groupID,
                                        js_graphics, js_curve_file)

    #----------------------------------------------------------------------------------------------
    # Print the end of the HTML file
    #----------------------------------------------------------------------------------------------
    createEndingHTML( local_html_install, file_load_list, js_graphics, curve_name_list)

    #---------------------------------------------------------------------------
    # restore printing to stdout
    # close the file
    #---------------------------------------------------------------------------

    sys.stdout = sys.__stdout__                     

    fp.close()                                      

    #-----------------------------------------------------------------------------------------------
    # Set the groups and permissions on the file we just created
    #-----------------------------------------------------------------------------------------------
    setFilePermissions( index_html_file, groupID)

    #-----------------------------------------------------------------------------------------------
    # Now that we have created the html file, remove the lock file
    #-----------------------------------------------------------------------------------------------
    unlockFile(asc_html_lock_file)

    #-----------------------------------------------------------------------------------------------
    # Success, so we return now
    #-----------------------------------------------------------------------------------------------
    return

  
# ##################################################################################################
#                                       E N D   O F   F I L E 
# ##################################################################################################
