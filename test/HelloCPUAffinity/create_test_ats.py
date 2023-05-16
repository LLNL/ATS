#!/usr/bin/env python3
"""Create a test.ats file."""
import itertools
import os
import sys


def get_file_header():
    """Returns ATS test file header. Contains imports, glue, and checker."""

    ofp_header = f"""import os
glue(independent=True)
glue(keep=True)
"""
    return ofp_header


def get_test_lines_generator():
    """Returns a generator containing independent tests."""

    # Command line args - 'clas' alternate between three args and nothing.
    clas = itertools.cycle(['', '2', '10', '20'])

    # Duplicate items in nprocs: [1, 2, ..., 64] --> [1, 1, 2, 2, ..., 64, 64]
    nprocs = sorted(4 * [1, 2, 4, 10])

    test_line = "t%d=test  (executable='./a.out', clas='%s', " \
                "label='a.out_%d', np=%d)\n"

    return (test_line % (test_num, arg_, test_num, num_proc)
            for test_num, arg_, num_proc in zip(range(1, 44, 1), clas, nprocs))


if __name__ == "__main__":
    TEST_ATS = "test.ats"
    FILE_HEADER = get_file_header()
    TEST_LINES = get_test_lines_generator()

    with open(TEST_ATS, 'w') as ofp:
        ofp.write(FILE_HEADER)
        for test in TEST_LINES:
            ofp.write(test)

    print(f"Most Excellent! Created ats test file {TEST_ATS}\n")
