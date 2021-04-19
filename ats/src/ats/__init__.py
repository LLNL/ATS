"""Automated testing system module.

This module is usually driven by an executable script, ``ats``, 
or by a customized driver that either calls manager.main() or which calls the 
same things with additional actions interspersed. 

The module begins by importing two modules ``times`` and ``configuration``, 
which must be done first. Then it sets up the ``manager`` object and the 
``testEnvironment`` dictionary.  

From ``configuration`` the environment variables SYS_TYPE, BATCH_TYPE, 
MACHINE_TYPE and MACHINE_DIR are obtained. These are used to choose the proper 
execution module (called a machine in ATS).

From the ``log`` module we get ``log`` and ``terminal``, two functions used
to send messages to the log file and terminal.

The statuses and their equivalent four-character abbreviations are:

* PASSED (PASS) -- test finished successfully.
* FAILED (FAIL) -- test was run, returned non-zero exit status.
* TIMEDOUT (TIME) -- test failed by exceeding its ``timelimit``.
* EXPECTED (EXPT) -- test ran and got an expected non-PASS status
* BATCHED (BACH) -- test was sent to the batch system
* FILTERED (FILT) -- the test was not run due to a filter
* SKIPPED (SKIP) -- the test was not attempted, for a reason given.

The following statuses are transitory or special-use:

* CREATED (INIT) -- the test has been created successfully, but not yet run.
* RUNNING (EXEC) -- the test is currently running.
* HALTED (HALT) -- the test was halted by a time cutoff option.
* LSFERROR (LSFE) -- the test encountered an error attributasble to LSF

The classes AtsTest and AtsTestGroup are defined here to enable user 
subclassing but must not be used directly -- creation of a test must go through 
the ``test`` or ``testif`` commands, and groups via ``group`` and ``endgroup``.

"""
import times
import configuration
from management import manager, testEnvironment   # manager.main() to execute
from tests import AtsTest, AtsTestGroup  
# for possible use in driver scripts or unit testing
from atsut import AtsError, AttributeDict, \
                  StatusCode, statuses, debug, \
                  CREATED, INVALID, PASSED, FAILED, HALTED, EXPECTED, LSFERROR, \
                  SKIPPED, BATCHED, RUNNING, FILTERED, TIMEDOUT
from configuration import SYS_TYPE, MACHINE_TYPE, BATCH_TYPE, MACHINE_DIR
from log import log, terminal

from times import Duration
# make statuses available as their abbreviations, too.
for key, value in statuses.items():
    exec "%s = %s" % (value.abr, key)
del key, value

