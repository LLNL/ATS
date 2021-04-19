
#####
Notes
#####

This chapter contains documentation useful for maintainence, customization,
and debugging.

*******
Modules
*******

.. index:: 
   :pair: ats;module documentation

The ats module contains several submodules documented below. The ``ats`` program
imports the ``ats`` module and calls the manager's ``main`` routine. 
As documented in :ref:`Custom Drivers <Custom_Drivers>`, 
a user may create their own driver and even break ``main`` down into pieces in 
that driver.
 
ats
===

.. automodule:: ats

configuration
=============

The configuration module makes the basic discoveries about the machines, 
creates the log, requests command-line options from the machines, and 
processes the options with call-backs to interested parties to examine them.

.. automodule:: ats.configuration
   :members:

management
==========

The management module is the main supervisor of the program, and is instantiated
as a singleton object, ``manager``.

.. automodule:: ats.management
   :members: 

tests
=====

This module defines test objects and groups.  However, these are not created
directly but rather via functions in the manager, ``test``, ``testif``, 
``group``, ``endgroup``.

.. automodule:: ats.tests
   :members:

schedulers
==========

The scheduler attribute of the machine is an instance of the ``StandardScheduler`` class.

.. automodule:: ats.schedulers
   :members:

machines
========

(See also :ref:`Porting <Porting>`.)

This module contains base definitions for interactive and batch facilities.
To adapt to a new platform, inherit from machine and override appropriate 
methods. 

.. automodule:: ats.machines
   :members:

log
===

The log is an instance of ``AtsLog``. The log object is callable
(See the  ``AtsLog.__call__`` method). A call is equivalent to the method ``write``.
The log call can write to a file, the terminal, or both.

An instance of AtsLog named ``terminal`` is also available. This writes 
only to the standard out, not to any file.

.. automodule:: ats.log
   :members:

times
=====

This module contains utility functions and a class that deal with times.

.. automodule:: ats.times
   :members:

atsut
=====

This module contains utilities and definitions (such as the statuses) used
widely in ATS. The basic error type ``AtsError`` is also defined here.
Many of these definitions are imported into the ``ats`` module proper.
The class AttributeDict is used in several places. It is a dictionary
that also accepts attribute-style reading and writing. 

.. automodule:: ats.atsut
   :members:

executables
===========

This small module is used to represent executables.

.. automodule:: ats.executables
   :members:


*****************
Programming Notes
*****************

Note that because of the complex interactions between priorities, dependents,
filters, and waits, the ``AtsTest`` and ``AtsTestGroup`` classes cannot be 
directly instantiated by a user. The purpose of making those classes visible
at the ats module level is to allow subclassing.

Forming Groups
==============

Each test has a ``group`` attribute. These are instances of `AtsTestGroup`. 
Under normal circumstances each test gets a new group instance with a distinct
group number, and that test is the only method of that group.  Doing this avoids
a considerable amount of logic compared to only having groups for tests
created in the scope of a `group()` command.

When a `group()` call occurs, the `newGroup` class method of the `AtsTest` 
class is called. This halts the incrementing of the group number and 
subsequent tests that are created share the group instance until either 
``endgroup()`` is called and calls the class method ``endGroup``, or we reach 
the end of the source file, which triggers a call to ``endGroup``.

Note that a ``group`` call can specify keyword / value pairs which bind more 
tightly than anything except an explicit pair in a `test` statement. 
This allows the user for example to specify a base label, with the other 
members of the group getting the same name with a ``#n`` numbering by default.

The group objects inherit from list and are basically a list of test objects
with routines added to treat the list as a collection.

Implementing Waits
==================

Three `AtsTest` class methods combine to implement `wait()`: `waitNewSource`,
called when a new file is begun; `waitEndSource`, called at the end of a 
sourced file; and `wait` itself, called by the user. 

The result is that each test object ends up with an attribute `waitUntil` 
which is a list of the tests this object must wait for.  Note that this 
attibute (on the test object, not the one on the class) must never be 
modified because it may be shared with another test. You will note in the 
coding several instances of such lists being copied with a colon selector, in
order to avoid unwanted sharing.

Since many of these lists are long stretches of consecutive integers, it would
be possible to save space by making them instances of a special class that 
acts like a list.  We have not yet done this and will until users decide they
are happy with the semantics we have currently implemented.

Dependents
==========

Each test has a list of all of its direct and indirect dependents. These lists
are created via the method ``addDependent`` of ``AtsTest`` called by the
``testif`` function.

This method enforces several important policies, such as disabling tests that
are children of tests that will never run or which are expected to give a 
failing result, or which are to be batched.

The need to enforce these policies drives the decision to do `canRun` early.
This means that by the time a dependent is created, the status of its parent(s) has been fixed as to filtered, skipped, or batched. Note particularly the case
where an otherwise interactive test gets switched to batch because it cannot
run on this interactive machine.
 
The Standard Machine
====================

As tests are created, the ``canRun`` method of the interactive machine is called
to determine if a test can run when the machine is empty. Assuming a test 
makes it into the final interactive test list, all of which are in status 
CREATED, we need to decide the order in which the tests are to be run.

This order is dynamic, as it depends on processor availablity. Other factors 
are the results of ``wait`` and ``group`` commands.

There are four conditions that must be met to run a test:

#. The test has status CREATED.
#. Enough processors are available.
#. The directory where the test is to be executed is not "blocked". The test
   would not be affected if its option ``independent`` is True. Otherwise there
   must not be a non-independent test or group currently reserving that 
   directory (that is, another test is running there or a group was started
   there that isn't finished yet).
#. Any parent tests are finished and have passed, and any tests this one must
   wait for because of ``wait()`` calls are no longer waiting to run.

As tests complete, any failure may put descendents into SKIP status.

During the ``load`` of the interactive test list, the ``totalPriority`` of 
a test is calculated using the test's list of children and tests that must
wait for it. The sum of the priorities of such subordinate tests becomes the 
``totalPriority`` of the test. The test list is then sorted on 
``totalPriority``.

To choose the next test to start, then, we take the first test in the list 
that satisfies the four conditions. (The routine ``canRunNow`` tests this.)

As tests complete, we must eventually find a new test to run if there is one 
whose status is still CREATED, because when no test is running any more, 
no directory is blocked and the tests have all been certified runnable on an 
empty machine by ``canRun``. 

When we can't find such a test, we' re done!

