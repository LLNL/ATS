#!/usr/bin/env python3
"""Create a test.ats file."""
import itertools
import os
import sys


def get_file_header():
    """Returns ATS test file header. Contains imports, glue, and checker."""

    ats_file_read_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'test_file_read.py')
    if not os.path.isfile(ats_file_read_path): 
        sys.exit(1)

    ats_file_write_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'test_file_write.py')
    if not os.path.isfile(ats_file_write_path):  
        sys.exit(1)



    ofp_header = f"""import os
glue(independent=True)
glue(keep=True)
my_file_write_script = '{ats_file_write_path}'
my_file_read_script = '{ats_file_read_path}'
"""
    return ofp_header


def get_test_lines_generator():
    """Returns a generator containing independent tests."""
    nprocs = sorted(2 * [10, 20, 30, 40, 50, 60, 70, 80])
    same_node_labels = itertools.cycle(['nodeA', 'nodeB', 'nodeC', 'nodeA', 'nodeA'])
    test_line = "t%d=test  (executable = my_file_write_script, level=20, clas='%s_%d', " \
                "label='t%d_label', np=%d, same_node='%s')\n"

    return (test_line % (test_num, label, test_num, test_num, num_proc, label)
            for test_num, num_proc, label in zip(range(1, 44, 2), nprocs, same_node_labels))

def get_testif_lines_generator():
    """Returns a generator containing testifs (conditional tests)."""
    same_node_labels = itertools.cycle(['nodeA', 'nodeB', 'nodeC', 'nodeA', 'nodeA'])
    testif_line = "t%d=testif(t%d, executable = my_file_read_script, " \
                  "level=20, clas='%s_%d', label='t%d_label', same_node='%s')\n"
    return (testif_line % (testif_num, testif_num - 1, label, testif_num - 1, testif_num, label)
            for testif_num, label  in zip (range(2, 45, 2), same_node_labels))

if __name__ == "__main__":
    TEST_ATS = "test.ats"
    FILE_HEADER  = get_file_header()
    TEST_LINES   = get_test_lines_generator()
    TESTIF_LINES = get_testif_lines_generator()

    with open(TEST_ATS, 'w') as ofp:
        ofp.write(FILE_HEADER)

        for test, testif in zip(TEST_LINES, TESTIF_LINES):
            ofp.write(test)
            ofp.write(testif)

    print(f"Most Excellent! Created ats test file {TEST_ATS}\n")
