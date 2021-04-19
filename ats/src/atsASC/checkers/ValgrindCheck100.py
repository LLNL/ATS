#!/usr/apps/ats/7.0.0/bin/python

import sys
import os
import re
#print "DEBUG SAD ValgrindCheck100 atsASC_Modules_dir = %s " % atsASC_Modules_dir
from atsASC.modules.ASC_utils import listfiles, execute, readFile

from optparse import OptionParser


####################################################################################
#
####################################################################################

def listfilesWithKernel(folder, kernel):
    kernel_string = "^%s" % kernel
    return [d for d in os.listdir(folder) if re.search(kernel_string, d) \
                                          if os.path.isfile(os.path.join(folder, d))]

# #################################################################################################
#
# pyCheck101 : First of possibly many future checking programs to be used with atsb.
#
# #################################################################################################
if __name__=="__main__":

    # ---------------------------------------------------------------------------------------------
    # local vars
    # ---------------------------------------------------------------------------------------------
    here = os.getcwd()          # current directory
    
    # ---------------------------------------------------------------------------------------------
    # Process command line args
    # ---------------------------------------------------------------------------------------------
    if (len(sys.argv) != 3):
        print "Usage: %s kernel label " % sys.argv[0]
        sys.exit(-1)

    kernel = sys.argv[1]
    kernel = sys.argv[2]

    # ---------------------------------------------------------------------------------------------
    # Create a list of valgrind files for this kernel.
    # Loop over each file.
    # Read the file, find the line which looks like:
    #
    # ==32623== ERROR SUMMARY: 883 errors from 261 contexts (suppressed: 120726 from 3060)
    #
    # Split the above line to get words list like so:
    #
    #
    # ['==32623==', 'ERROR', 'SUMMARY:', '883', 'errors', 'from', '261', 'contexts', '(suppressed:', '120726', 'from', '3060)']
    #
    # Grab the num of errors from the above words list by using hard coded index 3
    #
    # 883
    #
    # ---------------------------------------------------------------------------------------------
    max_num_errors = 0
    files = listfilesWithKernel(".", kernel + "-valgrind-")
    for a_file in files:
        lines = readFile(a_file)
        for line in lines:
            if re.search("ERROR SUMMARY", line):
                words = line.split()
                num_errors = int(words[3])
                print "File %s Valgrind_Errors %d " % (a_file, num_errors)
                if (num_errors > max_num_errors):
                    max_num_errors = num_errors

    if (max_num_errors > 0):
        sys.exit(-1)
    else:
        sys.exit(0)

# #################################################################################################
# End of File
# #################################################################################################
