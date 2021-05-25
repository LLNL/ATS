#!/usr/apps/ats/7.0.1/bin/python
import os
import sys

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(1)

    logfile = sys.argv[1]

    if os.path.exists(logfile):
        with open(logfile, 'r') as f:
            lines = f.readlines()

        for line in lines:
            if "SUCCESS" in line:
                print "checker success"
                sys.exit(0)
            elif "FAILURE" in line:
                print "checker failed"
                sys.exit(-1)

    # If we get to here, we did not find the log file
    # or the log file did not have PASSED in it
    print "test did not pass"
    sys.exit(1)
