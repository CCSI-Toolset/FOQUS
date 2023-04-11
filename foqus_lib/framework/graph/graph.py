#################################################################################
# FOQUS Copyright (c) 2012 - 2023, by the software owners: Oak Ridge Institute
# for Science and Education (ORISE), TRIAD National Security, LLC., Lawrence
# Livermore National Security, LLC., The Regents of the University of
# California, through Lawrence Berkeley National Laboratory, Battelle Memorial
# Institute, Pacific Northwest Division through Pacific Northwest National
# Laboratory, Carnegie Mellon University, West Virginia University, Boston
# University, the Trustees of Princeton University, The University of Texas at
# Austin, URS Energy & Construction, Inc., et al.  All rights reserved.
#
# Please see the file LICENSE.md for full copyright and license information,
# respectively. This file is also available online at the URL
# "https://github.com/CCSI-Toolset/FOQUS".
#################################################################################
"""graph.py

* This is the main class for storing directed graphs
* The graphs are used to represent a meta-flowsheet of connected simulations
* Includes methods to find tears and solve recycle

John Eslick, Carnegie Mellon University, 2014
"""

import queue
import foqus_lib.framework.sampleResults.results as resultList
import multiprocessing.dummy as multiprocessing
import numpy
import math
import time
import csv
import copy
import threading
import logging
import sys
from collections import OrderedDict
from foqus_lib.framework.graph.node import *  # Node, input var and output var classes
from foqus_lib.framework.graph.nodeModelTypes import nodeModelTypes
from foqus_lib.framework.graph.edge import *  # Edge and variable connection classes
from foqus_lib.framework.graph.OptGraphOptim import *  # Objective function calculation class
from foqus_lib.framework.sim.turbineConfiguration import *
from foqus_lib.framework.graph.nodeVars import *
import pandas

_log = logging.getLogger("foqus." + __name__)


class GraphEx(foqusException):
    def setCodeStrings(self):
        self.codeString[0] = "Finished Normally"
        self.codeString[1] = "Failure in node calculation, " "check node status"
        self.codeString[3] = (
            "Failure to create worker node " "(most likely could not talk to Turbine)"
        )
        self.codeString[5] = "Specified unknown tear solver"
        self.codeString[11] = "Wegstein solver failed to converge"
        self.codeString[12] = "Direct solver failed to converge"
        self.codeString[16] = "Error in presolve node"
        self.codeString[17] = "Error in postsolve node"
        self.codeString[19] = "Exception during graph execution (see foqus.log)"
        self.codeString[20] = "Flowsheet thread terminated"
        self.codeString[21] = "Session name required to run a flowsheet in Turbine"
        self.codeString[40] = "Error connecting to Turbine"
        self.codeString[50] = "Error loading session or inputs"
        self.codeString[100] = "Single Node Calculation Success"
        self.codeString[201] = "Found cycle in tree while finding calculation order"
        self.codeString[1001] = "Missing/Incomplete result dictionary"


class Graph(threading.Thread):
    """
    This class represents the information flow between simulations. Graph nodes
    represent simulations, and directed edges represent the flow of information.
    This graph class contains a lot of non-graph stuff for running simulations
    and calculations, and solving when the nodes are interdependent
    (recycle loops).
    """

    def __init__(self, statusVar=True):  # graph constructor function
        """
        Graph constructor

        Args:
            statusVar: if true include graph.error variable
        """
        # Thread stuff
        threading.Thread.__init__(self)
        self.ex = None
        self.stop = threading.Event()  # flag to say you want to stop
        self.rtDisconnect = threading.Event()  # flag to disconnect
        # from remote turbine but leave the session running
        self.resLock = threading.Lock()  # lock for read/write results
        self.statLock = threading.Lock()  # run status read/write lock
        self.daemon = True
        self.nodes = dict()  # nodes of graph representing simulations
        self.edges = []  # connections between simulations
        self.x = OrderedDict()  # dictionary of inputs
        self.f = OrderedDict()  # dictionary of outputs
        self.xvector = OrderedDict()  # dictionary of input vectors
        self.fvector = OrderedDict()  # dictionary of output vectors
        self.input = NodeVarList()
        self.output = NodeVarList()
        self.nvlist = None
        self.input_vectorlist = NodeVarVectorList()
        self.output_vectorlist = NodeVarVectorList()
        self.input.addNode("graph")  # global variables
        self.output.addNode("graph")  # global variables
        if statusVar:
            self.output.addVariable("graph", "error")
            self.output["graph"]["error"].desc = "Flowsheet error code"
        self.includeStatusOutput = statusVar
        self.xnames = []  # list of input names  (sorted alphabetically)
        self.fnames = []  # list of output names (sorted alphabetically)
        #
        self.solTime = 0  # Amount of time used to solve graph outputs
        self.errorStat = -1  # Solve error code
        self.setErrorCode(-1)
        #
        self.turbConfig = TurbineConfiguration()  # turbine config
        self.simList = dict()  # list of simulations
        self.turbSession = None  # Turbine session for remote turbine
        self.turbineJobIds = []  # Job list for remote turbine
        # SCC = strongly connected components
        self.sccNodes = []  # list of lists of SCC nodes
        self.sccEdges = []  # list of lists of SCC edges
        self.sccLink = []  # list of lists SCC ordering
        #
        self.turbineSim = None  # If a string use that simuation name in
        # Turbine if none don't submit flowsheet runs to turbine
        self.sessionFile = None  # session file to upload to turbine
        self.useTurbine = False
        self.turbchkfreq = 10
        #
        self.onlySingleNode = None  # If single node is set to a node name
        # the graph calculations are only done on a single node
        #
        # Default solver settings
        self.tearSolver = "Wegstein"
        self.tearMaxIt = 40
        self.tearTol = 0.001
        self.tearTolType = "abs"
        self.tearLog = False
        self.tearLogStub = "tear_log"
        self.tearBound = False
        self.wegAccMax = 9.0
        self.wegAccMin = -9.0
        self.staggerStart = 0.0
        self.threadName = ""
        self.runIndex = 0
        self.results = resultList.Results()
        self.singleCount = 0
        self.pre_solve_nodes = []
        self.post_solve_nodes = []
        self.no_solve_nodes = []

    def setErrorCode(self, e):
        self.errorStat = e
        if self.includeStatusOutput:
            self.output["graph"]["error"].value = e

    def turbineSimList(self):
        """
        Return a list of turbine simultaion names used in this
        flowsheet.
        """
        names = set()
        for nkey, node in self.nodes.items():
            if node.modelType in [
                nodeModelTypes.MODEL_TURBINE,
                nodeModelTypes.MODEL_DMF_LITE,
                nodeModelTypes.MODEL_DMF_SERV,
            ]:
                names.add(node.modelName)
        return names

    def terminate(self):
        """
        This will tell a graph thread to stop running.
        """
        self.stop.set()

    def remoteDisconnect(self):
        """
        Graph thread will stop but leaves the jobs submitted to Turbine
        running. (just batches to remote Turbine).
        """
        self.rtDisconnect.set()

    def errorLookup(self, i):
        """
        Give a descriptive error message to go with an
        integer error code.
        """
        e = NodeEx.GetInstance(i)
        if e is not None:
            return str(i)
        e = GraphEx()
        if i == -1:
            return "Graph calculations did not finish"
        try:
            return e.codeString[i]
        except:
            return "Unknown error"

    def copyGraph(self):
        """
        Make a copy of a graph by saving it to a dictionary and
        reloading it using the  loadDict() and saveDict() functions.
        The does not make an exact copy some things like generate
        global variables may need redone
        """
        sd = self.saveDict(results=False)
        gr = Graph(self.includeStatusOutput)
        gr.pymodels = self.pymodels
        gr.turbineSim = self.turbineSim
        gr.sessionFile = self.sessionFile
        gr.useTurbine = self.useTurbine
        gr.turbchkfreq = self.turbchkfreq
        gr.resubMax = self.resubMax
        gr.turbConfig = self.turbConfig
        gr.loadDict(sd)
        return gr

    def saveDict(self, results=True):
        """
        This is mostly used to save a graph as json, but
        it could also be used to make a copy of the graph.
        The information can be loaded back in with loadDict()
        """
        sd = {
            "errorStat": self.errorStat,
            "includeStatusOutput": self.includeStatusOutput,
            "nodes": self.saveNodeDict(),
            "edges": self.saveEdgeList(),
            "input": self.input.saveDict(),
            "output": self.output.saveDict(),
            "tearSolver": self.tearSolver,
            "tearMaxIt": self.tearMaxIt,
            "tearTol": self.tearTol,
            "tearTolType": self.tearTolType,
            "tearLog": self.tearLog,
            "tearLogStub": self.tearLogStub,
            "tearBound": self.tearBound,
            "wegAccMax": self.wegAccMax,
            "wegAccMin": self.wegAccMin,
            "singleCount": self.singleCount,
            "onlySingleNode": self.onlySingleNode,
            "simList": self.saveSimDict(),
            "pre_solve_nodes": self.pre_solve_nodes,
            "post_solve_nodes": self.post_solve_nodes,
            "no_solve_nodes": self.no_solve_nodes,
            "turbineSim": self.turbineSim,  # name of FOQUS sim for remote
        }
        nvl = self.input
        sd["input_vectorlist"] = self.input_vectorlist.saveDict(nvl)
        nvl = self.output
        sd["output_vectorlist"] = self.output_vectorlist.saveDict(nvl)
        if results:
            sd["results"] = self.results.saveDict()
        return sd

    def saveNodeDict(self):
        sd = {}
        for nkey, node in self.nodes.items():
            sd[nkey] = node.saveDict()
        return sd

    def saveEdgeList(self):
        sl = []
        # Save edges
        for edge in self.edges:
            sl.append(edge.saveDict())
        return sl

    def saveSimDict(self):
        sd = {}
        # Save simulation (model) list
        for key, sim in self.simList.items():
            sd[key] = sim.saveDict()
        return sd

    def loadDict(self, sd):
        """
        Loads a dictionary created by saveDict() or read from json
        """
        self.errorStat = sd.get("errorStat", self.errorStat)
        self.includeStatusOutput = sd.get("includeStatusOutput", True)
        self.tearSolver = sd.get("tearSolver", self.tearSolver)
        self.tearMaxIt = sd.get("tearMaxIt", self.tearMaxIt)
        self.tearTol = sd.get("tearTol", self.tearTol)
        self.tearLog = sd.get("tearLog", False)
        self.tearLogStub = sd.get("tearLogStub", "tear_log")
        self.tearBound = sd.get("tearBound", False)
        self.tearTolType = sd.get("tearTolType", self.tearTolType)
        self.wegAccMax = sd.get("wegAccMax", self.wegAccMax)
        self.wegAccMin = sd.get("wegAccMin", self.wegAccMin)
        self.singleCount = sd.get("singleCount", self.singleCount)
        self.pre_solve_nodes = sd.get("pre_solve_nodes", [])
        self.post_solve_nodes = sd.get("post_solve_nodes", [])
        self.no_solve_nodes = sd.get("no_sovle_nodes", [])
        self.turbineSim = sd.get("turbineSim", None)
        temp = sd.get("results", None)
        if temp:
            self.results.loadDict(temp)
        temp = sd.get("input", None)
        if temp:
            self.input.loadDict(temp)
        else:
            self.input.clear()
            self.input.addNode("graph")
        temp = sd.get("output", None)
        if temp:
            self.output.loadDict(temp)
        else:
            self.output.clear()
            self.input.addNode("graph")
        temp = sd.get("input_vectorlist", None)
        if temp:
            self.nvlist = self.input
            self.input_vectorlist.loadDict(temp)
        else:
            self.input_vectorlist.clear()
        temp = sd.get("output_vectorlist", None)
        if temp:
            self.nvlist = self.output
            self.output_vectorlist.loadDict(temp)
        else:
            self.output_vectorlist.clear()
        self.nodes = dict()
        self.edges = []
        self.simList = dict()
        self.onlySingleNode = sd.get("onlySingleNode", None)
        # load nodes
        for nkey, nd in sd["nodes"].items():
            n = self.addNode(nkey)
            n.loadDict(nd)
        # load edges
        for ed in sd["edges"]:
            edg = edge("", "")
            edg.loadDict(ed)
            self.edges.append(edg)
        if "graph" not in self.input:
            self.input.addNode("graph")
        if "graph" not in self.output:
            self.output.addNode("graph")
        if self.includeStatusOutput:
            if "error" not in self.output["graph"]:
                self.output.addVariable("graph", "error")
                self.output["graph"]["error"].desc = "Flowsheet error code"
                self.setErrorCode(self.errorStat)

    def saveValues(self):
        """
        This function saves the variable values and run status codes
        to a dictionary.  The dictionary can be written to a json
        string.
        """
        sd = {
            "solTime": self.solTime,
            "input": self.input.saveValues(),
            "output": self.output.saveValues(),
            "graphError": self.errorStat,
            "nodeError": {},
            "nodeSettings": {},
            "turbineMessages": {},
        }
        nvl = self.input
        sd["input_vectorvals"] = self.input_vectorlist.saveValues(nvl)
        nvl = self.output
        sd["output_vectorvals"] = self.output_vectorlist.saveValues(nvl)
        for nkey, node in self.nodes.items():
            sd["nodeError"][nkey] = node.calcError
            sd["turbineMessages"][nkey] = node.turbineMessages
            sd["nodeSettings"][nkey] = {}
            for okey, opt in node.options.items():
                sd["nodeSettings"][nkey][okey] = opt.value
        return sd

    def loadValues(self, sd):
        """Loads values for the graph variables from a dictionary it also loads
        status codes if they are present.  If no status codes are in the
        dictionary, error codes are set to -1 (not run yet).
        """
        self.solTime = sd.get("solTime", 0)
        o = sd.get("input", None)
        if o is not None:
            self.input.loadValues(o)
        else:
            _log.error("Failed to get 'input' from results: sd={}".format(sd))
        o = sd.get("output", None)
        if o is not None:
            self.output.loadValues(o)
        o = sd.get("input_vectorvals", None)
        if o is not None:
            self.nvlist = self.input
            self.input_vectorlist.loadValues(o)
        else:
            self.input_vectorlist.clear()
        o = sd.get("output_vectorvals", None)
        if o is not None:
            self.nvlist = self.output
            self.output_vectorlist.loadValues(o)
        self.setErrorCode(sd.get("graphError", -1))
        ne = sd.get("nodeError", {})
        tm = sd.get("turbineMessages", {})
        for nkey in self.nodes:
            self.nodes[nkey].calcError = ne.get(nkey, -1)
            self.nodes[nkey].turbineMessages = tm.get(nkey, "")
        return sd

    def getCenter(self):
        """
        returns the center of the graph if you draw it you will know
        where to center the view
        """
        ave_x = 0
        ave_y = 0
        ave_z = 0
        for name, node in self.nodes.items():
            ave_x += node.x
            ave_y += node.y
            ave_z += node.z
        if len(self.nodes) > 0:
            ave_x = float(ave_x) / float(len(self.nodes))
            ave_y = float(ave_y) / float(len(self.nodes))
            ave_z = float(ave_z) / float(len(self.nodes))
        return [ave_x, ave_y, ave_z]

    def setAsNotRun(self):
        """
        This sets all the error codes in the nodes and the graph to
        -1, which I am using to mean not executed.
        """
        for key, node in self.nodes.items():
            node.calcError = -1
        self.setErrorCode(-1)

    def killTurbineJobs(self):
        """
        Go through all the nodes and if they are turbine runs with a
        session id, kill all the jobs in that session.
        """
        for key, node in self.nodes.items():
            node.killTurbineSession()

    def generateGlobalVariables(self):
        """
        This function creates a dictionary of input variable
        (self.x) and a dictionary of output variables (self.f) and
        stores pointers to the input and output variables contained
        in the nodes.  The dictionary keys are:
        <node name>.<variable name>
        """
        self.x = self.input.createOldStyleDict()
        self.f = self.output.createOldStyleDict()
        self.xvector = self.input_vectorlist.createOldStyleDict()
        self.fvector = self.output_vectorlist.createOldStyleDict()
        # x and f are ordered dictionaries so keys are already sorted
        self.xnames = list(self.x.keys())  # get a list of input names
        self.fnames = list(self.f.keys())  # get a list of output names
        # self.xvectornames = list(self.xvector.keys())  # get a list of input vector names
        # self.fvectornames = list(self.fvector.keys())  # get a list of output vector names
        self.markConnectedInputs()  # mark which inputs are set by con.

    def markConnectedInputs(self):
        """
        Mark inputs that are connected to outputs these shouldn't be
        considered inputs for optimization or UQ purposes.
        """
        # clear all the connected flags
        for [name, node] in self.nodes.items():
            for [vname, var] in node.inVars.items():
                var.con = False
        # look at edges and find connections
        for edge in self.edges:
            node = self.nodes[edge.end]
            for con in edge.con:
                if edge.tear:
                    # connected by tear edge (initial value is a guess)
                    node.inVars[con.toName].con = 1
                else:
                    # connected by non-tear edge (initial irrelevant)
                    node.inVars[con.toName].con = 2

    def loadDefaults(self):
        """
        Return all input variables to there default value
        """
        for key, n in self.nodes.items():
            n.loadDefaultValues()

    def createNodeTurbineSessions(self, forceNew=True):
        err = False
        for key, node in self.nodes.items():
            # may want to raise an exception if sid
            # comes back as 0.  That would probably
            # be a problem contacting the gateway
            sid = node.createTurbineSession(forceNew=forceNew)
            if sid == 0:
                _log.warning("Problem getting session id for node: {}".format(key))
                err = True
        return err

    def uploadFlowseetToTurbine(self, dat, reset=False):
        """
        Save a session and upload it to turbine
        """
        simname = dat.name
        sessionFile = "tmp_to_turbine"
        dat.save(
            filename=sessionFile,
            updateCurrentFile=False,
            changeLogMsg="Save for turbine submission",
            indent=0,
            keepData=False,
        )
        self.turbineSim = "zzfoqus_{0}".format(simname.replace(" ", "_"))
        self.turbineReset = reset
        self.sessionFile = sessionFile
        self.turbConfig.uploadSimulation(
            simName=self.turbineSim, sinterConfigPath=self.sessionFile, update=True
        )

    def solveListValTurbineCreateSession(self):
        """
        Create a session in Turbine to run FOQUS flowsheet samples
        (split up solveListValTurbine() to help maintanabiliy)
        """
        try:
            turbSession = self.turbConfig.retryFunction(
                5, 20, 2, self.turbConfig.createSession
            )
        except:
            self.setErrorCode(40)
            return None
        self.turbSession = turbSession
        _log.info("Running FOQUS jobs in Turbine session: \n{0}".format(turbSession))
        return turbSession

    def solveListValTurbineCreateJobs(self, valueList, maxSend):
        """
        Make jobs to send to turbine split into smaller sets to
        submit large numbers of jobs to avoid send too much
        information a once.  Submit and start each set.
        """
        turbSession = self.turbSession
        njobs = len(valueList)
        njsets = int(math.ceil(float(njobs) / float(maxSend)))
        _log.debug("Sending jobs to Turbine in {0} sets".format(njsets))
        setIndex = [0] * (njsets + 1)
        for i in range(njsets + 1):
            setIndex[i] = maxSend * i
            if setIndex[i] > njobs:
                setIndex[i] = njobs
        jobIds = []
        for j in range(len(setIndex) - 1):
            j1 = setIndex[j]
            j2 = setIndex[j + 1]
            jobList = [None] * (j2 - j1)
            for i, jobVal in enumerate(valueList[j1:j2]):
                jobList[i] = {
                    "Simulation": self.turbineSim,
                    "Input": jobVal,
                    "Reset": False,
                }
            # add job list to turbine
            # with open("jobs{0}.json".format(j), 'w') as fp:
            #    json.dump(jobList, fp)
            jids = self.turbConfig.retryFunction(
                5, 20, 2, self.turbConfig.createJobsInSession, turbSession, jobList
            )
            _log.debug("Created Jobs: \n{0}".format(jids))
            jobIds.extend(jids)
            # Start the Turbine session before all jobs have been
            # submitted this will allow jobs to start running.
            # Submitting large sets of jobs may take a long time, so
            # may as well start running jobs, while doing it.
            try:
                self.turbConfig.retryFunction(
                    5, 20, 2, self.turbConfig.startSession, turbSession
                )
            except:
                _log.exception("Failed to start session")
                self.setErrorCode(40)
                return None
        return jobIds

    def solveListValTurbineGetGenerator(self):
        """
        Get a results genrator from Turbine, if fail return None
        """
        try:
            gid = self.turbConfig.retryFunction(
                5, 20, 2, self.turbConfig.getCompletedJobGen, self.turbSession
            )
        except:
            _log.exception("Failed to get generator")
            self.setErrorCode(40)
            return None
        _log.debug("Results generator: {0}".format(gid))
        return gid

    def solveListValTurbineGetGeneratorPage(self, gid):
        try:
            page = self.turbConfig.retryFunction(
                5, 20, 2, self.turbConfig.getCompletedJobPage, self.turbSession, gid
            )
        except:
            _log.exception("Could not get results page")
            return None
        return page

    def solveListValTurbineGeneratorReadPage(self, gid, page, maxRes):
        """
        Get the Turbine results from a generator page.
        """
        _log.debug("New results page {0} from {1}".format(page, gid))
        try:
            jres = self.turbConfig.retryFunction(
                5,
                20,
                2,
                self.turbConfig.getCompletedJobs,
                self.turbSession,
                gid,
                page,
                maxRes,
            )
        except:
            _log.exception("Error reading results page {0} from {1}".format(page, gid))
            return None
        return jres

    def solveListValTurbineReSub(self, inp, oi):
        """
        Resubmit a failed job for another try
        """
        job = {"Simulation": self.turbineSim, "Input": inp, "Reset": False}
        # Create new job to rerun failed job
        jid = self.turbConfig.retryFunction(
            5, 20, 2, self.turbConfig.createJobsInSession, self.turbSession, [job]
        )[0]
        # Start the job
        self.turbConfig.retryFunction(
            5, 20, 2, self.turbConfig.startSession, self.turbSession
        )
        # Log the retry
        _log.debug("Resubmitted Job {0} as {1}".format(oi, jid))
        # return new job number
        return jid

    def solveListValTurbine(self, valueList=None, maxSend=20, sid=None, jobIds=[]):
        """
        Send a list of flowsheet runs to Turbine, this allows the
        flowsheets to be solved in parallel.

        valueList = list of input dicts for jobs to run
        maxsend = the maximum number of jobs to send to Turbine at
            one time, for a large number of jobs the amount of input
            can get to large for Turbine to receive all at once.
        sid = A turbine session ID to reconnect to.  If a previous
            run was disconnected this will hook back up and contiune
            to receive results until the session is done.
        """
        ######
        # Create a session and submit jobs
        ######
        maxRes = 2000  # maximum number of results to get at once
        chk_sleep = self.turbchkfreq  # delay between checking for results
        resubMax = self.resubMax  # max times to resubmit failed sim.
        _log.debug("Turbine remote check interval: {0}".format(chk_sleep))
        _log.debug("Max. times to resubmit failed jobs {0}".format(resubMax))
        if sid is not None:
            # in this case reconnecting to a partly finished job set
            turbSession = sid
            self.turbSession = turbSession
            njobs = len(jobIds)
        else:
            # in this case submitting a new set of jobs
            njobs = len(valueList)
            # create turbine session
            turbSession = self.solveListValTurbineCreateSession()
            if turbSession is None:
                return
            # submit jobs, jobIds is a list of job ids
            jobIds = self.solveListValTurbineCreateJobs(valueList, maxSend)
            self.jobIds = jobIds
            if jobIds is None:
                return
        self.allSubmitted = True  # Flag to say job sumbmission is done
        # get results genrator
        gid = self.solveListValTurbineGetGenerator()
        if gid is None:
            return
        _log.debug("Turbine Result Generator: {0}".format(gid))
        ######
        # monitor the turbine session.
        ######
        rp = 0  # pages already read
        skipWait = False  # skip the wait between checking for results
        self.status["error"] = 0
        while self.status["unfinished"] > 0:
            # pause in between checking status, don't want to overwhelm
            # turbine with status requests.
            if not skipWait:
                time.sleep(float(chk_sleep))
            skipWait = False
            jres = None  # job results from Turbine
            # Get results page index
            page = self.solveListValTurbineGetGeneratorPage(gid)
            if page is None:
                # this means some exception getting page, no results
                # should either get previously read page of negative page
                break
            _log.debug("Turbine Result Generator Page: {0} {1}".format(page, rp))
            if page is not None and page > rp:
                jres = self.solveListValTurbineGeneratorReadPage(gid, page, maxRes)
                if jres is None:
                    _log.debug("There are results but exception getting them")
                    break
                if len(jres) == maxRes:
                    skipWait = True
            elif page == -2:
                # some jobs may be paused.  For now just end loop
                with self.statLock:
                    self.status["finished"] = njobs
                    self.status["unfinished"] = 0
                    self.status["error"] = njobs - self.status["success"]
                break
            else:  # page == 0, page already read, or page = -1
                pass
            if jres is not None:
                _log.debug(
                    "Turbine Result Generator Results LEN: {0}".format(len(jres))
                )
                rp += 1
                for job in jres:
                    assert isinstance(job, dict)
                    try:
                        i = jobIds.index(job["Id"])
                    except ValueError:
                        _log.debug(
                            "Job {0} ignore it must be a failed job that got resubmitted".format(
                                job["Id"]
                            )
                        )
                        continue
                    assert "State" in job, "Missing State Field in Job %s Record" % i
                    if job["State"] == "error":
                        logging.getLogger("foqus." + __name__).error(
                            "Job(%s) Error: %s",
                            job["Id"],
                            job.get("Message", "No Error Message Provided"),
                        )
                    jobRes = job.get("Output", None)
                    if jobRes is None:
                        jobErr = -3
                    else:
                        jobErr = jobRes.get("graphError", -2)
                    record = True
                    if self.res_re[i] < resubMax and jobErr != 0:
                        # if job error and resubmit option and first error
                        # then resubmit the job
                        self.res_re[i] += 1
                        jobInput = job.get("Input", None)
                        if jobInput is not None:
                            jobIds[i] = self.solveListValTurbineReSub(
                                jobInput, jobIds[i]
                            )
                            record = False  # retying so don't count
                    if record:
                        with self.resLock:
                            # record results
                            self.res[i] = job.get("Output", None)
                            if self.res[i] == None:
                                self.res_fin[i] = jobErr
                                self.res[i] = {
                                    "Id": job["Id"],
                                    "session": turbSession,
                                    "graphError": self.res_fin[i],
                                }
                            else:
                                assert isinstance(self.res[i], dict)
                                self.res[i]["session"] = turbSession
                                self.res[i]["Id"] = job["Id"]
                                self.res_fin[i] = jobErr
                            # Add information to see if was resubmitted
                            self.res[i]["resub"] = self.res_re[i]
                        with self.statLock:
                            self.status["finished"] += 1
                            self.status["unfinished"] -= 1
                            if jobErr != 0:
                                self.status["error"] += 1
                            else:
                                self.status["success"] += 1
            if self.stop.isSet():
                # if the thread terminate function has been called,
                # stop the thread by breaking out of the loop, any
                # unfinished jobs will be left with -1 status (not run)
                try:
                    self.turbConfig.killSession(turbSession)
                except:
                    _log.exception("Error terminating session {0}".format(turbSession))
                break
            elif self.rtDisconnect.isSet():
                # Just drop out of the monitoring loop
                break
        self.jobIds = jobIds

    def solveListVal(self, valueList):
        for key, node in self.nodes.items():
            if node.modelType == nodeModelTypes.MODEL_DMF_LITE:
                _log.debug("DMF will sync node {}".format(key))
                node.synced = False
            elif node.modelType == nodeModelTypes.MODEL_DMF_SERV:
                node.synced = False
            else:
                pass  # Doesn't matter synced is a DMF thing
        # originalValues = self.saveValues()
        assert isinstance(valueList, (list, tuple))
        # Ensure that the input scalar variable values get assigned to the input vector variables
        for i, vals in enumerate(valueList):
            vectorvals = dict()
            for n in self.nodes:
                vectorvals[n] = OrderedDict()
                for invarsvector in self.nodes[n].inVarsVector.keys():
                    vectorvals[n][invarsvector] = OrderedDict()
                    for invar in self.nodes[n].inVars.keys():
                        if invarsvector in invar:
                            invarsplit = invar.split("_")
                            idx = int(invarsplit[-1])
                            vectorvals[n][invarsvector][idx] = vals[n][invar]
            self.loadValues({"input": vals, "input_vectorvals": vectorvals})
            self.setErrorCode(-1)
            if not self.stop.isSet():
                # run solve if thread has not been stopped
                # it it has been stopped skip the solve and just
                # report a -1 error staus on remaining runs
                try:
                    self.solve()
                    with self.resLock:
                        self.res[i] = self.saveValues()
                        self.res_fin[i] = self.errorStat
                except Exception as e:
                    with self.resLock:
                        self.res[i] = None
                        self.res_fin[i] = -2
                        self.setErrorCode(-1)
                    _log.exception("Error executing a flowsheet sample")
            with self.statLock:
                self.status["finished"] += 1
                self.status["unfinished"] -= 1
                if self.errorStat != 0:
                    self.status["error"] += 1
                else:
                    self.status["success"] += 1

    def run(self):
        """
        This function should not be called directly
        it is called by the thread start() function

        If self.runList is set assume there are a set
        of runs specified by self.runList, otherwise
        assume it is a single run with current values
        """
        if not self.useTurbine:
            _log.debug("run: Running flowsheet(s) locally")
            # In this case the runs are done serially locally
            try:
                # run a single simulation or a list of simulations
                if not self.runList:
                    _log.debug("run: solve single simulation")
                    self.solve()
                    with self.resLock:
                        self.res[0] = self.saveValues()
                        self.res_fin[0] = self.errorStat
                else:
                    _log.debug("run: solve list simulations")
                    self.solveListVal(self.runList)
            except Exception as e:
                self.setErrorCode(19)
                self.ex = sys.exc_info()
                _log.exception("Exception in graph thread: %s" % (self.ex))
        else:
            _log.debug("run: Running flowsheet(s) through turbine")
            # in this case run should produce the same results but
            # the runs are submitted in a batch to Turbine
            #
            # whether it is a single run or a batch need to upload
            # session file to Turbine.  For the simulation name I
            # just use the session name.
            if not self.runList:
                # going to batch for single run or batch to turbine
                # need to make a runList for single run
                sd = self.saveValues()
                self.runList = [sd["input"]]
            # make sure there are no numpy arrays in runList
            for job in self.runList:
                for nkey in job:
                    for vkey in job[nkey]:
                        if type(job[nkey][vkey]).__module__ == numpy.__name__:
                            job[nkey][vkey] = job[nkey][vkey]
            if self.turbineSession is None:
                self.solveListValTurbine(self.runList)
            else:
                self.solveListValTurbine(sid=self.turbineSession, jobIds=self.jobIds)

    def runListAsThread(
        self, runList=None, useTurbine=False, sid=None, jobIds=[], resubs=None, dat=None
    ):
        """
        Open a new thread and run a list of simulations
        with the inputs specified in runList.  runList is
        a list of dictionaries with the format:
            runList[i][nodeKey][varKey] = value

        This returns a new running graph thread.  The results
        are stored in a list in the res attribute of the new
        graph thread.  The results are in list where each results
        is the output of the saveValues function.
        """
        self.useTurbine = useTurbine
        if not useTurbine:
            self.createNodeTurbineSessions(forceNew=False)
        newGr = self.copyGraph()
        if runList is not None and len(runList) > 0:
            newGr.res = [None] * len(runList)
            newGr.res_fin = [-1] * len(runList)
            newGr.res_re = [0] * len(runList)
        elif jobIds is not None:
            newGr.res = [None] * len(jobIds)
            newGr.res_fin = [-1] * len(jobIds)
            if resubs is None:
                newGr.res_re = [0] * len(jobIds)
            else:
                newGr.res_re = resubs
        else:
            raise ValueError("Must supply runList or jobIds")
        newGr.status = {
            "unfinished": len(newGr.res),
            "finished": 0,
            "error": 0,
            "success": 0,
        }
        newGr.runList = runList
        newGr.allSubmitted = False
        newGr.turbineSession = sid
        newGr.jobIds = jobIds
        newGr.start()
        return newGr

    def runAsThread(self, useTurbine=False, sid=None, dat=None):
        """
        Run current graph setting in a separate thread the
        results are stored in the res attribute of the returned
        graph.  The format of the results are a dictionary that
        can be loaded into the original graph with the loadValues
        function.

        This returns a new running graph thread.
        """
        self.useTurbine = useTurbine
        if not useTurbine:
            self.createNodeTurbineSessions(forceNew=False)
        newGr = self.copyGraph()
        newGr.status = {"unfinished": 1, "finished": 0, "error": 0, "success": 0}
        newGr.turbineSession = sid
        newGr.runList = None
        newGr.res = [None]
        newGr.res_fin = [-1]
        newGr.res_re = [0]
        newGr.start()
        return newGr

    def solve(self):
        """
        This function solves each strongly connected component
        following the SCC calculation ordering.  If an SCC has
        more than one tear they are converged simultaneously.
        I know that is probably not best but it is easy for now
        """
        # for key, node in self.nodes.items():
        #     if node.modelType == nodeModelTypes.MODEL_DMF_LITE:
        #         _log.debug("DMF will sync node {}".format(key))
        #         node.synced = False
        #     elif node.modelType == nodeModelTypes.MODEL_DMF_SERV:
        #         node.synced = False
        #     else:
        #         pass  # Doesn't matter synced is a DMF thing
        tstart = time.time()
        self.setAsNotRun()
        self.setErrorCode(0)
        self.generateGlobalVariables()
        for node in self.nodes:
            self.nodes[node].setGraph(self)
        # check if you only want to run a single node, this lest you run
        # calculations on a node in using the system already setup for
        # the graph but only evaluates a single node.
        if self.onlySingleNode in list(self.nodes.keys()):
            name = self.onlySingleNode
            _log.debug("solve: onlySingleNode %s", name)
            if self.runNode(name) != 0:
                self.setErrorCode(1)
            else:
                # use error code 100 to indicate successful single node
                # run, but make sure it is clear that whole graph was
                # not evaluated
                self.setErrorCode(100)
            self.solTime = time.time() - tstart
            return self.solTime
        elif self.onlySingleNode != None:
            _log.error("solve: onlySingleNode not in node keys")
            self.setErrorCode(4)
            return

        # Take the pre and post solve nodes out of the calculation order
        fs_sub = []
        for nkey, node in self.nodes.items():
            if nkey in self.pre_solve_nodes:
                node.seq = False
            elif nkey in self.post_solve_nodes:
                node.seq = False
            elif nkey in self.no_solve_nodes:
                node.seq = False
            else:
                node.seq = True
                fs_sub.append(nkey)
        # Run presove nodes in order
        for nkey in self.pre_solve_nodes:
            _log.debug("solve: run pre-solve node %s", nkey)
            node = self.nodes[nkey]
            node.runCalc()
            if node.calcError != 0:
                _log.debug("solve: pre-solve calcError %d", node.calcError)
                self.setErrorCode(16)
                self.solTime = time.time() - tstart
                return self.solTime
        # Run graph, order is based on tree with tears removed
        order = self.calculationOrder(subNodes=fs_sub)
        _log.debug("solve: runGraph")
        self.runGraph(order)
        # Check if there are any tears if no tears we are done
        solveTear = False
        for edge in self.edges:
            if edge.tear:
                solveTear = True
                break
        if not solveTear:
            _log.debug("solve: no tears flowsheet done run post solve nodes")
            for nkey in self.post_solve_nodes:
                _log.debug("solve: run post-solve node %s", nkey)
                node = self.nodes[nkey]
                node.runCalc()
                if node.calcError != 0:
                    _log.debug("solve: post-solve calcError %d", node.calcError)
                    self.setErrorCode(17)
                    self.solTime = time.time() - tstart
                    return self.solTime
            # All done return
            self.solTime = time.time() - tstart
            return self.solTime
        # Now solve tears if there are any...
        # first identify the strongly connected components
        [
            sccNodes,
            sccEdges,
            outEdges,
            inEdges,
            sccOrder,
        ] = self.stronglyConnectedSubGraphs(True)
        # sccOrder is the order in which to solve the SCCs there is a
        # possibility depending of the topology that some could be
        # solved at the same time so the ordering has two levels and
        # there are two loops.
        for lev in sccOrder:
            for sccIndex in lev:
                # find calculation order for nodes in a SCC subgraph
                order = self.calculationOrder([], sccNodes[sccIndex])
                # Add any tear streams that are completely in the SCC
                tears = []
                for edgeIndex in sccEdges[sccIndex]:
                    if self.edges[edgeIndex].tear == True:
                        tears.append(edgeIndex)
                # Run the selected tear solver on the SCC
                if self.tearSolver == "Wegstein" or self.tearSolver == "Direct":
                    [errCode, hist] = self.solveSubGraphWeg(
                        order,
                        tears,
                        itLimit=self.tearMaxIt,
                        tol=self.tearTol,
                        thetaMin=self.wegAccMin,
                        thetaMax=self.wegAccMax,
                        direct=self.tearSolver == "Direct",
                    )
                else:
                    errCode = 5
                if errCode != 0:
                    self.setErrorCode(errCode)
                    self.solTime = time.time() - tstart
                    return self.solTime
        _log.debug("solve: No errors so far and flowsheet converged, run post nodes")
        for nkey in self.post_solve_nodes:
            _log.debug("solve: run post-solve node %s", nkey)
            node = self.nodes[nkey]
            node.runCalc()
            if node.calcError != 0:
                _log.debug("solve: post-solve calcError %d", node.calcError)
                self.setErrorCode(17)
                self.solTime = time.time() - tstart
                return self.solTime

        _log.debug("solve: pre, flowsheet, post all done return success")
        self.setErrorCode(0)
        self.solTime = time.time() - tstart
        return self.solTime

    def checkTearStatus(self):
        """
        Check whether the specified tear streams are sufficient.
        If the graph minus the tear edges is not a tree then the
        tear set is not sufficient to solve the graph.
        """
        [
            sccNodes,
            sccEdges,
            outEdges,
            inEdges,
            sccOrder,
        ] = self.stronglyConnectedSubGraphs(False)
        for ns in sccNodes:
            if len(ns) > 1:
                return False
        return True

    def setTearX(self, tears, x):
        """
        Transfer the value of the two side of a set of tear streams
        to the value x, x is a list of values for each connection in
        each tear
        """
        i = 0
        for tear in tears:
            for con in self.edges[tear].con:
                self.nodes[self.edges[tear].end].inVars[con.toName].value = x[i]
                i += 1

    def solveSubGraphWeg(
        self,
        nodeOrder,
        tears,
        itLimit=40,
        tol=1.0e-5,
        thetaMin=-5,
        thetaMax=0,
        direct=False,
    ):
        """
        Use Wegstein to solve tears.  If multiple tears are given
        they are solved simultaneously.

        Args:
            nodeOrder: list of nodes order in which to calculate nodes
                (can be a subset of all nodes)
            tears: list of tear edges indexes if more than one they
                are solved simultaneously
            direct: If true use direct method

        Returns:
            This returns a 2 element list.
            0 - status code, 0 means completed normally
            1 - error history list of lists of differences between input
                and output that are supposed to be equal.  Each list is
                one iteration.
        """
        if self.tearLog:
            log_file = self.tearLogStub
            for j in range(100):
                # dont want to pick up too many of these files
                # but if there are multiple loops want to produce seperate
                # files for them
                if not os.path.isfile("{}{}.csv".format(log_file, j + 1)) or j == 99:
                    log_file = "{}{}.csv".format(log_file, j + 1)
                    break
        else:
            log_file = None
        numpy.seterr(divide="ignore", invalid="ignore")
        i = 0  # iteration counter
        if tears == []:  # no tears nothing to solve.
            # no need to iterate just run the calculations
            self.runGraph(nodeOrder)
            return [self.errorStat, None]
        else:  # start the solving
            gofx = []
            x = []
            names = []
            xmin = []
            xmax = []
            for tear in tears:
                nodes = self.nodes
                from_node = self.edges[tear].start
                to_node = self.edges[tear].end
                names += [con.toName for con in self.edges[tear].con]
                gofx += [
                    self.nodes[from_node].outVars[con.fromName].value
                    for con in self.edges[tear].con
                ]
                x += [
                    self.nodes[to_node].inVars[con.toName].value
                    for con in self.edges[tear].con
                ]
                xmax += [
                    self.nodes[to_node].inVars[con.toName].max
                    for con in self.edges[tear].con
                ]
                xmin += [
                    self.nodes[to_node].inVars[con.toName].min
                    for con in self.edges[tear].con
                ]
            hist = pandas.DataFrame(index=names)
            gofx = numpy.array(gofx)
            x = numpy.array(x)
            xmin = numpy.array(xmin)
            xmax = numpy.array(xmax)
            xrng = xmax - xmin
            if self.tearTolType == "abs":
                err = gofx - x
            elif self.tearTolType == "rng":
                err = (gofx - x) / xrng
            hist["xmin"] = xmin
            hist["xmax"] = xmax
            hist["err_{}".format(i)] = err
            hist["x_{}".format(i)] = x
            hist["g(x_{})".format(i)] = gofx
            if log_file is not None:
                hist.to_csv(log_file)
            if numpy.max(numpy.abs(err)) < tol:
                return [0, hist]  # already solved.
            # if not solved yet do one direct step
            x_prev = x
            gofx_prev = gofx
            x = gofx
            if self.tearBound:
                if numpy.any(x > xmax) or numpy.any(x < xmin):
                    _log.warning(
                        "Bound clipping while solving tear: {}".format(
                            numpy.array(names)[x > xmax]
                        )
                    )
                hist["next_x_{}_unbound".format(i)] = x
                x[x > xmax] = xmax[x > xmax]
                x[x < xmin] = xmin[x < xmin]
            else:
                if numpy.any(x > xmax) or numpy.any(x < xmin):
                    _log.warning(
                        "Out of bounds while solving tear: {}".format(
                            numpy.array(names)[x > xmax]
                        )
                    )
            hist["next_x_{}".format(i)] = x
            self.setTearX(tears, gofx)
            while True:
                self.runGraph(nodeOrder)
                if self.errorStat != 0:
                    _log.warning("Simulation failed in tear solve")
                    return [2, hist]  # 2, simulation failure
                gofx = []
                for tear in tears:
                    gofx += [
                        self.nodes[self.edges[tear].start].outVars[con.fromName].value
                        for con in self.edges[tear].con
                    ]
                gofx = numpy.array(gofx)
                if self.tearTolType == "abs":
                    err = gofx - x
                elif self.tearTolType == "rng":
                    err = (gofx - x) / xrng
                hist["err_{}".format(i)] = err
                hist["x_{}".format(i)] = x
                hist["g(x_{})".format(i)] = gofx
                if log_file is not None:
                    hist.to_csv(log_file)
                if numpy.max(numpy.abs(err)) < tol:
                    break
                if i > itLimit - 1:
                    _log.warning(
                        "tear failed to converge in {0} iterations".format(itLimit)
                    )
                    err_code = 12 if direct else 11
                    return [11, hist]
                if not direct:
                    denom = x - x_prev
                    slope = numpy.divide((gofx - gofx_prev), denom)
                    # if x and previous x are same just do direct sub
                    # for those elements
                    slope[numpy.absolute(denom) < 1e-10] = 0.0
                    theta = 1.0 / (1.0 - slope)
                    theta[theta < thetaMin] = thetaMin
                    theta[theta > thetaMax] = thetaMax
                    hist["theta_{}".format(i)] = theta
                x_prev = x
                gofx_prev = gofx
                x = gofx if direct else (1.0 - theta) * x + (theta) * gofx
                if self.tearBound:
                    if numpy.any(x > xmax) or numpy.any(x < xmin):
                        _log.warning(
                            "Bound clipping while solving tear: {}".format(
                                numpy.array(names)[x > xmax]
                            )
                        )
                    hist["next_x_{}_unbound".format(i)] = x
                    x[x > xmax] = xmax[x > xmax]
                    x[x < xmin] = xmin[x < xmin]
                else:
                    if numpy.any(x > xmax) or numpy.any(x < xmin):
                        _log.warning(
                            "Out-of-bounds while solving tear: {}".format(
                                numpy.array(names)[x > xmax]
                            )
                        )
                hist["next_x_{}".format(i)] = x
                self.setTearX(tears, x)
                i += 1
        return [0, hist]  # 0, everything is fine

    def tearErr(self, tears):
        x0 = []
        x1 = []
        for tear in tears:
            x0 += [
                self.nodes[self.edges[tear].start].outVars[con.fromName].value
                for con in self.edges[tear].con
            ]
            x1 += [
                self.nodes[self.edges[tear].end].inVars[con.toName].value
                for con in self.edges[tear].con
            ]
        x0 = numpy.array(x0)
        x1 = numpy.array(x1)
        return (x0 - x1, x1)

    def runGraph(self, order):
        """
        This runs calculations for nodes in a specific order.  The
        order argument in a list of lists of node names.  The nodes
        are run in the order given in the first list followed by the
        order given in the second list and so on.  Information is
        transfered between nodes for any active none tear edges
        after the completion of each node calculation.  If there
        is an error in any node this returns immediatly and sets the
        graph error status to indicate error.
        """
        for namelst in order:
            for name in namelst:
                if self.stop.isSet():
                    _log.error("runGraph(%s): error 20 stop is set", name)
                    self.setErrorCode(20)
                    return
                calcError = self.runNode(name)
                if calcError != 0:
                    _log.error("runGraph(%s): calcError=%d", name, calcError)
                    self.setErrorCode(1)
                    return

                for e in self.edges:
                    if e.start == name and e.tear == False and e.active == True:
                        _log.debug("runGraph(%s): transfer edge", name)
                        e.transferInformation(self)

    def runNode(self, name):
        """
        Run the calculations for the node named name
        """
        node = self.nodes[name]
        node.runCalc()
        return node.calcError

    def transferVars(self, edgeList):
        for i in edgeList:
            e = self.edges[i]
            e.transferInformation(self)

    def addNode(self, name, x=0, y=0, z=0):
        # Need to add the node to the variables first
        # for the time being
        if not name in self.input:
            self.input.addNode(name)
        if not name in self.output:
            self.output.addNode(name)
        if not name in self.input_vectorlist:
            self.input_vectorlist.addNode(name)
        if not name in self.output_vectorlist:
            self.output_vectorlist.addNode(name)
        self.nodes[name] = Node(x, y, z, parent=self, name=name)
        return self.nodes[name]

    def addEdge(self, name1, name2, curve=0.0):
        self.edges.append(edge(name1, name2, curve))
        return len(self.edges) - 1

    def deleteEdge(self, i):
        self.edges.pop(i)

    def deleteEdges(self, el):
        el = sorted(list(set(el)), reverse=True)
        for i in el:
            self.deleteEdge(i)

    def deleteNodes(self, nl):
        nl = list(set(nl))
        for n in nl:
            self.deleteNode(n)

    def deleteNode(self, i):
        self.nodes.pop(i)
        self.input.pop(i)
        self.output.pop(i)
        j = 0
        while j < len(self.edges):
            if self.edges[j].start == i or self.edges[j].end == i:
                self.deleteEdge(j)
            else:
                j += 1

    def renameNode(self, oldName, newName):
        if newName == oldName:
            return
        # Check if new name is in use
        # if it is don't rename
        if newName in list(self.nodes.keys()):
            raise (f"Can't rename to {newName}, name already in use.")
        # search edges and change names
        for edge in self.edges:
            if edge.start == oldName:
                edge.start = newName
            if edge.end == oldName:
                edge.end = newName
        # move node in dict
        self.nodes[newName] = self.nodes.pop(oldName)
        self.input[newName] = self.input.pop(oldName)
        self.output[newName] = self.output.pop(oldName)

    def nEdges(self, includeTear=True, includeInactive=False):
        # returns the number of edges in the graph
        # options for excluding tear edges and inactive edges
        ntear = 0
        ninactive = 0
        if not includeTear and not includeInactive:
            for e in self.edges:
                if e.tear and not includeTear:
                    ntear += 1
                if not e.acitve and not includeInactive:
                    ninactive += 1
        return len(self.edges) - ntear - ninactive

    def nNodes(self):
        """
        returns the number of nodes in a graph
        """
        return len(self.nodes)

    def adjMatrix(
        self,
        includeTear=False,
        includeInactive=False,
        subGraphNodes=None,
        subGraphEdges=None,
    ):
        """
        This function returns the common graph data structures:
            adjacency matrix
            reverse adjacency matrix
            adjacency lists
            reverse adjacency lists
        These structures are commonly used by graph algorithms.

        By default this function ignores inactive and tear edges,
        but they can be included optionally.  This can also be used
        to cunstruct data structures for subgraphs.  The sub graphs
        are specified by providing a list of node names and/or a
        list of edge indexes.

        Since the adjacency matrix gives the nodes indexs this
        function provides a way to get the index form the name
        or the name from the index.  The results returned are

        nn - dictionary to look up node index in adj matrix

        """
        nn = dict()  # matrix index lookup from node names
        ni = []  # node name lookup from matrix index
        mat = []  # adjacency matrix
        adj = []  # adjacency lists
        adjR = []  # reverse adjacency lists
        adjEdge = []  # edge adj lists (edges that are adj to node)
        adjEdgeR = []  # edge reverse adj lists
        # if no subgraph nodes where specified use the whole graph
        if subGraphNodes == None:
            subGraphNodes = list(self.nodes.keys())
        # if no subgraph edges where specified use the whole graph
        if subGraphEdges == None:
            subGraphEdges = list(range(len(self.edges)))
        # find edges to nodes not in the sub graph, also tear and inactive edges depending on options
        delSet = []  # set of edges to delete
        for i in range(len(subGraphEdges)):
            edge = self.edges[subGraphEdges[i]]
            if edge.tear and not includeTear:
                delSet.append(i)
                continue
            if not edge.active and not includeInactive:
                delSet.append(i)
                continue
            if not edge.start in subGraphNodes:
                delSet.append(i)
                continue
            if not edge.end in subGraphNodes:
                delSet.append(i)
                continue
        # remove edges from subgraph
        for i in reversed(delSet):
            subGraphEdges.pop(i)
        # Create lookup tables for
        # node name -> node index and node index -> node name
        i = 0
        ni = [""] * len(self.nodes)
        for key in self.nodes:
            if key in subGraphNodes:
                nn[key] = i
                ni[i] = key
                i += 1
        # Initialize empty adj matrix and lists
        for i in range(len(nn)):
            mat.append([False] * len(nn))
            adj.append([])
            adjR.append([])
            adjEdge.append([])
            adjEdgeR.append([])
        # Create adjacency matrix and adjacency lists
        for ei in range(len(self.edges)):
            if ei in subGraphEdges:
                edge = self.edges[ei]
                i = nn[edge.start]
                j = nn[edge.end]
                mat[i][j] = True
                adj[i].append(j)
                adjR[j].append(i)
                adjEdge[i] = ei
                adjEdgeR[j] = ei
        return (nn, ni, mat, adj, adjR, adjEdge, adjEdgeR, subGraphEdges)

    def adjLists(self):
        # adds a list of adjacent node to each node
        for key, node in self.nodes.items():
            node.adj = []
            node.revAdj = []
            node.adjEdge = []
            node.revAdjEdge = []
            node.adjT = []
            node.revAdjT = []
            node.adjEdgeT = []
            node.revAdjEdgeT = []
        i = 0
        for edge in self.edges:
            self.nodes[edge.start].adj.append(edge.end)
            self.nodes[edge.end].revAdj.append(edge.start)
            self.nodes[edge.start].adjEdge.append(edge)
            self.nodes[edge.end].revAdjEdge.append(edge)
            if edge.tear == False:
                self.nodes[edge.start].adjT.append(edge.end)
                self.nodes[edge.end].revAdjT.append(edge.start)
                self.nodes[edge.start].adjEdgeT.append(edge)
                self.nodes[edge.end].revAdjEdgeT.append(edge)
            i += 1

    def getEdgeIndex(self, vkey, wkey):
        # get index of edge from v to w returns None if no edge from v to w
        # multiple edges are not allowed
        indx = None
        for i in range(0, len(self.edges)):
            if self.edges[i].start == vkey:
                if self.edges[i].end == wkey:
                    indx = i
                    break
        return indx

    def setTearSet(self, tSet):
        # mark the given list of edges as tear edges
        # mark edges not in the list as not tear edges
        for edge in self.edges:
            edge.tear = False
        for i in tSet:
            self.edges[i].tear = True

    def cycleEdgeMatrix(self):
        # Return a cycle-edge incidence matrix, and cycle lists
        # The first list is a list of lists of all nodes in all cycles
        # The second list is a list of lists of all edges in all cycles
        [cycles, cycEdges] = self.allCycles()  # call cycle finding algorithm
        # Create empty incidence matrix
        ceMat = numpy.zeros((len(cycles), self.nEdges()), dtype=numpy.dtype(int))
        # Fill out incidence matrix
        for i in range(0, len(cycEdges)):
            for e in cycEdges[i]:
                ceMat[i, e] = 1
        return [ceMat, cycles, cycEdges]

    def allCycles(
        self,
        includeTear=True,
        includeInactive=False,
        subGraphNodes=None,
        subGraphEdges=None,
    ):
        """
        This function find all the cycles in a directed graph.
        The algorithm is based on Tarjan 1973 Enumeration of the
        elementary circuits of a directed graph,
        SIAM J. Comput. v3 n2 1973.
        ---Arguments---
        includeTear = {True, False} include or exclude tear edges
        includeInactive = {True, False} include or exclude
            edges marked inactive
        subGraphNodes = {None, []} if None consider all nodes,
            otherwise a list of nodes in a subgraph
        subGraphEdges = {None, []} if None consider all edges
            attached at both ends to a node in the subgraph.
            Otherwise a list of edge indexes in a subgraph only
            edges attached at both ends to a node in the subgraph
            will be included.
        ---Return Value---
        return[0] = a list of lists of nodes in each cycle
        return[1] = a list of lists of edges in each cycle
        """

        def backtrack(v):
            # sub-function recursive part
            f = False
            pointStack.append(v)
            mark[v] = True
            markStack.append(v)
            ws = list(adj[v])
            for w in ws:
                if w < s:
                    adj[v].remove(w)
                elif w == s:
                    f = True
                    cycles.append(list(pointStack))
                elif not mark[w]:
                    g = backtrack(w)
                    f = f or g
            if f == True:
                while markStack[-1] != v:
                    u = markStack.pop()
                    mark[u] = False
                markStack.pop()
                mark[v] = False
            pointStack.pop()
            return f

        # main part (and first call to above recursive function)
        # make adj lists
        [
            nodeIndexLookup,
            nodeNameLookup,
            adjMat,
            adj,
            adjR,
            adjEdges,
            adjEdgesR,
            subGraphEdges,
        ] = self.adjMatrix(includeTear, includeInactive, subGraphNodes, subGraphEdges)
        pointStack = []  # node stack
        markStack = []  # nodes that have been marked
        cycles = []  # list of cycles found
        mark = [False] * len(nodeNameLookup)  # if a node is marked
        for s in range(len(nodeNameLookup)):
            backtrack(s)
            while len(markStack) > 0:
                i = markStack.pop()
                mark[i] = False
        # Cycle is now a list of node indexes need to turn them back into names
        for cycle in cycles:
            for i in range(len(cycle)):
                cycle[i] = nodeNameLookup[cycle[i]]
        # Now find list of edges in the cycle
        edgeCycles = []
        for cyc in cycles:
            ecyc = []
            for i in range(0, len(cyc) - 1):
                ecyc.append(self.getEdgeIndex(cyc[i], cyc[i + 1]))
            ecyc.append(
                self.getEdgeIndex(cyc[-1], cyc[0])
            )  # edge from last index to cycle start
            edgeCycles.append(ecyc)
        return [cycles, edgeCycles]

    def stronglyConnectedSubGraphs(
        self,
        includeTear=True,
        includeInactive=False,
        subGraphNodes=None,
        subGraphEdges=None,
    ):
        """
        This is an algorithm for finding strongly connected components in a graph. It is based on
        Tarjan. 1972 Depth-First Search and Linear Graph Algorithms, SIAM J. Comput. v1 no. 2 1972

        Arguments:

        includeTear = {True, False} include or exclude tear edges
        includeInactive = {True, False} include or exclude edges marked inactive
        subGraphNodes = {None, []} if none consider all nodes, other wise a list of nodes in a subgraph
        subGraphEdges = {None, []} if none consider all edges attached at both ends to a node in the
                                    subgraph.  Otherwise a list of edge indexes in a subgraph only edges
                                    attached at both ends to a node in the subgraph will be inclued.

        Return Value:

        This function returns a list containing several results.
        result[0] = list of lists of node in each strongly connected component (SCC)
        result[1] = list of lists of edges in each SCC
        result[2] = list of lists of out edges in each SCC. (edges that start in a SCC but end outside)
        result[3] = list of lists of in edges in each SCC. (edges that end in a SCC but start outside)
        result[4] = list of order in which to calculate SCCs (the way the information flows, the SCC are a tree)
        """

        def sc(v, stk, depth, strngComps):
            # recursive sub-function for backtracking
            ndepth[v] = depth
            back[v] = depth
            depth += 1
            stk.append(v)
            for w in adj[v]:
                if ndepth[w] == None:
                    sc(w, stk, depth, strngComps)
                    back[v] = min(back[w], back[v])
                elif w in stk:
                    back[v] = min(back[w], back[v])
            if back[v] == ndepth[v]:
                scomp = []
                while True:
                    w = stk.pop()
                    scomp.append(nodeNameLookup[w])
                    if w == v:
                        break
                strngComps.append(scomp)
            return depth

        # Generate the adjacency matrix for the graph or subgraph
        [
            nodeIndexLookup,
            nodeNameLookup,
            adjMat,
            adj,
            adjR,
            adjEdges,
            adjEdgesR,
            subGraphEdges,
        ] = self.adjMatrix(includeTear, includeInactive, subGraphNodes, subGraphEdges)
        # depth      = 0   #depth index for depth first search
        stk = []  # node stack
        strngComps = []  # list of strongly connected components
        ndepth = [None] * len(nodeNameLookup)
        back = [None] * len(nodeNameLookup)
        # find the SCCs
        for v in range(len(nodeNameLookup)):
            if ndepth[v] == None:
                sc(v, stk, 0, strngComps)
        sccNodes = strngComps
        # Find the rest of the information about SCCs given the node partition
        sccEdges = []
        outEdges = []
        inEdges = []
        for nset in strngComps:
            [e, ie, oe] = self.subGraphEdges(nset)
            sccEdges.append(e)
            inEdges.append(ie)
            outEdges.append(oe)
        sccOrder = self.sccOrderCalc(sccNodes, inEdges, outEdges)
        return (sccNodes, sccEdges, outEdges, inEdges, sccOrder)

    def calculationOrder(self, roots=[], subNodes=None, subEdges=None):
        # Make adjacency lists
        if not self.checkTearStatus():
            [tearSets, ub1, ub2] = self.selectTear()
            self.setTearSet(tearSets[0])
        [nn, ni, mat, adj, adjR, adjEdge, adjEdgeR, subGraphEdges] = self.adjMatrix(
            False, False, subNodes, subEdges
        )
        rootsIndex = None
        order = []
        if len(roots) > 0:
            rootsIndex = []
            for name in roots:
                rootsIndex.append(nn[name])
        else:
            rootsIndex = None
        orderIndex = self.treeOrder(adj, adjR, rootsIndex)
        for i in range(len(orderIndex)):
            order.append([])
            for j in range(len(orderIndex[i])):
                order[i].append(ni[orderIndex[i][j]])
        return order

    def selectTear(self):
        """
        This finds optimal sets of tear edges based on two criteria.
        The primary objective is to minimize the maximum number of
        times any cycle is broken.  The seconday criteria is to
        minimize the number of tears.  This function uses a branch
        and bound type approach.

        Output:
            List of lists of tear sets.  All the tear sets returned
            are equally good there are often a very large number of
            equally good tear sets.

        Improvemnts for the future.
        I think I can imporve the efficency of this, but it is good
        enough for now.  Here are some ideas for improvement:
        1) Reduce the number of redundant solutions.  It is possible
           to find tears sets [1,2] and [2,1].  I eliminate
           redundent solutions from the results, but they can
           occur and it reduces efficency
        2) Look at strongly connected components instead of whole
           graph this would cut back on the size of graph we are
           looking at.  The flowsheets are rearly one strongly
           conneted componet.
        3) When you add an edge to a tear set you could reduce the
           size of the problem in the branch by only looking at
           strongly connected components with that edge removed.
        4) This returns all equally good optimal tear sets.  That
           may not really be nessicary.  For very large flowsheets
           There could be an extreemly large number of optimial tear
           edge sets.
        """

        def sear(depth, prevY):
            # This is a recursive function for generating tear sets
            # it selects one edge from a cycle, then calls itself
            # to select an edge from the next cycle.  It is a branch
            # and bound search tree to find best tear sets
            #
            # The function returns when all cycles are torn (which
            # may be before an edge was selected from each cycle if
            # cycles contain common edges.
            for i in range(0, len(cycleEdges[depth])):
                # Loop through all the edges in cycle with index depth
                y = list(prevY)  # get list of already selected tear stream
                y[cycleEdges[depth][i]] = 1
                Ay = numpy.dot(A, y)  # calculate the number of times each cycle is torn
                maxAy = max(Ay)
                sumY = sum(y)
                if maxAy > upperBound[0]:
                    # breaking a cycle to many times
                    continue  # done looking here branch is no good
                elif maxAy == upperBound[0] and sumY > upperBound[1]:
                    # too many tears
                    continue  # done looking here branch is no good
                # call self at next depth where a cycle is not broken
                if min(Ay) > 0:
                    if maxAy < upperBound[0]:
                        upperBound[0] = maxAy  # Most important factor
                        upperBound[1] = sumY  # Second most important
                    elif sumY < upperBound[1]:
                        upperBound[1] = sumY
                    # record solution
                    ySet.append([list(y), maxAy, sumY])
                else:
                    for j in range(depth + 1, nr):
                        if Ay[j] == 0:
                            sear(j, y)

        # ---END sear FUNCTION---
        # Get a quick and I think pretty good tear set for upper bound
        tearUB = self.tearUpperBound()
        # Find all the cycles in a graph and make cycle-edge matrix A
        # rows of A are cycles and columns of A are edges
        # 1 if a edge is in a cycle 0 otherwise
        [A, cycles, cycleEdges] = self.cycleEdgeMatrix()  #
        (nr, nc) = A.shape
        if nr == 0:  # no cycles no tear edges and we are done
            return [[[]], 0, 0]
        # There are cycles so find tear edges.
        y_init = [False] * self.nEdges()  # edge j in tear set?
        for jj in tearUB:
            y_init[jj] = 1  # y for initial u.b. solution
        Ay_init = numpy.dot(A, y_init)  # number of times each loop torn
        upperBound = [max(Ay_init), sum(y_init)]  # set two upper bounds
        # The fist upper bound is on number of times a loop is broken
        # Second upper bound is on number of tears
        y_init = [False] * self.nEdges()  # clear y vector to start search
        ySet = []  # a list of tear sets
        # in ySet the fist index is the tear set
        # three element are stored in each tear set:
        # 0 = y vector, 1 = max(Ay), 2 = sum(y)
        # Call recursive function to find tear sets
        st = time.time()
        sear(0, y_init)
        # screen found tear sets found
        # A set can be recorded before a change in upper bound so can
        # just trhow out sets with objectives higher than u.b.
        deleteSet = []  # vector of tear set indexes to delete
        for i in range(0, len(ySet)):
            if ySet[i][1] > upperBound[0]:
                deleteSet.append(i)
            elif ySet[i][1] == upperBound[0] and ySet[i][2] > upperBound[1]:
                deleteSet.append(i)
        for i in reversed(deleteSet):
            del ySet[i]
        # Check for duplicates and delete them
        deleteSet = []
        for i in range(0, len(ySet) - 1):
            if i in deleteSet:
                continue
            for j in range(i + 1, len(ySet)):
                if j in deleteSet:
                    continue
                for k in range(0, len(y_init)):
                    eq = True
                    if ySet[i][0][k] != ySet[j][0][k]:
                        eq = False
                        break
                if eq == True:
                    deleteSet.append(j)
        for i in reversed(sorted(deleteSet)):
            del ySet[i]
        # Turn the binary y vectors into lists of edges
        es = []
        for y in ySet:
            edges = []
            for i in range(0, len(y[0])):
                if y[0][i] == 1:
                    edges.append(i)
            es.append(edges)
        # Log ammount of time required to find tear sets
        _log.info("Teat steam search, elapsed time: " + str(time.time() - st))
        return [es, upperBound[0], upperBound[1]]

    def tearUpperBound(self):
        """
        This function quickly finds a sub-optimal set of tear
        edges.  This serves as an inital upperbound when looking
        for an optimal tear set.  Having an inital upper bound
        improves efficenty.

        This works by constructing a search tree and just makes a
        tear set out of all the back edges.
        """

        def cyc(vkey, vnode, depth):
            # this is a recursive function
            vnode.depth = depth
            depth += 1
            for wkey in vnode.adj:
                wnode = self.nodes[wkey]
                if wnode.depth == None:
                    wnode.parent = vkey
                    cyc(wkey, wnode, depth)
                elif wnode.depth < vnode.depth:
                    # found a back edge add to tear set
                    tearSet.append(self.getEdgeIndex(vkey, wkey))

        # End recursive part
        # main part
        self.adjLists()
        depth = 0
        tearSet = []  # list of back/tear edges
        for key, node in self.nodes.items():
            node.depth = None
            node.parent = None
        for vkey, vnode in self.nodes.items():
            if vnode.depth == None:
                cyc(vkey, vnode, depth)
        return tearSet

    def subGraphEdges(self, nodes):
        """
        This function returns a list of edges that are included in
        a subgraph given by a list of node names.  The function
        returns a list of three lists:
        Output List Elements:
        0 -- List of edges in the subgraph
        1 -- List of in edges to subgraph (edges that originate
            outside the subgraph but terminate in the subgraph)
        2 -- List of out edges from subgraph (originate but don't
            terminate in the subgraph)

        Arguments:
        nodes -- list of subgraph node names
        """
        # Given a subgraph defined by a set of nodes
        # find the edges in the subgraph
        e = []  # edges that connect two nodes in the subgraph
        ie = (
            []
        )  # in edges end at a node in the subgraph but end at a node not in the subgraph
        oe = (
            []
        )  # out edges start at a node in the subgraph but end at a node not in the subgraph
        for i in range(len(self.edges)):
            if self.edges[i].start in nodes:
                if self.edges[i].end in nodes:
                    # its in the sub graph
                    e.append(i)
                else:
                    # its an out edge of the subgraph
                    oe.append(i)
            elif self.edges[i].end in nodes:
                # its a in edge of the subgraph
                ie.append(i)
        return [e, ie, oe]

    def sccOrderCalc(self, sccNodes, ie, oe):
        """
        This determines the order in witch to do calculations
        for strongly connected components, it is used to help
        determine the most efficient order to solve tear streams

        if you have a graph like  SCC0--+-->--SCC1
                                        |
                                        +-->--SCC2
        you would want to do tear streams in SCC0 before SCC1
        and SCC2 to prevent extra iterations

        This just makes and adjacency list with the SCCs as nodes
        and calls the tree order function.

        Arguments
        sccNodes: List on lists of node names in the SCCs The top
            level list is the list of SCCs the list elements are
            lists of nodes in the SCC
        ie: list of lists of in edges to SCCs
        oe: list of lists of out edged to SCCs

        """
        # initialize empty adjacency lists
        adjlist = []  # SCC adjacency list
        adjlistR = []  # SCC reverse adjacency list
        for i in range(len(sccNodes)):
            adjlist.append([])
            adjlistR.append([])
        # create SCC adjacency lists
        done = False
        for i in range(len(sccNodes)):
            for j in range(len(sccNodes)):
                for ine in ie[i]:
                    for oute in oe[j]:
                        if ine == oute:
                            adjlist[j].append(i)
                            adjlistR[i].append(j)
                            done = True
                    if done:
                        break
                if done:
                    break
            done = False
        # The calculation order starts with root SCCs first
        return self.treeOrder(adjlist, adjlistR)

    def treeOrder(self, adj, adjR, roots=None):
        """
        This function determines the ordering of nodes in a directed
        tree.  This is a generic function that can opertate on any
        given tree represented the the adjaceny and reverse
        adjacency lists.  **If the adjacency list does not represent
        a tree the results are not valid.

        In the returned order, it is sometimes possible for more
        than one node to be caclulated at once.  So a list of lists
        is returned by this function.  These represent a bredth
        first search order of the tree.  Following the order all
        nodes that lead to a particular node will be visited
        before it.

        Arguments:
        adj: an adjeceny list for a directed tree.  This uses
            generic integer node indexes, not node names form the
            graph (self).  This allows this to be used on sub-graphs
            and graps of components more easily
        adjR: the reverse adjacency list coresponing to adj
        roots: list of node indexes to start from.  These do not
            need to be the root nodes of the tree, in some cases
            like when a node changes the changes may only affect
            nodes reachable in the tree from the changed node, in
            the case that roots are supplied not all the nodes in
            the tree may appear in the ordering.  If no roots are
            supplied, the roots of the tree are used.
        """
        adjR = copy.deepcopy(adjR)
        for i, l in enumerate(adjR):
            adjR[i] = set(l)
        if roots == None:
            roots = []
            mark = [True] * len(adj)  # mark all nodes if no roots specified
            r = [True] * len(adj)
            # no root specified so find roots of tree
            for i in adj:  # the roots are not adjacent to anything
                for j in i:  # remember this is directed graph
                    r[j] = False
            for i in range(len(r)):  # make list of roots
                if r[i]:
                    roots.append(i)
        else:  # if roots are specified mark descendants
            mark = [False] * len(adj)
            lst = roots
            while len(lst) > 0:
                lst2 = []
                for i in lst:
                    mark[i] = True
                    lst2 += adj[i]
                lst = set(lst2)  # remove dupes
        # Now we have list of roots, and roots and their desendants are
        # marked
        ndepth = [None] * len(adj)
        lst = copy.deepcopy(roots)
        order = []
        checknodes = set()  # list of candidate nodes for next depth
        for i in roots:  # nodes adjacent to roots are candidates
            checknodes.update(adj[i])
        depth = 0
        #
        while len(lst) > 0:
            order.append(lst)
            depth += 1
            lst = []  # nodes to add to the next depth in order
            delSet = set()  # nodes to delete from checknodes
            checkUpdate = set()  # nodes to add to checkNodes
            for i in checknodes:
                if ndepth[i] != None:
                    # This means there is a cycle in the graph
                    # this will lead to nonsense so throw exception
                    raise GraphEx(code=201)
                remSet = set()  # to remove from a nodes rev adj list
                for j in adjR[i]:
                    if j in order[depth - 1]:
                        # ancestor already placed
                        remSet.add(j)
                    elif mark[j] == False:
                        # ancestor doesn't descend from root
                        remSet.add(j)
                # delete parents from rev adj list if they were found
                # to be already placed or not in subgraph
                adjR[i] = adjR[i].difference(remSet)
                # if rev adj list is empty, all ancestors
                # have been placed so add node
                if len(adjR[i]) == 0:
                    ndepth[i] = depth
                    lst.append(i)
                    delSet.add(i)
                    checkUpdate.update(adj[i])
            # Delete the nodes that were added from the check set
            checknodes = checknodes.difference(delSet)
            checknodes = checknodes.union(checkUpdate)
        return order
