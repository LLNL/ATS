//
// 2016-Aug-30 Created as an ATS example for projects to test out
//
// Compile with your favoirt mpi C compiler wrapper 
//
// Simple test program to demonstrate light weight use of ATS with a code.
//
// MPI parallel program which 
//
// Prints FAILURE if run with 4 MPI processe -- yet exits with 0 status.
// Prints SUCCESS for all other runs.
// Exits with 0 status for all runs with an even number of processes.
// Exits with -1 status for all runs with an odd number of processes.
//
// Prints out the argument list so that users can ensure they have setup
// the ATS file correctly to vary the arguments per test case
// 
// This will be able to demonstrate that ATS inspects both the return value
// and an arbitrary string (SUCCESS/FAILURE for this test code) printed
// to stdout when determining if a code run is successul or not
//
// The following table gives some results
//
// num
// mpi    stdout  exit
// ranks  message code
// 1      SUCCESS -1
// 2      SUCCESS  0
// 3      SUCCESS -1
// 4      FAILURE  0 
// 5      SUCCESS -1
// 6      SUCCESS  0
// 7      SUCCESS -1
// 8      SUCCESS  0
//
#include "mpi.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main (int argc, char *argv[]) {
    int  my_rank=0, my_size=0, sz, argndx;
    char hostname[MPI_MAX_PROCESSOR_NAME]="UNKNOWN";
    char buffer[128];
    char arg_string[1024];

    memset(buffer,'\0',128);
    snprintf(buffer,127,"MPI Version %d.%d ",MPI_VERSION,MPI_SUBVERSION);

    MPI_Init(&argc, &argv);

    MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &my_size);
    MPI_Get_processor_name(hostname, &sz);

    if (my_rank == 0) {

        memset(arg_string, '\0', 1024);
        for (argndx=1; argndx<argc; argndx++) {
            if ( strlen(argv[argndx]) < 1020 - strlen(arg_string) ) {
                strcat(arg_string, argv[argndx]);
                strcat(arg_string, " ");
            }
        }

        printf("Hello ATS: There are %d MPI ranks running -- MPI Version is %s -- Argument list is %s\n", my_size,  buffer, arg_string);
    }
    MPI_Barrier(MPI_COMM_WORLD);

    printf("MPI Rank %d is on node %s\n", my_rank, hostname);

    MPI_Barrier(MPI_COMM_WORLD);
    if (my_rank == 0) {
        if (my_size == 4) { printf("FAILURE\n"); } // when run with 4 mpi processes this test will print FAILURE, but still return 0
        else              { printf("SUCCESS\n"); } // print SUCCESS any other time
    }
    MPI_Finalize();

    if ((my_size % 2) == 0) { exit(0); }    // If run with an even number of nodes, exit with 0

    exit(-1);   // if run with odd number of nodes exit with -1
}

// end of file
