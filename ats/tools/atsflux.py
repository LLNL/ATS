"""
Wrapper to start ATS with Flux compatibility.

Author: William Hobbs
        <hobbs17@llnl.gov>
        David Bloss
        <bloss1@llnl.gov>
        Shawn Dawson 
        <dawson6@llnl.gov>
"""

import argparse
import multiprocessing
import os
import shutil
import subprocess
import sys

# Python 3 method for querying number of CPUS on the node
num_cpus = multiprocessing.cpu_count()

# Get hostname to set defaults for if Flux is the native scheduler
my_hostname = os.environ.get("HOSTNAME", "unset")
if (my_hostname.startswith('rzwhip')):
    flux_native = True
    time_limit = 240
else:
    flux_native = False
    time_limit = 240

def _parse_args() -> argparse.Namespace:
    """Parse arguments for formatting ATS python files."""
    parser = argparse.ArgumentParser(description="ATS with Flux!")
    parser.add_argument(
        "-N",
        "--numNodes",
        default=2,
        type=int,
        help="Number of nodes allocated to atsflux.",
    )
    parser.add_argument(
        "-n",
        "--npMax",
        default=num_cpus,
        type=int,
        help="Max number of cores per node. Overrides default ATS detection of cores per node",
    )
    parser.add_argument(
        "--job_time",
        default=time_limit,
        type=int,
        help="Job allocation time limit in minutes",
    )
    parser.add_argument(
        "--exclusive",
        action="store_true",
        help="Exclusive use of nodes allocated.",
    )
    parser.add_argument(
        "-A",
        "--account",
        dest="account",
        default="guests",
        type=str,
        help="Project bank to charge.",
    )
    parser.add_argument(
        "-p",
        "--partition",
        default="pdebug",
        type=str,
        help="Partition in which to run atsflux jobs.",
    )
    parser.add_argument(
        "--flux",
        default=flux_native,
        action="store_true",
        help="Machine uses flux as the native scheduler.",
    )
    return parser.parse_known_args()


def main():
    """
    Wrapper driver for running ATS tests under Flux.

    Available command-line arguments:
        --numNodes=, -N
          Specify a number of nodes to use, will default to use 3.
        --npMax=, -n
          Max number of cores per node. Overrides default ATS detection of cores per node
        --account=, -A
          Specify a project bank to charge, will default to use whatever your default bank is.
        --partition=, -p
          Specify either the debug or batch partition, will default to use debug.
        --flux
          Machine uses flux as the native scheduler.  Do not use salloc and srun.
    """

    """Argument parsing logic goes first."""
    args, extra_args = _parse_args()

    """Check to make sure a valid Flux installation is present on the system."""
    try:
        version = int(
            subprocess.check_output([shutil.which("flux"), "-V"])
            .split()[1]
            .decode("utf-8")
            .split(".")[1]
        )
        if (version) < 38:
            sys.exit(
                f"""ATS ERROR: this system does not have a current version of Flux installed.
                Version 0.{version}.0 is installed but >= 0.38.0 is required. Please update
                the Flux version or use a different Flux (check which one you're using with `which flux`).
                """
            )
    except Exception:
        sys.exit(
            """ATS ERROR: this system does not have a current version of Flux installed.
            No version of Flux was found on this system but version >= 0.38.0 required. Please update
            the Flux version or specify a different Flux installation to use.
            """
        )

    # Total cores is number of nodes * number of cores per node
    total_cores = args.numNodes * args.npMax

    os.environ["NP_MAX"] = str(args.npMax)

    if args.flux:
        print("running flux natively")

        cmd = []

        # If FLUX_JOB_ID exists, assume we are already in a flux allocation.
        if "FLUX_JOB_ID" in os.environ or "FLUX_CONNECTOR_PATH" in os.environ or "FLUX_TERMINUS_SESSION" in os.environ:
            print("looks like we are already in a flux allocation")

        # else start flux from the login node
        else:
            cmd = [
                "flux", "alloc",
                "-N", f"{args.numNodes}",
                "-n", f"{total_cores}",
                "-t", f"{args.job_time}m",
                "--exclusive",
                "--output=atsflux.log"
            ]


    else:
        print("running flux under slurm")

        slurm_job_id = os.getenv("SLURM_JOB_ID")
        cmd = []

        if slurm_job_id == None:  ## if this is on login node
            cmd = [
                "salloc",
                f"--mpibind=off",
                f"--nodes={args.numNodes}",
                f"--partition={args.partition}",
                f"--account={args.account}",
                "--exclusive",
                f"--time={args.job_time}",
            ]
    
        cmd.extend(
            [
                "srun",
                f"-N{args.numNodes}",
                f"-n{args.numNodes}",
                "--pty",
                shutil.which("flux"),
                "start",
                "-o,-S,log-filename=out",
            ]
        )

    """Get the path to an .ats file and find the test file."""
    """Find the proper ATS implementation to pass the complete path."""
    myats = os.path.join(sys.exec_prefix, "bin", "ats")

    os.environ["MACHINE_TYPE"] = "flux00"
    cmd.append(myats)
    cmd.extend(extra_args)
    print("Executing: " + " ".join(cmd))

    completed_process subprocess.run(cmd, text=True)

    #  return return code from flux or salloc
    return(completed_process.returncode);


if __name__ == "__main__":
    main()
