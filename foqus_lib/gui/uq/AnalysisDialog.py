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
import os
import numpy
import shutil
import textwrap

from foqus_lib.framework.uq.SampleData import *
from foqus_lib.framework.uq.Model import *
from foqus_lib.framework.uq.SamplingMethods import *
from foqus_lib.framework.uq.ParameterScreening import *
from foqus_lib.framework.uq.Visualization import *
from foqus_lib.framework.uq.UncertaintyAnalysis import *
from foqus_lib.framework.uq.CorrelationAnalysis import *
from foqus_lib.framework.uq.SensitivityAnalysis import *
from foqus_lib.framework.uq.RSValidation import *
from foqus_lib.framework.uq.RSUncertaintyAnalysis import *
from foqus_lib.framework.uq.RSSensitivityAnalysis import *
from foqus_lib.framework.uq.RSVisualization import *
from foqus_lib.framework.uq.ResponseSurfaces import *
from foqus_lib.framework.uq.RawDataAnalyzer import *
from foqus_lib.framework.uq.RSAnalyzer import *
from foqus_lib.framework.uq.Visualizer import Visualizer
from foqus_lib.framework.uq.Common import *
from .AnalysisInfoDialog import *
from .InferenceDialog import *
from foqus_lib.gui.common.InputPriorTable import InputPriorTable
from . import RSCombos

# from AnalysisDialog_UI import Ui_Dialog
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QMessageBox,
    QFileDialog,
    QCheckBox,
    QTableWidgetItem,
    QAbstractItemView,
    QGridLayout,
    QDialog,
    QLabel,
    QPushButton,
)
from PyQt5.QtGui import QCursor

mypath = os.path.dirname(__file__)
_AnalysisDialogUI, _AnalysisDialog = uic.loadUiType(
    os.path.join(mypath, "AnalysisDialog_UI.ui")
)


class AnalysisDialog(_AnalysisDialog, _AnalysisDialogUI):
    # Info table
    idRow = 0
    numInputsRow = 1
    numOutputsRow = 2
    schemeRow = 3
    sampleSizeRow = 4
    descriptorRow = 5

    # Analysis table
    typeCol = 0
    subtypeCol = 1
    inputCol = 2
    outputCol = 3
    rsCol = 4

    def __init__(self, idNum, data, parent=None):
        super(AnalysisDialog, self).__init__(parent)
        self.setupUi(self)
        self.data = data
        self.parent = parent

        # clear all i/o folders
        Common.initFolder(RawDataAnalyzer.dname)
        Common.initFolder(RSAnalyzer.dname)
        Common.initFolder(Visualizer.dname)

        self.setWindowTitle(
            "Analysis of Ensemble %d: %s" % (idNum, data.getModelName())
        )

        self.wizardRSValidated = False

        ##### Hide until implemented!
        # self.analysisTableGroup.hide()

        ## Info table
        mask = ~(Qt.ItemIsEnabled)

        # ID Number
        item = QTableWidgetItem(str(idNum))
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        flags = item.flags()
        item.setFlags(flags & mask)
        item.setForeground(Qt.black)
        self.infoTable.setItem(self.idRow, 0, item)

        # Num inputs
        item = QTableWidgetItem(str(data.getNumInputs()))
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        flags = item.flags()
        item.setFlags(flags & mask)
        item.setForeground(Qt.black)
        self.infoTable.setItem(self.numInputsRow, 0, item)

        # Num outputs
        item = QTableWidgetItem(str(data.getNumOutputs()))
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        flags = item.flags()
        item.setFlags(flags & mask)
        item.setForeground(Qt.black)
        self.infoTable.setItem(self.numOutputsRow, 0, item)

        # Sample size
        item = QTableWidgetItem(str(data.getNumSamples()))
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        flags = item.flags()
        item.setFlags(flags & mask)
        self.infoTable.setItem(self.sampleSizeRow, 0, item)

        # Sampling scheme
        item = QTableWidgetItem(SamplingMethods.getFullName(data.getSampleMethod()))
        flags = item.flags()
        item.setFlags(flags & mask)
        item.setForeground(Qt.black)
        self.infoTable.setItem(self.schemeRow, 0, item)

        # Descriptor
        item = QTableWidgetItem(data.getModelName())
        flags = item.flags()
        item.setFlags(flags & mask)
        item.setForeground(Qt.black)
        self.infoTable.setItem(self.descriptorRow, 0, item)

        self.wizardModeButtonText = "Mode: Wizard (Click for Expert Mode)"
        self.expertModeButtonText = "Mode: Expert (Click for Wizard Mode)"

        self.numInputsOverWhichToScreen = 10
        self.paramScreenRecommendedText = (
            "You have over %d inputs. " % self.numInputsOverWhichToScreen
        )
        self.paramScreenRecommendedText += "Parameter selection is recommended to determine which inputs can be removed from initial consideration."
        self.noParamScreenNeededText = (
            "No parameter selection is necessary for %d inputs. " % data.getNumInputs()
        )
        self.noParamScreenNeededText += (
            "However, if selection is still desired, click here:"
        )

        self.numSamplesForRawAnalysis = 1000
        self.ensembleAnalysisRecommendedText = (
            "You have at least %d samples. " % self.numSamplesForRawAnalysis
        )
        self.ensembleAnalysisRecommendedText += "This is enough to perform analysis on the ensemble data with good results. "
        self.ensembleAnalysisRecommendedText += "You may still choose to analyze data evaluated by a response surface trained on the ensemble data instead."
        self.RSAnalysisRecommendedText = (
            "You have fewer than %d samples. " % self.numSamplesForRawAnalysis
        )
        self.RSAnalysisRecommendedText += "It is recommended to perform analysis using a response surface trained on the data rather than the raw data itself. "
        self.RSAnalysisRecommendedText += (
            "You may still choose to analyze the raw ensemble data instead."
        )

        # Set wizard page as default
        self.modeButton.setText(self.wizardModeButtonText)
        self.modePages.setCurrentIndex(0)

        self.modeButton.clicked.connect(self.switchModes)

        self.initWizardPage()
        self.initExpertPage()

        # Resize tables
        self.infoTable.resizeColumnsToContents()
        self.analysisTable.resizeColumnsToContents()
        self.show()

        width = (
            2 + self.infoTable.verticalHeader().width() + self.infoTable.columnWidth(0)
        )
        if self.infoTable.verticalScrollBar().isVisible():
            width += self.infoTable.verticalScrollBar().width()
        #        scollBarWidth = QApplication.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        #        width += scollBarWidth
        self.infoTable.setMaximumWidth(width)
        self.infoGroup.setMinimumWidth(width + 22)
        # self.infoGroup.setMaximumWidth(width + 60)
        maxHeight = 4
        for i in range(6):
            maxHeight += self.infoTable.rowHeight(i)
        self.infoTable.setMaximumHeight(maxHeight)

        #        print self.analysisTable.verticalHeader().width()
        width = 2 + self.analysisTable.verticalHeader().width()
        for i in range(self.analysisTable.columnCount()):
            width += self.analysisTable.columnWidth(i)
        #            print self.analysisTable.columnWidth(i)
        if self.analysisTable.verticalScrollBar().isVisible():
            width += self.analysisTable.verticalScrollBar().width()
        #        width += scollBarWidth
        self.analysisTable.setMinimumWidth(width)
        self.analysisTable.setMaximumWidth(width)
        self.analysisTable.setRowCount(0)
        self.analysisTable.itemSelectionChanged.connect(self.analysisSelected)
        self.analysisTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.analysisTable.setWordWrap(True)
        #        print width
        self.refreshAnalysisTable()
        self.analysisSelected()

        self.results_button.clicked.connect(self.showAnalysisResults)
        self.info_button.clicked.connect(self.showInfo)
        self.delete_button.clicked.connect(self.deleteAnalysis)

    def switchModes(self):
        QApplication.processEvents()
        if self.modeButton.text() == self.wizardModeButtonText:  # Wizard mode
            # Switch to Expert mode
            self.modeButton.setText(self.expertModeButtonText)
            self.modePages.setCurrentIndex(1)
        else:  # Expert mode
            # Switch to Wizard mode
            self.modeButton.setText(self.wizardModeButtonText)
            self.modePages.setCurrentIndex(0)
        QApplication.processEvents()

    def analysisSelected(self):
        selectedIndexes = self.analysisTable.selectedIndexes()
        if not selectedIndexes:
            self.info_button.setEnabled(False)
            self.results_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            return
        row = selectedIndexes[0].row()
        analysis = self.data.getAnalysisAtIndex(row)
        info = analysis.getAdditionalInfo()
        self.info_button.setEnabled(info is not None and len(info) > 0)
        self.results_button.setEnabled(True)
        self.delete_button.setEnabled(True)

    def refreshAnalysisTable(self):
        numAnalyses = self.data.getNumAnalyses()
        self.analysisTable.setRowCount(numAnalyses)
        for i in range(numAnalyses):
            self.updateAnalysisTableRow(i)

    def updateAnalysisTableWithNewRow(self):
        numAnalyses = self.data.getNumAnalyses()
        self.analysisTable.setRowCount(numAnalyses)
        self.updateAnalysisTableRow(numAnalyses - 1)
        self.analysisTable.selectRow(numAnalyses - 1)

    def updateAnalysisTableRow(self, row):
        analysis = self.data.getAnalysisAtIndex(row)

        # Analysis type
        item = self.analysisTable.item(row, self.typeCol)
        if item is None:
            item = QTableWidgetItem()
            self.analysisTable.setItem(row, self.typeCol, item)
        analType, subtype = analysis.getType()
        item.setText(UQAnalysis.getTypeFullName(analType))

        # Analysis subtype
        item = self.analysisTable.item(row, self.subtypeCol)
        if item is None:
            item = QTableWidgetItem()
            self.analysisTable.setItem(row, self.subtypeCol, item)
        item.setText(analysis.getSubTypeFullName(subtype))

        # Response surface
        item = self.analysisTable.item(row, self.rsCol)
        if item is None:
            item = QTableWidgetItem()
            self.analysisTable.setItem(row, self.rsCol, item)
        if isinstance(analysis, UQRSAnalysis):
            if isinstance(analysis.getResponseSurface(), str):
                item.setText(
                    ResponseSurfaces.getFullName(analysis.getResponseSurface())
                )
            else:
                names = [
                    ResponseSurfaces.getFullName(rs)
                    for rs in analysis.getResponseSurface()
                ]
                text = ", ".join(names)
                maxLength = max([len(name) for name in names]) + 1
                maxLength = max([maxLength, 15])
                item.setText(textwrap.fill(text, maxLength))
        else:
            item.setText("")

        # Input
        item = self.analysisTable.item(row, self.inputCol)
        if item is None:
            item = QTableWidgetItem()
            self.analysisTable.setItem(row, self.inputCol, item)
        inputs = analysis.getInputs()
        if inputs == None:
            input = ""
        elif len(inputs) == 1:
            input = self.data.getInputNames()[inputs[0] - 1]
        else:
            names = [self.data.getInputNames()[input - 1] for input in inputs]
            maxLength = max([len(name) for name in names]) + 1
            maxLength = max([maxLength, 15])
            input = ", ".join(names)
            input = textwrap.fill(input, maxLength)
        item.setText(input)

        # Output
        item = self.analysisTable.item(row, self.outputCol)
        if item is None:
            item = QTableWidgetItem()
            self.analysisTable.setItem(row, self.outputCol, item)
        outputs = analysis.getOutputs()
        if outputs == None:
            output = ""
        elif len(outputs) == 1:
            output = self.data.getOutputNames()[outputs[0] - 1]
        else:
            names = [self.data.getOutputNames()[output - 1] for output in outputs]
            maxLength = max([len(name) for name in names]) + 1
            maxLength = max([maxLength, 15])
            output = ", ".join(names)
            output = textwrap.fill(output, maxLength)
        item.setText(output)

        self.analysisTable.resizeColumnsToContents()
        self.analysisTable.resizeRowsToContents()

    def showInfo(self):
        row = self.analysisTable.selectedIndexes()[0].row()
        analysis = self.data.getAnalysisAtIndex(row)
        self.analysisInfoDialog = AnalysisInfoDialog(analysis.getAdditionalInfo(), self)
        self.analysisInfoDialog.show()

    def showAnalysisResults(self):
        row = self.analysisTable.selectedIndexes()[0].row()
        analysis = self.data.getAnalysisAtIndex(row)
        showList = None

        # Inference requires additional selection of which plots to display
        if isinstance(analysis, RSInference):

            class Dialog(QDialog):
                def __init__(self, xtable, parent=None):
                    super(Dialog, self).__init__(parent)
                    self.setWindowTitle("Plot input selection")
                    self.resize(100, 100)
                    self.gridLayout = QGridLayout(self)
                    text = QLabel("Select inputs to plot:")
                    self.gridLayout.addWidget(text, 0, 0, 1, 2)
                    self.checkboxes = [None] * len(xtable)
                    if len(xtable) > 12:
                        numCols = 2
                    else:
                        numCols = 1
                    numVariables = len([1 for x in xtable if x["type"] != "Design"])
                    numRows = (numVariables + 1) / 2
                    for i, x in enumerate(xtable):
                        if x["type"] != "Design":
                            chkbox = QCheckBox(x["name"])
                            self.checkboxes[i] = chkbox
                            if i >= numRows:
                                self.gridLayout.addWidget(chkbox, i - numRows + 1, 1)
                            else:
                                self.gridLayout.addWidget(chkbox, i + 1, 0)
                            if i in analysis.showList:
                                chkbox.setChecked(True)
                    self.okButton = QPushButton("OK")
                    self.okButton.clicked.connect(self.accept)
                    self.gridLayout.addWidget(self.okButton, numRows + 1, 0, 1, 1)
                    self.cancelButton = QPushButton("Cancel")
                    self.cancelButton.clicked.connect(self.reject)
                    self.gridLayout.addWidget(self.cancelButton, numRows + 1, 1, 1, 1)
                    self.adjustSize()

                def getShowList(self):
                    return [
                        i
                        for i, chkbox in enumerate(self.checkboxes)
                        if chkbox is not None and chkbox.isChecked()
                    ]

            d = Dialog(analysis.xtable, QApplication.activeWindow())
            result = d.exec_()
            if result == QDialog.Rejected:
                return
            showList = d.getShowList()
            d.deleteLater()

        self.freeze()
        try:
            if isinstance(analysis, RSInference):
                analysis.showResults(showList=showList)
            else:
                analysis.showResults()
        except IOError:
            self.unfreeze()
            msgBox = QMessageBox()
            msgBox.setText(
                "Analysis results file is missing. Do you want to run the analysis again?"
            )
            # msgBox.setInformativeText("Do you want to save your changes?")
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msgBox.setDefaultButton(QMessageBox.Yes)
            ret = msgBox.exec_()
            if ret == QMessageBox.Yes:
                self.freeze()
                if isinstance(analysis, RSInference):
                    analysis.endFunction = self.unfreeze
                analysis.analyze()
                if not isinstance(analysis, RSInference):
                    self.unfreeze()
            return
        self.unfreeze()

    def deleteAnalysis(self):
        row = self.analysisTable.selectedIndexes()[0].row()

        # Delete simulation
        self.data.removeAnalysisByIndex(row)
        self.refreshAnalysisTable()
        numAnalyses = self.data.getNumAnalyses()
        if numAnalyses > 0:
            if row >= numAnalyses:
                self.analysisTable.selectRow(numAnalyses - 1)

    def freeze(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

    def semifreeze(self):
        QApplication.setOverrideCursor(QCursor(Qt.BusyCursor))

    def unfreeze(self):
        QApplication.restoreOverrideCursor()

    ######################### Start logic common to both wizard and expert ######################

    ## Parameter screening

    def initParamScreenCombo(self, comboBox, method):
        # populate method combo
        comboBox.clear()
        if method in (
            SamplingMethods.MC,
            SamplingMethods.LPTAU,
            SamplingMethods.LH,
            SamplingMethods.OA,
            SamplingMethods.METIS,
            SamplingMethods.GMETIS,
        ):
            # ... disable MARS if not installed
            marsIndex = 0
            marsName = ParameterScreening.getSubTypeFullName(
                ParameterScreening.MARSRANK
            )
            comboBox.addItem(marsName)
            foundLibs = LocalExecutionModule.getPsuadeInstalledModules()
            foundMARS = foundLibs.get("MARS", False)
            if not foundMARS:
                marsName = marsName + " (Not installed)"
                comboBox.setItemText(marsIndex, marsName)
                model = comboBox.model()
                index = model.index(marsIndex, 0)
                item = model.itemFromIndex(index)
                item.setEnabled(False)
            # ... done disabling
            comboBox.addItem(
                ParameterScreening.getSubTypeFullName(ParameterScreening.SOT)
            )
            comboBox.addItem(
                ParameterScreening.getSubTypeFullName(ParameterScreening.DELTA)
            )
            comboBox.addItem(
                ParameterScreening.getSubTypeFullName(ParameterScreening.GP)
            )
        elif method == SamplingMethods.LSA:
            comboBox.addItem(
                ParameterScreening.getSubTypeFullName(ParameterScreening.LSA)
            )
        elif method == SamplingMethods.MOAT or method == SamplingMethods.GMOAT:
            comboBox.addItem(
                ParameterScreening.getSubTypeFullName(ParameterScreening.MOAT)
            )
        else:
            raise NotImplementedError(
                "There are no parameter screening methods that support sample type %s."
                % method
            )
        comboBox.setCurrentIndex(0)

    def screen(self, outputNum, screen_combo):

        self.freeze()

        # get screening method
        method = screen_combo.currentText()
        method = ParameterScreening.getEnumValue(method)
        # perform screening
        self.setModal(False)
        ps = ParameterScreening(self.data, outputNum, method)
        result = ps.analyze()
        if result is not None:
            self.data.addAnalysis(ps)
            self.updateAnalysisTableWithNewRow()

        self.unfreeze()

    def populateUserRegressionFile(self, regressionFile_edit):
        filename = regressionFile_edit.text()
        if len(filename) == 0:
            filename = os.getcwd()
        fname, selectedFilter = QFileDialog.getOpenFileName(
            self,
            "Indicate file that has user regression code:",
            filename,
            "Python File (*.py)",
        )
        if len(fname) > 0:  # if a file was indicated during browse
            regressionFile_edit.setText(fname)
            return True
        return False

    ## RS Validate
    def rsValidate(
        self,
        y,
        rs,
        rsOptions,
        genRSCode,
        nCV=None,
        userRegressionFile=None,
        testFile=None,
        error_tol_percent=10,
    ):
        self.freeze()

        data = self.data
        data = data.getValidSamples()  # filter out samples that have no output results

        # validate RS
        self.setModal(False)
        rsv = RSValidation(
            data,
            y,
            rs,
            rsOptions=rsOptions,
            genCodeFile=genRSCode,
            nCV=nCV,
            userRegressionFile=userRegressionFile,
            testFile=testFile,
            error_tol_percent=error_tol_percent,
        )
        mfile = rsv.analyze()
        if mfile is not None:
            self.data.addAnalysis(rsv)
            self.updateAnalysisTableWithNewRow()

        self.unfreeze()
        return mfile

    ## Analysis

    def dataViz(self, y, combo1, combo2):

        self.freeze()

        data = self.data

        # get inputs and set method
        inVarNames = data.getInputNames()
        x = []
        if combo1.currentIndex() > 0:
            x1 = combo1.currentText()
            x1 = inVarNames.index(x1) + 1
            x.append(x1)
        if combo2.currentIndex() > 0:
            x2 = combo2.currentText()
            x2 = inVarNames.index(x2) + 1
            x.append(x2)

        # visualize data
        self.setModal(False)
        # Visualizer.yScatter(fname, y, x, cmd)  #x indices are 1-indexed
        v = Visualization(data, y, x)
        result = v.analyze()

        if result is not None:
            self.data.addAnalysis(v)
            self.updateAnalysisTableWithNewRow()

        self.unfreeze()

    def dataAnalyze(self, output_combo, dataAnalyze_combo1, dataAnalyze_combo2):
        self.freeze()

        method = dataAnalyze_combo1.currentText()
        # get output
        y = output_combo.currentIndex()
        if output_combo.itemText(0) != "None selected":
            y += 1

        self.setModal(False)
        if method == "Uncertainty Analysis":
            # RawDataAnalyzer.performUA(fname, y)
            analysis = UncertaintyAnalysis(self.data, y)
        elif method == "Correlation Analysis":
            # RawDataAnalyzer.performCA(fname, y)
            analysis = CorrelationAnalysis(self.data, y)
        else:
            sa_method = dataAnalyze_combo2.currentIndex()
            analysis = SensitivityAnalysis(self.data, y, sa_method)

        result = analysis.analyze()
        if result is not None:
            self.data.addAnalysis(analysis)
            self.updateAnalysisTableWithNewRow()
        self.unfreeze()

    def initDataAnalyzeCombo1(self, combo1, combo2):
        nSamples = self.data.getNumSamples()

        # Find Sensitivity and Bayesian Inference
        numItems = combo1.count()
        sa = numItems
        inf = numItems
        for i in range(numItems):
            if combo1.itemText(i).startswith("Sensitivity"):
                sa = i
            elif "Infer" in combo1.itemText(i):
                inf = i

        # disable SA if nSamples < 1000
        if sa == numItems:
            raise RuntimeError("Combo 1 does not have sensitivity analysis")
        model = combo1.model()
        index = model.index(sa, 0)
        item = model.itemFromIndex(index)
        if nSamples < 1000:
            combo1.setItemText(sa, "Sensitivity (Requires at least 1K samples)")
            item.setEnabled(False)
            combo1.setCurrentIndex(0)
            combo2.hide()
        else:
            combo1.setItemText(sa, "Sensitivity Analysis ->")
            item.setEnabled(True)
            combo2.show()

        # Remove Bayesian
        if inf != numItems:
            combo1.removeItem(inf)

    def handleDataAnalyzeCombo2(self, combo1, combo2):
        data = self.data
        data = data.getValidSamples()  # filter out samples that have no output results
        nInputs = data.getNumInputs()
        nSamples = data.getNumSamples()

        method = combo1.currentText()
        combo2.clear()
        if method.startswith("Sensitivity"):
            disable = []
            enable = []
            if (
                nSamples < 1000
            ):  # this should never happen, as SA should be disabled in combo1
                disable = [
                    "First-order (Requires at least 1K samples)",
                    "Second-order (Requires at least 1K samples)",
                    "Total-order (Requires at least 10K samples)",
                ]
            else:
                if nInputs <= 2:
                    enable = ["First-order"]
                    disable = [
                        "Second-order (Requires at least 3 inputs)",
                        "Total-order (Requires at least 3 inputs)",
                    ]
                elif nSamples < 10000:
                    enable = ["First-order", "Second-order"]
                    disable = ["Total-order (Requires at least 10K samples)"]
                else:
                    if nInputs <= 2:
                        enable = ["First-order"]
                        disable = [
                            "Second-order (Requires at least 3 inputs)",
                            "Total-order (Requires at least 3 inputs)",
                        ]
                    elif nInputs > 10:
                        enable = ["First-order", "Second-order"]
                        disable = ["Total-order (Requires at most 10 inputs)"]
                    else:
                        enable = ["First-order", "Second-order", "Total-order"]
            for i in range(len(enable)):
                s = enable[i]
                combo2.addItem(s)
            for i in range(len(disable)):
                s = disable[i]
                combo2.addItem(s)
                model = combo2.model()
                index = model.index(i + len(enable), 0)
                item = model.itemFromIndex(index)
                item.setEnabled(False)
            combo2.setEnabled(True)
        else:
            combo2.setEnabled(False)

    ## RS Analysis

    def initRSAnalyzeCombo1(
        self, combo1, combo2, expertMode=False, samplePDFChosen=False
    ):
        numItems = combo1.count()
        sa = numItems
        for i in range(numItems):
            text = combo1.itemText(i)
            if text.startswith("Sensitivity"):
                sa = i
                break

        if sa == numItems:
            raise RuntimeError("Combo 1 does not have sensitivity analysis")

        model = combo1.model()
        index = model.index(sa, 0)
        item = model.itemFromIndex(index)
        item.setEnabled(not samplePDFChosen)
        if samplePDFChosen:
            combo1.setItemText(sa, "Sensitivity (Incompatible with Sample PDF)")
            if combo1.currentIndex() == sa:
                combo1.setCurrentIndex(sa - 1)
        else:
            combo1.setItemText(sa, "Sensitivity Analysis ->")
        combo2.show()

    def handleRSAnalyzeCombo2(self, combo1, combo2, samplePDFChosen=False):

        method = combo1.currentText()

        if method.startswith("Uncertainty Analysis ->"):  # expert mode has arrow
            if combo2.itemText(0) != "Aleatory Only":
                combo2.clear()
                combo2.addItem("Aleatory Only")
                combo2.addItem("Epistemic-Aleatory")
            combo2.setEnabled(True)
        elif method.startswith("Sensitivity"):
            if combo2.itemText(0) != "First-order":
                combo2.clear()
                combo2.addItem("First-order")
                nInputs = self.data.getNumInputs()
                disableHighSAs = False
                if nInputs <= 2:
                    combo2.addItem("Second-order (Requires at least 3 inputs)")
                    combo2.addItem("Total-order (Requires at least 3 inputs)")
                    disableHighSAs = True
                elif samplePDFChosen:
                    combo2.addItem("Second-order (Incompatible with Sample PDF)")
                    combo2.addItem("Total-order (Incompatible with Sample PDF)")
                    disableHighSAs = True
                else:
                    combo2.addItem("Second-order")
                    combo2.addItem("Total-order")
                if disableHighSAs:
                    model = combo2.model()
                    for i in [1, 2]:
                        index = model.index(i, 0)
                        item = model.itemFromIndex(index)
                        item.setEnabled(False)
            combo2.setEnabled(True)
        else:
            combo2.clear()
            combo2.setEnabled(False)
        combo2.show()

    def RSAnalyze(
        self,
        output_combo,
        RSAnalyze_combo1,
        RSAnalyze_combo2,
        legendre_spin,
        userRegressionFile_edit,
        rs,
        xprior=None,
        evars=None,
        marsBasis_spin=None,
        marsDegree_spin=None,
    ):

        self.freeze()

        # get output
        y = output_combo.currentIndex()
        if output_combo.itemText(0) != "None selected":
            y += 1

        # get method and analyze RS
        method = RSAnalyze_combo1.currentText()
        self.setModal(False)

        rsOptions = None
        if rs == ResponseSurfaces.getPsuadeName(ResponseSurfaces.LEGENDRE):
            rsOptions = legendre_spin.value()
        elif rs.startswith("MARS"):
            if marsBasis_spin is not None and marsDegree_spin is not None:
                rsOptions = {
                    "marsBases": marsBasis_spin.value(),
                    "marsInteractions": marsDegree_spin.value(),
                }
        if method == "Point Evaluation":
            # Evaluate RS
            data = self.data
            fnameRS = Common.getLocalFileName(
                RSAnalyzer.dname, data.getModelName().split()[0], ".rsdat"
            )
            data.writeToPsuade(fnameRS)
            value = RSAnalyzer.pointEval(
                fnameRS, xprior, y, rs, rsOptions, userRegressionFile_edit.text()
            )
            self.pointEval_label.setText(
                "RS evaluated value for %s is %g with a standard dev. of %g"
                % (output_combo.currentText(), float(value[0]), float(value[1]))
            )
        else:
            if method.startswith("Uncertainty Analysis"):
                # RSAnalyzer.performUA(fnameRS, y, rs, legendre_spin.value(), userRegressionFile_edit.text(), xprior)
                if "Epistemic" in RSAnalyze_combo2.currentText():
                    if len(evars) == 0 or len(evars) >= self.data.getNumInputs():
                        self.unfreeze()
                        QMessageBox.information(
                            self,
                            "No epistemic variables",
                            "This analysis requires at least one aleatory and one epistemic variable!",
                        )
                        return
                    analysis = RSUncertaintyAnalysis(
                        self.data,
                        y,
                        RSUncertaintyAnalysis.ALEATORY_EPISTEMIC,
                        rs,
                        rsOptions,
                        userRegressionFile_edit.text(),
                        xprior,
                    )
                else:
                    analysis = RSUncertaintyAnalysis(
                        self.data,
                        y,
                        RSUncertaintyAnalysis.ALEATORY_ONLY,
                        rs,
                        rsOptions,
                        userRegressionFile_edit.text(),
                        xprior,
                    )
            elif method.startswith("Sensitivity"):
                sa_method = RSAnalyze_combo2.currentIndex()
                analysis = RSSensitivityAnalysis(
                    self.data,
                    y,
                    sa_method,
                    rs,
                    rsOptions,
                    userRegressionFile_edit.text(),
                    xprior,
                )

            results = analysis.analyze()
            if results is not None:
                self.data.addAnalysis(analysis)
                self.updateAnalysisTableWithNewRow()

        self.unfreeze()

    def infer(self, wizardMode):
        dialog = InferenceDialog(self.data, wizardMode, parent=self)
        self.unfreeze()
        # dialog.exec_()
        # dialog.deleteLater()
        dialog.show()

    def initRSVizCombos(self, combo1, combo2, combo3):
        data = self.data
        data = data.getValidSamples()  # filter out samples that have no output results
        nSamples = data.getNumSamples()
        inVarNames = data.getInputNames()
        inTypes = data.getInputTypes()
        nInputs = inTypes.count(Model.VARIABLE)

        combo1.clear()
        combo2.clear()
        combo3.clear()
        combo1.addItem("None selected")
        for x, inType in zip(inVarNames, inTypes):
            if inType == Model.VARIABLE:
                combo1.addItem(x)
        combo1.setCurrentIndex(0)
        if nInputs > 1:
            combo2.addItem("None selected")
            for x, inType in zip(inVarNames, inTypes):
                if inType == Model.VARIABLE:
                    combo2.addItem(x)
            combo2.setCurrentIndex(0)
        if nSamples > 2:
            combo3.addItem("None selected")
            for x, inType in zip(inVarNames, inTypes):
                if inType == Model.VARIABLE:
                    combo3.addItem(x)
            combo3.setCurrentIndex(0)

    def RSVizCombosUnique(self, combo1, combo2, combo3=None):

        # get inputs
        x1 = combo1.currentIndex()
        x2 = combo2.currentIndex()
        x3 = 0
        if combo3 is not None:
            x3 = combo3.currentIndex()
        xlist = numpy.array([x1, x2, x3])
        k = numpy.where(xlist > 0)
        x = xlist[k]
        nx = len(x)
        uniqx = list(set(x))
        cond = (nx > 0) and (nx == len(uniqx))

        return cond

    def RSViz(
        self,
        y,
        combo1,
        combo2,
        combo3,
        rs,
        rsOptions=None,
        minVal=-numpy.inf,
        maxVal=numpy.inf,
        userRegressionFile=None,
    ):

        self.freeze()

        data = self.data

        # get inputs
        inVarNames = data.getInputNames()
        x = []
        if combo1.currentIndex() > 0:
            x1 = combo1.currentText()
            x1 = inVarNames.index(x1) + 1
            x.append(x1)
        if combo2.currentIndex() > 0:
            x2 = combo2.currentText()
            x2 = inVarNames.index(x2) + 1
            x.append(x2)
        if combo3.currentIndex() > 0:
            x3 = combo3.currentText()
            x3 = inVarNames.index(x3) + 1
            x.append(x3)

        # visualize data
        self.setModal(False)
        rsviz = RSVisualization(
            data, y, x, rs, minVal, maxVal, rsOptions, userRegressionFile
        )
        results = rsviz.analyze()
        if results is not None:
            self.data.addAnalysis(rsviz)
            self.updateAnalysisTableWithNewRow()

        self.unfreeze()

    ######################## Wizard page ################################

    def initWizardPage(self):
        self.initWizardScreenGroup()
        self.initWizardAnalysisGroup()

    # ---- Wizard Page Parameter Screening Group

    def initWizardScreenGroup(self):
        numInputs = self.data.getNumInputs()

        # Set up what's hidden or visible based on number of inputs
        if numInputs == 1:  # No screening for one input
            self.wizardScreenGroup.setVisible(False)
        elif numInputs <= self.numInputsOverWhichToScreen:  # No screening needed
            self.wizardScreenText.setText(self.noParamScreenNeededText)
            self.enableScreen_button.setVisible(True)
            self.setWizardScreenComponentsVisible(False)
        else:  # Screening needed
            self.wizardScreenText.setText(self.paramScreenRecommendedText)
            self.enableScreen_button.setVisible(False)

        self.enableScreen_button.clicked.connect(self.enableWizardScreen)

        # populate output combo
        self.wizardScreenOutput_combo.clear()
        # self.wizardScreenOutput_combo.addItem('None selected')
        ydata = self.data.getOutputData()
        disable = []
        currentIndex = 0
        for i, y in enumerate(self.data.getOutputNames()):
            data = ydata[:, i]
            std = numpy.std(data)
            if std == 0:
                text = y + " (No variance)"
                disable.append(i)
                if currentIndex == i:
                    currentIndex += 1
            else:
                text = y
            self.wizardScreenOutput_combo.addItem(text)
        if currentIndex == len(self.data.getOutputNames()):
            currentIndex = 0
        # disable items
        model = self.wizardScreenOutput_combo.model()
        for i in disable:
            index = model.index(i, 0)
            item = model.itemFromIndex(index)
            item.setEnabled(False)
        self.wizardScreenOutput_combo.setCurrentIndex(currentIndex)
        self.wizardScreenOutput_combo.setEnabled(True)

        self.initParamScreenCombo(
            self.wizardScreenMethod_combo, self.data.getSampleMethod()
        )
        self.wizardScreenCompute_button.clicked.connect(self.wizardScreen)

    def enableWizardScreen(self):
        self.enableScreen_button.setVisible(False)
        self.setWizardScreenComponentsVisible(True)

    def setWizardScreenComponentsVisible(self, visible):
        self.wizardScreenOutput_static.setVisible(visible)
        self.wizardScreenOutput_combo.setVisible(visible)
        self.wizardScreenMethod_static.setVisible(visible)
        self.wizardScreenMethod_combo.setVisible(visible)
        self.wizardScreenCompute_static.setVisible(visible)
        self.wizardScreenCompute_button.setVisible(visible)
        self.wizardScreenRepeat_static.setVisible(visible)

    def wizardScreen(self):
        y = self.wizardScreenOutput_combo.currentIndex() + 1
        self.screen(y, self.wizardScreenMethod_combo)
        QMessageBox.information(
            None,
            "Parameter Selection Plot",
            "Take note of which inputs are more sensitive and which are less. "
            "Taller bars in the plot mean more sensitive.",
        )

    # ---- Wizard Page Analysis Group

    def initWizardAnalysisGroup(self):
        data = self.data
        data = data.getValidSamples()  # filter out samples that have no output results
        nSamples = data.getNumSamples()
        nInputs = data.getNumInputs()

        self.wizardAnalysisOutput_combo.clear()
        # self.analysisOutput_combo.addItem('None selected')
        ydata = self.data.getOutputData()
        disable = []
        currentIndex = 0
        for i, y in enumerate(self.data.getOutputNames()):
            data = ydata[:, i]
            std = numpy.std(data)
            if std == 0:
                text = y + " (No variance)"
                disable.append(i)
                if currentIndex == i:
                    currentIndex += 1
            else:
                text = y
            self.wizardAnalysisOutput_combo.addItem(text)
        if currentIndex == len(self.data.getOutputNames()):
            currentIndex = 0
        # disable items
        model = self.wizardAnalysisOutput_combo.model()
        for i in disable:
            index = model.index(i, 0)
            item = model.itemFromIndex(index)
            item.setEnabled(False)
        self.wizardAnalysisOutput_combo.setCurrentIndex(currentIndex)
        self.wizardAnalysisOutput_combo.setEnabled(True)
        self.wizardAnalysisOutput_combo.currentIndexChanged[int].connect(
            self.deactivateWizardRSAnalysis
        )
        self.wizardEnsemble_radio.toggled.connect(self.setWizardEnsembleAnalysisMode)
        self.wizardRS_radio.toggled.connect(self.setWizardRSAnalysisMode)

        if self.data.getNumSamples() < self.numSamplesForRawAnalysis:
            self.wizardAnalysisText.setText(self.RSAnalysisRecommendedText)
            self.wizardRS_radio.setChecked(True)
        else:
            self.wizardAnalysisText.setText(self.ensembleAnalysisRecommendedText)
            self.wizardEnsemble_radio.setChecked(True)
        self.wizardAnalyze_combo2.setEnabled(False)

        self.wizardRSLegendre_spin.init(self.data)
        self.wizardRS_combo2.init(
            self.data, self.wizardRSLegendre_spin, self.wizardRSLegendre_static
        )  # Must be called after legendre spinbox
        self.wizardRS_combo1.init(
            self.data, self.wizardRS_combo2
        )  # Must be called after combo2 init
        self.wizardRSValidate_button.setEnabled(self.wizardRS_combo1.isEnabled())
        self.wizardRS_combo1.currentIndexChanged[int].connect(self.activateWizardRS1)
        self.wizardRS_combo2.currentIndexChanged[int].connect(self.activateWizardRS2)
        self.wizardRSLegendre_spin.valueChanged.connect(self.deactivateWizardRSAnalysis)

        self.wizardUserRegression_static.setEnabled(False)
        self.wizardUserRegressionFile_edit.setEnabled(False)
        self.wizardUserRegressionBrowse_button.setEnabled(False)
        self.wizardUserRegressionBrowse_button.clicked.connect(
            self.populateWizardUserRegressionFile
        )
        self.wizardRSValidate_button.clicked.connect(self.wizardRSValidate)
        self.wizardAnalyze_combo1.currentIndexChanged[int].connect(
            self.activateWizardAnalyze1
        )
        self.wizardAnalyze_button.clicked.connect(self.wizardAnalyze)
        self.initRSVizCombos(
            self.wizardViz_combo1, self.wizardViz_combo2, self.wizardViz_combo3
        )
        self.wizardViz_combo1.currentIndexChanged[int].connect(
            self.activateWizardVizButton
        )
        self.wizardViz_combo2.currentIndexChanged[int].connect(
            self.activateWizardVizButton
        )
        self.wizardViz_combo3.currentIndexChanged[int].connect(
            self.activateWizardVizButton
        )
        self.wizardViz_button.setEnabled(False)
        self.wizardViz_button.clicked.connect(self.wizardViz)
        self.wizardInfer_button.clicked.connect(self.wizardInfer)

    def showWizardRSAnalysisComponents(self, show):
        self.wizardRS_static.setVisible(show)
        self.wizardRS_combo1.setVisible(show)
        self.wizardRS_combo2.setVisible(show)
        self.wizardRSLegendre_static.setVisible(show)
        self.wizardRSLegendre_spin.setVisible(show)
        self.wizardUserRegression_static.setVisible(show)
        self.wizardUserRegressionFile_edit.setVisible(show)
        self.wizardUserRegressionBrowse_button.setVisible(show)
        self.wizardErrorEnvelope_static.setVisible(show)
        self.wizardErrorEnvelope_edit.setVisible(show)
        self.wizardPercentageSign_static.setVisible(show)
        self.wizardRSValidate_static.setVisible(show)
        self.wizardRSValidateNote_static.setVisible(show)
        self.wizardRSValidate_button.setVisible(show)
        self.wizardAnalysisRepeat_static.setVisible(show)
        self.wizardViz_combo3.setVisible(show)
        self.wizardInfer_static.setVisible(show)
        self.wizardInfer_button.setVisible(show)

    def setWizardEnsembleAnalysisMode(self, checked):
        if checked:
            self.showWizardRSAnalysisComponents(False)
            self.wizardViz_static.setText(
                '3. If you would like to visualize the data, choose the inputs and click "Visualize".'
            )
            self.wizardAnalyze_static.setText("4. Choose UQ Analysis:")
            self.wizardAnalyze_button.setEnabled(True)
            self.initDataAnalyzeCombo1(
                self.wizardAnalyze_combo1, self.wizardAnalyze_combo2
            )

    def setWizardRSAnalysisMode(self, checked):
        if checked:
            self.showWizardRSAnalysisComponents(True)
            self.wizardViz_static.setText(
                '5. If you would like to visualize the response surface for correctness of the chosen method for the selected output, choose the inputs and click "Visualize".'
            )
            self.wizardAnalyze_static.setText("7. Choose UQ Analysis:")
            self.initRSAnalyzeCombo1(
                self.wizardAnalyze_combo1, self.wizardAnalyze_combo2
            )
            if self.wizardRSValidated:
                self.activateWizardRSAnalysis()
            else:
                self.deactivateWizardRSAnalysis()

    def getWizardRS(self):
        return RSCombos.lookupRS(self.wizardRS_combo1, self.wizardRS_combo2)

    def activateWizardRS1(self):
        rs = self.wizardRS_combo1.currentText()

        enableValidateButton = True
        enableUserRegression = False
        if rs == ResponseSurfaces.getFullName(ResponseSurfaces.USER):
            enableUserRegression = True
            if len(self.wizardUserRegressionFile_edit.text()) == 0:
                enableValidateButton = False
        self.wizardRSValidate_button.setEnabled(enableValidateButton)
        self.wizardUserRegression_static.setEnabled(enableUserRegression)
        self.wizardUserRegressionFile_edit.setEnabled(enableUserRegression)
        self.wizardUserRegressionBrowse_button.setEnabled(enableUserRegression)

        self.deactivateWizardRSAnalysis()

    def activateWizardRS2(self):
        self.deactivateWizardRSAnalysis()

    def populateWizardUserRegressionFile(self):
        if self.populateUserRegressionFile(self.wizardUserRegressionFile_edit):
            self.wizardRSValidate_button.setEnabled(True)
        self.deactivateWizardRSAnalysis()

    def wizardRSValidate(self):
        self.freeze()
        # get output
        y = self.wizardAnalysisOutput_combo.currentIndex() + 1

        # get RS
        rs = self.getWizardRS()
        rsOptions = None
        if rs == ResponseSurfaces.getPsuadeName(ResponseSurfaces.LEGENDRE):
            rsOptions = self.wizardRSLegendre_spin.value()

        result = self.rsValidate(
            y,
            rs,
            rsOptions,
            False,
            userRegressionFile=self.wizardUserRegressionFile_edit.text(),
            error_tol_percent=self.wizardErrorEnvelope_edit.value(),
        )
        self.unfreeze()
        self.activateWizardRSAnalysis()

        # Make expert mode components reflect the same RS Validation
        self.output_combo.setCurrentIndex(
            self.wizardAnalysisOutput_combo.currentIndex() + 1
        )
        self.RS_combo1.setCurrentIndex(self.wizardRS_combo1.currentIndex())
        self.RS_combo2.setCurrentIndex(self.wizardRS_combo2.currentIndex())
        self.RSLegendre_spin.setValue(self.wizardRSLegendre_spin.value())
        self.doubleSpinBox.setValue(self.wizardErrorEnvelope_edit.value())
        self.expertUserRegressionFile_edit.setText(
            self.wizardUserRegressionFile_edit.text()
        )
        self.activateExpertRSAnalysis()

        if result is not None:
            QMessageBox.information(
                None,
                "Response Surface Validation Plot",
                "The two plots help you gauge the fitness of %s "
                "response surface to the ensemble data. The left "
                "plot is a histogram of the errors between the "
                "ensemble data and response surface prediction of "
                "that data for each sample. A good fit results in "
                "tall bars near 0.0 and very short bars further "
                "from 0.0.  On the right is a plot of predicted "
                "value vs. actual value. A good fit results in all "
                "the points being very close to the diagonal line." % rs,
            )

    def activateWizardRSAnalysis(self):
        self.wizardRSValidated = True
        self.wizardAnalyze_button.setEnabled(True)
        self.activateWizardVizButton()

    def deactivateWizardRSAnalysis(self):
        self.wizardRSValidated = False
        if self.wizardRS_radio.isChecked():
            self.wizardAnalyze_button.setEnabled(False)
        self.wizardViz_button.setEnabled(False)

    def activateWizardAnalyze1(self):
        if self.wizardEnsemble_radio.isChecked():  # Raw data
            self.handleDataAnalyzeCombo2(
                self.wizardAnalyze_combo1, self.wizardAnalyze_combo2
            )
        else:  # RS Analysis
            self.wizardAnalyze_combo2.show()
            self.handleRSAnalyzeCombo2(
                self.wizardAnalyze_combo1, self.wizardAnalyze_combo2
            )

    def wizardAnalyze(self):
        if self.wizardEnsemble_radio.isChecked():  # Raw data
            self.dataAnalyze(
                self.wizardAnalysisOutput_combo,
                self.wizardAnalyze_combo1,
                self.wizardAnalyze_combo2,
            )
        else:  # RS Analysis
            # get RS
            rs = self.getWizardRS()

            self.RSAnalyze(
                self.wizardAnalysisOutput_combo,
                self.wizardAnalyze_combo1,
                self.wizardAnalyze_combo2,
                self.wizardRSLegendre_spin,
                self.wizardUserRegressionFile_edit,
                rs,
            )

            # Show plot help text
            analysisType = self.wizardAnalyze_combo1.currentText()
            if analysisType.startswith("Uncertainty"):
                QMessageBox.information(
                    None,
                    "Uncertainty Analysis Plot",
                    "This plot displays the distribution of the output "
                    "(Normal on top, cumulative on the bottom) as well as "
                    "statistics on the top. Use this plot to gauge whether "
                    "the uncertainty of the output is acceptable. If not, "
                    "further analysis is needed to examine relationships "
                    "between inputs and outputs and what can be done to "
                    "reduce the uncertainties on the inputs that contribute "
                    "more to the uncertainty of this output.",
                )
            elif analysisType.startswith("Sensitivity"):
                order = self.wizardAnalyze_combo2.currentText()
                QMessageBox.information(
                    None,
                    "%s Plot" % order,
                    "Take note of which inputs are more sensitive and which are less. "
                    "Taller bars in the plot mean more sensitive.",
                )

    def activateWizardVizButton(self):
        if self.wizardEnsemble_radio.isChecked():
            enable = self.RSVizCombosUnique(
                self.wizardViz_combo1, self.wizardViz_combo2
            )
        else:
            enable = self.wizardRSValidated and self.RSVizCombosUnique(
                self.wizardViz_combo1, self.wizardViz_combo2, self.wizardViz_combo3
            )

        self.wizardViz_button.setEnabled(enable)

    def wizardViz(self):
        # get output
        y = self.wizardAnalysisOutput_combo.currentIndex() + 1

        if self.wizardEnsemble_radio.isChecked():
            self.dataViz(y, self.wizardViz_combo1, self.wizardViz_combo2)
        else:
            rs = self.getWizardRS()
            rsOptions = None
            if rs == ResponseSurfaces.getPsuadeName(ResponseSurfaces.LEGENDRE):
                rsOptions = self.RSLegendre_spin.value()
            self.RSViz(
                y,
                self.wizardViz_combo1,
                self.wizardViz_combo2,
                self.wizardViz_combo3,
                rs,
                rsOptions,
                userRegressionFile=self.wizardUserRegressionFile_edit.text(),
            )

    def wizardInfer(self):
        self.infer(True)

    ###################################### Expert page ####################################

    def initExpertPage(self):
        self.initExpertAnalysisGroups()
        ##### Expert Page
        self.output_combo.currentIndexChanged[int].connect(
            self.activateExpertAnalysisGroups
        )
        # ~ ~ ~ ~ ~ SCREEN GROUP ~ ~ ~ ~ ~
        self.screen_combo.currentIndexChanged[int].connect(self.activateScreenButton)
        self.screen_button.clicked.connect(self.expertScreen)
        # ~ ~ ~ ~ ~ DATA ANALYSIS GROUP ~ ~ ~ ~ ~
        self.dataAnalyze_combo1.currentIndexChanged[int].connect(
            self.activateDataAnalyze1
        )
        self.dataAnalyze_combo2.currentIndexChanged[int].connect(
            self.activateDataAnalyzeButton
        )
        self.dataAnalyze_button.clicked.connect(self.expertDataAnalyze)
        self.dataViz_combo1.currentIndexChanged[int].connect(self.activateDataVizButton)
        self.dataViz_combo2.currentIndexChanged[int].connect(self.activateDataVizButton)
        self.dataViz_button.clicked.connect(self.expertDataViz)
        # ~ ~ ~ ~ ~ RS ANALYSIS GROUP ~ ~ ~ ~ ~
        self.RS_combo1.currentIndexChanged[int].connect(self.activateRS1)
        self.RS_combo2.currentIndexChanged[int].connect(self.activateRS2)
        self.RSMarsBasis_spin.valueChanged.connect(self.deactivateExpertRSAnalysis)
        self.RSMarsBasis_spin.valueChanged.connect(self.activateRSValidateButton)
        self.RSMarsDegree_spin.valueChanged.connect(self.deactivateExpertRSAnalysis)
        self.RSMarsDegree_spin.valueChanged.connect(self.activateRSValidateButton)
        self.RSLegendre_spin.valueChanged.connect(self.deactivateExpertRSAnalysis)
        self.RSLegendre_spin.valueChanged.connect(self.activateRSValidateButton)
        self.expertUserRegressionBrowse_button.clicked.connect(
            self.populateExpertUserRegressionFile
        )
        self.testSet_chkbox.toggled.connect(self.activateTestSet)
        self.testSetBrowse_button.clicked.connect(self.populateTestSetFile)
        self.RSValidationGroups_spin.valueChanged.connect(
            self.RSValidate_button.setEnabled
        )
        self.RSCodeBrowse_button.clicked.connect(self.RSCodeBrowse)
        self.RSValidate_button.clicked.connect(self.expertRSValidate)
        self.RSAnalyze_combo1.currentIndexChanged[int].connect(self.activateRSAnalyze1)
        self.RSAnalyze_combo2.currentIndexChanged[int].connect(
            self.changePriorTableMode
        )
        self.RSAnalyze_combo2.currentIndexChanged[int].connect(
            self.activateRSAnalyzeButton
        )
        self.RSAnalyze_button.clicked.connect(self.expertRSAnalyze)
        self.inputPrior_table.pdfChanged.connect(self.inputPriorTablePDFChanged)
        self.inputPrior_table.typeChanged.connect(self.inputPriorTablePDFChanged)
        self.RSViz_combo1.currentIndexChanged[int].connect(self.activateRSVizButton)
        self.RSViz_combo2.currentIndexChanged[int].connect(self.activateRSVizButton)
        self.RSViz_combo3.currentIndexChanged[int].connect(self.activateRSVizButton)
        self.RSVizMin_chkbox.toggled.connect(self.activateRSVizMinEdit)
        self.RSVizMax_chkbox.toggled.connect(self.activateRSVizMaxEdit)
        self.RSViz_button.clicked.connect(self.expertRSViz)
        # ~ ~ ~ ~ ~ BAYESIAN INFERENCE ~ ~ ~ ~ ~
        self.expertInfer_button.clicked.connect(self.expertInfer)

        # populate output combo
        self.output_combo.clear()
        self.output_combo.addItem("None selected")
        ydata = self.data.getOutputData()
        disable = []
        for i, y in enumerate(self.data.getOutputNames()):
            data = ydata[:, i]
            std = numpy.std(data)
            if std == 0:
                text = y + " (No variance)"
                disable.append(i + 1)
            else:
                text = y
            self.output_combo.addItem(text)
        # disable items
        model = self.output_combo.model()
        for i in disable:
            index = model.index(i, 0)
            item = model.itemFromIndex(index)
            item.setEnabled(False)
        self.output_combo.setCurrentIndex(0)
        self.output_combo.setEnabled(True)

        # deactivate all groups until output is chosen
        self.paramSelectGroup.setEnabled(False)
        self.ensembleDataGroup.setEnabled(False)
        self.RSGroup.setEnabled(False)

    def initExpertAnalysisGroups(self):

        self.initExpertScreenGroup()
        self.initExpertDataGroup()
        self.initExpertRSGroup()

    def activateExpertAnalysisGroups(self):
        output = self.output_combo.currentText()
        enable = output != "None selected"

        # activate groups
        self.paramSelectGroup.setEnabled(enable)
        self.ensembleDataGroup.setEnabled(enable)
        self.RSGroup.setEnabled(enable)

        # change text for test set checkbox
        if enable:
            self.testSet_chkbox.setText("Use test set for\noutput %s" % output)

    # ~ ~ ~ ~ ~ EXPERT PAGE: SCREEN Group ~ ~ ~ ~ ~
    def initExpertScreenGroup(self):

        data = self.data

        # populate combo
        self.initParamScreenCombo(self.screen_combo, data.getSampleMethod())

        # activate button
        if self.screen_combo.count() > 0:
            self.screen_button.setEnabled(True)

    def activateScreenButton(self):
        self.screen_button.setEnabled(True)

    def enableScreen(self, b):
        self.output_combo.setEnabled(b)
        self.screen_button.setEnabled(b)
        self.screen_combo.setEnabled(b)

    def expertScreen(self):

        self.enableScreen(False)
        y = self.output_combo.currentIndex()
        self.screen(y, self.screen_combo)
        self.enableScreen(True)

    # ~ ~ ~ ~ ~ EXPERT PAGE: DATA ANALYSIS Group ~ ~ ~ ~ ~
    def initExpertDataGroup(self):

        self.dataAnalyze_combo1.setEnabled(True)
        self.dataAnalyze_combo1.setCurrentIndex(0)
        self.dataAnalyze_combo2.clear()
        self.dataAnalyze_combo2.setEnabled(False)
        self.dataAnalyze_button.setEnabled(True)  # defaults to UA
        self.dataViz_combo1.setEnabled(True)
        self.dataViz_combo2.setEnabled(True)
        self.dataViz_button.setEnabled(False)

        data = self.data
        nSamples = data.getNumSamples()
        inVarNames = data.getInputNames()
        inTypes = data.getInputTypes()
        nInputs = inTypes.count(Model.VARIABLE)

        # Populate analysis combos
        self.initDataAnalyzeCombo1(self.dataAnalyze_combo1, self.dataAnalyze_combo2)

        # populate combo
        self.dataViz_combo1.clear()
        self.dataViz_combo2.clear()
        self.dataViz_combo1.addItem("None selected")
        for x, inType in zip(inVarNames, inTypes):
            if inType == Model.VARIABLE:
                self.dataViz_combo1.addItem(x)
        self.dataViz_combo1.setCurrentIndex(0)
        if nInputs > 1:
            self.dataViz_combo2.addItem("None selected")
            for x, inType in zip(inVarNames, inTypes):
                if inType == Model.VARIABLE:
                    self.dataViz_combo2.addItem(x)
            self.dataViz_combo2.setCurrentIndex(0)

    def activateDataAnalyze1(self):
        self.handleDataAnalyzeCombo2(self.dataAnalyze_combo1, self.dataAnalyze_combo2)
        self.dataAnalyze_button.setEnabled(True)

    def activateDataAnalyzeButton(self):
        self.dataAnalyze_button.setEnabled(True)

    def enableDataAnalyze(self, b):
        self.output_combo.setEnabled(b)
        self.dataAnalyze_combo1.setEnabled(b)
        if self.dataAnalyze_combo2.count() > 0:
            self.dataAnalyze_combo2.setEnabled(b)
        else:
            self.dataAnalyze_combo2.setEnabled(False)
        self.dataAnalyze_button.setEnabled(b)

    def expertDataAnalyze(self):

        self.enableDataAnalyze(False)
        self.dataAnalyze(
            self.output_combo, self.dataAnalyze_combo1, self.dataAnalyze_combo2
        )
        self.enableDataAnalyze(True)

    def activateDataVizButton(self):

        x1 = self.dataViz_combo1.currentIndex()
        x2 = self.dataViz_combo2.currentIndex()
        xlist = numpy.array([x1, x2])
        k = numpy.where(xlist > 0)
        x = xlist[k]
        nx = len(x)
        uniqx = list(set(x))
        if (nx > 0) and (nx == len(uniqx)):
            self.dataViz_button.setEnabled(True)
        else:
            self.dataViz_button.setEnabled(False)

    def enableDataViz(self, b):
        self.output_combo.setEnabled(b)
        self.dataViz_combo1.setEnabled(b)
        self.dataViz_combo2.setEnabled(b)
        self.dataViz_button.setEnabled(b)

    def expertDataViz(self):

        self.enableDataViz(False)

        # get output
        y = self.output_combo.currentIndex()

        self.dataViz(y, self.dataViz_combo1, self.dataViz_combo2)
        self.enableDataViz(True)

    # ~ ~ ~ ~ ~ EXPERT PAGE: RS ANALYSIS GROUP ~ ~ ~ ~ ~
    def initExpertRSGroup(self):

        data = self.data
        data = data.getValidSamples()  # filter out samples that have no output results
        nSamples = data.getNumSamples()
        inTypes = data.getInputTypes()
        nInputs = inTypes.count(Model.VARIABLE)

        # set up GUI components
        self.RSMarsBasis_spin.init(data)
        self.RSMarsDegree_spin.init(data)
        self.RSLegendre_spin.init(data)
        self.RS_combo2.init(data, self.RSLegendre_spin, self.RSLegendre_static)
        self.RS_combo1.init(
            data,
            self.RS_combo2,
            marsBasisSpin=self.RSMarsBasis_spin,
            marsBasisCaption=self.RSMarsBasis_static,
            marsDegreeSpin=self.RSMarsDegree_spin,
            marsDegreeCaption=self.RSMarsDegree_static,
        )
        self.RSValidate_button.setEnabled(self.RS_combo1.isEnabled())
        self.expertUserRegression_static.setEnabled(False)
        self.expertUserRegressionFile_edit.setEnabled(False)
        self.expertUserRegressionBrowse_button.setEnabled(False)
        self.testSet_chkbox.setEnabled(False)
        self.testSet_edit.setEnabled(False)
        self.testSetBrowse_button.setEnabled(False)
        self.RSValidationGroups_spin.setMaximum(nSamples)
        self.RSValidationGroups_spin.setMinimum(2)
        nCV = min(10, nSamples)
        self.RSValidationGroups_spin.setValue(nCV)
        self.RSCodeBrowse_button.setEnabled(False)
        self.RSAnalyze_combo1.setEnabled(False)
        self.RSAnalyze_combo2.clear()
        self.RSAnalyze_combo2.addItems(["Aleatory Only", "Epistemic-Aleatory"])
        self.RSAnalyze_combo2.setEnabled(False)
        self.RSAnalyze_button.setEnabled(False)
        b = False
        self.RSViz_combo1.setEnabled(b)
        self.RSViz_combo2.setEnabled(b)
        self.RSViz_combo3.setEnabled(b)
        self.RSVizMin_chkbox.setEnabled(b)
        self.RSVizMax_chkbox.setEnabled(b)
        self.RSVizMin_chkbox.setChecked(False)
        self.RSVizMax_chkbox.setChecked(False)
        self.RSVizMin_edit.setEnabled(False)
        self.RSVizMax_edit.setEnabled(False)
        self.RSVizMin_edit.clear()
        self.RSVizMax_edit.clear()
        self.RSViz_button.setEnabled(False)

        # populate prior table
        self.inputPrior_table.init(data, InputPriorTable.RSANALYSIS)
        self.inputPrior_table.setEnabled(False)

        # populate combo
        self.initRSVizCombos(self.RSViz_combo1, self.RSViz_combo2, self.RSViz_combo3)

        self.samplePDFChosen = False
        self.epistemicMode = False

    def activateRS1(self):

        rs = self.RS_combo1.currentText()
        enableUserRegression = False
        if rs == ResponseSurfaces.getFullName(ResponseSurfaces.USER):
            enableUserRegression = True

        self.expertUserRegression_static.setEnabled(enableUserRegression)
        self.expertUserRegressionFile_edit.setEnabled(enableUserRegression)
        self.expertUserRegressionBrowse_button.setEnabled(enableUserRegression)
        self.testSet_chkbox.setEnabled(enableUserRegression)
        if enableUserRegression:
            self.activateTestSet()
        else:
            self.testSet_edit.setEnabled(False)
            self.testSetBrowse_button.setEnabled(False)
        self.RSValidationGroups_static.setEnabled(not enableUserRegression)
        self.RSValidationGroups_spin.setEnabled(not enableUserRegression)
        self.RSCodeBrowse_button.setEnabled(False)

        self.deactivateExpertRSAnalysis()
        self.activateRSValidateButton()

    def activateRS2(self):

        self.RSValidate_button.setEnabled(True)

        self.RSCodeBrowse_button.setEnabled(False)

        self.deactivateExpertRSAnalysis()

    def populateExpertUserRegressionFile(self):
        if self.populateUserRegressionFile(self.expertUserRegressionFile_edit):
            self.activateRSValidateButton()
            self.deactivateExpertRSAnalysis()

    def activateTestSet(self):
        enable = self.testSet_chkbox.isChecked()
        self.testSet_edit.setEnabled(enable)
        self.testSetBrowse_button.setEnabled(enable)
        self.activateRSValidateButton()

    def populateTestSetFile(self):
        filename = self.testSet_edit.text()
        if len(filename) == 0:
            filename = os.getcwd()
        fname, selectedFilter = QFileDialog.getOpenFileName(
            self, "Indicate file that has user regression test set:", filename
        )
        if len(fname) > 0:  # if a file was indicated during browse
            try:
                data = LocalExecutionModule.readSampleFromPsuadeFile(fname)
                if data.getNumOutputs() > 1:
                    QMessageBox.critical(
                        self, "File Outputs", "This file can only have one output!"
                    )
            except:
                QMessageBox.critical(
                    self,
                    "File format Incorrect",
                    "This file is not a PSUADE formatted file!",
                )
            self.testSet_edit.setText(fname)
        self.activateRSValidateButton()

    def activateRSCodeSave(self):
        rs = self.RS_combo2.currentText()
        if rs in [
            ResponseSurfaces.getFullName(ResponseSurfaces.MARSBAG),
            ResponseSurfaces.getFullName(ResponseSurfaces.USER),
        ]:
            enable = False
        else:
            enable = True
        self.RSCodeBrowse_button.setEnabled(enable)

    def RSCodeBrowse(self):
        filename = os.getcwd() + os.sep + "rs.py"
        fname, selectedFilter = QFileDialog.getSaveFileName(
            self,
            "Indicate file to save posterior input samples",
            filename,
            "Python code (*.py);;C code (*.c)",
        )
        if len(fname) > 0:  # if a file was indicated during browse
            if "*.py" in selectedFilter:
                origFile = "psuade_rs.py"
            else:
                origFile = "psuade_rs.info"
            if os.path.exists(origFile):
                if os.path.exists(fname):
                    os.remove(fname)
                shutil.copyfile(origFile, fname)

    def activateRSValidateButton(self):
        enabled = True

        rs = self.getExpertRS()
        if rs is None:
            enabled = False
        elif ResponseSurfaces.getEnumValue(rs) == ResponseSurfaces.USER:
            if len(self.expertUserRegressionFile_edit.text()) == 0:
                enabled = False
            elif self.testSet_chkbox.isChecked():
                if len(self.testSet_edit.text()) == 0:
                    enabled = False
        self.RSValidate_button.setEnabled(enabled)
        return enabled

    def getExpertRS(self):
        return RSCombos.lookupRS(self.RS_combo1, self.RS_combo2)

    def enableRSValidate(self, b):
        self.output_combo.setEnabled(b)
        self.RS_combo1.setEnabled(b)
        self.RS_combo2.setEnabled(b)
        self.RSLegendre_static.setEnabled(b)
        self.RSLegendre_spin.setEnabled(b)
        self.RSValidate_button.setEnabled(b)
        self.RSValidationGroups_static.setEnabled(b)
        self.RSValidationGroups_spin.setEnabled(b)
        self.RSCodeBrowse_button.setEnabled(b)
        # RS analysis relies on output file generated by RS validation
        self.RSAnalyze_combo1.setEnabled(b)
        self.RSAnalyze_combo2.setEnabled(b)
        self.RSAnalyze_button.setEnabled(b)

    def expertRSValidate(self):

        # check arguments
        if not self.activateRSValidateButton():
            return

        self.enableRSValidate(False)
        self.freeze()

        # get output
        y = self.output_combo.currentIndex()

        # get RS
        rs = self.getExpertRS()
        rsOptions = None
        error_tol_percent = self.doubleSpinBox.value()
        if rs == ResponseSurfaces.getPsuadeName(ResponseSurfaces.LEGENDRE):
            rsOptions = self.RSLegendre_spin.value()
        elif rs.startswith("MARS"):
            rsOptions = {
                "marsBases": self.RSMarsBasis_spin.value(),
                "marsInteractions": self.RSMarsDegree_spin.value(),
            }

        nCV = self.RSValidationGroups_spin.value()

        testFile = None
        if self.testSet_chkbox.isChecked():
            testFile = self.testSet_edit.text()

        genRSCode = True
        self.rsValidate(
            y,
            rs,
            rsOptions,
            genRSCode,
            nCV,
            self.expertUserRegressionFile_edit.text(),
            testFile,
            error_tol_percent,
        )

        rs = self.RS_combo2.currentText()
        if rs != ResponseSurfaces.getFullName(ResponseSurfaces.MARSBAG):
            if not os.path.exists("psuade_rs.info"):
                pass  # TODO: error psuade_rs.info missing
            if not os.path.exists("psuade_rs.py"):
                pass  # TODO: error psuade_rs.py missing

        self.activateRSCodeSave()
        self.activateExpertRSAnalysis()

        # Make expert mode components reflect the same RS Validation
        self.wizardAnalysisOutput_combo.setCurrentIndex(
            self.output_combo.currentIndex() - 1
        )
        self.wizardRS_combo1.setCurrentIndex(self.RS_combo1.currentIndex())
        self.wizardRS_combo2.setCurrentIndex(self.RS_combo2.currentIndex())
        self.wizardRSLegendre_spin.setValue(self.RSLegendre_spin.value())
        self.wizardUserRegressionFile_edit.setText(
            self.expertUserRegressionFile_edit.text()
        )
        self.wizardErrorEnvelope_edit.setValue(self.doubleSpinBox.value())
        self.activateWizardRSAnalysis()

        self.unfreeze()

    def activateExpertRSAnalysis(self):
        self.output_combo.setEnabled(True)

        # restore/disable RS validate GUI components
        self.RS_combo1.setEnabled(True)
        rs = self.RS_combo1.currentText()
        if rs.startswith("Polynomial") or rs.startswith("MARS"):
            self.RS_combo2.setEnabled(True)
            rs = self.RS_combo2.currentText()
            enable = rs == ResponseSurfaces.getFullName(ResponseSurfaces.LEGENDRE)
            self.RSLegendre_static.setEnabled(enable)
            self.RSLegendre_spin.setEnabled(enable)
            self.RSValidationGroups_static.setEnabled(True)
            self.RSValidationGroups_spin.setEnabled(True)
        else:
            self.RS_combo2.setEnabled(False)
            self.RSLegendre_static.setEnabled(False)
            self.RSLegendre_spin.setEnabled(False)
            enable = rs == ResponseSurfaces.getFullName(ResponseSurfaces.USER)
            self.expertUserRegression_static.setEnabled(enable)
            self.expertUserRegressionFile_edit.setEnabled(enable)
            self.expertUserRegressionBrowse_button.setEnabled(enable)
            self.RSValidationGroups_static.setEnabled(not enable)
            self.RSValidationGroups_spin.setEnabled(not enable)
        self.RSValidate_button.setEnabled(False)

        # enable RS analysis and visualization
        b = True
        self.RSAnalyze_combo1.setEnabled(b)
        self.RSAnalyze_combo2.setEnabled(b)
        self.RSAnalyze_button.setEnabled(b)
        self.inputPrior_table.setEnabled(b)
        self.RSViz_combo1.setEnabled(b)
        self.RSViz_combo2.setEnabled(b)
        self.RSViz_combo3.setEnabled(b)
        self.RSVizMin_chkbox.setEnabled(b)
        self.RSVizMax_chkbox.setEnabled(b)
        self.RSVizMin_chkbox.setChecked(False)
        self.RSVizMax_chkbox.setChecked(False)
        self.RSVizMin_edit.setEnabled(False)
        self.RSVizMax_edit.setEnabled(False)
        self.RSVizMin_edit.clear()
        self.RSVizMax_edit.clear()

    def deactivateExpertRSAnalysis(self):
        b = False
        self.RSAnalyze_combo1.setEnabled(b)
        self.RSAnalyze_combo1.setCurrentIndex(0)
        self.RSAnalyze_combo2.setEnabled(b)
        # self.RSAnalyze_combo2.clear()
        self.RSAnalyze_button.setEnabled(b)
        self.inputPrior_table.setEnabled(b)
        self.RSViz_combo1.setEnabled(b)
        self.RSViz_combo2.setEnabled(b)
        self.RSViz_combo3.setEnabled(b)
        self.RSViz_combo1.setCurrentIndex(0)
        self.RSViz_combo2.setCurrentIndex(0)
        self.RSViz_combo3.setCurrentIndex(0)
        self.RSVizMin_chkbox.setChecked(b)
        self.RSVizMax_chkbox.setChecked(b)
        self.RSVizMin_chkbox.setEnabled(b)
        self.RSVizMax_chkbox.setEnabled(b)
        self.RSVizMin_edit.clear()
        self.RSVizMax_edit.clear()
        self.RSVizMin_edit.setEnabled(b)
        self.RSVizMax_edit.setEnabled(b)

    def activateRSAnalyze1(self):
        self.initRSAnalyzeCombo1(
            self.RSAnalyze_combo1, self.RSAnalyze_combo2, True, self.samplePDFChosen
        )
        # temporarily disable the table mode change
        self.RSAnalyze_combo2.currentIndexChanged[int].disconnect(
            self.changePriorTableMode
        )
        self.handleRSAnalyzeCombo2(
            self.RSAnalyze_combo1, self.RSAnalyze_combo2, self.samplePDFChosen
        )
        self.RSAnalyze_combo2.currentIndexChanged[int].connect(
            self.changePriorTableMode
        )
        self.pointEval_label.setText("")
        self.changePriorTableMode()
        self.RSAnalyze_button.setEnabled(True)

    def inputPriorTablePDFChanged(self):
        self.samplePDFChosen = self.inputPrior_table.isSamplePDFChosen()
        self.activateRSAnalyze1()
        #        self.handleRSAnalyzeCombo2(self.RSAnalyze_combo1, self.RSAnalyze_combo2,
        #                                   self.samplePDFChosen)
        self.activateRSAnalyzeButton()

    def changePriorTableMode(self):
        self.disableTableSignals = True
        if self.RSAnalyze_combo1.currentText() != "Point Evaluation":
            self.inputPrior_table.setRSEvalMode(False)
        mode = self.RSAnalyze_combo2.currentText() == "Epistemic-Aleatory"
        # if mode != self.epistemicMode: # Change in mode
        if True:
            self.inputPrior_table.setAleatoryEpistemicMode(mode)
            self.epistemicMode = mode
        if self.RSAnalyze_combo1.currentText() == "Point Evaluation":
            self.inputPrior_table.setRSEvalMode(True)

    def activateRSAnalyzeButton(self):

        rs = self.getExpertRS()
        if rs is None:
            self.RSAnalyze_button.setEnabled(False)
            return False
        else:
            if self.inputPrior_table.checkValidInputs()[0]:
                self.RSAnalyze_button.setEnabled(True)
                return True
            else:
                self.RSAnalyze_button.setEnabled(False)
                return False

    def enableRSAnalyze(self, b):
        self.output_combo.setEnabled(b)
        self.RSAnalyze_combo1.setEnabled(b)
        if self.RSAnalyze_combo2.count() > 0:
            self.RSAnalyze_combo2.setEnabled(b)
        else:
            self.RSAnalyze_combo2.setEnabled(False)
        self.RSAnalyze_button.setEnabled(b)

    def expertRSAnalyze(self):

        # check arguments
        if not self.activateRSAnalyzeButton():
            return

        self.enableRSAnalyze(False)
        rs = self.getExpertRS()
        epistemicNames, epistemicIndices = self.inputPrior_table.getEpistemicVariables()
        evars = [indx + 1 for indx in epistemicIndices]
        self.RSAnalyze(
            self.output_combo,
            self.RSAnalyze_combo1,
            self.RSAnalyze_combo2,
            self.RSLegendre_spin,
            self.expertUserRegressionFile_edit,
            rs,
            self.inputPrior_table.getTableValues(),
            evars,
            self.RSMarsBasis_spin,
            self.RSMarsDegree_spin,
        )

        self.enableRSAnalyze(True)

    def activateRSVizMinEdit(self):
        if self.RSVizMin_chkbox.isChecked():
            self.RSVizMin_edit.setEnabled(True)
        else:
            self.RSVizMin_edit.setEnabled(False)

    def activateRSVizMaxEdit(self):
        if self.RSVizMax_chkbox.isChecked():
            self.RSVizMax_edit.setEnabled(True)
        else:
            self.RSVizMax_edit.setEnabled(False)

    def activateRSVizButton(self):

        # TO DO: activate based on valid min/max values if checkboxes are checked

        cond1 = self.RSVizCombosUnique(
            self.RSViz_combo1, self.RSViz_combo2, self.RSViz_combo3
        )

        # get min/max
        vmin = True
        vmax = True
        if self.RSVizMin_chkbox.isChecked():
            vmin = self.isnumeric(self.RSVizMin_edit.text())
        if self.RSVizMax_chkbox.isChecked():
            vmax = self.isnumeric(self.RSVizMin_edit.text())
        cond2 = vmin and vmax

        if cond1 and cond2:
            self.RSViz_button.setEnabled(True)
            return True
        else:
            self.RSViz_button.setEnabled(False)
            return False

    def enableRSViz(self, b):
        self.output_combo.setEnabled(b)
        self.RSViz_combo1.setEnabled(b)
        self.RSViz_combo2.setEnabled(b)
        self.RSViz_combo3.setEnabled(b)
        self.RSVizMin_chkbox.setEnabled(b)
        self.RSVizMax_chkbox.setEnabled(b)
        if self.RSVizMin_chkbox.isChecked():
            self.RSVizMin_edit.setEnabled(b)
        if self.RSVizMax_chkbox.isChecked():
            self.RSVizMax_edit.setEnabled(b)
        self.RSViz_button.setEnabled(b)

    def expertRSViz(self):

        # check arguments
        if not self.activateRSVizButton():
            return

        self.enableRSViz(False)

        # get output
        y = self.output_combo.currentIndex()

        # get min/max
        ymax = numpy.inf
        ymin = -ymax
        if self.RSVizMin_chkbox.isChecked():
            ymin = float(self.RSVizMin_edit.text())
        if self.RSVizMax_chkbox.isChecked():
            ymax = float(self.RSVizMax_edit.text())

        # get RS
        rs = self.getExpertRS()

        rsOptions = None
        if rs == ResponseSurfaces.getFullName(ResponseSurfaces.LEGENDRE):
            rsOptions = self.RSLegendre_spin.value()
        elif rs.startswith("MARS"):
            rsOptions = {
                "marsBases": self.RSMarsBasis_spin.value(),
                "marsInteractions": self.RSMarsDegree_spin.value(),
            }

        self.RSViz(
            y,
            self.RSViz_combo1,
            self.RSViz_combo2,
            self.RSViz_combo3,
            rs,
            rsOptions,
            ymin,
            ymax,
            userRegressionFile=self.expertUserRegressionFile_edit.text(),
        )

        self.enableRSViz(True)

    def expertInfer(self):
        self.infer(False)
