#include "mpi.h"
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <sched.h>
#include <omp.h>

/* Borrowed from util-linux-2.13-pre7/schedutils/taskset.c */
static char *cpuset_to_cstr(cpu_set_t *mask, char *str)
{
  char *ptr = str;
  int i, j, entry_made = 0;
  for (i = 0; i < CPU_SETSIZE; i++) {
    if (CPU_ISSET(i, mask)) {
      int run = 0;
      entry_made = 1;
      for (j = i + 1; j < CPU_SETSIZE; j++) {
        if (CPU_ISSET(j, mask)) run++;
        else break;
      }
      if (!run)
        sprintf(ptr, "%03d,", i);
      else if (run == 1) {
        sprintf(ptr, "%03d,%03d,", i, i + 1);
        i++;
      } else {
        sprintf(ptr, "%03d-%03d,", i, i + run);
        i += run;
      }
      while (*ptr != 0) ptr++;
    }
  }
  ptr -= entry_made;
  *ptr = 0;
  return(str);
}


int main( int argc, char *argv[])
{
  int  my_rank=0, my_size=0, sz, argndx;
  char hostname[MPI_MAX_PROCESSOR_NAME]="UNKNOWN";
  char buffer[128];
  char arg_string[1024];
  int thread;
  cpu_set_t coremask;
  char clbuf[7 * CPU_SETSIZE], hnbuf[64];

  memset(clbuf, 0, sizeof(clbuf));
  memset(hnbuf, 0, sizeof(hnbuf));

  if (argc < 2)
  {
    printf("(%i)Proper usage is: ./omp_test <unique_int_identifier> <int_seconds_to_sleep>\n",argc);
    exit(-1);
  }

  int unique_identifier = atoi(argv[1]);
  int seconds = atoi(argv[2]);

  (void)gethostname(hnbuf, sizeof(hnbuf));
    
  memset(buffer,'\0',128);
  snprintf(buffer,127,"MPI Version %d.%d ",MPI_VERSION,MPI_SUBVERSION);

  MPI_Init(&argc, &argv);

  MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
  MPI_Comm_size(MPI_COMM_WORLD, &my_size);
  MPI_Get_processor_name(hostname, &sz);

#pragma omp parallel private(thread, coremask, clbuf)
  {
    // #pragma omp master
    //    printf("There are a total of %03d procs.\n", omp_get_num_procs( ));
    thread = omp_get_thread_num();
    (void)sched_getaffinity(0, sizeof(coremask), &coremask);
    cpuset_to_cstr(&coremask, clbuf);
    #pragma omp barrier
    printf("Test %10d MPI_Rank:%d Thread:%02d Node:%s: Core:%s\n", unique_identifier,my_rank,thread,hnbuf,clbuf);
  }

  if (my_rank == 0)
  {
    printf("Test %10d Going to sleep %i seconds\n",unique_identifier,seconds);
    fflush(stdout);
  }
  sleep(seconds);
  MPI_Barrier(MPI_COMM_WORLD);


}




