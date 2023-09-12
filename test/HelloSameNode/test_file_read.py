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

    if rank == 0:
        f = open(TEST_FILE, 'r')
        lines = f.readlines()
        for line in lines:
            print(line)
            if (line == "testing same_node option under ATS"):
                print(f"Most Excellent! Read file correctly %s\n" % TEST_FILE)
            else:
                print(f"Bummer! Read file incorrectly %s\n" % TEST_FILE)
                os.remove(TEST_FILE)
                sys.exit(-1)
        f.close

        os.remove(TEST_FILE)

    sys.exit(0)
