#!/usr/bin/env python3
import os
import sys


KRIPKE_PATH = os.path.dirname(os.path.realpath(__file__))
TEST_ATS = "test.ats"


def create_ats_file(nprocs, nprocs_code_args, code, args, init_test_num=0):
    test_num = init_test_num or 1
    write_mode = 'a' if init_test_num else 'w'

    if init_test_num:
        file_contents = ""
    else:
        file_contents = "\n".join([
            "import os",
            "glue(independent=True)",
            "glue(keep=True)",
            f"my_checker = '{KRIPKE_PATH}/ats_check_log.py'\n",
        ])

    for nprocs_ndx, nproc in enumerate(nprocs):
        for arg in args:
            test_line = " ".join([
                f"t{test_num}=test ",
                f"(executable = '{code}',",
                f"clas = '{nprocs_code_args[nprocs_ndx]} {arg}',",
                f"label='{code}_{test_num}',",
                f"np={nproc},",
                "sandbox=False)\n",
            ])
            testif_line = " ".join([
                f"t{test_num + 1}=testif(t{test_num},",
                "executable = my_checker,",
                f"clas = t{test_num}.outname,",
                "nosrun=True)\n",
            ])
            test_num += 2
            file_contents += test_line
            file_contents += testif_line

    with open(TEST_ATS, write_mode) as ats_file:
        ats_file.write(file_contents)
    return test_num


if __name__ == "__main__":
    code = os.path.join(KRIPKE_PATH,
                        'kripke-v1.2.5-20e9ea9/build/bin/kripke.exe')

    # Define sequential test runs
    nprocs = [1]
    nprocs_code_args = ['']
    code_args = [
        '--layout dgz ',
        '--layout dzg ',
        '--layout gdz ',
        '--layout gzd ',
        '--layout zdg ',
        '--layout zgd ',
        '--layout dgz  --zset 2,4,8 --gset 2 --groups 6 ',
        '--layout dzg  --zset 2,4,8 --gset 2 --groups 6 ',
        '--layout gdz  --zset 2,4,8 --gset 2 --groups 6 ',
        '--layout gzd  --zset 2,4,8 --gset 2 --groups 6 ',
        '--layout zdg  --zset 2,4,8 --gset 2 --groups 6 ',
        '--layout zgd  --zset 2,4,8 --gset 2 --groups 6 ',
        '--layout dgz  --zset 2,4,8 --gset 2 --groups 6 ',
        '--layout dgz  --pmethod bj',
    ]
    # Create sequential entries in test.ats file.
    last_t = create_ats_file(nprocs, nprocs_code_args, code, code_args)

    # Define parallel test runs
    nprocs = [2, 4, 8, 16, 16]
    nprocs_code_args = [
        '--procs 2,1,1',
        '--procs 2,2,1',
        '--procs 2,2,2',
        '--procs 2,2,4',
        '--procs 4,4,1',
    ]
    code_args = [
        '--layout dgz ',
        '--layout dzg ',
        '--layout gdz ',
        '--layout gzd ',
        '--layout zdg ',
        '--layout zgd ',
        '--layout dgz  --pmethod bj',
    ]

    # Append parallel tests into the same test.ats file
    create_ats_file(nprocs, nprocs_code_args, code, code_args, last_t)

    print(f"Most Excellent! Created ats test file {TEST_ATS}")
