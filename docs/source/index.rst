#########################
The Automated Test System
#########################


********************
Purpose and Features
********************

.. index:: ATS features

The Automated Testing System (ATS) is an open-source,  Python-based tool for 
automating the running of tests of an application.  ATS can test any program 
that can signal success or failure via its exit status. 

ATS is distributed, introspective, and scalable. 

* It is distributed in two senses. First, there is no central database
  of tests to run. Tests may be spread over many directories and usually 
  adding a test in a subdirectory is entirely a local operation.  

* Introspective means that a test can be runnable by someone who is not an 
  expert, yet runnable with different arguments by someone who is. An 
  application test may contain within itself, in comments, directions for how to
  run itself in one or more ways.  An expert may run these tests normally using 
  his application; but when ATS runs it, it runs the application according to 
  the special comments within the input.

* Depending on the available resources, the execution of the tests can be done 
  over many processors and hosts, in parallel. Distributed execution and 
  test specification helps ATS stay scalable.

Other features of ATS include:

* A test may depend on another test, and will not be executed
  unless their parent test succeeds.

* Tests may be filtered out (that is, not executed) in many ways. 
  These may include number of processors, time limit, platform, or other 
  user-defined criteria.

* A level may be given to each test, and used to stratify a test suite into 
  subsets of increasing thoroughness.

* ATS is extensible. 
  The ats driver script does almost nothing except import the 
  ats module and call the ats.manager.main() method. It may suit your 
  purposes to make a different driver that does things before or after this
  invocation. The ats script uses the assets of the module ats
  to provide a command line interface-type testing system. Other
  interfaces, such as a GUI interface, are possible. 

* ATS makes it easy in particular to postprocess the results of the testing by 
  registering routines to be executed after the tests have completed, but before
  exiting.  

 * A facility is provided to make it easy to port ATS to new machines
   such as parallel processors and multi-noded distributed machines, or to take 
   advantage of multiple cores. The 'stock' ATS will run up to two tests at 
   once, each of them standard serial jobs (np = 1 in what follows).

While ATS input can be written using the full power of Python, the basic 
operations require only a few statements written in a special vocabulary that 
is not be hard to learn. For example::

    test(executable="/my/path/to/my/code", 
         clas="-input mydeck delta=3", 
         np=3)

executes the given executable with the given command-line arguments (clas),
launching the job is parallel on 3 processors. 

.. index:: function signatures

.. note:: A note on function signatures
   While this document assumes you can learn the basics of Python on your own, 
   function signatures require  careful understanding. In Python, the definition
   of a function parameter can have one or two asterisks in front of a name.
   
   * When calling such a function, in the place of a parameter with one asterisk
     in front of it, you can give zero or more comma-separated values
     as a value, which the function will receive as a list.
   
   * When a parameter name has two asterisks in front of it in the function 
     definition, you can give zero or more comma-separated keyword = value pairs
     when you call it, which the function will receive as a dictionary.
   
   For example, the ATS ``source`` function has the signature::
   
      source(*paths, **vocabulary)
   
   which means any of the following are legitimate calls to it::
   
       source('foo.py')
       source('foo.py', 'goo.py')
       source('foo.py', physics="on", music = "off")
       source(physics="on", music = "off")
       source()
   
   As it happens, the last of these doesn't do anything, but it is a legitimate 
   call. 
   
   .. note:: 
      All of the *paths* arguments must come before the first of the 
      *vocabulary* arguments.

Download and Install
====================

Installation of ATS is easy. Unpack the distribution and in the top-level
directory execute::

   python setup.py install

Public releases are at http://code.google.com/p/ats

The README.txt file contains installation instructions. ATS has been tested with 
Python 2.6 or later, available at http://python.org. 

ATS should translate to Python 3 by using the 2to3 utility but this has not yet been tried.

ATS should work, or be made to work, on any system which can run Python via
a command window. In particular it works out of the box on any Linux or Mac
system. ATS works on Windows but experience there is limited.

History
=======

ATS was written by Paul F. Dubois at Lawrence Livermore National Laboratory,
(LLNL) in about 2003. Although an open-source release was made, the software 
was highly oriented to the LLNL computer systems and one particular simulation, 
ATS has been in continuous use since then.

A revision in 2010-11 has compartmentalized the LLNL-specific system details,
and we have added new features to make the software more generally applicable
and more easily portable. 

The support team at LLNL includes Nu Ai Tang, T. J. Alumbaugh, and Ines Heinz. 
You can contact the author at dubois1@llnl.gov. For help with the LLNL 
features contact tang10@llnl.gov.

ATS was written to test scientific simulations, although it can be used for
any program that can be run with a command-line, does not require interaction,
and which can signal its own success or failure via its exit status (or be 
executed via a shell program with those properties). 

In general scientific programs do not produce predictable printed output, and so 
comparison of output files, so common in the testing literature, is not normally 
useful.They also are generally long-running and resource-consuming; hence ATS 
emphasises filtering, parallel execution, and prioritization under user control.
Provision for supporting batch execution is also provided.

LLNL Notes
==========

.. index:: LLNL-specific features

The LC distribution includes an LC directory containing definitions for the
local machines and the batch system. To make use of the features of LC machines
you will need to set either SYS_TYPE or MACHINE_TYPE. To install the LC machines, run::

    python setup.py install

in the LC directory after you have done so in the main ATS directory.

For help join the mailing list ats@lists.llnl.gov.

About The Documentation
=======================

This document is licensed under the terms of the LICENSE.txt file 
in the ATS distribution.

This documentation is written in reStructuredText, the standard language 
used by the Python documentation project. You should find the source,
available in the distribution, readable even without rendering. It can be if 
desired rendered into plain text files, web pages, PDF files, and other 
formats using the tools of the *Sphinx* project. The source files 
are located in the ``source`` subdirectory of the ``docs`` directory. The
Makefile in the ``docs`` directory will render the documents into 
the ``build`` subdirectory if appropriate parts of Sphinx have been 
installed.

If you install ``setuptools`` into your Python, you can get Sphinx with::

   easy_install -U Sphinx

.. toctree::
   :maxdepth: 3

   andyroid
   ats
   appendix
