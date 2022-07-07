import argparse
import os
import sys
import subprocess as sp

"""
Wrapper to start ATS with Flux compatibility.

Author: William Hobbs
        <hobbs17@llnl.gov>

"""


def _parse_args() -> argparse.Namespace:
    """Parse arguments for formatting ATS python files."""
    parser = argparse.ArgumentParser(description="ATS with Flux!")
    parser.add_argument(
        "-N",
        "--num-nodes",
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
        --nodes=
          Specify a number of nodes to use, will default to use 3.
        --bank=
          Specify a project bank to charge, will default to use whatever your default bank is.
        --partition=
          Specify either the debug or batch partition, will default to use debug.
    """

    """Check to make sure a valid Flux installation is present on the system."""
    args, extra_args = _parse_args()

    try:
        version = int(
            sp.check_output(["flux", "-V"])
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

    # TODO: 'sys_type' unused.
    # sys_type = os.getenv("SYS_TYPE")
    slurm_job_id = os.getenv("SLURM_JOB_ID")

    # num_nodes = 3
    # for index, arg in enumerate(sys.argv):
    #     if arg.find("nodes") >= 0:
    #         (key, val) = arg.split("=", 1)
    #         if val.startswith('"') and val.endswith(
    #             '"'
    #         ):  # strip off possible quotes
    #             val = val[1:-1]
    #         num_nodes = str(val)
    #         print("INFO: atsflux will use %s nodes" % num_nodes)
    #         del sys.argv[index]
    #
    # partition = "pdebug"
    # for index, arg in enumerate(sys.argv):
    #     if arg.find("partition") >= 0:
    #         (key, val) = arg.split("=", 1)
    #         if val.startswith('"') and val.endswith(
    #             '"'
    #         ):  # strip off possible quotes
    #             val = val[1:-1]
    #         partition = str(val)
    #         print("INFO: atsflux will use partition %s" % partition)
    #         del sys.argv[index]
    #
    # account = "guests"
    # for index, arg in enumerate(sys.argv):
    #     if arg.find("bank") >= 0:
    #         (key, val) = arg.split("=", 1)
    #         if val.startswith('"') and val.endswith(
    #             '"'
    #         ):  # strip off possible quotes
    #             val = val[1:-1]
    #         account = str(val)
    #         print("INFO: atsflux will use bank %s" % account)
    #         del sys.argv[index]
    #
    cmd = []

    if slurm_job_id == None:  ## if this is on login node
        cmd = [
            "salloc",
            f"--nodes={args.num_nodes}",
            f"--partition={args.partition}",
            f"--account={args.account}",
            "--time=60",
        ]

    """Get the path to an .ats file and find the test file."""
    """Find the proper ATS implementation to pass the complete path."""
    myats = os.path.join(sys.exec_prefix, "bin", "ats")

    # TODO: unused variables below commented out.
    """The following is copied from atslite1.pyL#28-46"""
    # test_ats_found = False
    test_ats_file = ""
    # clean_found = False
    # exclusive_found = False
    # nosub_found = False

    # TODO: test_ats_file should be found in extra_args
    test_ats_file = extra_args

    # for index, arg in enumerate(sys.argv):
        # print arg
        # if arg.find("=") >= 0:
        #     (key, val) = arg.split("=", 1)
        #     sys.argv[index] = key + '="' + val + '"'
        # elif arg.find("exclusive") >= 0:
        #     exclusive_found = True
        # elif arg.find("clean") >= 0:
        #     clean_found = True
        # elif arg.endswith(".ats"):
        #     test_ats_file = arg
        #     if not os.path.exists(test_ats_file):
        #         sys.exit("Bummer! Did not find test file %s" % (test_ats_file))

    cmd.extend(
        [
            "srun",
            f"-N{args.num_nodes}",
            f"-n{args.num_tasks}",
            "--pty",
            "/usr/bin/flux",
            "start",
            "-o,-S,log-filename=out",
        ]
    )
    os.environ["SYS_TYPE"] = "flux00"
    cmd.extend([myats, test_ats_file])
    print("Executing: " + " ".join(cmd))

    sp.run(cmd, text=True)


if __name__ == "__main__":
    main()
