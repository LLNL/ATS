#!/usr/apps/ats/7.0.1/bin/python
import os
import sys

if __name__ == '__main__':
    pwd = os.getcwd()

    if len(sys.argv) < 2:
        sys.exit(1)

    logfile = sys.argv[1]

    if os.path.exists(logfile):

        f = open( logfile, 'r')
        lines = f.readlines()
        f.close

        for line in lines:
            if "Differences found" in line:
                print "test did not pass"
                sys.exit(1)

        # If we get to here, we found no differences
        # test was good
        print "test passed"
        sys.exit(0)

    # If we get to here, we did not find the log file
    print "test did not pass"
    sys.exit(1)

# end of file
