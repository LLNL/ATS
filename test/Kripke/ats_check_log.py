#!/usr/bin/env python3
import os
import sys

if __name__ == '__main__':

    assert len(sys.argv) == 2, "Expected 1 argument."

    logfile = sys.argv[1]
    assert os.path.exists(logfile), f"File '{logfile}' not found."

    with open(logfile) as _file:
        log_file_text = _file.read()

    assert "Differences found" not in log_file_text, "test did not pass"
    print("test passed")
