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
"""
Methods:
    setName(name):
        Sets the name of the model

    getName():
        Gets name of the model

    setName(name):
        Sets the run file name (name of the driver or emulator file)

    getName():
        Gets run file name of the model (name of the driver or emulator file)

    setNumSamples(value):
        Sets number of samples

    getNumSamples():
        Get number of samples

    getNumInputs():
        Get number of inputs

    getNumOutputs():
        Get number of outputs

    setInputNames(names):
        Sets input names
        Arguments:
            Can be a collection (list, tuple) of names as a single argument -OR-
                multiple arguments with each being a single name

    getInputNames():
        Get input names. Returns tuple of names

    setOutputNames(names):
        Sets output names
        Arguments:
            Can be a collection (list, tuple) of names as a single argument -OR-
                multiple arguments with each being a single name

    getOutputNames():
        Get output names. Returns tuple of names

    setInputTypes(values):
        Sets input types (Model.VARIABLE or Model.FIXED)
        Arguments:
            A collection of values

    getInputTypes():
        Get input types. Returns tuple of input types (Model.VARIABLE or Model.FIXED)

    setInputMins(values):
        Sets input minimum values
        Arguments:
            A collection of values

    getInputMins():
        Get input minimums. Returns numpy.array of minimum values

    setInputMaxs(values):
        Sets input maximum values
        Arguments:
            A collection of values

    getInputMaxs():
        Get input maximums. Returns numpy.array of maximum values

    setInputDefaults(values):
        Sets input default values
        Arguments:
            A collection of values

    getInputDefaults():
        Get input defaults. Returns numpy.array of default values

    setSelectedOutputs(indices):
        Sets which outputs we want to look at
        Arguments:
            A collection of indices for the outputs selected

    getSelectedOutputs():
        Get the indices for the selected outputs

    setDriverName():
        Sets the filename of the driver or emulator

    getDriverName():
        Gets the filename of the driver or emulator
"""

import collections.abc
import numbers, json
import numpy

from .SamplingMethods import SamplingMethods
from .Distribution import *


class Model:
    FIXED, VARIABLE = list(range(2))  # Input type
    GATEWAY, LOCAL, EMULATOR = list(range(3))  # Run type
    NOT_CALCULATED, NEED_TO_CALCULATE, CALCULATED = list(
        range(3)
    )  # Emulator output status

    def __init__(self):
        self.name = None
        self.driverName = None
        self.optDriverName = None
        self.ensembleOptDriverName = None
        self.auxDriverName = None
        self.runType = None
        self.numInputs = 0
        self.numVarInputs = 0
        self.numOutputs = 0
        self.inputNames = None
        self.outputNames = None
        self.inputTypes = None
        self.inputMins = numpy.array(None)
        self.inputMaxs = numpy.array(None)
        self.inputDists = None
        self.inputDefaults = numpy.array(None)
        self.outputSelections = None
        self.emulatorOutputStatus = None
        self.emulatorTrainingFile = None
        self.namesIncludeNodes = False
        self.flowsheetFixed = None

    def saveFile(self, filename="UQModelTest.json"):
        """
        Save the model to a json file
        """
        sd = self.saveDict()
        with open(filename, "w") as f:
            json.dump(sd, f, indent=2)

    def saveDict(self):
        """
        Put model contents in a dictionary, so it can be easily
        saved in a json file.
        """
        sd = dict()
        sd["name"] = self.name
        sd["driverName"] = self.driverName
        sd["optDriverName"] = self.optDriverName
        sd["auxDriverName"] = self.auxDriverName
        sd["runType"] = self.runType
        sd["inputNames"] = self.inputNames
        sd["outputNames"] = self.outputNames
        sd["inputTypes"] = self.inputTypes
        sd["inputMins"] = self.inputMins.tolist()
        sd["inputMaxs"] = self.inputMaxs.tolist()
        sd["inputDists"] = []

        if self.inputDists:
            for dist in self.inputDists:
                sd["inputDists"].append(dist.saveDict())

        sd["inputDefaults"] = self.inputDefaults.tolist()
        sd["outputSelections"] = self.outputSelections
        sd["emulatorOutputStats"] = self.emulatorOutputStatus
        sd["emulatorTrainingFile"] = self.emulatorTrainingFile
        sd["namesIncludeNodes"] = self.namesIncludeNodes
        sd["inputsFlowsheetFixed"] = self.flowsheetFixed
        return sd

    def loadFile(self, filename="UQModelTest.json"):
        with open(filename, "r") as f:
            sd = json.load(f)
        self.loadDict(sd)

    def loadDict(self, sd):
        """
        Load model from a dictionary
        """
        self.setName(sd.get("name", None))
        self.setDriverName(sd.get("driverName", None))
        self.setOptDriverName(sd.get("optDriverName", None))
        self.setAuxDriverName(sd.get("auxDriverName", None))
        self.setRunType(sd.get("runType", None))
        self.setInputNames(sd.get("inputNames", None))
        self.setOutputNames(sd.get("outputNames", None))
        self.setInputTypes(sd.get("inputTypes", None))
        self.setInputMins(sd.get("inputMins", None))
        self.setInputMaxs(sd.get("inputMaxs", None))
        self.inputDists = []
        if "inputDists" in sd:
            for distDict in sd["inputDists"]:
                distr = Distribution(Distribution.UNIFORM)
                distr.loadDict(distDict)
                self.inputDists.append(distr)

        if not self.inputDists:
            self.inputDists = None
        self.setInputDefaults(sd.get("inputDefaults", None))
        self.setSelectedOutputs(sd.get("outputSelections", None))
        self.setNamesIncludeNodes(sd.get("namesIncludeNodes", None))
        stats = sd.get("emulatorOutputStats", None)
        for i, stat in enumerate(stats):
            self.setEmulatorOutputStatus(i, stat)
        self.setEmulatorTrainingFile(sd.get("emulatorTrainingFile", None))
        self.inputsFlowsheetFixed = sd.get("inputsFlowsheetFixed", None)

    def getName(self):
        return self.name

    def setName(self, name):
        self.name = name

    def getDriverName(self):
        return self.driverName

    def setDriverName(self, name):
        self.driverName = name

    def getOptDriverName(self):
        return self.optDriverName

    def setOptDriverName(self, name):
        self.optDriverName = name

    def getEnsembleOptDriverName(self):
        return self.ensembleOptDriverName

    def setEnsembleOptDriverName(self, name):
        self.ensembleOptDriverName = name

    def getAuxDriverName(self):
        return self.auxDriverName

    def setAuxDriverName(self, name):
        self.auxDriverName = name

    def getRunType(self):
        return self.runType

    def setRunType(self, runType):
        self.runType = runType

    def getNumInputs(self):
        return self.numInputs

    def getNumVarInputs(self):
        inputTypes = self.getInputTypes()
        numInputs = self.getNumInputs()
        count = 0
        for i in range(numInputs):
            if inputTypes[i]:
                count += 1
        self.numVarInputs = count
        return self.numVarInputs

    def getNumOutputs(self):
        return self.numOutputs

    def getEmulatorOutputStatus(self):
        return self.emulatorOutputStatus

    def setEmulatorOutputStatus(self, outputIds, value):

        if isinstance(outputIds, collections.abc.Sequence):  # Check if list or tuple
            for outputId in outputIds:
                self.emulatorOutputStatus[outputId] = value
        else:
            self.emulatorOutputStatus[outputIds] = value

    def getEmulatorTrainingFile(self):
        return self.emulatorTrainingFile

    def setEmulatorTrainingFile(self, fname):
        self.emulatorTrainingFile = fname

    def setNamesIncludeNodes(self, value):
        self.namesIncludeNodes = value

    def getNamesIncludeNodes(self):
        return self.namesIncludeNodes

    def setInputNames(self, *names):
        if len(names) == 1:
            # Remove single value from tuple. Needed if argument is a collection
            names = names[0]
        if isinstance(names, str):  # Single string
            self.inputNames = (names,)
        # Check all items in collection are strings
        elif all(isinstance(name, str) for name in names):
            self.inputNames = tuple([str(name) for name in names])
        else:
            raise TypeError("Not all names are strings!")

        self.numInputs = len(self.inputNames)
        self.flowsheetFixed = [False] * self.numInputs

    def getInputNames(self):
        self.inputNames = tuple([str(name) for name in self.inputNames])
        return self.inputNames

    def setOutputNames(self, *names):
        if len(names) == 1:
            names = names[0]
        if isinstance(names, str):  # Single string
            self.outputNames = (names,)
        # Check all items in collection are strings
        elif all(isinstance(name, str) for name in names):
            self.outputNames = tuple(names)
        else:
            raise TypeError("Not all names are strings!")

        self.numOutputs = len(self.outputNames)
        self.emulatorOutputStatus = [Model.NOT_CALCULATED] * self.numOutputs

    def getOutputNames(self):
        return self.outputNames

    def setInputTypes(self, types):
        if len(types) != self.numInputs:
            raise ValueError("Number of types does not match number of inputs!")
        self.inputTypes = tuple(types)

    def getInputTypes(self):
        return self.inputTypes

    def setInputMins(self, mins):
        if len(mins) != self.numInputs:
            raise ValueError("Number of minimums does not match number of inputs!")
        self.inputMins = numpy.array(mins)

    def getInputMins(self):
        return self.inputMins

    def setInputMaxs(self, maxs):
        if len(maxs) != self.numInputs:
            raise ValueError("Number of maximums does not match number of inputs!")
        self.inputMaxs = numpy.array(maxs)

    def getInputMaxs(self):
        return self.inputMaxs

    def getInputDistributions(self):
        return self.inputDists

    def setInputDistributions(self, distTypes, param1Vals=None, param2Vals=None):
        if len(distTypes) == 0 or distTypes == None:
            self.inputDists = []
        # Check if distTypes is a collection of Distribution objects
        elif all([isinstance(dist, Distribution) for dist in distTypes]):
            self.inputDists = distTypes
        else:
            inputDists = []
            if not param1Vals:
                param1Vals = [None]
            if not param2Vals:
                param2Vals = [None]
            # print distTypes, param1Vals, param2Vals
            for dist, val1, val2 in zip(distTypes, param1Vals, param2Vals):
                if dist is None:
                    distribObj = None
                else:
                    distribObj = Distribution(dist)
                    distribObj.setParameterValues(val1, val2)
                inputDists = inputDists + [distribObj]
            self.inputDists = tuple(inputDists)

    def setInputDefaults(self, defaults):
        if len(defaults) != self.numInputs:
            raise ValueError("Number of defaults does not match number of inputs!")
        self.inputDefaults = numpy.array(defaults)

    def getInputDefaults(self):
        return self.inputDefaults

    def setInputFlowsheetFixed(self, indexOrTuple):
        if isinstance(indexOrTuple, (list, tuple)):
            self.flowsheetFixed = indexOrTuple
        else:
            if self.flowsheetFixed is None:
                self.flowsheetFixed = [False] * self.numInputs
            self.flowsheetFixed[indexOrTuple] = True

    def getInputFlowsheetFixed(self, index=None):
        if index is None:
            return self.flowsheetFixed
        else:
            return self.flowsheetFixed[index]

    def setSelectedOutputs(self, indices):
        self.outputSelections = indices

    def getSelectedOutputs(self):
        return self.outputSelections
