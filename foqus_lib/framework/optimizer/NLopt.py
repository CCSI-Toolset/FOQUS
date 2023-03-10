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

* FOQUS optimization plugin for NLopt
* NLopt is licenced under the LGPL and available from
  http://ab-initio.mit.edu/wiki/index.php/NLopt
* NLopt developer Steven G. Johnson at MIT

John Eslick, Carnegie Mellon University, 2014
"""
import time  # Some of these things are left over from CMA-ES
import copy  # too lazy to sort out which I really need in here
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

# Check that the NLopt module is available and import it if possible.
# If not the NLopt plug-in will not be available.
try:
    import nlopt

    nlopt_available = True
except ImportError:
    logging.getLogger("foqus." + __name__).info("Failed to import the nlopt package")
    nlopt_available = False


def checkAvailable():
    """
    Plugins should have this function to check availability of any
    additional required software.  If requirements are not available
    plugin will not be available.
    """
    return nlopt_available


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
        Initialize NLOPT optimization module
        Args:
            dat = foqus session object
        """
        optimization.__init__(self, dat)  # base class __init__
        self.name = "NLopt"  # Plugin name is actually comming from file
        # name at this point so give file same name
        # (with a *.py).
        # Next is the description of the optimization
        # Unfortunatly not all the HTML below works
        self.methodDescription = (
            "<html>\n<head>"
            ".hangingindent {\n"
            "    margin-left: 22px ;\n"
            "    text-indent: -22px ;\n"
            "}\n"
            "</head>\n"
            '<p class="hangingindent">'
            "<p>Steven G. Johnson, The NLopt nonlinear-optimization"
            " package, http://ab-initio.mit.edu/nlopt <\p>"
            "<p>Algorithm Type: Both derivative free & gradient based</p>"
            "<p>Optimization Problems handling Capability: Nonlinear Optimization Problems with Nonlinear inequality constraints.</p>"
            "<p>AUGLAG, COBYLA, and ISRES algorithms support nonlinear equality constraints as well.</p>"
            "<p>NLopt contains several solvers by various authors"
            "see the NLopt documentation for more information</p>"
            "</html>"
        )
        self.available = nlopt_available  # If plugin is available
        self.description = "NLopt"  # Short description
        self.mp = False  # Can evaluate objectives in parallel?
        self.mobj = False  # Can do multi-objective optimzation?
        self.minVars = 2  # Minimum number of decision variables
        self.maxVars = 10000  # Maximum number of decision variables
        #
        # Next up is the solver options appearing on the solver options
        # page.  If the dtype is not specified the option will guess it
        # from the default value.  Providing a list of valid values
        # creates a dropdown box.
        #
        self.options.add(  # NLopt contains a bunch of slovers this is the
            name="Solver",  # list of solvers DFO to select from
            default="BOBYQA",
            dtype=str,
            validValues=[
                "BOBYQA",
                "COBYLA",
                "Nelder-Mead",
                "NEWUOA",
                "PRAXIS",
                "Sbplx",
                "CRS2",
                "DIRECT",
                "DIRECT-L",
                "DIRECT-L-RAND",
                "ESCH",
                "ISRES",
            ],
            desc="Solver",
        )
        self.options.add(
            name="pop",
            default=0,
            dtype=int,
            desc=(
                "Initial Population size for CRS2 or ISRES other "
                "methods do not use this paramter (<= 0 for default)"
            ),
        )
        self.options.add(
            name="init step",
            default=0,
            dtype=float,
            desc="Initial step size for some local DFOs (<=0 default)",
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
            name="tolfunabs",
            default=1.0e-9,
            desc="Function abs tolerance termiantion condition",
            dtype=float,
        )
        self.options.add(
            name="tolfunrel",
            default=1.0e-9,
            desc="Function relative tolerance termiantion condition",
            dtype=float,
        )
        self.options.add(
            name="tolxabs",
            default=1.0e-9,
            desc="X abs tolerance termiantion condition",
            dtype=float,
        )
        self.options.add(
            name="tolxrel",
            default=1.0e-9,
            desc="X relative tolerance termiantion condition",
            dtype=float,
        )
        self.options.add(
            name="maxeval",
            default=0,
            desc="maximum number of objective function evaluations",
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
            default="NLopt",
            dtype=str,
            desc="Name of flowsheet result set to store data",
        )
        self.options.add(
            name="Backup Interval",
            default=1.0,
            dtype=float,
            desc="How often (in hours) to save a backup session while "
            " optimization is running. Less than 0.03 disables",
        )

    def optMethod(self, s):
        """
        This function just takes the solver string and converts it to the
        NLopt enumerated type for the solver.
        """
        if s == "BOBYQA":
            return nlopt.LN_BOBYQA
        elif s == "COBYLA":
            return nlopt.LN_COBYLA
        elif s == "Nelder-Mead":
            return nlopt.LN_NELDERMEAD
        elif s == "NEWUOA":
            return nlopt.LN_NEWUOA
        elif s == "PRAXIS":
            return nlopt.LN_PRAXIS
        elif s == "Sbplx":
            return nlopt.LN_SBPLX
        elif s == "CRS2":
            return nlopt.GN_CRS2_LM
        elif s == "DIRECT":
            return nlopt.GN_DIRECT
        elif s == "DIRECT-L":
            return nlopt.GN_DIRECT_L
        elif s == "DIRECT-L-RAND":
            return nlopt.GN_DIRECT_L_RAND
        elif s == "ESCH":
            return nlopt.GN_ESCH
        elif s == "ISRES":
            return nlopt.GN_ISRES
        # default to bobyqa (should not get here maybe raise exception?)
        return nlopt.LN_BOBYQA

    def f(self, x, grad):
        """
        This is the function for the solver to call to get function
        evaluations.  This should run the FOQUS flowsheet also can
        stick in other dignostic output.  Whatever you like.  Since
        only the DFO solvers are made avalable the grad arg can be
        ignored.  If there is an exception in here optimization
        terminates (NLopt behavior).
        """
        # run the flowsheet at point x.  X is turned into a list there
        # because this function can return there results of multiple
        # evaluations here we just want one.  If FOQUS is setup right
        # this could do function evaluations in parallel (not with NLopt
        # because NLopt doesn't suport it))
        objValues, cv, pv = self.prob.runSamples([x], self)
        # objValues = list of lists of ojective function values
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
            self.bestSoFarList.append((self.prob.iterationNumber, self.bestSoFar))
            self.graph.loadValues(self.prob.gt.res[0])
            self.updateGraph = True  # this flag is for GUI if true the
            # flowsheet display needs updated
            self.resQueue.put(["BEST", [self.bestSoFar], x])
        #        else:
        # Spit out objective for objective plot coresponding to each function evaluation/iteration
        self.resQueue.put(["IT", self.prob.iterationNumber, obj])
        # Spit out message to messages window after exery 10 evaluations
        if not self.prob.iterationNumber % 10:
            self.msgQueue.put(
                "{0} obj: {1}".format(self.prob.iterationNumber, self.bestSoFar)
            )
        # Count iteration, (in this case actually evaluations)
        self.prob.iterationNumber += 1
        # Save flowsheet at certain intervals with best solution so
        # far stored.  If something bad happes and optimzation stops
        # at least you will have that.  Restart files are not possible
        # with NLopt, but can do with some solvers.
        if self.bkp_int > 0.03 and (time.time() - self.bkp_timer) / 3600 > self.bkp_int:
            self.bkp_timer = time.time()
            try:
                self.dat.save(  # save backup with data
                    filename="".join(["NLOpt_Backup_", self.dat.name, ".foqus"]),
                    updateCurrentFile=False,
                    bkp=False,
                )
            except Exception as e:
                logging.getLogger("foqus." + __name__).exception(
                    "Failed to save session backup {0}".format(str(e))
                )
        # Return the single objective value.
        return obj

    def optimize(self):
        """
        This is the main optimization routine.  This gets called to start
        things up.
        """
        # get the initial guess, flatten arrays and scale inputs
        xinit = self.graph.input.getFlat(self.prob.v, scaled=True)
        # Display a little information to check that things are working
        self.msgQueue.put(
            "Starting NLopt Optimization at {0}".format(
                time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
            )
        )
        self.msgQueue.put("\nDecision Variables\n---------------------")
        vals = self.graph.input.getFlat(self.prob.v, scaled=False)
        for i, xn in enumerate(self.prob.v):
            self.msgQueue.put("{0}: {1} scaled: {2}".format(xn, vals[i], xinit[i]))
        self.msgQueue.put("----------------------")
        n = len(xinit)  # Get the number of inputs
        # self.msgQueue.put("n = {0}".format(n))
        #
        # Read solver options and handle any special cases of options
        #
        upper = self.options["upper"].value  # These are for scaled vars
        lower = self.options["lower"].value  # usually 0 to 10 not usually
        # changed but could be
        # If upper and/or lower are scalar conver to array with the
        # number of variables.
        if type(upper) == float or type(upper) == int:
            upper = upper * numpy.ones(n)
        else:
            upper = numpy.array(upper)
        if type(lower) == float or type(lower) == int:
            lower = lower * numpy.ones(n)
        else:
            lower = numpy.array(lower)

        # Get solver string and convert to NLopt enum
        method = self.optMethod(self.options["Solver"].value)

        # Get rest of options
        absFunTol = self.options["tolfunabs"].value
        relFunTol = self.options["tolfunrel"].value
        absXtol = self.options["tolxabs"].value
        relXtol = self.options["tolxrel"].value
        maxeval = self.options["maxeval"].value
        maxtime = self.options["maxtime"].value
        saveRes = self.options["Save results"].value
        initStep = self.options["init step"].value
        pop = self.options["pop"].value
        setName = self.options["Set Name"].value
        self.bkp_int = self.options["Backup Interval"].value

        # The set name to use when saving evaluations in flowsheet results
        if saveRes:
            setName = self.dat.flowsheet.results.incrimentSetName(setName)
        #
        # Create optimization object and set options
        opt = nlopt.opt(method, n)
        opt.set_lower_bounds(lower)
        opt.set_upper_bounds(upper)
        opt.set_ftol_rel(relFunTol)
        opt.set_ftol_abs(absFunTol)
        opt.set_xtol_rel(relXtol)
        opt.set_xtol_abs(absXtol)
        opt.set_maxeval(maxeval)
        if initStep > 1e-11:
            opt.set_initial_step(initStep)
        if pop > 0:
            opt.set_population(pop)
        needLocalOpt = False  # so far I have not added any method that
        # would need this
        if needLocalOpt:
            opt2 = nlopt.opt(nlopt.LN_BOBYQA, n)
            opt.set_local_optimizer(opt2)
        # The solver is all setup and ready to go
        start = time.time()  # get start time
        self.userInterupt = False  #
        self.bestSoFar = float("inf")  # set inital best values
        self.bestSoFarList = []  # List of all previous best so far values
        #        self.bestSoFarList.append(self.bestSoFar)

        # self.prob is the optimzation problem. get it ready
        self.prob.iterationNumber = 0
        self.prob.initSolverParameters()  #
        self.prob.solverStart = start
        self.prob.maxSolverTime = maxtime
        if saveRes:
            self.prob.storeResults = setName
        else:
            self.prob.storeResults = None
        #
        opt.set_min_objective(self.f)  # set the solver objective function
        self.prob.prep(self)  # get problem ready for solving
        self.bkp_timer = time.time()  # timer for flowseet backup
        # Run the optimzation
        x = opt.optimize(xinit)
        # Print some final words now that optimzation is done.
        eltime = time.time() - start
        self.msgQueue.put(
            "{0}, Total Elasped Time {1}s, Obj: {2}".format(
                self.prob.iterationNumber, math.floor(eltime), self.bestSoFar
            )
        )
        self.resQueue.put(["IT", self.prob.iterationNumber, self.bestSoFar])
        self.resQueue.put(["BEST", [self.bestSoFar], x])
        #        print(self.bestSoFarList)
        min_obj_value = min(self.bestSoFarList, key=lambda t: t[1])
        self.msgQueue.put("Best result found stored in graph")
        self.msgQueue.put(
            "The best value for objective function was obtained at iteration number {}".format(
                min_obj_value[0]
            )
        )
