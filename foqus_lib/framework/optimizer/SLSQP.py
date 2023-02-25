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
""" #FOQUS_OPT_PLUGIN

Optimization plugins need to have the string "#FOQUS_OPT_PLUGIN" near the
begining of the file (see pluginSearch.plugins() for exact character count of
text).  They also need to have a .py extension and inherit the optimization class.

* FOQUS optimization plugin for scipy SLSQP using finite dif
* Uses scipy optimization module

John Eslick, Carnegie Mellon University, 2014
"""

import time
import copy
import csv
import pickle
import queue
import sys
import logging
import math
import numpy
import os
import traceback
from foqus_lib.framework.optimizer.optimization import optimization

try:
    import scipy

    slsqp_available = True
except ImportError:
    logging.getLogger("foqus." + __name__).info(
        "Failed to import scipy package used to access the slsqp solver"
    )
    slsqp_available = False


def checkAvailable():
    """
    Plugins should have this function to check availability of any
    additional required software.  If requirements are not available
    plugin will not be available.
    """
    return slsqp_available


class opt(optimization):
    """
    The optimization solver class.  Should be called opt and inherit
    optimization.  The are several attributes from the optimization
    base class that should be set for an optimization plug-in:
    - available True or False, False it some required thing is not
        present
    - name The name of the solver
    - mp True or False, can use multiprocessing?
    - mobj True or False, handles multiple objectives?
    - options An optionList object to add solver options to

    Some functions must also be implemented.  Following this example
    __init()__ call base class init, set attributes, add options
    optimize() run optimization periodically send out results for
        monitoring, and check stop flag
    """

    def __init__(self, dat=None):
        """
        Initialize CMA-ES optimization module
        """
        optimization.__init__(self, dat)
        self.name = "SciPy-SLSQP"
        self.methodDescription = (
            "<html>\n<head>"
            ".hangingindent {\n"
            "    margin-left: 22px ;\n"
            "    text-indent: -22px ;\n"
            "}\n"
            "</head>\n"
            '<p class="hangingindent">'
            "<p>Developer: Dieter Kraft</p>"
            "<p>Algorithm Type: Han–Powell quasi–Newton method</p>"
            "<p>Optimization Problems handling Capability: Nonlinear Optimization Problems with general equality & inequality constraints, and variable bounds.</p>"
            "</html>"
        )
        self.options.add(
            name="upper",
            default=10.0,
            dtype=float,
            desc="Upper bound on scaled variables (usually 10.0)",
        )
        self.options.add(
            name="lower",
            default=0.0,
            desc="Lower bound on scaled variables (usually 0.0)",
        )
        self.options.add(
            name="ftol",
            default=1.0e-9,
            desc="Function abs tolerance termiantion condition",
            dtype=float,
        )
        self.options.add(
            name="eps",
            default=1.0e-11,
            desc="Jacobian approximation step size",
            dtype=float,
        )
        self.options.add(
            name="maxiter",
            default=1000000,
            desc="maximum number of iterations",
            dtype=int,
        )
        self.options.add(
            name="maxtime",
            default=48.0,
            desc="maximum time to allow for optimization (hours)",
            dtype=float,
        )
        self.options.add(
            name="Save results", default=True, desc="Save all flowsheet results?"
        )
        self.options.add(
            name="Set Name",
            default="SciPy-SLSQP",
            dtype=str,
            desc="Name of flowsheet result set to store data",
        )

    def f(self, x):
        # Only using DFO so grad can be ignored, if implimnet later,
        # grad must be modified in place
        # the optimization will terminate if an exception is raised
        objValues, cv, pv = self.prob.runSamples([x], self)
        if self.stop.isSet():
            self.userInterupt = True
            raise Exception("User interupt")
        obj = float(objValues[0][0])
        if obj < self.bestSoFar:
            self.bestSoFar = obj
            self.graph.loadValues(self.prob.gt.res[0])
            self.updateGraph = True
            self.resQueue.put(["BEST", [self.bestSoFar], x])
        self.resQueue.put(["IT", self.prob.iterationNumber, self.bestSoFar])
        if not self.prob.iterationNumber % 10:
            self.msgQueue.put(
                "{0} obj: {1}".format(self.prob.iterationNumber, self.bestSoFar)
            )
        self.prob.iterationNumber += 1
        return obj

    def optimize(self):
        """
        This is the optimization routine.
        """
        # get the initial guess, flatten arrays and scale inputs
        xinit = self.graph.input.getFlat(self.prob.v, scaled=True)
        # Display a little information to check that things are working
        self.msgQueue.put(
            "Starting SLSQP Optimization at {0}".format(
                time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
            )
        )
        self.msgQueue.put("\nDecision Variables\n---------------------")
        vals = self.graph.input.getFlat(self.prob.v, scaled=False)
        for i, xn in enumerate(self.prob.v):
            self.msgQueue.put("{0}: {1} scaled: {2}".format(xn, vals[i], xinit[i]))
        self.msgQueue.put("----------------------")
        n = len(xinit)
        # self.msgQueue.put("n = {0}".format(n))
        #
        # Read solver options and handle any special cases of options
        #
        upper = self.options["upper"].value
        lower = self.options["lower"].value
        if type(upper) == float or type(upper) == int:
            upper = upper * numpy.ones(n)
        else:
            upper = numpy.array(upper)
        if type(lower) == float or type(lower) == int:
            lower = lower * numpy.ones(n)
        else:
            lower = numpy.array(lower)
        bounds = []
        for i in range(n):
            bounds.append((lower[i], upper[i]))
        ftol = self.options["ftol"].value
        eps = self.options["eps"].value
        maxiter = self.options["maxiter"].value
        maxtime = self.options["maxtime"].value
        saveRes = self.options["Save results"].value
        setName = self.options["Set Name"].value
        if saveRes:
            setName = self.dat.flowsheet.results.incrimentSetName(setName)
        start = time.time()
        self.userInterupt = False
        self.bestSoFar = float("inf")
        self.prob.iterationNumber = 0
        self.prob.initSolverParameters()
        self.prob.solverStart = start
        self.prob.maxSolverTime = maxtime
        if saveRes:
            self.prob.storeResults = setName
        else:
            self.prob.storeResults = None
        self.prob.prep(self)
        ores = scipy.optimize.minimize(
            self.f,
            xinit,
            method="SLSQP",
            bounds=bounds,
            options={"ftol": ftol, "eps": eps, "maxiter": maxiter},
        )
        # Print some final words
        eltime = time.time() - start
        self.msgQueue.put(
            "{0}, Total Elasped Time {1}s, Obj: {2}".format(
                self.prob.iterationNumber, math.floor(eltime), self.bestSoFar
            )
        )
        self.resQueue.put(["IT", self.prob.iterationNumber, self.bestSoFar])
        self.resQueue.put(["BEST", [self.bestSoFar], ores.x])
        self.msgQueue.put("Best result found stored in graph")
