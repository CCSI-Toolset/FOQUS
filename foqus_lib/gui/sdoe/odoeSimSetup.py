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
import os
import copy
import tempfile
import subprocess

from foqus_lib.framework.sampleResults.results import Results
from foqus_lib.framework.uq.LocalExecutionModule import LocalExecutionModule
from foqus_lib.framework.uq.Model import Model
from foqus_lib.framework.uq.SampleData import SampleData
from foqus_lib.framework.uq.Distribution import Distribution
from foqus_lib.framework.uq.SamplingMethods import SamplingMethods
from foqus_lib.framework.uq.ExperimentalDesign import ExperimentalDesign
from foqus_lib.framework.uq.Common import Common
from foqus_lib.gui.flowsheet.dataBrowserFrame import dataBrowserFrame
from .sdoePreview import sdoePreview
from foqus_lib.gui.common.InputPriorTable import InputPriorTable

# from SimSetup_UI import Ui_Dialog
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStackedLayout, QComboBox, QApplication, QMessageBox
from PyQt5.QtGui import QCursor

mypath = os.path.dirname(__file__)
_SimSetupUI, _odoeSimSetup = uic.loadUiType(os.path.join(mypath, "SimSetup_UI.ui"))


class odoeSimSetup(_odoeSimSetup, _SimSetupUI):

    SCHEME_PAGE_INDEX = 0
    LOAD_PAGE_INDEX = 1
    FLOWSHEET_PAGE_INDEX = 2

    def __init__(
        self, model, session, viewOnly=False, returnDataSignal=None, parent=None
    ):
        super(odoeSimSetup, self).__init__(parent)

        self.setupUi(self)
        self.viewOnly = viewOnly
        self.returnDataSignal = returnDataSignal
        self.sampleFileSet = (
            set()
        )  # Contains which inputs are of the distribution "Sample from File"

        self.fsDataBrowser = dataBrowserFrame(session, self)
        self.dataViewWidget.setLayout(QStackedLayout(self.dataViewWidget))
        self.dataViewWidget.layout().addWidget(self.fsDataBrowser)
        self.fsDataBrowser.refreshContents()

        self.fileLoaded = False
        self.samplesGenerated = False

        self.currentArchiveData = None

        self.model = model
        self.session = session

        if isinstance(model, Model):
            data = SampleData(model)
            dists = []
            for i in range(model.getNumInputs()):
                dists = dists + ["U"]
            data.setInputDistributions(dists)
        else:
            data = model
            self.currentArchiveData = data

        self.ignoreDistributionCheck = False

        if model.getRunType() == Model.EMULATOR:
            self.flowsheetDataRadio.setHidden(True)

        if viewOnly:
            self.loadSamplesRadio.setEnabled(False)
            self.flowsheetDataRadio.setEnabled(False)
        self.loadSamplesRadio.clicked.connect(self.setPage)
        self.flowsheetDataRadio.clicked.connect(self.setPage)
        self.chooseSchemeRadio.clicked.connect(self.setPage)
        self.setPage()

        self.groupBox_2.setHidden(True)

        self.cancelButton.clicked.connect(self.cancel)
        self.previewButton.clicked.connect(self.preview)
        self.previewButton.setEnabled(False)
        self.doneButton.clicked.connect(self.doneClicked)
        self.doneButton.setEnabled(False)
        if viewOnly:
            self.cancelButton.setText("OK")
            self.doneButton.setHidden(True)
            self.samplingTabs.setTabEnabled(1, False)

        # Make sure appropriate option is visible
        if not isinstance(model, Model):
            if model.getInputData() is not None:
                self.previewButton.setEnabled(True)
                if not viewOnly:
                    self.doneButton.setEnabled(True)
                self.runData = model

        # Make sure distribution tab is showing
        self.samplingTabs.setCurrentIndex(0)
        self.samplingTabs.currentChanged[int].connect(self.checkDists)

        # Set up distributions table
        self.distTable.init(model, InputPriorTable.SIMSETUP, viewOnly=viewOnly)

        self.allFixedButton.clicked.connect(self.makeAllFixed)
        self.allVariableButton.clicked.connect(self.makeAllVariable)
        if viewOnly or model.getRunType() == Model.EMULATOR:
            self.allFixedButton.setHidden(True)
            self.allVariableButton.setHidden(True)

        # Set up sampling schemes tab
        self.generateSamplesButton.setEnabled(False)
        self.generateStatusText.setText("")
        self.allSchemesRadio.setChecked(True)

        foundLibs = LocalExecutionModule.getPsuadeInstalledModules()
        foundMETIS = foundLibs["METIS"]

        self.schemesList.clear()
        self.schemesList.addItems(SamplingMethods.fullNames[0:4])
        self.schemesList.addItems(SamplingMethods.fullNames[7:8])
        self.schemesList.addItems(SamplingMethods.fullNames[9:])

        if not foundMETIS:
            item = self.schemesList.item(SamplingMethods.METIS)
            text = item.text()
            item.setText(text + " (Not installed)")
            flags = item.flags()
            item.setFlags(flags & ~Qt.ItemIsEnabled)

        if isinstance(model, SampleData):
            self.schemesList.setCurrentRow(model.getSampleMethod())
            self.generateSamplesButton.setEnabled(True)

        # Change lists of schemes displayed
        self.allSchemesRadio.toggled.connect(self.showAllSchemes)
        self.adaptiveRefineRadio.toggled.connect(self.showAdaptiveRefineSchemes)
        self.otherRadio.toggled.connect(self.showOtherSchemes)

        self.schemesList.currentItemChanged.connect(self.handleGenerateSamplesButton)
        self.generateSamplesButton.clicked.connect(self.generateSamples)

    def cancel(self):
        self.reject()

    def doneClicked(self):
        if self.returnDataSignal:
            self.returnDataSignal.emit(self.getData())
            dirname = os.path.join(os.getcwd(), "ODOE_Files")
            filename = os.path.join(dirname, self.getData().getModelName())
            self.getData().writeToCsv(filename, inputsOnly=True)

        self.accept()

    def setPage(self):
        """
        Change the page view
        """

        self.samplePages.setCurrentIndex(self.SCHEME_PAGE_INDEX)
        self.previewButton.setEnabled(self.samplesGenerated)
        self.doneButton.setEnabled(self.samplesGenerated)

    def makeAllFixed(self):
        self.distTable.makeAllFixed()

    def makeAllVariable(self):
        self.distTable.makeAllVariable()

    def checkDists(self, tabIndex):
        if tabIndex == 0 or self.ignoreDistributionCheck:
            self.ignoreDistributionCheck = False
            return

        showMessage = False
        if self.distTable.getNumVariables() == 0:
            showMessage = True
            message = "All inputs are fixed! One needs to be variable."
        else:
            valid, error = self.distTable.checkValidInputs()
            if not valid:
                showMessage = True
                message = (
                    "Distribution settings not correct or entirely filled out! %s"
                    % error
                )
            else:
                rowsToWarnAboutMass = []
                for row in range(self.distTable.rowCount()):
                    for col in [3, 4]:
                        item = self.distTable.item(row, col)
                        if col == 3:
                            minVal = float(item.text())
                        else:
                            maxVal = float(item.text())

                    #### Get distribution parameters
                    for col in [6, 7]:
                        cellTable = self.distTable.cellWidget(row, col)
                        if isinstance(cellTable, QComboBox):
                            continue
                        item = None
                        if cellTable is not None:
                            item = cellTable.item(0, 1)
                        if item is not None and item.text():
                            if col == 6:
                                distParam1 = float(item.text())
                            else:
                                distParam2 = float(item.text())
                        else:
                            if col == 6:
                                distParam1 = None
                            else:
                                distParam2 = None

                    #### Check mass and warn if below 50%
                    # Only collect those that are not fixed to generate inputs
                    combobox = self.distTable.cellWidget(row, 5)
                    dist = combobox.currentIndex()
                    # Create file for psuade input
                    if dist not in [Distribution.UNIFORM, Distribution.SAMPLE]:
                        f = tempfile.SpooledTemporaryFile()
                        for i in range(2):
                            f.write(b"cdf_lookup\n")
                            distNum = dist
                            if dist == Distribution.BETA:
                                distNum = 4
                            elif dist == Distribution.WEIBULL:
                                distNum = 5
                            elif dist == Distribution.GAMMA:
                                distNum = 6
                            elif dist == Distribution.EXPONENTIAL:
                                distNum = 7
                            f.write(b"%d\n" % distNum)  # Number of distribution
                            f.write(b"%f\n" % distParam1)  # Parameter 1
                            if distParam2 is not None:
                                f.write(b"%f\n" % distParam2)  # Parameter 2
                            if i == 0:
                                val = minVal
                            else:
                                val = maxVal
                            f.write(b"%f\n" % val)  # Min or max value
                        f.write(b"quit\n")
                        f.seek(0)

                        # invoke psuade
                        psuadePath = LocalExecutionModule.getPsuadePath()
                        if psuadePath is None:
                            return
                        p = subprocess.Popen(
                            psuadePath,
                            stdin=f,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True,
                        )
                        f.close()

                        # process error
                        out, error = p.communicate()
                        if error:
                            Common.showError(error, out)
                            return None

                        # parse output
                        lines = out.splitlines()
                        vals = []
                        for line in lines:
                            if "Cumulative probability = " in line.decode("utf-8"):
                                words = line.split()
                                vals.append(float(words[-1]))

                        mass = vals[1] - vals[0]
                        if mass < 0.5:
                            rowsToWarnAboutMass.append(row)

                if len(rowsToWarnAboutMass) > 0:
                    self.samplingTabs.setCurrentIndex(0)
                    for row in rowsToWarnAboutMass:
                        msgbox = QMessageBox()
                        msgbox.setWindowTitle("UQ/Opt GUI Warning")
                        msgbox.setText(
                            "Regarding input "
                            + self.model.getInputNames()[row]
                            + ": Min/max range is narrow for its distribution. "
                            + "This could cause sample generation to take more time.  Continue?"
                        )
                        msgbox.setIcon(QMessageBox.Warning)
                        msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                        msgbox.setDefaultButton(QMessageBox.Yes)
                        ret = msgbox.exec_()
                        if ret != QMessageBox.Yes:
                            self.distTable.selectRow(row)
                            return
                    self.ignoreDistributionCheck = True
                    self.samplingTabs.setCurrentIndex(1)

        if showMessage:
            self.samplingTabs.setCurrentIndex(0)
            msgbox = QMessageBox()
            msgbox.setWindowTitle("UQ/Opt GUI Warning")
            msgbox.setText(message)
            msgbox.setIcon(QMessageBox.Warning)
            msgbox.exec_()
            return

    ### Sampling schemes methods
    def showAllSchemes(self):
        if self.chooseSchemeRadio.isChecked():
            foundLibs = LocalExecutionModule.getPsuadeInstalledModules()
            foundMETIS = foundLibs["METIS"]

            self.schemesList.clear()
            self.schemesList.addItems(SamplingMethods.fullNames[0:4])
            self.schemesList.addItems(SamplingMethods.fullNames[7:8])
            if not foundMETIS:
                item = self.schemesList.item(SamplingMethods.METIS)
                text = item.text()
                item.setText(text + " (Not installed)")
                flags = item.flags()
                item.setFlags(flags & ~Qt.ItemIsEnabled)

    def showAdaptiveRefineSchemes(self):
        if self.adaptiveRefineRadio.isChecked():
            foundLibs = LocalExecutionModule.getPsuadeInstalledModules()
            foundMETIS = foundLibs["METIS"]
            self.schemesList.clear()
            self.schemesList.addItem(SamplingMethods.getFullName(SamplingMethods.METIS))
            if not foundMETIS:
                item = self.schemesList.item(0)
                text = item.text()
                item.setText(text + " (Not installed)")
                flags = item.flags()
                item.setFlags(flags & ~Qt.ItemIsEnabled)

    def showOtherSchemes(self):
        if self.otherRadio.isChecked():
            self.schemesList.clear()
            self.schemesList.addItem(SamplingMethods.getFullName(SamplingMethods.MC))
            self.schemesList.addItem(SamplingMethods.getFullName(SamplingMethods.LPTAU))
            self.schemesList.addItem(SamplingMethods.getFullName(SamplingMethods.LH))
            self.schemesList.addItem(SamplingMethods.getFullName(SamplingMethods.OA))

    def handleGenerateSamplesButton(self):
        self.generateSamplesButton.setEnabled(self.schemesList.currentRow() != -1)

    def generateSamples(self):

        # Gather all info into SampleData object
        if isinstance(self.model, Model):
            model = copy.deepcopy(self.model)
        else:
            model = copy.deepcopy(self.model.model)

        # Gather distributions from distribution table
        types = []
        modelTypes = self.model.getInputTypes()
        defaults = []
        modelDefaults = self.model.getInputDefaults()
        mins = []
        modelMins = self.model.getInputMins()
        maxs = []
        modelMaxs = self.model.getInputMaxs()
        dists = []
        selectedInputs = []
        # Set sampling scheme to selected or monte carlo if adaptive
        if self.chooseSchemeRadio.isChecked():
            scheme = self.schemesList.currentItem().text()
        else:
            scheme = "Monte Carlo"

        # First get parameters for the model
        row = 0
        for inputNum in range(self.model.getNumInputs()):
            if modelTypes[inputNum] == Model.VARIABLE:
                # Type
                combobox = self.distTable.cellWidget(row, 1)
                if combobox is None:
                    text = self.distTable.item(row, 1).text()
                else:
                    text = combobox.currentText()

                if text == "Fixed":
                    value = Model.FIXED
                else:
                    value = Model.VARIABLE

                types.append(value)
                if value == Model.VARIABLE:
                    selectedInputs.append(inputNum)

                # Defaults
                item = self.distTable.item(row, 2)
                if item is None or len(item.text()) == 0:
                    defaults.append(None)
                else:
                    defaults.append(float(item.text()))

                # Mins
                item = self.distTable.item(row, 3)
                mins.append(float(item.text()))

                # Maxs
                item = self.distTable.item(row, 4)
                maxs.append(float(item.text()))

                row += 1
            else:  # Fixed
                types.append(Model.FIXED)
                defaults.append(modelDefaults[inputNum])
                mins.append(modelMins[inputNum])
                maxs.append(modelMaxs[inputNum])

        # Update model
        model.setInputTypes(types)
        model.setInputDefaults(defaults)
        model.setInputMins(mins)
        model.setInputMaxs(maxs)

        # Create SampleData object
        runData = SampleData(model, self.session)
        res = Results()
        res.odoe_add_result(runData)
        possibleNames = []
        odoeCandList = []
        for i in range(len(self.session.odoeCandList)):
            odoeCandList.append(self.session.odoeCandList[i].getModelName())
        for i in range(100):
            possibleNames.append("ODoE_Candidate_%s" % str(i + 1))
        for i in range(len(possibleNames)):
            if possibleNames[i] not in odoeCandList:
                newName = possibleNames[i]
                break
            else:
                newName = possibleNames[i + 1]

        runData.setModelName(newName)
        runData.setFromFile(False)

        # Now get distributions for the SampleData object
        numSampleFromFile = 0
        row = 0
        for inputNum in range(self.model.getNumInputs()):
            if modelTypes[inputNum] == Model.VARIABLE:
                # Only collect those that are not fixed to generate inputs
                combobox = self.distTable.cellWidget(row, 5)
                dist = combobox.currentIndex()
                # Check non-uniform distribution and non-Monte Carlo scheme
                if (
                    False
                ):  # dist != Distribution.UNIFORM and SamplingMethods.getEnumValue(scheme) != SamplingMethods.MC:
                    msgbox = QMessageBox()
                    msgbox.setWindowTitle("UQ/Opt GUI Warning")
                    msgbox.setText(
                        "Non-Uniform distributions are not compatible with any "
                        + "sampling scheme other than Monte Carlo!  Please change "
                        + "all distributions back to uniform or select Monte Carlo "
                        + "sampling scheme."
                    )
                    msgbox.setIcon(QMessageBox.Warning)
                    msgbox.exec_()
                    return

                if dist == Distribution.SAMPLE:
                    numSampleFromFile += 1

                dists += [self.distTable.getDistribution(row)]

                row += 1
            else:  # Fixed
                dist = Distribution(Distribution.UNIFORM)
                dists = dists + [dist]

        runData.setInputDistributions(dists)

        numSamples = int(self.numSamplesBox.value())
        runData.setNumSamples(numSamples)
        runData.setSampleMethod(scheme)

        # Check number of samples
        scheme = runData.getSampleMethod()
        newNumSamples = SamplingMethods.validateSampleSize(
            scheme, len(selectedInputs), numSamples
        )
        if scheme == SamplingMethods.LSA:
            if newNumSamples != numSamples:
                msgbox = QMessageBox()
                msgbox.setWindowTitle("UQ/Opt GUI Warning")
                msgbox.setText(
                    "%s scheme with %d variable inputs requires %d samples! Do you want to proceed?"
                    % (
                        SamplingMethods.getPsuadeName(scheme),
                        len(selectedInputs),
                        newNumSamples,
                    )
                )
                msgbox.setIcon(QMessageBox.Question)
                msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msgbox.setDefaultButton(QMessageBox.Yes)
                response = msgbox.exec_()
                if response == QMessageBox.Yes:
                    runData.setNumSamples(newNumSamples)
                else:
                    return
        elif scheme == SamplingMethods.MOAT or scheme == SamplingMethods.GMOAT:
            if type(newNumSamples) is tuple:
                msgbox = QMessageBox()
                msgbox.setWindowTitle("UQ/Opt GUI Warning")
                msgbox.setText(
                    "%s scheme with %d variable inputs cannot have %d samples! How do you want to proceed?"
                    % (
                        SamplingMethods.getFullName(scheme),
                        len(selectedInputs),
                        numSamples,
                    )
                )
                msgbox.setIcon(QMessageBox.Question)
                firstValButton = msgbox.addButton(
                    "Change to %d samples" % newNumSamples[0], QMessageBox.AcceptRole
                )
                secondValButton = msgbox.addButton(
                    "Change to %d samples" % newNumSamples[1], QMessageBox.AcceptRole
                )
                cancelButton = msgbox.addButton(QMessageBox.Cancel)

                msgbox.exec_()
                if msgbox.clickedButton() == firstValButton:
                    runData.setNumSamples(int(newNumSamples[0]))
                elif msgbox.clickedButton() == secondValButton:
                    runData.setNumSamples(int(newNumSamples[1]))
                else:
                    return

        # Visual indications of processing
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.generateStatusText.setText("Generating...")
        self.generateStatusText.repaint()

        # Generate samples for the variable inputs
        selectedRunData = ExperimentalDesign.generateSamples(
            runData, selectedInputs, self.model.getSelectedOutputs()
        )
        if selectedRunData is None:
            QApplication.restoreOverrideCursor()
            self.generateStatusText.setText("")
            return
        selectedInputData = selectedRunData.getInputData()

        # Add fixed inputs back in
        fullInputData = [0] * runData.getNumSamples()
        for row in range(runData.getNumSamples()):
            rowData = []
            selectedIndex = 0
            for col in range(runData.getNumInputs()):
                if col in selectedInputs:
                    rowData.append(selectedInputData[row][selectedIndex])
                    selectedIndex = selectedIndex + 1
                else:
                    rowData.append(defaults[col])
            fullInputData[row] = rowData
        runData.setInputData(fullInputData)
        runData.setRunState([0] * runData.getNumSamples())
        self.runData = runData

        # Handle archive of METIS file
        if self.runData.getSampleMethod() == SamplingMethods.METIS:
            if self.currentArchiveData is not None:
                self.currentArchiveData.removeArchiveFolder()
                pass
            self.runData.archiveFile("psuadeMetisInfo")
            self.currentArchiveData = self.runData

        # Restore cursor
        QApplication.restoreOverrideCursor()
        self.generateStatusText.setText("Done!")

        self.samplesGenerated = True
        self.previewButton.setEnabled(True)
        self.doneButton.setEnabled(True)

    # Preview button
    def preview(self):
        previewData = self.runData
        hname = None
        dirname = os.path.join(os.getcwd(), "ODOE_Files")
        usf = None
        nusf = None
        irsf = None
        scatterLabel = "Candidates"
        nImpPts = 0

        filename = os.path.join(dirname, self.getData().getModelName())
        self.getData().writeToCsv(filename, inputsOnly=True)

        dialog = sdoePreview(
            previewData, hname, dirname, usf, nusf, irsf, scatterLabel, nImpPts, self
        )
        dialog.show()

    # Return data
    def getData(self):
        return self.runData
