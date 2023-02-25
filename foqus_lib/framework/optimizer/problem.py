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
"""problem.py

* This performs optimization problem evaluation

John Eslick, Carnegie Mellon University, 2014
"""

import copy
import time
import math
import csv
import json
import logging
import operator
from foqus_lib.framework.foqusOptions.optionList import optionList
from foqus_lib.framework.at_dict.at_dict import AtDict
from functools import reduce


class objectiveFunction(object):
    def __init__(self, pycode="", ps=1, failval=1000):
        self.pycode = pycode
        self.fail = failval
        self.penScale = ps

    def saveDict(self):
        sd = dict()
        sd["pycode"] = self.pycode
        sd["fail"] = self.fail
        sd["penScale"] = self.penScale
        return sd

    def loadDict(self, sd):
        self.pycode = sd["pycode"]
        self.fail = sd["fail"]
        self.penScale = sd["penScale"]


class inequalityConstraint(object):
    def __init__(self, pc="", ps=100, pf="Linear"):
        self.pycode = pc
        self.penalty = ps
        self.penForm = pf

    def saveDict(self):
        sd = dict()
        sd["pycode"] = self.pycode
        sd["penalty"] = self.penalty
        sd["penForm"] = self.penForm
        return sd

    def loadDict(self, sd):
        self.pycode = sd["pycode"]
        self.penalty = sd["penalty"]
        self.penForm = sd["penForm"]


class problem(object):
    OBJ_TYPE_EVAL = 0  # use eval to cal objective
    OBJ_TYPE_PARAM = 1  # parameter estimation type objective
    OBJ_TYPE_OUU = 2  # opt under uncertainty type onjective
    OBJ_TYPE_CUST = 3  # custom objective totally open python code

    def __init__(self):
        self.obj = []  # Objective functions for eval type
        self.g = []  # Inequality constraints for eval type
        self.custpy = ""  # custom python objective code
        self.objtype = self.OBJ_TYPE_EVAL  # objective evalulation type
        self.v = []  # List of decision variable names (subset of inputs)
        self.vs = []  # List of sampled variable names (subset of inputs)
        self.samp = {}  #
        self.solver = None  # should be a solver name string
        self.solverOptions = {}  # option list object for solver options
        self.initSolverParameters()
        self.runMethod = 0  # 0 -- run locally, 1 -- use turbine/foqus

    def initSolverParameters(self):
        # Attributes used to interact with solver, don't need to save
        self.solverStart = time.time()
        self.userInterupt = False
        self.maxTimeInterupt = False
        self.maxSolverTime = 48
        self.totalSamplesRead = 0
        self.totalSampleErrors = 0
        self.iterationNumber = 0
        self.storeResults = True

    def run(self, dat):
        self.dat = dat
        slv = dat.optSolvers.plugins[self.solver].opt(dat)
        slv.options.loadValues(self.solverOptions[self.solver])
        slv.start()
        return slv

    def saveDict(self):
        """
        Save an optimization problem to a dictionary.  Usually used to write a
        problem to a json file.
        """
        sd = {
            "obj": [o.saveDict() for o in self.obj],
            "g": [g.saveDict() for g in self.g],
            "objtype": self.objtype,
            "custpy": self.custpy,
            "v": self.v,
            "vs": self.vs,
            "samp": self.samp,
            "solver": self.solver,
            "solverOptions": {},
        }
        for skey in self.solverOptions:
            sd["solverOptions"][skey] = {}
            for okey, ov in self.solverOptions[skey].items():
                sd["solverOptions"][skey][okey] = ov
        return sd

    def loadDict(self, sd):
        """
        Load the optimization problem from a dictionary.  Usualy
        used when reading a problem back in from a json file.
        """
        self.obj = []
        self.g = []
        self.h = []
        self.objtype = sd.get("objtype", self.OBJ_TYPE_EVAL)
        self.custpy = sd.get("custpy", "")
        self.samp = sd.get("samp", {})
        self.v = sd.get("v", [])
        self.vs = sd.get("vs", [])
        self.solver = sd.get("solver", None)
        #
        for d in sd.get("obj", []):
            self.obj.append(objectiveFunction())
            self.obj[-1].loadDict(d)
        #
        for d in sd.get("g", []):
            self.g.append(inequalityConstraint())
            self.g[-1].loadDict(d)
        #
        self.solverOptions = {}
        if not "solverOptions" in sd:
            return
        for dkey, d in sd["solverOptions"].items():
            self.solverOptions[dkey] = {}
            for okey, ov in d.items():
                self.solverOptions[dkey][okey] = ov

    def loadSamples(self, fname):
        with open(fname, "r") as f:
            cr = csv.reader(f)
            head = [h.strip() for h in next(cr)]
            for h in head:
                if not self.samp.get(h, False):
                    self.samp[h] = []
            for row in cr:
                for i, el in enumerate(row):
                    self.samp[head[i]].append(json.loads(el))

    def fullfactorial(self, sdict):
        """
        Generate full factorial samples
        """
        w = []
        mapDict = {}
        j = 0
        for key, lst in sdict.items():
            w.append(lst)
            mapDict[key] = j
            j += 1
        # w is a list of lists of values
        # now we will generate a sample for every combination of w's
        c = [0] * len(w)  # location vector
        cmax = [0] * len(w)
        for i in range(len(w)):
            cmax[i] = len(w[i])
        # w2 is a list of all the samples
        # just initialize it to all zeros
        w2 = [0] * len(w)
        for i in range(len(w2)):
            w2[i] = [0.0] * reduce(operator.mul, cmax, 1)
        j = 0
        while c[0] < cmax[0]:
            for i in range(len(w)):
                w2[i][j] = w[i][c[i]]
            j += 1
            for i in reversed(list(range(len(c)))):
                c[i] += 1
                if c[i] == cmax[i] and i != 0:
                    c[i] = 0
                else:
                    break
        # now copy samples from w2 to problem sample list
        # j is now number of samples
        nsamp = j
        sa = {}
        for i in range(nsamp):
            for key, j in mapDict.items():
                sa[key] = w2[j][i]
            self.addSample(sa)

    def deleteSamples(self, rows):
        rows = sorted(rows, reverse=True)
        for key, item in self.samp.items():
            for r in rows:
                del item[r]

    def clearSamples(self):
        self.samp = {}

    def numSamples(self):
        if len(self.samp) == 0:
            n = 0
        else:
            n = len(list(self.samp.values())[0])
        return n

    def addSampleVar(self, vname):
        """
        Adds a variable to the sample dict, not to the sample var
        list (self.vs).  I keep track of samples for varaibles that
        are not sample variables just in case the user changes their
        mind about the set of sample variables.  All the defined
        samples won't be lost.
        """
        n = self.numSamples()
        if vname not in self.samp:
            if n > 0:
                self.samp[vname] = [float("nan")] * n
            else:
                self.samp[vname] = []

    def addSample(self, samples):
        for key in samples:
            if key not in self.samp:
                self.addSampleVar(key)
        for key in self.samp:
            self.samp[key].append(samples.get(key, float("nan")))

    def runSamples(self, X, slv):
        """Runs the flowsheet samples for the objective calculation

        Args:
        X: a list of flat vector of descision variable values.
            The variableordering is given by the list self.v
        gr: is the graph (flowsheet) object that will be used to
            run the samples

        If a set of samples is defined by self.samp, each flowsheet
        will be run number of smapls times for each X
        """
        self.userInterupt = False
        self.maxTimeInterupt = False
        snum = 1
        # Setup new sample vectors that have the decision and sample
        # variables and the
        samp = []  # the sample set for FOQUS graph
        if len(self.vs) > 0 and self.numSamples() > 0:
            snum = self.numSamples()
            for xvec in X:
                vals = slv.graph.input.unflatten(self.v, xvec, unScale=True)
                for s in range(self.numSamples()):
                    samp.append(copy.deepcopy(self.inpDict))
                    for nkey in vals:
                        for vkey in vals[nkey]:
                            samp[-1][nkey][vkey] = vals[nkey][vkey]
                    # Now add on sample variable info
                    for vname in self.vs:
                        vname2 = vname.split(".", 1)
                        samp[-1][vname2[0]][vname2[1]] = self.samp[vname][s]
        else:
            for xvec in X:  # create sample set in correct format
                # need to unscale the inputs the solver sees to run sims
                vals = slv.graph.input.unflatten(self.v, xvec, unScale=True)
                samp.append(copy.deepcopy(self.inpDict))
                for nkey in vals:
                    for vkey in vals[nkey]:
                        samp[-1][nkey][vkey] = vals[nkey][vkey]
        nsam = len(samp)  # number of samples this iteration
        # sumbmit samples to a new graph thread that will run them
        if self.dat.foqusSettings.runFlowsheetMethod == 0:
            # run the flowsheet in this FOQUS
            gt = slv.graph.runListAsThread(samp)
        elif self.dat.foqusSettings.runFlowsheetMethod == 1:
            # run the flowsheet using turbine/foqus consumer
            # first save a session file (need to upload to turbine)
            gt = slv.graph.runListAsThread(samp, useTurbine=True)
        else:
            raise Exception("Invalid Run Mode")
        # Start monitoring the jobs
        finished = 0  # number of samples that have finished this it
        readres = [False] * len(gt.res)
        goagain = True
        while goagain:  # wait for samples to run
            if slv.stop.isSet():  # check for stop flag
                self.userInterupt = True
                gt.terminate()
                # keep wait loop going, gt should kill current job
                # and fill rest of jobs with error status then stop
            if self.maxSolverTime > 0.0002:
                if (time.time() - self.solverStart) / 3600.0 > self.maxSolverTime:
                    self.maxTimeInterupt = True
                    gt.terminate()
            gt.join(2)  # wait for gt to finish, time out after 2 sec
            goagain = gt.is_alive()
            with gt.statLock:
                status = copy.copy(gt.status)
            if status["finished"] != finished or not goagain:
                # if it is the last time through because the thread is
                # no longer alive make sure to read the last of the
                # results, the finished counter goes up before the
                # job results are retrived from turbine
                finished = status["finished"]
                # Put out progress monitor message to queue
                slv.resQueue.put(
                    [
                        "PROG",
                        finished,
                        nsam,
                        status["error"],
                        self.iterationNumber,
                        self.totalSamplesRead + finished,
                        self.totalSampleErrors + status["error"],
                    ]
                )
                # get sample result
                with gt.resLock:
                    if self.storeResults:
                        for i in range(len(gt.res)):
                            if not readres[i] and gt.res_fin[i] != -1:
                                readres[i] = True
                                slv.graph.results.addFromSavedValues(
                                    self.storeResults,
                                    "res_{0:05d}_{1:05d}".format(
                                        self.iterationNumber, i
                                    ),
                                    None,
                                    gt.res[i],
                                )
        self.totalSamplesRead = self.totalSamplesRead + nsam
        self.totalSampleErrors = self.totalSampleErrors + status["error"]
        self.gt = gt
        if gt.errorStat == 40:
            raise Exception("Error connecting to Turbine")
        inputvectorscopy = slv.graph.input_vectorlist.copy()
        outputvectorscopy = slv.graph.output_vectorlist.copy()
        for n in slv.graph.nodes:
            mergecopy = inputvectorscopy[n].keys() | outputvectorscopy[n].keys()
            if any(k in self.obj[0].pycode for k in mergecopy):
                return self.calculateObjVector(gt.res, nsamples=snum)
            else:
                return self.calculateObj(gt.res, nsamples=snum)

    def prep(self, slv):
        """
        do whatever can be done outside the objective calucualtion
        loop to speed things up
        """
        if self.objtype == self.OBJ_TYPE_CUST:
            exec(self.custpy, globals())
            self.custObjFunc = objfunc  # pylint: disable=undefined-variable
        self.inpDict = slv.graph.saveValues()["input"]

    def calculateObj(self, svlist, nsamples=1):
        """
        Do some commnon preliminary setup then call the right type
        of objective calculation.

        svlist is a list of flowsheet evaluation results
        nsamples is the number of flowsheet calculations that go
            into each objective evaluation.  svlist is arranged
            so that there are blocks of samples use to cacluatate
            objective functions
        """
        numObj = len(svlist) // nsamples  # number of obj. func. evals.
        res = [[float("nan")]] * numObj
        const = [[0.0]] * numObj
        pen = [[0.0]] * numObj
        for obj_index in range(numObj):
            # split up sv lists into parts for objcalcs
            istart = obj_index * nsamples
            model_res = svlist[istart : istart + nsamples]
            x = [0] * nsamples
            f = [0] * nsamples
            fail = [False] * nsamples
            for i, sv in enumerate(model_res):
                if sv is None:
                    # this is probably due to an exception being
                    # thrown during flowsheet eval so is an error.
                    fail[i] = True
                elif sv.get("input", None) is None:
                    # if the sample has no input something is wrong
                    fail[i] = True
                elif sv.get("output", None) is None:
                    # if the sample has no input something is wrong
                    fail[i] = True
                else:
                    if nsamples == 1:
                        x = sv["input"]
                        f = sv["output"]
                    else:
                        x[i] = sv["input"]
                        f[i] = sv["output"]
                    if sv["graphError"] != 0:
                        # This is just some error that was caught usually
                        # means failed to converge.
                        fail[i] = True
            (x, f) = self.get_at_dicts(x, f)
            if self.objtype == self.OBJ_TYPE_EVAL:
                (
                    res[obj_index],
                    const[obj_index],
                    pen[obj_index],
                ) = self.calculateObjSimpExp(x, f, fail)
            elif self.objtype == self.OBJ_TYPE_CUST:
                res[obj_index], const[obj_index], pen[obj_index] = self.custObjFunc(
                    x, f, fail
                )
        return res, const, pen

    def calculateObjVector(self, svlist, nsamples=1):
        """
        Do some commnon preliminary setup then call the right type
        of objective calculation.

        svlist is a list of flowsheet evaluation results
        nsamples is the number of flowsheet calculations that go
            into each objective evaluation.  svlist is arranged
            so that there are blocks of samples use to cacluatate
            objective functions
        """
        numObj = len(svlist) // nsamples  # number of obj. func. evals.
        res = [[float("nan")]] * numObj
        const = [[0.0]] * numObj
        pen = [[0.0]] * numObj
        for obj_index in range(numObj):
            # split up sv lists into parts for objcalcs
            istart = obj_index * nsamples
            model_res = svlist[istart : istart + nsamples]
            xvector = [0] * nsamples
            fvector = [0] * nsamples
            fail = [False] * nsamples
            for i, sv in enumerate(model_res):
                if sv is None:
                    # this is probably due to an exception being
                    # thrown during flowsheet eval so is an error.
                    fail[i] = True
                elif sv.get("input_vectorvals", None) is None:
                    # if the sample has no input something is wrong
                    fail[i] = True
                elif sv.get("output_vectorvals", None) is None:
                    # if the sample has no input something is wrong
                    fail[i] = True
                else:
                    if nsamples == 1:
                        xvector = sv["input_vectorvals"]
                        fvector = sv["output_vectorvals"]
                    else:
                        xvector[i] = sv["input_vectorvals"]
                        fvector[i] = sv["output_vectorvals"]
                    if sv["graphError"] != 0:
                        # This is just some error that was caught usually
                        # means failed to converge.
                        fail[i] = True
            (xvector, fvector) = self.get_at_dicts(xvector, fvector)
            if self.objtype == self.OBJ_TYPE_EVAL:
                (
                    res[obj_index],
                    const[obj_index],
                    pen[obj_index],
                ) = self.calculateObjSimpExp(xvector, fvector, fail)
            elif self.objtype == self.OBJ_TYPE_CUST:
                res[obj_index], const[obj_index], pen[obj_index] = self.custObjFunc(
                    xvector, fvector, fail
                )
        return res, const, pen

    def get_at_dicts(self, x, f):
        if isinstance(x, list):  # samples
            for i, xe in enumerate(x):
                x[i] = AtDict(x[i])
                for key in x[i]:
                    x[i][key] = AtDict(x[i][key])
        else:  # no samples
            x = AtDict(x)
            for key in x:
                x[key] = AtDict(x[key])
        if isinstance(f, list):  # samples
            for i, fe in enumerate(f):
                f[i] = AtDict(f[i])
                for key in f[i]:
                    f[i][key] = AtDict(f[i][key])
        else:  # no samples
            f = AtDict(f)
            for key in f:
                f[key] = AtDict(f[key])
        return x, f

    def calculateObjSimpExp(self, x, f, failVec):
        """ """
        res_e = []
        const_e = []
        fail = any(failVec)
        penTotal = 0.0
        for o in self.g:
            if fail:
                vi = 0
            else:
                vi = eval(o.pycode, locals())
            if vi <= 0:
                # if vi is negitive no constraint violation so set
                # vi to 0 for zero penalty
                vi = 0
            # calculate penalty
            if o.penForm == "Linear":
                pen = vi * o.penalty
            elif o.penForm == "Quadratic":
                pen = vi * vi * o.penalty
            elif o.penForm == "Step" and vi > 0.0:
                pen = o.penalty
            penTotal += pen
            const_e.append(pen)
        # Evaluate objective functions there may be more than one
        # this is to accomidate multi-objective optimization
        for o in self.obj:
            if fail:
                objfunc = o.fail
            else:
                try:
                    objfunc = eval(o.pycode, locals())
                    objfunc += penTotal * o.penScale
                except Exception as e:
                    logging.getLogger("foqus." + __name__).error(
                        "Error executing objective calc " + str(e)
                    )
                    objfunc = o.fail
            res_e.append(objfunc)
        return res_e, const_e, penTotal

    def check(self, graph, minVars=2, maxVars=1000, mustScale=True):
        """
        Check that an optimization problem is properly specified as
        much as possible.
        """
        # Check number of variables
        n = 0
        graph.generateGlobalVariables()
        sv = graph.saveValues()
        for vname in self.v:
            n += 1
            if mustScale and graph.input.get(vname).scaling == "None":
                return [
                    1,
                    (
                        "All optimization variables must be scaled "
                        "check decision variable scaling"
                    ),
                ]
            vmin = graph.input.get(vname).min
            vmax = graph.input.get(vname).max
            if vmax - vmin <= 1e-10:
                return [
                    1,
                    (
                        "The maximum must be greater than the "
                        "minimum for all decision variables"
                    ),
                ]
        if n < minVars:
            return [
                1,
                "Optimization method requires at least " + str(minVars) + " variables",
            ]
        if n > maxVars:
            return [
                1,
                "Optimization method can have at most " + str(minVars) + "variables",
            ]
        # Check Objective expressions
        if len(self.obj) < 1 and self.objtype == self.OBJ_TYPE_EVAL:
            return [
                1,
                (
                    "Must have at least one objective function.  If "
                    "a single objective method is used the first objective"
                    " will be be evaluated, and the rest will be ignored"
                ),
            ]
        # Check code for objectives
        #        sv = graph.saveValues()
        #        x = sv['input']
        #        f = sv['output']
        #        x = graph.input.valueDict(x)
        #        f = graph.output.valueDict(f)
        #        for o in self.obj:
        #            try:
        #                exec(o.pycode)
        #                objfunc + 1.0
        #            except Exception, e:
        #                return [
        #                    1,
        #                    "Error evaluating an objective function:"
        #                    " {0} error: {1} ".format(o.pycode ,str(e))]
        #        # check Constraint expressions
        #        for o in self.g:
        #            try:
        #                exec(o.pycode)
        #                violoation + 1.0
        #            except Exception, e:
        #                return [
        #                    1,
        #                    "Error evaluating a constraint function:"
        #                    " {0} error: {1} ".format(o.pycode ,str(e))]
        return [0, ""]
