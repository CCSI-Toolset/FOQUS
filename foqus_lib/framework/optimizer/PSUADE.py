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

"""
#
# PSUADE
#
import time
import copy
import csv
import queue
import sys
import logging
import math
import numpy
import os
import traceback
from foqus_lib.framework.optimizer.optimization import optimization


def checkAvailable():
    """
    Plugins should have this function to check availability of any
    additional required software.  If requirements are not available
    plugin will not be available.
    """
    # TODO check for PSUADE
    return True


class opt(optimization):
    """
    The optimization solver class.  Should be called opt and inherit
    optimization.  The are several attributes from the optimization
    base class that should be set for an optimization plug-in:
    - available True or False, False it some required thing is not
        present
    - name The name of the solver
    - mp True or False, can use parallel?
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
        self.name = "PSUADE"
        self.methodDescription = (
            "<html>\n<head>"
            ".hangingindent {\n"
            "    margin-left: 22px ;\n"
            "    text-indent: -22px ;\n"
            "}\n"
            "</head>\n"
            "<p><b>PSUADE Optimiation Library</b></p></html>"
        )
        self.available = True
        self.description = "PSUADE Optimzation solvers"
        self.mp = False  # can be parallel?
        self.mobj = False  # handles multiobjective?
        self.minVars = 2  # minimum number of decision variables
        self.maxVars = 10000  # max variables
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
            name="tol", default=None, desc="Some termination crieria", dtype=float
        )
        self.options.add(
            name="Results name",
            default="Opt_PSUADE",
            desc="The name assigned to the flowsheet result set.",
        )

    def optimize(self):
        """
        This is the optimization routine.
        """
        # get the initial guess, flatten arrays and scale inputs
        xinit = self.graph.input.getFlat(self.prob.v, scaled=True)
        # Display a little information to check that things are working
        self.msgQueue.put(
            "Starting PSUADE Optimization at {0}".format(
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
        upper = self.options["upper"].value
        lower = self.options["lower"].value
        tol = self.options["tol"].value
        setName = self.options["Results name"].value
        # Increment set name if already used
        setName = self.dat.flowsheet.results.incrimentSetName(setName)
        #
        # Options are all read in so now initialize things
        #
        # Start time for calculation of elapsed time
        start = time.time()
        # Print messages in logs so can know when optimization started
        # and what the popsize is for debugging mostly
        logging.getLogger("foqus." + __name__).info("Starting PSUADE optimization")

        self.msgQueue.put("This doesn't do anything yet")
