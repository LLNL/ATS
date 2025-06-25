// ----------------------------------------------------------------------------------------
//
// This source includes a simple makefile.  Refer to READ.ME.
// 
// ----------------------------------------------------------------------------------------
#include <stdlib.h>
#include <stdio.h>
#include <stddef.h>
#include <string.h>
#include <stdint.h>
#include <sys/types.h>
#include <assert.h>
#include <unistd.h>
#include <sched.h>
#include <time.h>
#include <mpi.h>
#include "gputest_this.hh"

// ----------------------------------------------------------------------------------------
// Prototypes
// ----------------------------------------------------------------------------------------
static void Call_Cuda_Hello_Method1(int mpi_rank, int some_user_number);
#if 0
static void Call_Cuda_Hello_Method2(int mpi_rank);
#endif
static void MC_Core_Affinity(int mpi_rank, int mpi_size, int *node_num);
static char *MC_cpuset_to_cstr(cpu_set_t *mask, char *str);

template <typename Function> __global__ void SAD_operatorLaunch(Function lambda, int unused)
{
    lambda(unused);
}

// ----------------------------------------------------------------------------------------
//
// ----------------------------------------------------------------------------------------
__global__ void Cuda_Hello_Global(char *a, int *b, int some_user_number)
{
    a[threadIdx.x] += b[threadIdx.x];
}
// ----------------------------------------------------------------------------------------
// host routines
// ----------------------------------------------------------------------------------------
static void Call_Cuda_Hello_Method1(int mpi_rank,  int some_user_number)
{
    const int N = 16;
    const int blocksize = 16;

    // Array a has "Hello"
    // Array b has an array of ints, which will be added to array a to 
    // create the string "World"
    // Ascii H + 15 = W
    // Ascii e + 10 = o
    // etc.
    //
    // Both arrays are passed to the GPU kernel to do the work.
    //
    // Array a with the updated string is passed back from the device and
    // is then printed.
    // 
    char a[N] = "Hello \0\0\0\0\0\0";
    int b[N] = {15, 10, 6, 0, -11, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};

    char *ad;
    int *bd;
    const int csize = N*sizeof(char);
    const int isize = N*sizeof(int);

    if (mpi_rank == 0)
    {
        fprintf(stdout,"\n    -------- Cuda Hello World Global Test Begin --------\n");
        fprintf(stdout,"    %s", a); // This will print Hello
        fprintf(stdout,"\n");
    }

    SADGPU_MALLOC( (void**)&ad, csize );
    SADGPU_MALLOC( (void**)&bd, isize );
    SADGPU_MEMCPY(ad, a, csize, SADGPU_MEMCPY_HOST_TO_DEVICE );
    SADGPU_MEMCPY(bd, b, isize, SADGPU_MEMCPY_HOST_TO_DEVICE );

    dim3 dimBlock( blocksize, 1 );
    dim3 dimGrid( 1, 1 );

    SADGPU_PEEK_AT_LAST_ERROR();

    Cuda_Hello_Global<<<dimGrid, dimBlock>>>(ad, bd, some_user_number);

    SADGPU_PEEK_AT_LAST_ERROR();

    SADGPU_MEMCPY(a, ad, csize, SADGPU_MEMCPY_DEVICE_TO_HOST );
    SADGPU_FREE(ad);
    SADGPU_FREE(bd);

    if ( strcmp(a, "World!") != 0 )
    {
        printf("%s\n", a);
        fflush(stdout);
        printf("kernel launch gave the wrong answer\n");
        abort();
    }

    if (mpi_rank == 0)
    {
        fprintf(stdout, "    %s\n", a); // This will print World
        fprintf(stdout, "    -------- Cuda Hello World Global Test End   --------\n");
    }
}


// ----------------------------------------------------------------------------------------
// host routines
// ----------------------------------------------------------------------------------------
#if 0
Comment out for now, may be useful later, so hang onto code
static void Call_Cuda_Hello_Method2(int mpi_rank)
{
    const int N = 16;
    const int blocksize = 16;

    char a[N] = "Hello \0\0\0\0\0\0";
    int b[N] = {15, 10, 6, 0, -11, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
    // char c[N] = "012345678901234";

    char *am;
    int *bm;
    const int csize = N*sizeof(char);
    const int isize = N*sizeof(int);

    if (mpi_rank == 0)
    {
        fprintf(stdout,"\n    -------- Cuda Hello World Lambda Test Begin --------\n");
        fprintf(stdout,"    %s", a); // This will print Hello
        fprintf(stdout,"\n");
    }

    SADGPU_MALLOC_MANAGED( (void**)&am, csize );
    SADGPU_MALLOC_MANAGED( (void**)&bm, isize );

    memcpy(am, a, csize);   // Copy 'Hello' from a to am, treat managed memory like regular memory
    memcpy(bm, b, isize);   // do not use host to device memcpy, just use memcpy

    dim3 dimBlock( blocksize, 1 );
    dim3 dimGrid( 1, 1 );

    auto lambda = [=] __host__ __device__(int unused) 
    {

    #if defined (__CUDA_ARCH__) || defined (__HIP_DEVICE_COMPILE__)
        am[threadIdx.x] += bm[threadIdx.x];
    #else
        printf("ERROR should not be here, but need some sort of host code to compile __host__ __this__ with --expt-extended-lambda\n");
        printf("ERROR the host and device kernels must both capture the same arguments, or there will be a compile error\n");
        printf("I00 am=%p\n",am);
        printf("I00 bm=%p\n",bm);
        am[0] += bm[0];
    #endif
    };

    SAD_operatorLaunch<<<dimGrid, dimBlock>>>(lambda, 0);

    SADGPU_PEEK_AT_LAST_ERROR();

    SADGPU_DEVICE_SYNCRHONIZE();
    SADGPU_PEEK_AT_LAST_ERROR();


    if ( strcmp(am, "World!") != 0 )
    {
        printf("%s\n", am);
        fflush(stdout);
        printf("kernel launch gave the wrong answer\n");
        abort();
    }

    if (mpi_rank == 0)
    {
        fprintf(stdout, "    %s\n", am); // This will print World
        fprintf(stdout, "    -------- Cuda Hello World Lambda Test End   --------\n");
    }

    SADGPU_FREE(am);
    SADGPU_FREE(bm);
}
#endif

// ----------------------------------------------------------------------------------------
// main driver
// ----------------------------------------------------------------------------------------

int main(int argc, char *argv[])
{
    int my_rank = 0, my_num_mpi = 1, node_num = 0;
    const int kb = 1024;
    const int mb = kb * kb;
    char print_buf[256];
    MPI_Status status;

    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    int some_user_number = 0;
    if (argc > 1)
    {
        some_user_number = atoi(argv[1]);
    }

    // ---------------------------------
    // Initialize MPI, get rank and size
    // ---------------------------------
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &my_num_mpi);

    time_t my_time = time(NULL);
    if (my_rank == 0)
    {
        printf("START TIME %s", ctime(&my_time));
    }

    // ---------------------------------
    // Print compiler information
    // ---------------------------------
    if (my_rank == 0)
    {
        printf("\n    -------- Compiler Versions ------------\n");

#if defined (__clang__)
        printf("    Clang Version     = %i.%i.%i \n",__clang_major__,__clang_minor__,__clang_patchlevel__);
#endif

#if defined(CUDART_VERSION)
        printf("    CUDART_VERSION    = %i\n",CUDART_VERSION);
#endif

#if defined(HIP_VERSION)
        printf("    HIP_VERSION       = %i\n",HIP_VERSION);
        printf("    HIP_VERSION_MAJOR = %i\n",HIP_VERSION_MAJOR);
        printf("    HIP_VERSION_MINOR = %i\n",HIP_VERSION_MINOR);
        printf("    HIP_VERSION_PATCH = %i\n\n",HIP_VERSION_PATCH);
#endif
        printf("\n");
    }

    // ----------------------------------------------------------------------
    // Call routine to print cpu core affinity
    // ----------------------------------------------------------------------
    MC_Core_Affinity(my_rank, my_num_mpi, &node_num);

    // ----------------------------------------------------------------------
    // Print GPU device information
    // ----------------------------------------------------------------------
    SADGPU_DEVICE_RESET();
    int deviceCount = 0; 
    SADGPU_GET_DEVICE_COUNT(&deviceCount);

        // Print the number of GPUs seen by the MPI ranks.
        // Create a unique number for the hardware identifier in the uuid property 
        // for the GPU device. This is a char array of 16, but is not printable,
        // so simply convert each byte to an unsigned long long and add the
        // 16 numbers together to get a unique identifier we can use.

    memset(print_buf, '\0', 256);
    snprintf(print_buf, 255, "    MPI Rank %i sees %i GPU devices with these physical gpu identifiers: ",my_rank,deviceCount);

    for(int device_ndx = 0; device_ndx < deviceCount; ++device_ndx)
    {
        SADGPU_DEVICE_PROP props;
        SADGPU_GET_DEVICE_PROPERTIES(&props, device_ndx);

        // The PCI Bus ID string is typically in the format "domain:bus:device.function" (e.g., "0000:03:00.0").
        char pcibus_id[32], small_buf[32];
        memset(pcibus_id, 0, 32);
        memset(small_buf, 0, 32);
        SADGPU_GET_DEVICE_PCI_BUS_ID(pcibus_id, sizeof(pcibus_id), device_ndx)
        snprintf(small_buf, 31, "%i-%s ", node_num, pcibus_id);
        strcat(print_buf, small_buf);
    }
    strcat(print_buf, "\n");

    if (my_rank == 0)
    {
        printf("%s\n    -------- GPU Information ------------\n","");
        printf("%s",print_buf);
        for (size_t source = 1; source<my_num_mpi; ++source)
        {
            MPI_Recv(print_buf, 256, MPI_CHAR, source, 99, MPI_COMM_WORLD, &status);
            printf("%s",print_buf);
        }
    }
    else
    {
        MPI_Send(print_buf, 256, MPI_CHAR, 0, 99, MPI_COMM_WORLD);
    }


    if ( (my_rank == 0) && (deviceCount > 0) )
    {
        SADGPU_DEVICE_PROP props;
        SADGPU_GET_DEVICE_PROPERTIES(&props, 0);
            
        printf("\n");
        printf("    Global Memory:        %lu mb\n",props.totalGlobalMem / mb);
        printf("    Shared memory:        %lu kb\n",props.sharedMemPerBlock / kb);
        printf("    Constant memory:      %lu kb\n",props.totalConstMem / kb);
        printf("    Block registers:      %i \n",props.regsPerBlock);
        printf("    Warp size:            %i \n",props.warpSize);
        printf("    Threads per block:    %i \n",props.maxThreadsPerBlock);
        printf("    Max block dimensions: [%i, %i, %i] \n", props.maxThreadsDim[0], props.maxThreadsDim[1], props.maxThreadsDim[2]);
        printf("    Max grid dimensions:  [%i, %i, %i] \n", props.maxGridSize[0],   props.maxGridSize[1],    props.maxGridSize[2]);
    }


    // ----------------------------------------------------------------------
    // 
    // ----------------------------------------------------------------------
    // Call global gpu function

    if (some_user_number > 0)  { sleep(some_user_number); }
    Call_Cuda_Hello_Method1(my_rank, some_user_number);


#if 0
Comment out for now, keep in case wanted later
    // call using Lambda and operator launch
    if (some_user_number > 0)  { sleep(some_user_number); }
    Call_Cuda_Hello_Method2(my_rank);
#endif

    my_time = time(NULL);
    if (my_rank == 0)
    {
        printf("STOP  TIME %s", ctime(&my_time));
    }

    // ----------------------------------------------------------------------
    // Shut down  MPI
    // ----------------------------------------------------------------------
    MPI_Finalize();

    return(0);
}

//----------------------------------------------------------------------------------------------------------------------
// 
//----------------------------------------------------------------------------------------------------------------------
static void MC_Core_Affinity(int world_rank, int world_size, int *node_num)
{
    int thread, hostname_sz;
    cpu_set_t coremask;
    char clbuf[7 * CPU_SETSIZE], hostname[MPI_MAX_PROCESSOR_NAME]="UNKNOWN";
    char print_buf[256]; 
    MPI_Status status;

    MPI_Get_processor_name(hostname, &hostname_sz);

    // Get the integer part of the node name. blue47 is 47 for instance.
    size_t indx2 = strcspn(hostname, "0123456789");
    *node_num = atoi(&hostname[indx2]);

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
        MC_cpuset_to_cstr(&coremask, clbuf);
        #ifdef HAVE_OPENMP
        #pragma omp barrier
        #endif
        print_buf[255] = '\0';
        snprintf(print_buf, 255, "%s    MPI Rank:%04d  Thread:%04d  Node:%12s  Core Affinity:%3s\n",
            "",world_rank, thread, hostname, clbuf);
    }

    if (world_rank == 0)
    {
        printf("    -------- MPI Rank / Thread Id / Node / Core Affinity  ------------\n");
        printf("    %i MPI Ranks\n", world_size);
        printf("%s",print_buf);
        for (size_t source = 1; source<world_size; ++source)
        {
            MPI_Recv(print_buf, 256, MPI_CHAR, source, 99, MPI_COMM_WORLD, &status);
            printf("%s",print_buf);
        }
    }
    else
    {
        MPI_Send(print_buf, 256, MPI_CHAR, 0, 99, MPI_COMM_WORLD);
    }

    return;
}

//----------------------------------------------------------------------------------------------------------------------
//  2019-06-24 SAD  Borrowed from util-linux-2.13-pre7/schedutils/taskset.c
//                  returns string with core affinity.
//----------------------------------------------------------------------------------------------------------------------
static char *MC_cpuset_to_cstr(cpu_set_t *mask, char *str)
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





// ----------------------------------------------------------------------------------------
// End of File
// ----------------------------------------------------------------------------------------
