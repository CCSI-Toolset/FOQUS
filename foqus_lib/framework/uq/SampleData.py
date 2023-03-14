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
    SampleData(Model):
        Must be instantiated with an object of type Model

    setSampleMethod(value):
        Sets sample method with SamplingMethods value.  Can be string full name
        or PSUADE abbrev

    getSampleMethod():
        Get sample method

    setNumSamples(value):
        Sets the number of samples within the model
    getNumSamples():
        Get number of samples

    getModelName():
        Gets the name of the model
    getNumInputs():
        Get number of inputs
    getNumOutputs():
        Get number of outputs
    getInputNames():
        Get input names. Returns tuple of names
    getOutputNames():
        Get output names. Returns tuple of names
    getInputTypes():
        Get input types (Model.FIXED or Model.VARIABLE).
        Returns tuple of values
    getInputMins():
        Get input minimums. Returns numpy array of values
    getInputMaxs():
        Get input maximums. Returns numpy array of values
    getInputDefaults():
        Get input defaults. Returns numpy array of values
    getInputDistributions():
        Get tuple of input Distribution objects
    getSelectedOutputs():
        Get the indices of the selected outputs
    getDriverName():
        Get the file for the driver or emulator for local runs

    setSampleFileName(name):
        Set the name of the file from which to sample.
        This is to accomodate the S distribution type in psuade
    getSampleFileName():
        Get the name of the file that was sampled

    setInputDistributions(distributions, parameter1Values, parameter2Values):
        Sets input distributions
        Arguments:
            distributions - A collection of Distribution enum values,
                            distribution names, or abbrevs
            parameter1Values - A collection of the values for parameter 1
                                (mean, alpha, etc.)
                                Use None for those values that are empty
                                    (e.g. mean for uniform distribution)
            parameter2Values - A collection of the values for parameter 2
                                (std dev, beta, etc.)
                                Use None for those values that are empty
                                    (e.g. mean for uniform distribution)


    getInputDistributions():
        Get input distributions.  Returns tuple of Distribution enum values

    setInputData(data):
        Arguments:
            Can be a numpy.array or numpy.mat
            Also can be python collection of numbers:
                [1,2,3]: 1x3 matrix
                [(1,2,3),(4,5,6)]: 2x3 matrix
            Each row corresponds to a sample.
            Each column corresponds to an input.

    getInputData():
        Get input data as a numpy.array.  Each row is a sample.
        Each column is one input.

    setOutputData(data):
        Arguments:
            Can be a numpy.array or numpy.mat
            Also can be python collection of numbers:
                [1,2,3]: 1x3 matrix
                [(1,2,3),(4,5,6)]: 2x3 matrix
            Each row corresponds to a sample.
            Each column corresponds to an output.

    getOutputData():
        Get output data as a numpy.array.  Each row is a sample.
        Each column is one output.

    setRunState(data):
        Arguments:
            Can be a numpy.array of bools
            Also can be python collection of bools: [True, False, True, True]

    getRunState():
        Get run state data.  Returns numpy.array of bools

    setLegendreOrder(int order):
        Sets the order for Legendre Polynomial response surface type

    getLegendreOrder():
        Returns the Legendre Polynomial response surface order

    getValidSamples():
        Returns a new SampleData object that contains all the valid samples (run state = True)

    writeToPsuade():
        Writes SampleData object to a psuade file

    writeToCsv():
        Writes SampleData data to a csv file that can be read in by Excel
"""

import os
import numpy
import copy
import time
from .Model import Model
from .Distribution import Distribution
from .SamplingMethods import SamplingMethods
from .ResponseSurfaces import ResponseSurfaces
from .UQAnalysis import UQAnalysis


class SampleData(object):
    def __init__(self, model, session=None):
        if not isinstance(model, Model):
            raise TypeError("Expecting an object of type Model!")
        self.ID = time.strftime("Ensemble_%y%m%d%H%M%S")
        self.session = session
        self.numSamples = 0
        self.origNumSamples = None
        self.numSamplesAdded = 0
        self.sampleMethod = None
        self.model = copy.deepcopy(model)
        self.inputData = []
        self.outputData = []
        self.runState = []
        self.legendreOrder = None
        self.fromFile = False
        self.sampleRSType = None
        self.analyses = []
        self.turbineJobIds = []
        self.turbineSession = None
        self.turbineResub = []
        self.numImputedPoints = 0

    def __deepcopy__(self, memo):
        x = SampleData.__new__(SampleData)
        memo[id(self)] = x
        for n, v in self.__dict__.items():
            if n == "session":
                setattr(x, n, self.__getattribute__(n))
            elif n == "analyses":
                setattr(x, n, [])
            else:
                setattr(x, n, copy.deepcopy(v, memo))
        return x

    def saveDict(self):
        sd = dict()
        sd["ID"] = self.ID
        sd["numSamples"] = self.numSamples
        sd["origNumSamples"] = self.origNumSamples
        sd["numSamplesAdded"] = self.numSamplesAdded
        sd["numImputedPoints"] = self.numImputedPoints
        sd["fromFile"] = self.fromFile
        sd["sampleMethod"] = SamplingMethods.getPsuadeName(self.sampleMethod)
        sd["model"] = self.model.saveDict()
        if isinstance(self.inputData, numpy.ndarray):
            sd["inputData"] = self.inputData.tolist()
        else:
            sd["inputData"] = self.inputData

        if isinstance(self.outputData, numpy.ndarray):
            sd["outputData"] = self.outputData.tolist()
        else:
            sd["outputData"] = self.outputData
        sd["runState"] = self.runState.tolist()
        sd["legendreOrder"] = self.legendreOrder
        sd["fromFile"] = self.fromFile
        sd["sampleRSType"] = ResponseSurfaces.getPsuadeName(self.sampleRSType)
        sd["turbineJobIds"] = self.turbineJobIds
        sd["turbineSession"] = self.turbineSession
        sd["turbineResub"] = self.turbineResub
        sd["analyses"] = []
        for analysis in self.analyses:
            sd["analyses"].append(analysis.saveDict())

        return sd

    def loadDict(self, sd):
        self.model = Model()
        try:
            self.model.loadDict(sd["model"])
        except:
            pass

        self.setID(sd.get("ID", ""))
        self.setNumSamples(sd.get("numSamples", 0))
        self.origNumSamples = sd.get("origNumSamples", self.getNumSamples())
        self.setNumSamplesAdded(sd.get("numSamplesAdded", 0))
        self.setNumImputedPoints(sd.get("numImputedPoints", 0))
        self.setFromFile(sd.get("fromFile", False))
        self.setSampleMethod(sd.get("sampleMethod", None))
        self.setInputData(sd.get("inputData", None))
        self.setOutputData(sd.get("outputData", None))
        self.setRunState(sd.get("runState", None))
        self.legendreOrder = sd.get("legendreOrder", None)
        self.fromFile = sd.get("fromFile", False)
        self.sampleRSType = ResponseSurfaces.getEnumValue(sd.get("sampleRSType"))
        self.turbineJobIds = sd.get("turbineJobIds", [])
        self.turbineSession = sd.get("turbineSession", None)
        self.turbineResub = sd.get("turbineResub", [])
        inputDists = []
        if "inputDists" in sd["model"]:
            for distDict in sd["model"]["inputDists"]:
                distr = Distribution(Distribution.UNIFORM)
                distr.loadDict(distDict)
                inputDists.append(distr)
        self.setInputDistributions(inputDists)
        self.analyses = []
        if "analyses" in sd:
            for analDict in sd["analyses"]:
                type = UQAnalysis.getTypeEnumValue(analDict["type"])
                if type == UQAnalysis.PARAM_SCREEN:
                    from .ParameterScreening import ParameterScreening

                    anal = ParameterScreening(
                        self, analDict["outputs"], analDict["subType"]
                    )
                elif type == UQAnalysis.UNCERTAINTY:
                    from .UncertaintyAnalysis import UncertaintyAnalysis

                    anal = UncertaintyAnalysis(self, analDict["outputs"])
                elif type == UQAnalysis.CORRELATION:
                    from .CorrelationAnalysis import CorrelationAnalysis

                    anal = CorrelationAnalysis(self, analDict["outputs"])
                elif type == UQAnalysis.SENSITIVITY:
                    from .SensitivityAnalysis import SensitivityAnalysis

                    anal = SensitivityAnalysis(
                        self, analDict["outputs"], analDict["subType"]
                    )
                elif type == UQAnalysis.VISUALIZATION:
                    from .Visualization import Visualization

                    anal = Visualization(self, analDict["outputs"], analDict["inputs"])
                else:  # RS Analyses
                    userRegressionFile = (
                        analDict["userRegressionFile"]
                        if "userRegressionFile" in analDict
                        else None
                    )
                    if type == UQAnalysis.RS_VALIDATION:
                        from .RSValidation import RSValidation

                        testFile = (
                            analDict["testFile"] if "testFile" in analDict else None
                        )
                        anal = RSValidation(
                            self,
                            analDict["outputs"],
                            analDict["rs"],
                            analDict["rsOptions"],
                            analDict["genCodeFile"],
                            analDict["nCV"],
                            userRegressionFile,
                            testFile,
                        )
                    elif type == UQAnalysis.RS_UNCERTAINTY:
                        from .RSUncertaintyAnalysis import RSUncertaintyAnalysis

                        anal = RSUncertaintyAnalysis(
                            self,
                            analDict["outputs"],
                            analDict["subType"],
                            analDict["rs"],
                            analDict["rsOptions"],
                            userRegressionFile,
                            analDict["xprior"],
                        )
                    elif type == UQAnalysis.RS_SENSITIVITY:
                        from .RSSensitivityAnalysis import RSSensitivityAnalysis

                        anal = RSSensitivityAnalysis(
                            self,
                            analDict["outputs"],
                            analDict["subType"],
                            analDict["rs"],
                            analDict["rsOptions"],
                            userRegressionFile,
                            analDict["xprior"],
                        )
                    elif type == UQAnalysis.INFERENCE:
                        from .RSInference import RSInference

                        anal = RSInference(
                            self,
                            analDict["ytable"],
                            analDict["xtable"],
                            analDict["obsTable"],
                            analDict["genPostSample"],
                            analDict["addDisc"],
                            analDict["showList"],
                            userRegressionFile=userRegressionFile,
                        )
                    elif type == UQAnalysis.RS_VISUALIZATION:
                        from .RSVisualization import RSVisualization

                        anal = RSVisualization(
                            self,
                            analDict["outputs"],
                            analDict["inputs"],
                            analDict["rs"],
                            analDict["minVal"],
                            analDict["maxVal"],
                            analDict["rsOptions"],
                            userRegressionFile,
                        )

                anal.loadDict(analDict)
                self.analyses.append(anal)

    def setSession(self, session):
        self.session = session

    def getSession(self):
        return self.session

    def setID(self, string):
        self.ID = string

    def getID(self):
        return self.ID

    def setSampleMethod(self, value):
        if isinstance(value, str):  # Single string
            value = SamplingMethods.getEnumValue(value)
        self.sampleMethod = value

    def getSampleMethod(self):
        return self.sampleMethod

    def setNumSamples(self, value):
        self.numSamples = value
        self.runState = [False] * value
        if self.origNumSamples is None:
            self.origNumSamples = value

    def getNumSamples(self):
        return self.numSamples

    def setNumSamplesAdded(self, value):
        self.numSamplesAdded = value

    def getNumSamplesAdded(self):
        return self.numSamplesAdded

    def setNumImputedPoints(self, value):
        self.numImputedPoints = value

    def getNumImputedPoints(self):
        return self.numImputedPoints

    def setOrigNumSamples(self, value):
        self.origNumSamples = value

    def getOrigNumSamples(self):
        return self.origNumSamples

    def getModelName(self):
        return self.model.getName()

    def setModelName(self, name):
        self.model.setName(name)

    def getNumInputs(self):
        return self.model.getNumInputs()

    def getNumVarInputs(self):
        return self.model.getNumVarInputs()

    def getNumOutputs(self):
        return self.model.getNumOutputs()

    def getNamesIncludeNodes(self):
        return self.model.getNamesIncludeNodes()

    def getInputNames(self):
        return self.model.getInputNames()

    def getOutputNames(self):
        return self.model.getOutputNames()

    def getInputTypes(self):
        return self.model.getInputTypes()

    def getInputMins(self):
        return self.model.getInputMins()

    def getInputMaxs(self):
        return self.model.getInputMaxs()

    def getInputDefaults(self):
        return self.model.getInputDefaults()

    def getInputFlowsheetFixed(self, index=None):
        return self.model.getInputFlowsheetFixed(index)

    def getSelectedOutputs(self):
        return self.model.getSelectedOutputs()

    def getDriverName(self):
        return self.model.getDriverName()

    def setDriverName(self, name):
        self.model.setDriverName(name)

    def getOptDriverName(self):
        return self.model.getOptDriverName()

    def setOptDriverName(self, name):
        self.model.setOptDriverName(name)

    def getEnsembleOptDriverName(self):
        return self.model.getEnsembleOptDriverName()

    def setEnsembleOptDriverName(self, name):
        self.model.setEnsembleOptDriverName(name)

    def getAuxDriverName(self):
        return self.model.getAuxDriverName()

    def setAuxDriverName(self, name):
        self.model.setAuxDriverName(name)

    def getRunType(self):
        return self.model.getRunType()

    def setRunType(self, value):
        self.model.setRunType(value)

    def setFromFile(self, value):
        self.fromFile = value

    def getFromFile(self):
        return self.fromFile

    def setSampleRSType(self, RSType):
        # print RSType
        if isinstance(RSType, str):
            self.sampleRSType = ResponseSurfaces.getEnumValue(RSType)
        else:
            self.sampleRSType = RSType

    def getSampleRSType(self):
        return self.sampleRSType

    def setEmulatorOutputStatus(self, outputIds, value):
        self.model.setEmulatorOutputStatus(outputIds, value)

    def getEmulatorOutputStatus(self):
        return self.model.getEmulatorOutputStatus()

    def setEmulatorTrainingFile(self, fname):
        self.model.setEmulatorTrainingFile(fname)

    def getEmulatorTrainingFile(self):
        return self.model.getEmulatorTrainingFile()

    def setInputDistributions(self, distTypes, param1Vals=None, param2Vals=None):
        self.model.setInputDistributions(distTypes, param1Vals, param2Vals)

    def getInputDistributions(self):
        return self.model.getInputDistributions()

    def setInputData(self, data):
        temp = numpy.array(data, dtype=float, ndmin=2)
        if temp.shape[0] != self.getNumSamples():
            raise ValueError(
                "Number of data samples %d does not match model number of samples %d!"
                % (temp.shape[0], self.getNumSamples())
            )
        elif temp.shape[1] != self.getNumInputs():
            raise ValueError(
                "Number of data inputs does not match model number of inputs!"
            )
        self.inputData = temp

    def getInputData(self):
        return self.inputData

    def setOutputData(self, data):
        if data == []:
            self.outputData = []
            return
        temp = numpy.array(data, dtype=float, ndmin=2)
        if temp.shape[0] != self.getNumSamples():
            raise ValueError(
                "Number of data samples does not match model number of samples!"
            )
        elif temp.shape[1] != self.model.getNumOutputs():
            raise ValueError(
                "Number of data outputs does not match model number of outputs!"
            )
        self.outputData = temp

    def getOutputData(self):
        return self.outputData

    def setRunState(self, data):
        temp = numpy.array(data, dtype=bool)
        if temp.size != self.getNumSamples():
            raise ValueError(
                "Number of run state entries does not match model number of samples"
            )
        self.runState = temp

    def getRunState(self):
        return self.runState

    def clearRunState(self):
        data = [False] * self.getNumSamples()
        self.runState = numpy.array(data, dtype=bool)
        self.outputData = []

    def setLegendreOrder(self, num):
        self.legendreOrder = num

    def getLegendreOrder(self):
        return self.legendreOrder

    def getNumAnalyses(self):
        return len(self.analyses)

    def addAnalysis(self, analysis):
        self.analyses.append(analysis)

    def getAnalysisAtIndex(self, index):
        return self.analyses[index]

    def removeAnalysisByIndex(self, index):
        analysis = self.analyses[index]
        self.removeArchiveFolder(analysis.ID)
        del self.analyses[index]

    def archiveFile(self, fileName, folderStructure=None):
        if self.session == None:
            raise Exception(
                "SampleData object does not have a session associated with it"
            )
            return
        if folderStructure is None:
            folderStructure = []
        if isinstance(folderStructure, str):
            folderStructure = [folderStructure]
        folderStructure.insert(0, self.ID)
        self.session.archiveFile(fileName, folderStructure)

    def restoreFromArchive(self, fileName, folderStructure=None):
        if self.session == None:
            raise Exception(
                "SampleData object does not have a session associated with it"
            )
            return
        if folderStructure is None:
            folderStructure = []
        if isinstance(folderStructure, str):
            folderStructure = [folderStructure]
        folderStructure.insert(0, self.ID)
        self.session.restoreFromArchive(fileName, folderStructure)

    def removeArchiveFolder(self, folderStructure=None):
        if self.session == None:
            raise Exception(
                "SampleData object does not have a session associated with it"
            )
            return
        if folderStructure is None:
            folderStructure = []
        if isinstance(folderStructure, str):
            folderStructure = [folderStructure]
        folderStructure.insert(0, self.ID)
        self.session.removeArchiveFolder(folderStructure)

    def removeArchiveFile(self, fileName, folderStructure=None):
        if self.session == None:
            raise Exception(
                "SampleData object does not have a session associated with it"
            )
            return
        if folderStructure is None:
            folderStructure = []
        if isinstance(folderStructure, str):
            folderStructure = [folderStructure]
        folderStructure.insert(0, self.ID)
        self.session.removeArchiveFile(fileName, folderStructure)

    def existsInArchive(self, fileName, folderStructure=None):
        if self.session == None:
            raise Exception(
                "SampleData object does not have a session associated with it"
            )
            return
        if folderStructure is None:
            folderStructure = []
        if isinstance(folderStructure, str):
            folderStructure = [folderStructure]
        folderStructure.insert(0, self.ID)
        return self.session.existsInArchive(fileName, folderStructure)

    def getValidSamples(self):
        # Get indices of valid samples
        validSamples = numpy.flatnonzero(self.runState)
        return self.getSubSample(validSamples)

    def getSubSample(self, indices):
        # Create new samples
        newSamples = copy.deepcopy(self)

        indices = numpy.array(indices)
        numSamples = indices.size
        newSamples.setNumSamples(numSamples)

        # Filter data and assign to new data object
        inputs = self.inputData
        newSamples.setInputData(inputs[indices])
        outputs = self.outputData
        if not isinstance(outputs, numpy.ndarray) or outputs.shape[0] == 0:
            newSamples.setOutputData([])
        else:
            newSamples.setOutputData(outputs[indices])
        runState = self.runState
        newSamples.setRunState(runState[indices])

        return newSamples

    def deleteInputs(self, indices):
        indices = [ind for ind in indices if 0 <= ind < self.getNumInputs()]
        mask = numpy.ones(self.getNumInputs(), dtype=bool)
        mask[indices] = False
        self.model.setInputNames(
            [name for i, name in enumerate(self.getInputNames()) if i not in indices]
        )
        self.model.setInputTypes(
            [type for i, type in enumerate(self.getInputTypes()) if i not in indices]
        )
        self.model.setInputMins(self.getInputMins()[mask])
        self.model.setInputMaxs(self.getInputMaxs()[mask])
        self.model.setInputDistributions(
            [
                dist
                for i, dist in enumerate(self.getInputDistributions())
                if i not in indices
            ]
        )
        self.model.setInputDefaults(self.getInputDefaults()[mask])
        self.inputData = self.inputData[..., mask]

    def deleteOutputs(self, indices):
        indices = [ind for ind in indices if 0 <= ind < self.getNumOutputs()]
        mask = numpy.ones(self.getNumOutputs(), dtype=bool)
        mask[indices] = False
        selected = numpy.zeros(self.getNumOutputs(), dtype=bool)
        self.model.setOutputNames(
            [name for i, name in enumerate(self.getOutputNames()) if i not in indices]
        )
        selectedOutputs = self.model.getSelectedOutputs()
        selected[selectedOutputs] = True
        selected = selected[mask]
        selectedOutputs = numpy.flatnonzero(selected)
        self.model.setSelectedOutputs(selectedOutputs)
        self.outputData = self.outputData[..., mask]

    def writeToPsuade(self, filename, fixedAsVariables=False):
        outf = open(filename, "w")
        if self.getNamesIncludeNodes():
            outf.write("# NAMESHAVENODES\n")
        outf.write("PSUADE_IO (Note : inputs not true inputs if pdf ~=U)\n")
        types = self.getInputTypes()

        if fixedAsVariables:
            numInputs = self.getNumInputs()
        else:
            numInputs = types.count(Model.VARIABLE)
        outf.write(
            "%d %d %d\n" % (numInputs, self.getNumOutputs(), self.getNumSamples())
        )

        # Write out data
        hasOutputData = False
        if self.outputData is not None:
            if isinstance(self.outputData, numpy.ndarray):
                if self.outputData.size > 0:
                    hasOutputData = True
            elif self.outputData:
                if (
                    isinstance(self.outputData[0], list)
                    and len(self.outputData[0]) == 0
                ):
                    hasOutputData = False
                else:
                    hasOutputData = True
        for i in range(self.getNumSamples()):
            outf.write("%d %d\n" % (i + 1, self.runState[i]))
            for j in range(self.getNumInputs()):
                if types[j] == Model.VARIABLE or fixedAsVariables:
                    outf.write(" % .16e\n" % self.inputData[i][j])
            for j in range(self.getNumOutputs()):
                if hasOutputData and not numpy.isnan(self.outputData[i][j]):
                    outf.write(" % .16e\n" % self.outputData[i][j])
                else:
                    outf.write(" 9.9999999999999997e+34\n")

        outf.write("PSUADE_IO\n")
        outf.write("PSUADE\n")

        # Write inputs
        outf.write("INPUT\n")
        numFixed = self.getNumInputs() - numInputs
        if numFixed > 0:
            outf.write("   num_fixed %d\n" % numFixed)
        # outf.write('   dimension = %d\n' % self.getNumInputs())
        outf.write("   dimension = %d\n" % numInputs)
        names = self.getInputNames()
        mins = self.getInputMins()
        maxs = self.getInputMaxs()
        defaults = self.getInputDefaults()
        distributions = self.getInputDistributions()
        if distributions is None:
            self.setInputDistributions([Distribution.UNIFORM] * self.getNumInputs())
            distributions = self.getInputDistributions()
            self.setInputDistributions([])

        fixedIndex = 1
        variableIndex = 1
        for name, minimum, maximum, inType, dist, default in zip(
            names, mins, maxs, types, distributions, defaults
        ):
            if not fixedAsVariables and inType == Model.FIXED:
                outf.write("   fixed %d %s =  % .16e\n" % (fixedIndex, name, default))
                fixedIndex = fixedIndex + 1
            else:
                outf.write(
                    "   variable %d %s  =  % .16e  % .16e\n"
                    % (variableIndex, name, minimum, maximum)
                )
                if dist is not None:
                    distType = dist.getDistributionType()
                    distParams = dist.getParameterValues()
                    if distType != Distribution.UNIFORM:
                        outf.write(
                            "   PDF %d %c"
                            % (variableIndex, Distribution.getPsuadeName(distType))
                        )
                        if distType == Distribution.SAMPLE:
                            fileString = distParams[0]
                            import platform

                            if platform.system() == "Windows":
                                import win32api

                                fileString = win32api.GetShortPathName(fileString)
                            outf.write(" %s %d" % (fileString, distParams[1]))
                        else:
                            if distParams[0] is not None:
                                outf.write(" % .16e" % distParams[0])
                            if distParams[1] is not None:
                                outf.write(" % .16e" % distParams[1])
                        outf.write("\n")
                variableIndex = variableIndex + 1
        outf.write("END\n")

        # Write outputs
        outf.write("OUTPUT\n")
        outf.write("   dimension = %d\n" % self.getNumOutputs())
        names = self.getOutputNames()
        indices = list(range(self.getNumOutputs()))
        for i, name in zip(indices, names):
            outf.write("   variable %d %s\n" % (i + 1, name))
        outf.write("END\n")

        # Write Method
        outf.write("METHOD\n")
        if self.getSampleMethod() != None:
            outf.write(
                "   sampling = %s\n"
                % SamplingMethods.getPsuadeName(self.getSampleMethod())
            )
        outf.write("   num_samples = %d\n" % self.getNumSamples())
        outf.write("   num_replications = 1\n")
        outf.write("   num_refinements = 0\n")
        outf.write("   refinement_size = 10000000\n")
        outf.write("   reference_num_refinements = 0\n")
        outf.write("END\n")

        # Write Application
        outf.write("APPLICATION\n")
        driverString = self.getDriverName()
        if driverString is None or not os.path.exists(driverString):
            driverString = "NONE"
        else:
            import platform

            if platform.system() == "Windows":
                import win32api

                driverString = win32api.GetShortPathName(driverString)
        outf.write("   driver = %s\n" % driverString)
        driverString = self.getOptDriverName()
        if driverString != "PSUADE_LOCAL":
            if driverString is None or not os.path.exists(driverString):
                driverString = "NONE"
            else:
                import platform

                if platform.system() == "Windows":
                    import win32api

                    driverString = win32api.GetShortPathName(driverString)
        outf.write("   opt_driver = %s\n" % driverString)
        driverString = self.getEnsembleOptDriverName()
        if driverString != "PSUADE_LOCAL":
            if driverString is None or not os.path.exists(driverString):
                driverString = "NONE"
            else:
                import platform

                if platform.system() == "Windows":
                    import win32api

                    driverString = win32api.GetShortPathName(driverString)
        outf.write("   ensemble_opt_driver = %s\n" % driverString)
        driverString = self.getAuxDriverName()
        if driverString is None or not os.path.exists(driverString):
            driverString = "NONE"
        else:
            import platform

            if platform.system() == "Windows":
                import win32api

                driverString = win32api.GetShortPathName(driverString)
        outf.write("   aux_opt_driver = %s\n" % driverString)
        outf.write("   max_job_wait_time = 1000000\n")
        outf.write("   save_frequency = 1\n")
        outf.write("END\n")

        # Write Analysis
        outf.write("ANALYSIS\n")
        outf.write("   analyzer output_id  = 1\n")
        rs = self.getSampleRSType()
        if rs == None:
            rs = "MARS"
        else:
            rs = ResponseSurfaces.getPsuadeName(rs)
        outf.write("   analyzer rstype = %s\n" % rs)

        order = self.getLegendreOrder()
        if order is not None:
            outf.write("   analyzer rs_legendre_order = %d\n" % self.getLegendreOrder())
        outf.write("   analyzer threshold = 1.000000e+00\n")
        outf.write("   diagnostics 1\n")
        outf.write("END\n")

        outf.write("END\n")
        outf.close()

    def writeToCsv(
        self,
        filename,
        inputsOnly=False,
        outputsOnly=False,
        inputIndex=None,
        outputIndices=None,
    ):
        outf = open(filename, "w")

        # Write variable names

        inputNames = self.getInputNames()
        outputNames = self.getOutputNames()
        if inputIndex is not None:
            varNames = [inputNames[inputIndex]]
        elif outputIndices is not None:
            if isinstance(outputIndices, (tuple, list)):
                varNames = [outputNames[index] for index in outputIndices]
            else:
                varNames = [outputNames[outputIndices]]
        elif inputsOnly:
            varNames = inputNames
        elif outputsOnly:
            varNames = outputNames
        else:
            varNames = inputNames + outputNames
        outf.write('"%s"' % varNames[0])
        for name in varNames[1:]:
            outf.write(',"%s"' % name)
        outf.write("\n")

        # Write data
        inData = self.getInputData()
        outData = self.getOutputData()
        if inputIndex is not None:
            data = inData[:, inputIndex]
        elif outputIndices is not None:
            data = outData[:, outputIndices]
        elif inputsOnly:
            data = inData
        elif outputsOnly:
            data = outData
        else:
            data = numpy.hstack((inData, outData))
        for row in data:
            if isinstance(row, numpy.ndarray):
                outf.write("%f" % row[0])
                for item in row[1:]:
                    outf.write(",%f" % item)
            else:
                outf.write("%f" % row)
            outf.write("\n")

        outf.close()
