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

* This is an example of an optimization plugin for FOQUS, CMA
  optimization solver from https://www.lri.fr/~hansen/cmaes_inmatlab.html#python
* This optimiztion plugin is basically just a wrapper for the available
  CMA code to make it work with FOQUS.
* CMA-ES Refrence:

  Hansen, N. (2006). The CMA Evolution Strategy: A Comparing Review.
       In J.A. Lozano, P. Larranga, I. Inza and E. Bengoetxea (eds.).
       Towards a new evolutionary computation. Advances in estimation
       of distribution algorithms. pp. 75-102, Springer.

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

# Check that the CMA-ES python script is available and import it if
# possible.  If not the CMA-ES plug-in will not be available.
try:
    import cma

    cma_available = True
except ImportError:
    logging.getLogger("foqus." + __name__).info("CMA-ES not found")
    cma_available = False


def checkAvailable():
    """
    Plugins should have this function to check availability of any
    additional required software.  If requirements are not available
    plugin will not be available.
    """
    return cma_available


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
        self.name = "CMA-ES"
        self.methodDescription = (
            "<html>\n<head>"
            ".hangingindent {\n"
            "    margin-left: 22px ;\n"
            "    text-indent: -22px ;\n"
            "}\n"
            "</head>\n"
            '<p class="hangingindent">'
            "<p><b>Covariance Matrix Adaptation Evolutionary Strategy"
            " (CMA-ES)</b></p>"
            "<p>Developer: Nikolaus Hansen</p>"
            "<p>Algorithm Type: Genetic/Evolutionary</p>"
            "<p>Optimization Problems handling Capability: Nonlinear, Non Convex, Unconstrained Optimization problems, with optional bounds on variables. Variable limit: 3-100</p>"
            "<p>More Details found here: http://cma.gforge.inria.fr/"
            "</html>"
        )
        self.available = cma_available
        self.description = "CMA-ES from ..."
        self.mp = True
        self.mobj = False
        self.minVars = 2
        self.maxVars = 10000
        self.options.add(
            name="upper",
            default=10.0,
            dtype=float,  # don't need this if default is proper type
            desc="Upper bound on scaled variables (usually 10.0)",
        )
        self.options.add(
            name="lower",
            default=0.0,
            desc="Lower bound on scaled variables (usually 0.0)",
        )
        self.options.add(
            name="tolfun",
            default=None,
            desc="Function range tolerance termiantion condition, "
            "The range of function values of the best objective "
            "over the last 10 + 30*N/popsize and all the "
            "evaluations in the most recent iteration, "
            "N=number of decision variables "
            "(null solver default 10**-11)",
            dtype=float,
        )
        self.options.add(
            name="tolstagnation",
            default=None,
            desc="stop after this number of iterations without "
            "improvment (null solver default, "
            "100+100*N**1.5/popsize, N = number of variables)",
            dtype=float,
        )
        self.options.add(
            name="tolx",
            default=None,
            desc="Tolerance for changes in decision variables, "
            "termiantion condition, stop if standard deviation of "
            "the distribution in all directions is less that tolx "
            "(null solver default 10**-11)",
            dtype=float,
        )
        self.options.add(
            name="seed", default=0, desc="Random number seed (0 uses clock)"
        )
        self.options.add(
            name="itmax",
            default=0,
            desc="Maximum number of iterations (0 go until converges)",
            dtype=int,
        )
        self.options.add(
            name="popsize",
            default=6,
            desc="Number of samples per iteration.  The suggested"
            "number lacking another information and on a single "
            "processor is 4 + floor(3*loge(N)) where N is the "
            "number of decision variables",
        )
        self.options.add(
            name="sd0",
            default=2,
            desc="Initial standard deviation about starting point",
        )
        self.options.add(
            name="Results name",
            default="CMA_Results",
            desc="The name assigned to the flowsheet result set.",
        )
        self.options.add(
            name="Restart out",
            default="",
            desc="Restart file for, {n} replaced by iteration index",
        )
        self.options.add(
            name="Restart modulus",
            default=1,
            desc="Create restart file every x iterations (0 no restart)",
        )
        self.options.add(
            name="Restart in",
            default="",
            desc="A file to restart from. (if empty string start new)",
        )
        self.options.add(
            name="It timeout",
            default=3600,
            desc="Iteration timeout (sec). unfinished sims fail",
        )
        self.options.add(
            name="Max time",
            default=0.0,
            desc="Max time allowed for optimization (hours), "
            "not exact, but will not terminate sooner (0 for "
            "no time limit",
        )
        self.options.add(
            name="Save results", default=True, desc="Save all flowsheet results?"
        )
        self.options.add(
            name="Backup interval",
            default=10,
            desc="Iterations between saving FOQUS session backup" " (0 no backup)",
        )
        self.options.add(
            name="Log Objective",
            default="",
            desc="Append objective mix/max after every iteration",
        )

    def optimize(self):
        """
        This is the optimization routine.
        """
        # get the initial guess, flatten arrays and scale inputs
        xinit = self.graph.input.getFlat(self.prob.v, scaled=True)
        # Display a little information to check that things are working
        self.msgQueue.put(
            "Starting CMA-ES Optimization at {0}".format(
                time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
            )
        )
        self.msgQueue.put("\nDecision Variables\n---------------------")
        vals = self.graph.input.getFlat(self.prob.v, scaled=False)
        for i, xn in enumerate(self.prob.v):
            self.msgQueue.put("{0}: {1} scaled: {2}".format(xn, vals[i], xinit[i]))
        self.msgQueue.put("----------------------")
        #
        # Read solver options and handle any special cases of options
        #
        itmax = self.options["itmax"].value
        # if itmax is 0 special no limit case
        if itmax == 0:
            itmax = 2e10  # okay so it's a limit but very high
        upper = self.options["upper"].value
        lower = self.options["lower"].value
        sd0 = self.options["sd0"].value
        setName = self.options["Results name"].value
        pickIn = self.options["Restart in"].value
        pickOut = self.options["Restart out"].value
        pickMod = self.options["Restart modulus"].value
        maxTime = self.options["Max time"].value
        itTimeout = self.options["It timeout"].value
        popsize = self.options["popsize"].value
        storeRes = self.options["Save results"].value
        backupInt = self.options["Backup interval"].value
        tolfun = self.options["tolfun"].value
        tolx = self.options["tolx"].value
        tolstagnation = self.options["tolstagnation"].value
        objRecFile = self.options["Log Objective"].value
        # Increment set name it already used
        setName = self.dat.flowsheet.results.incrimentSetName(setName)
        #
        # Some of these options get passed to the CMA-ES solver so set
        # up options dict for that
        #
        opts = {
            "bounds": [self.options["lower"].value, self.options["upper"].value],
            "seed": self.options["seed"].value,
            "popsize": popsize,
        }
        if tolfun != None:
            opts["tolfun"] = tolfun
        if tolx != None:
            opts["tolx"] = tolx
        if tolstagnation != None:
            opts["tolstagnation"] = tolstagnation
        #
        # Options are all read in so now initialize things
        #
        # Start time for calculation of elapsed time
        start = time.time()
        # Print messages in logs so can know when optimization started
        # and what the popsize is for debugging mostly
        logging.getLogger("foqus." + __name__).info("Starting optimization")
        logging.getLogger("foqus." + __name__).debug(
            "popsize = " + str(opts["popsize"])
        )
        #
        # Create CMA-ES object either reload pickled CMA-ES object
        # or startup a new optimization
        #
        if pickIn != "" and pickIn != None:
            try:
                with open(pickIn, "rb") as pf:
                    es = pickle.load(pf)
                it = es.result()[4]  # iteration index
                self.msgQueue.put("Reloaded " + str(it) + " iterations")
                bestSoFar = [es.result()[1]]
                bestCoord = es.result()[0]
                self.resQueue.put(["BEST", bestSoFar, bestCoord])
                self.resQueue.put(["IT", it - 1, bestSoFar[0]])
            except:
                logging.getLogger("foqus." + __name__).exception(
                    "Failed to load restart file"
                )
                self.msgQueue.put(traceback.format_exc())
                self.msgQueue.put("Couldn't open restart file: " + pickIn)
                self.msgQueue.put("Not proceeding with optimization")
                self.msgQueue.put("Check the solver settings")
                return
        else:  # if no restart file create new CMA-ES object
            es = cma.CMAEvolutionStrategy(xinit, sd0, opts)
            it = 0  # the iteration index
            bestSoFar = numpy.array(numpy.inf)
        #
        # Put initial progress message out, jus says no samples have run
        # and on first iteration (or whatever iteration from restart)
        #
        self.resQueue.put(["PROG", 0, popsize, 0, it, 0, 0])
        #
        # setup the problem object to share information with solver
        # when calculating objective and running flowsheet samples
        #
        self.prob.initSolverParameters()
        self.prob.solverStart = start
        self.prob.maxSolverTime = maxTime
        if storeRes:
            self.prob.storeResults = setName
        else:
            self.prob.storeResults = None
        ###
        # Enter main loop for optimization iteration
        ###
        picklec = 0  # iterations since last pickle
        self.prob.prep(self)
        while not es.stop() and it < itmax:  # iteration loop
            # set prob iteration number (just for status messages
            # that come from prob while it is running samples)
            self.prob.iterationNumber = it
            # get a set of sample points from CMA-ES
            X = es.ask()
            # Run samples and calculate objective values
            objValues, cv, pv = self.prob.runSamples(X, self)
            # Put objective, constration, and penalty information in log
            # for debugging.
            logging.getLogger("foqus." + __name__).debug(
                "It {0}\n\nObj:\n{1}\n\nConst: {2}\n\nPen: {3}\n".format(
                    it, objValues, cv, pv
                )
            )
            # if the problem took to long or user pressed stop
            # leave the itetation loop
            userInterupt = self.prob.userInterupt
            maxTimeInterupt = self.prob.maxTimeInterupt
            if userInterupt or userInterupt:
                break  # break to optimization iteration loop if stopped
            # see if the best value so far has changed, and update
            # display information if it has
            f = numpy.array([o[0] for o in objValues])
            i = numpy.argmin(f)
            if (
                f[i] < bestSoFar
                and self.prob.gt.res[i * self.prob.numSamples()] is not None
            ):
                bestSoFar = f[i]
                self.graph.loadValues(self.prob.gt.res[i * self.prob.numSamples()])
                self.updateGraph = True
                self.resQueue.put(["BEST", [bestSoFar], X[i]])
            #
            # Create a file that just logs the basic objective function
            # information, this will give you some performance info
            # That can be analized later.
            if objRecFile:
                with open(objRecFile, "ab") as orf:
                    orf.write(
                        "\n{0}, {1}, {2}, {3}, {4}".format(
                            it,
                            bestSoFar,
                            numpy.min(objValues),
                            numpy.max(objValues),
                            time.time() - start,
                        )
                    )
            #
            # Pass the objective information back to CMA-ES
            # So will be ready in next cycle to ask for more samples
            #
            es.tell(X, numpy.array(f))  # pass result to CMA-ES
            #
            # Try to save restart file (optional)
            #
            try:
                if pickMod and not it % pickMod:  # pickle if its time
                    if pickOut and pickOut != "":  # and file name
                        pickOut2 = pickOut.replace("{n}", str(it).zfill(4))
                        with open(pickOut2, "wb") as pf:
                            pickle.dump(es, pf)
            except Exception as e:
                logging.getLogger("foqus." + __name__).exception(
                    "Failed to save restart {0}".format(str(e))
                )
            #
            # Try to backup the session including results if stored
            # (optional)
            #
            try:
                if backupInt and it % backupInt == 0:
                    self.dat.save(  # save backup with data
                        filename="".join(["Opt_Backup_", self.dat.name, ".foqus"]),
                        updateCurrentFile=False,
                        bkp=False,
                    )
            except Exception as e:
                logging.getLogger("foqus." + __name__).exception(
                    "Failed to save session backup {0}".format(str(e))
                )
            #
            # Finish up iteration loop
            #
            eltime = time.time() - start
            r = es.result  # get the results from CMA-ES
            self.msgQueue.put(
                "{0}, Total Elasped Time {1}s, Obj: {2}".format(
                    it, math.floor(eltime), r[1]
                )
            )
            self.resQueue.put(["IT", it, r[1]])
            it += 1  # increment iteration count
        ###
        # End of the iteration loop
        ###
        it -= 1  # decrement iteration count to last iteration done
        self.dat.save(  # save backup with data from last iteration
            filename="".join(["Opt_Final_", self.dat.name, ".json"]),
            updateCurrentFile=False,
            bkp=False,
        )
        #
        # Print out final solver mesages about the results
        #
        if it > 0:
            r = es.result  # get the results from CMA-ES
            xvec = r[0]  # first element in result list is minimizer vector
            # Summarize results in console
            self.msgQueue.put(
                "-------------------\n Elapsed Time: {0}s".format(
                    str(time.time() - start)
                )
            )
            self.msgQueue.put("-------------------\nSolution\n---------------------")
            self.msgQueue.put("Best Objective: " + str(r[1]))
            self.msgQueue.put("Iterations: " + str(r[4]))
            self.msgQueue.put("Samples per iteration: " + str(r[3] / r[4]))
            self.msgQueue.put("Total samples: " + str(r[3]))
            self.msgQueue.put(
                "Total failed samples: " + str(self.prob.totalSampleErrors)
            )
        else:
            self.msgQueue.put("**Stopped before first iteration completed**")
        if userInterupt:
            self.msgQueue.put("**Stopped by user**")
        if maxTimeInterupt:
            self.msgQueue.put("**Stopped due to maximum allowed time**")
        self.msgQueue.put("\n\nBest inputs are stored in graph")
