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
atsASC_Visit_Testing_dir = os.path.join(atsModulesDir, 'atsASC/Visit');
sys.path.append( atsASC_Visit_Testing_dir )

from atsASC.Visit.visit_testing.visit_testing import *

# #################################################################################################
# Main so this script may be run standalone
# ##################################################################################################
if __name__=="__main__":

    #
    # Verify arguments to this driver script
    # Verify the script given exists and ends with .py
    # Construct baseline and results dirs based on the script name
    #
    if len(sys.argv) < 2:
        print "Usage : %s test_script" % sys.argv[0]
        sys.exit(1)
    my_test_script = sys.argv[1]

    if not os.path.isfile(my_test_script) or not my_test_script.endswith('.py'):
        print "Error: %s is not a python test script" % my_test_script
        sys.exit(1)

    my_baseline_dir = my_test_script.replace(".py","_baseline")
    my_results_dir  = my_test_script.replace(".py","_results")

    #
    # Call a VisIt test script using VisIt's testing infrastructure.
    #
    res = run_visit_test(my_test_script,
                         baseline_dir=my_baseline_dir,
                         data_dir=os.getcwd(),
                         verbose=True, 
                         output_dir=my_results_dir)

    #
    # Process results of running the test
    #
    return_code = 0
    print ""
    print "[example results]"
    for script_result in res["results"]:
        print "%s/%s" % (script_result["category"],script_result["file"]) ,
        print ": " , script_result["status"]
        if script_result["status"] == "unacceptable":
            return_code = -1
        ooga = script_result["status"]
        for sect in script_result["details"]["sections"]:
            print " section:", sect["name"]
            print "  cases:"
            for case in sect["cases"]:
                print "   %s: %s" % (case["name"],case["status"])

    sys.exit(return_code)
    
# End of File
