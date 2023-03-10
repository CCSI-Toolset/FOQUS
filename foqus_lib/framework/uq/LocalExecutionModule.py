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
Includes all functionality to read data from file, maintain Psuade location,
and make local runs

Methods:
    readSampleFromPsuadeFile(string fileName, bool returnModelOnly):
        Returns a SampleData object created from the contents of a Psuade file.
        If returnModelOnly is set to True, only returns a Model object.

    readDataFromSimpleFile(string fileName):
        Returns a numpy array from a simple formatted file, that only contains
        sample values.  Each row of the array corresponds to a sample, each column
        is an input or output value for the sample.

    setPsuadePath():
        Brings up a Qt file dialog to allow user to browse to Psuade location.
        Saves Psuade location to a file.  This method only needs to be called
        once if Psuade location will never be changed.
        Note: Depending on platform, may require a QtWidgets.QApplication object
            to be instantiated.

    getPsuadePath():
        Returns location of Psuade in a string.

    genConfigFile(data, fileName):
        Creates config file used in Jim Leek's scripts for running locally.
        Arguments:
            data - A SampleData object containing the data
            fileName - Name of the config file to write

    startRun(SampleData):
        Starts the run then returns.
        Note: Must use getNumUnfinishedRunSamples() or isRunFinished() to check
        if the run is done.  Use getRunData() to get the results.

    getNumUnfinishedRunSamples():
        Returns the number of samples that have yet to run as an integer.
        Returns -1 if called without starting a run previously, or some other error.

    isRunFinished():
        Returns whether run is complete as a bool.

    getRunData():
        Returns the results of the run as a SampleData object

"""

import sys
import os
import subprocess
import glob
import platform
import numpy
import copy
import re
import csv

try:
    from PyQt5 import QtCore, QtWidgets

    usePyside = True
except:
    usePyside = False

from .Model import Model
from .SampleData import SampleData
from .Distribution import Distribution
from .ResponseSurfaces import ResponseSurfaces
from .SamplingMethods import SamplingMethods
from .Common import Common

from turbine.commands import turbine_psuade_session_script
from turbine.commands import _open_config


class LocalExecutionModule(object):

    dname = os.getcwd() + os.path.sep + "LocalExecutionModule_files"

    runStarted = False
    runComplete = False
    psuadeFile = None
    configFile = None
    runType = None

    process = None
    stdoutF = None
    stderrF = None
    numSamples = 0

    session = None
    psuadeVersion = (
        "1.7.6"  # Change this to change the version of psuade that is required
    )

    @staticmethod
    def readSampleFromPsuadeFile(fileName, returnModelOnly=False):
        f = open(fileName, "r")
        lines = f.readlines()
        f.close()

        model = Model()
        path, fname = os.path.split(fileName)  # exclude path from file name
        model.setName(fname)

        namesIncludeNodes = False
        hasSampleData = False
        readData = False
        readInputs = False
        readOutputs = False
        numInputs = None
        driverName = None
        optDriverName = None
        auxDriverName = None
        sampleType = None
        legendreOrder = None
        sampleMethod = None
        # WHY there are a few pylint errors related to inputData, outputData, and runState
        # for operations that assume these 3 variables to be iterables
        # this could be addressed without disabling the checks by setting them to empty lists
        # it's also not clear if all the branches in this function work correctly
        inputData = None
        outputData = None
        runState = None

        inputNames = []
        outputNames = []
        inputTypes = []
        inputMins = []
        inputMaxs = []
        inputDefaults = []
        inputDists = []
        inputDistParam1s = []
        inputDistParam2s = []

        for line in lines:
            if line[0] == "#" and "NAMESHAVENODES" in line:
                namesIncludeNodes = True
            if len(line) > 0 and line[0] != "#":  # Not comment
                if line.startswith("PSUADE_IO"):
                    readData = not readData
                    hasSampleData = True
                elif line.startswith("INPUT"):
                    readInputs = True
                elif line.startswith("OUTPUT"):
                    readOutputs = True
                elif line.startswith("END"):
                    if readInputs:
                        readInputs = False
                    elif readOutputs:
                        readOutputs = False
                elif readData:  # Read samples
                    if numInputs is None:  # Have not read number of inputs
                        nums = line.split()
                        numInputs = int(nums[0])
                        numOutputs = int(nums[1])
                        numSamples = int(nums[2])
                        runState = [False] * numSamples
                        inputData = [0] * numSamples
                        outputData = [0] * numSamples
                        readSampleData = False
                    elif not readSampleData:  # Sample number and run state
                        nums = line.split()
                        sampleNum = int(nums[0]) - 1
                        # runState at this point should still be None, so this would cause a runtime error
                        # TODO pylint: disable=unsupported-assignment-operation
                        runState[sampleNum] = bool(int(nums[1]))
                        # TODO pylint: enable=unsupported-assignment-operation
                        readSampleData = True
                        numValuesRead = 0
                        sampleInputs = [0] * numInputs
                        sampleOutputs = [0] * numOutputs
                    else:
                        if numValuesRead < numInputs:  # Input value
                            if line.strip() in [
                                "9.9999999999999997e+34",
                                "9.9999999999999997e+034",
                            ]:
                                line = "nan"
                            sampleInputs[numValuesRead] = float(line)
                            numValuesRead = numValuesRead + 1
                        else:  # Output value
                            if line.strip() in [
                                "9.9999999999999997e+34",
                                "9.9999999999999997e+034",
                            ]:
                                line = "nan"
                            sampleOutputs[numValuesRead - numInputs] = float(line)
                            numValuesRead = numValuesRead + 1
                            if numValuesRead - numInputs == numOutputs:
                                # pylint: disable=unsupported-assignment-operation
                                inputData[sampleNum] = sampleInputs
                                outputData[sampleNum] = sampleOutputs
                                # pylint: enable=unsupported-assignment-operation
                                readSampleData = False
                elif readInputs:  # Read inputs
                    stripped = line.strip()
                    values = stripped.split()
                    if values[0] == "variable":  # Variable name min max
                        inputNames = inputNames + [values[2]]
                        inputTypes = inputTypes + [Model.VARIABLE]
                        inputMins = inputMins + [float(values[4])]
                        inputMaxs = inputMaxs + [float(values[5])]
                        inputDefaults = inputDefaults + [
                            (float(values[4]) + float(values[5])) / 2
                        ]
                        inputDists = inputDists + ["U"]
                        inputDistParam1s = inputDistParam1s + [None]
                        inputDistParam2s = inputDistParam2s + [None]
                    elif values[0] == "fixed":  # Fixed variable
                        inputNames = inputNames + [values[2]]
                        inputTypes = inputTypes + [Model.FIXED]
                        fixedVal = float(values[4])
                        inputMins = inputMins + [fixedVal]
                        inputMaxs = inputMaxs + [fixedVal]
                        inputDefaults = inputDefaults + [fixedVal]
                        inputDists = inputDists + ["U"]
                        inputDistParam1s = inputDistParam1s + [None]
                        inputDistParam2s = inputDistParam2s + [None]
                        # Insert input values
                        if hasSampleData:
                            for i in range(len(inputData)):
                                # pylint: disable=unsubscriptable-object
                                inputRow = inputData[i]
                                inputRow.insert(len(inputNames) - 1, fixedVal)
                                # pylint: disable=unsupported-assignment-operation
                                inputData[i] = inputRow
                    elif values[0] == "PDF":  # Distribution
                        index = int(values[1]) - 1
                        inputDists[index] = values[2]
                        if len(values) > 3:
                            if values[2] == Distribution.getPsuadeName(
                                Distribution.SAMPLE
                            ):
                                inputDistParam1s[index] = values[3]
                            else:
                                inputDistParam1s[index] = float(values[3])
                            if len(values) > 4:
                                inputDistParam2s[index] = float(values[4])

                elif readOutputs:  # Read outputs
                    stripped = line.strip()  # Variable name
                    if stripped.startswith("variable"):
                        values = stripped.split()
                        outputNames = outputNames + [values[2]]
                else:
                    stripped = line.strip()
                    values = stripped.split()
                    if values[0] == "sampling":  # Sampling method
                        sampleMethod = values[2]
                    elif values[0] == "driver":  # Driver
                        if values[2] == "NONE":
                            values[2] = None
                        driverName = values[2]
                        if (
                            values[2] is not None
                            and values[2] != "PSUADE_LOCAL"
                            and not os.path.exists(driverName)
                        ):
                            # Check if driver exists in same directory as this file
                            if os.path.exists(os.path.join(path, driverName)):
                                driverName = os.path.join(path, driverName)
                            else:  # Don't set the name because the file does not exist
                                driverName = None
                    elif values[0] == "opt_driver":  # Optimization driver
                        if values[2] == "NONE":
                            values[2] = None
                        optDriverName = values[2]
                        if (
                            values[2] is not None
                            and values[2] != "PSUADE_LOCAL"
                            and not os.path.exists(optDriverName)
                        ):
                            # Check if driver exists in same directory as this file
                            if os.path.exists(os.path.join(path, optDriverName)):
                                optDriverName = os.path.join(path, optDriverName)
                            else:  # Don't set the name because the file does not exist
                                optDriverName = None
                    elif values[0] == "aux_opt_driver":  # Batch simulation driver
                        if values[2] == "NONE":
                            values[2] = None
                        auxDriverName = values[2]
                        if values[2] is not None and not os.path.exists(auxDriverName):
                            # Check if driver exists in same directory as this file
                            if os.path.exists(os.path.join(path, auxDriverName)):
                                auxDriverName = os.path.join(path, auxDriverName)
                            else:  # Don't set the name because the file does not exist
                                auxDriverName = None
                    elif values[0] == "num_samples":  # Number of samples
                        numSamples = int(values[2])
                    elif values[0] == "analyzer":  # Analysis values
                        if values[1] == "rstype":
                            sampleType = values[3]
                            sampleType = ResponseSurfaces.getEnumValue(sampleType)
                        elif values[1] == "rs_legendre_order":
                            legendreOrder = int(values[3])

        model.setInputNames(inputNames)
        model.setOutputNames(outputNames)
        model.setNamesIncludeNodes(namesIncludeNodes)
        model.setInputTypes(inputTypes)
        model.setInputMins(inputMins)
        model.setInputMaxs(inputMaxs)
        model.setInputDefaults(inputDefaults)
        model.setSelectedOutputs(list(range(len(outputNames))))
        model.setDriverName(driverName)
        model.setOptDriverName(optDriverName)
        model.setAuxDriverName(auxDriverName)
        model.setRunType(Model.LOCAL)

        if returnModelOnly:
            return model

        data = SampleData(model)
        data.setFromFile(True)
        data.setNumSamples(numSamples)
        if sampleMethod is None:
            data.setSampleMethod(SamplingMethods.MC)
        else:
            data.setSampleMethod(sampleMethod)
        data.setInputDistributions(inputDists, inputDistParam1s, inputDistParam2s)
        data.setSampleRSType(sampleType)
        data.setLegendreOrder(legendreOrder)
        if inputData:
            data.setInputData(inputData)
        if outputData:
            data.setOutputData(outputData)
        if runState:
            data.setRunState(runState)
        return data

    @staticmethod
    def readDataFromCsvFile(fileName, askForNumInputs=True):
        def is_number(s):
            try:
                float(s)
                return True
            except ValueError:
                return False

        with open(fileName, "rt") as csvfile:
            # Detect dialect of csv file
            dialect = csv.Sniffer().sniff(csvfile.readline())
            csvfile.seek(0)

            # Read csv file
            reader = csv.reader(csvfile, dialect)
            headers = next(reader)
            try:
                list(map(float, headers))
                headers = [""] * len(headers)
                csvfile.seek(0)
            except:  # Headers exist
                pass

            numInputs = None
            if askForNumInputs:
                # TO DO: Cleaning PySide stuff
                if not usePyside or QtWidgets.QApplication.instance() is None:
                    numInputs = int(
                        input(
                            "How many of the columns are inputs? \nInputs must be on the left."
                        )
                    )
                else:
                    numInputs, ok = QtWidgets.QInputDialog.getInt(
                        None,
                        "Number of inputs",
                        "How many of the columns are inputs? \n"
                        "Inputs must be on the left.",
                        value=len(headers),
                        min=1,
                        max=len(headers),
                    )
                    if not ok:
                        return None

            inputVals = []
            outputVals = []
            runState = []
            for row in reader:
                while row[-1] == "":
                    row.pop()
                row = [float(v) if is_number(v) else "nan" for v in row]
                if len(row) < len(headers):
                    row.append("nan")

                if not numInputs and not askForNumInputs:
                    numInputs = len(row)
                inputVals.append(row[:numInputs])
                outputVals.append(row[numInputs:])
                if len(headers) > len(row):
                    outputVals += [float("nan")] * (len(headers) - len(row))
                    outputVals.append(row)
                    runState.append(0)
                else:
                    runState.append(1)

        inputArray = numpy.array(inputVals, dtype=float, ndmin=2)
        outputArray = numpy.array(outputVals, dtype=float, ndmin=2)
        return (
            inputArray,
            outputArray,
            headers[:numInputs],
            headers[numInputs:],
            runState,
        )

    @staticmethod
    def readSampleFromCsvFile(fileName, askForNumInputs=True):
        (
            inputVals,
            outputVals,
            inputNames,
            outputNames,
            runState,
        ) = LocalExecutionModule.readDataFromCsvFile(fileName, askForNumInputs)
        numInputs = inputVals.shape[1]
        numOutputs = outputVals.shape[1]

        # Setup model
        model = Model()
        _path, fname = os.path.split(fileName)  # exclude path from file name
        model.setName(fname)
        model.setInputNames(inputNames)
        model.setOutputNames(outputNames)
        model.setInputTypes([Model.VARIABLE] * numInputs)
        mins = list(inputVals[0])
        for rowVals in inputVals[1:]:
            for col in range(numInputs):
                if rowVals[col] < mins[col]:
                    mins[col] = rowVals[col]
        model.setInputMins(mins)
        maxs = list(inputVals[0])
        for rowVals in inputVals[1:]:
            for col in range(numInputs):
                if rowVals[col] > maxs[col]:
                    maxs[col] = rowVals[col]
        model.setInputMaxs(maxs)
        model.setInputDefaults([(min + max) / 2 for min, max in zip(mins, maxs)])
        model.setSelectedOutputs(list(range(numOutputs)))
        model.setRunType(Model.LOCAL)

        data = SampleData(model)
        data.setFromFile(True)
        data.setNumSamples(len(inputVals))
        data.setSampleMethod(SamplingMethods.MC)
        data.setInputDistributions(
            ["U"] * numInputs, [None] * numInputs, [None] * numInputs
        )
        data.setInputData(inputVals)
        if outputVals.size > 0:
            data.setOutputData(outputVals)
        data.setRunState(runState)
        return data

    @staticmethod
    def readDataFromSimpleFile(fileName, hasColumnNumbers=True):

        f = open(fileName, "r")
        lines = f.readlines()
        f.close()

        # remove empty lines
        lines = [line for line in lines if len(line.strip()) > 0]

        # ignore text preceded by '#'
        c = "#"
        lines = [line.strip().split(c)[0] for line in lines if not line.startswith(c)]

        # delete lines preceded by 'PSUADE_BEGIN' and 'PSUADE_END'
        lines = [
            line
            for line in lines
            if not line.startswith(("PSUADE_BEGIN", "PSUADE_END"))
        ]
        nlines = len(lines)

        # process header
        k = 0
        header = lines[k]
        nums = header.split()
        numSamples = int(nums[0])
        numInputs = int(nums[1])
        numOutputs = 0
        if len(nums) == 3:
            numOutputs = int(nums[2])

        # process samples
        data = [None] * numSamples
        for i in range(nlines - k - 1):
            line = lines[i + k + 1]
            nums = line.split()
            data[i] = [float(x) for x in nums]

        # split samples
        data = numpy.array(data)
        if hasColumnNumbers:
            inputData = data[:, 1 : numInputs + 1]
        else:
            inputData = data[:, :numInputs]
        inputArray = numpy.array(inputData, dtype=float, ndmin=2)
        outputArray = None
        if numOutputs:
            if hasColumnNumbers:
                outputData = data[:, numInputs + 1 :]
            else:
                outputData = data[:, numInputs:]
            outputArray = numpy.array(outputData, dtype=float, ndmin=2)

        return inputArray, outputArray, numInputs, numOutputs

    @staticmethod
    def writeSimpleFile(fileName, inputData, outputData=None, rowLabels=True):
        if isinstance(inputData, numpy.ndarray):
            inputData = inputData.tolist()
        numSamples = len(inputData)
        numInputs = len(inputData[0])
        numOutputs = 0
        if outputData:
            if isinstance(inputData, numpy.ndarray):
                outputData = outputData.tolist()
            numOutputs = len(outputData[0])
        else:
            outputData = [[] for i in range(numSamples)]

        f = open(fileName, "w")
        f.write(" ".join(map(str, [numSamples, numInputs, numOutputs])))
        f.write("\n")
        for i, (inRow, outRow) in enumerate(zip(inputData, outputData), 1):
            if rowLabels:
                f.write(" ".join(map(str, [i] + inRow + outRow)))
                f.write("\n")
            else:
                f.write(" ".join(map(str, inRow + outRow)))
                f.write("\n")

        f.close()

    @staticmethod
    def readMCMCFile(fileName):

        f = open(fileName, "r")
        lines = f.readlines()
        f.close()

        # remove empty lines
        lines = [line for line in lines if len(line.strip()) > 0]

        # ignore text preceded by '#'
        c = "#"
        lines = [line.strip().split(c)[0] for line in lines if not line.startswith(c)]

        # delete lines preceded by 'PSUADE_BEGIN' and 'PSUADE_END'
        lines = [
            line
            for line in lines
            if not line.startswith(("PSUADE_BEGIN", "PSUADE_END"))
        ]
        nlines = len(lines)

        # process header
        k = 0
        header = lines[k]
        nums = header.split()
        numExps = int(nums[0])
        _numOutputs = int(nums[1])
        numDesign = int(nums[2])
        designVariables = [int(num) for num in nums[3:]]
        # Ignore the rest which are the numbers for which inputs are design parameters

        # process samples
        data = [None] * numExps
        for i in range(nlines - k - 1):
            line = lines[i + k + 1]
            nums = line.split()
            data[i] = [float(x) for x in nums]

        # split samples
        data = numpy.array(data)
        designData = data[:, 1 : numDesign + 1]
        designArray = numpy.array(designData, dtype=float, ndmin=2)
        outputData = data[:, numDesign + 1 :]
        outputArray = numpy.array(outputData, dtype=float, ndmin=2)

        return designVariables, designArray, outputArray

    @staticmethod
    def saveMCMCFile(fname, numOutputs, numDesign, designIDs, data):
        f = open(fname, "w")
        f.write("%d %d %d" % (len(data), numOutputs, numDesign))
        for ID in designIDs:
            f.write(" %d" % ID)
        f.write("\n")

        for i, row in enumerate(data):
            f.write("%d" % (i + 1))
            for value in row:
                f.write(" %g" % value)
            f.write("\n")
        f.close()

    @staticmethod
    def setPsuadePath(forceDialog=False):
        # Returns empty string if cancelled
        if platform.system() == "Windows":
            # default location for psuade
            psuadeLoc = (
                "C:/Program Files (x86)/psuade_project %s/bin/psuade.exe"
                % LocalExecutionModule.psuadeVersion
            )
            # on Windows, if psuade is not at its default location, prompt user
            if not os.path.exists(psuadeLoc) or forceDialog:
                if not forceDialog:
                    msgBox = QtWidgets.QMessageBox()
                    msgBox.setText(
                        "Location of PSUADE has not been set! Browse to its location on the next screen."
                    )
                    msgBox.exec_()
                location = ""
                if os.path.exists(psuadeLoc):
                    location = psuadeLoc
                psuadeLoc, _filterName = QtWidgets.QFileDialog.getOpenFileName(
                    None, "Location of Psuade", location, "Executable File (psuade.exe)"
                )
            while len(psuadeLoc) > 0:
                compatible = LocalExecutionModule.getPsuadeExeCompatibility(psuadeLoc)
                if not compatible:
                    msgBox = QtWidgets.QMessageBox()
                    msgBox.setText(
                        "PSUADE version must be %s or later! Browse to its location on the next screen."
                        % LocalExecutionModule.psuadeVersion
                    )
                    msgBox.exec_()
                    psuadeLoc, _filterName = QtWidgets.QFileDialog.getOpenFileName(
                        None,
                        "Location of Psuade",
                        psuadeLoc,
                        "Executable File (psuade.exe)",
                    )
                else:
                    _psuadeFile = LocalExecutionModule.writePsuadePath(psuadeLoc)
                    if LocalExecutionModule.session is not None:
                        LocalExecutionModule.session.foqusSettings.psuade_path = (
                            psuadeLoc
                        )
                        LocalExecutionModule.session.foqusSettings.save()
                        LocalExecutionModule.session.foqusSettings.load()
                    break
        else:
            # on all other platforms, check existence of user-defined PSUADEPATH
            if not forceDialog:
                msgBox = QtWidgets.QMessageBox()
                msgBox.setText(
                    "Location of PSUADE has not been set! Browse to its location on the next screen."
                )
                msgBox.exec_()

            fileDlg = QtWidgets.QFileDialog(caption="Location of Psuade")
            fileDlg.setFileMode(QtWidgets.QFileDialog.ExistingFile)
            proxyModel = LocalExecutionModule.executableFilter()
            fileDlg.setProxyModel(proxyModel)
            if fileDlg.exec_():
                psuadeLoc = fileDlg.selectedFiles()
                if isinstance(psuadeLoc, list):
                    psuadeLoc = psuadeLoc[0]
            else:
                psuadeLoc = ""
            if len(psuadeLoc) > 0:
                _psuadeFile = LocalExecutionModule.writePsuadePath(psuadeLoc)
                if LocalExecutionModule.session is not None:
                    LocalExecutionModule.session.foqusSettings.psuade_path = psuadeLoc
                    LocalExecutionModule.session.foqusSettings.save()
                    LocalExecutionModule.session.foqusSettings.load()
        return psuadeLoc

    if usePyside:

        class executableFilter(QtCore.QSortFilterProxyModel):
            def filterAcceptsRow(self, sourceRow, sourceParent):
                index = self.sourceModel().index(sourceRow, 0, sourceParent)
                if self.sourceModel().isDir(index):
                    return True
                if "psuade" not in self.sourceModel().fileName(index).lower():
                    return False
                fileInfo = self.sourceModel().fileInfo(index)
                return fileInfo.isExecutable() | fileInfo.isSymLink()

    @staticmethod
    def writePsuadePath(psuadeLoc):
        psuadeFile = os.getcwd() + os.path.sep + "PSUADEPATH"
        f = open(psuadeFile, "w")
        f.write("%s" % psuadeLoc)
        f.close()
        return psuadeFile

    @staticmethod
    def getPsuadePath(showErrorIfNotFound=True):
        fileName = os.getcwd() + os.path.sep + "PSUADEPATH"
        psuadeLoc = None
        if (
            LocalExecutionModule.session is None
            or len(LocalExecutionModule.session.foqusSettings.psuade_path) == 0
        ) and not os.path.exists(fileName):
            if not usePyside or QtWidgets.QApplication.instance() is None:
                if showErrorIfNotFound:
                    raise IOError(
                        "Location of PSUADE has not been set! "
                        + "Please put the path into the file %s" % fileName
                    )
            else:
                if showErrorIfNotFound:
                    location = LocalExecutionModule.setPsuadePath()
                    if len(location) > 0:
                        psuadeLoc = location
        else:
            if LocalExecutionModule.session:
                location = LocalExecutionModule.session.foqusSettings.psuade_path
            else:
                f = open(fileName, "r")
                location = f.readline().rstrip()
                f.close()
            if not os.path.exists(location):
                if not usePyside or QtWidgets.QApplication.instance() is None:
                    if showErrorIfNotFound:
                        raise IOError(
                            "Location of PSUADE incorrect! "
                            + "Please put the correct path into the file %s" % fileName
                        )
                else:
                    if showErrorIfNotFound:
                        location = LocalExecutionModule.setPsuadePath()
                        if len(location) > 0:
                            psuadeLoc = location
            else:
                compatible = LocalExecutionModule.getPsuadeExeCompatibility(location)
                if not compatible:
                    if not usePyside or QtWidgets.QApplication.instance() is None:
                        if showErrorIfNotFound:
                            raise IOError(
                                "Version of PSUADE must be %s or higher!\nPlease put the correct path into "
                                "the file %s"
                                % (LocalExecutionModule.psuadeVersion, fileName)
                            )
                    else:
                        if showErrorIfNotFound:
                            location = LocalExecutionModule.setPsuadePath()
                            if len(location) > 0:
                                psuadeLoc = location
                else:
                    psuadeLoc = location

        if psuadeLoc is None:
            if usePyside and showErrorIfNotFound:
                msgBox = QtWidgets.QMessageBox()
                msgBox.setText(
                    "Location of PSUADE has not been set! You will need to set it to continue."
                )
                msgBox.exec_()
            else:
                raise IOError(
                    "Location of PSUADE has not been set! You will need to set it to continue.\nPlease put "
                    "the correct path into the file %s" % fileName
                )
            return None

        if platform.system() == "Windows":
            import win32api

            psuadeLoc = win32api.GetShortPathName(psuadeLoc)
        return psuadeLoc.rstrip()

    @staticmethod
    def getPsuadeExeCompatibility(psuadePath):
        # Check psuade version is 1.7.4 or later
        if platform.system() == "Windows":
            import win32api

            psuadePath = win32api.GetShortPathName(psuadePath)

        p = subprocess.Popen(
            psuadePath + " --info",
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
        out, error = p.communicate()

        if error:
            print(error)
            return False

        lines = out.splitlines()
        compatible = False
        for line in lines:
            if "PSUADE version" in line.decode("utf-8"):
                words = line.split()
                versionNum = words[-1]
                nums = versionNum.decode("utf-8").split(".")
                reqds = LocalExecutionModule.psuadeVersion.split(".")
                lastEqual = False
                for i, (num, reqd) in enumerate(zip(nums, reqds)):
                    lastEqual = False
                    num = int(re.search("\d+", num).group())
                    reqd = int(reqd)
                    if num < reqd:
                        break
                    elif num > reqd:
                        compatible = True
                        break
                    else:
                        lastEqual = True
                if i == min([len(nums), len(reqds)]) - 1 and lastEqual:
                    compatible = True
                    break

        return compatible

    @staticmethod
    def getPsuadeInstalledModules():

        libs = ["MARS", "TPROS", "SVM", "METIS"]
        foundLibs = dict()
        for lib in libs:
            foundLibs[lib] = False

        # psuadePath = LocalExecutionModule.getPsuadePath(False)
        psuadePath = LocalExecutionModule.getPsuadePath()
        if psuadePath is None:
            # return foundLibs
            raise Exception("PSUADE path not set!")

        p = subprocess.Popen(
            psuadePath + " --info",
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
        # process error
        out, error = p.communicate()
        if error:
            Common.showError(error, out)
            return foundLibs

        # parse results
        lines = out.splitlines()
        installedString = "installed... true"
        if len(lines) >= 2:
            for line in lines:  # skip first line with version info
                for lib in libs:
                    if (lib in line.decode("utf-8")) and (
                        installedString in line.decode("utf-8")
                    ):
                        foundLibs[lib] = True
                        break

        return foundLibs

    @staticmethod
    def genConfigFile(data, fileName):
        f = open(fileName, "w")
        f.write("[Logging]\n")
        username = "testing"
        password = "hello"
        f.write("[Consumer]\n")
        f.write("[Session]\n")
        f.write("[Job]\n")
        f.write("[Simulation]\n")
        f.write("name=Solid_Absorber_v1\n")
        f.write("[Application]\n")

        f.write("[PSUADE]\n")
        f.write("PSUADE=%s\n" % LocalExecutionModule.getPsuadePath())

        f.write("[Authentication]\n")
        f.write("username=%s\n" % username)
        f.write("password=%s\n" % password)

        f.write("[Inputs]\n")
        inputNames = data.getInputNames()
        for i in range(data.getNumInputs()):
            f.write("%s=%d\n" % (inputNames[i], i))

        f.write("[Outputs]\n")
        # richmass = '';
        # richco2 = '';
        # leanmass = '';
        # leanco2 = '';
        # captureFraction = false;

        outputNames = data.getOutputNames()
        for i in range(data.getNumOutputs()):
            f.write("var%d=%s\n" % (i + 1, outputNames[i]))

        f.write("[OutputsOrder]\n")
        for i in range(data.getNumOutputs()):
            f.write("%d=var%d\n" % (i, i + 1))

        f.close()

    @staticmethod
    def writeSelectedVars(data, filename):
        outf = open(filename, "w")
        outf.write("PSUADE\n")

        # Write inputs
        outf.write("INPUT\n")
        outf.write("   dimension = %d\n" % data.getNumInputs())
        names = data.getInputNames()
        mins = data.getInputMins()
        maxs = data.getInputMaxs()
        indices = list(range(data.getNumInputs()))
        for i, name, minimum, maximum in zip(indices, names, mins, maxs):
            outf.write("   variable %d %s = %e %e\n" % (i + 1, name, minimum, maximum))
        distributions = data.getInputDistributions()
        for i, dist in zip(indices, distributions):
            distType = dist.getDistributionType()
            distParams = dist.getParameterValues()
            if distType != Distribution.UNIFORM:
                outf.write(
                    "   PDF %d %c %e"
                    % (i + 1, Distribution.getPsuadeName(distType), distParams[0])
                )
                if distParams[1] is not None:
                    outf.write(" %e" % distParams[1])
                outf.write("\n")
        outf.write("END\n")

        # Write outputs
        outf.write("OUTPUT\n")
        outf.write("   dimension = %d\n" % data.getNumOutputs())
        names = data.getOutputNames()
        indices = list(range(data.getNumOutputs()))
        for i, name in zip(indices, names):
            outf.write("   variable %d %s\n" % (i + 1, name))
        outf.write("END\n")

        outf.write("END\n")

    @staticmethod
    def startRun(data):
        LocalExecutionModule.runType = Model.LOCAL
        LocalExecutionModule.runComplete = False
        LocalExecutionModule.runStarted = False
        LocalExecutionModule.numSamples = data.getNumSamples()

        # Remove old files
        psuadeDataFile = os.getcwd() + os.path.sep + "psuadeData"
        if os.path.exists(psuadeDataFile):
            os.remove(psuadeDataFile)
        psuadeOutFile = os.getcwd() + os.path.sep + "psuadeOut"
        if os.path.exists(psuadeOutFile):
            os.remove(psuadeOutFile)
        psuadeAppsFiles = os.getcwd() + os.path.sep + "psuadeApps_ct.*"
        for f in glob.glob(psuadeAppsFiles):
            os.remove(f)

        # Config file
        LocalExecutionModule.configFile = os.getcwd() + os.path.sep + "config.txt"
        if os.path.exists(LocalExecutionModule.configFile):
            os.remove(LocalExecutionModule.configFile)
        LocalExecutionModule.genConfigFile(data, LocalExecutionModule.configFile)

        # Psuade file
        LocalExecutionModule.psuadeFile = os.getcwd() + os.path.sep + "psuadeDriver"
        data.writeToPsuade(LocalExecutionModule.psuadeFile)

        # selectedVars file
        selectedVarsFile = os.getcwd() + os.path.sep + "selectedVars"
        LocalExecutionModule.writeSelectedVars(data, selectedVarsFile)

        # Start run
        # print 'Starting run'
        LocalExecutionModule.stdoutF = open("stdout", "w")
        LocalExecutionModule.stderrF = open("stderr", "w")
        LocalExecutionModule.runStarted = True

        config = _open_config(LocalExecutionModule.configFile)
        # print turbine_psuade_session_script.__file__
        turbine_psuade_session_script.local_launch(
            config, LocalExecutionModule.psuadeFile
        )

    @staticmethod
    def getNumUnfinishedRunSamples():
        if not LocalExecutionModule.runStarted:
            return -1
        elif LocalExecutionModule.runComplete:
            return 0

        if not os.path.exists("psuadePath"):
            return -1

        if LocalExecutionModule.runType == Model.LOCAL:
            print("getting config")
            config = _open_config(LocalExecutionModule.configFile)
        else:
            config = None
        numUnfinished = turbine_psuade_session_script.local_unfinished(
            config, "psuadeData"
        )
        if numUnfinished == 0:
            LocalExecutionModule.runComplete = True
            LocalExecutionModule.stdoutF.close()
            LocalExecutionModule.stderrF.close()

            # Clean up files
            psuadeAppsFiles = os.getcwd() + os.path.sep + "psuadeApps_ct.*"
            for f in glob.glob(psuadeAppsFiles):
                os.remove(f)

            # Check if process is stopped with errors
            # elif LocalExecutionModule.process.state() != QtCore.QProcess.Running:
            # elif LocalExecutionModule.process.poll() is not None:  # Process done
            # LocalExecutionModule.stdoutF.close()
            # LocalExecutionModule.stderrF.close()

            # Clean up files
            psuadeAppsFiles = os.getcwd() + os.path.sep + "psuadeApps_ct.*"
            for f in glob.glob(psuadeAppsFiles):
                os.remove(f)

            # Open file and assert error from psuade
            # errorOutput = LocalExecutionModule.process.readAllStandardError()
            # print errorOutput
            # standardOutput = LocalExecutionModule.process.readAllStandardOutput()
            # print standardOutput
            # outF = open(os.getcwd() + '\\stdout')
            # lines = outF.readlines()
            # raise RuntimeError(lines)

        return numUnfinished

    @staticmethod
    def isRunFinished():
        if not LocalExecutionModule.runStarted:
            # print 'Run has not started!'
            return False
        elif LocalExecutionModule.runComplete:  # Already been determined done
            return True

        # runComplete = False does not necessarily mean run is still going.
        # Need to check.

        # WHY there is no LocalExecutionModule.getNumFinishedRuns() function,
        # so this looks like a legitimate cause for runtime errors
        # the method isRunFinished() itself seems to have no references,
        # which suggests that this piece of code is never executed
        LocalExecutionModule.getNumFinishedRuns()  # TODO pylint: disable=no-member  # Update the runComplete bool
        return LocalExecutionModule.runComplete

    @staticmethod
    def getRunData():
        if not LocalExecutionModule.runStarted:
            # print 'Run has not started!'
            return None
        psuadeOutFile = os.getcwd() + os.path.sep + "psuadeOutFile"

        import shutil

        shutil.copyfile("psuadeData", psuadeOutFile)

        data = LocalExecutionModule.readSampleFromPsuadeFile(psuadeOutFile)
        return data

    if usePyside:

        @staticmethod
        def startEmulatorRun(data):
            LocalExecutionModule.runType = Model.EMULATOR
            textDialog = Common.textDialog()
            LocalExecutionModule.runThread = emulatorRunThread(data, textDialog)
            LocalExecutionModule.runThread.start()

        @staticmethod
        def getEmulatorRunData():
            return LocalExecutionModule.runThread.returnData

        @staticmethod
        def getEmulatorOutputsFinished():
            return LocalExecutionModule.runThread.numOutputsFinished


if usePyside:

    class emulatorRunThread(QtCore.QThread):
        def __init__(self, data, textDialog, parent=None):
            QtCore.QThread.__init__(self)
            self.data = data
            self.parent = parent
            self.returnData = copy.deepcopy(data)
            self.numOutputsFinished = 0
            self.textDialog = textDialog

        class Communicate(QtCore.QObject):
            textDialogShowSignal = QtCore.pyqtSignal()
            textDialogCloseSignal = QtCore.pyqtSignal()
            textDialogInsertSignal = QtCore.pyqtSignal(str)
            textDialogEnsureVisibleSignal = QtCore.pyqtSignal()

        def run(self):
            LocalExecutionModule.runComplete = False
            LocalExecutionModule.runStarted = False
            LocalExecutionModule.numSamples = self.data.getNumSamples()

            # Remove old files
            psuadeDataFile = os.getcwd() + os.path.sep + "psuadeData"
            if os.path.exists(psuadeDataFile):
                os.remove(psuadeDataFile)
            psuadeOutFile = os.getcwd() + os.path.sep + "psuadeOut"
            if os.path.exists(psuadeOutFile):
                os.remove(psuadeOutFile)
            psuadeAppsFiles = os.getcwd() + os.path.sep + "psuadeApps_ct.*"
            for f in glob.glob(psuadeAppsFiles):
                os.remove(f)

            # Run
            outputStatus = self.data.getEmulatorOutputStatus()
            # print outputStatus
            emulatorFileName = "emulatorData"
            self.data.writeToPsuade(emulatorFileName)
            from .RSAnalyzer import (
                RSAnalyzer,
            )  # importing at top creates circular import

            LocalExecutionModule.runStarted = True
            Common.initFolder(RSAnalyzer.dname)
            c = self.Communicate()
            c.textDialogShowSignal.connect(self.textDialog.show)
            c.textDialogCloseSignal.connect(self.textDialog.close)
            c.textDialogInsertSignal.connect(self.textDialog.textedit.insertPlainText)
            c.textDialogEnsureVisibleSignal.connect(
                self.textDialog.textedit.ensureCursorVisible
            )
            for i, status in enumerate(outputStatus):
                if status == Model.NEED_TO_CALCULATE:
                    import time

                    _start = time.process_time()
                    psfile, _rs, _legOrder = RSAnalyzer.emulate(
                        self.data.getEmulatorTrainingFile(),
                        emulatorFileName,
                        i + 1,
                        textDialog=self.textDialog,
                        dialogShowSignal=c.textDialogShowSignal,
                        dialogCloseSignal=c.textDialogCloseSignal,
                        textInsertSignal=c.textDialogInsertSignal,
                        ensureVisibleSignal=c.textDialogEnsureVisibleSignal,
                    )

                    runData = LocalExecutionModule.readSampleFromPsuadeFile(psfile)
                    outputData = runData.getOutputData()
                    originalOutputData = self.returnData.getOutputData()
                    if (
                        not isinstance(originalOutputData, numpy.ndarray)
                        and not originalOutputData
                    ):
                        outputRow = [
                            9.9999999999999997e34
                        ] * self.returnData.getNumOutputs()
                        originalOutputData = numpy.array(
                            [outputRow] * self.returnData.getNumSamples()
                        )
                    originalOutputData[:, i] = numpy.transpose(outputData)
                    self.returnData.setOutputData(originalOutputData)
                    self.data.setEmulatorOutputStatus(i, Model.CALCULATED)
                    self.numOutputsFinished = self.numOutputsFinished + 1
                    try:
                        os.remove("psuadeData")
                    except:
                        pass
            self.returnData.setRunState([True] * self.returnData.getNumSamples())
            LocalExecutionModule.runFinished = True


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
