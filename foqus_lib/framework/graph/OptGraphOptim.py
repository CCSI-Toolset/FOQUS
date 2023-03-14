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
import numpy
import time
import math
from foqus_lib.framework.graph.node import *
from foqus_lib.framework.graph.edge import *


class optimObj:
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


class optimInEq:
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


class optim:
    def __init__(self):
        self.obj = []  # Objective functions
        self.g = []  # Inequality constraints
        self.v = []  # List of input variable names that are decision variables
        self.x = dict()  # Inputs to simulation

    def saveDict(self):
        sd = dict()
        sd["obj"] = []
        sd["g"] = []
        sd["v"] = self.v
        #
        for g in self.g:
            sd["g"].append(g.saveDict())
        for o in self.obj:
            sd["obj"].append(o.saveDict())
        #
        return sd

    def loadDict(self, sd):
        self.obj = []
        self.g = []
        self.h = []
        self.v = sd["v"]
        #
        for d in sd["obj"]:
            self.obj.append(optimObj())
            self.obj[-1].loadDict(d)
        #
        for d in sd["g"]:
            self.g.append(optimInEq())
            self.g[-1].loadDict(d)

    def calculateObj(self, fail=False):
        penTotal = 0
        res = []
        const = []
        x = self.x
        for o in self.g:
            vi = eval(o.pycode)
            const.append(vi)
            if vi <= 0:
                vi = 0
            # calculate penalty
            if o.penForm == "Linear":
                penTotal += vi * o.penalty
            elif o.penForm == "Quadratic":
                penTotal += vi * vi * o.penalty
            elif o.penForm == "Step" and vi > 0.0:
                penTotal += o.penalty
        for o in self.obj:
            if fail:
                objfunc = numpy.array(o.fail)
            else:
                try:
                    objfunc = numpy.array(eval(o.pycode))
                    objfunc += numpy.array(penTotal * o.penScale)
                except:
                    objfunc = numpy.array(o.fail)
            res.append(objfunc)
        return res, const

    def check(self, minVars=2):
        # Check number of variables
        n = 0
        for vname in self.v:
            n += self.x[vname].value.size
            if self.x[vname].scaling == "None":
                return [
                    1,
                    "All optimization variables must be scaled check decision variable scaling",
                ]
            min = self.x[vname].min
            max = self.x[vname].max
            if numpy.min(numpy.array(max) - numpy.array(min)) <= 1e-10:
                return [
                    1,
                    "The maximum must be greater than the minimum for all decision variables",
                ]
        if n < minVars:
            return [1, "Optimization method requires at least " + str(minVars)]
        # Check Objective expressions
        x = self.x
        if len(self.obj) < 1:
            return [
                1,
                "Must have at lease one objective function.  If a single objective method is used the first objective will be be evaluated, and the rest will be ignored",
            ]
        for o in self.obj:
            try:
                eval(o.pycode)
            except Exception as e:
                return [1, "Error evaluating an objective function: " + str(e)]
        # check Constraint expressions
        for o in self.g:
            try:
                eval(o.pycode)
            except Exception as e:
                return [1, "Error evaluating a constraint function: " + str(e)]
        return [0, ""]
