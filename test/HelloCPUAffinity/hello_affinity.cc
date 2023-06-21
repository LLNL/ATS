//----------------------------------------------------------------------------------------------------------------------
// 2019-Jun-24
//
// SAD = Shawn Dawson
// SAD example of coing to print MPI and Core affinty.
//
// Sample Compile Lines:
//
// RZGenie: mpic++     -g -O1 -qopenmp -pthread  -DHAVE_OPENMP hello_affinity.cc
// RZAnsel: mpiclang++ -g -O1 -fopenmp -lpthread -DHAVE_OPENMP hello_affinity.cc
// RZAnsel: mpig++     -g -O1 -fopenmp -lpthread -DHAVE_OPENMP hello_affinity.cc
// RZAnsel: mpixlC     -g -O1 -qsmp=omp:noopt -lpthread -DHAVE_OPENMP hello_affinity.cc
//
// Sample Run Lines showing different affinities
//
// OpenMP env setting which impact thread affinity (set them as you will to see how it impacts thread affinity)
//
// export OMP_DISPLAY_ENV=False     True|False  (set to True, to show actual OMP settings)
// export OMP_NUM_THREADS=4
// export OMP_PROC_BIND=True        True|False|Master|Close|Sprea
// export OMP_PLACES=core           threas|cores|sockets or a specific list
//
// An of course, one can run under the LLNL mpibind program or use the srun option to run to achieve this.
//
// RZGenie:
//
// srun -N4-4 -n 8 ./a.out | sort
//
// RZAnsel (lots more run variations possible with lrun or jsrun)
//
// lrun -N4-4 -n 4               ./a.out | sort
// lrun -N4-4 -n 4 --mpibind=off ./a.out | sort
//
//----------------------------------------------------------------------------------------------------------------------

#define HAVE_SYSCALL_H
#define HAVE_SCHED_H

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <sys/types.h>
#include <unistd.h>
#include <time.h>
#include <mpi.h>

#ifdef HAVE_OPENMP
#include <omp.h>
#endif

#if defined(HAVE_SYSCALL_H) && defined(HAVE_SCHED_H)
#include <sys/syscall.h>
#include <sched.h>
static char *SAD_cpuset_to_cstr(cpu_set_t *mask, char *str);
#endif

static void SAD_Core_Affinity(void);

//----------------------------------------------------------------------------------------------------------------------
//  2019-06-24 SAD  Borrowe from util-linux-2.13-pre7/schedutils/taskset.c
//                  returns string with core affinity.
//----------------------------------------------------------------------------------------------------------------------
#if defined(HAVE_SYSCALL_H) && defined(HAVE_SCHED_H)

static char *SAD_cpuset_to_cstr(cpu_set_t *mask, char *str)
{
    char *ptr = str;
    int i, j, entry_made = 0;
    for (i = 0; i < CPU_SETSIZE; i++)
    {
        if (CPU_ISSET(i, mask))
        {
            int run = 0;
            entry_made = 1;
            for (j = i + 1; j < CPU_SETSIZE; j++)
            {
                if (CPU_ISSET(j, mask)) { run++; } else { break; }
            }
            if (!run)
            {
                sprintf(ptr, "%d,", i);
            }
            else if (run == 1)
            {
               sprintf(ptr, "%d,%d,", i, i + 1);
                i++;
            }
            else
            {
                sprintf(ptr, "%d-%d,", i, i + run);
                i += run;
            }
            while (*ptr != 0) { ptr++; }
        }
    }
    ptr -= entry_made;
    *ptr = 0;
    return(str);
}
#endif

//----------------------------------------------------------------------------------------------------------------------
//  2019-06-24 SAD  Prints core affinty by rank/thread

//----------------------------------------------------------------------------------------------------------------------
static void SAD_Core_Affinity(void)
{
#if defined(HAVE_SYSCALL_H) && defined(HAVE_SCHED_H)
    int world_rank, thread, hostname_sz;
    cpu_set_t coremask;
    char clbuf[7 * CPU_SETSIZE], hostname[MPI_MAX_PROCESSOR_NAME]="UNKNOWN";

    MPI_Barrier(MPI_COMM_WORLD);

    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);
    MPI_Get_processor_name(hostname, &hostname_sz);
    if (world_rank == 0)
    {
        printf("    -------- MPI Rank / Thread Id / Node / Core Affinity  ------------\n");
    }
    fflush(stdout);
    MPI_Barrier(MPI_COMM_WORLD);

    memset(clbuf, 0, sizeof(clbuf));
    #ifdef HAVE_OPENMP
    #pragma omp parallel private(thread, coremask, clbuf)
    #endif
    {
        #ifdef HAVE_OPENMP
        thread = omp_get_thread_num();
        #else
        thread = 0;
        #endif
        (void)sched_getaffinity(0, sizeof(coremask), &coremask);
        SAD_cpuset_to_cstr(&coremask, clbuf);
        #ifdef HAVE_OPENMP
        #pragma omp barrier
        #endif
        printf("    MPI Rank:%4d  Thread:%4d  Node:%s  Core Affinity:%2s\n", world_rank, thread, hostname, clbuf);
    }
    MPI_Barrier(MPI_COMM_WORLD);
    fflush(stdout);
#endif
    return;
}


//----------------------------------------------------------------------------------------------------------------------
//  2019-06-24 SAD  Sample main to print Core affinity
//----------------------------------------------------------------------------------------------------------------------
int main(int argc, char **argv)
{
    int my_rank, my_num_mpi, sleep_seconds = 0;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &my_num_mpi);

    // Optional seconds to sleep as an input argument
    if (argc > 1)
    {
       sleep_seconds = atoi(argv[1]); 
    }

    time_t my_time = time(NULL);
    if (my_rank == 0)
    {
        printf("START TIME %s", ctime(&my_time));
    }

    SAD_Core_Affinity();

    if (sleep_seconds > 0)
    {
        if (my_rank == 0)
        {
            printf("Going to sleep %i seconds\n", sleep_seconds);
            fflush(stdout);
        }

        sleep(sleep_seconds);

        MPI_Barrier(MPI_COMM_WORLD);

       if (my_rank == 0) { printf("Waking up\n"); }
    }

    if (my_rank == 0) { printf("Good-night Gracie.\n"); }

    my_time = time(NULL);
    if (my_rank == 0)
    {
        printf("STOP  TIME %s", ctime(&my_time));
    }

    return(0);
}

//----------------------------------------------------------------------------------------------------------------------
// End Of File
//----------------------------------------------------------------------------------------------------------------------
