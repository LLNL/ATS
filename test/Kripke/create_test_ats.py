#!/usr/bin/env python2
from __future__ import print_function
import os
import sys

independent=True
sandbox=False

ABS_FILE_PATH = os.path.dirname(os.path.realpath(__file__))
checker = os.path.join(ABS_FILE_PATH, 'ats_check_log.py')
test_ats="test.ats"
code = os.path.join(ABS_FILE_PATH, 'kripke-v1.2.5-20e9ea9/build/bin/kripke.exe')

test_ats="test.ats"

# -------------------------------------------------------------------------------------------------
# Define the sequential test runs here
# -------------------------------------------------------------------------------------------------
nprocs=[1]
nprocs_code_args=['']

code_args=['--layout dgz ',
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
           '--layout dgz  --pmethod bj'
          ]

# -------------------------------------------------------------------------------------------------
# Define parallel tests here.
# Broken out into two sections as I noticed that not all of the sequential tests may be run
# in parallel.
# -------------------------------------------------------------------------------------------------
nprocs_2=[2, 4, 8, 16, 16]
nprocs_code_args_2=['--procs 2,1,1', '--procs 2,2,1', '--procs 2,2,2', '--procs 2,2,4', '--procs 4,4,1']

code_args_2=['--layout dgz ',
             '--layout dzg ',
             '--layout gdz ',
             '--layout gzd ',
             '--layout zdg ',
             '--layout zgd ',
             '--layout dgz  --pmethod bj'
            ]

# -------------------------------------------------------------------------------------------------
# Main.  Call ATS routine to use the above data to create a test.ats file
# -------------------------------------------------------------------------------------------------
#tempstr = sys.executable
#atsModulesDir  = tempstr.replace('bin/python','')
#atsASC_Modules_dir = os.path.join(atsModulesDir, 'atsASC/modules')
#sys.path.append( atsASC_Modules_dir )

from atsASC.modules.ASC_utils import create_ats_file_version_004

if __name__=="__main__":

    # First create sequential entries in test.ats file.
    # Then append parallel tests into the same test.ats file 
    last_t = create_ats_file_version_004(independent, checker, test_ats, nprocs,   nprocs_code_args,   code, code_args,   sandbox)
    last_t = create_ats_file_version_004(independent, checker, test_ats, nprocs_2, nprocs_code_args_2, code, code_args_2, sandbox, last_t)

# end of file
