#!/usr/bin/env python3
"""Create a test.ats file."""
import itertools
import os
import sys


def get_file_header():
    """Returns ATS test file header. Contains imports, glue."""
    ofp_header = f"""import os
glue(independent=True)
glue(keep=True)
"""
    return ofp_header


def get_test_lines_generator():
    """Returns a generator containing independent tests."""

    # Command line args - 'secs' alternate between 2, 5, and 10 seconds for sleep time.
    secs = itertools.cycle(['5', '10', '20'])

    # nodes alternate between ...
    nnodes = itertools.cycle(['0', '1', '2'])

    # nthreads alternate between ...
    nthreads = itertools.cycle(['4,', '2'])

    # nprocs alternate between ...
    nprocs = itertools.cycle(['2', '4'])

    test_line = "t%d=test  (executable='./omp_test', clas='%d %s', " \
                "label='omp_test_%d', nn=%s, np=%s, nt=%s)\n"

    return (test_line % (test_num, test_num, sec, test_num, num_nodes, num_proc, num_threads)
        for test_num, sec, num_nodes, num_proc, num_threads in 
            zip(range(1, 44, 2), secs, nnodes, nprocs, nthreads))



if __name__ == "__main__":
    TEST_ATS = "test.ats"
    FILE_HEADER = get_file_header()
    TEST_LINES = get_test_lines_generator()

    with open(TEST_ATS, 'w') as ofp:
        ofp.write(FILE_HEADER)
        for test in TEST_LINES:
            ofp.write(test)

    print(f"Most Excellent! Created ats test file {TEST_ATS}\n")
