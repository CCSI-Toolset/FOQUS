###############################################################################
# FOQUS Copyright (c) 2012 - 2021, by the software owners: Oak Ridge Institute
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
#
###############################################################################
"""node.py

* This contains the classes for nodes

John Eslick, Carnegie Mellon University, 2014
"""

import os
import time
import json
import math
import subprocess
import logging
import traceback
import re
from foqus_lib.framework.graph.nodeVars import *
from foqus_lib.framework.graph.nodeModelTypes import nodeModelTypes
from collections import OrderedDict
from foqus_lib.framework.foqusOptions.optionList import optionList
from foqus_lib.framework.sim.turbineConfiguration import TurbineInterfaceEx
from foqus_lib.framework.at_dict.at_dict import AtDict


class NodeOptionSets:
    OTHER_OPTIONS = 0
    NODE_OPTIONS = 1
    TURBINE_OPTIONS = 2
    SINTER_OPTIONS = 3
    PLUGIN_OPTONS = 4


class PyCodeInterupt(Exception):
    pass


class NpCodeEx(Exception):
    def __init__(self, msg="", code=100):
        self.code = code
        self.msg = msg

    def __str__(self):
        return str(self.msg)


class NodeEx(foqusException):
    def setCodeStrings(self):
        # 100's reserved for python code script errors
        self.codeString[-1] = "Did not finish"
        self.codeString[0] = "Finished Normally"
        self.codeString[1] = "Simulation error (see job logs)"
        self.codeString[3] = "Maximum wait time exceeded"
        self.codeString[4] = "Failed to create Turbine session ID"
        self.codeString[6] = "Maximum run time exceeded"
        self.codeString[5] = "Failed to add job to Turbine"
        self.codeString[7] = "Turbine simulation error"
        self.codeString[8] = "Failed to start Turbine Job"
        self.codeString[9] = "Unknown model type"
        self.codeString[10] = "Failed to get job status"
        self.codeString[11] = "Graph thread terminated"
        self.codeString[20] = "Error in Python node script code"
        self.codeString[21] = "Error in Python node script code"
        self.codeString[23] = "Could not convert numpy value to list"
        self.codeString[27] = "Can't read variable in results (see log)"
        self.codeString[50] = "Node script interupt exception"
        self.codeString[61] = "Unknow type string"


class Node:
    """
        This class stores information for graph nodes.  It also contains
        function for running a calculations and simulations associated
        with a node.  The varaibles associated with nodes are all stored
        at the graph level, so the parent graph of a node needs to be
        set before running any calcualtions, so the node knows where
        to find variables, turbine config info,...
    """

    def __init__(self, x=0, y=0, z=0, parent=None, name=None):
        #
        self.setGraph(parent, name)  # set parent graph and node name
        self.modelType = nodeModelTypes.MODEL_NONE  # Model type
        self.modelName = ""  # name of node model
        self.calcCount = 0
        self.altInput = None
        self.vis = True  # whether or not to display node
        self.seq = True  # whether or not to include in calcualtion order
        self.x = x  # coordinate for drawing graph
        self.y = y  # coordinate for drawing graph
        self.z = z  # coordinate for drawing graph
        self.calcError = -1  # error code, 0 = good
        ## node calculations
        self.scriptMode = "post"
        self.pythonCode = ""
        ## Node/Model Options
        self.options = optionList()
        ## Turbine stuff
        self.turbSession = 0  # turbine session id
        self.turbJobID = None  # turbine job id
        self.turbApp = None  # application that runs model
        self.turbineMessages = ""
        ## Python Plugin Stuff
        self.pyModel = None
        ##
        self.running = False
        self.synced = True

    def setGraph(self, gr, name=None):
        """
            Set the parent graph, node name, location of inputs and
            location of outputs.
        """
        self.gr = gr
        if name != None:
            self.name = name
        self.inVars = gr.input[self.name]
        self.outVars = gr.output[self.name]
        self.inVarsVector = gr.input_vectorlist[self.name]
        self.outVarsVector = gr.output_vectorlist[self.name]

    def addTurbineOptions(self):
        """
            Add options related to how FOQUS deals with Turbine.  These
            options should only be in nodes that run a model from
            turbine.
        """
        app = self.turbApp
        if app == "Excel":  # excel reset to true by default
            resetSim = False
            resetDisable = False
        else:
            resetSim = False
            resetDisable = False
        self.options.addIfNew(
            name="Visible",
            default=False,
            dtype=bool,
            desc=("This options show the simulator window"),
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Initialize Model",
            default=False,
            dtype=bool,
            desc=(
                "If this is true, the simulation is run with default"
                " values to initialize it before running the "
                " model inputs. This is often useful with Aspen Plus"
            ),
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Reset",
            default=resetSim,
            dtype=bool,
            desc=(
                "This options will cause a simulation to be reset to" " after each run."
            ),
            disable=resetDisable,
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Reset on Fail",
            default=True,
            dtype=bool,
            desc=(
                "This option causes the consumer to shut down if a si"
                "mulation fails.  A new one will start on next run."
            ),
            disable=resetDisable,
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Retry",
            default=False,
            dtype=bool,
            desc=("If a simulation fails retry one time."),
            disable=resetDisable,
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Allow Simulation Warnings",
            default=True,
            desc=(
                "Consider a simulation successful if it completes "
                "with warnings. (AspenPlus only for now)"
            ),
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Max consumer reuse",
            default=90,
            desc=(
                "Number maximum of times to reuse a Turbine consumer"
                " before forcing it to restart"
            ),
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Maximum Wait Time (s)",
            default=1440.0,
            dtype=float,
            desc=(
                "This is the ammount of time in seconds that FOQUS "
                "should wait for results to come back from Turbine."
            ),
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Maximum Run Time (s)",
            default=840.0,
            desc=(
                "This is the ammount of time in seconds that FOQUS "
                "should wait for results to come back from Turbine "
                "once the simulation starts running."
            ),
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Min Status Check Interval",
            default=4.0,
            desc=("This is the minimum amount of time between job " "status checks."),
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Max Status Check Interval",
            default=5.0,
            desc=("This is the maximum ammount of time between job " "status"),
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Override Turbine Configuration",
            default="",
            desc=(
                "Optional, provide a path to a Trubine config to "
                "submit models for this node to a alternative Turbine "
                "gateway.  This can be used for special simualtions."
            ),
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )

    def errorLookup(self, i):
        """
            Give a descriptive error message to go with an integer
            error code.
        """
        ex = NodeEx()
        return ex.codeString.get(i, "unknown error")

    def saveDict(self):
        """
            Put the contents of a node into a dictionary.  This can be
            used as part of a method to save a graph to a file or to
            make a copy of the node, although there are probably better
            ways to make a copy.
        """
        sd = dict()
        sd["modelType"] = self.modelType
        sd["modelName"] = self.modelName
        sd["x"] = self.x
        sd["y"] = self.y
        sd["z"] = self.z
        sd["scriptMode"] = self.scriptMode
        sd["pythonCode"] = self.pythonCode
        sd["calcError"] = self.calcError
        sd["options"] = self.options.saveDict()
        sd["turbApp"] = self.turbApp
        sd["turbSession"] = self.turbSession
        sd["synced"] = self.synced
        return sd

    def loadDict(self, sd):
        """
            Read the node attributes fro a dictionary created by
            saveDict().
        """
        self.modelType = sd.get("modelType", nodeModelTypes.MODEL_NONE)
        self.x = sd.get("x", 0)
        self.y = sd.get("y", 0)
        self.z = sd.get("z", 0)
        self.synced = sd.get("synced", False)
        self.modelName = sd.get("modelName", "")
        self.modelType = sd.get("modelType", nodeModelTypes.MODEL_NONE)
        self.scriptMode = sd.get("scriptMode", "post")
        self.pythonCode = sd.get("pythonCode", "")
        self.calcError = sd.get("calcError", -1)
        self.turbApp = sd.get("turbApp", None)
        self.turbSession = sd.get("turbSession", 0)
        self.options = optionList()
        o = sd.get("options", None)
        if o:
            self.options.loadDict(o)
        if self.modelType == nodeModelTypes.MODEL_TURBINE:
            self.addTurbineOptions()
        # Below is just to maintain compatibility with older session files
        # It may be deleted at some point in the future
        if "inVars" in sd:
            for vkey, var in sd["inVars"].items():
                v = self.gr.input.addVariable(self.name, vkey)
                v.loadDict(var)
        if "outVars" in sd:
            for vkey, var in sd["outVars"].items():
                v = self.gr.output.addVariable(self.name, vkey)
                v.loadDict(var)
        if "inVarsVector" in sd:
            for vkey, var in sd["inVarsVector"].items():
                v = self.gr.input_vectorlist.addVectorVariable(self.name, vkey)
                v.loadDict(var)
        if "outVarsVector" in sd:
            for vkey, var in sd["outVarsVector"].items():
                v = self.gr.output_vectorlist.addVectorVariable(self.name, vkey)
                v.loadDict(var)

    def stringToType(self, s):
        # only check start of string since sinter inclued dimensions
        # after foqus will pick up dimensions from the default value
        if s[:6] == "double":
            return float
        elif s[:5] == "float":
            return float
        elif s[:3] == "int":
            # Covers int and integer
            return int
        elif s[:3] == "str":
            # covers string and str
            return str
        else:
            raise NodeEx(code=61, msg=str(s))

    def setSim(self, newType=None, newModel=None, force=False, ids=None):
        """
        Set-up the node to run a simulation with Turbine
        """
        if newModel == self.modelName and newType == self.modelType and force == False:
            # no change the simulation is already set maybe use force
            # if something about simulation changes and you want to
            # reset the model
            return
        if newModel == None or newModel == "" or newType == nodeModelTypes.MODEL_NONE:
            # No model specified set model to none
            self.modelName = ""
            self.modelType = nodeModelTypes.MODEL_NONE
        else:  # A model name was specified
            self.modelName = newModel
            self.modelType = newType
        # Delete the options will add back options for the new simulation
        self.options.clear()
        # delete all variables where set == sinter other variables
        # where added by user and can stay.  the sinter set name may
        # be a little out dated, but I'll stick with it for now
        # the only variable sets should be sinter and user
        names = list(self.inVars.keys())
        delSets = ["sinter", "pymodel"]
        for name in names:
            if self.gr.input[self.name][name].set in delSets:
                del self.gr.input[self.name][name]
        names = list(self.outVars.keys())
        for name in names:
            if self.gr.output[self.name][name].set in delSets:
                del self.gr.output[self.name][name]
        # clear the pyModel since it may be old now
        self.pyModel = None
        # Now add stuff to the node depending on the model type
        if self.modelType == nodeModelTypes.MODEL_NONE:
            # no model don't add any variables and do nothing
            return
        elif self.modelType == nodeModelTypes.MODEL_PLUGIN:
            # python plugin worry about this later
            inst = self.gr.pymodels.plugins[self.modelName].pymodel_pg()
            # the node can have the pymodel instances variables since
            # i'm not going to use the pymodel instance for anything
            # else there is no need to copy them.  I'll create a
            # different instance for running the model.
            for vkey, v in inst.inputs.items():
                self.gr.input[self.name][vkey] = v
            for vkey, v in inst.outputs.items():
                self.gr.output[self.name][vkey] = v
        elif self.modelType == nodeModelTypes.MODEL_TURBINE:
            sc = self.gr.turbConfig.getSinterConfig(self.modelName)
            modelTitle = str(sc.get("title", ""))
            modelAuthor = str(sc.get("author", ""))
            modelDate = str(sc.get("date", ""))
            modelDesc = str(sc.get("description", ""))
            modelFile = self.gr.turbConfig.getModelFileFromSinterConfigDict(sc)
            app = self.gr.turbConfig.getAppByExtension(modelFile)
            self.turbApp = app
            # Create input vectors, if any
            for name, item in sc["inputs"].items():
                if "vector" in item:
                    vector_name = item.get("vector",None)
                    if vector_name not in self.gr.input_vectorlist[self.name]:
                        self.gr.input_vectorlist[self.name][vector_name] = NodeVarVector()
                        self.gr.input_vectorlist[self.name][vector_name].dtype = object
            # Add inputs
            for name, item in sc["inputs"].items():
                dtype = self.stringToType(item.get("type", "float"))
                if "vector" in item:
                    vector_name = item.get("vector",None)
                    vector_index = item.get("index",None)
                    name = vector_name + "_{0}".format(vector_index)
                self.gr.input[self.name][name] = NodeVars(
                    value=item.get("default", 0.0),
                    vmin=item.get("min", None),
                    vmax=item.get("max", None),
                    vdflt=item.get("default", None),
                    unit=str(item.get("units", "")),
                    vst="sinter",
                    dtype=dtype,
                    vdesc=str(item.get("description", "")),
                    tags=[],
                )
                # If the variable is part of a vector, add it to the vector variable
                if "vector" in item:
                    self.gr.input_vectorlist[self.name][vector_name].vector[vector_index] =\
                        self.gr.input[self.name][name]
                    self.gr.input_vectorlist[self.name][vector_name].ipvname = \
                        (self.name,name)
                        
            # Create output vectors, if any
            for name, item in sc["outputs"].items():
                if "vector" in item:
                    vector_name = item.get("vector",None)
                    if vector_name not in self.gr.output_vectorlist[self.name]:
                        self.gr.output_vectorlist[self.name][vector_name] = NodeVarVector()
                        self.gr.output_vectorlist[self.name][vector_name].dtype = object
            # Add outputs
            for name, item in sc["outputs"].items():
                dtype = self.stringToType(item.get("type", "float"))
                if "vector" in item:
                    vector_name = item.get("vector",None)
                    vector_index = item.get("index",None)
                    name = vector_name + "_{0}".format(vector_index)
                self.gr.output[self.name][name] = NodeVars(
                    value=item.get("default", 0.0),
                    unit=str(item.get("units", "")),
                    vdesc=str(item.get("description", "")),
                    vst="sinter",
                    dtype=dtype,
                    tags=[],
                )
                # If the variable is part of a vector, add it to the vector variable
                if "vector" in item:
                    self.gr.output_vectorlist[self.name][vector_name].vector[vector_index] =\
                        self.gr.output[self.name][name]
                    self.gr.output_vectorlist[self.name][vector_name].opvname = \
                        (self.name,name)
                
            # Add an extra output varialbe for simulation status
            # I think this comes out of all simulation run through
            # SimSinter, but its not in the sinter config file.
            self.gr.output[self.name]["status"] = NodeVars(
                value=0, vdesc="Simulation Status Code", vst="sinter"
            )
            # addTurbineOptions
            self.addTurbineOptions()
            if "settings" in sc:
                for name, item in sc["settings"].items():
                    self.options.add(
                        name=name,
                        default=item["default"],
                        desc=item["description"],
                        optSet=NodeOptionSets.SINTER_OPTIONS,
                    )

    def upadteSCDefaults(self, outfile=None):
        if outfile is None:
            outfile = "{0}.json".format(self.modelName)
        sc = self.gr.turbConfig.getSinterConfig(self.modelName)
        for name, item in sc["inputs"].items():
            if name in self.gr.input[self.name]:
                item["default"] = self.gr.input[self.name][name].value
                item["default"] = item["default"]
        with open(outfile, "wb") as f:
            json.dump(sc, f, indent=2)

    def loadDefaultValues(self):
        """
            Change the current input values to their defaults
        """
        for key, var in self.inVars.items():
            var.value = var.default
            
        for key, var in self.inVarsVector.items():
            var.value = var.default

    def runCalc(self, nanout=False):
        """
            This function calcualtate the node's output values from
            the inputs.  First it does the model calculations then
            any Python post-processing calculations.  The model and
            or the post-processing calculations can be omitted.  If
            niether are pressent the model will successfully execute
            but do nothing.
        """
        self.turbineMessages = ""
        self.calcError = -1  # set error code to incomplete
        self.calcCount += 1
        self.altInput = None
        # raise Exception("Test exeception")
        if nanout:
            # Set all outputs to numpy.nan to avoid confusion about
            # whether the output value is valid.  After successful
            # completion the nan values will be replaced.  May want
            # ouput values for initial guess though so I made this
            # optional and disabled for now.  Should check node status
            # instead of depending on nan
            for vname, var in self.outVars.items():
                var.makeNaN()
        # Run Python script before model
        if (
            self.pythonCode != ""
            and self.pythonCode is not None
            and self.scriptMode == "pre"
        ):
            self.runPython()
        # Run model or python script that should run model
        if (
            self.pythonCode != ""
            and self.pythonCode is not None
            and self.scriptMode == "total"
        ):
            self.runPython()
        else:
            self.runModel()
        # Run python script after model.
        if (
            self.pythonCode != ""
            and self.pythonCode is not None
            and self.scriptMode == "post"
        ):
            self.runPython()
        # If you made it here and nothing threw an exception or reset
        # the error code, the cacluation finished succesfully
        if self.calcError == -1:
            self.calcError = 0

    def runModel(self):
        """
            Run the Model associated with the node.
        """
        self.calcError = -1
        if self.modelType == nodeModelTypes.MODEL_NONE:
            pass
        elif self.modelType == nodeModelTypes.MODEL_PLUGIN:
            self.runPymodelPlugin()
        elif self.modelType == nodeModelTypes.MODEL_TURBINE:
            self.runTurbineCalc(retry=self.options["Retry"].value)
        else:
            # This shouldn't happen from the GUI there should
            # be no way to select an unknown model type.
            logging.getLogger("foqus." + __name__).error(
                "unknown run type: " + str(self.modelType)
            )
            self.calcError = 9

    def getValues(self):
        x = dict()
        f = dict()
        xvector = dict()
        fvector = dict()
        # Copy the inputs and outputs to easy-to-use temporary dicts
        for vkey, var in self.inVars.items():
            x[vkey] = var.value
        for vkey, var in self.outVars.items():
            f[vkey] = var.value
        for vkey, var in self.inVarsVector.items():
            xvector[vkey] = [var.vector[i].value for i in range(len(var.vector))]
        for vkey, var in self.outVarsVector.items():
            fvector[vkey] = [var.vector[i].value for i in range(len(var.vector))]
        return x, f

    def resetModel(self):
        """
            Stop consumer, when the model is run next a new consumer
            will start up for it.  This is useful if a model fails.
        """
        if self.modelType == nodeModelTypes.MODEL_TURBINE:
            self.gr.turbConfig.stopConsumer(self.name)

    def runPymodelPlugin(self):
        """
            Runs a Python node plugin model.
        """
        # create a python model instance if needed
        if not self.pyModel:
            self.pyModel = self.gr.pymodels.plugins[self.modelName].pymodel_pg()
        # set the instance inputs
        for vkey, v in self.gr.input[self.name].items():
            if vkey in self.pyModel.inputs:
                self.pyModel.inputs[vkey].value = v.value
        # run the model
        self.pyModel.setNode(self)
        self.pyModel.run()
        # set the node outputs
        for vkey, v in self.gr.output[self.name].items():
            if vkey in self.pyModel.outputs:
                v.value = self.pyModel.outputs[vkey].value

    def runPython(self):
        # Run the python post code for a node.  I know this could be a
        # big security risk, but for this use it should be okay for now
        #
        # Input variable values are stored in the x dictionary and
        # outputs are stored in the f dictionary
        x = AtDict()
        f = AtDict()
        # Copy the inputs and outputs to easy-to-use temporary dicts
        for vkey, var in self.inVars.items():
            x[vkey] = var.value
        for vkey, var in self.outVars.items():
            f[vkey] = var.value
        # Now try to execute the post code
        try:
            exec(self.pythonCode)
            # copy the output variables values back, and don't allow
            # modification of the input values (you can if you get
            # tricky but don't know why you would.  That would be very
            # confusing.
            for vkey, var in f.items():
                if vkey in self.outVars:
                    self.outVars[vkey].value = var
                    for vec in self.outVarsVector:
                        if vec in vkey:
                            idx = int(vkey.split('_')[-1])
                            self.outVars[vkey].value = self.outVarsVector[vec].vector[idx]['value']
        except PyCodeInterupt as e:
            logging.getLogger("foqus." + __name__).error(
                "Node script interupt: " + str(e)
            )
            if self.calcError == -1:
                # if no error code set go with 50
                # otherwise the sim would appear to be successful
                self.calcError = 50
        except NpCodeEx as e:
            logging.getLogger("foqus." + __name__).exception(
                "Error in node python code: {0}, {1}".format(e.code, e.msg)
            )
            self.calcError = e.code
        except Exception as e:
            logging.getLogger("foqus." + __name__).exception(
                "Error in node python code"
            )
            self.calcError = 21

    def generateInputJSON(self):
        # Takes the input variables in the sinter set and generates
        # a json input file in the format expected by the turbine
        # gateway currently this json file is just for one at a time
        try:
            cid = self.gr.turbConfig.consumerID(self.name)
        except:
            cid = None
        inputSetL1 = dict()
        inputSetL2 = dict()
        inputSetL1["Simulation"] = self.modelName
        inputSetL1["Initialize"] = self.options["Initialize Model"].value
        inputSetL1["Reset"] = self.options["Reset"].value
        inputSetL1["Visible"] = self.options["Visible"].value
        inputSetL1["Input"] = inputSetL2
        if cid is not None and cid != 0:
            inputSetL1["ConsumerId"] = cid
            # inputSetL1["ConsumerId"] = cid.replace('-', "")
        runList = [inputSetL1]
        for vkey, var in self.gr.input[self.name].items():
            if var.set == "sinter":
                try:
                    if self.altInput is not None:
                        # WHY pylint erroneously reports this as an error,
                        # because it is not able to take the "is not None" check into account
                        inputSetL2[vkey] = self.altInput[vkey]  # pylint: disable=unsubscriptable-object
                    else:
                        inputSetL2[vkey] = var.value
                except:
                    self.calcError = 23
                    raise NodeEx(
                        code=23,
                        msg="Node: {0}, Var: {1}, Value: {2}".format(
                            self.name, vkey, var.value
                        ),
                    )
        for vkey, var in self.options.items():
            if var.optSet == NodeOptionSets.SINTER_OPTIONS:
                inputSetL1["Input"][vkey] = var.value
        s = json.dumps(runList, sort_keys=True, indent=2)
        logging.getLogger("foqus." + __name__).debug("Generated Job JSON:\n" + s)
        return s

    def runTurbineCalc(self, retry=False):
        """
            This function runs turbine models
        """
        res = None
        altTurb = self.options["Override Turbine Configuration"].value
        maxWaitTime = self.options["Maximum Wait Time (s)"].value
        maxRunTime = self.options["Maximum Run Time (s)"].value
        minCheckInt = self.options["Min Status Check Interval"].value
        maxCheckInt = self.options["Max Status Check Interval"].value
        alwarn = self.options["Allow Simulation Warnings"].value
        maxConsumerUse = self.options["Max consumer reuse"].value
        app = self.turbApp
        # app = self.gr.turbConfig.getSimApplication(self.modelName)
        configProfile = self.gr.turbConfig
        if altTurb != "":
            # use alternate to local TurbineLite
            # less good but sometimes needed to run a special kind of
            # simulation that can't be run locally.
            localRun = False
        else:
            # This is always the first choice, almost always use this
            localRun = True  # use local
        # Reload the TurbineConfig depending on run type.
        if localRun:
            configProfile.updateSettings()
        else:
            configProfile.updateSettings(altConfig=altTurb)
            logging.getLogger("foqus." + __name__).debug(
                "Alternate Turbine configuration: {0} for node: {1}".format(
                    altTurb, self.name
                )
            )
        # turbine session id
        sid = self.createTurbineSession(forceNew=False)
        # check consumer reuse counter
        # Count that the consumer has been used. stop if hit maxuse
        if localRun and maxConsumerUse > 0:
            count = configProfile.consumerCount(self.name)
            if count >= maxConsumerUse:
                logging.getLogger("foqus." + __name__).debug(
                    "Max consumer use exceeded restarting consumer {0}".format(
                        self.name
                    )
                )
                configProfile.stopConsumer(self.name)
        # Start consumer for this model.  If already started this
        # does nothing.
        if localRun:
            configProfile.startConsumer(self.name, self.modelName)
            configProfile.consumerCountInc(self.name)
        # Generate json string for job and load it
        inputjson = self.generateInputJSON()
        inputData = json.loads(inputjson)
        try:  # try to append job to turbine session
            jobID = configProfile.retryFunction(
                5, 30, 1, configProfile.createJobsInSession, sid, inputData
            )[0]
        except Exception as e:
            logging.getLogger("foqus." + __name__).exception("Failed create job")
            self.calcError = 5
            configProfile.updateSettings()
            return
        # Try to start jobs if doesn't start at first try some more
        try:
            configProfile.retryFunction(5, 30, 1, configProfile.startSession, sid)
        except Exception as e:
            logging.getLogger("foqus." + __name__).exception(
                "Failed start job: {0}".format(jobID)
            )
            self.calcError = 8
            configProfile.updateSettings()
            return
        logging.getLogger("foqus." + __name__).debug(
            "Started Job: {0} Turbin SID: {1}".format(jobID, sid)
        )
        # Monitor jobs, there are some timeouts if jobs fail to finish
        # in an allowed amount of time they are terminated
        try:
            # passing the node name and model name allows the consumer
            # to be monitored and restarted if it stops unexpectedly.
            res = configProfile.monitorJob(
                jobID,
                maxWaitTime=maxWaitTime,
                maxRunTime=maxRunTime,
                minCheckInt=minCheckInt,
                maxCheckInt=maxCheckInt,
                stopFlag=self.gr.stop,
                nodeName=self.name,
                simName=self.modelName,
                allowWarnings=alwarn,
                app=app,
                checkConsumer=localRun,
            )
            logging.getLogger("foqus." + __name__).debug(
                "Job finished successfully: " + str(jobID)
            )
        except TurbineInterfaceEx as e:
            res = configProfile.res
            if e.code == 351:
                self.calcError = 1
            elif e.code == 352:
                self.calcError = 6
            elif e.code == 353:
                self.calcError = 3
            elif e.code == 354:
                self.calcError = 10
            elif e.code == 355:
                self.calcError = 11
            else:
                self.calcError = 7
            logging.getLogger("foqus." + __name__).error(
                "Error while motoring job: {0}, Ex: {1}".format(str(jobID), str(e))
            )
        except Exception as e:
            self.calcError = 10
            res = configProfile.res
            logging.getLogger("foqus." + __name__).warning(
                "Error while motoring job: {0}, Ex: {1}".format(str(jobID), str(e))
            )
        # if error code is not -1 some other error and sim not successful
        readResults = True
        if self.calcError == -1:
            logging.getLogger("foqus." + __name__).info(
                "Job " + str(jobID) + " Finished Successfully"
            )
        else:
            # The job failed, don't know why but I'll restart the
            # consumer so that the next run will be less likely to fail.
            if localRun and self.options["Reset on Fail"].value:
                logging.getLogger("foqus." + __name__).info(
                    "Job failed, stopping consumer for {0}".format(self.modelName)
                )
                self.resetModel()
            elif localRun:
                logging.getLogger("foqus." + __name__).info(
                    "Job failed, will not stop consumer for {0}".format(self.modelName)
                )
            # Possibly retry the simulation if it failed
            if retry and not self.gr.stop.isSet():
                logging.getLogger("foqus." + __name__).info(
                    "Retrying Failed Job " + str(jobID)
                )
                # rerun this function
                # reset error code so doesn't automatically think
                # the retry fails.
                self.calcError = -1
                self.runTurbineCalc(retry=False)
                # don't read results if retrying because the results
                # will be read in the retry call if successful
                readResults = False
            else:
                logging.getLogger("foqus." + __name__).info(
                    "Job " + str(jobID) + " Failed will not retry"
                )
        # Even if there was an error try to read output
        logging.getLogger("foqus." + __name__).debug(
            "Job " + str(jobID) + " Results:\n" + json.dumps(res)
        )
        if res is not None:
            m = res.get("Messages", "")
            if m is None or m == "":
                self.turbineMessages = ""
            else:
                self.turbineMessages = json.dumps(m)
            # single quotes are bad news when trying to instert this into
            # the TurbineLite database in consumer mode so they gone
            self.turbineMessages = self.turbineMessages.replace("'", '"')
        if res and readResults and "Output" in res and res["Output"]:
            outputlog = []
            for vname in res["Output"]:
                try:
                    self.gr.output[self.name][vname].value = res["Output"][vname][
                        "value"
                    ]
                    outputlog.append(
                        "{0} = {1}".format(vname, res["Output"][vname]["value"])
                    )
                except KeyError:
                    # if there is an output of the simulation that
                    # doesn't match the outputs in the node that's
                    # okay may have deleted a variable.  Simulation may
                    # also have failed before producing any output.
                    logging.getLogger("foqus." + __name__).exception()
            logging.getLogger("foqus." + __name__).debug(
                "Outputs: {0}\n".format("\n".join(outputlog))
            )
        # reset the turbine config back to whatever is in the settings
        # in case an alternative config was used.
        configProfile.updateSettings()

    def createTurbineSession(self, forceNew=True):
        """
            Create a new Turbine session for grouping
            simulation results on Turbine.
        """
        # Check that a simulation is assigned to this node and that the
        # run type is turbine otherwise return None, this will mean that
        # the node is not using turbine to run
        if self.modelType != nodeModelTypes.MODEL_TURBINE:
            self.turbSession = None
            return None
        # If force new loose the old session so need a new one
        if forceNew:
            self.turbSession = None
        # Try to get a new session id from the gateway if exists
        if self.turbSession:
            # check that it is valid
            try:
                if self.gr.turbConfig.sessionExists(self.turbSession):
                    return self.turbSession
            except Exception as e:
                logging.getLogger("foqus." + __name__).exception(
                    "Failed to check for existence of session while"
                    " creating session, Exception: "
                )
                return 0
        # Session didn't exist so create a new id
        try:
            self.turbSession = self.gr.turbConfig.createSession()
        except Exception as e:
            logging.getLogger("foqus." + __name__).exception(
                "Failed to create a new session."
            )
            self.turbSession = 0
            return 0
        return self.turbSession

    def killTurbineSession(self):
        """
            Tries to kill all turbine jobs associated with this node
            started by any thread or process.
        """
        if self.modelType != nodeModelTypes.MODEL_TURBINE:
            return
        if self.modelName == "" or self.modelName == None:
            return
        sid = self.turbSession
        if sid == 0 or sid == "" or sid == None:
            return
        try:
            self.gr.turbConfig.killSession(sid)
        except Exception as e:
            logging.getLogger("foqus." + __name__).error(
                "Failed to kill session sid: {0} Exception: {1}".format(sid, str(e))
            )
