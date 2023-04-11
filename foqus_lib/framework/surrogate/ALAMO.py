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
""" #FOQUS_SURROGATE_PLUGIN

Surrogate plugins need to have the string "#FOQUS_SURROGATE_PLUGIN" near the
begining of the file (see pluginSearch.plugins() for exact character count of
text).  They also need to have a .py extension and inherit the surrogate class.

* This is an example of a surrogate model builder plugin for FOQUS,
  it uses the ALAMO surrogate model builder program ref:

  Cozad, A., N. V. Sahinidis and D. C. Miller, Automatic Learning of
      Algebraic Models for Optimization, AIChE Journal, accepted, 2014.

* A setting of this plugin is the location of the ALAMO executable

John Eslick, Carnegie Mellon University, 2014

"""


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
# from foqus_lib.framework.graph.graph import Graph
from foqus_lib.framework.surrogate.surrogate import surrogate
from foqus_lib.framework.uq.SurrogateParser import SurrogateParser
from foqus_lib.framework.listen import listen
from foqus_lib.framework.session.session import exePath
from multiprocessing.connection import Client


def checkAvailable():
    """Plug-ins should have this function to check availability of any
    additional required software.  If requirements are not available
    plug-in will not be available.
    """
    # I don't really check anything for now the ALAMO exec location is
    # just a setting of the plug-in, you may or may not need GAMS or
    # MATLAB
    return True


class surrogateMethod(surrogate):
    metaDataJsonString = """
    "CCSIFileMetaData":{
        "ID":"uuid",
        "CreationTime":"",
        "ModificationTime":"",
        "ChangeLog":[],
        "DisplayName":"",
        "OriginalFilename":"",
        "Application":"foqus_surogate_plugin",
        "Description":"ALAMO FOQUS Plugin",
        "MIMEType":"application/ccsi+foqus",
        "Confidence":"testing",
        "Parents":[],
        "UpdateMetadata":True,
        "Version":""}
    """
    name = "ALAMO"

    def __init__(self, dat=None):
        """
        ALAMO interface constructor
        """
        surrogate.__init__(self, dat)
        self.name = "ALAMO"
        self.ex = None
        # still working on hanging indent for references
        self.methodDescription = (
            "<html>\n<head>"
            ".hangingindent {\n"
            "    margin-left: 22px ;\n"
            "    text-indent: -22px ;\n"
            "}\n"
            "</head>\n"
            "<b>Automatic Learning of Algebraic Models for Optimization"
            " (ALAMO)</b>"
            '<p class="hangingindent">Cozad, A., N. V. Sahinidis '
            "and D. C. Miller, Learning surrogate models "
            "for simulation‐based optimization, "
            "AIChE Journal, 60, p. 2211–2227, 2014.</p></html>"
        )
        self.alamoDir = "alamo"
        self.inputCols = [
            ("XFACTOR", float, 1.0),
            ("EXTRAPXMIN", float, 0.0),
            ("EXTRAPXMAX", float, 1.0),
        ]
        self.outputCols = [
            ("MAXTERMS", int, -1),
            ("IGNORE", int, 0),
            ("TOLMEANERROR", float, 0.000001),
            ("TOLRELMETRIC", float, 0.000001),
            ("ZMIN", float, 0.0),
            ("ZMAX", float, 1.0),
            ("CUSTOMCON", list, []),
        ]
        self.updateVarCols()
        # include a Section called DATA Settings
        # Check the ALAMOSettings_v2.xlsx with hints and new labels
        self.options.add(
            name="Initial Data Filter",
            section="DATA Settings",
            default="All",
            dtype=str,
            desc="Filter to be applied to the initial data set.",
            hint="Data filters help the user to generate models based"
            "on specific data for each variable.",
            validValues=["All", "None"],
        )

        self.options.add(
            name="Validation Data Filter",
            section="DATA Settings",
            default="None",
            dtype=str,
            desc="Data set used to compute model errors at the validation phase.",
            hint="The number of data points in a preexisting validation data set"
            "can be specified by the user",
            validValues=["All", "None"],
        )
        # Maxtime
        self.options.add(
            name="MAXTIME",
            section="DATA Settings",
            default=2000,
            desc="Maximum total execution time in seconds.",
            hint="This time includes all steps of the algorithm, including "
            "time to read problem, preprocess data, solve "
            "optimization subproblems, and print results.",
        )
        self.options.add(
            name="MINPOINTS",
            section="DATA Settings",
            default=0,
            dtype=int,
            desc="Convergence is assessed only if the simulator is able to compute the "
            "output variables for at least MINPOINTS out the data points requested by ALAMO.",
            hint="A reduced number of MINPOINTS may reduce the computational time to get a model,"
            "but also reducess the accuracy of the model. MINPOINTS must be a positive integer.",
        )
        self.options.add(
            name="NSAMPLE",
            section="Data Settings",
            default=0,
            dtype=int,
            desc="Number of data points to be generated by sampling before any model is built.",
            hint="These points will be used for model builing along with the NDATA points specified by the user. NSAMPLE must be a nonnegative integer.",
        )
        self.options.add(
            name="MAXSIM",
            section="Data Settings",
            default=5,
            dtype=int,
            desc=" Maximum number of successive simulator failures allowed before quit",
            hint="MAXSIM must be a nonnegative integer",
        )
        # Sampler
        self.samplers = {"None": 0, "Random": 1, "SNOBFIT": 2}
        self.options.add(
            name="SAMPLER",
            section="DATA Settings",
            default="None",
            desc="Adaptive sampling method to be used. If adaptive sampling is used, also set MAXITER below.",
            hint="Adaptive sampling method to be used by ALAMO when more data points are needed by the model"
            "If random is used a simulator must be provided by the user. If SNOBFIT is used a simulator must be"
            " by the user and MATLAB must be istalled.",
            validValues=sorted(
                list(self.samplers.keys()), key=lambda k: self.samplers[k]
            ),
        )
        self.options.add(
            name="MAXITER",
            section="DATA Settings",
            default=1,
            desc="Maximum number of ALAMO iterations, 1 = no adaptive sampling, 0 = no limit",
            hint="The maximum number of ALMAO iterations for adaptive sampling, 1 = no adaptive sampling, 0 = no limit",
        )
        self.options.add(
            name="PRESET",
            section="DATA Settings",
            default=-111111,
            desc="Value to be used if the simulation fails.",
            hint="This value must be carefully chosen to be an otherwise not realizable value for the output variables",
        )
        # Add the Section: Model Settings
        self.options.add(
            name="MONOMIALPOWER",
            section="Model Settings",
            default=[1, 2, 3],
            dtype=list,
            desc="Vector of monomial powers considered in basis "
            "functions. Use an empty vector for none.",
            hint="Exponential terms allowed in the algebraic model as basis functions.",
        )
        self.options.add(
            name="MULTI2POWER",
            section="Model Settings",
            default=[1],
            desc="Vector of powers to be considered for pairwise "
            "combinations in basis functions.   Empty vector "
            "for none.",
            hint="Pairwise combination of powers allowed in the algebraic model.",
        )
        self.options.add(
            name="MULTI3POWER",
            section="Model Settings",
            default=[],
            desc="Vector of three variables combinations of powers to be consiedered as basis functions.",
            hint="Empty vector for none [].",
        )
        self.options.add(
            name="RATIOPOWER",
            section="Model Settings",
            default=[],
            desc="Vector of ratio combinations of powers to be considered in the basis functions.",
            hint="Ratio combinations of powers are empty as default.",
        )
        self.options.add(
            name="EXPFCNS",
            section="Model Settings",
            default=True,
            desc="Use or not of exponential functions as basis functions in the model.",
        )
        self.options.add(
            name="LOGFCNS",
            section="Model Settings",
            default=True,
            desc="Logarithimic functions are considered as basis "
            "functions if true; otherwise, they are not considered.",
        )
        self.options.add(
            name="SINFCNS",
            section="Model Settings",
            default=False,
            desc="Sine functions are considered as basis functions if "
            "true; otherwise, they are not considered.",
        )
        self.options.add(
            name="COSFCNS",
            section="Model Settings",
            default=False,
            desc="Cosine functions are considered as basis functions if "
            "true; otherwise, they are not considered.",
        )
        self.options.add(
            name="LINFCNS",
            section="Model Settings",
            default=False,
            desc=" Linear functions are considered as basis functions if true;"
            "otherwise, they are not considered.",
        )
        self.options.add(
            name="CONSTANT",
            section="Model Settings",
            default=False,
            desc=" A constant will be considered as a basis function if true;"
            "otherwise, its not considered.",
        )
        self.options.add(
            name="CUSTOMBAS",
            section="Model Settings",
            default=[],
            dtype=list,
            desc="A list of user-supplied custom basis functions can "
            "be provided by the user. ",
            hint="The parser is not case sensitive and allows for any "
            "Fortran functional expression in terms of the XLABELS. "
            "In addition, the symbol ^ may be used to denote power "
            "operations instead of **.",
        )
        self.modelers = {
            "BIC": 1,
            "Mallow's Cp": 2,
            "AICc": 3,
            "HQC": 4,
            "MSE": 5,
            "Convex Penalty": 6,
            "RIC": 7,
        }
        self.options.add(
            name="MODELER",
            section="Model Settings",
            default="BIC",
            dtype=str,
            desc="Fitness metric to be used for model building.",
            hint="Possible values are Bayesian information criterion, "
            "Mallow's Cp, the corrected Akaike's information "
            "criterion, the Hannan-Quinn information criterion, "
            "mean square error, and a convex penalty consisting of "
            "the sum of square errors and a term penalizing model "
            "size.",
            validValues=sorted(
                list(self.modelers.keys()), key=lambda k: self.modelers[k]
            ),
        )
        self.options.add(
            name="CONVPEN",
            section="Model Settings",
            default=10.0,
            desc="Convex penalty term used if Convex penalty is selected.",
            hint='When MODELER is set to "Convex Penalty," a convex '
            "penalty consisting of the sum of square errors and a "
            "term penalizing model size is used for model building. "
            "In this case, the size of the model is weighted "
            "by CONPEN.",
        )
        self.screener = {
            "No Screening": 0,
            "Screening with Lasso": 1,
            "Screening with sure independence screener": 2,
        }
        self.options.add(
            name="SCREENER",
            section="Model Settings",
            default="No Screening",
            desc="Regularization method is used to reduce the number of "
            "potential basis functions before optimization.",
            hint="",
            validValues=sorted(
                list(self.screener.keys()), key=lambda k: self.screener[k]
            ),
        )
        self.options.add(
            name="SCALEZ",
            section="Model Settings",
            default=False,
            dtype=bool,
            desc="If used, the variables are scaled prior to the optimization problem is solved.",
            hint="The problem is solved using a mathematical programming solver. Usually, scaling"
            " the variables may help the optimization.",
        )
        # Add the Section: SOLVER Settings
        self.options.add(
            name="GAMS",
            section="Solver Settings",
            default="gams",
            desc="GAMS path is needed. GAMS is the software used to solve the optimization problems.",
            hint="The executable path is expected here or the user must declare GAMS.exe in the environment path.",
        )
        self.options.add(
            name="GAMSSOLVER",
            section="Solver Settings",
            default="BARON",
            desc="Name of preferred GAMS solver for solving ALAMO's mixed-integer quadratic subproblems.",
            hint=" Special features "
            "have been implemented in ALAMO and BARON that "
            "make BARON the preferred selection for this option. "
            "However, any mixed-integer quadratic programming solver "
            "available under GAMS can be used. ",
        )
        self.options.add(
            name="SOLVEMIP",
            section="Solver Settings",
            default=False,
            dtype=bool,
            desc="GAMS will be used to solve ALAMO's MIPs/MIQPs if checked",
            hint="",
        )
        self.funform = {"Fortran": 1, "GAMS": 2, "BARON": 3, "C": 4}
        self.options.add(
            name="FUNFORM",
            section="Solver Settings",
            default="Fortran",
            desc="Format for printing basis functions and models found by ALAMO. Fortran must be selected to generate FOQUS UQ and flowsheet models.",
            hint="",
            validValues=sorted(
                list(self.funform.keys()), key=lambda k: self.funform[k]
            ),
        )
        self.options.add(
            name="MIPOPTCA",
            section="Solver Settings",
            default=0.05,
            desc="Absolute convergence tolerance for mixed-integer "
            "optimization problems.",
            hint="This must be a nonnegative " "scalar.",
        )
        self.options.add(
            name="MIPOPTCR",
            section="Solver Settings",
            default=0.0001,
            desc="Relative convergence tolerance for mixed-integer "
            "optimization problems.",
            hint="This must be a nonnegative " "scalar.",
        )
        self.options.add(
            name="LINEARERROR",
            section="Solver Settings",
            default=False,
            desc="If true, a linear objective is used when solving "
            "the mixed-integer optimization problems.",
            hint="If used the Quadratic objective function is replaced by a linear objective function.",
        )
        self.options.add(
            name="CONREG",
            section="Solver Settings",
            default=False,
            desc="Specify whether a constraint regression is used or not.",
            hint="If CONREG is true, bounds on output variables are " "enforced.",
        )
        self.options.add(
            name="CRNCUSTOM",
            section="Solver Settings",
            default=False,
            desc="If true, constraints need to be entered in variables tab.",
        )
        self.options.add(
            name="CRNINITIAL",
            section="Solver Settings",
            default=0,
            dtype=int,
            desc="Number of random bounding points at which constraints "
            "are sampled initially.",
            hint="CRNINITIAL must be a " "nonnegative integer.",
        )
        self.options.add(
            name="CRNMAXITER",
            section="Solver Settings",
            default=10,
            dtype=int,
            desc="Maximum allowed constrained regressions iterations.",
            hint="Constraints are enforced on additional points during "
            "each iteration. CRMAXITER must be a positive integer.",
        )
        self.options.add(
            name="CRNVIOL",
            section="Solver Settings",
            default=100,
            dtype=int,
            desc="Number of bounding points added per round per bound "
            "in each iteration.",
            hint="CRNVIOL must be a positive integer.",
        )
        self.options.add(
            name="CRNTRIALS",
            section="Solver Settings",
            default=100,
            dtype=int,
            desc="Number of random trial bounding points per round of "
            "constrained regression.",
            hint="CRNTRIALS must be a positive " "integer.",
        )
        self.options.add(
            name="CRTOL",
            section="Solver Settings",
            default=1e-3,
            dtype=int,
            desc="Tolerance within which custom constraints must be satisfied. Real greater than 1e-5 is expected",
            hint="Bound and custom constraints will be satisfied within an absolute tolerance equal to CRTOL",
        )
        # Add the Section: Advanced Settings
        self.options.add(
            name="Input File",
            section="Advanced Settings",
            default="alamo.alm",
            dtype=str,
            desc="File name for ALAMO input file.",
        )
        self.options.add(
            name="FOQUS Model (for UQ)",
            section="Advanced Settings",
            default="alamo_surrogate_uq.py",
            dtype=str,
            desc=".py file for UQ analysis.",
        )
        self.options.add(
            name="FOQUS Model (for Flowsheet)",
            section="Advanced Settings",
            default="alamo_surrogate_fs.py",
            dtype=str,
            desc=".py file flowsheet plugin, saved to user_plugins"
            " in the working directory.",
        )
        self.options.add(
            name="Pyomo Model for Optimization",
            section="Advanced Settings",
            default="alamo_surrogate_pyomo_optim.py",
            dtype=str,
            desc=".py file, meant for surrogate based optimization to be used within FOQUS optimizer plugin, saved to user_plugins"
            " in the working directory.",
        )
        self.options.add(
            name="Standalone Pyomo Model for Optimization",
            section="Advanced Settings",
            default="alamo_surrogate_pyomo_optim_standalone.py",
            dtype=str,
            desc=".py file, meant for surrogate based optimization to be used standalone, saved to user_plugins"
            " in the working directory.",
        )

        self.inputVarButtons = (("Set XFACTOR from range", self.autoXFact),)
        self.outputVarButtons = (
            ("Set ZMIN and ZMAX from current data filter", self.autoZMin),
        )

    def autoXFact(self):
        for var in self.input:
            xf = 10 ** int(
                math.log10(
                    self.graph.input.get(var).max - self.graph.input.get(var).min
                )
            )
            self.setInputVarOption("XFACTOR", var, xf)

    def autoZMin(self):
        for var in self.output:
            vals = self.dat.flowsheet.results.getVarColumn(var)
            self.setOutputVarOption("ZMAX", var, max(vals))
            self.setOutputVarOption("ZMIN", var, min(vals))

    def updateOptions(self):
        filters = sorted(
            list(self.dat.flowsheet.results.filters.keys()), key=lambda s: s.lower()
        )
        self.options["Validation Data Filter"].validValues = filters
        self.options["Initial Data Filter"].validValues = filters

    def setupWorkingDir(self):
        alamoDir = self.alamoDir
        adaptive = self.options["SAMPLER"].value
        # create dir does nothing if dir exists, but does not raise
        # exception
        self.createDir(alamoDir)
        # Copy needed files
        if adaptive:
            dest = os.path.join(alamoDir, "foqusALAMOClient.py")
            if not os.path.exists(dest):
                mydir = os.path.dirname(__file__)
                src = os.path.join(mydir, "foqusALAMOClient.py")
                shutil.copyfile(src, dest)

    def run(self):
        """
        This function overloads the Thread class function,
        and is called when you run start() to start a new thread.
        """
        alamoExe = self.dat.foqusSettings.alamo_path
        try:
            assert os.path.isfile(alamoExe)
        except AssertionError:
            msg = (
                "The ALAMO executable was not found. Check the ALAMO exec "
                "path in settings and that ALAMO is installed."
            )
            self.msgQueue.put(msg)
            raise AssertionError(msg)
        try:
            # Setup dictionaries to convert between foqus and ALAMO
            # variable names.  Also setup a list of input and output
            # variable names for ALAMO.  I'm going to keep the dicts
            # for now in case using the FOQUS variables names in ALAMO
            # doesn't work out for some reason.
            uq_file = self.options["FOQUS Model (for UQ)"].value
            self.xList = self.input
            self.zList = self.output
            self.xi = {}
            self.zi = {}
            cn = self.graph.input.compoundNames(sort=True)
            # Remove the edge connected simulation input variables from the flowsheet
            for invars in self.graph.xnames:
                if self.graph.x[invars].con:
                    cn.remove(invars)
            for v in self.xList:
                self.xi[v] = cn.index(v)
            cn = self.graph.output.compoundNames(sort=False)
            for v in self.zList:
                self.zi[v] = cn.index(v)
            # Get options and show some information about settings
            adaptive = self.options["SAMPLER"].value
            alamoDir = self.alamoDir
            alamoDirFull = os.path.abspath(alamoDir)
            self.setupWorkingDir()
            adpexe = os.path.join(alamoDirFull, "foqusALAMOClient.py")
            self.writeAlamoInputFile(adaptiveExe=adpexe)
            if self.checkNumVars():
                return
            alamoInput = self.options["Input File"].value
            alamoOutput = alamoInput.rsplit(".", 1)[0] + ".lst"
            self.msgQueue.put("------------------------------------")
            self.msgQueue.put("Starting ALAMO\n")
            self.msgQueue.put("Exec File Path:    " + alamoExe)
            self.msgQueue.put("Sub-directory:     " + alamoDir)
            self.msgQueue.put("Input File Name:   " + alamoInput)
            self.msgQueue.put("Output File Name:  " + alamoOutput)
            self.msgQueue.put("SAMPLER:           " + str(adaptive))
            self.msgQueue.put("UQ Driver File:    " + uq_file)
            self.msgQueue.put("------------------------------------")
            # If using adaptive sampleing open a network socket to listen
            if adaptive:
                listener = listen.foqusListener(self.dat)
                listener.setInputs(self.input)
                listener.setOutputs(self.output)
                listener.failValue = self.options["PRESET"].value
                address = listener.address
                listener.start()
            # Run Alamo
            process = subprocess.Popen(
                [alamoExe, alamoInput],
                cwd=alamoDir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=None,
                creationflags=win32process.CREATE_NO_WINDOW,
            )
            line = process.stdout.readline()
            while process.poll() == None or line != b"":
                if line == b"":
                    time.sleep(0.2)
                if line != b"":
                    self.msgQueue.put(line.decode("utf-8").rstrip())
                line = process.stdout.readline()
                if self.stop.set():
                    self.msgQueue.put("**terminated by user**")
                    #                    self.killTurbineJobs()
                    #                    self.stopAllConsumers()
                    process.kill()
                    break
            if adaptive:
                # stop the listener
                conn = Client(address)
                conn.send(["quit"])
                conn.close()
            alamoOutput = os.path.join(alamoDir, alamoOutput)
            if self.options["FUNFORM"].value != "Fortran":
                self.msgQueue.put(
                    "MUST USE FORTRAN FORM to make UQ and flowsheet plugins"
                )
                self.msgQueue.put("Skipping plugin creation")
                return
            res = SurrogateParser.parseAlamo(alamoOutput)
            self.result = res
            # self.msgQueue.put(str(res))
            self.writePlugin()
            self.writepyomofile()
            self.writepyomostandalonefile()
            print(self.dat.flowsheet.output)
            SurrogateParser.writeAlamoDriver(
                self.result,
                uq_file,
                ii=self.ii,
                oi=self.oi,
                inputNames=self.xList2,
                outputNames=self.zList2,
            )
            self.driverFile = uq_file
        except Exception:
            self.ex = sys.exc_info()
            logging.getLogger("foqus." + __name__).error(
                "Exception in ALAMO Thread", exc_info=sys.exc_info()
            )

    def writeAlamoInputFile(
        self,
        adaptiveExe="foqusALAMOClient.py",
    ):
        """Write the input file for the ALAMO executable."""
        # Get around the need to associate py files with a python
        # interperater in Windows.
        adaptive = self.samplers.get(self.options["SAMPLER"].value, False)
        if os.name == "nt":
            if adaptive:
                with open(adaptiveExe + ".bat", "w") as f:
                    f.write("python {} %*".format(adaptiveExe))
                adaptiveExe += ".bat"
            # On Windows, need to use short file names for ALAMO
            adaptiveExe = win32api.GetShortPathName(adaptiveExe)
        if not adaptive:
            maxiter = 1
            adaptive = 1
        else:
            maxiter = self.options["MAXITER"].value
        # Number f input and output variables
        nin = self.nInput()
        nout = self.nOutput()
        # Filter for initial data
        dataFilter = self.options["Initial Data Filter"].value
        # filter for validation data
        validFilter = self.options["Validation Data Filter"].value
        # set the number of initial data
        self.graph.results.set_filter(dataFilter)
        ndata = self.graph.results.count_rows(filtered=True)
        # set the number of validation data
        self.graph.results.set_filter(validFilter)
        nvaldata = self.graph.results.count_rows(filtered=True)
        # Get some option values
        nsample = self.options["NSAMPLE"].value
        maxsim = self.options["MAXSIM"].value
        modeler = self.modelers.get(self.options["MODELER"].value, 1)
        preset = self.options["PRESET"].value
        maxtime = self.options["MAXTIME"].value
        scalez = int(self.options["SCALEZ"].value)
        mono = list(map(str, self.options["MONOMIALPOWER"].value))
        multi2 = list(map(str, self.options["MULTI2POWER"].value))
        multi3 = list(map(str, self.options["MULTI3POWER"].value))
        ratios = list(map(str, self.options["RATIOPOWER"].value))
        expfcns = int(self.options["EXPFCNS"].value)
        logfcns = int(self.options["LOGFCNS"].value)
        sinfcns = int(self.options["SINFCNS"].value)
        cosfcns = int(self.options["COSFCNS"].value)
        linfcns = int(self.options["LINFCNS"].value)
        constant = int(self.options["CONSTANT"].value)
        custombas = list(map(str, self.options["CUSTOMBAS"].value))
        convpen = self.options["CONVPEN"].value
        screener = self.screener[self.options["SCREENER"].value]
        mipoptca = self.options["MIPOPTCA"].value
        mipoptcr = self.options["MIPOPTCR"].value
        linearerror = int(self.options["LINEARERROR"].value)
        gams = self.options["GAMS"].value
        gamssolver = self.options["GAMSSOLVER"].value
        solvemip = int(self.options["SOLVEMIP"].value)
        funform = self.funform[self.options["FUNFORM"].value]
        conreg = self.options["CONREG"].value
        crninitial = self.options["CRNINITIAL"].value
        crnmaxiter = self.options["CRNMAXITER"].value
        crnviol = self.options["CRNVIOL"].value
        crntrials = self.options["CRNTRIALS"].value
        crtol = self.options["CRTOL"].value
        usecrncustom = self.options["CRNCUSTOM"].value
        # make list of custom constraints
        customcon = []
        for ii, x in enumerate(self.output):
            val = copy.copy(self.getOutputVarOption("CUSTOMCON", x))
            for i, c in enumerate(val):
                val[i] = "{0} {1}".format(ii + 1, c)
            customcon.extend(val)
        # Replace periods with underscore in variable labels for ALAMO
        # period is not okay for gams so someimes casues problem in ALAMO
        self.xListNP = copy.copy(self.xList)
        self.zListNP = copy.copy(self.zList)
        self.xList2 = copy.copy(self.xList)  # xlist, node names removed if possible
        self.zList2 = copy.copy(self.zList)  # zlist, node names removed if possible
        self.ii = {}
        self.oi = {}
        for i, v in enumerate(self.xListNP):
            self.xListNP[i] = v.replace(".", "_")
            self.ii[self.xListNP[i]] = self.xi[self.xList[i]]
        for i, v in enumerate(self.zListNP):
            self.zListNP[i] = v.replace(".", "_")
            self.oi[self.zListNP[i]] = self.zi[self.zList[i]]
        for i, v in enumerate(custombas):
            custombas[i] = v.replace(".", "_")
        for i, v in enumerate(customcon):
            customcon[i] = v.replace(".", "_")

        nkey, vkey = self.xList2[0].split(".", 1)
        for i, v in enumerate(self.xList2):
            nkey2, vkey = v.split(".", 1)
            self.xList2[i] = vkey
            if nkey != nkey2:
                self.xList2 = copy.copy(self.xList)
                break

        nkey, vkey = self.zList2[0].split(".", 1)
        for i, v in enumerate(self.zList2):
            nkey2, vkey = v.split(".", 1)
            self.zList2[i] = vkey
            if nkey != nkey2:
                self.zList2 = copy.copy(self.zList)
                break

        # Set the path to the alamo input file
        almFile = os.path.join(self.alamoDir, self.options["Input File"].value)
        # Start writing the ALAMO input file
        with open(almFile, "w") as af:
            af.write("preset {0}\n".format(preset))
            af.write("maxtime {0}\n".format(maxtime))
            af.write("modeler {0}\n".format(modeler))
            af.write("convpen {0}\n".format(convpen))
            af.write("screener {0}\n".format(screener))
            af.write("mipoptca {0}\n".format(mipoptca))
            af.write("mipoptcr {0}\n".format(mipoptcr))
            af.write("linearerror {0}\n".format(linearerror))
            af.write('gams "{0}"\n'.format(gams))
            af.write("gamssolver {0}\n".format(gamssolver))
            af.write("solvemip {0}\n".format(solvemip))
            af.write("funform {0}\n".format(funform))
            af.write("sampler {0}\n".format(adaptive))
            af.write("maxiter {0}\n".format(maxiter))
            af.write("maxsim {0}\n".format(maxsim))
            af.write("simulator {}\n".format(adaptiveExe))
            af.write("#simin input.txt\n")
            af.write("#simout output.txt\n")
            af.write("ninputs {0}\n".format(nin))
            af.write("noutputs {0}\n".format(nout))
            # write the min vector
            self.minVals = []
            for x in self.input:
                self.minVals.append(self.graph.input.get(x).min)
            af.write("xmin {0}\n".format(" ".join(map(str, self.minVals))))
            # write the max vector
            self.maxVals = []
            for x in self.input:
                self.maxVals.append(self.graph.input.get(x).max)
            af.write("xmax {0}\n".format(" ".join(map(str, self.maxVals))))
            # Per Variable Options, Inputs
            # XFACTOR
            xfact = []
            for x in self.input:
                val = self.getInputVarOption("XFACTOR", x)
                xfact.append(val)
            af.write("xfactor {0}\n".format(" ".join(map(str, xfact))))
            af.write("scalez {0}\n".format(scalez))
            # MAXTERMS
            maxterms = []
            for x in self.output:
                val = self.getOutputVarOption("MAXTERMS", x)
                maxterms.append(val)
            af.write("maxterms {0}\n".format(" ".join(map(str, maxterms))))
            # IGNORE
            ignore = []
            for x in self.output:
                val = self.getOutputVarOption("IGNORE", x)
                ignore.extend(np.array(val).flatten())
            af.write("ignore {0}\n".format(" ".join(map(str, ignore))))
            # TOLMEANERROR
            tme = []
            for x in self.output:
                val = self.getOutputVarOption("TOLMEANERROR", x)
                tme.extend(np.array(val).flatten())
            af.write("tolmeanerror {0}\n".format(" ".join(map(str, tme))))
            # TOLRELMETRIC
            trm = []
            for x in self.output:
                val = self.getOutputVarOption("TOLRELMETRIC", x)
                trm.extend(np.array(val).flatten())
            af.write("tolrelmetric {0}\n".format(" ".join(map(str, trm))))
            #
            af.write("initialpoints {0}\n".format(ndata))
            af.write("ndata {0}\n".format(ndata))
            af.write("nsample {0}\n".format(nsample))
            af.write("nvaldata {0}\n".format(nvaldata))
            af.write("xlabels {0}\n".format(" ".join(self.xListNP)))
            af.write("zlabels {0}\n".format(" ".join(self.zListNP)))
            af.write("mono {0}\n".format(len(mono)))
            af.write("multi2 {0}\n".format(len(multi2)))
            af.write("multi3 {0}\n".format(len(multi3)))
            # if len(ratios) != 0:
            af.write("ratios {0}\n".format(len(ratios)))
            if len(mono) > 0:
                af.write("monomialpower {0}\n".format(" ".join(mono)))
            if len(multi2) > 0:
                af.write("multi2power {0}\n".format(" ".join(multi2)))
            if len(multi3) > 0:
                af.write("multi3power {0}\n".format(" ".join(multi3)))
            if len(ratios) > 0:
                af.write("ratiopower {0}\n".format(" ".join(ratios)))
            af.write("expfcns {0}\n".format(expfcns))
            af.write("logfcns {0}\n".format(logfcns))
            af.write("sinfcns {0}\n".format(sinfcns))
            af.write("cosfcns {0}\n".format(cosfcns))
            af.write("linfcns {0}\n".format(linfcns))
            af.write("constant {0}\n".format(constant))
            # Custom basis functions
            if len(custombas) > 0:
                af.write("ncustombas {0}\n".format(len(custombas)))
                af.write("BEGIN_CUSTOMBAS\n")
                for s in custombas:
                    af.write("  {0}\n".format(s))
                af.write("END_CUSTOMBAS\n")
            # Constrained regression
            af.write("conreg {0}\n".format(int(conreg)))
            af.write("crninitial {0}\n".format(crninitial))
            af.write("crmaxiter {0}\n".format(crnmaxiter))
            af.write("crnviol {0}\n".format(crnviol))
            af.write("crntrials {0}\n".format(crntrials))
            af.write("crtol {0}\n".format(crtol))
            if conreg:
                z = []
                for x in self.output:
                    val = self.getOutputVarOption("ZMIN", x)
                    z.extend(np.array(val).flatten())
                af.write("zmin {0}\n".format(" ".join(map(str, z))))
                z = []
                for x in self.output:
                    val = self.getOutputVarOption("ZMAX", x)
                    z.extend(np.array(val).flatten())
                af.write("zmax {0}\n".format(" ".join(map(str, z))))
                z = []
                for x in self.input:
                    val = self.getInputVarOption("EXTRAPXMIN", x)
                    z.extend(np.array(val).flatten())
                af.write("extrapxmin {0}\n".format(" ".join(map(str, z))))
                z = []
                for x in self.input:
                    val = self.getInputVarOption("EXTRAPXMAX", x)
                    z.extend(np.array(val).flatten())
                af.write("extrapxmax {0}\n".format(" ".join(map(str, z))))
            # custom constraints
            if len(customcon) > 0 and usecrncustom:
                af.write("crncustom {0}\n".format(len(customcon)))
                af.write("BEGIN_CUSTOMCON\n")
                for s in customcon:
                    af.write("  {0}\n".format(s))
                af.write("END_CUSTOMCON\n")
            # Write initial data section
            res = self.graph.results
            res.set_filter(dataFilter)
            if res.count_rows(filtered=True) > 0:
                af.write("\nBEGIN_DATA\n")
                # reset filter to intial data set
                for i in res.get_indexes(filtered=True):
                    line = [0] * (nin + nout)
                    p = 0
                    for j, vname in enumerate(self.input):
                        line[p] = res["input.{}".format(vname)][i]
                        p += 1
                    for j, vname in enumerate(self.output):
                        line[p] = res["output.{}".format(vname)][i]
                        p += 1
                    line = [str(x) for x in line]
                    af.write(" ".join(line))
                    af.write("\n")
                af.write("END_DATA\n")
            # write validation data section (probably should reuse code
            # from initial data section but I'm in  hurry so just doing
            # a cut and paste job for now
            af.write("\nBEGIN_VALDATA\n")
            # Reset data filter to validation set
            res.set_filter(validFilter)
            for i in res.get_indexes(filtered=True):
                line = [0] * (nin + nout)
                p = 0
                for j, vname in enumerate(self.input):
                    line[p] = res["input.{}".format(vname)][i]
                    p += 1
                for j, vname in enumerate(self.output):
                    line[p] = res["output.{}".format(vname)][i]
                    p += 1
                line = [str(x) for x in line]
                af.write(" ".join(line))
                af.write("\n")
            af.write("END_VALDATA\n")

    def writePlugin(self):
        excludeBefore = "[a-zA-Z0-9_'\".]"
        excludeAfter = "[0-9a-zA-Z_.('\"]"
        file_name = self.options["FOQUS Model (for Flowsheet)"].value
        # Replace variables in the resulting equations with foqus
        # plugin variable names.
        eq_list = []
        for eq_str in self.result["outputEqns"]:
            for i, v in enumerate(self.xList):
                vo = self.xListNP[i]
                pat = "(?<!{0}){1}(?!{2})".format(
                    excludeBefore, vo.replace(".", "\\."), excludeAfter
                )
                newForm = "self.inputs['{0}'].value".format(v)
                eq_str = re.sub(pat, newForm, eq_str)
            for i, v in enumerate(self.zList):
                vo = self.zListNP[i]
                pat = "(?<!{0}){1}(?!{2})".format(
                    excludeBefore, vo.replace(".", "\\."), excludeAfter
                )
                newForm = "self.outputs['{0}'].value".format(v)
                eq_str = re.sub(pat, newForm, eq_str)
            eq_list.append(eq_str.strip())
        # Write the standard code top
        s = self.writePluginTop(method="ALAMO", comments=["ALAMO Model for Flowsheet"])
        with open(os.path.join("user_plugins", file_name), "w") as f:
            f.write(s)
            # write the equations
            f.write("\n")
            f.write("    def run(self):\n")
            for eq in eq_list:
                f.write("        {0}\n".format(eq))
        self.dat.reloadPlugins()

    def writepyomofile(self):
        excludeBefore = "[a-zA-Z0-9_'\".]"
        excludeAfter = "[0-9a-zA-Z_.('\"]"
        file_name3 = self.options["Pyomo Model for Optimization"].value

        minval = []
        maxval = []
        initvals = []
        initvals_output = []

        gin = self.dat.flowsheet.input
        gout = self.dat.flowsheet.output

        for i, v in enumerate(self.input):
            # get the basic variable information
            minVal = gin.get(v).min
            maxVal = gin.get(v).max
            initval = gin.get(v).value
            minval.append(minVal)
            maxval.append(maxVal)
            initvals.append(initval)

        for i, v in enumerate(self.output):
            initvalout = gout.get(v).value
            initvals_output.append(initvalout)

        with open(os.path.join("user_plugins", file_name3), "w") as f:
            f.write("from pyomo.environ import *\n")
            f.write("from pyomo.opt import SolverFactory\n")
            f.write("from pyomo.core.kernel.component_set import ComponentSet\n")
            f.write("import pyutilib.subprocess.GlobalData\n")
            f.write(
                "pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False\n"
            )
            f.write("def main():\n")
            f.write("    surrvarin_names = []\n")
            f.write("    surrvarout_names = []\n")
            f.write("    m=ConcreteModel()\n")
            f.write("    surrvarin_names_original = {0}\n".format(self.xList))
            f.write("    surrvarout_names_original = {0}\n".format(self.zList))

            v1list = []

            for v in self.xList:
                v1 = v.replace(".", "_")
                v1list.append(v1)

            f.write("    for v1 in {0}:\n".format(v1list))
            f.write("        m.add_component('{0}'.format(v1),Var())\n")
            f.write("        surrvarin_names.append(v1)\n")
            f.write("    vlist1 = [v for v in m.component_objects(Var)]\n")

            f.write("    minval={0}\n".format(minval))
            f.write("    maxval={0}\n".format(maxval))
            f.write("    initvals={0}\n".format(initvals))
            f.write("    for i,v in enumerate({0}):\n".format(v1list))
            f.write("        vlist1[i].setlb(minval[i])\n")
            f.write("        vlist1[i].setub(maxval[i])\n")
            f.write("        vlist1[i].value = initvals[i]\n")

            v2list = []

            for v in self.zList:
                v2 = v.replace(".", "_")
                v2list.append(v2)
            f.write("    initvals_output = {0}\n".format(initvals_output))
            f.write("    for v2 in {0}:\n".format(v2list))
            f.write("        m.add_component('{0}'.format(v2),Var())\n")
            f.write("        surrvarout_names.append(v2)\n")
            f.write("    vlist2 = [v for v in m.component_objects(Var)]\n")
            f.write("    vlist2 = list(ComponentSet(vlist2) - ComponentSet(vlist1))\n")

            f.write("    for i,v in enumerate({0}):\n".format(v2list))
            f.write("        vlist2[i].value = initvals_output[i]\n")

            eq_list1 = []
            for eq_str1 in self.result["outputEqns"]:
                for i, v in enumerate(self.xList):
                    vo1 = self.xListNP[i]
                    pat1 = "(?<!{0}){1}(?!{2})".format(
                        excludeBefore, vo1.replace(".", "\\."), excludeAfter
                    )
                    newForm1 = "m.{0}".format(v1list[i])
                    eq_str1 = re.sub(pat1, newForm1, eq_str1)

                p1 = re.compile("(=)")
                eq_str1 = p1.sub("==", eq_str1)

                for i, v in enumerate(self.zList):
                    vo2 = self.zListNP[i]
                    pat2 = "(?<!{0}){1}(?!{2})".format(
                        excludeBefore, vo2.replace(".", "\\."), excludeAfter
                    )
                    newForm2 = "m.{0}".format(v2list[i])
                    eq_str1 = re.sub(pat2, newForm2, eq_str1)
                eq_list1.append(eq_str1.strip())

            f.write("    m.c=ConstraintList()\n")
            for e in eq_list1:
                f.write("    m.c.add({0})\n".format(e))

            f.write("    for i,vr in enumerate(vlist2):\n")
            f.write("        vr.value = -value(m.c[i+1].body - vr)\n")

            f.write("    surrvarin_names_pyomo = vlist1\n")
            f.write("    surrvarout_names_pyomo = []\n")
            f.write("    for v in m.component_objects(Var):\n")
            f.write("        if v not in vlist1:\n")
            f.write("            surrvarout_names_pyomo.append(v)\n")
            f.write(
                "    return surrvarin_names_pyomo, surrvarout_names_pyomo, surrvarin_names_original, surrvarout_names_original, surrvarin_names, surrvarout_names,m\n"
            )

        self.dat.reloadPlugins()

    def writepyomostandalonefile(self):
        excludeBefore = "[a-zA-Z0-9_'\".]"
        excludeAfter = "[0-9a-zA-Z_.('\"]"
        file_name3 = self.options["Standalone Pyomo Model for Optimization"].value

        minval = []
        maxval = []
        initvals = []

        gin = self.dat.flowsheet.input
        for i, v in enumerate(self.input):
            # get the basic variable information
            minVal = gin.get(v).min
            maxVal = gin.get(v).max
            initval = gin.get(v).value
            minval.append(minVal)
            maxval.append(maxVal)
            initvals.append(initval)

        with open(os.path.join("user_plugins", file_name3), "w") as f:
            f.write("# This file is meant for standalone use.\n")
            f.write("# Surrogate Model based Optimizaton.\n")
            f.write("from pyomo.environ import *\n")
            f.write("from pyomo.opt import SolverFactory\n")
            f.write("from pyomo.core.kernel.component_set import ComponentSet\n")
            f.write("import pyutilib.subprocess.GlobalData\n")
            f.write(
                "pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False\n"
            )
            f.write("m=ConcreteModel()\n")

            v1list = []

            for v in self.xList:
                v1 = v.replace(".", "_")
                v1list.append(v1)

            f.write("for v1 in {0}:\n".format(v1list))
            f.write("    m.add_component('{0}'.format(v1),Var())\n")
            f.write("vlist1 = [v for v in m.component_objects(Var)]\n")

            f.write("minval={0}\n".format(minval))
            f.write("maxval={0}\n".format(maxval))
            f.write("initvals={0}\n".format(initvals))
            f.write("for i,v in enumerate({0}):\n".format(v1list))
            f.write("    vlist1[i].setlb(minval[i])\n")
            f.write("    vlist1[i].setub(maxval[i])\n")
            f.write("    vlist1[i].value = initvals[i]\n")

            v2list = []

            for v in self.zList:
                v2 = v.replace(".", "_")
                v2list.append(v2)

            f.write("for v2 in {0}:\n".format(v2list))
            f.write("    m.add_component('{0}'.format(v2),Var(initialize = 0.0001))\n")
            f.write("vlist2 = [v for v in m.component_objects(Var)]\n")
            f.write("vlist2 = list(ComponentSet(vlist2) - ComponentSet(vlist1))\n")

            f.write(
                " # ****Add more variables in pyomo format, if necessary, here****\n"
            )

            f.write(" # ********\n")

            eq_list1 = []
            for eq_str1 in self.result["outputEqns"]:
                for i, v in enumerate(self.xList):
                    vo1 = self.xListNP[i]
                    pat1 = "(?<!{0}){1}(?!{2})".format(
                        excludeBefore, vo1.replace(".", "\\."), excludeAfter
                    )
                    newForm1 = "m.{0}".format(v1list[i])
                    eq_str1 = re.sub(pat1, newForm1, eq_str1)

                p1 = re.compile("(=)")
                eq_str1 = p1.sub("==", eq_str1)

                for i, v in enumerate(self.zList):
                    vo2 = self.zListNP[i]
                    pat2 = "(?<!{0}){1}(?!{2})".format(
                        excludeBefore, vo2.replace(".", "\\."), excludeAfter
                    )
                    newForm2 = "m.{0}".format(v2list[i])
                    eq_str1 = re.sub(pat2, newForm2, eq_str1)
                eq_list1.append(eq_str1.strip())

            f.write("m.c=ConstraintList()\n")
            for e in eq_list1:
                f.write("m.c.add({0})\n".format(e))

            f.write("for i,vr in enumerate(vlist2):\n")
            f.write("    vr.value = -value(m.c[i+1].body - vr)\n")

            f.write(
                " # ****Add more constraints in pyomo format, if necessary, here****\n"
            )

            f.write(" # ********\n")

            f.write(" # Write the objective function below\n")

            f.write("m.obj=Objective(expr=1)\n")

            f.write(" # Enter the solver, and appropriate options below\n")

            f.write("opt = SolverFactory('ipopt')\n")

            f.write("opt.solve(m,tee=True)\n")

        self.dat.reloadPlugins()
