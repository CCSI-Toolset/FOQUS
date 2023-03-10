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
import sys
import shutil
import os

from foqus_lib.framework.uq.SampleData import *
from foqus_lib.framework.uq.Model import *
from foqus_lib.framework.uq.SamplingMethods import *
from foqus_lib.framework.uq.ResponseSurfaces import *
from foqus_lib.framework.uq.RSInference import *
from foqus_lib.framework.solventfit.SolventFit import SolventFit
from foqus_lib.framework.uq.Visualizer import Visualizer
from foqus_lib.framework.uq.Common import *
from . import RSCombos
from foqus_lib.gui.common.InputPriorTable import InputPriorTable

# from InferenceDialog_UI import Ui_Dialog
from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *

mypath = os.path.dirname(__file__)
_InferenceDialogUI, _InferenceDialog = uic.loadUiType(
    os.path.join(mypath, "InferenceDialog_UI.ui")
)


class InferenceDialog(_InferenceDialog, _InferenceDialogUI):
    format = "%.5f"  # numeric format for table entries in UQ Toolbox

    def __init__(self, data, wizardMode=False, userRegressionFile=None, parent=None):
        super(InferenceDialog, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)
        self.originalData = data
        data = data.getValidSamples()  # filter out samples that have no output results
        self.data = data
        self.wizardMode = wizardMode
        self.userRegressionFile = userRegressionFile
        self.fileDir = ""

        self.obsTableValues = {}
        self.obsTableDefaultValues = []

        self.setWindowTitle("Bayesian Inference of Ensemble %s" % data.getModelName())

        # Hide items in wizard mode and expert mode
        if wizardMode:
            self.discrepancy_chkbox.hide()
            self.discrepancySave_chkbox.hide()
            self.discrepancySave_edit.hide()
            self.discrepancySave_button.hide()
            self.loadObs_button.hide()
            self.saveObs_button.hide()
        else:
            self.outputInstruction.hide()
            self.inputInstruction.hide()
            self.obsInstruction.hide()
            self.saveInstruction.hide()
            self.inferInstruction.hide()
            self.replotInstruction.hide()
            self.numExperiments_static.setText("Number of experiments:")

        self.outputColumnHeaders = [
            self.output_table.horizontalHeaderItem(i).text()
            for i in range(self.output_table.columnCount())
        ]

        self.infSave_chkbox.toggled.connect(self.activateInfSave)
        self.infSave_button.clicked.connect(self.infBrowse)
        self.inf_button.clicked.connect(self.infer)
        self.replot_button.clicked.connect(self.replot)

        Common.initFolder(RSInferencer.dname)

        nSamples = data.getNumSamples()
        nInputs = data.getNumInputs()

        # activate save components
        ### TO DO: change initFolder to not delete post sample files OR save somewhere else
        sampleFile = Common.getLocalFileName(
            os.getcwd(), data.getModelName().split()[0], ".inputPostSample"
        )
        self.infSave_edit.setText(sampleFile)
        self.infSave_chkbox.setEnabled(True)
        self.infSave_button.setEnabled(False)
        self.infSave_edit.setEnabled(False)

        # populate tables
        self.output_table.setEnabled(True)
        self.initPriorTable()
        self.inputPrior_table.setEnabled(True)
        # self.refreshOutputTable()
        self.outputCol_index = {"obs": 0, "name": 1, "rs1": 2, "rs2": 3, "legendre": 4}
        if not self.wizardMode:
            self.outputCol_index["marsbasis"] = 5
            self.outputCol_index["marsinteraction"] = 6
        self.refreshOutputTable()
        self.inputPrior_table.setSolventFitMode(False)
        self.initObsTable()
        self.refreshObsTable()
        self.obs_table.setEnabled(True)

        # Number of experiments spinbox
        self.numExperiments_spin.setMinimum(1)
        self.numExperiments_spin.valueChanged.connect(self.setObsTableRowCount)
        self.setObsTableRowCount(1)

        self.loadObs_button.clicked.connect(self.loadObservation)
        self.saveObs_button.clicked.connect(self.saveObservation)
        self.saveObs_button.setEnabled(False)

        self.discrepancy_chkbox.toggled.connect(self.activateDiscrepancy)
        self.discrepancySave_chkbox.setEnabled(False)
        self.discrepancySave_chkbox.toggled.connect(self.activateDiscrepancySave)
        self.discrepancySave_edit.setEnabled(False)
        self.discrepancySave_button.setEnabled(False)
        self.discrepancySave_button.clicked.connect(self.setDiscrepancyFile)

        # deactivate infer button
        self.inf_button.setEnabled(False)

        # deactivate replot button
        self.replot_button.setEnabled(False)

        # Changes in cells will check fields
        self.output_table.cellChanged.connect(self.activateInfButton)
        #        self.inputPrior_table.cellChanged.connect(self.activateInfButton)
        self.inputPrior_table.pdfChanged.connect(self.activateInfButton)
        self.numExperiments_spin.valueChanged.connect(self.activateInfButton)
        self.obs_table.cellChanged.connect(self.activateInfButton)

    def freeze(self):
        QApplication.setOverrideCursor(QCursor(QtCore.Qt.WaitCursor))

    def semifreeze(self):
        QApplication.setOverrideCursor(QCursor(QtCore.Qt.BusyCursor))

    def unfreeze(self):
        QApplication.restoreOverrideCursor()

    @staticmethod
    def isnumeric(str):
        if len(str) == 0:
            return False
        try:
            float(str)
            return True
        except ValueError:
            return False

    def activateInfSave(self):
        b = self.infSave_chkbox.isChecked()
        self.infSave_button.setEnabled(b)
        self.infSave_edit.setEnabled(b)

    def infBrowse(self):
        fname = self.infSave_edit.text()
        fname, selectedFilter = QFileDialog.getSaveFileName(
            self, "Indicate file to save posterior input samples", fname
        )
        if len(fname) > 0:  # if a file was indicated during browse
            self.infSave_edit.setText(fname)
            self.replot_button.setEnabled(False)

    def activateDiscrepancy(self):
        b = self.discrepancy_chkbox.isChecked()
        self.discrepancySave_chkbox.setEnabled(b)
        if b:
            self.activateDiscrepancySave()
        else:
            self.discrepancySave_chkbox.setEnabled(False)
            self.discrepancySave_edit.setEnabled(False)
            self.discrepancySave_button.setEnabled(False)

    def activateDiscrepancySave(self):
        b = self.discrepancySave_chkbox.isChecked()
        self.discrepancySave_edit.setEnabled(b)
        self.discrepancySave_button.setEnabled(b)

    def setDiscrepancyFile(self):
        fname = self.discrepancySave_edit.text()
        fname, selectedFilter = QFileDialog.getSaveFileName(
            self, "Indicate file to save posterior input samples", fname
        )
        if len(fname) > 0:  # if a file was indicated during browse
            self.discrepancySave_edit.setText(fname)

    def refreshOutputTable(self):

        data = self.data
        data = data.getValidSamples()  # filter out samples that have no output results
        nSamples = data.getNumSamples()
        inTypes = data.getInputTypes()
        nInputs = inTypes.count(Model.VARIABLE)
        y = data.getOutputData()

        # populate table
        outVarNames = data.getOutputNames()
        nOutputs = data.getNumOutputs()
        self.output_table.setRowCount(nOutputs)
        self.output_table.setColumnCount(len(self.outputCol_index))
        self.output_table.setHorizontalHeaderLabels(
            self.outputColumnHeaders[: len(self.outputCol_index)]
        )
        self.outputMeans = [0] * nOutputs
        self.outputStdDevs = [0] * nOutputs
        for i in range(nOutputs):

            # compute mean and standard deviation
            yi = y[:, i]
            mu = np.mean(yi)
            self.outputMeans[i] = mu
            sigma = np.std(yi)
            self.outputStdDevs[i] = sigma

            # add output name
            item = QTableWidgetItem(outVarNames[i])
            flags = item.flags()
            mask = ~QtCore.Qt.ItemIsEnabled
            item.setFlags(flags & mask)
            item.setForeground(Qt.black)
            self.output_table.setItem(i, self.outputCol_index["name"], item)
            # if output takes on one value, then disable that output from inference
            if sigma > 0:
                # add checkbox
                chkbox = self.output_table.cellWidget(i, self.outputCol_index["obs"])
                if chkbox is None:
                    chkbox = QCheckBox("", self)
                    chkbox.setChecked(False)
                    chkbox.setEnabled(True)
                    chkbox.toggled.connect(self.refreshObsTable)
                    chkbox.toggled.connect(self.activateInfButton)
                    self.output_table.setCellWidget(
                        i, self.outputCol_index["obs"], chkbox
                    )

                # add combo boxes for RS1 and rs2 and Legendre spinbox
                combo1 = RSCombos.RSCombo1(self)
                combo2 = RSCombos.RSCombo2(self)
                legendreSpin = RSCombos.LegendreSpinBox(self)
                marsBasisSpin = None
                marsInteractionSpin = None
                if "marsbasis" in self.outputCol_index:
                    marsBasisSpin = RSCombos.MarsBasisSpinBox(self)
                    marsBasisSpin.init(data)
                if "marsinteraction" in self.outputCol_index:
                    marsInteractionSpin = RSCombos.MarsDegreeSpinBox(self)
                    marsInteractionSpin.init(data)

                legendreSpin.init(data)
                combo2.init(data, legendreSpin, useShortNames=True)
                combo1.init(
                    data,
                    combo2,
                    True,
                    True,
                    marsBasisSpin=marsBasisSpin,
                    marsDegreeSpin=marsInteractionSpin,
                )

                combo1.setProperty("row", i)
                combo2.setProperty("row", i)

                combo1.currentIndexChanged[int].connect(self.disableReplot)
                combo2.currentIndexChanged[int].connect(self.disableReplot)
                combo2.fileAdded.connect(self.refreshUserRegressionFiles)
                legendreSpin.valueChanged[int].connect(self.disableReplot)
                if "marsbasis" in self.outputCol_index:
                    marsBasisSpin.valueChanged[int].connect(self.disableReplot)
                if "marsinteraction" in self.outputCol_index:
                    marsInteractionSpin.valueChanged[int].connect(self.disableReplot)

                self.output_table.setCellWidget(i, self.outputCol_index["rs1"], combo1)
                self.output_table.setCellWidget(i, self.outputCol_index["rs2"], combo2)
                self.output_table.setCellWidget(
                    i, self.outputCol_index["legendre"], legendreSpin
                )
                if "marsbasis" in self.outputCol_index:
                    self.output_table.setCellWidget(
                        i, self.outputCol_index["marsbasis"], marsBasisSpin
                    )
                if "marsinteraction" in self.outputCol_index:
                    self.output_table.setCellWidget(
                        i, self.outputCol_index["marsinteraction"], marsInteractionSpin
                    )

            else:
                # add a disabled checkbox
                chkbox = QCheckBox("")
                chkbox.setChecked(False)
                chkbox.setEnabled(False)
                self.output_table.setCellWidget(i, self.outputCol_index["obs"], chkbox)
                # add inactive field for RS1
                item = QTableWidgetItem("")
                flags = item.flags()
                mask = ~QtCore.Qt.ItemIsEnabled
                item.setFlags(flags & mask)
                item.setForeground(Qt.black)
                item.setBackground(Qt.lightGray)
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.output_table.setItem(i, self.outputCol_index["rs1"], item)
                # add inactive field for RS2
                item = QTableWidgetItem("")
                flags = item.flags()
                mask = ~QtCore.Qt.ItemIsEnabled
                item.setFlags(flags & mask)
                item.setForeground(Qt.black)
                item.setBackground(Qt.lightGray)
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.output_table.setItem(i, self.outputCol_index["rs2"], item)

            # add inactive field for Legendre
            item = QTableWidgetItem("")
            flags = item.flags()
            mask = ~QtCore.Qt.ItemIsEnabled
            item.setFlags(flags & mask)
            item.setForeground(Qt.black)
            item.setBackground(Qt.lightGray)
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.output_table.setItem(i, self.outputCol_index["legendre"], item)

        self.output_table.resizeColumnsToContents()

    def disableReplot(self):
        self.replot_button.setEnabled(False)

    def refreshUserRegressionFiles(self):
        rows = self.output_table.rowCount()
        for row in range(rows):
            combo = self.output_table.cellWidget(row, self.outputCol_index["rs2"])
            if combo is not None:
                combo.refresh()
        self.output_table.resizeColumnsToContents()

    def initPriorTable(self):
        self.inputPrior_table.init(
            self.data, InputPriorTable.INFERENCE, self.wizardMode
        )
        self.inputPrior_table.typeChanged.connect(self.refreshObsTable)
        self.inputPrior_table.pdfChanged.connect(self.disableReplot)

    def initObsTable(self):
        self.obs_table.setRowCount(1)
        self.obs_table.setColumnCount(0)

    def setObsTableRowCount(self, count):
        self.obs_table.setRowCount(count)
        for row in range(count):
            item = self.obs_table.verticalHeaderItem(row)
            if item is None:
                item = QTableWidgetItem("Experiment %d" % (row + 1))
                self.obs_table.setVerticalHeaderItem(row, item)

                # Populate default values
                for col in range(self.obs_table.columnCount()):
                    value = self.obsTableDefaultValues[col]
                    if value is not None:
                        item = QTableWidgetItem("%g" % value)
                        self.obs_table.setItem(row, col, item)

    def loadObservation(self):
        if platform.system() == "Windows":
            allFiles = "*.*"
        else:
            allFiles = "*"
        fname, _ = QFileDialog.getOpenFileName(
            self,
            "Browse to observations file",
            self.fileDir,
            "Psuade Simple File (*.smp);;CSV (Comma delimited) (*.csv);;All files (%s)"
            % allFiles,
        )
        if not fname:  # Cancelled
            return

        self.fileDir = os.path.dirname(fname)

        try:
            if fname.endswith(".csv"):
                data = LocalExecutionModule.readDataFromCsvFile(fname, False)
                data = data[0]
                numExps = data.shape[0]
            else:
                _, designData, outputData = LocalExecutionModule.readMCMCFile(fname)
                numExps = designData.shape[0]
                data = np.hstack([designData, outputData])
        except:  # Invalid file
            import traceback

            traceback.print_exc()
            msgbox = QMessageBox()
            msgbox.setWindowTitle("UQ/Opt GUI Warning")
            msgbox.setText(
                "File format not recognized!  File must be in PSUADE simple or CSV format."
            )
            msgbox.setIcon(QMessageBox.Warning)
            msgbox.exec_()
            # combobox.setCurrentIndex(0)
            return

        showMessage = False
        mcmcNumDesign = self.inputPrior_table.getNumDesignVariables()
        if fname.endswith(".csv"):
            numCols = data.shape[1]
            expectedCols = mcmcNumDesign + 2 * self.getNumObservedOutputs()
            if numCols != expectedCols:
                showMessage = True
                message = (
                    "Number of columns in file (%d) does not match expected (%d for %d design values and average and std dev columns for %d observed outputs)"
                    % (
                        numCols,
                        expectedCols,
                        mcmcNumDesign,
                        self.getNumObservedOutputs(),
                    )
                )
        else:
            numDesign = designData.shape[1]
            numOutputColumns = outputData.shape[1]

            if numDesign != mcmcNumDesign:
                showMessage = True
                message = (
                    "Number of design parameters selected (%d) does not match file (%d)."
                    % (numDesign, mcmcNumDesign)
                )
            elif numOutputColumns != 2 * self.getNumObservedOutputs():
                showMessage = True
                message = (
                    "Number of outputs observed (%d) does not match file (%d)."
                    % (self.getNumObservedOutputs(), numOutputColumns / 2)
                )

        if showMessage:
            msgbox = QMessageBox()
            msgbox.setWindowTitle("UQ/Opt GUI Warning")
            msgbox.setText(message)
            msgbox.setIcon(QMessageBox.Warning)
            msgbox.exec_()
            return

        self.freeze()
        self.numExperiments_spin.setValue(numExps)
        self.obs_table.setRowCount(numExps)
        for r in range(numExps):
            for c in range(data.shape[1]):
                item = self.obs_table.item(r, c)
                if item is None:
                    item = QTableWidgetItem()
                    self.obs_table.setItem(r, c, item)
                item.setText("%g" % data[r, c])
        self.unfreeze()

    def saveObservation(self):
        fname, selectedFilter = QFileDialog.getSaveFileName(
            self, "Set observation file name:"
        )
        if len(fname) == 0:  # Cancelled
            return

        designVariables, indices = self.inputPrior_table.getDesignVariables()
        indices = [index + 1 for index in indices]
        data = []
        for row in range(self.obs_table.rowCount()):
            rowValues = []
            for col in range(self.obs_table.columnCount()):
                item = self.obs_table.item(row, col)
                rowValues.append(float(item.text()))
            data.append(rowValues)

        LocalExecutionModule.saveMCMCFile(
            fname,
            self.getNumObservedOutputs(),
            self.inputPrior_table.getNumDesignVariables(),
            indices,
            data,
        )

    def refreshObsTable(self):
        self.replot_button.setEnabled(False)
        numRows = self.obs_table.rowCount()
        ### Store info before change
        colValues = {}

        for c in range(self.obs_table.columnCount()):
            columnHeader = self.obs_table.horizontalHeaderItem(c).text()
            values = [""] * numRows
            for r in range(numRows):
                item = self.obs_table.item(r, c)
                if item is not None:
                    values[r] = item.text()
            colValues[columnHeader] = values

        ### Update table

        ## Set number of columns
        numCols = self.inputPrior_table.getNumDesignVariables()  # Design variables
        # outputs
        count = self.getNumObservedOutputs()
        numCols += count * 2  # mean and std

        self.obs_table.clearContents()
        self.setObsTableRowCount(numRows)
        self.obs_table.setColumnCount(numCols)
        self.obsTableValues.clear()

        ## Fill in column names
        labels = []
        designVariables, indices = self.inputPrior_table.getDesignVariables()
        numDesignVariables = len(designVariables)
        for i, name in enumerate(designVariables):
            labels.append(name + " Value")
        for row in range(self.output_table.rowCount()):
            chkbox = self.output_table.cellWidget(row, self.outputCol_index["obs"])
            if chkbox is not None and chkbox.isChecked():
                name = self.output_table.item(row, self.outputCol_index["name"]).text()
                labels.append(name + " Mean")
                indices.append(row)
                labels.append(name + " Std Dev")
                indices.append(row)
        self.obs_table.setHorizontalHeaderLabels(labels)

        ## Repopulate values
        self.obsTableDefaultValues = [None] * numCols
        for col, label in enumerate(labels):
            if col >= numDesignVariables:
                if label.endswith("Mean"):
                    defvalue = self.outputMeans[indices[col]]
                else:
                    defvalue = self.outputStdDevs[indices[col]]
                self.obsTableDefaultValues[col] = defvalue
            if label in colValues:
                values = colValues[label]
                for row, value in enumerate(values):
                    item = self.obs_table.item(row, col)
                    if item is None:
                        item = QTableWidgetItem()
                        self.obs_table.setItem(row, col, item)
                    item.setText(value)
                    self.obsTableValues[(row, col)] = value
            elif col >= numDesignVariables:
                for row in range(numRows):
                    item = self.obs_table.item(row, col)
                    if item is None:
                        item = QTableWidgetItem()
                        self.obs_table.setItem(row, col, item)
                    item.setText("%g" % defvalue)
                    self.obsTableValues[(row, col)] = "%g" % defvalue

        self.obs_table.resizeColumnsToContents()

    def getNumObservedOutputs(self):
        count = 0
        for row in range(self.output_table.rowCount()):
            chkbox = self.output_table.cellWidget(row, self.outputCol_index["obs"])
            if chkbox is not None and chkbox.isChecked():
                count += 1
        return count

    def getObservedOutputsIndices(self):
        count = 0
        indices = []
        for row in range(self.output_table.rowCount()):
            chkbox = self.output_table.cellWidget(row, self.outputCol_index["obs"])
            if chkbox is not None and chkbox.isChecked():
                indices.append(row)
        return indices

    def checkOutputTable(self):
        for i in range(self.output_table.rowCount()):
            chkbox = self.output_table.cellWidget(i, self.outputCol_index["obs"])
            if chkbox is not None and chkbox.isChecked():
                return True
        return False

    def checkObs(self):
        b = False
        for r in range(self.obs_table.rowCount()):
            names, indices = self.inputPrior_table.getDesignVariables()
            numDesign = len(names)
            mins = self.inputPrior_table.getMins()
            maxs = self.inputPrior_table.getMaxs()
            for c in range(self.obs_table.columnCount()):
                item = self.obs_table.item(r, c)
                if item is not None:
                    text = item.text()
                    if len(text) > 0:
                        if (r, c) in self.obsTableValues:
                            textSame = text == self.obsTableValues[(r, c)]
                        else:
                            textSame = False
                        self.obsTableValues[(r, c)] = text
                        showMessage = False
                        if not self.isnumeric(text):
                            showMessage = True
                            message = "Value must be a number!"
                        elif c < numDesign:
                            value = float(item.text())
                            index = indices[c]
                            minVal = mins[index]
                            maxVal = maxs[index]
                            if value < minVal or value > maxVal:
                                showMessage = True
                                message = "Value must be between %g and %g!" % (
                                    minVal,
                                    maxVal,
                                )
                        elif (c - numDesign) % 2 == 1:  # Std Dev value
                            value = float(item.text())
                            if value <= 0:
                                showMessage = True
                                message = "Std dev value must be greater than 0!"
                        if showMessage:
                            if not textSame:
                                msgbox = QMessageBox()
                                msgbox.setWindowTitle("UQ/Opt GUI Warning")
                                msgbox.setText(message)
                                msgbox.setIcon(QMessageBox.Warning)
                                response = msgbox.exec_()
                                self.obs_table.setCurrentCell(r, c)
                                self.obs_table.setFocus()
                            # self.colorChanged.add((r, c))
                            item.setForeground(QColor(192, 0, 0))
                            return False
                        else:
                            # self.colorChanged.add((r, c))
                            item.setForeground(QColor(0, 0, 0))
                            b = True
                    else:
                        return False
                else:
                    return False
        return b

    def activateInfButton(self, row=None, col=None):
        # TO DO: check valid file name in self.infSave_edit.text()

        self.replot_button.setEnabled(False)

        showList = self.inputPrior_table.getShowInputList()
        if (
            self.checkOutputTable()
            and self.checkObs()
            and self.inputPrior_table.checkValidInputs()[0]
            and len(showList) > 0
        ):
            self.saveObs_button.setEnabled(True)
            self.inf_button.setEnabled(True)
            return True
        else:
            self.saveObs_button.setEnabled(False)
            self.inf_button.setEnabled(False)
            return False

    def enableInf(self, b):
        self.infSave_chkbox.setEnabled(b)
        if b:
            if self.infSave_chkbox.isChecked():
                self.infSave_edit.setEnabled(True)
                self.infSave_button.setEnabled(True)
            self.discrepancy_chkbox.setEnabled(True)
            if self.discrepancy_chkbox.isChecked():
                self.discrepancySave_chkbox.setEnabled(True)
                if self.discrepancySave_chkbox.isChecked():
                    self.discrepancySave_edit.setEnabled(True)
                    self.discrepancySave_button.setEnabled(True)
        else:
            self.infSave_edit.setEnabled(False)
            self.infSave_button.setEnabled(False)
            self.discrepancy_chkbox.setEnabled(False)
            self.discrepancySave_chkbox.setEnabled(False)
            self.discrepancySave_edit.setEnabled(False)
            self.discrepancySave_button.setEnabled(False)

        # self.inf_button.setEnabled(b)
        self.inf_button.setEnabled(b)
        self.output_table.setEnabled(b)
        self.inputPrior_table.setEnabled(b)
        self.replot_button.setEnabled(b)

    def infer(self):
        if self.inf_button.text() == "Infer":
            if os.path.exists("psuade_stop"):
                os.remove("psuade_stop")

            # check arguments
            if not self.activateInfButton():
                return

            Common.initFolder(RSInferencer.dname)

            self.semifreeze()
            self.stopInfer = False

            data = self.data
            data = (
                data.getValidSamples()
            )  # filter out samples that have no output results

            # parse output table
            nOutputs = self.output_table.rowCount()
            col_index = self.outputCol_index
            ytable = [None] * nOutputs
            for i in range(nOutputs):
                chkbox = self.output_table.cellWidget(i, col_index["obs"])
                if chkbox.isChecked():
                    outputName = self.output_table.item(i, col_index["name"]).text()
                    value = {"name": outputName}
                    rs1 = self.output_table.cellWidget(i, col_index["rs1"])
                    rs2 = self.output_table.cellWidget(i, col_index["rs2"])
                    rs = RSCombos.lookupRS(rs1, rs2)
                    rsIndex = ResponseSurfaces.getEnumValue(rs)
                    value["rsIndex"] = rsIndex
                    if not self.wizardMode and rsIndex in (
                        ResponseSurfaces.MARS,
                        ResponseSurfaces.MARSBAG,
                    ):
                        marsBases = self.output_table.cellWidget(
                            i, col_index["marsbasis"]
                        ).value()
                        marsInteractions = self.output_table.cellWidget(
                            i, col_index["marsinteraction"]
                        ).value()
                        value["marsBases"] = marsBases
                        value["marsInteractions"] = marsInteractions
                    elif rsIndex == ResponseSurfaces.LEGENDRE:
                        legendreOrder = self.output_table.cellWidget(
                            i, col_index["legendre"]
                        ).value()
                        value["legendreOrder"] = legendreOrder
                    elif rsIndex == ResponseSurfaces.USER:
                        fileName = rs2.getFile()
                        value["userRegressionFile"] = fileName
                        outputName = Common.getUserRegressionOutputName(
                            outputName, fileName, data
                        )
                        value["userRegressionArg"] = outputName
                    ytable[i] = value

            # parse input prior table
            xtable = self.inputPrior_table.getTableValues()

            # parse obs table
            numExp = self.obs_table.rowCount()
            obsTable = [0] * numExp
            for i in range(numExp):
                values = [i + 1]
                for j in range(self.obs_table.columnCount()):
                    item = self.obs_table.item(i, j)
                    values.append(item.text())
                obsTable[i] = values

            ##            fname = Common.getLocalFileName(RSInferencer.dname, data.getModelName(), '.dat')
            ##            data.writeToPsuade(fname)

            # perform inference
            saveSample = self.infSave_chkbox.isChecked()
            showList = self.inputPrior_table.getShowInputList()
            self.inf_button.setText("Stop")  # Switch button to allow stop
            useDiscrepancy = self.discrepancy_chkbox.isChecked()
            self.setModal(False)
            self.enableInf(False)

            self.inference = RSInference(
                data,
                ytable,
                xtable,
                obsTable,
                genPostSample=saveSample,
                addDisc=useDiscrepancy,
                showList=showList,
                endFunction=self.finishInfer,
                disableWhilePlotting=self.inf_button,
                userRegressionFile=self.userRegressionFile,
            )
            self.inference.analyze()

        else:  # Infer button says stop
            f = open("psuade_stop", "w")
            f.close()
            self.stopInfer = True
            self.inference.inferencer.stopInference()
            self.inf_button.setText("Infer")
            self.unfreeze()
            self.output_table.setEnabled(True)
            self.inputPrior_table.setEnabled(True)

    #            self.enableInf(True)

    def finishInfer(self):  # Called after inference is done
        #        mfile = 'matlabmcmc2.m'
        #        if os.path.exists(mfile):  #Inference happened just fine
        if self.inference.getResultsFile() is not None:
            # copy posterior sample to designated file
            if (
                self.infSave_chkbox.isChecked()
                and self.inference.inferencer.sampleFile is not None
            ):
                sampleFile = self.infSave_edit.text()
                if os.path.exists(sampleFile):
                    os.remove(sampleFile)
                os.rename(self.inference.inferencer.sampleFile, sampleFile)

            if (
                self.discrepancy_chkbox.isChecked()
                and self.discrepancySave_chkbox.isChecked()
            ):
                os.rename("psDiscrepancyModel", self.discrepancySave_edit.text())

            message = ""
            if self.wizardMode:
                message = (
                    "This plot shows the posterior distribution of the inputs "
                    "that will result in the observations specified.  The "
                    "diagonal subplots show the distribution of each individual "
                    "input as a histogram. The off-diagonal subplots are "
                    "pair-wise heatmaps of this distribution. "
                )
            if self.stopInfer:
                if (
                    self.inference.inferencer.mfile is None
                ):  # PSUADE was not allowed to go far enough to provide a plot
                    message = "Inference was not allowed to complete far enough to create a plot.  If one is desired, please start inference again."
                else:
                    message += "Because inference was not allowed to fully complete, these results are not as accurate as possible."

            if len(message) > 0:
                QMessageBox.information(self, "Bayesian Inference Plot", message)

        self.unfreeze()
        self.inf_button.setText("Infer")
        self.enableInf(True)
        # self.inf_button.setEnabled(True)
        self.output_table.setEnabled(True)
        self.inputPrior_table.setEnabled(True)
        if self.inference.getResultsFile() is not None:
            self.replot_button.setEnabled(True)

            # Add inference analysis to original ensemble
            self.inference.endFunction = None
            # self.inference.inferencer = None
            self.inference.disableWhilePlotting = None
            self.originalData.addAnalysis(self.inference)
            if self.parent is not None:
                self.parent.updateAnalysisTableWithNewRow()

    def replot(self):
        self.freeze()

        showList = self.inputPrior_table.getShowInputList()
        if len(showList) == 0:
            QMessageBox.information(
                self,
                "Bayesian Inference Plot",
                "At least one input must be selected for display.",
            )
            self.unfreeze()
            return

        self.inference.showResults(showList)

        self.unfreeze()
