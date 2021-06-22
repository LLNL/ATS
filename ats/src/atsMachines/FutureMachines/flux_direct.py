#ATS:flux                  SELF FluxDirect  800000
"""A flux machine for ATS
"""
from __future__ import print_function
from ats import machines, debug, atsut
from ats import log, terminal
from ats import configuration
from ats.atsut import RUNNING, TIMEDOUT, PASSED, FAILED, BATCHED, CREATED, SKIPPED, HALTED, EXPECTED, statuses, AtsError
from ats import schedulers

import sys, os, time, json
import thread
import errno

import flux
import flux.kvs as kvs
import flux.jsc as jsc

import lcMachines


class FluxScheduler (schedulers.StandardScheduler):
    pass

def run_broker(flux_handle):
    flux_handle.reactor_run(flux_handle.get_reactor(), 0)

def update_test_status(json_response, arg, errnum):
    #print >>sys.stderr, "RECEIVED RESPONSE"
    #print >>sys.stderr, "JSON", json_response
    response = json.loads(json_response)
    #print >>sys.stderr, response, jsc.job_num2state(response['state-pair']['nstate'])
    test_to_update = arg.submitted.get(response['jobid'], None)
    if test_to_update is None:
        print("GOT UNEXPECTED RESPONSE %s" % response)
        return
    new_state = response['state-pair']['nstate']
    if new_state >= jsc.lib.J_NULL and new_state < jsc.lib.J_RUNNING:
        test_to_update.fluxStatus = 'submitted'
        test_to_update.set(RUNNING, "Submitted, pending allocation") #not really true... but as close as they come
    elif new_state == jsc.lib.J_RUNNING:
        if test_to_update.fluxStatus != 'running':
            arg.running.append(test_to_update)
            with kvs.get_dir(arg.fh, test_to_update.kvs_path) as d:
                test_to_update.startTime = float(d['running-time'])
        test_to_update.fluxStatus = 'running'
        test_to_update.set(RUNNING, test_to_update.commandLine)
    elif new_state > jsc.lib.J_RUNNING and new_state != jsc.lib.J_COMPLETING:
        if test_to_update.fluxStatus != 'done':
            arg.running.remove(test_to_update)
            arg.submitted.pop(test_to_update.job_id, None)
        test_to_update.fluxStatus = 'done'
        status = HALTED # test is done, pre-set to a did-not-run state # TODO: see if this is the right code for this
        if new_state == jsc.lib.J_COMPLETE:
            # flux says it ran ok, check return code
            with kvs.get_dir(arg.fh, test_to_update.kvs_path) as d:
                try:
                    exit_status = d['exit_status']
                except:
                    exit_status = 5
                    for k in d:
                        print("LWJ KVS DEBUG %s=%s" % (k, d[k]))
                test_to_update.endTime = float(d['complete-time'])
                if exit_status['min'] == exit_status['max'] and exit_status['min'] == 0:
                    status = PASSED
                else:
                    status = FAILED
        else:
            # it didn't run ok, don't check anything else
            if configuration.options.oneFailure:
                raise AtsError, "Test failed in oneFailure mode."
        print("UPDATING TEST STATUS TO %s" % status, file=sys.stderr)
        test_to_update.set(status, test_to_update.elapsedTime())
        arg.noteEnd(test_to_update)

# class FluxDirect (machines.Machine):
class FluxDirect (lcMachines.LCMachineCore):
    def __init__(self, name, npMaxH):
        self.submitted = dict()
        self.fh = flux.Flux()
        jsc.notify_status(self.fh, update_test_status, self)
        # self.broker_thread = thread.start_new_thread(run_broker, (self.fh,))
        self.cores = 0
        max_cores = 0
        self.numNodes = 0
        self.numberCoresInUse = 0
        with kvs.get_dir(self.fh, 'resource.hwloc.by_rank') as d:
            for name, rankdir in d.items():
                max_cores = max(max_cores, rankdir['Core'])
                self.cores += rankdir['Core']
                self.numNodes += 1
        self.npMax = max_cores
        # initialize the upper versions with the real core count
        super(FluxDirect, self).__init__(name, self.cores)
        # self.numberTestsRunningMax = 1 # TODO: REMOVE THIS DEBUG VALUE self.cores * 2 # for flux, this is number in the scheduling queue
        self.numberTestsRunningMax = 1000 # for flux, this is number in the scheduling queue
        self.scheduler = FluxScheduler()
        self.timer = self.fh.timer_watcher_create(
                after=self.naptime,
                repeat=self.naptime,
                callback=lambda fh, y, z, w:
                    fh.reactor_stop(fh.get_reactor()))
        self.timer.start()

    def addOptions(self, parser):

        "Add options needed on this machine."
        parser.add_option("--partition", action="store", type="string", dest='partition',
            default = 'pdebug',
            help = "Partition in which to run jobs with np > 0")

        parser.add_option("--numNodes", action="store", type="int", dest='numNodes',
           default = 2,
           help="Number of nodes to use")

        parser.add_option("--distribution", action="store", type="string", dest='distribution',
           default = 'unset',
           help="srun distribution of mpi processes across nodes")

    def getNumberOfProcessors(self):
        return self.cores

    def label(self):
        return "FluxDirect: %d nodes, %d processors per node." % (
            self.numNodes, self.npMax)

    def calculateCommandList(self, test):
        """Prepare for run of executable using a suitable command. First we get the plain command
         line that would be executed on a vanilla serial machine, then we modify it if necessary
         for use on this machines.
        """

        np                 = max(test.np, 1)
        test.cpus_per_task = 1
        commandList        = self.calculateBasicCommandList(test)
        timeNow            = time.strftime('%H%M%S',time.localtime())
        test.jobname       = "t%d_%d%s%s" % (np, test.serialNumber, test.namebase[0:50], timeNow)
        minNodes           = np / self.npMax + (np % self.npMax != 0 )

        num_nodes = test.options.get('nn', -1)

        #NOTE: this only works with a sub-instance per job, but it's the closest thing we have
        clist = ["flux", "wreckrun", "-n %i" % np , ]

        if num_nodes > 0:
            test.numNodesToUse = num_nodes
            clist.append("-N %i" % (num_nodes))

        clist.extend(commandList)
        return clist

    def canRun(self, test):
        """Is this machine able to run the test interactively when resources become available?
           If so return ''.  Otherwise return the reason it cannot be run here.
        """
        np = max(test.np, 1)
        if np > self.cores:
            return "Too many processors needed (%d)" % np

        return ''

    def startRun(self, test):
        """For interactive test object, launch the test object.
           Return True if able to start the test.
        """
        self.runOrder += 1
        test.runOrder = self.runOrder
        # TODO: consider incorporating helper into flux for this
        if test.commandList == ['not run']:
            test.commandList = self.calculateBasicCommandList(test)
        jobspec = {
                'nnodes': 0, # TODO: this should be 0, or something to say "I don't care" but that's causing issues
                'ntasks': max(test.np, 1),
                'ncores': max(test.np, 1),
                'cmdline': test.commandList,
                'environ': dict(os.environ), # TODO: add environment updating stuff
                'cwd': test.directory,
                'walltime': test.timelimit.value,
                'output': {
                    'files': {
                        'stdout': test.outname,
                        'stderror': test.errname if not (hasattr(test, 'combineOutput') and test.combineOutput) else test.outname,
                    }
                },
            'opts': {
                'ntasks' : max(test.np, 1),
                'cores-per-task' : 1,
            },
        }
        new_ld_library_path = "/opt/ibm/spectrum_mpi/lib/pami_port:/opt/ibm/spectrum_mpi/lib:/opt/ibm/spectrum_mpi/lib:/opt/mellanox/hcoll/lib"
        if os.environ['LD_LIBRARY_PATH']:
            new_ld_library_path += ":{}".format(os.environ['LD_LIBRARY_PATH'])
        jobspec['environ'] = {k: v for k, v in jobspec['environ'].iteritems() if k.split('_')[0] not in ('JSM', 'OMPI', 'PMIX', 'ENVIRONMENT')}
        jobspec['environ'].update({"OMPI_MCA_osc": "pt2pt",
                                   "OMPI_MCA_pml": "yalla",
                                   "OMPI_MCA_btl": "self",
                                   "OPAL_LIBDIR": "/usr/tce/packages/spectrum-mpi/ibm/spectrum-mpi-rolling-release/lib",
                                   "LD_LIBRARY_PATH": new_ld_library_path,
                                   "OMPI_MCA_coll_hcoll_enable": "0",
                                   "OMPI_MCA_orte_tmpdir_base": test.directory,
                                   #"LD_PRELOAD":"/opt/ibm/spectrum_mpi/lib/libpami_cudahook.so",
                                  })
        jobspec['environ'].pop('PMIX_SERVER_URI', None)
        jobspec['environ'].pop('PMIX_SERVER_URI2', None)
        # print jobspec
        job_response = self.fh.rpc_send('job.submit', jobspec)
        print(job_response)
        if job_response is None:
            raise RuntimeError("RPC response invalid")
        if job_response.get('errnum', None) is not None:
            raise RuntimeError("Job creation failed with error code {}".format(
                job_response['errnum']))
        test.job_id = job_response['jobid']
        test.kvs_path = job_response['kvs_path']
        test.status = RUNNING # was BATCHED, not true, but made prototyping easier, re-investigate this later
        self.submitted[test.job_id] = test

        self.noteLaunch(test)
        return True

    def noteLaunch(self, test):
        self.numberTestsRunning += 1 # max(test.np, 1)
        self.numberCoresInUse += max(test.np, 1)

    def noteEnd(self, test):
        self.numberTestsRunning -= 1 # max(test.np, 1)
        self.numberCoresInUse -= max(test.np, 1)

    def periodicReport(self):
        "Make the machine-specific part of periodic report to the terminal."
        terminal(len(self.running), "tests running on", self.numberTestsRunning,
              "of", self.cores, "cores.")

    def checkRunning(self):
        try:
            self.fh.reactor_run(self.fh.get_reactor(), self.fh.REACTOR_ONCE)
        except EnvironmentError as e:
            if e.errno == errno.EAGAIN:
                pass
            else:
                raise e
        # super(FluxDirect, self).checkRunning()

    def getStatus (self, test):
        raise RuntimeError("Should not run")
