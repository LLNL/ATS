//
// 2019-Nov-5 Created for testing of OpenMP bothon on the host and on the device
//
#include "mpi.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <time.h>
#include <sys/time.h>
#include <sys/syscall.h>
#include <sched.h>


#if defined(HAVE_OPENMP)
#include <omp.h>
#endif


#define MY_N          500
#define MY_NSQUARED   250000
#define MY_THRESHHOLD 1000
#define MY_NITER      2         // used to run certain GPU kernels multiple times

#define MY_ABORT abort()      // uncomment if we want the code to abort if GPU tests fail
//#define MY_ABORT 

int Node_ID(char *in_hostname);
int Node_Communicator(MPI_Comm world_comm, MPI_Comm &node_comm, int &node_rank, int &node_size, char *in_hostname);
int Node_Master_Communicator(MPI_Comm world_comm, MPI_Comm &node_master_comm, int &node_master_rank, int &node_master_size, char *in_hostname);
void Begin_Mapping(int in_rank, int in_size, char *in_hostname);
void Omp_Info(int in_rank, int in_size);
void Omp_Test(int in_rank, int in_size, int in_seed1, int in_seed2, int in_seed3);
void Begin_Affinity(int in_rank, int in_size, char *in_hostname);
char *CPU_Set_To_Cstr(cpu_set_t *mask, char *str);
//void Pass_Baton(int in_rank, int in_size);

//----------------------------------------------------------------------------------------------------------------------
//
//----------------------------------------------------------------------------------------------------------------------
char *CPU_Set_To_Cstr(cpu_set_t *mask, char *str)
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

//----------------------------------------------------------------------------------------------------------------------
//
//----------------------------------------------------------------------------------------------------------------------
#if 0
void Pass_Baton(int in_rank, int in_size)
{
    // baton processing.  First rank 0, then rank 1, etc. 
    char baton[1];
    MPI_Status status;
    if (in_rank == 0)
    {
        baton[0] = (char)in_rank;
        MPI_Send(baton, 1, MPI_CHAR, in_rank+1, 88, MPI_COMM_WORLD);
        MPI_Recv(baton, 1, MPI_CHAR, in_size-1, 88, MPI_COMM_WORLD, &status); 
    }
    else if (in_rank == (in_size - 1))
    {
        MPI_Recv(baton, 1, MPI_CHAR, in_rank-1, 88, MPI_COMM_WORLD, &status);
        baton[0] = (char)in_rank;
        MPI_Send(baton, 1, MPI_CHAR, 0, 88, MPI_COMM_WORLD);
    }
    else
    {
        MPI_Recv(baton, 1, MPI_CHAR, in_rank-1, 88, MPI_COMM_WORLD, &status);
        baton[0] = (char)in_rank;
        MPI_Send(baton,  1, MPI_CHAR, in_rank+1, 88, MPI_COMM_WORLD);
    }
}
#endif


//----------------------------------------------------------------------------------------------------------------------
//
//----------------------------------------------------------------------------------------------------------------------
void Begin_Affinity(int in_rank, int in_size, char *in_hostname)
{
    int thread = 0, size_of_print_buffer = 0, num_max_threads = 1;
    cpu_set_t coremask;
    MPI_Status status;
    char clbuf[7 * CPU_SETSIZE]; 
    char *print_buffer = NULL;

#if defined HAVE_OPENMP
    num_max_threads = omp_get_max_threads();
#endif

    // Allocate char buffer into which all threads will write their data
    size_of_print_buffer = 120 *num_max_threads;
    print_buffer = (char *)calloc(size_of_print_buffer, sizeof(char));
    memset(print_buffer, '\0', size_of_print_buffer);

    // Master MPI process prints out the header
    if (in_rank == 0)
    {
        printf("    -------- MPI Rank / Thread Id / Node / Core Affinity  ------------\n");
    }

    // This threaded section is used such that each thread finds its affinity to the physical
    // core and prints a message of this info to the common buffer
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
        CPU_Set_To_Cstr(&coremask, clbuf);
        char * print_buffer_ptr = print_buffer + (thread * 120);
        snprintf(print_buffer_ptr,  120, "    MPI Rank:%4d  Thread:%4d  Node:%s  Core Affinity:%s\n", in_rank, thread, in_hostname, clbuf);
    }

    // Now, we want only mpi rank 0 to print to stdout.
    // So mpi rank 0 first writes it's data.  Then it recvs all the other ranks data and
    // writes them.  If not rank0, just send the buffer to rank 0. 
    if (in_rank != 0)
    {
        MPI_Send(print_buffer, size_of_print_buffer, MPI_CHAR, 0, 106, MPI_COMM_WORLD);
    }
    else
    {
        for (int tnum=0; tnum<num_max_threads; ++tnum)
        {
            char * print_buffer_ptr = print_buffer + (tnum * 120);
            printf("%s", print_buffer_ptr);
        }

        for (int source=1; source<in_size; ++source)
        {
            MPI_Recv(print_buffer, size_of_print_buffer, MPI_CHAR, source, 106, MPI_COMM_WORLD, &status);
            for (int tnum=0; tnum<num_max_threads; ++tnum)
            {
                char * print_buffer_ptr = print_buffer + (tnum * 120);
                printf("%s", print_buffer_ptr);
            }
        }
    }

    free(print_buffer);
    return;
}


//----------------------------------------------------------------------------------------------------------------------
//
//----------------------------------------------------------------------------------------------------------------------
int Node_ID(char *in_hostname)
{
    int  val = 0;
    int  processor_name_len;
    char processor_name[MPI_MAX_PROCESSOR_NAME];

    memset(processor_name, '\0', MPI_MAX_PROCESSOR_NAME);
    int err = MPI_Get_processor_name( processor_name, &processor_name_len );

    if (err != 0)
    {
        fprintf(stderr, "MPI_Get_processor_name returned %d", err );
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    if ( ( processor_name_len >= MPI_MAX_PROCESSOR_NAME) || ( processor_name_len <= 0) )
    {
        fprintf(stderr, "MPI_Get_processor_name returned bad strling length");
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    /* For sequential codes (built with MPI Stubs library for instance */
    val = 1;

    /* the following strips node num from names like ilx3 and updates output*/
    for (size_t ndx = 0; ndx < strlen(processor_name); ndx++)
    {
        if (isdigit(processor_name[ndx]))
        {
            val = atoi(&processor_name[ndx]);
            ndx = strlen(processor_name);
            break;
        }
    }
    return val;
}


//----------------------------------------------------------------------------------------------------------------------
//
//----------------------------------------------------------------------------------------------------------------------
int Node_Communicator(MPI_Comm world_comm, MPI_Comm &node_comm, int &node_rank, int &node_size, char *in_hostname)
{
    int nodeid = Node_ID(in_hostname);

    MPI_Comm_split(world_comm, nodeid, 0, &node_comm);
    MPI_Comm_rank (node_comm, &node_rank);
    MPI_Comm_size (node_comm, &node_size);

    return 0;
}

//----------------------------------------------------------------------------------------------------------------------
//
//----------------------------------------------------------------------------------------------------------------------
int Node_Master_Communicator(MPI_Comm world_comm, MPI_Comm &node_master_comm, int &node_master_rank, 
    int &node_master_size, char *in_hostname)
{
    int is_leader;
    int node_rank, node_size;
    MPI_Comm node_comm;

    node_master_comm = MPI_COMM_NULL;
    Node_Communicator(world_comm, node_comm, node_rank, node_size, in_hostname);

    is_leader = (node_rank == 0) ? 1 : MPI_UNDEFINED;
    MPI_Comm_split(world_comm, is_leader, 0, &node_master_comm);

    if (node_master_comm != MPI_COMM_NULL)
    {
        MPI_Comm_rank(node_master_comm, &node_master_rank);
        MPI_Comm_size(node_master_comm, &node_master_size);
    }
    else
    {
        node_master_rank = -1;
        node_master_size = -1;
    }
    return 0;
}



//----------------------------------------------------------------------------------------------------------------------
//
//----------------------------------------------------------------------------------------------------------------------
void Begin_Mapping(int in_rank, int in_size, char *in_hostname)
{
    // -------------------------------------------------------------------------------------------------------------
    // Get the hardware node id, print mapping of world mpi ids to physical hardware nodes
    // -------------------------------------------------------------------------------------------------------------
    int  nodeid, *nodeids = NULL;

    nodeids = (int *)calloc(in_size, sizeof(int));

    nodeid = Node_ID(in_hostname);

    MPI_Allgather(&nodeid, 1, MPI_INT, nodeids, 1, MPI_INT, MPI_COMM_WORLD);

    if (in_rank == 0)
    {
         printf("    -------- Inter-Node (World) MPI Communicator Info ------------\n");
         for(int ndx = 0; ndx < in_size; ndx++)
         {
             printf("    World Rank:%4d  Node Number:%4d  \n", ndx, nodeids[ndx]);
         }
         printf("\n");
    }
    MPI_Barrier(MPI_COMM_WORLD);

    free(nodeids);

    // -------------------------------------------------------------------------------------------------------------
    // Get the on-node (intranode) communicators and print
    // -------------------------------------------------------------------------------------------------------------
    MPI_Barrier(MPI_COMM_WORLD);
    MPI_Comm node_comm;
    MPI_Status status;
    int node_rank, node_size;
    char buffer[256];
    Node_Communicator(MPI_COMM_WORLD, node_comm, node_rank, node_size, in_hostname);

    // At this point, a lazy programmer would just call print and let each MPI process print
    // its info.  But this makes it harder for a user to read as the messages get mixed up on
    // screen.  So instead, each mpi process will snprintf to a buffer, 
    // send the buffer to the master, and let the master print the buffers in order.
    snprintf(buffer, 255, "    Node Rank:%4d of %4d  Node Name:%s  World Rank %4d of %4d \n",
        node_rank, node_size, in_hostname, in_rank, in_size);

    if (in_rank != 0)
    {
        MPI_Send(buffer, strlen(buffer)+1, MPI_CHAR, 0, 96, MPI_COMM_WORLD);
    }
    else
    {
        printf("    -------- Intra-Node (On Node) MPI Communicator Info ------------\n");
        printf("%s",buffer);

        for (int source=1; source<in_size; source++)
        {
            MPI_Recv(buffer, 256, MPI_CHAR, source, 96, MPI_COMM_WORLD, &status);
            printf("%s", buffer);
        }
        printf("\n");
    }

    MPI_Barrier(MPI_COMM_WORLD);

    // -------------------------------------------------------------------------------------------------------------
    // Get Node Master communicators and print
    // -------------------------------------------------------------------------------------------------------------
    MPI_Barrier(MPI_COMM_WORLD);
    MPI_Comm node_master_comm;
    int node_master_rank, node_master_size;
    Node_Master_Communicator(MPI_COMM_WORLD, node_master_comm, node_master_rank, node_master_size, in_hostname);

    // At this point, only the subset of MPI Proceses which are node masters will do work
    // the node_master_comm will be MPI_COMM_NULL for MPI processes not in this communicator
    if (node_master_comm != MPI_COMM_NULL)
    {
        snprintf(buffer, 255, "    Node Master Rank:%4d of %4d  Node Name:%s  World Rank %4d of %d Node Rank %4d of %d\n",
            node_master_rank, node_master_size, in_hostname, in_rank, in_size, node_rank, node_size);

        if (node_master_rank != 0)
        {
            MPI_Send(buffer, strlen(buffer)+1, MPI_CHAR, 0, 106, node_master_comm);
        }
        else
        {
            printf("    -------- Inter-Node (Node Master) MPI Communicator Info ------------\n");
            printf("%s",buffer);

             for (int source=1; source<node_master_size; source++)
            {
                MPI_Recv(buffer, 256, MPI_CHAR, source, 106, node_master_comm, &status);
                printf("%s", buffer);
            }
            printf("\n");
        }
    }
    MPI_Barrier(MPI_COMM_WORLD);

    if (node_master_comm != MPI_COMM_NULL) { MPI_Comm_free(&node_master_comm); }
    MPI_Comm_free(&node_comm);
}


//----------------------------------------------------------------------------------------------------------------------
//
//----------------------------------------------------------------------------------------------------------------------
void Omp_Info(int in_rank, int in_size)
{
#if defined HAVE_OPENMP
    int num_max_threads = omp_get_max_threads();
    if (in_rank == 0) {
        printf("\n\n    OpenMP Cores                   : Detects %d Max OpenMP Threads\n",num_max_threads);
    }

#if defined HAVE_OPENMP_4
    int num_gpus = omp_get_num_devices();
    int default_device = omp_get_default_device();

    if (in_rank == 0) {
        printf("    OpenMP GPU Test                : Detects %d GPU devices\n",num_gpus);
        printf("    OpenMP GPU Test                : Default device = %d\n",default_device);
    }

    if ((num_gpus > 1) && (default_device == 0)) { omp_set_default_device(default_device + 1);  }

    default_device = omp_get_default_device();

    if (in_rank == 0) {
        printf("    OpenMP GPU Test                : Set Default device = %d\n",default_device);
    }
#endif

    MPI_Barrier(MPI_COMM_WORLD);
#endif
}


//----------------------------------------------------------------------------------------------------------------------
//
//----------------------------------------------------------------------------------------------------------------------
void Omp_Test(int in_rank, int in_size, int in_seed1, int in_seed2, int in_seed3)
{
#if defined(HAVE_OPENMP)

    // Have only msater rank do the work for now
    if (in_rank != 0) { return; }

    double *awork = (double *) calloc(MY_N * MY_N, sizeof(double));
    double *bwork = (double *) calloc(MY_N * MY_N, sizeof(double));
    double *cwork = (double *) calloc(MY_N * MY_N, sizeof(double));
    double *dwork = (double *) calloc(MY_N * MY_N, sizeof(double));
    double *ework = (double *) calloc(MY_N * MY_N, sizeof(double));
    double *fwork = (double *) calloc(MY_N * MY_N, sizeof(double));
    double  time_start, time_stop, serial_value;

    // used to randomize work -- don't want it optimized out
    srand ( time(NULL) );
    int seed1 = (rand()%10);
    int seed2 = (rand()%100);
    int seed3 = (rand()%200);

    // Allow user input to bypass the random setting
    if (in_seed1 > 0) { seed1 = in_seed1; }
    if (in_seed2 > 0) { seed2 = in_seed2; }
    if (in_seed3 > 0) { seed3 = in_seed3; }

    printf("    OpenMP Tests                   : seed1=%d seed2=%d seed3=%d\n",seed1,seed2,seed3);
    printf("    OpenMP Tests                   : Will perform %d iterations of each OpenMP test\n",MY_NITER);
    printf("    OpenMP Host MM Test            : omp parallel over outer loop\n");

#if defined HAVE_OPENMP_4
    printf("    OpenMP GPU MM Test No Collapse : omp target teams without a collapse option\n");
    printf("    OpenMP GPU MM Test Collapse    : omp target teams with    a collapse option\n");
#endif

    // ---------------------------------------------------------------------------------------------------------
    // Initialize the matrixes
    // ---------------------------------------------------------------------------------------------------------
    for(int i=0;i<MY_N;i++)
    {
        for(int j=0;j<MY_N;j++)
        {
            awork[(i * MY_N) + j] = (double)(i+seed2) * ((double)(j+seed3));
            bwork[(i * MY_N) + j] = (double)(j+seed1) * ((double)(i+seed3));
            cwork[(i * MY_N) + j] = 0.0;
        }
    }

    // randomness to flumux the optimizer
    if ((seed2 * seed3) == 2574) { for (int i=0; i<10; ++i) { fprintf(stderr,"DEBUG 101 awork[%i] = %e bwork[%i]=%e cwork[%i]=%e\n",i,awork[i],i,bwork[i],i,cwork[i]); } }

    // ---------------------------------------------------------------------------------------------------------
    // Serial  Matrix Computations
    // rzmanta: bsub -x -n 1  -Is -W 240 -G guests /usr/bin/bash
    // rzmanta: mpirun -np 1 ./executable Input.inp  -debug_gpu
    // ---------------------------------------------------------------------------------------------------------
    time_start = omp_get_wtime();
    for(int i=0;i<MY_N;i++)
    {
        for(int j=0;j<MY_N;j++)
        {
            for(int m=0;m<MY_N;m++)
            {
                cwork[(i * MY_N) + j] = awork[(i * MY_N) + j] + bwork[(i * MY_N) + j] ;
                cwork[(i * MY_N) + j] = cwork[(i * MY_N) + j] * (m+1) ;
                for(int n=0;n<seed2;n++)
                {
                   cwork[(i * MY_N) + j] = cwork[(i * MY_N) + j] + ((n+m) * seed1)  ;
                }
            }
        }
    }
    time_stop = omp_get_wtime();

    // randomness to flumux the optimizer
    if ((seed2 * seed3) == 2574) { for (int i=0; i<10; ++i) { fprintf(stderr,"DEBUG 102 awork[%i] = %e bwork[%i]=%e cwork[%i]=%e\n",i,awork[i],i,bwork[i],i,cwork[i]); } }

    serial_value = cwork[seed3]; // save one expected value
    printf("    OpenMP Serial MM Test          : %5.3f seconds - Serial Matrix Multiply expected answer = %e \n",
        time_stop - time_start,serial_value);

    // ---------------------------------------------------------------------------------------------------------
    // Multi-Core (Host) OpenMP  Matrix Computations
    // ---------------------------------------------------------------------------------------------------------
    for (int iter=0; iter<MY_NITER; iter++)
    {
        for(int i=0;i<MY_N;i++) { for(int j=0;j<MY_N;j++) { dwork[(i * MY_N) + j] = 0.0; } } // zero out result array
        dwork[seed3] = seed2 * seed1; // nonsense value to check that it is recalculated correctly.
        time_start = omp_get_wtime();

        #pragma omp parallel for
        for(int i=0;i<MY_N;i++)
        {
            for(int j=0;j<MY_N;j++)
            {
                for(int m=0;m<MY_N;m++)
                {
                    dwork[(i * MY_N) + j] = awork[(i * MY_N) + j] + bwork[(i * MY_N) + j] ;
                    dwork[(i * MY_N) + j] = dwork[(i * MY_N) + j] * (m+1) ;
                    for(int n=0;n<seed2;n++)
                    {
                       dwork[(i * MY_N) + j] = dwork[(i * MY_N) + j] + ((n+m) * seed1) ;
                    }
                }
            }
        }
        time_stop = omp_get_wtime();
        printf("    OpenMP Host MM Test            : %5.3f seconds - OpenMP Multi-Core Matrix Multiply. Does %e=%e ?\n",
            time_stop - time_start, dwork[seed3],serial_value);
        if (serial_value != dwork[seed3])
        {
            printf("    OpenMP Host MM Test            : ERROR: OpenMP Host MM Test failed!\n");
            MY_ABORT;
        }

        // randomness to flumux the optimizer
        if ((seed2 * seed3) == 2574) { for (int i=0; i<10; ++i) { fprintf(stderr,"DEBUG 103 awork[%i] = %e bwork[%i]=%e dwork[%i]=%e\n",i,awork[i],i,bwork[i],i,dwork[i]); } }
    }


    // ---------------------------------------------------------------------------------------------------------
    // GPU using map clause Matrix Computations without collapse
    // ---------------------------------------------------------------------------------------------------------
#if defined HAVE_OPENMP_4
    for (int iter=0; iter<MY_NITER; iter++)
    {
        for(int i=0;i<MY_N;i++) { for(int j=0;j<MY_N;j++) { fwork[(i * MY_N) + j] = 0.0; } } // zero out result array
        fwork[seed3] = seed2 * seed1; // nonsense value to check that it is recalculated correctly.

        time_start = omp_get_wtime();
        #pragma omp target data map(to:awork[0:MY_NSQUARED], bwork[0:MY_NSQUARED]) map(tofrom: fwork[0:MY_NSQUARED])
        {
            #pragma omp target teams distribute parallel for thread_limit(64)
            for(int i=0;i<MY_N;i++)
            {
                for(int j=0;j<MY_N;j++)
                {
                    for(int m=0;m<MY_N;m++)
                    {
                        fwork[(i * MY_N) + j] = awork[(i * MY_N) + j] + bwork[(i * MY_N) + j] ;
                        fwork[(i * MY_N) + j] = fwork[(i * MY_N) + j] * (m+1) ;
                        for(int n=0;n<seed2;n++)
                        {
                           fwork[(i * MY_N) + j] = fwork[(i * MY_N) + j] + ((n+m) * seed1) ;
                        }
                    }
                }
            }
        }
        time_stop = omp_get_wtime();
        printf("    OpenMP GPU MM Test No Collapse : %5.3f seconds - GPU Device Matrix Multiply. Does %e=%e ?\n",
            time_stop - time_start, fwork[seed3], serial_value);

        if (serial_value != fwork[seed3])
        {
            printf("    OpenMP GPU MM Test No Collapse : ERROR: OpenMP GPU MM Test 1 failed! %e != %e \n", serial_value, fwork[seed3]);
            MY_ABORT;
        }

        // randomness to flumux the optimizer
        if ((seed2 * seed3) == 2574) { for (int i=0; i<10; ++i) { fprintf(stderr,"DEBUG 103 awork[%i] = %e bwork[%i]=%e fwork[%i]=%e\n",i,awork[i],i,bwork[i],i,fwork[i]); } }
    }

    // ---------------------------------------------------------------------------------------------------------
    // GPU using map clause Matrix Computations with collapse clause
    // ---------------------------------------------------------------------------------------------------------
    for (int iter=0; iter<MY_NITER; iter++)
    {
        for(int i=0;i<MY_N;i++) { for(int j=0;j<MY_N;j++) { ework[(i * MY_N) + j] = 0.0; } } // zero out result array
        ework[seed3] = seed2 * seed1; // nonsense value to check that it is recalculated correctly.
        time_start = omp_get_wtime();
        //sleep(1);
        #pragma omp target data map(to:awork[0:MY_NSQUARED], bwork[0:MY_NSQUARED]) map(tofrom: ework[0:MY_NSQUARED])
        {
            #pragma omp target teams distribute parallel for collapse(2) thread_limit(64)
            for(int i=0;i<MY_N;i++)
            {
                for(int j=0;j<MY_N;j++)
                {
                    for(int m=0;m<MY_N;m++)
                    {
                        ework[(i * MY_N) + j] = awork[(i * MY_N) + j] + bwork[(i * MY_N) + j] ;
                        ework[(i * MY_N) + j] = ework[(i * MY_N) + j] * (m+1) ;
                        for(int n=0;n<seed2;n++)
                        {
                           ework[(i * MY_N) + j] = ework[(i * MY_N) + j] + ((n+m) * seed1) ;
                        }
                    }
                }
            }
        }
        time_stop = omp_get_wtime();
        printf("    OpenMP GPU MM Test Collapse    : %5.3f seconds - GPU Device Matrix Multiply. Does %e=%e ?\n",
            time_stop - time_start, ework[seed3], serial_value);

        if (serial_value != ework[seed3])
        {
            printf("    OpenMP GPU MM Collapse   : ERROR: OpenMP GPU MM Test 2 failed! %e != %e \n", serial_value, ework[seed3]);
            MY_ABORT;
        }

        // randomness to flumux the optimizer
        if ((seed2 * seed3) == 2574) { for (int i=0; i<10; ++i) { fprintf(stderr,"DEBUG 103 awork[%i] = %e bwork[%i]=%e ework[%i]=%e\n",i,awork[i],i,bwork[i],i,ework[i]); } }
    }

    free(awork);
    free(bwork);
    free(cwork);
    free(dwork);
    free(ework);
    free(fwork);

#endif  // end HAVE_OPENMP_4
#endif  // end HAVE_OPENMP

    return;
}


//----------------------------------------------------------------------------------------------------------------------
//
//----------------------------------------------------------------------------------------------------------------------

int main (int argc, char *argv[]) {
    int  my_rank=0, my_size=0, sz, argndx, my_seed1=0, my_seed2=0, my_seed3=0;
    char hostname[MPI_MAX_PROCESSOR_NAME]="UNKNOWN";
    char buffer[128];
    char arg_string[1024];

    // If arguments are given, the will be for the seeds.  They are optional.  There are up to three seeds
    // This is a bit of hidden feature, used to test ATS. It bypasses the use of the random function to generate the seeds
    //  It is not advertised and there is no error checking
    if (argc > 1) { my_seed1 = atoi(argv[1]); }
    if (argc > 2) { my_seed2 = atoi(argv[2]); }
    if (argc > 3) { my_seed3 = atoi(argv[3]); }

    memset(buffer,'\0',128);
    snprintf(buffer,127,"MPI Version %d.%d ",MPI_VERSION,MPI_SUBVERSION);

    MPI_Init(&argc, &argv);

    MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &my_size);
    MPI_Get_processor_name(hostname, &sz);

    Begin_Mapping(my_rank, my_size, hostname);
    Begin_Affinity(my_rank, my_size, hostname);

    MPI_Barrier(MPI_COMM_WORLD);
    Omp_Info(my_rank, my_size);
    Omp_Test(my_rank, my_size, my_seed1, my_seed2, my_seed3);

    MPI_Barrier(MPI_COMM_WORLD);
    MPI_Finalize();

    if ((my_size % 2) == 0) { exit(0); }    // If run with an even number of nodes, exit with 0

    exit(-1);   // if run with odd number of nodes exit with -1
}

//----------------------------------------------------------------------------------------------------------------------
// end of file
//----------------------------------------------------------------------------------------------------------------------
