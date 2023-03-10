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
import abc  # abstract base class
import time


class UQAnalysis(object, metaclass=abc.ABCMeta):
    (
        PARAM_SCREEN,
        UNCERTAINTY,
        CORRELATION,
        SENSITIVITY,
        VISUALIZATION,
        RS_VALIDATION,
        RS_UNCERTAINTY,
        RS_SENSITIVITY,
        INFERENCE,
        RS_VISUALIZATION,
    ) = list(range(10))

    fullNames = (
        "Parameter Screening",
        "Uncertainty Analysis",
        "Correlation Analysis",
        "Sensitivity Analysis",
        "Visualization",
        "RS Validation",
        "RS Uncertainty Analysis",
        "RS Sensitivity Analysis",
        "Bayesian Inference",
        "RS Visualization",
    )

    codeNames = (
        "ps",
        "ua",
        "ca",
        "sa",
        "viz",
        "rsvalid",
        "rsua",
        "rssa",
        "inf",
        "rsviz",
    )

    FIRST_ORDER, SECOND_ORDER, TOTAL_ORDER = list(range(3))
    sensitivityTypes = ("First-order", "Second-order", "Total-order")

    @staticmethod
    def getTypeFullName(num):
        return UQAnalysis.fullNames[num]

    @staticmethod
    def getTypeEnumValue(name):
        if name is None:
            return None
        if name in UQAnalysis.fullNames:
            index = UQAnalysis.fullNames.index(name)
        else:
            index = UQAnalysis.codeNames.index(name)
        return index

    @staticmethod
    def getSubTypeFullName(num):
        return None

    def __init__(self, ensemble, outputs, analysisType, subType=None):
        self.ensemble = ensemble
        self.type = analysisType
        self.subType = subType
        self.ID = time.strftime("Analysis_%y%m%d%H%M%S")
        self.setOutputs(outputs)
        self.legendreOrder = 0
        self.lowerThreshold = None
        self.upperThreshold = None
        self.inputs = None
        self.description = None

    def saveDict(self):
        sd = dict()
        sd["ID"] = self.ID
        sd["type"] = self.codeNames[self.type]
        sd["subType"] = self.subType
        sd["inputs"] = self.inputs
        sd["outputs"] = self.outputs
        sd["legendreOrder"] = self.legendreOrder
        sd["description"] = self.description
        return sd

    def loadDict(self, sd):
        self.ID = sd.get("ID", "")
        self.type = UQAnalysis.getTypeEnumValue(sd.get("type", None))
        self.subType = sd.get("subType", None)
        self.inputs = sd.get("inputs", None)
        self.outputs = sd.get("outputs", None)
        self.legendreOrder = sd.get("legendreOrder", None)
        self.description = sd.get("description", None)

    def setEnsemble(self, ensemble):
        self.ensemble = ensemble

    def getEnsemble(self):
        return self.ensemble

    def getType(self):
        return (self.type, self.subType)

    def setID(self, string):
        self.ID = string

    def getID(self):
        return self.ID

    def setOutputs(self, outputs):
        if not isinstance(outputs, (list, tuple)):
            self.outputs = [outputs]
        else:
            self.outputs = list(outputs)

    def getOutputs(self):
        return self.outputs

    def setInputs(self, inputs):
        if not isinstance(inputs, (list, tuple)):
            self.inputs = [inputs]
        else:
            self.inputs = list(inputs)

    def getInputs(self):
        return self.inputs

    @abc.abstractmethod
    def analyze(self):
        pass

    @abc.abstractmethod
    def showResults(self):
        pass

    def getAdditionalInfo(self):
        return None

    def setDescription(self, text):
        self.description = text

    def getDescription(self):
        return self.description

    def archiveFile(self, fileName, folderStructure=None):
        if self.ensemble == None:
            raise Exception(
                "UQAnalysis object does not have an ensemble associated with it"
            )
            return
        if folderStructure is None:
            folderStructure = []
        if isinstance(folderStructure, str):
            folderStructure = [folderStructure]
        folderStructure.insert(0, self.ID)
        self.ensemble.archiveFile(fileName, folderStructure)

    def restoreFromArchive(self, fileName, folderStructure=None):
        if self.ensemble == None:
            raise Exception(
                "UQAnalysis object does not have an ensemble associated with it"
            )
            return
        if folderStructure is None:
            folderStructure = []
        if isinstance(folderStructure, str):
            folderStructure = [folderStructure]
        folderStructure.insert(0, self.ID)
        return self.ensemble.restoreFromArchive(fileName, folderStructure)

    def removeArchiveFolder(self, folderStructure=None):
        if self.ensemble == None:
            raise Exception(
                "UQAnalysis object does not have an ensemble associated with it"
            )
            return
        if folderStructure is None:
            folderStructure = []
        if isinstance(folderStructure, str):
            folderStructure = [folderStructure]
        folderStructure.insert(0, self.ID)
        self.ensemble.removeArchiveFolder(folderStructure)

    def removeArchiveFile(self, fileName, folderStructure=None):
        if self.ensemble == None:
            raise Exception(
                "UQAnalysis object does not have an ensemble associated with it"
            )
            return
        if folderStructure is None:
            folderStructure = []
        if isinstance(folderStructure, str):
            folderStructure = [folderStructure]
        folderStructure.insert(0, self.ID)
        self.ensemble.removeArchiveFile(fileName, folderStructure)

    def existsInArchive(self, fileName, folderStructure=None):
        if self.ensemble == None:
            raise Exception(
                "UQAnalysis object does not have an ensemble associated with it"
            )
            return
        if folderStructure is None:
            folderStructure = []
        if isinstance(folderStructure, str):
            folderStructure = [folderStructure]
        folderStructure.insert(0, self.ID)
        return self.ensemble.existsInArchive(fileName, folderStructure)
