#!/usr/bin/env python3
"""Create a test.ats file."""
import itertools
import os
import sys


def get_file_header():
    """Returns ATS test file header. Contains imports, glue, and checker."""
    ats_log_checker_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'ats_check_log.py')
    if not os.path.isfile(ats_log_checker_path):
        sys.exit(1)

    ofp_header = f"""import os
glue(independent=True)
glue(keep=True)
my_checker = '{ats_log_checker_path}'
"""
    return ofp_header


def get_test_lines_generator():
    """Returns a generator containing independent tests."""
    # Command line args - 'clas' alternate between three args and nothing.
    clas = itertools.cycle(['', 'arg1 arg2 arg3'])
    # Duplicate items in nprocs: [1, 2, ..., 64] --> [1, 1, 2, 2, ..., 64, 64]
    nprocs = sorted(2 * [1, 2, 3, 4, 5, 6, 7, 8, 16 ])

    test_line = "t%d=test  (executable='./a.out', clas='%s', " \
                "label='a.out_%d', np=%d, sandbox=False)\n"
    return (test_line % (test_num, arg_, test_num, num_proc)
            for test_num, arg_, num_proc in zip(range(1, 44, 2), clas, nprocs))


def get_testif_lines_generator():
    """Returns a generator containing testifs (conditional tests)."""
    testif_line = "t%d=testif(t%d, executable = my_checker, " \
                  "clas = t%d.outname, nosrun=True)\n"
    return (testif_line % (testif_num, testif_num - 1, testif_num - 1)
            for testif_num in range(2, 45, 2))


if __name__ == "__main__":
    TEST_ATS = "test.ats"
    FILE_HEADER = get_file_header()
    TEST_LINES = get_test_lines_generator()
    TESTIF_LINES = get_testif_lines_generator()

    with open(TEST_ATS, 'w') as ofp:
        ofp.write(FILE_HEADER)
        for test, testif in zip(TEST_LINES, TESTIF_LINES):
            ofp.write(test)
            ofp.write(testif)

    print(f"Most Excellent! Created ats test file {TEST_ATS}\n")
