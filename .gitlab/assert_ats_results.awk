#!/usr/bin/awk -f

###############################################################################
## PURPOSE:
##  Compare expected totals of test results against ats.log file.
##
## USAGE:
##  assert_ats_results.awk -v PASSED=<num> FAILED=<num> SKIPPED=<num> ats.log
###############################################################################

/^PASSED:/ { PASSED_FOUND=$2 }
/^FAILED:/ { FAILED_FOUND=$2 }
/^SKIPPED:/ { SKIPPED_FOUND=$2 }

END {
    if ( PASSED == "" ) {
        printf("ERROR: 'PASSED' variable not set in %s", FILENAME)
        exit 1
    }
    if ( FAILED == "" ) {
        printf("ERROR: 'FAILED' variable not set in %s", FILENAME)
        exit 1
    }
    if ( SKIPPED == "" ) {
        printf("ERROR: 'SKIPPED' variable not set in %s", FILENAME)
        exit 1
    }

    if ( PASSED == PASSED_FOUND &&
         FAILED == FAILED_FOUND &&
         SKIPPED == SKIPPED_FOUND ) {
        print "Success! Expected PASSED, FAILED, SKIPPED results found."
        exit 0
    }

    print "ASSERTION FAILED: Expected PASSED, FAILED, SKIPPED results not found."
    print "\nResults found:"
    printf("%18s %10s\n", "Expected", "Actual")
    printf("PASSED: %10d %10d\n", PASSED, PASSED_FOUND)
    printf("FAILED: %10d %10d\n", FAILED, FAILED_FOUND)
    printf("SKIPPED: %9d %10d\n", SKIPPED, SKIPPED_FOUND)
    exit 1
}
