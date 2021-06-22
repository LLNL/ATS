#!/usr/bin/env python3
import os
import sys

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(1)

    LOGFILE = sys.argv[1]

    if os.path.exists(LOGFILE):
        with open(LOGFILE, 'r') as f:
            LOGFILE_CONTENTS = f.read()

        if "SUCCESS" in LOGFILE_CONTENTS:
            print("checker success")
            sys.exit(0)
        elif "FAILURE" in LOGFILE_CONTENTS:
            print("checker failed")
            sys.exit(-1)

    # If we get to here, we did not find the log file
    # or the log file did not have SUCCESS in it
    print("test did not pass")
    sys.exit(1)
