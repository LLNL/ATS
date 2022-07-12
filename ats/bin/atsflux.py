"""
Wrapper to start ATS with Flux compatibility.

Author: William Hobbs
        <hobbs17@llnl.gov>
        David Bloss
        <bloss1@llnl.gov>
"""

import argparse
import os
import shutil
import subprocess
import sys


def _parse_args() -> argparse.Namespace:
    """Parse arguments for formatting ATS python files."""
    parser = argparse.ArgumentParser(description="ATS with Flux!")
    parser.add_argument(
        "-N",
        "--numNodes",
        default=3,
        type=int,
        help="Number of nodes allocated to atsflux.",
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
    return parser.parse_known_args()


def main():
    """
    Wrapper driver for running ATS tests under Flux.

    Available command-line arguments:
        --numNodes=, -N
          Specify a number of nodes to use, will default to use 3.
        --bank=
          Specify a project bank to charge, will default to use whatever your default bank is.
        --partition=
          Specify either the debug or batch partition, will default to use debug.
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
                f"""Error: this system does not have a current version of Flux installed.
                Version 0.{version}.0 is installed but >= 0.38.0 is required. Please update
                the Flux version or use a different Flux (check which one you're using with `which flux`).
                """
            )
    except Exception:
        sys.exit(
            """Error: this system does not have a current version of Flux installed.
            No version of Flux was found on this system but version >= 0.38.0 required. Please update
            the Flux version or specify a different Flux installation to use.
            """
        )

    slurm_job_id = os.getenv("SLURM_JOB_ID")
    cmd = []

    if slurm_job_id == None:  ## if this is on login node
        cmd = [
            "salloc",
            f"--nodes={args.numNodes}",
            f"--partition={args.partition}",
            f"--account={args.account}",
            "--exclusive",
            "--time=60",
        ]

    """Get the path to an .ats file and find the test file."""
    """Find the proper ATS implementation to pass the complete path."""
    myats = os.path.join(sys.exec_prefix, "bin", "ats")

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
    os.environ["SYS_TYPE"] = "flux00"
    cmd.append(myats)
    cmd.extend(extra_args)
    print("Executing: " + " ".join(cmd))

    subprocess.run(cmd, text=True)


if __name__ == "__main__":
    main()
