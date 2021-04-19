#!/usr/apps/ats/7.0.0/bin/python

########################################################################################################################
# Get path to python used to execute this script, and setup other paths which can be used by clients to import
# modules.
########################################################################################################################

import sys
sys.dont_write_bytecode = True
import os

#
# Find modules built and distributed with this python distribution.
#
#atsModulesDir            = '/g/g16/dawson/atsnightly/nightlyTests/chaos_5_x86_64_ib/'
tempstr                  = sys.executable
atsModulesDir            = tempstr.replace('bin/python','')
atsASC_Checkers_dir      = os.path.join(atsModulesDir, 'atsASC/checkers');
atsASC_Modules_dir       = os.path.join(atsModulesDir, 'atsASC/modules');
atsASC_Visit_Testing_dir = os.path.join(atsModulesDir, 'atsASC/Visit');
atsExtras_dir            = os.path.join(atsModulesDir, 'atsExtras');

print "atsModulesDir            = %s" % atsModulesDir
print "atsASC_Checkers_dir      = %s" % atsASC_Checkers_dir
print "atsASC_Modules_dir       = %s" % atsASC_Modules_dir
print "atsASC_Visit_Testing_dir = %s" % atsASC_Visit_Testing_dir
print "atsExtras_dir            = %s" % atsExtras_dir

sys.path.append( atsASC_Visit_Testing_dir )

from visit_testing import *

########################################################################################################################
#
# File as kinda distributed by Visit starts here
#
########################################################################################################################
"""
file: example_driver.py

description:

Basic driver that runs a visit test and consumes 
the results of all the test cases run .

"""

# #################################################################################################
# Main so this script may be run standalone
# ##################################################################################################
if __name__=="__main__":

    #
    # Call a VisIt test script using VisIt's testing infrastructure.
    #
    res = run_visit_test("tests/category/example_script.py",
                         data_dir="data",
                         baseline_dir="baseline",
                         output_dir="_results_%s" % os.environ["USER"])

    #
    # After this method returns:
    #
    # 1) `res' will be a python dictonary that holds a tree of results.
    #
    # 2) A bunch of goodies will live in the dir `_results'
    #
    #  * To view the generated html pages open `_results/html/index.html'
    #  * The contents of `res' are also stored in `_results/results.json'
    #    (you can load them manually via json.load(open("_results/results.json"))
    #
    # 3) The current results (images and text) are in `_results/current'
    #    If you need to rebaseline, you can simply replace the contexts of `baseline'
    #    with the appropriate files from `_results/current'
    #
    # For this example driver, simply traverse the result tree and print 
    # the details of each script tested 
    #
    #
    #
    print ""
    print "[example results]"
    for script_result in res["results"]:
        print "%s/%s" % (script_result["category"],script_result["file"]) ,
        print ": " , script_result["status"]
        for sect in script_result["details"]["sections"]:
            print " section:", sect["name"]
            print "  cases:"
            for case in sect["cases"]:
                print "   %s: %s" % (case["name"],case["status"])
    

# End of File
