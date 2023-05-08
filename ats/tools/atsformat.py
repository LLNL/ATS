#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    """Parse arguments for formatting ATS python files."""
    parser = argparse.ArgumentParser(description="Format ATS python files.")
    parser.add_argument(
        "-c",
        "--check",
        action="store_true",
        help="Check if isort or black would format ATS' code",
    )
    parser.add_argument(
        "path",
        nargs="+",
        type=Path,
        help="File(s) or directory to parse recursively.",
    )
    return parser.parse_args()


def unformat_ATS_headers(ats_file) -> None:
    """Undo formatting on ATS headers. Keep `#ATS:` and `#BATS:` as is."""
    with open(ats_file) as _file:
        file_contents = _file.read()

    formatted_contents = file_contents.replace("# ATS:", "#ATS:").replace(
        "# BATS:", "#BATS:"
    )

    with open(ats_file, "w") as _file:
        _file.write(formatted_contents)


def main() -> None:
    """ATS files formatting script using various formatters."""
    args = _parse_args()

    # Favor formatters found by Python over ones found in system $PATH
    BLACK_CMD = [sys.executable, "-m", "black"]
    ISORT_CMD = [sys.executable, "-m", "isort"]
    BLACK_OPTIONS = ["--check"] if args.check else []
    ISORT_OPTIONS = [
        "--check" if args.check else "--apply",
        "--profile",
        "black",
    ]

    print("ATS: Running Black formatter...")
    completed_process = subprocess.run(BLACK_CMD + BLACK_OPTIONS + args.path)
    print("ATS: Black formatter done.\n")
    if completed_process.returncode != 0:
        return(completed_process.returncode)

    print("ATS: Running isort formatter...")
    completed_process = subprocess.run(ISORT_CMD + ISORT_OPTIONS + args.path)
    print("ATS: isort formatter done.")
    if completed_process.returncode != 0:
        return(completed_process.returncode)

    for machine_file in Path("ats", "atsMachines").glob("*.py"):
        unformat_ATS_headers(machine_file)

    return(0)


if __name__ == "__main__":
    main()
