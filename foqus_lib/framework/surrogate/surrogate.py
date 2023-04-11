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
from foqus_lib.framework.foqusOptions.optionList import optionList
import threading
import copy
import queue
import os
import foqus_lib.framework.uq.SurrogateParser
import json


class surrogate(threading.Thread):
    """
    This is a base class for surrogate model building methods.
    It should be inherited by surrogate model classes.  The
    saveDict and loadDict functions can be overloaded.

    The run and runAdaptive functions should also be overloaded.
    Not all surrogate model methods will need a run adaptive
    function.
    """

    name = "surrogate"

    def __init__(self, dat):
        threading.Thread.__init__(self)
        self.stop = threading.Event()
        self.daemon = True
        self.clear()
        self.dat = dat
        self.options = optionList()
        self.setData(dat)
        self.driverFile = ""
        # self.directCopy is a list of attributes that can be
        # copied with copy.deepcopy and can be understood by
        # the json module.  This saves some work saving the
        # object to a dictionary that can be turned into a json
        # string.  Some things may not fit this and you may need
        # to overload the saveDict and loadDict functions.
        self.directCopy = ["input", "output", "inputOptions", "outputOptions"]
        self.msgQueue = queue.Queue()  # queue for messages to print
        self.resQueue = queue.Queue()  # a queue for plots and monitoring
        self.inputOptions = dict()
        self.outputOptions = dict()
        self.inputCols = []
        self.outputCols = []
        self.minInputs = 1
        self.maxInputs = 1000
        self.minOutputs = 1
        self.maxOutputs = 1000

        self.inputVarButtons = ()
        self.outputVarButtons = ()

    def clear(self):
        self.input = []
        self.output = []
        self.inputScaleFact = {}
        self.ex = None

    def updateVarCols(self):
        for i, item in enumerate(self.inputCols):
            if self.inputOptions.get(item[0], None) is None:
                self.inputOptions[item[0]] = {}
        for i, item in enumerate(self.outputCols):
            if self.outputOptions.get(item[0], None) is None:
                self.outputOptions[item[0]] = {}

    def getInputVarOption(self, opt, var):
        """
        Get input variable specific option.  If option doesn't exist
        returns none.  If variables doesn't exist return default
            opt: string option name
            var: string variable name
        """
        d = self.inputOptions.get(opt, None)
        if d is None:
            return None
        v = d.get(var, None)
        if v == None:  # look up default
            v = next(x for x in self.inputCols if x[0] == opt)[2]
        return v

    def getOutputVarOption(self, opt, var):
        """
        Get output variable specific option.  If option doesn't exist
        returns none.  If variables doesn't exist return default
            opt: string option name
            var: string variable name
        """
        d = self.outputOptions.get(opt, None)
        if d is None:
            return None
        v = d.get(var, None)
        if v == None:  # look up default
            v = next(x for x in self.outputCols if x[0] == opt)[2]
        return v

    def setInputVarOption(self, opt, var, val=None):
        """
        Set input variable specific option.  If option doesn't exist
        returns none.  If variables doesn't exist set/return default
        If val is set and option exists returs val.
            opt: string option name
            var: string variable name
            val: value to set if none use default
        """
        d = self.inputOptions.get(opt, None)
        if d is None:
            return None
        if val == None:
            val = self.getInputVarOption(opt, var)
        d[var] = val
        return val

    def setOutputVarOption(self, opt, var, val=None):
        """
        Set output variable specific option.  If option doesn't exist
        returns none.  If variables doesn't exist set/return default
        If val is set and option exists returs val.
            opt: string option name
            var: string variable name
            val: value to set if none use default
        """
        d = self.outputOptions.get(opt, None)
        if d is None:
            return None
        if val == None:
            val = self.getOutputVarOption(opt, var)
        d[var] = val
        return val

    def updateOptions(self):
        """ """
        pass

    def location(self):
        # WHY this is likely a real error reported by pylint,
        # which suggests that this function is never run
        return os.path(os.path.dirname(__file__))  # TODO pylint: disable=not-callable

    def saveInSession(self):
        self.dat.surrogateProblem[self.name] = self.saveDict()

    def loadFromSession(self):
        if self.dat.surrogateProblem is not None:
            sd = self.dat.surrogateProblem.get(self.name, None)
            if sd is not None:
                self.loadDict(sd)

    def saveDict(self):
        sd = {}
        for att in self.directCopy:
            sd[att] = copy.deepcopy(self.__dict__[att])
        sd["options"] = self.options.saveValues()
        return sd

    def loadDict(self, sd):
        for att in self.directCopy:
            if sd.get(att, None) != None:
                self.__dict__[att] = sd[att]
        self.updateVarCols()
        opts = sd.get("options", None)
        if opts is not None:
            self.options.loadValues(opts)

    def run(self):
        pass

    def nInput(self):
        return len(self.input)

    def nOutput(self):
        return len(self.output)

    def checkNumVars(self):
        err = 0
        if self.nInput() < self.minInputs:
            self.msgQueue.put(
                "**Must select at least {0} input variables".format(self.minInputs)
            )
            err = 1
        if self.nInput() > self.maxInputs:
            self.msgQueue.put(
                "**Must select at most {0} input variables".format(self.maxInputs)
            )
            err = 1
        if self.nOutput() < self.minOutputs:
            self.msgQueue.put(
                "**Must select at least {0} output variables".format(self.minOutputs)
            )
            err = 1
        if self.nOutput() > self.maxOutputs:
            self.msgQueue.put(
                "**Must select at most {0} output variables".format(self.maxOutputs)
            )
            err = 1
        return err

    def createDir(self, wdir=None):
        """
        Check for a working directory and create it if it
        does not exist
        """
        if wdir == None:
            return
        # Check if wdir exists and create it if not.
        try:
            os.makedirs(wdir)
        except OSError as e:
            if not os.path.isdir(wdir):
                raise e

    def setData(self, dat=None):
        """
        Set the session data so the optimization routine can get
        the flowsheet and whatever else it may need.
        """
        self.dat = dat
        if dat:
            self.graph = dat.flowsheet
        else:
            self.graph = None

    def terminate(self):
        """
        This sets the stop flag to indicate that you want to stop
        the optimization.  The optimize function needs to check the
        stop flag periodically for this to work, so the optimization
        may take some time to stop, or may not stop at all if the
        flag is not checked in the derived class.
        """
        self.stop.set()

    def writePluginTop(self, method="Generic", comments=[], importLines=[]):
        """
        Write the code for the top protion of a flowsheet plugin
        that does the standard imports and variable definitions in
        the class init.  Returns string.
        """
        lines = []  # Join lines into a string at end (it's faster)
        # The first comment is needed for FOQUS to identify file as
        # a Python flowsheet model plugin.
        lines.append("# FOQUS_PYMODEL_PLUGIN")
        # Some comments just for users lookin into the file
        lines.append("#")
        lines.append("# {0} surrogate export".format(method))
        lines.append("# THIS FILE WAS AUTOMATICALLY GENERATED.")
        lines.append("#")
        for comment in comments:
            lines.append("# {0}".format(comment))
        # Standard module imports
        lines.append("import numpy")
        lines.append("import scipy")
        lines.append("import subprocess")
        lines.append("from math import *")
        lines.append("from foqus_lib.framework.pymodel.pymodel import *")
        lines.append("from foqus_lib.framework.graph.nodeVars import *")
        # Any other imports
        lines.extend(importLines)
        lines.append("")
        # Add check available function.  This function can be used to
        # check that the need components are available, but I'm not
        # really using it for anything yet
        lines.append("def checkAvailable():")
        lines.append("    return True")
        lines.append("")
        # Now create the plugin class and portion of __init__ that adds
        # input and output variables.
        lines.append("class pymodel_pg(pymodel):")
        lines.append("    def __init__(self):")
        lines.append("        pymodel.__init__(self)")
        # Some indents
        s8 = "        "
        s12 = "            "
        # flowsheet variables
        gin = self.dat.flowsheet.input
        gout = self.dat.flowsheet.output
        # input variables
        inputvals = []
        for i, v in enumerate(self.input):
            # get the basic variable information
            minVal = gin.get(v).min
            maxVal = gin.get(v).max
            defVal = gin.get(v).default
            desc = gin.get(v).desc
            desc = desc.replace("\n", " ")
            # create variable object
            lines.append(s8 + "self.inputs['{0}'] = NodeVars(".format(v))
            lines.append(s12 + "value = {0},".format(defVal))
            lines.append(s12 + "vmin = {0},".format(minVal))
            lines.append(s12 + "vmax = {0},".format(maxVal))
            lines.append(s12 + "vdflt = {0},".format(defVal))
            lines.append(s12 + 'unit = "",')
            lines.append(s12 + 'vst = "pymodel",')
            lines.append(s12 + 'vdesc = "{0}",'.format(desc))
            lines.append(s12 + "tags = [],")
            lines.append(s12 + "dtype = float)")
            inputvals.append(defVal)
        # input vector of default values (needed for ACOSSO, BSS-ANOVA & iREVEAL)
        lines.append(s8 + "self.inputvals = {0}".format(json.dumps(inputvals)))
        # output variables
        for i, v in enumerate(self.output):
            # get basic information
            minVal = gout.get(v).min
            maxVal = gout.get(v).max
            defVal = gout.get(v).default
            desc = gout.get(v).desc
            # create object
            lines.append(s8 + "self.outputs['{0}'] = NodeVars(".format(v))
            lines.append(s12 + "value = {0},".format(defVal))
            lines.append(s12 + "vmin = {0},".format(minVal))
            lines.append(s12 + "vmax = {0},".format(maxVal))
            lines.append(s12 + "vdflt = {0},".format(defVal))
            lines.append(s12 + 'unit = "",')
            lines.append(s12 + 'vst = "pymodel",')
            lines.append(s12 + 'vdesc = "{0}",'.format(desc))
            lines.append(s12 + "tags = [],")
            lines.append(s12 + "dtype = float)")
        # add a blank line on the end
        lines.append("")
        return "\n".join(lines)
