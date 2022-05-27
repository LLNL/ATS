# ATS Release Notes

## 7.0.105

Update sleepBeforeRun option.
Renamed from sleepBeforeSrun.
Still honor sleepBeforeSrun, simply map
to sleepBeforeRun.
Change value given to this option from an int to a float.
    
Add tossrun for VIP project usage.

Default ruby machine type to slurm56
   
Add Krike testing to Python 3 branch
    
Account for slurm version such as 21.08.8-2
    
Added --useMinNodes for toss (slurm)
    
If --useMinNodes specified, then within an allocation
  specify
    srun_nodes="--nodes=%i-%i" % (minNodes, minNodes)
    
when starting the job, where minNodes is the minimum
number of nodes needed for the requested number of MPI
processes.   This is experimental at this point,
and may lead to hangs or lower throughput.
    
Add smpi options to ats command line
Either one of these may be used to disable the --smpiargs="-gpu" option.
  --smpi_off
  --smpi_show


## 7.0.100

* Port to Python 3.8

## 7.0 

* 2021-April-19
* Migrated from Bitbucket to GitHub


