#!/usr/bin/env python3
"""Write a file on disk to /usr/tmp."""
import os
import sys
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

if __name__ == "__main__":

    if len(sys.argv) > 1:
        node_label=sys.argv[1]
    else:
        node_label="unset"

    TEST_FILE = "/usr/tmp/ats_test_same_node_" + node_label + ".txt"

    if (rank == 0):
        with open(TEST_FILE, 'w') as ofp:
            ofp.write("testing same_node option under ATS")
        ofp.close()

        print(f"Most Excellent! wrote file %s\n" % TEST_FILE)

    sys.exit(0)
