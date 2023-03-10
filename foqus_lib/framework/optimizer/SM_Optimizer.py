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

* FOQUS optimization plugin for Surrogate Based Optimization in Pyomo

Anuja Deshpande, KeyLogic Systems, Inc. - NETL
"""

import csv
import pickle
import importlib
import numpy as np
import threading
import queue
import logging
import subprocess
import os
import sys
import copy
import traceback
import time
import shutil
import re
import math

try:
    import win32api  # used to get short file name for alamo sim exe
    import win32process
except:
    pass

from foqus_lib.framework.optimizer.optimization import optimization
from foqus_lib.framework.graph.nodeVars import NodeVars
from foqus_lib.framework.graph.edge import edge, edgeConnect
from foqus_lib.framework.surrogate.surrogate import surrogate
from foqus_lib.framework.uq.SurrogateParser import SurrogateParser

# Check that the required pyomo, pyDOE, and smt packages are available for the surrogate based optimization plugin and import it.
# If not the Surrogate Based Optimization plug-in will not be available.

try:
    # add direct imports (in addition to existing wildcard import)
    # to make pylint happy without affecting the existing runtime behavior
    from pyomo.environ import (
        Var,
        Objective,
        Constraint,
        ConstraintList,
        ConcreteModel,
        PositiveReals,
        value,
        log,
        exp,
    )
    from pyomo.opt import SolverFactory
    import pyutilib.subprocess.GlobalData

    pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False
    from pyomo.core.expr import current as EXPR
    from pyomo.core.expr.current import clone_expression
    from pyDOE import *
    from smt.sampling_methods import LHS

    packages_available = True
except ImportError:
    logging.getLogger("foqus." + __name__).info(
        "Failed to import the required packages for SM Optimizer solver"
    )
    packages_available = False


def checkAvailable():
    """
    Plugins should have this function to check availability of any
    additional required software.  If requirements are not available
    plugin will not be available.
    """
    return packages_available


class opt(optimization):
    """
    The optimization solver (in this case, SM_Optimizer) class.
    It describes the solver & its properties. Should be called opt and
    inherit optimization.  The are several attributes from the optimization
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
        Initialize Pyomo_Surrogate optimization module
        Args:
            dat = foqus session object
        """
        optimization.__init__(self, dat)  # base class __init__

        # Description of the optimization
        self.methodDescription = "This solver provides the option to perform mathematical \
             optimization based on surrogate models developed for the FOQUS \
                 flowsheet"
        self.available = packages_available  # If plugin is available
        self.description = "Optimization Solver"  # Short description
        self.mp = False  # Can evaluate objectives in parallel?
        self.mobj = False  # Can do multi-objective optimzation?
        self.minVars = 1  # Minimum number of decision variables
        self.maxVars = 10000  # Maximum number of decision variables

        # Next up is the solver options appearing on the solver options
        # page.  If the dtype is not specified the option will guess it
        # from the default value.  Providing a list of valid values
        # creates a dropdown box.

        self.options.add(
            name="Solver source",
            default="pyomo",
            dtype=str,
            desc="Source of math optimization solver (pyomo or gams)",
        )

        self.options.add(
            name="Model type",
            default="nlp",
            dtype=str,
            desc="Type of math optimization model (used for gams)",
        )

        self.options.add(
            name="Math optimization solver",
            default="ipopt",
            dtype=str,
            desc="Solver to be used for math optimization at each iteration",
        )

        self.options.add(
            name="Math optimizer working - display",
            default=True,
            desc="Display of math optimization solver iterations in terminal anaconda prompt",
        )

        self.options.add(
            name="Solver options",
            default={
                "tol": 1e-6,
                "max_iter": 40,
                "halt_on_ampl_error": "yes",
                "linear_solver": "ma27",
                "warm_start_init_point": "yes",
            },
            dtype=object,
            desc="Math optimization solver options",
        )

        self.options.add(
            name="Maximum algorithm iterations",
            default=10,
            dtype=float,
            desc="Maximum iterations for surrogate based optimization algorithm",
        )

        self.options.add(
            name="Alpha",
            default=0.8,
            dtype=float,
            desc="Fractional reduction in surrogate modeling space",
        )

        self.options.add(
            name="Number of surrogate modeling samples",
            default=10,
            dtype=float,
            desc="Number of samples for generating modified surrogate model",
        )

        self.options.add(
            name="Bound ratio",
            default=1,
            dtype=float,
            desc="Ratio of upper and lower bounds of decision variables",
        )

        self.options.add(
            name="Multistart",
            default=True,
            desc="Multistart approach for each iteration's math optimization initialization",
        )

        self.options.add(
            name="Objective value tolerance",
            default=1e-03,
            dtype=float,
            desc="Tolerance for deviation from objective function evaluated at optimum, from Aspen Simulation",
        )

        self.options.add(
            name="Inequality constraint tolerance",
            default=1e-03,
            dtype=float,
            desc="Tolerance for constraint satisfaction at optimum, from Aspen Simulation",
        )

        self.options.add(
            name="Output variable tolerance",
            default=1e-03,
            dtype=float,
            desc="Tolerance for deviation of output variable values at optimum decision variables, calculated from Aspen Simulation, and Surrogate Model",
        )

        self.options.add(
            name="Save results", default=True, desc="Save math optimization results"
        )

        self.options.add(
            name="Set name",
            default="PYOMO_SM",
            dtype=str,
            desc="Name of flowsheet result set to store data",
        )

        self.options.add(
            name="Pyomo surrogate file",
            default="",
            dtype=str,
            desc="Name of python file containing surrogate based pyomo model",
        )

        self.options.add(
            name="Surrogate model storing file",
            default="",
            dtype=str,
            desc="Name of text file storing surrogate model from each algorithm iteration",
        )

        self.options.add(
            name="Algorithm convergence plots file",
            default="",
            dtype=str,
            desc="Name of python file with algorithm convergence plots",
        )

        self.options.add(
            name="Parity plot file",
            default="",
            dtype=str,
            desc="Name of python file with the parity plot for the final surrogate model",
        )

    def f(self, x):
        """
        #        This is the function for the solver to call to get function
        #        evaluations.  This should run the FOQUS flowsheet also can
        #        stick in other dignostic output.  Whatever you like.
        """
        #        #run the flowsheet at point x.  X is turned into a list there
        #        #because this function can return there results of multiple
        #        #evaluations.  If FOQUS is setup right
        #        #this could do function evaluations in parallel

        if self.stop.isSet():  # if user pushed stop button
            self.userInterupt = True
            raise Exception("User interupt")  # raise exeception to stop

        objValues, cv, pv = self.prob.runSamples([x], self)
        # objValues = list of lists of objective function values
        #             first list is for mutiple evaluations second list
        #             is for multi-objective.  In this case one evaluation
        #             one objective [[obj]].
        # cv = constraint violations
        # pv = constraint violation penalty

        obj = float(objValues[0][0])  # get objective

        # Return the single objective value.
        return obj, cv, pv

    def optimize(self):
        """
        This is the main optimization routine.  This gets called to start
        things up.
        """

        # Display a little information to check that things are working
        self.msgQueue.put(
            "Starting Surrogate based Optimization at {0}".format(
                time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
            )
        )

        self.msgQueue.put("----------------------")
        self.bestSoFarList = []

        # Get user options
        solversource = self.options["Solver source"].value
        mathoptsolver = self.options["Math optimization solver"].value
        mtype = self.options["Model type"].value
        Maxiter_Algo = self.options["Maximum algorithm iterations"].value
        alpha = self.options["Alpha"].value
        num_lhs = self.options["Number of surrogate modeling samples"].value
        bound_ratio = self.options["Bound ratio"].value
        multistart = self.options["Multistart"].value
        tee = self.options["Math optimizer working - display"].value
        solver_options = self.options["Solver options"].value
        obj_tolerance = self.options["Objective value tolerance"].value
        outputvar_tolerance = self.options["Inequality constraint tolerance"].value
        inequality_tolerance = self.options["Output variable tolerance"].value
        Saveresults = self.options["Save results"].value
        SetName = self.options["Set name"].value
        pyomo_surrogate = self.options["Pyomo surrogate file"].value
        file_name_SM_stored = self.options["Surrogate model storing file"].value
        file_name_plots = self.options["Algorithm convergence plots file"].value
        uq_file = self.options["Parity plot file"].value

        # The set name to use when saving evaluations in flowsheet results
        # (to get unique set names in flowsheet results section)
        if Saveresults:
            setName = self.dat.flowsheet.results.incrimentSetName(SetName)

        # The solver is all setup and ready to go
        start = time.time()  # get start time
        self.userInterupt = False  #
        self.bestSoFar = float("inf")  # set inital best values

        # self.prob is the optimzation problem. get it ready
        self.prob.iterationNumber = 0
        self.prob.initSolverParameters()  #
        self.prob.solverStart = start
        if Saveresults:
            self.prob.storeResults = setName
        else:
            self.prob.storeResults = None

        self.prob.prep(self)  # get problem ready for solving
        self.bkp_timer = time.time()  # timer for flowseet backup

        #        *******
        simin = self.dat.flowsheet.input
        simout = self.dat.flowsheet.output

        #        List of simulation input and output variable names
        self.simin_names = self.graph.xnames
        self.simout_names = self.graph.fnames

        #        Creating a copy of the above list
        self.simin_nam = self.simin_names[:]
        self.simout_nam = self.simout_names[:]

        #       Changing simulation variable names to match pyomo names
        for i, n in enumerate(self.simin_names[:]):
            n1 = n.replace(".", "_")
            self.simin_nam[i] = n1

        for i, n in enumerate(self.simout_names[:]):
            n2 = n.replace(".", "_")
            self.simout_nam[i] = n2
        #        *******
        #       Importing the user defined surrogate model file
        mod = importlib.import_module(pyomo_surrogate)
        #        *******
        # ******Obtaining non surrogate input and output var names, and
        # setting bounds, initializations******

        #        Calling the pyomo based surrogate model from the user provided file,
        # using main function
        (
            self.surrin_names_pyomo,
            self.surrout_names_pyomo,
            self.surrin_names_original,
            self.surrout_names_original,
            self.surrin_names,
            self.surrout_names,
            self.m,
        ) = mod.main()

        #       Obtaining the non surrogate input and output variable names in
        #      "node_var" format and the original names for non surrogate variables
        #       in "node.var" format

        self.nonsurrin_names_original = []
        self.nonsurrout_names_original = []
        self.nonsurrin_names = []
        self.nonsurrout_names = []

        for i, simvar in enumerate(self.simin_nam):
            if simvar not in self.surrin_names:
                if not self.graph.x[self.simin_names[i]].con:
                    self.nonsurrin_names_original.append(self.simin_names[i])
                    self.nonsurrin_names.append(simvar)

        edge_list = self.graph.edges

        for i, simvar in enumerate(self.simout_nam):
            if simvar not in self.surrout_names:
                if "status" not in simvar:
                    if "graph_error" not in simvar:
                        for e in edge_list:
                            l = [c.fromName for c in e.con if c.active]
                            if str(self.simout_names[i]).split(".", 1)[1] not in l:
                                self.nonsurrout_names_original.append(
                                    self.simout_names[i]
                                )
                                self.nonsurrout_names.append(simvar)

        #        Creating Pyomo variables corresponding to non surrogate vars
        self.nonsurrin_names_pyomo = []
        self.nonsurrout_names_pyomo = []

        for i, nonsurrin in enumerate(self.nonsurrin_names):
            nonsurrin_original = self.nonsurrin_names_original[i]
            minv = simin.get(nonsurrin_original).min
            maxv = simin.get(nonsurrin_original).max
            initv = simin.get(nonsurrin_original).value
            self.m.add_component(
                "{0}".format(nonsurrin), Var(bounds=(minv, maxv), initialize=initv)
            )
            self.nonsurrin_names_pyomo.append(getattr(self.m, nonsurrin))

        for i, nonsurrout in enumerate(self.nonsurrout_names):
            nonsurrout_original = self.nonsurrout_names_original[i]
            self.m.add_component("{0}".format(nonsurrout), Var(initialize=0.01))
            self.nonsurrout_names_pyomo.append(getattr(self.m, nonsurrout))

        #        Obtaining list of FOQUS node input & output variable names
        self.sim_input_vars_original = [
            "x." + v for v in self.surrin_names_original + self.nonsurrin_names_original
        ]
        self.sim_output_vars_original = [
            "f." + v
            for v in self.surrout_names_original + self.nonsurrout_names_original
        ]
        self.sim_input_vars_pyomo = [
            "self.m." + str(v)
            for v in self.surrin_names_pyomo + self.nonsurrin_names_pyomo
        ]
        self.sim_output_vars_pyomo = [
            "self.m." + str(v)
            for v in self.surrout_names_pyomo + self.nonsurrout_names_pyomo
        ]

        #        Creating a dictionary that maps FOQUS vars to Pyomo vars
        self.var_map_dict = dict()
        for i, vr in enumerate(self.sim_input_vars_original):
            self.var_map_dict[vr] = self.sim_input_vars_pyomo[i]
        for i, vr in enumerate(self.sim_output_vars_original):
            self.var_map_dict[vr] = self.sim_output_vars_pyomo[i]

        #       Obtaining FOQUS objective function & constraints g <= 0
        objexpr = self.prob.obj
        constrexprs = self.prob.g

        #        Replacing the FOQUS variables with Pyomo variables in objective
        #        function and constraints
        o = objexpr[0].pycode
        for k in self.var_map_dict.keys():
            if k in o[:]:
                o = re.sub(
                    r"(?<![a-z]){0}(?![a-z])".format(k), str(self.var_map_dict[k]), o
                )

        self.m.obj = Objective(expr=eval(o))
        if len(constrexprs) != 0:
            self.m.con = ConstraintList()
            for k in constrexprs:
                g = k.pycode
                for k in self.var_map_dict.keys():
                    if k in g[:]:
                        g = re.sub(
                            r"(?<![a-z]){0}(?![a-z])".format(k),
                            str(self.var_map_dict[k]),
                            g,
                        )
                self.m.con.add(eval(g) <= 0)

        #        Checking decision variables & fixing other variables
        for i, fv in enumerate(self.graph.xnames):
            if not self.graph.x[self.simin_names[i]].con:
                if fv not in self.prob.v:
                    fv_pyomo_name = self.simin_nam[i]
                    fv_pyomo = getattr(self.m, fv_pyomo_name)
                    fv_pyomo.fix(fv_pyomo.value)
        self.m.pprint()

        # Obtaining decision variable names in "node_var" format
        dvar_names = []
        for v in self.prob.v[:]:
            v1 = v.replace(".", "_")
            dvar_names.append(v1)

        #       Solving the optimization problem with user provided options
        if solversource == "gams":
            optimizer = SolverFactory(solversource)
            io_options = dict()
            io_options["solver"] = mathoptsolver
            if not os.path.exists("temp"):
                os.makedirs("temp")
            with open("temp/" + mathoptsolver + ".opt", "w") as f:
                for k, v in solver_options.items():
                    f.write(str(k) + " " + str(v) + "\n")
            io_options["add_options"] = ["gams_model.optfile=1;"]
            io_options["mtype"] = mtype
            # io_options['warmstart'] = Warmstart
            kwds = dict()
            kwds["io_options"] = io_options
            kwds["tee"] = tee
            kwds["keepfiles"] = True
            kwds["tmpdir"] = "temp"
        else:
            optimizer = SolverFactory(mathoptsolver)
            kwds = dict()
            kwds["tee"] = tee
            optimizer.options = solver_options

        solution_time = []

        #   Implementing multi-start approach
        start_time_1 = time.time()
        decvars = [getattr(self.m, v) for v in dvar_names]
        surroutvarlist = [str(v) for v in self.surrout_names_pyomo]
        surroutvars = [getattr(self.m, v) for v in surroutvarlist]

        if multistart is True:
            initvals = []
            # Obtain the combination of all initialization points
            for var in decvars:
                initvals.append([var.value, var.lb, var.ub, (var.lb + var.ub) / 2])
            initvals_prod = list(zip(*initvals))

            input_initvals = np.zeros(len(initvals_prod), dtype=object)
            output_initvals = np.zeros(len(initvals_prod), dtype=object)
            input_optim = np.zeros(len(initvals_prod), dtype=object)
            output_optim = np.zeros(len(initvals_prod), dtype=object)
            objvals = np.zeros(len(initvals_prod), dtype=object)
            solver_status = np.zeros(len(initvals_prod), dtype=object)
            solver_termination_condition = np.zeros(len(initvals_prod), dtype=object)
            solver_time = np.zeros(len(initvals_prod), dtype=object)

            # Solve the optimization model for all initialization points
            # & save solver details
            for i1, initvallist in enumerate(initvals_prod):
                i_initvals = []
                o_initvals = []
                i_optim = []
                o_optim = []
                for i, initv in enumerate(initvallist):
                    decvars[i].value = initv
                    i_initvals.append(decvars[i].value)
                for i, initout in enumerate(surroutvars):
                    initout.value = -value(self.m.c[i + 1].body - initout)
                    o_initvals.append(initout.value)
                input_initvals[i1] = i_initvals
                output_initvals[i1] = o_initvals
                r = optimizer.solve(self.m, **kwds)
                for dvar in decvars:
                    i_optim.append(dvar.value)
                for sout in surroutvars:
                    o_optim.append(sout.value)
                if str(r.solver.termination_condition) == "optimal":
                    input_optim[i1] = i_optim
                    output_optim[i1] = o_optim
                    objvals[i1] = self.m.obj()
                    solver_status[i1] = str(r.solver.status)
                    solver_termination_condition[i1] = str(
                        r.solver.termination_condition
                    )
                    solver_time[i1] = str(r.solver.time)
                elif str(r.solver.termination_condition) == "locallyOptimal":
                    input_optim[i1] = i_optim
                    output_optim[i1] = o_optim
                    objvals[i1] = self.m.obj()
                    solver_status[i1] = str(r.solver.status)
                    solver_termination_condition[i1] = str(
                        r.solver.termination_condition
                    )
                    solver_time[i1] = str(r.solver.user_time)
                    # solver_time[i1]='yes'
                else:
                    input_optim[i1] = math.inf
                    output_optim[i1] = math.inf
                    objvals[i1] = math.inf
                    solver_status[i1] = math.inf
                    solver_termination_condition[i1] = math.inf
                    solver_time[i1] = math.inf

            # Assign the best initialization value
            minobjval_idx = np.argmin(objvals)

            for i, var in enumerate(decvars):
                var.value = initvals_prod[minobjval_idx][i]
            for i, initout in enumerate(surroutvars):
                initout.value = -value(self.m.c[i + 1].body - initout)

        else:
            inputinitvals = np.zeros(len(decvars))
            outputinitvals = np.zeros(len(surroutvars))
            for i, var in enumerate(decvars):
                inputinitvals[i] = var.value
            for i, initout in enumerate(surroutvars):
                initout.value = -value(self.m.c[i + 1].body - initout)
                outputinitvals[i] = initout.value
            r = optimizer.solve(self.m, **kwds)

        end_time_1 = time.time()
        t1 = end_time_1 - start_time_1

        self.msgQueue.put("****ITERATION 1****\n")
        self.msgQueue.put("**Bounds & Initializations for the Optimization Model**")
        for i, var in enumerate(self.m.component_data_objects(Var)):
            if var not in self.nonsurrout_names_pyomo:
                self.msgQueue.put("Variable: {0}".format(str(var)))
                if multistart is True:
                    self.msgQueue.put("Initialization Value: {0}".format(str(var())))
                else:
                    # Input decision variables
                    if var in decvars:
                        varindx = decvars.index(var)
                        self.msgQueue.put(
                            "Initialization Value: {0}".format(
                                str(inputinitvals[varindx])
                            )
                        )
                    # Output variables
                    elif var in surroutvars:
                        varindx = surroutvars.index(var)
                        self.msgQueue.put(
                            "Initialization Value: {0}".format(
                                str(outputinitvals[varindx])
                            )
                        )
                if var in [getattr(self.m, v) for v in dvar_names]:
                    self.msgQueue.put("Variable Type: Decision")
                    self.msgQueue.put(
                        "Lower Bound: {0}  Upper Bound: {1}\n".format(
                            str(var.lb), str(var.ub)
                        )
                    )
                elif var.fixed:
                    self.msgQueue.put("Variable Type: Fixed")
                    self.msgQueue.put("Value: {0}\n".format(var.value))
                else:
                    self.msgQueue.put("Variable Type: State\n")
        if multistart is True:
            for i, var in enumerate(decvars):
                var.value = input_optim[minobjval_idx][i]

            for i, initout in enumerate(surroutvars):
                initout.value = -value(self.m.c[i + 1].body - initout)

        self.msgQueue.put("**Pyomo Mathematical Optimization Solution**")
        if multistart is True:
            self.msgQueue.put("Solver Status: {0}".format(solver_status[minobjval_idx]))
            self.msgQueue.put(
                "Solver Termination Condition: {0}".format(
                    solver_termination_condition[minobjval_idx]
                )
            )
            self.msgQueue.put(
                "Solver Solution Time: {0} s".format(solver_time[minobjval_idx])
            )
        else:
            self.msgQueue.put("Solver Status: {0}".format(r.solver.status))
            self.msgQueue.put(
                "Solver Termination Condition: {0}".format(
                    r.solver.termination_condition
                )
            )
            self.msgQueue.put("Solver Solution Time: {0} s".format(r.solver.time))
        self.msgQueue.put("The optimum variable values are:")
        self.msgQueue.put("-----------------------------------------")
        for var in self.m.component_data_objects(Var):
            if var not in self.nonsurrout_names_pyomo:
                self.msgQueue.put("{0}   {1}".format(str(var), str(var())))
        self.msgQueue.put("-----------------------------------------")
        if multistart is True:
            self.msgQueue.put(
                "The optimum objective function value based on the surrogate model is {0}\n".format(
                    str(objvals[minobjval_idx])
                )
            )
        else:
            self.msgQueue.put(
                "The optimum objective function value based on the surrogate model is {0}\n".format(
                    self.m.obj()
                )
            )
        self.msgQueue.put(
            "Time taken to implement iteration 1 step 2 is {} s".format(
                end_time_1 - start_time_1
            )
        )
        self.m.display()

        start_time_2 = time.time()
        dvar_scaled = []
        #        Linear scaling of decision variables
        for i, d in enumerate(self.prob.v):
            dvar = getattr(self.m, dvar_names[i])
            dvar_min_unscaled = simin.get(d).min
            dvar_max_unscaled = simin.get(d).max
            dvar_scaled.append(
                10
                * (dvar.value - dvar_min_unscaled)
                / (dvar_max_unscaled - dvar_min_unscaled)
            )

        #        Carrying out aspen simulation at optimum decision variable value
        xf = np.array(dvar_scaled)
        instance, cv, pv = self.f(xf)
        end_time_2 = time.time()
        t2 = end_time_2 - start_time_2

        self.msgQueue.put("**Rigorous Simulation Run at the Optimum**")
        self.msgQueue.put(
            "The optimum objective function value based on rigorous simulation is {0}\n".format(
                instance
            )
        )
        self.msgQueue.put(
            "Time taken to implement iteration 1 step 3 is {} s".format(
                end_time_2 - start_time_2
            )
        )

        #       Loading the above simulation result in FOQUS flowsheet
        self.graph.loadValues(self.prob.gt.res[0])

        #        Termination Condition Prep
        start_time_3 = time.time()
        #       Obtaining the values of FOQUS surrogate output variables corresponding
        #       to optimum decision variables
        #       Storing the values in a dictionary
        foqus_outvars = dict()
        for nodeName in [k for k in simout.keys() if k != "graph"]:
            self.outVars = simout[nodeName]
            for vkey, var in list(
                (i, k) for (i, k) in self.outVars.items() if i != "status"
            )[:]:
                vkey = str(nodeName) + "_" + str(vkey)
                if vkey in [str(v) for v in self.surrout_names_pyomo]:
                    foqus_outvars[vkey] = var.value

        #       Accessing values of corresponding surrogate output variables from
        #       surrogate optimization
        pyomo_outvars = dict()
        pyomovar_names = [str(v) for v in self.surrout_names_pyomo]
        for v in pyomovar_names:
            variable = getattr(self.m, v)
            pyomo_outvars[v] = variable.value

        #       Calculating fractional difference between output variables
        outvar_val_fracdiff = []
        for v in foqus_outvars.keys():
            y_sim = foqus_outvars[v]
            y_pyomo = pyomo_outvars[v]
            outvar_val_fracdiff.append(abs(y_sim - y_pyomo) / y_sim)

        #       Total solution time
        optim_sol_plugin_sim = self.prob.gt.res[0]
        self.surr_optim_sol_time = optim_sol_plugin_sim["solTime"]

        #        Obtaining rigorous simulation and surrogate model based objective
        #        function values (f* and f) at optimum solution
        f_str = instance
        f = self.m.obj()

        #        Printing Termination Condition Values
        self.msgQueue.put("**Termination Condition Values**")
        self.msgQueue.put(
            "Fractional Difference in Objective Values (Rigorous Simulation & Surrogate Model): {0}".format(
                abs((f_str - f) / f_str)
            )
        )
        self.msgQueue.put(
            "Fractional Difference in Output Variable Values (Rigorous Simulation & Surrogate Model): {0}".format(
                outvar_val_fracdiff
            )
        )
        self.msgQueue.put("Constraint Violation: {0}\n".format(cv))

        #        Accessing the surrogate input variables in pyomo
        surrin_pyomo = []
        for i, d in enumerate(self.surrin_names_pyomo):
            if str(d) in dvar_names:
                surrinvar = getattr(self.m, str(self.surrin_names_pyomo[i]))
                surrin_pyomo.append(surrinvar)
        obj_func_vals = []
        obj_func_vals.append(f)

        obj_fracdif_vals = [abs((f_str - f) / f_str)]

        y_fracdif_vals = [sum(outvar_val_fracdiff) / len(outvar_val_fracdiff)]

        if len(constrexprs) != 0:
            constr_viol_vals = [sum(viol[0] for viol in cv) / len(cv)]

        #        Applying Termination Condition
        #       1. abs(f* - f)/f* <= eps ; 2. abs(y* - y)/y* <= eps ;
        #       3. constraint_violation <= tolerance
        if abs((f_str - f) / f_str) <= obj_tolerance:
            if all(item <= outputvar_tolerance for item in outvar_val_fracdiff):
                if len(constrexprs) != 0:
                    if all(viol[0] <= inequality_tolerance for viol in cv):
                        flag = 0
                        self.msgQueue.put("Optimization Successful")
                    else:
                        flag = 1
                        self.msgQueue.put(
                            "Inequality constraints 'g' not satisfied corresponding to rigorous simulation values"
                        )
                        self.msgQueue.put("Surrogate Model Improvement Required")
                        self.msgQueue.put("****Proceed to next iteration****\n")
                else:
                    flag = 0
                    self.msgQueue.put("Optimization Successful")
            else:
                flag = 2
                self.msgQueue.put(
                    "Difference between aspen simulation and surrogate model output var values at optimal solution, outside tolerance bound"
                )
                self.msgQueue.put("Surrogate Model Improvement Required")
                self.msgQueue.put("****Proceed to next iteration****\n")

        else:
            flag = 3
            self.msgQueue.put("None of the termination conditions satisfied")
            self.msgQueue.put("Surrogate Model Improvement Required")
            self.msgQueue.put("****Proceed to next iteration****\n")

        end_time_3 = time.time()
        t3 = end_time_3 - start_time_3

        self.msgQueue.put(
            "Time taken to implement iteration 1 step 4 is {} s".format(
                end_time_3 - start_time_3
            )
        )
        self.msgQueue.put(
            "Total Time taken to implement iteration 1 is {} s".format(t1 + t2 + t3)
        )
        solution_time.append(t1 + t2 + t3)

        # Print final results
        if flag == 0:
            self.msgQueue.put("\n***OPTIMIZATION RESULT***\n")
            self.msgQueue.put("\n**Optimum value of decision variables**\n")
            for i, v in enumerate(decvars):
                self.msgQueue.put("{0}:{1}\n".format(str(v), v()))
            self.msgQueue.put("\n**Rigorous simulation output variable values**\n")
            for outv in self.graph.fnames:
                self.msgQueue.put(
                    "{0}:{1}\n".format(str(outv), self.graph.f[outv].value)
                )

        #       Store the current iteration surrogate model in a text file
        with open(os.path.join("user_plugins", file_name_SM_stored), "w") as f:
            f.write("Iteration 1 Surrogate Model\n")
            for k in self.m.c.keys():
                f.write("{0} = 0\n".format(self.m.c[k].body))

        #       ****Setting up iterations to improve the surrogate model and
        #           perform the optimization****
        algo_iter = 1

        while flag != 0 and algo_iter <= Maxiter_Algo:
            SM_rebuild_start = time.time()
            algo_iter += 1
            #            Changing the value of alpha after iteration 5
            if algo_iter == 5:
                alpha = alpha / 2
            #            Shrinking the surrogate model input variable bounds
            #            (the ones that are decision variables)
            surrin_bounds = []
            for d in surrin_pyomo:
                delta = d.ub - d.lb
                d_lb_upd = d.value - (delta * alpha / 2)
                d_ub_upd = d.value + (delta * alpha / 2)

                if d_lb_upd <= d.lb:
                    d_lb_upd = d.lb
                if d_ub_upd >= d.ub:
                    d_ub_upd = d.ub

                surrin_bounds.append([d_lb_upd, d_ub_upd])
            surrin_bounds_arr = np.array(surrin_bounds)

            #            Checking the distance between the bounds and terminating
            #            the algorithm if too less
            if any(b[1] / (b[0] + 0.0001) <= bound_ratio for b in surrin_bounds):
                self.msgQueue.put(
                    "The decision variable bounds are too close for optimization to run successfully"
                )
                self.msgQueue.put(
                    "Iteration {0} corresponds to the best solution that can be obtained".format(
                        algo_iter - 1
                    )
                )
                break

            #            Creating Latin Hypercube Samples within the shrunk bounds
            sampling = LHS(xlimits=surrin_bounds_arr)
            num = num_lhs
            # samples * variables value array
            latin_hypercube_samples = sampling(num)
            self.msgQueue.put("**Rebuilding Surrogate Model**")
            self.msgQueue.put("Trust Region: {0}".format(surrin_bounds))
            self.msgQueue.put("Latin Hypercube Sampling with {0} points".format(num))

            # *** Running Simulations for each sample point
            surrin_samples_values = []
            for s in range(len(latin_hypercube_samples)):
                surrinscaled = []
                surrin_outputvals = [None] * len(self.surrout_names)
                for d in range(len(surrin_pyomo)):
                    surrin_min_bound = simin.get(self.surrin_names_original[d]).min
                    surrin_max_bound = simin.get(self.surrin_names_original[d]).max
                    surrinscaled.append(
                        10
                        * (latin_hypercube_samples[s][d] - surrin_min_bound)
                        / (surrin_max_bound - surrin_min_bound)
                    )
                xf1 = np.array(surrinscaled)
                instance1, cv1, pv1 = self.f(xf1)

                #                Obtaining the output values corresponding to each sample point
                for nodeName in [k for k in simout.keys() if k != "graph"]:
                    for outVarName in [
                        k
                        for k in self.prob.gt.res[0]["output"][nodeName]
                        if k != "status"
                    ]:
                        surrout_value = self.prob.gt.res[0]["output"][nodeName][
                            outVarName
                        ]
                        nodevar = str(nodeName) + "_" + str(outVarName)
                        if nodevar in [str(v) for v in self.surrout_names_pyomo]:
                            indx = [str(v) for v in self.surrout_names_pyomo].index(
                                nodevar
                            )
                            surrin_outputvals[indx] = surrout_value

                surrin_samples_values.append(surrin_outputvals)
            latin_hypercube_samples_values = np.array(surrin_samples_values)
            self.msgQueue.put("Rigorous Model Simulations for each LHS point completed")

            # This is working. It reads and replaces text within alamo.alm itself(r+)
            # Creating Updated ALAMO input file with shrunk surrogate input variable bounds, and new LHS samples
            with open(os.path.join("alamo", "alamo.alm"), "r+") as f:
                lines = f.readlines()
                idx1 = lines.index("BEGIN_DATA\n")
                idx2 = lines.index("END_DATA\n")
                idx3 = lines.index("BEGIN_VALDATA\n")
                idx4 = lines.index("END_VALDATA\n")

                f.seek(0)
                f.truncate()
                for line in lines:

                    index = lines.index(line)

                    if "xmin" in line:
                        nummin = re.findall(r"\d+\.\d+", line)
                        for i, n in enumerate(nummin):
                            d = surrin_pyomo[i]
                            line = re.sub(nummin[i], "{0}".format(d_lb_upd), line)

                    if "xmax" in line:
                        nummax = re.findall(r"\d+\.\d+", line)
                        for i, n in enumerate(nummax):
                            d = surrin_pyomo[i]
                            line = re.sub(nummax[i], "{0}".format(d_ub_upd), line)

                    if "sampler" in line:
                        line = re.sub(r"\d+", "1", line)
                    if "maxiter" in line:
                        line = re.sub(r"\d+", "1", line)

                    if "initialpoints" in line:
                        line = re.sub(
                            r"\d+", "{0}".format(len(latin_hypercube_samples)), line
                        )
                    if "ndata" in line:
                        line = re.sub(
                            r"\d+", "{0}".format(len(latin_hypercube_samples)), line
                        )
                    if "nvaldata" in line:
                        line = re.sub(
                            r"\d+", "{0}".format(len(latin_hypercube_samples)), line
                        )
                    if index in range(idx1 + 1, idx2):
                        sampl1 = index - idx1 - 1
                        if sampl1 <= len(latin_hypercube_samples) - 1:
                            vl1 = re.findall(r"\d+\.\d+", line)
                            for i, v in enumerate(vl1):
                                if i <= len(surrin_pyomo) - 1:
                                    line = re.sub(
                                        v,
                                        "{0}".format(
                                            float(latin_hypercube_samples[sampl1][i])
                                        ),
                                        line,
                                    )
                                else:
                                    line = re.sub(
                                        v,
                                        "{0}".format(
                                            float(
                                                latin_hypercube_samples_values[sampl1][
                                                    i - len(surrin_pyomo)
                                                ]
                                            )
                                        ),
                                        line,
                                    )
                        else:
                            line = re.sub(r"\d+\.\d+", "", line)

                    if index in range(idx3 + 1, idx4):
                        sampl2 = index - idx3 - 1
                        if sampl2 <= len(latin_hypercube_samples) - 1:
                            vl2 = re.findall(r"\d+\.\d+", line)
                            for i, v in enumerate(vl2):
                                if i <= len(surrin_pyomo) - 1:
                                    line = re.sub(
                                        v,
                                        "{0}".format(
                                            float(latin_hypercube_samples[sampl2][i])
                                        ),
                                        line,
                                    )
                                else:
                                    line = re.sub(
                                        v,
                                        "{0}".format(
                                            float(
                                                latin_hypercube_samples_values[sampl2][
                                                    i - len(surrin_pyomo)
                                                ]
                                            )
                                        ),
                                        line,
                                    )

                        else:
                            line = re.sub(r"\d+\.\d+", "", line)
                    if not line.strip():
                        continue
                    else:
                        f.write(line)

            alamoExe = self.dat.foqusSettings.alamo_path
            alamoInput = "alamo.alm"
            alamoDir = "alamo"
            alamoDirFull = os.path.abspath(alamoDir)
            process = subprocess.Popen(
                [alamoExe, alamoInput],
                cwd=alamoDir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=None,
                creationflags=win32process.CREATE_NO_WINDOW,
            )

            line = process.stdout.readline()
            while process.poll() is None:
                time.sleep(0.2)
                line = process.stdout.readline()

            #   alamo.lst gets automatically created after running alamo and this code below accesses the path in which this file gets created
            alamoOutput = alamoInput.rsplit(".", 1)[0] + ".lst"
            alamoOutput = os.path.join(alamoDir, alamoOutput)
            res = SurrogateParser.parseAlamo(alamoOutput)
            self.result = res

            SM_rebuild_end = time.time()

            self.msgQueue.put("Surrogate Model Built and Parsed\n")
            self.msgQueue.put(
                "Time taken to rebuild surrogate model is {} s".format(
                    SM_rebuild_end - SM_rebuild_start
                )
            )
            solution_time.append(SM_rebuild_end - SM_rebuild_start)

            # ***Change Surrogate Input Variable Bounds in Pyomo Model
            # .setlb and .setub methods for surrvarin_names_pyomo
            for i, v in enumerate(self.surrin_names_pyomo):
                if str(d) in dvar_names:
                    surrvarin_pyomo = getattr(self.m, str(v))
                    surrvarin_pyomo.setlb(surrin_bounds[i][0])
                    surrvarin_pyomo.setub(surrin_bounds[i][1])

            # *** Obtaining new surrogate model in pyomo format
            excludeBefore = "[a-zA-Z0-9_'\".]"
            excludeAfter = "[0-9a-zA-Z_.('\"]"
            eq_list1 = []
            for eq_str1 in self.result["outputEqns"]:
                for i, v in enumerate(self.surrin_names_original):
                    vo1 = str(self.surrin_names_pyomo[i])
                    pat1 = "(?<!{0}){1}(?!{2})".format(
                        excludeBefore, vo1.replace(".", "\\."), excludeAfter
                    )
                    newForm1 = "self.m.{0}".format(str(self.surrin_names_pyomo[i]))
                    eq_str1 = re.sub(pat1, newForm1, eq_str1)

                p1 = re.compile("(=)")
                eq_str1 = p1.sub("==", eq_str1)

                for i, v in enumerate(self.surrout_names_original):
                    vo2 = str(self.surrout_names_pyomo[i])
                    pat2 = "(?<!{0}){1}(?!{2})".format(
                        excludeBefore, vo2.replace(".", "\\."), excludeAfter
                    )
                    newForm2 = "self.m.{0}".format(str(self.surrout_names_pyomo[i]))
                    eq_str1 = re.sub(pat2, newForm2, eq_str1)
                eq_list1.append(eq_str1.strip())
            # *****
            # **Deleting the previous surrogate model pyomo constraints
            self.m.del_component(self.m.c)
            # Delete implicit pyomo set created
            self.m.del_component(self.m.c_index)

            # *****Creating pyomo constraints from new surrogate model
            self.m.c = ConstraintList()
            for eq_str1 in eq_list1:
                eq = eval(eq_str1)
                self.m.c.add(eq)
            self.m.pprint()
            # *******Implementing multi-start approach*******
            start_time = time.time()
            if multistart is True:
                initvals = []

                # Obtain the combination of all initialization points
                for var in decvars:
                    initvals.append([var.value, var.lb, var.ub, (var.lb + var.ub) / 2])
                initvals_prod = list(zip(*initvals))

                input_initvals = np.zeros(len(initvals_prod), dtype=object)
                output_initvals = np.zeros(len(initvals_prod), dtype=object)
                input_optim = np.zeros(len(initvals_prod), dtype=object)
                output_optim = np.zeros(len(initvals_prod), dtype=object)
                objvals = np.zeros(len(initvals_prod), dtype=object)
                solver_status = np.zeros(len(initvals_prod), dtype=object)
                solver_termination_condition = np.zeros(
                    len(initvals_prod), dtype=object
                )
                solver_time = np.zeros(len(initvals_prod), dtype=object)

                # Solve the optimization model for all initialization points
                # & save solver details
                for i1, initvallist in enumerate(initvals_prod):
                    i_initvals = []
                    o_initvals = []
                    i_optim = []
                    o_optim = []
                    for i, initv in enumerate(initvallist):
                        decvars[i].value = initv
                        i_initvals.append(decvars[i].value)
                    for i, initout in enumerate(surroutvars):
                        initout.value = -value(self.m.c[i + 1].body - initout)
                        o_initvals.append(initout.value)
                    input_initvals[i1] = i_initvals
                    output_initvals[i1] = o_initvals
                    r = optimizer.solve(self.m, **kwds)
                    for dvar in decvars:
                        i_optim.append(dvar.value)
                    for sout in surroutvars:
                        o_optim.append(sout.value)
                    if str(r.solver.termination_condition) == "optimal":
                        input_optim[i1] = i_optim
                        output_optim[i1] = o_optim
                        objvals[i1] = self.m.obj()
                        solver_status[i1] = str(r.solver.status)
                        solver_termination_condition[i1] = str(
                            r.solver.termination_condition
                        )
                        solver_time[i1] = str(r.solver.time)
                    elif str(r.solver.termination_condition) == "locallyOptimal":
                        input_optim[i1] = i_optim
                        output_optim[i1] = o_optim
                        objvals[i1] = self.m.obj()
                        solver_status[i1] = str(r.solver.status)
                        solver_termination_condition[i1] = str(
                            r.solver.termination_condition
                        )
                        solver_time[i1] = str(r.solver.user_time)
                    else:
                        input_optim[i1] = math.inf
                        output_optim[i1] = math.inf
                        objvals[i1] = math.inf
                        solver_status[i1] = math.inf
                        solver_termination_condition[i1] = math.inf
                        solver_time[i1] = math.inf

                # Assign the best initialization value
                minobjval_idx = np.argmin(objvals)

                for i, var in enumerate(decvars):
                    var.value = initvals_prod[minobjval_idx][i]
                for i, initout in enumerate(surroutvars):
                    initout.value = -value(self.m.c[i + 1].body - initout)

            # *********************************************************************
            self.msgQueue.put("****ITERATION {0}****\n".format(algo_iter))
            self.msgQueue.put("**Bounds & Initializations for the Optimization Model**")
            for var in self.m.component_data_objects(Var):
                if var not in self.nonsurrout_names_pyomo:
                    self.msgQueue.put("Variable: {0}".format(str(var)))
                    self.msgQueue.put("Initialization Value: {0}".format(str(var())))

                    if var in [getattr(self.m, v) for v in dvar_names]:
                        self.msgQueue.put("Variable Type: Decision")
                        self.msgQueue.put(
                            "Lower Bound: {0}  Upper Bound: {1}\n".format(
                                str(var.lb), str(var.ub)
                            )
                        )
                    elif var.fixed:
                        self.msgQueue.put("Variable Type: Fixed")
                        self.msgQueue.put("Value: {0}\n".format(var.value))
                    else:
                        self.msgQueue.put("Variable Type: State\n")

            if multistart is True:
                for i, var in enumerate(decvars):
                    var.value = input_optim[minobjval_idx][i]

                for i, initout in enumerate(surroutvars):
                    initout.value = -value(self.m.c[i + 1].body - initout)
            else:
                r = optimizer.solve(self.m, **kwds)
            end_time = time.time()
            t = end_time - start_time

            self.msgQueue.put("**Pyomo Mathematical Optimization Solution**")
            if multistart is True:
                self.msgQueue.put(
                    "Solver Status: {0}".format(solver_status[minobjval_idx])
                )
                self.msgQueue.put(
                    "Solver Termination Condition: {0}".format(
                        solver_termination_condition[minobjval_idx]
                    )
                )
                self.msgQueue.put(
                    "Solver Solution Time: {0} s".format(solver_time[minobjval_idx])
                )
            else:
                self.msgQueue.put("Solver Status: {0}".format(r.solver.status))
                self.msgQueue.put(
                    "Solver Termination Condition: {0}".format(
                        r.solver.termination_condition
                    )
                )
                self.msgQueue.put("Solver Solution Time: {0} s".format(r.solver.time))
            self.msgQueue.put("The optimum variable values are:")
            self.msgQueue.put("-----------------------------------------")
            for var in self.m.component_data_objects(Var):
                if var not in self.nonsurrout_names_pyomo:
                    self.msgQueue.put("{0}   {1}".format(str(var), str(var())))
            self.msgQueue.put("-----------------------------------------")
            if multistart is True:
                self.msgQueue.put(
                    "The optimum objective function value based on the surrogate model is {0}\n".format(
                        str(objvals[minobjval_idx])
                    )
                )
            else:
                self.msgQueue.put(
                    "The optimum objective function value based on the surrogate model is {0}\n".format(
                        self.m.obj()
                    )
                )

            self.msgQueue.put(
                "Time taken to implement iteration {} step 2 is {} s".format(
                    algo_iter, end_time - start_time
                )
            )
            self.m.display()

            #            ***Checking termination conditions to continue iterations***
            start_time_1 = time.time()
            dvar_scaled = []
            #        Linear scaling of decision variables
            for i, d in enumerate(self.prob.v):
                dvar = getattr(self.m, dvar_names[i])

                dvar_min_unscaled = simin.get(d).min
                dvar_max_unscaled = simin.get(d).max
                dvar_scaled.append(
                    10
                    * (dvar.value - dvar_min_unscaled)
                    / (dvar_max_unscaled - dvar_min_unscaled)
                )

            #        Carrying out aspen simulation at optimum decision variable value
            xf = np.array(dvar_scaled)
            instance, cv, pv = self.f(xf)
            end_time_1 = time.time()
            t1 = end_time_1 - start_time_1

            self.msgQueue.put("**Rigorous Simulation Run at the Optimum**")
            self.msgQueue.put(
                "The optimum objective function value based on rigorous simulation is {0}\n".format(
                    instance
                )
            )
            self.msgQueue.put(
                "Time taken to implement iteration {} step 3 is {} s".format(
                    algo_iter, end_time_1 - start_time_1
                )
            )

            #       Loading the above simulation result in FOQUS flowsheet
            self.graph.loadValues(self.prob.gt.res[0])

            #        Termination Condition Prep
            start_time_2 = time.time()
            #       Obtaining the values of FOQUS surrogate output variables corresponding to optimum decision variables
            #        Storing the values in a dictionary
            foqus_outvars = dict()
            for nodeName in [k for k in simout.keys() if k != "graph"]:
                self.outVars = simout[nodeName]
                for vkey, var in list(
                    (i, k) for (i, k) in self.outVars.items() if i != "status"
                )[:]:
                    vkey = str(nodeName) + "_" + str(vkey)
                    if vkey in [str(v) for v in self.surrout_names_pyomo]:
                        foqus_outvars[vkey] = var.value

            #       Accessing values of corresponding surrogate output variables from surrogate optimization
            pyomo_outvars = dict()
            pyomovar_names = [str(v) for v in self.surrout_names_pyomo]
            for v in pyomovar_names:
                variable = getattr(self.m, v)
                pyomo_outvars[v] = variable.value

            #       Calculating fractional difference between output variables
            outvar_val_fracdiff = []
            for v in foqus_outvars.keys():
                y_sim = foqus_outvars[v]
                y_pyomo = pyomo_outvars[v]
                outvar_val_fracdiff.append(abs(y_sim - y_pyomo) / y_sim)

            #       Total solution time
            optim_sol_plugin_sim = self.prob.gt.res[0]
            self.surr_optim_sol_time = optim_sol_plugin_sim["solTime"]

            #       Obtaining objective function values
            f_str = instance
            f = self.m.obj()

            obj_func_vals.append(f)
            obj_fracdif_vals.append(abs((f_str - f) / f_str))
            y_fracdif_vals.append(sum(outvar_val_fracdiff) / len(outvar_val_fracdiff))
            if len(constrexprs) != 0:
                constr_viol_vals.append(sum(viol[0] for viol in cv) / len(cv))

            #  Printing Termination Condition Values
            self.msgQueue.put("**Termination Condition Values**")
            self.msgQueue.put(
                "Fractional Difference in Objective Values (Rigorous Simulation & Surrogate Model): {0}".format(
                    abs((f_str - f) / f_str)
                )
            )
            self.msgQueue.put(
                "Fractional Difference in Output Variable Values (Rigorous Simulation & Surrogate Model): {0}".format(
                    outvar_val_fracdiff
                )
            )
            self.msgQueue.put("Constraint Violation: {0}\n".format(cv))

            #            Applying the termination conditions and deciding whether to continue improving the surrogate model through the while loop, depending on the value of 'flag' variable
            if abs((f_str - f) / f_str) <= obj_tolerance:
                if all(item <= outputvar_tolerance for item in outvar_val_fracdiff):
                    if len(constrexprs) != 0:
                        if all(viol[0] <= inequality_tolerance for viol in cv):
                            flag = 0
                            self.msgQueue.put("Optimization Successful")
                        else:
                            flag = 1
                            self.msgQueue.put("{0}".format(cv))
                            self.msgQueue.put("Inequality constraints g' not satisfied")
                            self.msgQueue.put("Surrogate Model Improvement Required")
                            self.msgQueue.put("****Proceed to next iteration****\n")
                    else:
                        flag = 0
                        self.msgQueue.put("Optimization Successful")
                else:
                    flag = 2
                    self.msgQueue.put("{0}".format(outvar_val_fracdiff))
                    self.msgQueue.put("{0}".format(cv))
                    self.msgQueue.put(
                        "Difference between aspen simulation and surrogate model output var values at optimal solution, outside tolerance bound"
                    )
                    self.msgQueue.put("Surrogate Model Improvement Required")
                    self.msgQueue.put("****Proceed to next iteration****\n")

            else:
                flag = 3
                self.msgQueue.put("None of the termination conditions satisfied")
                self.msgQueue.put("Surrogate Model Improvement Required")
                self.msgQueue.put("****Proceed to next iteration****\n")
            end_time_2 = time.time()
            t2 = end_time_2 - start_time_2

            self.msgQueue.put(
                "Time taken to implement iteration {} step 4 is {} s".format(
                    algo_iter, end_time_2 - start_time_2
                )
            )
            self.msgQueue.put(
                "Total Time taken to implement iteration {} is {} s".format(
                    algo_iter, t + t1 + t2
                )
            )
            solution_time.append(t + t1 + t2)

            # Print final results, and generate parity plot python file if optimization successful
            if flag == 0:
                self.msgQueue.put("\n***OPTIMIZATION RESULT***\n")
                self.msgQueue.put("\n**Optimum value of decision variables**\n")
                for i, v in enumerate(decvars):
                    self.msgQueue.put("{0}:{1}\n".format(str(v), v()))
                self.msgQueue.put("\n**Rigorous simulation output variable values**\n")
                for outv in self.graph.fnames:
                    self.msgQueue.put(
                        "{0}:{1}\n".format(str(outv), self.graph.f[outv].value)
                    )

                # # ***Generate python file for Parity Plot***
                with open(os.path.join("user_plugins", uq_file), "w") as f:
                    f.write(
                        "Input_Data = {0}\n".format(latin_hypercube_samples.tolist())
                    )
                    f.write(
                        "Simulator_Output_Data = {0}\n".format(
                            latin_hypercube_samples_values.tolist()
                        )
                    )
                    SM_outdata = []
                    surrvarinpyomo = []
                    for v in self.surrin_names_pyomo:
                        surrvarin = getattr(self.m, str(v))
                        surrvarinpyomo.append(surrvarin)
                    for s in latin_hypercube_samples:
                        out = []
                        for i, vin in enumerate(surrvarinpyomo):
                            vin.value = s[i]
                        for i, vout in enumerate(surroutvars):
                            vout = -value(self.m.c[i + 1].body - vout)
                            out.append(vout)
                        SM_outdata.append(out)
                    f.write("SM_Output_Data = {0}\n".format(SM_outdata))

            # Store the current iteration surrogate model in a text file
            with open(os.path.join("user_plugins", file_name_SM_stored), "a") as f:
                f.write("\nIteration {0} Surrogate Model\n".format(algo_iter))
                for k in self.m.c.keys():
                    f.write("{0} = 0\n".format(self.m.c[k].body))

        self.msgQueue.put(
            "Total Solution Time for SM Optimizer is {} s".format(sum(solution_time))
        )
        with open(os.path.join("user_plugins", file_name_plots), "w") as f:
            f.write("import matplotlib.pyplot as plt\n")
            f.write("iterations = {0}\n".format(list(range(1, algo_iter + 1))))
            f.write("obj_func_vals = {0}\n".format(obj_func_vals))
            f.write("obj_fracdif_vals = {0}\n".format(obj_fracdif_vals))
            f.write("y_fracdif_vals = {0}\n".format(y_fracdif_vals))
            if len(constrexprs) != 0:
                f.write("constr_viol_vals = {0}\n".format(constr_viol_vals))
            f.write(
                "fig, (ax1, ax2, ax3, ax4) = plt.subplots(4,figsize=(5,15),sharex=True)\n"
            )
            f.write("fig.tight_layout()\n")
            f.write("fig.suptitle('Algorithm Convergence')\n")
            f.write("plt.xticks(iterations)\n")
            f.write("plt.xlabel('Iterations')\n")
            f.write("ax4.set_ylim(0,0.5)\n")
            f.write(
                "ax1.plot(iterations,obj_func_vals,'--bo',label='Objective Value Improvement with algorithm')\n"
            )
            f.write(
                "ax2.plot(iterations,obj_fracdif_vals,'--go',label='Fractional difference in objective values wrt rigorous model:abs((f*-f)/f*)')\n"
            )
            f.write(
                "ax3.plot(iterations,y_fracdif_vals,'--ro',label='Mean value of fractional difference in surrogate output variable values wrt rigorous model:abs((y* - y) /y*)')\n"
            )
            if len(constrexprs) != 0:
                f.write(
                    "ax4.plot(iterations,constr_viol_vals,'--ko',label='Mean value of constraint violation')\n"
                )
            f.write("ax1.legend(bbox_to_anchor=(2,1))\n")
            f.write("ax2.legend(bbox_to_anchor=(1.1,1))\n")
            f.write("ax3.legend(bbox_to_anchor=(1.1,1))\n")
            if len(constrexprs) != 0:
                f.write("ax4.legend(bbox_to_anchor=(2,1))\n")
