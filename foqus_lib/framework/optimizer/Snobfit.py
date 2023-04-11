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

* FOQUS optimization plugin for Snobfit

Anuja Deshpande, KeyLogic Systems, Inc. - NETL
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
from foqus_lib.framework.graph.OptGraphOptim import optim, optimObj
from foqus_lib.framework.graph.nodeVars import NodeVars

# Check that the Snobfit module is available and import it if possible.
# If not the Snobfit plug-in will not be available.
try:
    import SQSnobFit
    import SQCommon

    snobfit_available = True
except ImportError:
    logging.getLogger("foqus." + __name__).info(
        "Failed to import SQSnobFit and SQCommon packages used to access the snobfit solver"
    )
    snobfit_available = False


def checkAvailable():
    """
    Plugins should have this function to check availability of any
    additional required software.  If requirements are not available
    plugin will not be available.
    """
    return snobfit_available


class opt(optimization):
    """
    The optimization solver (in this case, Snobfit) class. It describes the solver & its properties. Should be called opt and inherit
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
        Initialize Snobfit optimization module
        Args:
            dat = foqus session object
        """
        optimization.__init__(self, dat)  # base class __init__
        self.name = "Snobfit"  # Plugin name is actually comming from file
        # name at this point so give file same name
        # (with a *.py).
        # Next is the description of the optimization
        self.methodDescription = (
            "<html>\n<head>"
            ".hangingindent {\n"
            "    margin-left: 22px ;\n"
            "    text-indent: -22px ;\n"
            "}\n"
            "</head>\n"
            '<p class="hangingindent">'
            "<p>Developer: WALTRAUD HUYER and ARNOLD NEUMAIER</p>"
            "<p>Algorithm Type: Branch & Local Fit</p>"
            "<p>Optimization Problems handling Capability: Unconstrained Noisy Optimization problems with box bounds, and optional soft constraints</p>"
            "</html>"
        )
        self.available = snobfit_available  # If plugin is available
        self.description = "Optimization Solver"  # Short description
        self.mp = False  # Can evaluate objectives in parallel?
        self.mobj = False  # Can do multi-objective optimzation?
        self.minVars = 2  # Minimum number of decision variables
        self.maxVars = 10000  # Maximum number of decision variables

        # Next up is the solver options appearing on the solver options
        # page.  If the dtype is not specified the option will guess it
        # from the default value.  Providing a list of valid values
        # creates a dropdown box.

        # ******** FROZEN OPTIONS FOR NOW*****************
        #        self.options.add(
        #        name='bounds',
        #        dtype=object,
        #        desc="Box Bounds of decision variables")

        #        self.options.add(
        #        name='nreq',
        #        default=2,
        #        dtype=int,
        #        desc="Required Number of Suggested Evaluation Points Generated by SnobFit")

        #        self.options.add(
        #        name='p',
        #        default=0.5,
        #        dtype=float,
        #        desc="Probability of Generating a Class 4 Point")
        # ******************************************************

        self.options.add(
            name="budget",
            default=10000,
            dtype=int,
            desc="Limit on the number of function calls",
        )

        self.options.add(
            name="minfcall",
            default=500,
            dtype=int,
            desc="Minimum number of function values before considering stopping",
        )

        self.options.add(
            name="nstop",
            default=5,
            dtype=int,
            desc="Number of snobfit calls upto which no improvement is tolerated",
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
            default="SNOBFIT",
            dtype=str,
            desc="Name of flowsheet result set to store data",
        )

        self.options.add(
            name="Backup Interval",
            default=0.5,
            dtype=float,
            desc="How often (in hours) to save a backup session while "
            " optimization is running. Less than 0.03 disables",
        )

    def f(self, x):
        """
        This is the function for the solver to call to get function
        evaluations.  This should run the FOQUS flowsheet also can
        stick in other dignostic output.  Whatever you like.  Since
        only the DFO solvers are made avalable the grad arg can be
        ignored.
        """
        # run the flowsheet at point x.  X is turned into a list there
        # because this function can return there results of multiple
        # evaluations.  If FOQUS is setup right
        # this could do function evaluations in parallel

        objValues, cv, pv = self.prob.runSamples([x], self)
        # objValues = list of lists of objective function values
        #             first list is for mutiple evaluations second list
        #             is for multi-objective.  In this case one evaluation
        #             one objective [[obj]].
        # cv = constraint violations
        # pv = constraint violation penalty

        if self.stop.isSet():  # if user pushed stop button
            self.userInterupt = True
            raise Exception("User interupt")  # raise exeception to stop

        obj = float(objValues[0][0])  # get objective

        # See is objective is better and update best solution found if
        # so this is used to update the flowsheet, plots, and messages
        if obj < self.bestSoFar and self.prob.gt.res[0] is not None:
            self.bestSoFar = obj
            self.graph.loadValues(self.prob.gt.res[0])
            self.updateGraph = True  # this flag is for GUI if true the
            # flowsheet display needs updated
            self.resQueue.put(["BEST", [self.bestSoFar], x])
        # Spit out objective for objective plot
        self.resQueue.put(["IT", self.prob.iterationNumber, self.bestSoFar])

        # Spit out message to messages window after every 2 evaluations
        if not self.prob.iterationNumber % 2:
            self.msgQueue.put(
                "{0} obj: {1}".format(self.prob.iterationNumber, self.bestSoFar)
            )
        # Count iteration, (in this case actually evaluations)
        self.prob.iterationNumber += 1
        # Save flowsheet at certain intervals with best solution so
        # far stored.  If something bad happes and optimzation stops
        # at least you will have that.

        #        best solution of flowsheet saved
        if self.bkp_int > 0.03 and (time.time() - self.bkp_timer) / 3600 > self.bkp_int:
            self.bkp_timer = time.time()
            try:
                self.dat.save(  # save backup with data
                    filename="".join(["SNOBFIT_Backup_", self.dat.name, ".foqus"]),
                    updateCurrentFile=False,
                    bkp=False,
                )
            except Exception as e:
                logging.getLogger("foqus." + __name__).exception(
                    "Failed to save session backup {0}".format(str(e))
                )
        # Return the single objective value.
        return obj

    #    Embed the snobfit driver within the optimize routine function
    def optimize(self):
        """
        This is the main optimization routine.  This gets called to start
        things up.
        """
        # giving the initalization to the snobfit solver
        xinit = numpy.array([])

        # Display a little information to check that things are working
        self.msgQueue.put(
            "Starting SNOBFIT Optimization at {0}".format(
                time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
            )
        )

        self.msgQueue.put("\nDecision Variables\n---------------------")
        vals = self.graph.input.getFlat(self.prob.v, scaled=False)
        for i, xn in enumerate(self.prob.v):
            self.msgQueue.put("{0}: {1}".format(xn, vals[i]))
        self.msgQueue.put("----------------------")

        # Get user options
        #        bounds=numpy.array(self.options["bounds"].value)
        #        p=self.options["p"].value
        budget = self.options["budget"].value
        minfcall = self.options["minfcall"].value
        nstop = self.options["nstop"].value
        maxtime = self.options["maxtime"].value
        saveRes = self.options["Save results"].value
        setName = self.options["Set Name"].value
        self.bkp_int = self.options["Backup Interval"].value

        # The set name to use when saving evaluations in flowsheet results (to get unique set names in flowsheet results section)
        if saveRes:
            setName = self.dat.flowsheet.results.incrimentSetName(setName)

        # The solver is all setup and ready to go
        start = time.time()  # get start time
        self.userInterupt = False  #
        self.bestSoFar = float("inf")  # set inital best values

        # self.prob is the optimzation problem. get it ready
        self.prob.iterationNumber = 0
        self.prob.initSolverParameters()  #
        self.prob.solverStart = start
        self.prob.maxSolverTime = maxtime
        if saveRes:
            self.prob.storeResults = setName
        else:
            self.prob.storeResults = None

        self.prob.prep(self)  # get problem ready for solving
        self.bkp_timer = time.time()  # timer for flowseet backup

        #       Setting the scaled bounds for decision variables before passing it to the solver
        optim_vars = [self.graph.x[xn] for xn in self.prob.v]
        #        b = [[k.min,k.max] for k in optim_vars]
        b = [[0, 10]] * len(optim_vars)
        bounds = numpy.array(b)

        #       Calling the snobfit driver to perform optimization
        request, xbest, fbest = SQSnobFit._snobfit.minimize(
            self.f, xinit, bounds, budget
        )

        xbest_unscaled = []

        #       Unscaling the decision variable values for display
        for i, z in enumerate(xbest):
            xbest_unscaled.append(optim_vars[i].unscale2(z))

        #        *********
        #        req_idx=[(k,i) for k,m in enumerate(request) for i,j in enumerate(m)]
        #        for l,m in req_idx:
        #            request[l,m]=request[l,m].unscale()
        #        *********
        eltime = time.time() - start
        self.msgQueue.put(
            "{0}, Total Elasped Time {1}s, Obj: {2}, xbest: {3}".format(
                self.prob.iterationNumber,
                math.floor(eltime),
                self.bestSoFar,
                xbest_unscaled,
            )
        )
        #        self.msgQueue.put("Requested Points Generated by SNOBFIT: {}".format(request))
        self.resQueue.put(["IT", self.prob.iterationNumber, self.bestSoFar])
        self.resQueue.put(["BEST", [self.bestSoFar], xbest])
        self.msgQueue.put("Best result found stored in graph")
