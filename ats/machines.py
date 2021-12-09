"""Definition of class Machine for overriding.
"""
import subprocess, sys, os, time, shlex
from ats.atsut import RUNNING, TIMEDOUT, PASSED, FAILED, LSFERROR, \
     SKIPPED, HALTED, AttributeDict, AtsError
from ats.log import log, terminal
from shutil import copytree, ignore_patterns

def comparePriorities (t1, t2):
    "Input is two tests; return comparison based on totalPriority."
    return t2.totalPriority - t1.totalPriority

#-----------------------------------------------------------
# class MachineCore
#-----------------------------------------------------------
class MachineCore(object):
    """Invariable parts of a machine. Not capable of being instantiated"""

    debugClass = False
    canRunNow_debugClass = False
    printExperimentalNotice = False
    printSleepBeforeSrunNotice = True

    # self.numberTestsRunningMax is not really the max number of tests running
    # but is rather the max number of processors which can run tests.
    def label(self):
        return '%s(%d)' % (self.name, self.numberTestsRunningMax)

    def split(self, astring):
        "Correctly split a clas string into a list of arguments for this machine."
        return shlex.split(astring)

    def calculateBasicCommandList(self, test):
        """Prepare for run of executable using a suitable command.
           Returns the plain command line that would be executed on a vanilla
           machine.
        """
        return test.executable.commandList + test.clas

    def examineBasicOptions(self, options):
        "Examine options from command line, possibly override command line choices."
        from ats import configuration
        if configuration.options.sequential:
            self.numberTestsRunningMax = 1
        elif self.hardLimit:
            if options.npMax > 0:
                self.numberTestsRunningMax = options.npMax
        else:
            if options.npMax > 0:
                self.numberTestsRunningMax = options.npMax

    def checkForTimeOut(self, test):
        """ Check the time elapsed since test's start time.  If greater
        then the timelimit, return true, else return false.  test's
        end time is set if time elapsed exceeds time limit """
        from ats import configuration
        timeNow= time.time()
        timePassed= timeNow - test.startTime
        cut = configuration.cuttime
        fraction = timePassed / test.timelimit.value

        #print "DEBUG checkForTimeOut 000"
        #print timeNow
        #print timePassed
        #print test.timelimit.value
        #print cut
        #print fraction
        #print "DEBUG checkForTimeOut 100"
        if (timePassed < 0):         # system clock change, reset start time
            test.setStartTimeDate()
        elif (timePassed >= test.timelimit.value):   # process timed out
            return 1, fraction
        elif cut is not None and timePassed >= cut.value:
            return -1, fraction
        return 0, fraction

    def checkRunning(self):
        """Find those tests still running. getStatus checks for timeout.
        """
        # print "DEBUG checkRunning 100\n"
        from ats import configuration
        time.sleep(self.naptime)
        stillRunning = []
        for test in self.running:
            done = self.getStatus(test)
            if not done:
                stillRunning.append(test)
            else:   # test has finished
                if test.status is not PASSED:
                    if configuration.options.oneFailure:
                        raise AtsError("Test failed in oneFailure mode.")
        self.running = stillRunning

    def remainingCapacity(self):
        """How many processors are free? Could be overriden to answer the real question,
what is the largest job you could start at this time?"""
        return self.numberTestsRunningMax - self.numberTestsRunning

    def getStatus (self, test):
        """
Override this only if not using subprocess (unusual).
Obtains the exit code of the test object process and then sets
the status of the test object accordingly. Returns True if test done.

When a test has completed you must set test.statusCode and
call self.testEnded(test, status). You may add a message as a third arg,
which will be shown in the test's final report.
testEnded will call your bookkeeping method noteEnd.
"""
        from ats import configuration
        test.child.poll()
        #print test.child.returncode
        if test.child.returncode is None:
            overtime, fraction = self.checkForTimeOut(test)
            #print "DEBUG getStatus 100"
            #print overtime
            #print fraction
            #print "DEBUG getStatus 200"
            if fraction > .9 or overtime != 0:
                # If a process produces a lot of output, it may fill its output
                # buffer and then block until something is read from it.

                # How should testStdout handle this? ???
                #
                # 2017-08-15 SAD putting back in poll, to see if it fixes hang.
                if configuration.SYS_TYPE.startswith('somesystemxxx'):
                    stdoutdata, stderrdata = test.child.communicate()

                # Now, poll it again.
                test.child.poll()


        if test.child.returncode is None: #still running, but too long?
            overtime, fraction = self.checkForTimeOut(test)
            #print "DEBUG getStatus 300"
            #print overtime
            #print fraction
            #print "DEBUG getStatus 400"
            if overtime != 0:
                self.kill(test)
                test.statusCode=2
                test.setEndDateTime()
                if overtime > 0:
                    status = TIMEDOUT
                else:
                    status = HALTED  #one minute mode
            else:
                #print "DEBUG getStatus 320"
                # SAD
                # Coding to detect SLURM deficiencies, and abort job.
                # Implemented 2016-Aug-30
                slurm_error = False;
                f = open( test.errname, 'r')
                lines = f.readlines()
                f.close
                for line in lines:
                    if slurm_error == False:
                        if "Slurmd could not set up environment for batch job" in line:
                            print("ATS Halting test %s. Detected slurm launch failure : %s " % (test.name, line))
                            slurm_error = True
                        elif "srun: error: Unable to create job step" in line:
                            print("ATS Halting test %s. Detected slurm error : %s " % (test.name, line))
                            slurm_error = True
                        elif "Error opening remote shared memory object in shm_open" in line:
                            print("ATS Halting test %s. Detected MPI shared memory failure : %s " % (test.name, line))
                            slurm_error = True
                        elif "PSM could not set up shared memory segment" in line:
                            print("ATS Halting test %s. Detected MPI shared memory failure : %s " % (test.name, line))
                            slurm_error = True
                        elif "Attempting to use an MPI routine before initializing MPICH" in line:
                            print("ATS Halting test %s. Detected MPI Error : %s " % (test.name, line))
                            slurm_error = True
                        elif "Bus error)" in line:
                            print("ATS Halting test %s. Detected Bus Error (perhaps MPI related) : %s " % (test.name, line))
                            slurm_error = True

                if slurm_error:
                    self.kill(test)
                    test.statusCode=2
                    test.setEndDateTime()
                    status = HALTED

                else:
                    return False
        else:
            # print "DEBUG getStatus 400"
            test.setEndDateTime()
            test.statusCode = test.child.returncode
            # If the user set ignoreReturnCode to True then set statusCode to 0.
            ignoreReturnCode  = test.options.get('ignoreReturnCode', False)
            if ignoreReturnCode:
                test.statusCode = 0
            if test.statusCode == 0:                               # process is done
                status = PASSED
            else:
                # Coding to detect LSF deficiencies
                # Implemented 2018-12-12
                lsf_error = False;
                f = open( test.errname, 'r')
                lines = f.readlines()
                f.close
                for line in lines:
                    if lsf_error == False:
                        if "Terminated while pending" in line:
                            print("ATS Detected LSF Job Start Error %s.  Detected LSF launch failure : %s " % (test.name, line))
                            lsf_error = True
                        elif "JSM daemon timed" in line:
                            print("ATS Detected LSF Job Start Error %s.  Detected LSF launch failure : %s " % (test.name, line))
                            lsf_error = True
                            #time.sleep(10)      # See if sleeiping helps the JSM daemon recover
                        elif "Error initializing RM" in line:
                            print("ATS Detected LSF Job Start Error %s.  Detected LSF launch failure : %s " % (test.name, line))
                            lsf_error = True
                            #time.sleep(10)      # See if sleeiping helps the JSM daemon recover
                        elif "Bus error)" in line:
                            print("ATS Halting test %s. Detected Bus Error (perhaps MPI related) : %s " % (test.name, line))
                            lsf_error = True

                if not lsf_error:
                    f = open( test.outname, 'r')
                    lines = f.readlines()
                    f.close
                    for line in lines:
                        if lsf_error == False:
                            if "Error: Locate pipe file" in line:
                                print("ATS Detected LSF Job Start Error %s.  Detected LSF launch failure : %s " % (test.name, line))
                                lsf_error = True
                            elif "Could not read jskill" in line:
                                print("ATS Detected LSF Job Scheduler Error %s.  : %s " % (test.name, line))
                                lsf_error = True
                            elif "Error initializing RM" in line:
                                print("ATS Detected LSF Job Start Error %s.  Detected LSF launch failure : %s " % (test.name, line))
                                lsf_error = True


                #sys.exit(-1) SAD ambyr
                #print "DEBUG getStatus 420 statusCode is %d " % test.statusCode
                if lsf_error:
                    print("ATS LSF Development: LSFE Detected statusCode is %d " % test.statusCode)
                    test.statusCode=2
                    test.setEndDateTime()
                    status = LSFERROR

                else:
                    status= FAILED


        # Send test's stdout/stderr to file and to terminal
        if test.stdOutLocGet() == 'both':
            outhandle, errhandle = test.fileHandleGet()
            for line in test.child.stdout:
                print(line)
                print(line, file=outhandle)

        self.testEnded(test, status)

        #if hasattr(test, 'runningWithinSalloc'):
        #    if test.runningWithinSalloc == True:
        #        print "DEBUG Sleeping 1 sec after job end %s" % test.name
        #        time.sleep(1)

        return True

    def testEnded(self, test, status):
        """Do book-keeping when a job has exited;
call noteEnd for machine-specific part.
"""
        from ats import configuration
        if MachineCore.debugClass:
            print("DEBUG MachineCore.testEnded invoked cwd= %s " % (os.getcwd()))

        globalPostrunScript_outname = test.globalPostrunScript_outname
        globalPostrunScript         = test.options.get('globalPostrunScript', None)
        #verbose                     = test.options.get('verbose', False)
        verbose                     = configuration.options.debug

        if not (globalPostrunScript == "unset"):
            here = os.getcwd()
            os.chdir( test.directory )
            if os.path.exists( globalPostrunScript ):
                self._executePreOrPostRunScript( globalPostrunScript, test, verbose, globalPostrunScript_outname )
            else:
                log("ERROR: globalPostrunScript %s not found" % (globalPostrunScript), echo=True)
                sys.exit(-1)
            os.chdir( here )

        self.numberTestsRunning -= 1
        if MachineCore.debugClass or MachineCore.canRunNow_debugClass:
            print("DEBUG MachineCore.testEnded decreased self.numberTestsRunning by 1 to %d " % self.numberTestsRunning)

        #if num_nodes' in test.__dict__:
        #    num_nodes = test.__dict__.get('num_nodes')
        #    self.numberNodesExclusivelyUsed -= num_nodes
        #    print "MachineCore.testEnded decreased self.numberNodesExclusivelyUsed by %d to %d " % \
        #        (num_nodes, self.numberNodesExclusivelyUsed)

        if test.numNodesToUse > 0:
            self.numberNodesExclusivelyUsed -= test.numNodesToUse
            if MachineCore.debugClass or MachineCore.canRunNow_debugClass:
                print("DEBUG MachineCore.testEnded decreased self.numberNodesExclusivelyUsed by %d to %d (max is %d)" %
                      (test.numNodesToUse, self.numberNodesExclusivelyUsed, self.numNodes))

        test.set(status, test.elapsedTime())
           #note test.status is not necessarily status after this!
           #see test.expectedResult

        self.noteEnd(test)  #to be defined in children

        # now close the outputs
        if test.stdOutLocGet() != 'terminal':
            test.fileHandleClose()

        self.scheduler.testEnded(test)

    def kill(self, test): # override if not using subprocess
        "Kill the job running test."
        if test.child:
            test.child.kill()
            if test.stdOutLocGet() != 'terminal':
                test.fileHandleClose()

    def launch (self, test):
        """Start executable using a suitable command.
           Return True if able to do so.
           Call noteLaunch if launch succeeded."""

        from ats import configuration
        #print test.__dict__
        ##print self.__dict__

        nosrun  = test.options.get('nosrun', False)
        serial  = test.options.get('serial', False) # support serial=True on a per-test basis for backwards compatability for a while
        if nosrun == True or serial == True:
            test.commandList = self.calculateBasicCommandList(test)
            test.cpus_per_task = 1
        else:
            test.commandList = self.calculateCommandList(test)
            if  test.commandList==None:
                log("ATS def launch returning false, commandList is None", echo=True)
                return False

        #
        # On Blueos (Sierra/Ansel) Set JSM_JSRUN_NO_WARN_OVERSUBSCRIBE the same as lrun does
        #
        if configuration.SYS_TYPE.startswith('blueos'):
            os.environ['JSM_JSRUN_NO_WARN_OVERSUBSCRIBE'] = '1'

        # To enable running of threaded codes in 1 thread mode, the OMP_NUM_THREADS must be
        # set either by the user before the run, or by the test 'nt' option, or by
        # the command line option to ATS --ompNumThreads.  If none of these are set, then
        # set it to 1.
        if configuration.options.ompNumThreads > 0:
            # Priority 1 setting, ats command line
            if configuration.options.verbose:
                print("ATS launch setting OMP_NUM_THREADS %d as user specified --ompNumThreads=%d" %
                      (configuration.options.ompNumThreads, configuration.options.ompNumThreads))
            os.environ['OMP_NUM_THREADS'] = str(configuration.options.ompNumThreads)
        else:
            # Priority 2  setting, within an ATS test line
            omp_num_threads = test.options.get('nt', -1)
            if (omp_num_threads > 0):
                if configuration.options.verbose:
                    print("ATS launch setting OMP_NUM_THREADS %d based on test 'nt'option" % omp_num_threads)
                os.environ['OMP_NUM_THREADS'] = str(omp_num_threads)
            else:
                # Priority 3 setting, the user has already set OMP_NUM_THREADS in their environment
                if 'OMP_NUM_THREADS' in os.environ:
                    if configuration.options.verbose:
                        temp_omp= os.getenv("OMP_NUM_THREADS")
                        # print "ATS detected that OMP_NUM_THREADS is already set to %s" % (temp_omp)
                # Priority 4 setting, set it to 1 if it is not othewise set
                else:
                    if configuration.options.verbose:
                        print("ATS launch setting OMP_NUM_THREADS 1 by default for as it was not specified for the test.")
                        # print "    This should allow for threaded applications to run with non threaded tests with a single thread."
                    os.environ['OMP_NUM_THREADS'] = str(1)

        # Set default KMP_AFFINITY so that OpenMP runs are OK on Toss 3
        # This is experimental for now.
        if configuration.SYS_TYPE.startswith('toss'):
            if MachineCore.printExperimentalNotice:
                MachineCore.printExperimentalNotice = False
                print("ATS Experimental: setting KMP_AFFINITY to %s on Toss" % configuration.options.kmpAffinity)
            os.environ['KMP_AFFINITY'] = configuration.options.kmpAffinity

        # Turn off shared memory mpi collective operations on toss and chaos
        if configuration.SYS_TYPE.startswith('toss'):
            os.environ['VIADEV_USE_SHMEM_COLL'] = "0"

        if configuration.SYS_TYPE.startswith('chaos'):
            os.environ['VIADEV_USE_SHMEM_COLL'] = "0"

        # LS_COLORS can mess up somesystem and is not needed for any platform by ATS
        os.environ['LS_COLORS'] = ""

        # Bamboo env vars can also mess up somesystem runs by exceeding char limit for env vars
        # remove them
        os.environ['bamboo_shortJobName'] = ""
        os.environ['bamboo_capability_system_git_executable'] = ""
        os.environ['bamboo_build_working_directory'] = ""
        os.environ['bamboo_shortPlanKey'] = ""
        os.environ['bamboo_planName'] = ""
        os.environ['bamboo_capability_system_jdk_JDK_1_8_0_71'] = ""
        os.environ['bamboo_buildKey'] = ""
        os.environ['bamboo_capability_system_jdk_JDK'] = ""
        os.environ['bamboo_capability_sys_type'] = ""
        os.environ['bamboo_capability_cluster'] = ""
        os.environ['bamboo_buildFailed'] = ""
        os.environ['bamboo_buildResultKey'] = ""
        os.environ['bamboo_plan_storageTag'] = ""
        os.environ['bamboo_planKey'] = ""
        os.environ['bamboo_capability_system_builder_ant_Ant'] = ""
        os.environ['bamboo_shortPlanName'] = ""
        os.environ['bamboo_buildResultsUrl'] = ""
        os.environ['bamboo_buildPlanName'] = ""
        os.environ['bamboo_working_directory'] = ""
        os.environ['bamboo_agentWorkingDirectory'] = ""
        os.environ['bamboo_buildTimeStamp'] = ""
        os.environ['bamboo_shortJobKey'] = ""
        os.environ['bamboo_buildNumber'] = ""
        os.environ['bamboo_agentId'] = ""
        os.environ['bamboo_capability_system_jdk_JDK_1_8'] = ""
        os.environ['bamboo_resultsUrl'] = ""

        test.commandLine = " ".join(test.commandList)

        sandbox        = test.options.get('sandbox', False)
        directory      = test.options.get('directory', None)
        deck_directory = test.options.get('deck_directory', None)

        if sandbox:
            # directory is the name of the sandbox directory
            if directory == None or directory == '':
                directory = ('%s_%d_%04d_%s') % ('sandbox', os.getpid(), test.serialNumber, test.namebase)

            if deck_directory == None or deck_directory == '':
                deck_directory = os.getcwd()

            if not os.path.isdir( directory ) :

                if MachineCore.debugClass:
                    print("MachineCore.launch \n\tcwd=%s \n\tdir=%s \n\tdeck_directory=%s" %
                          (os.getcwd(), directory, deck_directory))

                log("ATS machines.py Creating sandbox directory : %s" % directory, echo=True)
                copytree(deck_directory, directory, ignore=ignore_patterns('*.logs', 'html', '.svn', '*sandbox*'))


        #--- placing this here doesn't allow the machines to handle the skip option themselves..
        if configuration.options.skip:
            test.set(SKIPPED, "--skip option")
            return False

        test.setStartDateTime()
        result = self._launch(test)
        if result:
            self.noteLaunch(test)

        return result

    def __results(self, key, default, results, options):
        val = results.get(key, default)
        if val == default:
            val = options.get(key, default)
        return val

    def log_prepend(self, test, outhandle):
        # Prepend information about the test to its standard output
        magic = test.options.get('magic', '#ATS:')
        results = test.getResults()

        commandLine = self.__results('commandLine', '', results, test.options)
        print("%scommandLine =%s" % (magic, commandLine), file=test.outhandle)

        if hasattr(test, 'rs_filename'):
            if os.path.isfile(test.rs_filename):
                myfile = open(test.rs_filename, mode='r')
                all_of_it = myfile.read()
                myfile.close()
                print("%sjsrun_rs =\n%s" % (magic, all_of_it), file=test.outhandle)

        directory = self.__results('directory', '', results, test.options)
        print("%sdirectory =%s" % (magic, directory), file=test.outhandle)

        executable = self.__results('executable', '', results, test.options)
        print("%sexecutable =%s" % (magic, executable), file=test.outhandle)

        name = self.__results('name', '', results, test.options)
        print("%sname =%s" % (magic, name), file=test.outhandle)

        clas = self.__results('clas', '', results, test.options)
        print("%sclas =%s" % (magic, clas), file=test.outhandle)

        np = self.__results('np', 1, results, test.options)
        print("%snp =%s" % (magic, np), file=test.outhandle)

        script = self.__results('script', '', results, test.options)
        print("%sscript =%s" % (magic, script), file=test.outhandle)

        testpath = self.__results('testpath', '', results, test.options)
        print("%stestpath =%s\n" % (magic, testpath), file=test.outhandle)

        test.outhandle.flush()
        os.fsync(test.outhandle.fileno())

    def _launch(self, test):
        """Replace if not using subprocess (unusual).
The subprocess part of launch. Also the part that might fail.
"""
        if MachineCore.debugClass:
            print("DEBUG MachineCore._launch invoked cwd= %s " % os.getcwd())
            #print self
            #print test
            #print test.options
            #print test.__dict__
            #print self.__dict__


        from ats import configuration
        # See if user specified a file to use as stdin to the test problem.
        stdin_file                  = test.options.get('stdin', None)
        globalPrerunScript_outname  = test.globalPrerunScript_outname
        globalPrerunScript          = test.options.get('globalPrerunScript', None)
        #verbose                     = test.options.get('verbose', False)
        verbose                     = configuration.options.debug


        if not (globalPrerunScript == "unset"):
            here = os.getcwd()
            os.chdir( test.directory )
            if os.path.exists( globalPrerunScript ):
                self._executePreOrPostRunScript( globalPrerunScript, test, verbose, globalPrerunScript_outname )
            else:
                log("ERROR: globalPrerunScript %s not found" % (globalPrerunScript), echo=True)
                sys.exit(-1)
            os.chdir( here )

        try:
            Eadd    = test.options.get('env', None)
            if Eadd is None:
                E = None
            else:
                # This is old Paul DuBois coding, with ugly syntax.
                #
                # That is the syntax for the user within a 'test' or #ATS line is:
                # env={'ANIMAL': 'duck', 'CITY': 'Seattle', 'PLANET': 'Venus'}
                #
                # The apparent reason for this ugliness, is that is how the environment
                # object is stored in Python.  So it amakes the coding easier
                # here, but it shifts the burden to the user to get that syntax correct,
                # including the brackets, quotes, commans, and colons.
                #
                # Will live with this for now, but would really like this to be more human friendly
                #
                # env="ANIMAL=duck, CITY=Seattle, PLANET=Venus"
                #
                if MachineCore.debugClass:
                    print("DEBUG MachineCore._launch env specified =  %s " % Eadd)
                E = os.environ.copy()
                E.update(Eadd)

            testStdout = test.stdOutLocGet()

            if stdin_file is None:
                #print "DEBUG MachineCore._launch 010 "
                testStdin = None
            else:
                #print "DEBUG MachineCore._launch 020 "
                testStdin = open(test.directory + '/' + stdin_file)

            # 2016-09-01
            # Starting jobs too fast confuses slurm and MPI.  Short wait between each job submittal
            # This showsd up with my atsHello test program
            # Default sleep is 1 on toss, 0 on other systems, may be set by user on command line
            # 2016-12-02
            # Default sleep is now 0 on all systems.
            if hasattr(test, 'runningWithinSalloc'):
                if configuration.options.sleepBeforeSrun > 0:
                    if MachineCore.printSleepBeforeSrunNotice:
                        MachineCore.printSleepBeforeSrunNotice = False
                        print("ATS Info: MachineCore._launch Will sleep %d seconds before each srun " % configuration.options.sleepBeforeSrun)
                    time.sleep(configuration.options.sleepBeforeSrun)
            else:
                if configuration.options.sleepBeforeSrun > 0:
                    if MachineCore.printSleepBeforeSrunNotice:
                        MachineCore.printSleepBeforeSrunNotice = False
                        print("ATS Info: MachineCore._launch Will sleep %d seconds before each srun " % configuration.options.sleepBeforeSrun)
                    time.sleep(configuration.options.sleepBeforeSrun)


            if testStdout == 'file':
                # Get the file handles for standard out and standard error
                outhandle, errhandle = test.fileHandleGet()

                # Prepend information about the test to its standard output
                self.log_prepend(test, test.outhandle)

                if stdin_file is None:
                # SAD ambyr
                #print "DEBUG MachineCore._launch 050 "
                #print "DEBUG MachineCore._launch %s " % test.commandList
                #print E
                #test.child = subprocess.Popen(test.commandList, cwd=test.directory, stdout=outhandle, stderr=errhandle, env=E, text=True)
                    test.child = subprocess.Popen(test.commandList, universal_newlines=True, cwd=test.directory, stdout=outhandle, stderr=errhandle, env=E, text=True)
                    #test.child.wait()
                else:
                    #print "DEBUG MachineCore._launch 110 "
                    #print testStdin
                    #print "DEBUG MachineCore._launch 120 test.directory = %s" % test.directory
                    test.child = subprocess.Popen(test.commandList, cwd=test.directory, stdout = outhandle, stderr = errhandle, env=E, stdin=testStdin, text=True)

            elif testStdout == 'terminal':
                if MachineCore.debugClass:
                    print("DEBUG MachineCore._launch Invoking Popen 2 %s " % test.commandList)


                if stdin_file is None:
                    test.child = subprocess.Popen(test.commandList, cwd=test.directory, env=E, text=True)
                else:
                    test.child = subprocess.Popen(test.commandList, cwd=test.directory, env=E, stdin=testStdin, text=True)

            elif testStdout == 'both':
                # Get the file handles for standard out and standard error
                outhandle, errhandle = test.fileHandleGet()

                # Prepend information about the test to its standard output
                self.log_prepend(test, test.outhandle)

                if MachineCore.debugClass:
                    print("DEBUG MachineCore._launch Invoking Popen 3 %s " % test.commandList)

                if stdin_file is None:
                    test.child = subprocess.Popen(test.commandList, cwd=test.directory, stdout = subprocess.PIPE, stderr=subprocess.STDOUT, env=E, text=True)
                else:
                    test.child = subprocess.Popen(test.commandList, cwd=test.directory, stdout = subprocess.PIPE, stderr=subprocess.STDOUT, env=E, stdin=testStdin)

            test.set(RUNNING, test.commandLine)

            self.running.append(test)
            self.numberTestsRunning += 1
            if MachineCore.debugClass or MachineCore.canRunNow_debugClass:
                print("DEBUG MachineCore.testEnded increased self.numberTestsRunning by 1 to %d " % self.numberTestsRunning)

            if test.numNodesToUse > 0:
                self.numberNodesExclusivelyUsed += test.numNodesToUse
                if MachineCore.debugClass or MachineCore.canRunNow_debugClass:
                    print("DEBUG MachineCore._launch__ increased self.numberNodesExclusivelyUsed by %d to %d (max is %d)" %
                          (test.numNodesToUse, self.numberNodesExclusivelyUsed, self.numNodes))

            return True

        except OSError as e:
            if test.stdOutLocGet() != 'terminal':
                test.fileHandleClose()

            test.set(FAILED, str(e))
            return False

    def startRun(self, test):
        """For interactive test object, launch the test object.
           Return True if able to start the test.
        """
        if MachineCore.debugClass:
            print("DEBUG MachineCore.startRun invoked")
        self.runOrder += 1
        test.runOrder = self.runOrder
        return self.launch(test)

    def _execute(self, cmd_line, verbose=False, file_name=None, exit=True):
        """
        Function to run a command and display output to screen.
        """

        if file_name is not None:
            execute_ofp = open(file_name, 'w')

        process = subprocess.Popen(cmd_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        # Poll process for new output until finished
        while True:
            nextline = process.stdout.readline()
            if (nextline == '' and process.poll() != None):
                break
            if (verbose == True):
                sys.stdout.write(nextline)
                # sys.stdout.flush()
            if file_name is not None:
                execute_ofp.write(nextline)

        output = process.communicate()[0]
        exitCode = process.returncode

        if file_name is not None:
            execute_ofp.close()

        if (exitCode == 0):
            pass
        else:
            if exit:
                log('%s FATAL RETURN CODE %d Command: %s' % ("ATS", exitCode, cmd_line), echo=True)
                raise SystemExit(1)

        return exitCode

    def _executePreOrPostRunScript(self, cmd_line, test, verbose=False, file_name=None, exit=True):
        """
        Function to run a command and display output to screen.  The test dictionary is passed in as a string
        """

        #print "AMBYR"
        #for key in test.__dict__:
        #   print "test key ", key, " is ", test.__dict__[key]
        #print "ONDRE"

        my_executable  = str(test.__dict__["executable"])
        my_commandLine = str(test.__dict__["commandLine"])
        my_np = str(test.__dict__["np"])
        my_outname = str(test.__dict__["outname"])
        my_directory = str(test.__dict__["directory"])

        if file_name is not None:
            execute_ofp = open(file_name, 'w')

        process = subprocess.Popen(cmd_line + \
            " " + '"' + my_executable + '"' + \
            " " + '"' + my_np + '"' + \
            " " + '"' + my_directory + '"' + \
            " " + '"' + my_outname + '"' + \
            " " + '"' + my_commandLine + '"', \
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        # Poll process for new output until finished
        while True:
            nextline = process.stdout.readline()
            if (nextline == '' and process.poll() != None):
                break
            if (verbose == True):
                sys.stdout.write(nextline)
                # sys.stdout.flush()
            if file_name is not None:
                execute_ofp.write(nextline)

        output = process.communicate()[0]
        exitCode = process.returncode

        if file_name is not None:
            execute_ofp.close()

        if (exitCode == 0):
            pass
        else:
            if exit:
                log('%s FATAL RETURN CODE %d Command: %s' % ("ATS", exitCode, cmd_line), echo=True)
                raise SystemExit(1)

        return exitCode



#### end of MachineCore

#-----------------------------------------------------------
# class Machine
#-----------------------------------------------------------
class Machine (MachineCore):
    """Class intended for override by specific machine environments.
Some methods are possible overrides.
Usually the parent version should be called too.
To call the parent version of foo: super(YourClass, self).foo(args)
However, the most important methods have a "basic" verison you can just call.
You can call your class anything, just put the correct comment line at
the top of your machine. See documentation for porting.
"""
    def __init__(self, name, npMaxH):
        """Be sure to call this from child if overridden

Initialize this machine. npMax supplied by __init__, hardware limit.
If npMax is negative, may be overridden by command line. If positive,
is hard upper limit.
"""

        # print "DEBUG Machine:MachineCore %s %d" % (name, npMaxH)

        self.name =  name
        self.numberTestsRunning = 0
        self.numberNodesExclusivelyUsed = 0
        self.numberTestsRunningMax = max(1, abs(npMaxH))
        self.numNodes = -1
        self.npMaxH= npMaxH    # allow the machine modules to access this value
        self.hardLimit = (npMaxH > 0)
        self.naptime = 0.2 #number of seconds to sleep between checks on running tests.
        self.running = []
        self.runOrder = 0
        from ats import schedulers
        self.scheduler = schedulers.StandardScheduler()
        self.init()


    def init(self):
        "Override to add any needed initialization."
        pass

    def addOptions(self, parser):
        "Override to add  options needed on this machine."
        pass

    def examineOptions(self, options):
        """Examine options from command line, possibly override command line choices.
           Always call examineBasicOptions
        """
        self.examineBasicOptions(options)


    def calculateCommandList(self, test):
        """Prepare for run of executable using a suitable command.
If overriding, get the vanilla one from ``calculateBasicCommand``,
then modify if necessary.
        """
        return self.calculateBasicCommandList(test)

    def periodicReport(self):
        "Make the machine-specific part of periodic report to the terminal."
        terminal(len(self.running), "tests running on", self.numberTestsRunning,
              "of", self.numberTestsRunningMax, "processors.")

    def canRun(self, test):
        """
A child will almost always replace this method.

Is this machine able to run the test interactively when resources become
available?  If so return ''.

Otherwise return the reason it cannot be run here.
"""
        if test.np > 1:   #generic machine sequential only
            return "Too many processors needed (%d)" % test.np
        return ''

    def canRunNow(self, test):
        """
A child will almost replace this method. No need to call parent version.

Is this machine able to run this test now? Return True/False.
If True is returned, an attempt will be made to launch. noteLaunch will be
called if this succeeds.
"""
        return self.numberTestsRunning  + 1 <= self.numberTestsRunningMax

    def noteLaunch(self, test):
        """
A child will almost replace this method. No need to call parent version.

test has been launched. Do your bookkeeping. numberTestsRunning has already
been incremented.
"""
        pass

    def noteEnd(self, test):
        """
A child will almost replace this method. No need to call parent version.

test has finished running. Do any bookkeeping you need. numberTestsRunning has
already been decremented.
"""
        pass

    def quit(self):
        """
A child might replace this method. No need to call parent version.
Final cleanup if any.
        """
        pass





    def getResults(self):
        """
A child might replace this to put more information in the results,
but probaby wants to call the parent and then update the
dictionary this method returns.

Return AttributeDict of machine-specific facts for manager postprocessing state.
Include results from the scheduler.
"""
        result = AttributeDict()
        result.update(self.scheduler.getResults())
        result.update(
           dict(name=self.name,
           numberTestsRunningMax = self.numberTestsRunningMax,
           hardLimit = self.hardLimit,
           naptime = self.naptime)
           )
        return result

#-----------------------------------------------------------
# class BatchFacility
#-----------------------------------------------------------
class BatchFacility(object):
    """Interface to a batchmachine"""
    def init(self):
        pass

    def getResults(self):
        "Return machine-specific facts for manager postprocessing state."
        return AttributeDict(name=self.label())

    def label(self):
        "Return a name for this facility."
        return ''

    def addOptions(self, parser):
        "Add batch options to command line (see optparser)"
        pass

    def examineOptions(self, options):
        "Examine the options."
        pass

    def load(self, testlist):
        "Execute these tests"
        return

    def quit(self):
        "Called when ats is done."
        pass


#-----------------------------------------------------------
# class BatchSimulator
#-----------------------------------------------------------
class BatchSimulator(BatchFacility):
    """
A fake batch you can use for debugging input by setting::

    BATCH_TYPE=batchsimulator

"""
    def label(self):
        return "BatchSimulator"

    def __init__(self, name, npMaxH):
        self.name =  name
        self.npMaxH = npMaxH
        self.np = npMaxH

    def load(self, batchlist):
        "Simulate the batch system"
        log("Simulation of batch load:",  echo=True)
        for t in batchlist:
            log(t, echo=True)
