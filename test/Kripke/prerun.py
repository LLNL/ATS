#!/usr/bin/env python3
import sys

# 2016-Oct-18 Initial script setup by Shawn Dawson
#
# Sample post run script for use with Kripke and Veritas
# 
# Several items that could be of use to Veritas are passed in as 
# arguments.
#
# As checkers are just another test, and as the post run script is run for all tests, this
# will also be called for the checkers. 
#
# These can be differentiated by looking at sys.argv[1] which is likely to be 'kripke' for Kripke
# and something else for the checker.  Depending on how Veritas wants to process data, either of these
# may be of use.  
#
# Contact Shawn for the list of the other arguments, or for needed data that is not there yet.
# He has started with the number of processors, the executable, the name of the executable log file (stdout)
# the actual test command line, and the directory where the test was run, but this was just a guess
# to get us started.
#

if __name__ == "__main__":
    print "Hello From Pre Run Script"

    for index, arg in enumerate(sys.argv):
        print(f"Argument {index}: {arg}")
