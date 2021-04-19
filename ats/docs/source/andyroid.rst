##########################
The ATS Tutorial, Andyroid
##########################

.. index:: Andyroid

************************
Introduction To Andyroid
************************

We have seen a brief overview of ATS and its rationale. This part of the 
document discusses an extended example and some hints about how to use ATS.  
It is followed by a reference section. Few adventurers survive the reference 
section; take an easy trip with this tutorial before venturing into that jungle.

The sources you need to follow along interactively are in the 
``Examples/Andyroid`` subdirectory of the ATS distribution. However, you 
can also just read along. 

The premise of this tutorial is that we have a program called *andyroid*; it 
has a post-processor named *andyroidPoster* that runs using the output file of 
*andyroid* as input. 

These two executables are located in subdirectory *andyroid*. To avoid having 
to compile anything for this example, these are in fact scripts, so that 
to execute *andyroid* is really accomplished by executing::

    python andyroid/andyroid.py

but you can just imagine that andyroid is a compiled program that has been 
installed in that subdirectory. You can see the options *andyroid* has by
executing ``python andyroid/andyroid.py --help``.

      -h, --help               show this help message and exit
      -i FILE, --input=FILE    input file name
      -o FILE, --output=FILE   output file name
      --delta                  Add delta?
      --alpha=ALPHA            A vital parameter

From here on out we will assume *andyroid* is an alias for 
``python andyroid/andyroid.py`` so that we don't add to the confusion with the 
extra text that would not be present for a real program. Just pretend 
*andyroid* is a compiled program.

Running Andyroid under ATS
==========================

Let's suppose that we normally test our program *andyroid* by using this 
command::

     andyroid -i test1.in -o test1.out

How do we get ATS to execute this test for us? The simplest way is to make 
a file ``simpleTestSuite.ats`` that contains::

    import os
    # this is the system-independent way to say "python andyroid/andyroid.py"
    andyroid =sys.executable + ' ' + os.path.join("andyroid", "andyroid.py")

    test(executable = andyroid,
         clas = '-i test1.in -o test1.out', label= 'test1')

.. index:: clas

(``clas`` stands for "Command Line ArgumentS"). Then execute:

    ats simpleTestSuite   

Note: this is not the recommended strategy, but there is a lot to learn
by starting simply. ATS has lots of command-line options as detailed in 
the reference part of this document, but we don't need any yet.

.. index::
   triple;ats.log;atss.log;logs
   pair:log;directory

Go ahead and try it. You'll notice some interesting things here.

* The input file simpleTestSuite was found even though we didn't put on 
  the .ats extension. ATS tries the name, then the name with .ats added,
  and finally the name with .py added.
* We constructed the name of the executable using sys.executable so that 
  it would use the same Python that ats is being run with. In general, 
  ATS tests the executable to be sure it exists and does not rely on 
  your path to find it, so you must be precise. This is to avoid having 
  all your tests pass when in fact you didn't execute the program you 
  intended to test.
* ``label`` is a name for this test. A test has both a unique serial number,
  and a unique label. (If the label isn't unique ATS will make it unique
  after all the tests have been collected from your input file(s).)
* The output from the program we test (and separately, its standard error), 
  and the output from ats itself, are put in a single directory. This 
  directory has a name that contains the kind of computer we're running on,
  and the time. The directory has the extension ``.logs``. 

  The output files for a given test contain the test's serial number, 
  a simplified form of the label, and the time. That doesn't mean all 
  the output from the test goes there; if the test creates files it creates 
  them  in the directory where ATS is running them, which is by default the 
  directory of the "sourced" file that specified the test. That doesn't have to 
  be so, as explained in the reference section entry for the 
  :ref:`test function <testFunction>`.

  So, when you ran ``simpleTestSuite``, *andyroid* created 
  a ``something.logs`` directory, containing ``ats.log``. Unless the test 
  failed, the standard output and standard error (which were in that same
  directory) have been deleted. 
      
  To make ATS keep the output we can add an option to the test command, 
  ``keep = True``. Or, we can run ATS with a ``--keep`` option, which will
  keep the output of any test that doesn't have ``keep = False`` as an option.

You'll also notice the log has full information on which tests passed or failed,
and has various summaries and the list of what tests were started in what order.
Additional information on scheduling is available in ``atss.log``, especially 
when using the ``--verbose``\  or ``--debug``\  options.

Also in the log directory after ATS has finished execution is a file named "atsr.py",
where the "r" stands for "results". This file can be used in postprocessing; see
:ref:`Results Facility <Results_Facility>` for details.

********************
ATS Execution Phases
********************

ATS works in six phases.

#. Read the files on the command line.
#. Examine the collection of tests, make sure every test has a distinct label, 
   and identify batch, interactive, and ineligible jobs (for example, one 
   that needs more processors than are available).
#. Dispatch any batch jobs that have been specified to the batch system.
   If there is no batch system, such jobs are usually skipped, but this 
   can be overridden by the '--allInteractive' option.
#. Run the tests.
#. Report the results
#. Run any postprocessors the user has defined.

Here are the details.

Phase 1: Sourcing
=================

The first phase is to read the files you specify on the command line in the 
order you gave them. This is called *sourcing* them, because it is equivalent 
to using ATS's ``source`` command. 

A file being sourced is written in Python using some already built-in features, 
as we discuss later. In ``simpleTestSuite``\ , we are able to refer to a 
function called ``test``\ , which is already defined for us. 

A test is created for each ``test`` or ``testif`` statement that is executed.
However, the ATS statements such as ``test`` can be mixed with arbitrary
Python statements.

The ``test`` or ``testif`` statements return a value, a test object. 
This object contains all the information about the test; its attributes 
are documented in the reference manual.

.. warning:: A test is not executed when the test function is executed.

   The input language creates the illusion that the test function is causing
   the test itself to be executed. And it is ... eventually, but not now.
   The test statement creates a test object and puts it in a big list of 
   test objects, but it doesn't execute any tests until it is entirely 
   done sourcing files.

   Consequently, you  may not test the truth value of a test object::

      if test(...):   # ERROR CANNOT DO THIS
         test(...)
   
      t = test(...)
      if t: ...        # NOR THIS

   This coding is disallowed because it looks like it is making one test
   depend upon another, but it isn't. The tests are not executed at this 
   stage but rather later. 

To make one test depend on another's success, we do this::

   t = test(...)
   testif(t, ...)

As the tests are collected, the filters that have been defined so far are
used to see if the test should be attempted or not. Besides any user-defined
filters there are built-in filters on the number of processors, ``np``, and the 
``level``.  The level is simply an easier-to-use filter that lets us execute 
just a portion of a test suite.

.. index::group
.. index::endgroup
.. index::wait

Two more functions, ``group`` and ``endgroup``\ , can be used to group together 
a set of tests that are to be considered as a unit for reporting success or failure,
and optionally for protecting one or more directories from interference from other tests.

The ``wait`` function can be used to divide source files into portions, so that 
the tests defined in that source file, after a ``wait()`` call, execute only when the 
tests declared above it are completed. 

All these features are described in more detail in the reference material
chapter :ref:`Controlling Input  <Input>`.

In the log, the end of the input phase is marked with a message that says, 
"Input complete."

Phase 2: Sorting
================

The tests are examined to determine these things:

* Is the test to be executed interactively or in a batch system?
* Does the test depend on another (via a ``testif`` statement) so that
  its execution must follow that of its parent (and be cancelled if the
  parent fails?).
* Is the test a member of a group, or subject to a ``wait`` statement?
* Are there sufficient CPU resources to run the test?

From all this information, the list of tests that each test must wait for 
is calculated, and a priority is assigned.

Phase 3: Batch
==============

Any tests that are scheduled for batch are sent off to be handled by the
batch system. The details of how that is done and how you find out what 
happened depends on the particular batch system.

Phase 4: Execution
==================

ATS must decide which tests to start given the available resources. To that 
end, each test has a priority. We can assign that priority (an integer) in the 
test statement itself, but if we do not, a priority is calculated that reflects 
the value of np (the number of processors the test requires) in the test and the
priorities of any tests that must wait for this one to finish.

As a result, parent tests tend to be executed earlier so that they do not 
become a bottleneck. But, depending on the available resources, lower-priority 
jobs may be used to keep the machine "full". 

You can see from the logs (especially atss.log``) which tests were started. If you see 
that a test ends up executing for a long time after all the others are finished, you can 
give it a higher priority. If you aren't getting the behavior you expect, 
see the reference chapters for further details, especially 
:ref:`directory blocking <directory_blocking>`.

After test execution is completed, a file named ``continue.ats`` is written into
the logs directory if any of the tests failed. After fixing the problem, you can
use ``continue.ats`` as an additional input file to another ats run. This allows
you to fix as many problems as possible before attempting a full test suite 
again.

Phase 5: Report
===============

Reports are made about the tests, followed by summaries.  Some tests can 
be made to report on the terminal only if they fail, using the ``record`` or ``group`` 
options.  These reports are made to the log. Information about tests that finished can be 
seen immediately by using the ``--verbose`` command-line option.

Phase 6: Postprocessing
=======================

.. index::
   pair:  postprocessing; file ``atsr.py``

Any functions registered by the user for post-processing are executed. 

.. function:: onExit(f)

    onExit(f) can be called with a the name of a function that
    takes one argument, the ATS manager object. At the end of the ATS run this 
    function will be called. The function f can do whatever it likes. 

Multiple functions can be registered and they will be called in the order in 
which they were registered.  Possible applications are printing reports, 
making graphs, etc.

.. note:: The master testlist is manager.testlist.

A file ``atsr.py`` is written into the log directory and can be used for 
postprocessing after ATS has finished. Using this facility, you can compare
runs or analyze previous runs. 
See :ref:`Results Facility <Results_Facility>` in the reference section.

Postprocessing Example
----------------------

Here we add coding to our ATS input file to print out information for 
those tests that were filtered out::

   def showFiltered (manager):
      filtered = [t in manager.testlist if t.status is FILTERED]
      log("Detailed list of filtered tests.")
      log.indent()
      for t in filtered:
          log(t.serialNumber, t.name, t.note)
      log.dedent()
   onExit(showFiltered)

.. index::
   pair: interactive;postprocessing

It would also work to put the showFiltered function in a file showf.py, run::

    python -i <logdirectory>/atsr.py showf.py

    >>> showFiltered(state)

The file ``atsr.py`` defines a variable ``state`` that contains information equivalent to the 
``manager`` object. Using the ``-i`` flag to Python, you can interactively examine the results
of the ATS run.

Debugging Techniques
====================

.. function:: level = debug(ivalue = None)
   ivalue is an integer, or omitted.

With no arguments, ``debug`` returns the current debug level; with an argument
it sets the level.::

    if debug():
        test(....)
    old = debug()  #save current value
    debug(1)
    ...  # debug is true in this section
    debug(old)   # restore previous value

So you can have various levels of debugging in your own coding::

    myDebugLevel = 2
    dsave = debug()   # save the current value
    debug(myDebugLevel)
    if debug():
         .... do some stuff...
    if debug() >= 2:
        ... do some more stuff...
    debug(dsave)   # restore original value

.. note:: 
   The ``--debug`` command-line option is equivalent to a ``debug(1)`` call at 
   the start of your input.

Just remember you can't do an ``if`` on a test object, and it is 
rather pointless to do something right after a test statement because the test 
won't run until the input is all finished. 

::

    logDefinition(name1, ... , echo=True, logging=True) 

can be used to log the named vocabulary words , or with no words, 
all the names. 

Debugging Scheduling
====================

If you run in debug or verbose mode, you will get a lot of information about 
what affected the job schedule by examining the ``atss.log`` file. Entries 
appear showing whether a job that could have executed has been blocked because 
it is waiting for directory blocking (B), waits or dependencies (W), or for 
adequate numbers of processors (C for "CPUs").

***************************
Structuring Your Test Suite
***************************

.. index::
   pair: test options; glue
   pair: test options; stick

It is rare that a test suite of any size becomes an all-or-nothing affair. The
more tests there are, the more the need to run selected sets for selected 
purposes.  However, having the same test specifications repeated in a variety
of input files for ATS is an invitation to maintenance headaches. 

Simple First Steps
==================

We could do the entire test suite by making ``simpleTestSuite`` larger, 
listing one test after another in a single file.  As we will see later, 
various filters and level indicators can be used to make it possible to 
execute selected subsets of the test list.

For example (``inline.ats``)::

   import os, sys
   codeDir = os.path.abspath(os.path.join(os.getcwd(), 'andyroid'))
   andyroid = '%s %s/andyroid.py' % (sys.executable, codeDir)
   andyroidPoster = '%s %s/andyroidPoster.py' % (sys.executable, codeDir)
   stick(clas="-i %(inputFile)s -o %(outputFile)s %(opts)s")
   stick(opts='')
   
   glue(level=10)
   test(executable=andyroid, inputFile='test1.in', outputFile="test1.out", 
             label="test1")
   
   glue(level=20) 
   t = test(executable=andyroid, inputFile='test1.in', outputFile="test1d.out", 
             opts="--delta", label="test1d")
   testif(t, clas = 'test1d.out', executable=andyroidPoster, label='test1dpost', 
          keep=1)
   
However, in our experience a centralized test file is not a good idea except
on a small project. If you have several developers who work in a distributed
source tree, it is better to have the tests near where the developers work,
so that they can add new tests and don't have to fight over a single file
containing a master test list. Instead the master file, or a few files
for different purposes, should contain mostly ``source`` statements to 
source the master files of various subdirectories; e.g.::

    source('subdirectory1/area1.ats')
    source('subdirectory2/area2.ats')
    source('subdirectory3/area3.ats')

and so on down the tree until you get to files that actually specify tests
in different areas.

.. index:: define

However, when you start to do this, you do lose one thing. Remember our 
line that specified what "andyroid" meant? That would have to be repeated
all the way down unless we do something about it. That's not so bad until
the day you want to run some alternate version of andyroid. The solution
is to define the symbol "andyroid" so that it will be known in any 
subsequent "sourced" files::

    andyroid = '/my/path/to/andyroid'
    define(andyroid=andyroid)
    source('subdirectory1/area1.ats')
    ...

We will see this in action later.

Understanding The Test Statement
================================

In Python, functions often take arguments of the form name = value.
These are called keyword-value pairs. 

The `test` function takes these arguments:

 * Zero, one or two positional arguments, followed by

 * An arbitrary number of keyword-value pairs. These keyword-value pairs are 
   collectively called the "options". 

The possible forms are:: 

    test(script, clas, option1 = value1, ...)
    test(script, option1 = value1, ...)
    test(option1 = value1, ...)

The `testif` function is the same with an additional (required) first argument, 
the value returned by a previous `test` or `testif` function.

Understanding Test Options
--------------------------

.. index::
   pair: test; options
   pair: test option; script
   pair: test option; executable
   pair: test option; clas
   pair: test option; test command-line
   pair: test option; np
   pair: test option; label
   pair: test option; batch
   pair: test option; level	
   pair: test option; priority
   pair: test option; independent
   pair: test option; timelimit
   pair: test option; keep
   pair: test option; record
   pair: test option; priority
   pair: test option; hideOutput
   pair: test option; magic
   pair: test option; directory
   pair: test option; SYSTEMS

Some options have default values. Here is a list of the arguments and options
in approximate level of importance or likelyhood of use::

    * script can be given by an option rather than as a positional 
      argument, or omitted.

    * clas can likewise be given as an option and in fact must be if
      script is omitted, or omitted.

    * executable = 'path/to/executable' is the program to be tested.
      If not given, the executable is the one specified with the ``-e`` 
      (or ``--executable``) command-line option, which defaults to Python 
      itself.

      Your executable may include options, such as '/path/to/executable -f',
      or may be given as a list of components, such as 
      ['/path/to/executable', '-f']. If the path contains a space, you
      must use the list form to avoid ambiguity.

    * np = 0  is the number of processors required. Zero means 1 processor
              but may differ in consequence from np = 1 on some machines.

    * label should always be specified to help you understand which test
      is referred to in ATS's output. It defaults to the script name.

    * name is calculated from the name of the executable, but you can 
      set it explicitly. The full name of the test is "name (label)".

    * batch = False; if set to True, the job is executed in batch if possible 
      and otherwise not at all unless ``--allInteractive`` is used.

    * level = 1 is the level of the test, which is subject to the built-in 
      level filter controlled by the ``--level`` command-line option.

    * priority is calculated for you if not given.

    * independent = False; if set to True, the test can be executed when
      CPU resources are available. If False, the test will not be able to execute
      until no other test is running in that directory. See also the 
      :ref:`group facility <group_statement>`.

    * timelimit has a default value of 30m, or as set on the command line
      with ``--timelimit``. The test will be killed and given a timed-out 
      status if it is not finished running after this much time.

    * keep = 0; if set to 1 (or set to 1 by the ``--keep`` option), the output
      files are kept even for tests that passed. If set to 2, the standard
      error file is also kept.

    * check = False; if True, a test that passes is listed as one whose
      output needs to be checked by hand.

    * record = True; record can be set to False to omit summary reports of 
      this test unless it fails. You might do this with tests that are
      simply post-processing followups to a test upon which they depend.

    * hideOutput = False; if set to true, any captured output is not 
      printed in the log. (See the discussion Using Magic Output).

    * directory defaults to the directory in which script resides; or if
      script is not given, to the directory in which the file being 
      sourced statement resides. ATS will execute ``executable`` in this 
      directory.

    * magic = "ATS:"; if an output line starts with this symbol, the
      rest of the line is stored in test.output. The newline at the
      end is stripped off. 

    * SYSTEMS if given is a list of machine names on which this test is to 
      be executed. Otherwise the test will be executed if otherwise eligible.

Resolving Option Values
+++++++++++++++++++++++

For each option keyword there is a final value determined as follows:

    * Start with the default value, if any.
    * Apply values that have been set using the ``glue`` function.
    * Apply values that have been set using the ``tack`` function
    * Apply values that have been set using the ``stick`` function.
    * Apply values that have been set using the ``group`` function.
    * Apply values in the test's options.

This final value is used. The dictionary of final values is used for
interpolation into `script` and `clas`, and for filtering.

Here are the scopes of the various ways of setting values:

* Values set in a test statement apply only to that test.
* Values set with ``stick`` apply only to test statements that follow it
  within the same file. A file sourced by this one does not see the *stuck* 
  value. 
* Values set with ``tack`` apply until to all subsequent test statements until the file 
  being currently sourced is completed. If this file sources another, the 
  tacked value applies in it too.
* Values set with ``glue`` apply to all subsequent test statements until overwritten. 
* Values set with ``group`` apply to all tests defined within the group.  This scope 
  also ends at the end of a source file.
* Values set on the command line apply for the entire run. 

User-Defined Options
====================

.. index::
   pair: test options; user-defined
   pair: options; user-defined

You can add any keyword-value pairs you want to the ``test`` statements, and 
set defaults for them with the ``glue``, ``tack``, or ``stick`` statements. Then
you can use them for filtering or for interpolation into ``clas`` and 
``script``. 

.. index::
   pair: interpolation; options
   pair: interpolation; clas
   pair: interpolation; script
   pair: options; using filters with

Interpolation of the options into clas and script is done by using Python's 
% operator. For example, if clas = "-in %(inputFile)s", and we have an option 
inputFile = 'test1.in', the result will be clas = "-in test1.in".

The user can define options for the purpose of controlling which tests
get executed. For example, if you do this at the top of your input::

    glue(threshold = 0.)

and in some tests you have a different value::

    test(...)
    test(..., threshold = 1., label = 'just me!')
    stick(threshold=10.)
    test(...)
    test(...)

then you can execute ATS with a filter to screen out those tests where 
threshold is outside of some range::

    ats mytest -f 'threshold >=0.5 and threshold <=2.0'

This would execute only the second test above.

Default values can also be defined locally with ``glue``, ``tack``, 
``stick`` and ``group`` directives, and filtered with ``filter`` directives. Including a 
small file with such values and filters might be an effective way to define a
suite::

    ats mydefinitions mytest

where mydefinitions contains glue, tack, and filter specifications.

Pop quiz: in the preceding sentence, why isn't stick mentioned?

Understanding Defines
=====================

.. index::
   pair: vocabulary; define
   pair: vocabulary; undefine
   pair: vocabulary; get
   pair: vocabulary; printing

When a file is sourced, the language in which it is parsed consists of 
any Python statement or built-in function, plus a limited vocabulary that
includes functions like ``test``, ``testif``, ``glue``, ``tack``, ``stick``, 
and ``log``.  The user can manipulate this list for *subsequent* sourced files 
using these functions:

    * define(name=value) adds the name with the given value to the vocabulary.
    * undefine(name) removes name from the vocabulary.
    * logDefinition(name) prints the value of name in the vocabulary; with no
      name given, it prints the entire vocabulary.
    * get(name) retrieves the value associated with name.

If you source a file that adds to the vocabulary, it will not apply in the
rest of the file that did the sourcing. For example::

    source('mydefs.ats')  # in mydefs.ats, define(foo=value) is executed.
    source('file2.ats')  # foo will be defined while sourcing file2.ats.
    test(executable=foo)  # Error! foo not defined here

To remedy this we use the ``get`` function::

    foo = get('foo')
    test(executable=foo)  # foo defined here now.
 
.. index::
   pair: input; file sourced only once
 
Here's an important fact about sourcing: a file is never sourced twice.
If it has already been sourced, it is skipped. That means that it is 
not expensive to do::

    source('mydefs.ats')
    foo = get('foo')

in any input files. It won't matter which of them is executed first, they
will all get the definition for foo that they need.
 
Defining functions
==================

.. index::
   pair: functions; defining
   pair: functions; wrappers

Note that you can define anything to put it in the vocabulary, including 
Python functions. For example, suppose we wish to define a function
that executes andyroid and its post-processor andyroidPoster and which has
an interface of our choosing. Here is an example (file andyroid/andyroid.ats)::

    import os, sys
    here = os.getcwd()
    codeDir = os.path.abspath(os.path.join(here))
    defaultAndyroid = '%s %s/andyroid.py' % (sys.executable, codeDir)
    defaultAndyroidPoster = '%s %s/andyroidPoster.py' % (sys.executable, codeDir)
    
    andyroid = os.environ.get('andyroid', defaultAndyroid)
    andyroidPoster = os.environ.get('andyroidPoster', defaultAndyroidPoster)
    
    count = 0
    def runAndPost(inputFile, outputFile=None, label=None, 
                   delta = False,
                   alpha = None, **options):
        global count
        count += 1
        if outputFile is None:
            outputFile = 'andyroid%05d.out' % count
        if label is None: 
            label = inputFile
        clas = "-i %s -o %s" % (inputFile, outputFile)
    
        if delta: 
            clas += " --delta"
    
        if alpha is not None:
            clas += " --alpha %f" % alpha
    
    # Test the code
        t = test(clas=clas, executable=andyroid, label = label, 
                 name="Andyroid", **options)
    
    # Test the postprocessor
    # report = False means omit separate report for postprocessor if it passes.
        testif(t, clas=outputFile, executable=andyroidPoster, label=t.name,
                 report=False, name="AndyroidPoster", keep = 1) 
        return t
    
    define(andyroid=runAndPost)

(We return the test ``t`` in case we later want to have access to it, such as 
making another test depend on it by defining a similar ``runAndPostIf(t, ...)`` 
function.)
    
Now we can define a new file ``testSuite.ats``:: 

    source('andyroid/andyroid.ats')
    andyroid = get('andyroid')
    andyroid('test1.in', label='test1')
    andyroid('test1.in', label='test1d', delta=True)

This will result in ATS running andyroid and then, if successful, andyroidPoster,
with two different labels and values for delta.

We used the value of the argument delta to set the command line arguments, 
but we also set it as a test option. Then, if we want to run only those
tests with ``--delta``, we can do it with a filter::

    ats -f 'delta' suite

.. index::
   pair: group; example

We might also choose to modify this example to include ``group()`` and ``endgroup()`` at the
top and bottom of runAndPost; the group call could set options that we wanted in each 
test statement, and we would save all the output in case of failure of any part of it.

Leveling
========

.. index::
   pair: option; level
   pair: test suite; structuring
   pair: option; stick

ATS has a built-in leveling filter. Using ``stick`` to set a value, you 
can break up tests into levels and execute only those below a certain 
value, or between certain values::

    source('andyroid/andyroid.ats')
    andyroid = get('andyroidTest')

    stick(level=10)
    andyroid('test1.in', label='test1')
    andyroid('test1.in', label='test1d', delta=True)

    stick(level=20)
    andyroid('test2.in', label='test2') 
    andyroid('test2.in', label='big run', delta=True,
            level = 30)

executed with command-lines such as::

    ats --level 10 suite    
    ats -f 'level >= 4 and level =< 12' suite

These two levels, 10 and 20, might correspond to daily and weekly tests
for example. We recommend leaving some room to change your mind.

Introspection
-------------

.. index:: introspection
.. index::
   pair: test suite; structuring
   pair: ``#ATS:``;input
   pair: magic; input

When a file is sourced, the normal action is to execute the contents of that
file using the ATS vocabulary. However, magic is possible! Before explaining
how to do the magic, let's understand the motivation for it.

An expert on the some area of *andyroid* may have a test routine, say "testX.in",
that he uses, running the program with some variety of test inputs. However,
another member of the team will in general not know how to do this. So
it would be nice if the expert had a good way to embed in the test the 
knowledge of what parameters to use to run it, without interfering in 
the ability of the expert to run it by hand in a different way.

Now, strictly speaking you don't have a problem here. You can have 
a separate test file, testX.ats,
and this file can have test lines for each test the expert believes should
be run, perhaps also giving them appropriate levels, time limits, etc.

However, that often leads to having this extra file for absolutely no reason
other than to make this information available to ATS. And so is born the
concept of "introspection": ATS looks inside a file it is about to 
source and discovers that it is both the input file to be tested and 
the instructions on how to test it, the latter appearing to be comments.

For example, assuming *andyroid* uses a "#ATS:" at the start of the line
to denote magic comments, testX.in might look like this::

    #ATS:andyroid(inputFile=SELF, label="testX easy")
    #ATS:andyroid(inputFile=SELF, delta=True, label="testX hard")
    ... body of the testX file

This would cause source("testX.in") to actually create two tests, where 
the word SELF will evaluate to "testX.in". The file will not be further
sourced, so the language used in the rest of it need not be Python.

If you wish to source a file with a different magic commenting convention, 
this is possible -- see the User's Manual explanation of the ``source`` function.

Putting It All Together
-----------------------

The example given here in file ``suite`` is expanded in file ``fancySuite``. 
There you can see use of many of the concepts discussed here and in the advanced
section below. Note that the file begins by sourcing that same andyroid.ats
file that we used before. It then starts the testing with Test/main.ats, which
in turn sources files in directories simple, delta, and psweep.

In directory ``simple`` there is a test that is going to fail. It has been 
given an option "development=True". A default value of False has been given
to the other tests by using a ``glue`` statement in main.ats. Since we used 
``glue`` and not ``stick``, this value persists into the subdirectories.

In directory delta there are some tests that turn on the ``--delta`` option.

In directory psweep we see that in fact psweep.ats is the input file
for Andyroid, but introspection is used to execute it many times with 
different values of alpha. 

***************
Advanced Topics
***************

Modifying ATS itself should rarely be necessary. The techniques in this chapter
show how much you can do with customized drivers and machine specifications.

Expecting Failure
=================

.. index::
   pair: expected; failure
   pair: status; expected

Applying the tilde (~) operator to a test marks it as a test that is expected to 
FAIL. Thus::

    ~test(....)

will be considered to have passed only if it ends up with status FAILED. The
status will be changed to EXPECTED and a entry made in the t.notes list documenting
this fact.  See the reference manual for further details.

Postprocessing
==============

Postprocessing the results of the ATS run can be done using a custom
driver or using the ``onExit`` facility.

Using the Log
=============

.. index:: log

One of the defined vocabulary items is an object named ``log``; it acts like
a function and prints its arguments into the log and / or on the terminal,
space separated and terminated by a newline.  For example, if you put
this in your sourced file::
   
    log('Entering test section', 'foo', echo=True)

then "Entering test section foo" will be printed to the log and to the 
terminal. This may give you a good fuzzy feeling if you are unsure of
what tests are being initiated.

The ``echo`` value controls output to the terminal. Another flag, ``logging``, 
controls whether or not the output is stored in the log.

Using Magic Output
==================

.. index::
   pair: ``#ATS:``; output
   pair: magic; output

When a test writes something to its standard output that begins with
some magic prefix, ATS captures those lines and stores them in the
test object as a list (``test.output``). The lines have their final newline
removed. If the option ``hideOutput`` is True, such output is written in the log
when the test finishes. By default it is False.

The magic output prefix is set in the test's option ``magic``; the default value
is ``#ATS:``.  

.. note:: This differs from the ``magic`` argument to ``source``;
   they have the same default but otherwise are not connected. The ``source`` 
   magic controls the introspection process for input; the ``test`` magic option
   controls the capture of part or all of the output from running the test.

Setting the ``magic`` output prefix to ``None`` prevents any output collection.

The list would be available to any post-processor using ``onExit`` or 
a custom driver. You may wish to set ``--hideOutput`` if you are just 
going to post-process.

Output Magic Example
--------------------

If we define a test with a magic option of "shazam!"::

     test1 = test(executable=something, ..., magic="shazam!")

Suppose the test runs and prints::

    shazam!4.2 6.8

After the test exits, ``test1.output`` is ``["4.2 6.8"]``.

Capturing All The Output
------------------------

.. index::
   pair: magic; output
   single: capturing all output
   pair: magic; empty string

Any test with a ``magic`` option which is an empty string (formed
by using two consecutive single or double quotes) then all the output from
the program is captured and stored in the test's ``output`` attribute.
You can then do something with it via postprocessing or view it in the log.

A Note on Notes
---------------

.. index::
   pair: test; notes

Each test also has an attribute ``notes``, a list of strings. These notes are 
currently used to note that certain things have happened and are used in the
summary of results. You can append strings to this attribute if you wish. 

Making Custom Drivers
=====================

.. _Custom_Drivers:

.. index::
   pair: custom; driver
   pair: custom; command line

The main program ``ats`` is a very short script; stripped of some error
reporting it reads::

    #!/env/bin/python   [this line adjusted on installation]
    import ats
    ats.manager.main()
    
``ats.manager`` is an object that controls the ats run. Before you 
call ``main``, you can do other things such as register ``onExit`` functions. 
You can massage the arguments (``sys.argv[1:]``) and pass the resulting 
**string** as ``main's`` argument. (Python's **shlex** module can help 
manipulate argument lists.).

After ``main`` returns, the master list of tests is ``ats.manager.testlist``.
All the statuses are available as attributes in the ats module.

For example, this driver would add a list of tests that failed in some way
to a database::

    #!/env/bin/python   [make sure it points to ATS's python]
    import ats
    from ats import CREATED, INVALID, FAILED, TIMEDOUT, manager
    manager.main()
    failed = [CREATED, INVALID, FAILED, TIMEDOUT]
    (open the database)
    for test in manager.testlist:
        if test.status in failed:
            (write test.name and details to database)
    (close the database)
 
The task of installing this script alongside the main ats script, and 
adjusting the first line, can be handled with a separate setup.py script or by
editing setup.py to add another script before installing. Change this line
in setup.py::

       scripts = [codename]

to read::

       scripts = [codename, "your_script_name"]

If you need tighter control, instead of calling main you can call its 
constituent parts::

        from ats import manager 
        manager.init(clas)  # note, string argument  
                            # omit clas = use command line
        manager.firstBanner()
        manager.core()
        manager.postprocess()
        manager.finalReport()
        manager.saveResults()
        self.finalBanner()

Here is what those pieces do:

* ``init`` processes the command line and the machine gets defined.
  The function has 3 possible arguments: a command line, and two
  call-back functions for adding and examining command-line options.
* ``firstBanner`` initializes the log -- before this has been called,
  using the ``ats.log`` object will just write to the terminal.
  After this call, the manager vocabulary is "up", so you can
  safely call things like ``glue``, ``define``, ``test``, etc.
* ``core`` does the "phases" of collection, sorting, and execution. 
* ``postprocess`` calls the user's onExit routines.
* ``finalReport`` writes the detailed report.
* ``saveResults`` creates the `atsr.py`` file.
* ``finalBanner`` writes ATS' summaries and exit messages.

Please let the authors know of any needs for further refinement.

The handyAndy Custom Driver
---------------------------

.. index::
   pair: driver; handyAndy

Andyroid has a little custom driver ``handyAndy``. This driver takes care of
the sourcing of ``andyroid.ats`` and does some postprocessing looking for 
failures that did not have the the option ``development`` set to True; these
are true failures. If users used ``handyAndy`` instead of ats itself, the
``source`` - ``get`` procedure could be left out of all the ATS input files.

