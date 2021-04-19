#!/bin/env python
#*****************************************************************************
#*****************************************************************************
"""
Streamlined Python callable interfaces for VisIt's test suite.
"""

import os
from atsASC.Visit.visit_testing import visit_test_suite
from atsASC.Visit.visit_testing import visit_test_reports

def run_visit_test(script_file,
             data_dir=None,
             baseline_dir=None,
             output_dir=None,
             visit_bin="/usr/gapps/visit/bin/visit",
             verbose=False):
    tests = [script_file]
    return run_visit_tests(tests,
                           data_dir,
                           baseline_dir,
                           output_dir,
                           visit_bin,
                           verbose)

def run_visit_tests(tests,
                    data_dir=None,
                    baseline_dir=None,
                    output_dir=None,
                    visit_bin="/usr/gapps/visit/bin/visit",
                    verbose=False):
    opts = visit_test_suite.default_suite_options()
    if not data_dir is None:
        opts["data_dir"]     = data_dir
    if not baseline_dir is None:
        opts["baseline_dir"] = baseline_dir
    if not output_dir is None:
        opts["result_dir"] = output_dir
    opts["executable"] = visit_bin
    # override other default options
    opts["check_data"]    = False
    opts["cleanup_delay"] = 1
    if verbose:
        opts["verbose"] = True
    opts["test_dir"] = os.path.split(os.path.abspath(__file__))[0]
    print opts["test_dir"]
    res_file  = visit_test_suite.main(opts,tests)
    return visit_test_reports.JSONIndex.load_results(res_file,True)

