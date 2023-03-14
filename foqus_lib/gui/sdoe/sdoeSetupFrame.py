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
import platform
import os
import logging
import copy
import time
import pandas as pd
from datetime import datetime
from foqus_lib.gui.sdoe.updateSDOEModelDialog import *
from foqus_lib.gui.sdoe.sdoeSimSetup import *
from foqus_lib.gui.sdoe.odoeSimSetup import *
from foqus_lib.gui.uq import RSCombos
from foqus_lib.gui.uq.uqDataBrowserFrame import uqDataBrowserFrame
from foqus_lib.framework.uq.DataProcessor import *
from foqus_lib.framework.uq.RSValidation import *
from foqus_lib.framework.uq.RSAnalyzer import *
from foqus_lib.framework.uq.Common import *
from foqus_lib.framework.uq.LocalExecutionModule import *
from foqus_lib.framework.sampleResults.results import Results

from foqus_lib.framework.sdoe import df_utils, odoeu, sdoe
from .sdoePreview import sdoePreview
from foqus_lib.gui.common.InputPriorTable import InputPriorTable

from PyQt5 import QtCore, uic, QtGui
from PyQt5.QtWidgets import (
    QStyledItemDelegate,
    QApplication,
    QTableWidgetItem,
    QPushButton,
    QStyle,
    QDialog,
    QMessageBox,
    QMenu,
    QAbstractItemView,
    QCheckBox,
)
from PyQt5.QtCore import QCoreApplication, QSize, QRect, QEvent
from PyQt5.QtGui import QCursor

from PyQt5 import uic

mypath = os.path.dirname(__file__)
_sdoeSetupFrameUI, _sdoeSetupFrame = uic.loadUiType(
    os.path.join(mypath, "sdoeSetupFrame_UI.ui")
)


class sdoeSetupFrame(_sdoeSetupFrame, _sdoeSetupFrameUI):
    runsFinishedSignal = QtCore.pyqtSignal()
    addDataSignal = QtCore.pyqtSignal(SampleData)
    changeDataSignal = QtCore.pyqtSignal(SampleData)
    addPriorSignal = QtCore.pyqtSignal(SampleData)
    addCandidateSignal = QtCore.pyqtSignal(SampleData)
    changeCandidateSignal = QtCore.pyqtSignal(SampleData)
    addEvalSignal = QtCore.pyqtSignal(SampleData)
    changeEvalSignal = QtCore.pyqtSignal(SampleData)
    format = "%.5f"  # numeric format for table entries in UQ Toolbox
    drawDataDeleteTable = True  # flag to track whether delete table needs to be redrawn

    numberCol = 0
    selCol = 1
    typeCol = 2
    setupCol = 3
    nameCol = 4
    rs1Col = 5
    rs2Col = 6
    rsValCol = 7
    rsConfCol = 8
    impCol = 9

    descriptorCol = 0
    viewCol = 1

    indexCol = 0
    selectCol = 1
    fileCol = 2
    visualizeCol = 3

    imputedData = False
    dname = os.path.join(os.getcwd(), "SDOE_files")
    odoe_dname = os.path.join(os.getcwd(), "ODOE_files")

    # This delegate is used to make the checkboxes in the delete table centered
    class MyItemDelegate(QStyledItemDelegate):
        def paint(self, painter, option, index):
            if index.row() == 0 or index.column() == 0:
                textMargin = (
                    QApplication.style().pixelMetric(QStyle.PM_FocusFrameHMargin) + 1
                )
                newRect = QStyle.alignedRect(
                    option.direction,
                    Qt.AlignCenter,
                    QSize(
                        option.decorationSize.width() + 5,
                        option.decorationSize.height(),
                    ),
                    QRect(
                        option.rect.x() + textMargin,
                        option.rect.y(),
                        option.rect.width() - (2 * textMargin),
                        option.rect.height(),
                    ),
                )
                option.rect = newRect
            QStyledItemDelegate.paint(self, painter, option, index)

        def editorEvent(self, event, model, option, index):
            # make sure that the item is checkable
            flags = model.flags(index)
            if not (flags & Qt.ItemIsUserCheckable) or not (flags & Qt.ItemIsEnabled):
                return False
            # make sure that we have a check state
            value = index.data(Qt.CheckStateRole)
            if value is None:
                return False
            # make sure that we have the right event type
            if event.type() == QEvent.MouseButtonRelease:
                textMargin = (
                    QApplication.style().pixelMetric(QStyle.PM_FocusFrameHMargin) + 1
                )
                checkRect = QStyle.alignedRect(
                    option.direction,
                    Qt.AlignCenter,
                    option.decorationSize,
                    QRect(
                        option.rect.x() + (2 * textMargin),
                        option.rect.y(),
                        option.rect.width() - (2 * textMargin),
                        option.rect.height(),
                    ),
                )
                if not checkRect.contains(event.pos()):
                    return False
            elif event.type() == QEvent.KeyPress:
                if event.key() != Qt.Key_Space and event.key() != Qt.Key_Select:
                    return False
            else:
                return False

            if int(value) == Qt.Checked:
                state = Qt.Unchecked
            else:
                state = Qt.Checked

            return model.setData(index, state, Qt.CheckStateRole)

    def __init__(self, dat, parent=None):
        super(sdoeSetupFrame, self).__init__(parent=parent)
        self.setupUi(self)
        self.dat = dat
        LocalExecutionModule.session = dat
        self.filterWidget = uqDataBrowserFrame(self)
        self.filterWidget.indicesSelectedSignal.connect(self.createFilteredEnsemble)
        self.filterFrame.setLayout(QStackedLayout(self.filterFrame))
        self.filterFrame.layout().addWidget(self.filterWidget)
        self.sdoePages.setCurrentIndex(0)

        # Set up simulation ensembles section
        self.sdoe_radioButton.clicked.connect(self.checkMode)
        self.odoe_radioButton.clicked.connect(self.checkMode)
        self.addSimulationButton.clicked.connect(self.addSimulation)
        self.addSimulationButton.setEnabled(True)
        self.addDataSignal.connect(self.addDataToSimTable)
        self.addPriorSignal.connect(self.addInputPrior)
        self.addCandidateSignal.connect(self.addDataToCandTable)
        self.loadFileButton.clicked.connect(self.loadSimulation)
        self.loadFileButton.setEnabled(True)
        self.cloneButton.clicked.connect(self.cloneSimulation)
        self.cloneButton.setEnabled(False)
        self.deleteButton.clicked.connect(self.deleteSimulation)
        self.deleteButton.setEnabled(False)
        self.saveButton.clicked.connect(self.saveSimulation)
        self.saveButton.setEnabled(False)
        self.confirmButton.clicked.connect(self.confirmEnsembles)
        self.confirmButton.setEnabled(False)

        self.filesTable.resizeColumnsToContents()
        self.filesTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.filesTable.itemSelectionChanged.connect(self.simSelected)
        self.filesTable.cellChanged.connect(self.simDescriptionChanged)
        # TODO pylint: disable=undefined-variable
        self.changeDataSignal.connect(lambda data: self.changeDataInSimTable(data, row))
        self.changeCandidateSignal.connect(
            lambda data: self.changeDataInCandTable(data, row)
        )
        self.changeEvalSignal.connect(
            lambda data: self.changeDataInEvalTable(data, row)
        )
        # TODO pylint: enable=undefined-variable

        # Set up Ensemble Aggregation section
        self.aggFilesTable.setEnabled(False)
        self.backSelectionButton.clicked.connect(self.backToSelection)
        self.backSelectionButton.setEnabled(False)
        self.analyzeButton.setEnabled(False)

        # Set up UQ toolbox
        self.dataTabs.setEnabled(False)

        # Perform all connects here
        # ........ DATA PAGE ..............
        self.dataTabs.setCurrentIndex(0)
        self.dataTabs.currentChanged[int].connect(self.getDataTab)
        self.deletionButton.clicked.connect(self.delete)
        self.changeButton.clicked.connect(self.updateOutputValues)
        self.changeButton.hide()
        self.resetButton.clicked.connect(self.redrawDeleteTable)
        self.deleteTable.itemChanged.connect(self.deleteTableCellChanged)
        self.deleteTable.verticalScrollBar().valueChanged.connect(
            self.scrollDeleteTable
        )
        self.delegate = sdoeSetupFrame.MyItemDelegate(self)
        self.deleteTable.setItemDelegate(self.delegate)

        # Create SDOE & ODOE directories
        Common.initFolder(self.dname)
        Common.initFolder(self.odoe_dname)

        # Initialize ODoE Page
        self.odoe_inputs_groupBox.setEnabled(False)
        self.odoe_outputs_groupBox.setEnabled(False)
        self.odoe_design_groupBox.setEnabled(False)
        self.odoe_setup_groupBox.setEnabled(False)
        self.odoe_data = None
        self.odoe_priorData = None
        self.resultMessage = None
        self.loadtrainData_button.clicked.connect(self.loadRStrainData)
        self.confirmInputs_button.clicked.connect(self.confirmInputs)
        self.outputCol_index = {"sel": 0, "name": 1, "rs1": 2, "rs2": 3}
        self.outputColumnHeaders = [
            self.output_table.horizontalHeaderItem(i).text()
            for i in range(self.output_table.columnCount())
        ]
        self.outputMeans = None
        self.outputStdDevs = None

        self.yesCand_radioButton.clicked.connect(self.checkCandFile)
        self.noCand_radioButton.clicked.connect(self.checkCandFile)
        self.generateCandidate_button.clicked.connect(self.generateCandidate)
        self.loadCandidate_button.clicked.connect(self.loadCandidate)

        self.yesEval_radioButton.clicked.connect(self.checkEvalFile)
        self.noEval_radioButton.clicked.connect(self.checkEvalFile)
        self.loadEval_button.clicked.connect(self.loadEval)

        self.odoe_cand_table.resizeColumnsToContents()
        self.odoe_cand_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.odoe_cand_table.itemSelectionChanged.connect(self.candSelected)
        self.deleteSelection_button.clicked.connect(self.deleteSelection)

        self.odoe_eval_table.resizeColumnsToContents()
        self.odoe_eval_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.odoe_eval_table.itemSelectionChanged.connect(self.evalSelected)
        self.deleteEval_button.clicked.connect(self.deleteEval)

        self.confirmCandidates_button.clicked.connect(self.confirmCandidates)
        self.validateRS_button.clicked.connect(self.validateRS)
        self.confirmRS_button.clicked.connect(self.confirmRS)
        self.restarts_comboBox.setMinimumContentsLength(4)
        self.runOdoe_button.clicked.connect(self.runOdoe)

    # Check if SDoE or ODoE
    def checkMode(self):
        if self.sdoe_radioButton.isChecked():
            self.sdoePages.setCurrentIndex(0)
        else:
            self.sdoePages.setCurrentIndex(1)

    # Go through list of ensembles
    def confirmEnsembles(self):
        QApplication.processEvents()
        self.updateAggTable()
        self.aggFilesTable.setEnabled(True)
        self.backSelectionButton.setEnabled(True)
        self.analyzeButton.clicked.connect(self.launchSdoe)
        self.analyzeButton.setEnabled(True)
        self.filesTable.setEnabled(False)
        self.addSimulationButton.setEnabled(False)
        self.loadFileButton.setEnabled(False)
        self.cloneButton.setEnabled(False)
        self.deleteButton.setEnabled(False)
        self.saveButton.setEnabled(False)
        self.confirmButton.setEnabled(False)
        self.dataTabs.setEnabled(False)
        QApplication.processEvents()

    def on_combobox_changed(self):
        self.confirmButton.setEnabled(self.hasCandidates())

    def on_checkbox_changed_sdoe(self):
        self.confirmButton.setEnabled(self.hasCandidates())

    def getEnsembleList(self):
        cand_list = []
        hist_list = []
        numFiles = len(self.dat.sdoeSimList)
        for i in range(numFiles):
            if (
                str(self.filesTable.cellWidget(i, self.typeCol).currentText())
                == "Candidate"
                and self.filesTable.cellWidget(i, self.selCol).isChecked()
            ):
                cand_list.append(self.dat.sdoeSimList[i])
            elif (
                str(self.filesTable.cellWidget(i, self.typeCol).currentText())
                == "Previous Data"
                and self.filesTable.cellWidget(i, self.selCol).isChecked()
            ):
                hist_list.append(self.dat.sdoeSimList[i])
        return cand_list, hist_list  # returns sample data structures

    def aggregateEnsembleList(self):
        cand_list, hist_list = self.getEnsembleList()

        cand_csv_list = []
        for cand in cand_list:
            cand_path = os.path.join(self.dname, cand.getModelName())
            if "imputed" in cand_path:
                self.imputedData = True
            else:
                self.imputedData = False
            if not os.path.exists(cand_path):
                cand.writeToCsv(cand_path, inputsOnly=True)
            cand_csv_list.append(cand_path)

        hist_csv_list = []
        for hist in hist_list:
            hist_path = os.path.join(self.dname, hist.getModelName())
            if "imputed" in hist_path:
                self.imputedData = True
            else:
                self.imputedData = False
            if not os.path.exists(hist_path):
                hist.writeToCsv(hist_path, inputsOnly=True)
            hist_csv_list.append(hist_path)

        cand_agg, hist_agg = df_utils.check(cand_csv_list, hist_csv_list)
        return cand_agg, hist_agg

    def createAggData(self):
        cand_agg, hist_agg = self.aggregateEnsembleList()  # these are dfs
        cand_agg.insert(0, "__id", range(cand_agg.shape[0]), True)

        cand_fname = os.path.join(self.dname, "aggregate_candidates.csv")
        df_utils.write(cand_fname, cand_agg)
        candidateData = LocalExecutionModule.readSampleFromCsvFile(
            cand_fname, askForNumInputs=False
        )

        hist_fname = os.path.join(self.dname, "aggregate_previousData.csv")
        if len(hist_agg) == 0:
            historyData = None
        else:
            hist_agg.insert(
                0,
                "__id",
                range(cand_agg.shape[0], cand_agg.shape[0] + hist_agg.shape[0]),
                True,
            )
            df_utils.write(hist_fname, hist_agg)
            historyData = LocalExecutionModule.readSampleFromCsvFile(
                hist_fname, askForNumInputs=False
            )

        return candidateData, historyData

    def backToSelection(self):
        QApplication.processEvents()
        self.aggFilesTable.setEnabled(False)
        self.backSelectionButton.setEnabled(False)
        self.analyzeButton.setEnabled(False)
        self.filesTable.setEnabled(True)
        self.addSimulationButton.setEnabled(True)
        self.loadFileButton.setEnabled(True)
        self.cloneButton.setEnabled(True)
        self.deleteButton.setEnabled(True)
        self.saveButton.setEnabled(True)
        self.dataTabs.setEnabled(True)
        self.confirmButton.setEnabled(self.hasCandidates())
        QApplication.processEvents()

    def refresh(self):
        numSims = len(self.dat.sdoeSimList)
        self.filesTable.setRowCount(numSims)
        for i in range(numSims):
            self.updateSimTableRow(i)

        if numSims == 0:
            self.dataTabs.setEnabled(False)
            self.confirmButton.setEnabled(False)

    def simSelected(self):
        selectedIndexes = self.filesTable.selectedIndexes()
        if not selectedIndexes:
            self.cloneButton.setEnabled(False)
            self.deleteButton.setEnabled(False)
            self.saveButton.setEnabled(False)
            self.dataTabs.setEnabled(False)
            self.deleteTable.clear()
            self.deleteTable.setRowCount(0)
            self.deleteTable.setColumnCount(0)
            return
        self.dataTabs.setEnabled(False)  # Prevent uq toolbox changes
        self.cloneButton.setEnabled(True)
        self.deleteButton.setEnabled(True)
        self.saveButton.setEnabled(True)

        row = selectedIndexes[0].row()
        _sim = self.dat.sdoeSimList[row]

        self.freeze()
        self.initUQToolBox()
        self.dataTabs.setEnabled(True)
        self.unfreeze()
        QCoreApplication.processEvents()

    def simDescriptionChanged(self, row, column):
        if column == sdoeSetupFrame.nameCol:
            sim = self.dat.sdoeSimList[row]
            item = self.filesTable.item(row, column)
            newName = item.text()
            sim.setModelName(newName)

    def addSimulation(self):
        updateDialog = updateSDOEModelDialog(self.dat, self)
        result = updateDialog.exec_()
        if result == QDialog.Rejected:
            return

        simDialog = sdoeSimSetup(
            # WHY self.dat.model is set in updateSDOEModelDialog(),
            # but this is not detected by pylint
            self.dat.model,  # pylint: disable=no-member
            self.dat,
            returnDataSignal=self.addDataSignal,
            parent=self,
        )
        simDialog.show()

    def cloneSimulation(self):
        # Get selected row
        row = self.filesTable.selectedIndexes()[0].row()
        sim = copy.deepcopy(self.dat.sdoeSimList[row])  # Create copy of sim
        sim.clearRunState()
        sim.turbineSession = None
        sim.turbineJobIds = []
        self.dat.sdoeSimList.append(sim)  # Add to simulation list
        res = Results()
        res.sdoe_add_result(sim)
        self.dat.sdoeFilterResultsList.append(sim)

        # Update table
        self.updateSimTable()

    def loadSimulation(self):

        self.freeze()

        # Get file name
        if platform.system() == "Windows":
            _allFiles = "*.*"
        else:
            _allFiles = "*"
        fileName, selectedFilter = QFileDialog.getOpenFileName(
            self, "Open Ensemble", "", "CSV (Comma delimited) (*.csv)"
        )
        if len(fileName) == 0:
            self.unfreeze()
            return

        if fileName.endswith(".csv"):
            data = LocalExecutionModule.readSampleFromCsvFile(fileName, False)
        else:
            try:
                data = LocalExecutionModule.readSampleFromPsuadeFile(fileName)
            except:
                import traceback

                traceback.print_exc()
                QMessageBox.critical(
                    self,
                    "Incorrect format",
                    "File does not have the correct format! Please consult the users manual "
                    "about the format.",
                )
                logging.getLogger("foqus." + __name__).exception(
                    "Error loading psuade file."
                )
                self.unfreeze()
                return
        dataInfo = self.dataInfo(data)
        if dataInfo:
            QMessageBox.critical(
                self,
                "Incorrect format",
                "File has missing values in one or more of the input columns.\n"
                "Please correct the issue or load a different file.",
            )
            self.unfreeze()
            return
        else:
            data.setSession(self.dat)
            self.dat.sdoeSimList.append(data)

            res = Results()
            res.sdoe_add_result(data)
            self.dat.sdoeFilterResultsList.append(res)
            shutil.copy(fileName, self.dname)

            # Update table
            self.updateSimTable()
            self.dataTabs.setEnabled(True)
            self.unfreeze()

    def updateSimTable(self):
        QApplication.processEvents()
        # Update table
        numSims = len(self.dat.sdoeSimList)
        self.filesTable.setRowCount(numSims)
        self.updateSimTableRow(numSims - 1)
        self.filesTable.selectRow(numSims - 1)
        self.confirmButton.setEnabled(self.hasCandidates())
        QApplication.processEvents()

    def updateAggTable(self):
        self.updateAggTableRow(0)
        self.updateAggTableRow(1)
        self.updateAggTableRow(2)

    def deleteSimulation(self):
        QApplication.processEvents()
        # Get selected row
        row = self.filesTable.selectedIndexes()[0].row()

        # Delete simulation
        self.dat.sdoeSimList.pop(row)
        self.dat.sdoeFilterResultsList.pop(row)
        self.dataTabs.setCurrentIndex(0)
        self.refresh()
        QApplication.processEvents()
        numSims = len(self.dat.sdoeSimList)
        if numSims > 0:
            if row >= numSims:
                self.filesTable.selectRow(numSims - 1)
                row = numSims - 1
            _sim = self.dat.sdoeSimList[row]
        self.confirmButton.setEnabled(self.hasCandidates())
        QApplication.processEvents()

    def saveSimulation(self):
        psuadeFilter = "Psuade Files (*.dat)"
        csvFilter = "Comma-Separated Values (Excel) (*.csv)"

        # Get selected row
        row = self.filesTable.selectedIndexes()[0].row()

        sim = self.dat.sdoeSimList[row]
        fileName, selectedFilter = QFileDialog.getSaveFileName(
            self, "File to Save Ensemble", "", psuadeFilter + ";;" + csvFilter
        )
        if fileName == "":
            return
        if selectedFilter == psuadeFilter:
            sim.writeToPsuade(fileName)
        else:
            sim.writeToCsv(fileName, inputsOnly=True)

    def editSim(self):
        sender = self.sender()
        row = sender.property("row")

        self.changeDataSignal.disconnect()
        self.changeDataSignal.connect(lambda data: self.changeDataInSimTable(data, row))

        previewData = self.dat.sdoeSimList[row]
        hname = None
        usf = None
        nusf = None
        irsf = None
        scatterLabel = "Candidates"
        nImpPts = previewData.getNumImputedPoints()
        dialog = sdoePreview(
            previewData, hname, self.dname, usf, nusf, irsf, scatterLabel, nImpPts, self
        )
        dialog.show()

    def editAgg(self):
        sender = self.sender()
        _row = sender.property("row")
        candidateData, historyData = self.createAggData()

        previewData = candidateData
        if historyData is not None:
            hname = os.path.join(self.dname, historyData.getModelName())
        else:
            hname = None
        usf = None
        nusf = None
        irsf = None
        scatterLabel = "Candidates"
        nImpPts = 0
        dialog = sdoePreview(
            previewData, hname, self.dname, usf, nusf, irsf, scatterLabel, nImpPts, self
        )
        dialog.show()

    def rsVal(self):
        QApplication.processEvents()
        self.freeze()
        sender = self.sender()
        row = sender.property("row")

        self.changeDataSignal.disconnect()
        self.changeDataSignal.connect(lambda data: self.changeDataInSimTable(data, row))

        data = copy.deepcopy(self.dat.sdoeSimList[row])
        numInputs = data.getNumInputs()
        indices_raw = np.argwhere(np.isnan(data.getInputData()))
        indices_del = []
        for ind in indices_raw:
            indices_del.append(ind[0])
        indices = []
        for ind in range(data.getInputData().shape[0]):
            if ind not in indices_del:
                indices.append(ind)
        data = data.getSubSample(indices)
        names = data.getInputNames()
        output_data = np.transpose(
            np.array(data.getInputData()[:, -1], ndmin=2, dtype=float)
        )
        data.deleteInputs([numInputs - 1])
        data.model.numOutputs = 1
        data.model.setOutputNames(names[-1])
        data.setOutputData(output_data)
        y = 1
        rs1 = self.filesTable.cellWidget(row, self.rs1Col)
        rs2 = self.filesTable.cellWidget(row, self.rs2Col)
        rs = RSCombos.lookupRS(rs1, rs2)

        if rs.startswith("MARS"):
            rsOptions = {
                "marsBases": min([100, data.getNumSamples()]),
                "marsInteractions": min([8, data.getNumVarInputs()]),
            }
        else:
            rsOptions = None

        genRSCode = True

        rsv = RSValidation(
            data,
            y,
            rs,
            rsOptions=rsOptions,
            genCodeFile=genRSCode,
            odoe=True,
            error_tol_percent=5,
        )
        _mfile = rsv.analyze()

        msgBox = QMessageBox()
        msgBox.setWindowTitle("Response Surface Validation Plot")
        msgBox.setText(
            "Check the response surface validation plot."
            "If the generated response surface satisfy your needs, please confirm."
            "If not, please select a new response surface and validate again."
        )
        msgBox.exec_()
        self.filesTable.cellWidget(row, self.rsConfCol).setEnabled(True)
        self.unfreeze()
        QApplication.processEvents()

    def rsConf(self):
        QApplication.processEvents()
        sender = self.sender()
        row = sender.property("row")

        self.changeDataSignal.disconnect()
        self.changeDataSignal.connect(lambda data: self.changeDataInSimTable(data, row))

        self.filesTable.cellWidget(row, self.impCol).setEnabled(True)

        QApplication.processEvents()

    def dataImputation(self):
        QApplication.processEvents()
        sender = self.sender()
        row = sender.property("row")

        self.changeDataSignal.disconnect()
        self.changeDataSignal.connect(lambda data: self.changeDataInSimTable(data, row))

        data = copy.deepcopy(self.dat.sdoeSimList[row])
        numInputs = data.getNumInputs()
        indices_raw = np.argwhere(np.isnan(data.getInputData()))
        indices = []
        for ind in indices_raw:
            indices.append(ind[0])
        data = data.getSubSample(indices)
        names = data.getInputNames()
        output_data = np.transpose(
            np.array(data.getInputData()[:, -1], ndmin=2, dtype=float)
        )
        data.deleteInputs([numInputs - 1])
        data.model.numOutputs = 1
        data.model.setOutputNames(names[-1])
        data.setOutputData(output_data)

        fname = Common.getLocalFileName(
            RSAnalyzer.dname, data.getModelName().split()[0], ".dat"
        )

        eval_fname = os.path.join(RSAnalyzer.dname, "rseval.dat")
        RSAnalyzer.writeRSsample(eval_fname, data.getInputData(), row=True, sdoe=True)

        y = 1
        rs1 = self.filesTable.cellWidget(row, self.rs1Col)
        rs2 = self.filesTable.cellWidget(row, self.rs2Col)
        rs = RSCombos.lookupRS(rs1, rs2)

        ytest = sdoe.dataImputation(fname, y, rs, eval_fname)
        testInput, testOutput, _numInputs, _numOutputs = sdoe.readEvalSample(ytest)

        trainSet = LocalExecutionModule.readSampleFromPsuadeFile(fname)
        trainInput = trainSet.getInputData()
        trainOutput = trainSet.getOutputData()
        colNames = trainSet.getInputNames() + trainSet.getOutputNames()
        trainData = np.concatenate((trainInput, trainOutput), axis=1)
        temp = np.concatenate((testInput, testOutput), axis=1)
        testData = np.delete(temp, -1, axis=1)
        nImpPts = testData.shape[0]
        finalData = np.concatenate((trainData, testData), axis=0)
        df = pd.DataFrame(finalData, columns=colNames)
        fileName = os.path.join(
            self.dname,
            data.getModelName().split(".csv")[0] + "_{}_imputed.csv".format(rs),
        )
        df_utils.write(fileName, df)

        data = LocalExecutionModule.readSampleFromCsvFile(fileName, False)
        data.setSession(self.dat)
        data.setNumImputedPoints(nImpPts)
        self.dat.sdoeSimList.append(data)

        res = Results()
        res.sdoe_add_result(data)
        self.dat.sdoeFilterResultsList.append(res)

        # Update table
        self.updateSimTable()
        self.dataTabs.setEnabled(True)
        self.unfreeze()

        QApplication.processEvents()

    def hasCandidates(self):
        cand_list, hist_list = self.getEnsembleList()
        return len(cand_list) > 0

    def missingData(self, data):
        arr = data.getInputData()
        return np.sum(np.isnan(arr)) > 0

    def dataInfo(self, data):
        arr = data.getInputData()
        if np.sum(np.isnan(arr)) > 0:
            warningMessage = "{} candidate file info:\n\n".format(data.getModelName())
            for i in range(data.getNumInputs()):
                warningMessage += 'Missing values for column "{}": {}/{}\n'.format(
                    data.getInputNames()[i],
                    sum(np.isnan(arr)[:, i]),
                    data.getNumSamples(),
                )
            msgBox = QMessageBox()
            msgBox.setText(warningMessage)
            msgBox.exec_()
            for i in range(5, 10):
                self.filesTable.setColumnHidden(i, False)
        else:
            for i in range(5, 10):
                self.filesTable.setColumnHidden(i, True)

        return np.sum(np.isnan(arr[:, 0:-1])) > 0

    def addDataToSimTable(self, data):
        if data is None:
            return
        self.dat.sdoeSimList.append(data)
        res = Results()
        res.sdoe_add_result(data)
        self.dat.sdoeFilterResultsList.append(res)

        self.updateSimTable()

    def changeDataInSimTable(self, data, row):
        if data is None:
            return
        self.dat.sdoeSimList[row] = data
        res = Results()
        res.sdoe_add_result(data)
        self.dat.sdoeFilterResultsList[row] = res

        self.updateSimTableRow(row)

    def updateSimTableRow(self, row):
        data = self.dat.sdoeSimList[row]
        item = self.filesTable.item(row, self.numberCol)
        if item is None:
            item = QTableWidgetItem()
        item.setText(str(row + 1))
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        flags = item.flags()
        mask = ~Qt.ItemIsEditable
        item.setFlags(flags & mask)
        self.filesTable.setItem(row, self.numberCol, item)

        # create checkboxes for select column
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        self.filesTable.setCellWidget(row, self.selCol, checkbox)
        checkbox.setProperty("row", row)
        checkbox.toggled.connect(self.on_checkbox_changed_sdoe)

        # Create combo boxes for type column
        combo = QComboBox()
        combo.addItems(["Candidate", "Previous Data"])
        self.filesTable.setCellWidget(row, self.typeCol, combo)
        combo.currentTextChanged.connect(self.on_combobox_changed)
        combo.setMinimumContentsLength(13)

        # Setup name column
        item = self.filesTable.item(row, self.nameCol)
        if item is None:
            item = QTableWidgetItem()
        item.setText(data.getModelName())
        self.filesTable.setItem(row, self.nameCol, item)

        # Create view button for setup column
        viewButton = self.filesTable.cellWidget(row, self.setupCol)
        newViewButton = False
        if viewButton is None:
            newViewButton = True
            viewButton = QPushButton()
            viewButton.setText("View")
            viewButton.setToolTip("View and plot the candidate set or previous data.")

        viewButton.setProperty("row", row)
        if newViewButton:
            viewButton.clicked.connect(self.editSim)
            self.filesTable.setCellWidget(row, self.setupCol, viewButton)

        # add combo boxes for rs1 and rs2 columns
        combo1 = RSCombos.RSCombo1(self)
        combo2 = RSCombos.RSCombo2(self)
        legendreSpin = RSCombos.LegendreSpinBox(self)
        marsBasisSpin = None
        marsInteractionSpin = None

        legendreSpin.init(data)
        combo2.init(data, legendreSpin, useShortNames=True, odoe=True)
        combo2.setMinimumContentsLength(10)
        combo1.init(
            data,
            combo2,
            True,
            True,
            marsBasisSpin=marsBasisSpin,
            marsDegreeSpin=marsInteractionSpin,
            odoe=True,
        )

        combo1.setProperty("row", row)
        combo2.setProperty("row", row)

        combo1.setEnabled(self.missingData(data))
        combo2.setEnabled(self.missingData(data))

        self.filesTable.setCellWidget(row, self.rs1Col, combo1)
        self.filesTable.setCellWidget(row, self.rs2Col, combo2)

        # Create validate RS button for RS Validation column
        rsValButton = self.filesTable.cellWidget(row, self.rsValCol)
        newRsValButton = False
        if rsValButton is None:
            newRsValButton = True
            rsValButton = QPushButton()
            rsValButton.setText("Validate RS")
            rsValButton.setToolTip("Validate the selected response surface.")

        rsValButton.setProperty("row", row)
        if newRsValButton:
            rsValButton.clicked.connect(self.rsVal)
            rsValButton.setEnabled(self.missingData(data))
            self.filesTable.setCellWidget(row, self.rsValCol, rsValButton)

        # Create confirm RS button for RS Confirmation column
        rsConfButton = self.filesTable.cellWidget(row, self.rsConfCol)
        newRsConfButton = False
        if rsConfButton is None:
            newRsConfButton = True
            rsConfButton = QPushButton()
            rsConfButton.setText("Confirm RS")
            rsConfButton.setToolTip(
                "If you are happy with the response surface, please confirm."
            )

        rsConfButton.setProperty("row", row)
        if newRsConfButton:
            rsConfButton.clicked.connect(self.rsConf)
            rsConfButton.setEnabled(False)
            self.filesTable.setCellWidget(row, self.rsConfCol, rsConfButton)

        # Create data imputation button for data imputation column
        impButton = self.filesTable.cellWidget(row, self.impCol)
        newImpButton = False
        if impButton is None:
            newImpButton = True
            impButton = QPushButton()
            impButton.setText("Impute")
            impButton.setToolTip("Impute missing data and create a new completed set.")

        impButton.setProperty("row", row)
        if newImpButton:
            impButton.clicked.connect(self.dataImputation)
            impButton.setEnabled(False)
            self.filesTable.setCellWidget(row, self.impCol, impButton)

        # Resize table
        self.resizeColumns()
        minWidth = (
            2
            + self.filesTable.columnWidth(0)
            + self.filesTable.columnWidth(1)
            + self.filesTable.columnWidth(2)
            + self.filesTable.columnWidth(3)
        )
        if self.filesTable.verticalScrollBar().isVisible():
            minWidth += self.filesTable.verticalScrollBar().width()
        self.filesTable.setMinimumWidth(minWidth)

    def resizeColumns(self):
        self.filesTable.resizeColumnsToContents()
        self.aggFilesTable.resizeColumnsToContents()

    def updateAggTableRow(self, row):
        viewButton = self.aggFilesTable.cellWidget(row, self.viewCol)
        newViewButton = False
        if viewButton is None:
            newViewButton = True
            viewButton = QPushButton()
            viewButton.setText("View")

        viewButton.setProperty("row", row)
        if newViewButton:
            viewButton.clicked.connect(self.editAgg)
            self.aggFilesTable.setCellWidget(0, self.viewCol, viewButton)

        candidateData, historyData = self.createAggData()

        item = self.aggFilesTable.item(0, self.descriptorCol)
        item.setText(candidateData.getModelName())
        self.aggFilesTable.setItem(0, self.descriptorCol, item)

        item = self.aggFilesTable.item(1, self.descriptorCol)
        if historyData is None:
            item.setText("None")
        else:
            item.setText(historyData.getModelName())
        self.aggFilesTable.setItem(1, self.descriptorCol, item)

        item = self.aggFilesTable.item(2, self.descriptorCol)
        item.setText(self.dname)
        self.aggFilesTable.setItem(2, self.descriptorCol, item)

        combo = QComboBox()
        combo.addItems(
            [
                "Uniform Space Filling (USF)",
                "Non-Uniform Space Filling (NUSF)",
                "Input-Response Space Filling (IRSF)",
            ]
        )
        self.aggFilesTable.setCellWidget(3, self.descriptorCol, combo)
        combo.setEnabled(True)
        if self.imputedData:
            combo.model().item(0).setEnabled(False)
            combo.setCurrentIndex(1)

        combo.setToolTip(
            "<ul>"
            "<li><b>Uniform Space Filling Designs</b> place design points so that they’re evenly spread "
            "out throughout the input space. Use when the goal is to collect information across the "
            "experimental region, without assumptions about which areas of the region are more "
            "important than others. This provides good precision for predicting new results at any new "
            "location in the input space, because data will have been collected close by.</li>"
            "<br>"
            "<li><b>Non-Uniform Space Filling Designs</b> maintain the goal of having design points spread"
            " throughout the input space but add a feature of being able to emphasize some regions "
            "more than others. Use for added flexibility when certain areas of the input space require "
            "more in-depth exploration than others.</li>"
            "</ul>"
        )

        # Resize table
        self.resizeColumns()
        minWidth = (
            2
            + self.aggFilesTable.columnWidth(0)
            + self.aggFilesTable.columnWidth(1)
            + self.aggFilesTable.columnWidth(2)
        )
        if self.aggFilesTable.verticalScrollBar().isVisible():
            minWidth += self.aggFilesTable.verticalScrollBar().width()
        self.aggFilesTable.setMinimumWidth(minWidth)

    def launchSdoe(self):
        candidateData, historyData = self.createAggData()
        dname = self.dname
        if (
            str(self.aggFilesTable.cellWidget(3, self.descriptorCol).currentText())
            == "Uniform Space Filling (USF)"
        ):
            type = "USF"
        elif (
            str(self.aggFilesTable.cellWidget(3, self.descriptorCol).currentText())
            == "Non-Uniform Space "
            "Filling (NUSF)"
        ):
            type = "NUSF"
        elif (
            str(self.aggFilesTable.cellWidget(3, self.descriptorCol).currentText())
            == "Input-Response Space "
            "Filling (IRSF)"
        ):
            type = "IRSF"
        analysis = []

        from .sdoeAnalysisDialog import sdoeAnalysisDialog

        dialog = sdoeAnalysisDialog(
            candidateData, dname, analysis, historyData, type, self
        )
        dialog.exec_()
        dialog.deleteLater()

    def initUQToolBox(self):

        # call this only after a row in simulationTable is selected
        self.initData()
        QCoreApplication.processEvents()
        self.dataTabs.setEnabled(True)
        self.initDelete()
        self.drawDataDeleteTable = False
        QCoreApplication.processEvents()

    def freeze(self):
        QApplication.setOverrideCursor(QCursor(QtCore.Qt.WaitCursor))

    def semifreeze(self):
        QApplication.setOverrideCursor(QCursor(QtCore.Qt.BusyCursor))

    def unfreeze(self):
        QApplication.restoreOverrideCursor()

    @staticmethod
    def isnumeric(str):
        try:
            float(str)
            return True
        except ValueError:
            return False

    # ........ DATA PAGE ...................
    def initData(self):
        self.dataTabs.setCurrentIndex(0)
        self.initFilter()

    def getDataTab(self):
        tabIndex = self.dataTabs.currentIndex()
        deleteIndex = 0

        if tabIndex == deleteIndex:
            if self.drawDataDeleteTable:
                self.initDelete()
                self.drawDataDeleteTable = False

    # ........ DATA PAGE: FILTER TAB ...................
    def initFilter(self):
        self.refreshFilterData()

    def createFilteredEnsemble(self, indices):
        self.freeze()

        # get selected row
        row = self.filesTable.selectedIndexes()[0].row()
        data = self.dat.sdoeSimList[row]

        newdata = data.getSubSample(indices)

        newdata.setModelName(data.getModelName().split(".")[0] + ".filtered")
        newdata.setSession(self.dat)

        # add to simulation table, select new data
        self.dat.sdoeSimList.append(newdata)
        res = Results()
        res.sdoe_add_result(newdata)
        self.dat.sdoeFilterResultsList.append(res)

        self.updateSimTable()

        # reset components
        self.unfreeze()

    def refreshFilterData(self, updateResult=False):
        indexes = self.filesTable.selectedIndexes()
        if len(indexes) == 0:
            return
        row = indexes[0].row()
        data = self.dat.sdoeSimList[row]

        if updateResult or not self.dat.sdoeFilterResultsList:
            if not self.dat.sdoeFilterResultsList:
                self.dat.sdoeFilterResultsList = [None] * len(self.dat.sdoeSimList)
            res = Results()
            res.sdoe_add_result(data)
            self.dat.sdoeFilterResultsList[row] = res
        else:
            res = self.dat.sdoeFilterResultsList[row]

        self.filterWidget.init(self.dat)
        self.filterWidget.setResults(res)
        self.filterWidget.refreshContents()

    # ........ DATA PAGE: DELETE TAB ...................
    def initDelete(self):

        Common.initFolder(DataProcessor.dname)

        self.freeze()

        # get selected row
        row = self.filesTable.selectedIndexes()[0].row()
        data = self.dat.sdoeSimList[row]

        # populate table
        self.inputData = data.getInputData()
        self.outputData = data.getOutputData()
        inputNames = data.getInputNames()
        self.nInputs = data.getNumInputs()
        outputNames = data.getOutputNames()
        self.nOutputs = data.getNumOutputs()
        self.nSamples = data.getNumSamples()
        self.nSamplesAdded = data.getNumSamplesAdded()

        self.isDrawingDeleteTable = True
        self.deleteTable.cellClicked.connect(self.activateDeleteButton)
        self.deleteTable.setColumnCount(self.nInputs + self.nOutputs + 1)
        self.deleteTable.setRowCount(self.nSamples + 1)
        self.deleteTable.setHorizontalHeaderLabels(
            ("Variables",) + inputNames + outputNames
        )
        self.deleteTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.deleteTable.customContextMenuRequested.connect(self.popup)
        self.deleteTable.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.deleteTable.verticalHeader().customContextMenuRequested.connect(self.popup)
        sampleLabels = tuple([str(i) for i in range(1, self.nSamples + 1)])
        self.deleteTable.setVerticalHeaderLabels(("Sample #",) + sampleLabels)
        inputColor = QtGui.QColor(255, 0, 0, 50)  # translucent red
        inputRefinedColor = QtGui.QColor(255, 0, 0, 100)
        mask = ~Qt.ItemIsEditable
        checkboxMask = ~(Qt.ItemIsSelectable | Qt.ItemIsEditable)
        end = self.nSamples

        # Blank corner cell
        item = QTableWidgetItem()
        flags = item.flags()
        item.setFlags(flags & mask)
        self.deleteTable.setItem(0, 0, item)

        self.deleteScrollRow = 1
        if end > 15:
            end = 15
        for r in range(end):
            item = QTableWidgetItem()
            flags = item.flags()
            item.setFlags(flags & checkboxMask)
            item.setCheckState(Qt.Unchecked)
            self.deleteTable.setItem(r + 1, 0, item)

        for c in range(self.nInputs):  # populate input values
            item = QTableWidgetItem()
            flags = item.flags()
            item.setFlags(flags & mask)
            self.deleteTable.setItem(0, c + 1, item)
            for r in range(end):
                item = QTableWidgetItem(self.format % self.inputData[r][c])
                flags = item.flags()
                item.setFlags(flags & mask)
                if r < self.nSamples - self.nSamplesAdded:
                    color = inputColor
                else:
                    color = inputRefinedColor
                item.setBackground(color)
                self.deleteTable.setItem(r + 1, c + 1, item)
        for c in range(self.nOutputs):  # output values populated in redrawDeleteTable()
            item = self.deleteTable.item(0, self.nInputs + c + 1)
            if item is None:
                item = QTableWidgetItem()
                self.deleteTable.setItem(0, self.nInputs + c + 1, item)
            flags = item.flags()
            item.setFlags(flags & mask)
            item.setCheckState(Qt.Unchecked)

            for r in range(end):
                item = self.deleteTable.item(r + 1, self.nInputs + c + 1)
                if item is None:
                    item = QTableWidgetItem()
                    self.deleteTable.setItem(r + 1, self.nInputs + c + 1, item)
        self.redrawDeleteTable()

        self.unfreeze()

    def popup(self, pos):
        menu = QMenu()
        checkAction = menu.addAction("Check selected rows")
        unCheckAction = menu.addAction("Uncheck selected rows")
        action = menu.exec_(self.deleteTable.mapToGlobal(pos))
        check = None
        if action == checkAction:
            check = Qt.Checked
        elif action == unCheckAction:
            check = Qt.Unchecked
        if check is not None:
            self.freeze()
            rows = set(
                [
                    i.row()
                    for i in self.deleteTable.selectionModel().selection().indexes()
                ]
            )
            _nSamples = self.deleteTable.rowCount() - 1
            for r in rows:
                item = self.deleteTable.item(r, 0)
                if item is None:
                    item = QTableWidgetItem()
                    flags = item.flags()
                    mask = ~(Qt.ItemIsSelectable | Qt.ItemIsEditable)
                    item.setFlags(flags & mask)
                    item.setCheckState(check)
                    self.deleteTable.setItem(r, 0, item)
                if item is not None:
                    item.setCheckState(check)
            self.activateDeleteButton(rows.pop(), 0)
            self.unfreeze()

    def scrollDeleteTable(self, first):
        if first >= self.inputData.shape[0]:
            return
        self.isDrawingDeleteTable = True
        if first == 0:
            first = 1
        if first > 1:
            first -= 1
        self.deleteScrollRow = first

        inputColor = QtGui.QColor(255, 0, 0, 50)  # translucent red
        inputRefinedColor = QtGui.QColor(255, 0, 0, 100)
        outputColor = QtGui.QColor(255, 255, 0, 50)  # translucent yellow
        outputRefinedColor = QtGui.QColor(255, 255, 0, 100)  # translucent yellow
        mask = ~Qt.ItemIsEditable
        checkboxMask = ~(Qt.ItemIsSelectable | Qt.ItemIsEditable)
        numRows = self.deleteTable.rowCount()
        end = first + 15
        if end > numRows:
            end = numRows
        for r in range(first, end):
            item = self.deleteTable.item(r, 0)
            if item is None:
                item = QTableWidgetItem()
                flags = item.flags()
                item.setFlags(flags & checkboxMask)
                item.setCheckState(Qt.Unchecked)
                self.deleteTable.setItem(r, 0, item)
            for c in range(self.nInputs):  # populate input values
                item = self.deleteTable.item(r, c + 1)
                if item is None:
                    item = QTableWidgetItem(self.format % self.inputData[r - 1][c])
                    flags = item.flags()
                    item.setFlags(flags & mask)
                    if r - 1 < self.nSamples - self.nSamplesAdded:
                        color = inputColor
                    else:
                        color = inputRefinedColor
                    item.setBackground(color)
                    self.deleteTable.setItem(r, c + 1, item)
            if isinstance(self.outputData, numpy.ndarray):
                for c in range(self.nOutputs):  # populate output values
                    item = self.deleteTable.item(r, self.nInputs + c + 1)
                    if item is None:
                        if math.isnan(self.outputData[r - 1][c]):
                            item = QTableWidgetItem()
                        else:
                            item = QTableWidgetItem(
                                self.format % self.outputData[r - 1][c]
                            )
                        if r - 1 < self.nSamples - self.nSamplesAdded:
                            color = outputColor
                        else:
                            color = outputRefinedColor
                        item.setBackground(color)
                        self.deleteTable.setItem(r, self.nInputs + c + 1, item)

        self.isDrawingDeleteTable = False

    def redrawDeleteTable(self):
        # Does not rewrite input values for speed purposes.  These never change

        self.isDrawingDeleteTable = True
        self.freeze()

        # get selected row
        row = self.filesTable.selectedIndexes()[0].row()
        data = self.dat.sdoeSimList[row]
        _data = data.getValidSamples()  # filter out samples that have no output results

        outputColor = QtGui.QColor(255, 255, 0, 50)  # translucent yellow
        outputRefinedColor = QtGui.QColor(255, 255, 0, 100)  # translucent yellow
        for c in range(self.nInputs):
            item = self.deleteTable.item(0, c + 1)
            item.setCheckState(Qt.Unchecked)
            for r in range(self.nSamples):
                item = self.deleteTable.item(r + 1, 0)
                if item is not None:
                    item.setCheckState(Qt.Unchecked)

        for c in range(self.nOutputs):  # populate output values
            item = self.deleteTable.item(0, self.nInputs + c + 1)
            item.setCheckState(Qt.Unchecked)
            for r in range(self.deleteScrollRow - 1, self.deleteScrollRow + 14):
                item = self.deleteTable.item(r + 1, self.nInputs + c + 1)
                if item is not None:
                    if isinstance(self.outputData, numpy.ndarray) and not numpy.isnan(
                        self.outputData[r][c]
                    ):
                        item.setText(self.format % self.outputData[r][c])
                    else:
                        item.setText("")
                    if r < self.nSamples - self.nSamplesAdded:
                        _color = outputColor
                    else:
                        _color = outputRefinedColor
                    item.setBackground(outputColor)

        self.deleteTable.resizeRowsToContents()
        self.deleteTable.resizeColumnsToContents()

        self.deleteTable.setEnabled(True)
        self.deletionButton.setEnabled(False)
        self.changeButton.setEnabled(False)

        self.isDrawingDeleteTable = False
        self.unfreeze()

    def getDeleteSelections(self):

        nSamples = self.deleteTable.rowCount() - 1
        nVars = self.deleteTable.columnCount() - 1

        # get selected row
        row = self.filesTable.selectedIndexes()[0].row()
        data = self.dat.sdoeSimList[row]
        data = data.getValidSamples()  # filter out samples that have no output results

        # get data info
        nInputs = data.getNumInputs()
        nOutputs = data.getNumOutputs()

        # get selections
        samples = []
        vars = []
        for i in range(1, nSamples + 1):
            item = self.deleteTable.item(i, 0)
            if (item is not None) and item.checkState() == Qt.Checked:
                samples.append(i - 1)
        for i in range(1, nVars + 1):
            item = self.deleteTable.item(0, i)
            if (item is not None) and item.checkState() == Qt.Checked:
                vars.append(i - 1)

        # partition selections into inputs and outputs
        inVars = []
        outVars = []
        if vars:
            vars = numpy.array(vars)
            k = numpy.where(vars < nInputs)
            inVars = vars[k]
            inVars = inVars.tolist()
            k = numpy.where(vars >= nInputs)
            outVars = vars[k]
            outVars = outVars.tolist()
            outVars = [x - nInputs for x in outVars]

        return (
            samples,
            inVars,
            outVars,
            nSamples,
            nInputs,
            nOutputs,
        )  # first 3 output args are 1-indexed

    def activateDeleteButton(self, row, column):

        if row == 0 or column == 0:
            b = False
            (
                samples,
                inVars,
                outVars,
                nSamples,
                nInputs,
                nOutputs,
            ) = self.getDeleteSelections()
            if samples or inVars or outVars:
                if (nSamples - len(samples) > 0) and (nInputs - len(inVars) > 0):
                    b = True

            self.deletionButton.setEnabled(b)
            return b

    def enableDelete(self, b):
        self.deleteTable.setEnabled(b)
        self.deletionButton.setEnabled(b)

    def delete(self):

        # check arguments
        if not self.activateDeleteButton(0, 0):
            return

        self.enableDelete(False)
        self.freeze()

        # get selected row
        row = self.filesTable.selectedIndexes()[0].row()
        data = self.dat.sdoeSimList[row]
        fname = Common.getLocalFileName(
            DataProcessor.dname, data.getModelName().split()[0], ".dat"
        )
        data.writeToPsuade(fname)

        # perform deletion
        (
            samples,
            inVars,
            outVars,
            nSamples,
            nInputs,
            nOutputs,
        ) = self.getDeleteSelections()
        if samples:
            samplesToKeep = [i for i in range(nSamples) if i not in samples]
            newdata = data.getSubSample(samplesToKeep)
        else:
            newdata = copy.deepcopy(data)
        if inVars:
            newdata.deleteInputs(inVars)
        if outVars:
            newdata.deleteOutputs(outVars)

        newdata.setModelName(data.getModelName().split(".")[0] + ".deleted")
        newdata.setSession(self.dat)

        # add to simulation table, select new data
        self.dat.sdoeSimList.append(newdata)
        res = Results()
        res.sdoe_add_result(newdata)
        self.dat.sdoeFilterResultsList.append(res)
        self.updateSimTable()

        self.deleteTable.resizeColumnsToContents()

        # reset components
        self.unfreeze()

    def deleteTableCellChanged(self, item):
        if self.isDrawingDeleteTable:
            return

        index = self.deleteTable.indexFromItem(item)
        row = index.row()
        col = index.column()

        modifiedColor = QtGui.QColor(0, 250, 0, 100)  # translucent green

        # get selected row
        simRow = self.filesTable.selectedIndexes()[0].row()
        data = self.dat.sdoeSimList[simRow]

        nInputs = data.getNumInputs()
        outputData = data.getOutputData()
        _nOutputs = data.getNumOutputs()
        _nSamples = data.getNumSamples()

        if len(outputData) == 0:
            item.setBackground(modifiedColor)
        else:
            origValue = outputData[row - 1, col - nInputs - 1]
            value = float(item.text())

            if value != origValue:
                item.setBackground(modifiedColor)

        self.changeButton.setEnabled(True)

    def updateOutputValues(self):
        # Warn user
        button = QMessageBox.question(
            self,
            "Change output values?",
            "You are about to permanently change the output values.  "
            "This cannot be undone.  Do you want to proceed?",
            QMessageBox.Yes,
            QMessageBox.No,
        )
        if button != QMessageBox.Yes:
            return

        # get selected row
        row = self.filesTable.selectedIndexes()[0].row()
        origData = self.dat.sdoeSimList[row]
        data = self.dat.sdoeSimList[row]

        nInputs = data.getNumInputs()
        outputData = data.getOutputData()
        nOutputs = data.getNumOutputs()
        nSamples = data.getNumSamples()
        runState = data.getRunState()

        if len(outputData) == 0:
            outputData = numpy.empty((nSamples, nOutputs))
            outputData[:] = numpy.NAN
        for outputNum in range(nOutputs):
            for sampleNum in range(nSamples):
                item = self.deleteTable.item(sampleNum + 1, outputNum + nInputs + 1)
                if item is not None:
                    if len(item.text()) > 0:
                        value = float(item.text())
                        outputData[sampleNum, outputNum] = value
                if outputNum == nOutputs - 1:
                    hasNan = False
                    for c in range(nOutputs):
                        if numpy.isnan(outputData[sampleNum, c]):
                            hasNan = True
                    if not hasNan:
                        runState[sampleNum] = True
        origData.setOutputData(outputData)
        origData.setRunState(runState)
        self.outputData = outputData
        self.redrawDeleteTable()
        self.updateSimTableRow(row)

    # ODoE Page starts here
    def loadRStrainData(self):
        self.freeze()
        # Get file name
        if platform.system() == "Windows":
            _allFiles = "*.*"
        else:
            _allFiles = "*"
        fileName, selectedFilter = QFileDialog.getOpenFileName(
            self, "Open Train Data", "", "CSV (Comma delimited) (*.csv)"
        )
        if len(fileName) == 0:
            self.unfreeze()
            return

        if fileName.endswith(".csv"):
            data = LocalExecutionModule.readSampleFromCsvFile(fileName, True)
        else:
            try:
                data = LocalExecutionModule.readSampleFromPsuadeFile(fileName)
            except:
                import traceback

                traceback.print_exc()
                QMessageBox.critical(
                    self,
                    "Incorrect format",
                    "File does not have the correct format! Please consult the users manual "
                    "about the format.",
                )
                logging.getLogger("foqus." + __name__).exception(
                    "Error loading psuade file."
                )
                self.unfreeze()
                return
        self.trainData_edit.setText(fileName)
        self.odoe_data = data
        self.odoe_inputs_groupBox.setEnabled(True)
        self.input_table.init(self.odoe_data, InputPriorTable.ODOE)
        self.refreshOutputTable()

        self.unfreeze()

    def refreshOutputTable(self):
        data = self.odoe_data
        data = data.getValidSamples()  # filter out samples that have no output results
        y = data.getOutputData()

        # populate table
        outVarNames = data.getOutputNames()
        nOutputs = data.getNumOutputs()
        self.outputMeans = [0] * nOutputs
        self.outputStdDevs = [0] * nOutputs
        self.output_table.setRowCount(nOutputs)
        self.output_table.setColumnCount(len(self.outputCol_index))
        self.output_table.setHorizontalHeaderLabels(
            self.outputColumnHeaders[: len(self.outputCol_index)]
        )
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
                chkbox = self.output_table.cellWidget(i, self.outputCol_index["sel"])
                if chkbox is None:
                    chkbox = QCheckBox("", self)
                    chkbox.setChecked(True)
                    chkbox.setEnabled(True)
                    self.output_table.setCellWidget(
                        i, self.outputCol_index["sel"], chkbox
                    )
                    chkbox.toggled.connect(self.on_output_checkbox_changed)

                # add combo boxes for RS1 and rs2 and Legendre spinbox
                combo1 = RSCombos.RSCombo1(self)
                combo2 = RSCombos.RSCombo2(self)
                legendreSpin = RSCombos.LegendreSpinBox(self)
                marsBasisSpin = None
                marsInteractionSpin = None
                if "mars1" in self.outputCol_index:
                    marsBasisSpin = RSCombos.MarsBasisSpinBox(self)
                    marsBasisSpin.init(data)
                if "mars2" in self.outputCol_index:
                    marsInteractionSpin = RSCombos.MarsDegreeSpinBox(self)
                    marsInteractionSpin.init(data)

                legendreSpin.init(data)
                combo2.init(data, legendreSpin, useShortNames=True, odoe=True)
                combo2.setMinimumContentsLength(10)
                combo1.init(
                    data,
                    combo2,
                    True,
                    True,
                    marsBasisSpin=marsBasisSpin,
                    marsDegreeSpin=marsInteractionSpin,
                    odoe=True,
                )

                combo1.setProperty("row", i)
                combo2.setProperty("row", i)

                self.output_table.setCellWidget(i, self.outputCol_index["rs1"], combo1)
                self.output_table.setCellWidget(i, self.outputCol_index["rs2"], combo2)
                if "mars1" in self.outputCol_index:
                    self.output_table.setCellWidget(
                        i, self.outputCol_index["mars1"], marsBasisSpin
                    )
                if "mars2" in self.outputCol_index:
                    self.output_table.setCellWidget(
                        i, self.outputCol_index["mars2"], marsInteractionSpin
                    )

            else:
                # add a disabled checkbox
                chkbox = QCheckBox("")
                chkbox.setChecked(False)
                chkbox.setEnabled(False)
                self.output_table.setCellWidget(i, self.outputCol_index["sel"], chkbox)
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

        self.output_table.resizeColumnsToContents()

    def checkCandFile(self):
        if self.yesCand_radioButton.isChecked():
            self.loadCandidate_button.setEnabled(True)
            self.generateCandidate_button.setEnabled(False)
        else:
            self.loadCandidate_button.setEnabled(False)
            self.generateCandidate_button.setEnabled(True)

    def checkEvalFile(self):
        if self.yesEval_radioButton.isChecked():
            self.loadEval_button.setEnabled(True)
        else:
            self.loadEval_button.setEnabled(False)

    def confirmInputs(self):
        QApplication.processEvents()
        self.generateInputPriorData()
        self.odoe_design_groupBox.setEnabled(True)
        self.generateCandidate_button.setEnabled(False)
        self.deleteSelection_button.setEnabled(False)
        self.deleteEval_button.setEnabled(False)
        self.confirmCandidates_button.setEnabled(self.checkCandidates())
        QApplication.processEvents()

    def generateInputPriorData(self):
        QApplication.processEvents()
        data = copy.deepcopy(self.odoe_data)
        names, indices = self.input_table.getVariablesWithType("Variable")
        del_indices = []
        for i in range(data.getNumInputs()):
            if i not in indices:
                del_indices.append(i)

        data.deleteInputs(del_indices)

        simDialog = odoeSimSetup(
            data.model, self.dat, returnDataSignal=self.addPriorSignal, parent=self
        )
        simDialog.show()

        QApplication.processEvents()

    def addInputPrior(self, data):
        self.odoe_priorData = data

    def loadCandidate(self):
        self.freeze()
        # Get file name
        if platform.system() == "Windows":
            _allFiles = "*.*"
        else:
            _allFiles = "*"
        fileName, selectedFilter = QFileDialog.getOpenFileName(
            self, "Open Candidate Set", "", "CSV (Comma delimited) (*.csv)"
        )
        if len(fileName) == 0:
            self.unfreeze()
            return

        if fileName.endswith(".csv"):
            data = LocalExecutionModule.readSampleFromCsvFile(fileName, False)
        else:
            try:
                data = LocalExecutionModule.readSampleFromPsuadeFile(fileName)
            except:
                import traceback

                traceback.print_exc()
                QMessageBox.critical(
                    self,
                    "Incorrect format",
                    "File does not have the correct format! Please consult the users manual "
                    "about the format.",
                )
                logging.getLogger("foqus." + __name__).exception(
                    "Error loading psuade file."
                )
                self.unfreeze()
                return

        data.setSession(self.dat)
        self.dat.odoeCandList.append(data)

        res = Results()
        res.odoe_add_result(data)
        shutil.copy(fileName, self.odoe_dname)

        # Update table
        self.updateCandTable()
        self.unfreeze()

    def generateCandidate(self):
        data = copy.deepcopy(self.odoe_data)
        names, indices = self.input_table.getDesignVariables()
        del_indices = []
        for i in range(data.getNumInputs()):
            if i not in indices:
                del_indices.append(i)

        data.deleteInputs(del_indices)
        simDialog = odoeSimSetup(
            data.model, self.dat, returnDataSignal=self.addCandidateSignal, parent=self
        )
        simDialog.show()

    def addDataToCandTable(self, data):
        if data is None:
            return
        self.dat.odoeCandList.append(data)
        res = Results()
        res.odoe_add_result(data)

        self.updateCandTable()

    def changeDataInCandTable(self, data, row):
        if data is None:
            return
        self.dat.odoeCandList[row] = data
        res = Results()
        res.odoe_add_result(data)

        self.updateCandTableRow(row)

    def updateCandTable(self):
        QApplication.processEvents()
        # Update table
        numCands = len(self.dat.odoeCandList)
        self.odoe_cand_table.setRowCount(numCands)
        self.updateCandTableRow(numCands - 1)
        self.odoe_cand_table.selectRow(numCands - 1)
        self.odoe_cand_table.resizeColumnsToContents()
        self.confirmCandidates_button.setEnabled(self.checkCandidates())
        QApplication.processEvents()

    def updateCandTableRow(self, row):
        data = self.dat.odoeCandList[row]
        item = self.odoe_cand_table.item(row, self.indexCol)
        if item is None:
            item = QTableWidgetItem()
        item.setText(str(row + 1))
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        flags = item.flags()
        mask = ~Qt.ItemIsEditable
        item.setFlags(flags & mask)
        self.odoe_cand_table.setItem(row, self.indexCol, item)

        item = self.odoe_cand_table.item(row, self.fileCol)
        if item is None:
            item = QTableWidgetItem()
        item.setText(data.getModelName())
        self.odoe_cand_table.setItem(row, self.fileCol, item)

        # create checkboxes for select column
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        self.odoe_cand_table.setCellWidget(row, self.selectCol, checkbox)
        checkbox.setProperty("row", row)
        checkbox.toggled.connect(self.on_checkbox_changed)

        viewButton = self.odoe_cand_table.cellWidget(row, self.visualizeCol)
        newViewButton = False
        if viewButton is None:
            newViewButton = True
            viewButton = QPushButton()
            viewButton.setText("View")
            viewButton.setToolTip("View and plot the candidate set.")

        viewButton.setProperty("row", row)
        if newViewButton:
            viewButton.clicked.connect(self.viewCand)
            self.odoe_cand_table.setCellWidget(row, self.visualizeCol, viewButton)

        # Resize table
        self.resizeColumns()
        minWidth = (
            2
            + self.odoe_cand_table.columnWidth(0)
            + self.odoe_cand_table.columnWidth(1)
            + self.odoe_cand_table.columnWidth(2)
            + self.odoe_cand_table.columnWidth(3)
        )
        if self.odoe_cand_table.verticalScrollBar().isVisible():
            minWidth += self.odoe_cand_table.verticalScrollBar().width()
        self.odoe_cand_table.setMinimumWidth(minWidth)

    def viewCand(self):
        sender = self.sender()
        row = sender.property("row")

        self.changeCandidateSignal.disconnect()
        self.changeCandidateSignal.connect(
            lambda data: self.changeDataInCandTable(data, row)
        )

        previewData = self.dat.odoeCandList[row]
        hname = None
        usf = None
        nusf = None
        irsf = None
        scatterLabel = "Candidates"
        nImpPts = 0
        dialog = sdoePreview(
            previewData,
            hname,
            self.odoe_dname,
            usf,
            nusf,
            irsf,
            scatterLabel,
            nImpPts,
            self,
        )
        dialog.show()

    def candSelected(self):
        selectedIndexes = self.odoe_cand_table.selectedIndexes()
        if not selectedIndexes:
            self.deleteSelection_button.setEnabled(False)
            return
        self.deleteSelection_button.setEnabled(True)

        row = selectedIndexes[0].row()
        _cand = self.dat.odoeCandList[row]

    def deleteSelection(self):
        QApplication.processEvents()
        # Get selected row
        row = self.odoe_cand_table.selectedIndexes()[0].row()

        # Delete simulation
        self.dat.odoeCandList.pop(row)
        self.refreshCandTable()
        QApplication.processEvents()
        numCands = len(self.dat.odoeCandList)
        if numCands > 0:
            if row >= numCands:
                self.odoe_cand_table.selectRow(numCands - 1)
                row = numCands - 1
            _cand = self.dat.odoeCandList[row]
        QApplication.processEvents()

    def refreshCandTable(self):
        numCands = len(self.dat.odoeCandList)
        self.odoe_cand_table.setRowCount(numCands)
        for i in range(numCands):
            self.updateCandTableRow(i)

        if numCands == 0:
            self.confirmCandidates_button.setEnabled(False)

    def checkCandidates(self):
        numCands = len(self.dat.odoeCandList)
        count = 0
        for row in range(numCands):
            if self.odoe_cand_table.cellWidget(row, self.selectCol).isChecked():
                count += 1

        return count > 0

    def on_checkbox_changed(self):
        self.confirmCandidates_button.setEnabled(self.checkCandidates())

    def getCandList(self):
        cand_list = []
        numFiles = len(self.dat.odoeCandList)
        for i in range(numFiles):
            if self.odoe_cand_table.cellWidget(i, self.selectCol).isChecked():
                cand_list.append(self.dat.odoeCandList[i])

        return cand_list  # returns sample data structures

    def aggregateCandList(self):
        cand_list = self.getCandList()

        cand_csv_list = []
        for cand in cand_list:
            cand_path = os.path.join(self.odoe_dname, cand.getModelName())
            if not os.path.exists(cand_path):
                cand.writeToCsv(cand_path, inputsOnly=True)
            cand_csv_list.append(cand_path)

        hist_csv_list = []

        cand_agg, hist_agg = df_utils.check(cand_csv_list, hist_csv_list)
        return cand_agg

    def createAggCandData(self):
        cand_agg = self.aggregateCandList()  # this is a df

        cand_fname = os.path.join(self.odoe_dname, "aggregate_candidates.csv")
        df_utils.write(cand_fname, cand_agg)
        candidateData = LocalExecutionModule.readSampleFromCsvFile(
            cand_fname, askForNumInputs=False
        )

        return candidateData

    def confirmCandidates(self):
        QApplication.processEvents()
        candData = self.createAggCandData()
        eval_list = self.getEvalList()
        if len(eval_list) > 0:
            _evalData = self.createAggEvalData()
        if self.checkCandCols(candData):
            self.odoe_outputs_groupBox.setEnabled(True)
            self.validateRS_button.setEnabled(self.checkOutputs())
            self.confirmRS_button.setEnabled(False)
        else:
            self.showColWarning()
        QApplication.processEvents()

    def checkCandCols(self, candData):
        designVarsNames, designVarsIndex = self.input_table.getDesignVariables()
        candInputNames = list(candData.getInputNames())
        return designVarsNames == candInputNames

    def showColWarning(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Design inputs and candidates/evaluation set do not match!")
        msg.setText(
            "The design inputs selected in the input settings table do not match the candidate/evaluation set inputs."
            "Please make sure your candidate/evaluation set inputs match the design inputs."
        )
        msg.setStandardButtons(QMessageBox.Ok)
        reply = msg.exec_()
        return reply

    def loadEval(self):
        self.freeze()
        # Get file name
        if platform.system() == "Windows":
            _allFiles = "*.*"
        else:
            _allFiles = "*"
        fileName, selectedFilter = QFileDialog.getOpenFileName(
            self, "Open Evaluation Set", "", "CSV (Comma delimited) (*.csv)"
        )
        if len(fileName) == 0:
            self.unfreeze()
            return

        if fileName.endswith(".csv"):
            data = LocalExecutionModule.readSampleFromCsvFile(fileName, False)
        else:
            try:
                data = LocalExecutionModule.readSampleFromPsuadeFile(fileName)
            except:
                import traceback

                traceback.print_exc()
                QMessageBox.critical(
                    self,
                    "Incorrect format",
                    "File does not have the correct format! Please consult the users manual "
                    "about the format.",
                )
                logging.getLogger("foqus." + __name__).exception(
                    "Error loading psuade file."
                )
                self.unfreeze()
                return

        data.setSession(self.dat)
        self.dat.odoeEvalList.append(data)

        res = Results()
        res.eval_add_result(data)
        shutil.copy(fileName, self.odoe_dname)

        # Update table
        self.updateEvalTable()
        self.unfreeze()

    def addDataToEvalTable(self, data):
        if data is None:
            return
        self.dat.odoeEvalList.append(data)
        res = Results()
        res.eval_add_result(data)

        self.updateEvalTable()

    def changeDataInEvalTable(self, data, row):
        if data is None:
            return
        self.dat.odoeEvalList[row] = data
        res = Results()
        res.eval_add_result(data)

        self.updateEvalTableRow(row)

    def updateEvalTable(self):
        QApplication.processEvents()
        # Update table
        numEvals = len(self.dat.odoeEvalList)
        self.odoe_eval_table.setRowCount(numEvals)
        self.updateEvalTableRow(numEvals - 1)
        self.odoe_eval_table.selectRow(numEvals - 1)
        self.odoe_eval_table.resizeColumnsToContents()
        QApplication.processEvents()

    def updateEvalTableRow(self, row):
        data = self.dat.odoeEvalList[row]
        item = self.odoe_eval_table.item(row, self.indexCol)
        if item is None:
            item = QTableWidgetItem()
        item.setText(str(row + 1))
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        flags = item.flags()
        mask = ~Qt.ItemIsEditable
        item.setFlags(flags & mask)
        self.odoe_eval_table.setItem(row, self.indexCol, item)

        item = self.odoe_eval_table.item(row, self.fileCol)
        if item is None:
            item = QTableWidgetItem()
        item.setText(data.getModelName())
        self.odoe_eval_table.setItem(row, self.fileCol, item)

        # create checkboxes for select column
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        self.odoe_eval_table.setCellWidget(row, self.selectCol, checkbox)
        checkbox.setProperty("row", row)
        checkbox.toggled.connect(self.on_checkbox_changed_eval)

        viewButton = self.odoe_eval_table.cellWidget(row, self.visualizeCol)
        newViewButton = False
        if viewButton is None:
            newViewButton = True
            viewButton = QPushButton()
            viewButton.setText("View")
            viewButton.setToolTip("View and plot the evaluation set.")

        viewButton.setProperty("row", row)
        if newViewButton:
            viewButton.clicked.connect(self.viewEval)
            self.odoe_eval_table.setCellWidget(row, self.visualizeCol, viewButton)

        # Resize table
        self.resizeColumns()
        minWidth = (
            2
            + self.odoe_eval_table.columnWidth(0)
            + self.odoe_eval_table.columnWidth(1)
            + self.odoe_eval_table.columnWidth(2)
            + self.odoe_eval_table.columnWidth(3)
        )
        if self.odoe_eval_table.verticalScrollBar().isVisible():
            minWidth += self.odoe_eval_table.verticalScrollBar().width()
        self.odoe_eval_table.setMinimumWidth(minWidth)

    def viewEval(self):
        sender = self.sender()
        row = sender.property("row")

        self.changeEvalSignal.disconnect()
        self.changeEvalSignal.connect(
            lambda data: self.changeDataInEvalTable(data, row)
        )

        previewData = self.dat.odoeEvalList[row]
        hname = None
        usf = None
        nusf = None
        irsf = None
        scatterLabel = "Evaluations"
        nImpPts = 0
        dialog = sdoePreview(
            previewData,
            hname,
            self.odoe_dname,
            usf,
            nusf,
            irsf,
            scatterLabel,
            nImpPts,
            self,
        )
        dialog.show()

    def evalSelected(self):
        selectedIndexes = self.odoe_eval_table.selectedIndexes()
        if not selectedIndexes:
            self.deleteEval_button.setEnabled(False)
            return
        self.deleteEval_button.setEnabled(True)

        row = selectedIndexes[0].row()
        _eval = self.dat.odoeEvalList[row]

    def deleteEval(self):
        QApplication.processEvents()
        # Get selected row
        row = self.odoe_eval_table.selectedIndexes()[0].row()

        # Delete simulation
        self.dat.odoeEvalList.pop(row)
        self.refreshEvalTable()
        QApplication.processEvents()
        numEvals = len(self.dat.odoeEvalList)
        if numEvals > 0:
            if row >= numEvals:
                self.odoe_eval_table.selectRow(numEvals - 1)
                row = numEvals - 1
            _eval = self.dat.odoeEvalList[row]
        QApplication.processEvents()

    def refreshEvalTable(self):
        numEvals = len(self.dat.odoeEvalList)
        self.odoe_eval_table.setRowCount(numEvals)
        for i in range(numEvals):
            self.updateEvalTableRow(i)

    def checkEvals(self):
        numEvals = len(self.dat.odoeEvalList)
        count = 0
        for row in range(numEvals):
            if self.odoe_eval_table.cellWidget(row, self.selectCol).isChecked():
                count += 1

        return count > 0

    def on_checkbox_changed_eval(self):
        self.confirmCandidates_button.setEnabled(self.checkCandidates())

    def getEvalList(self):
        eval_list = []
        numFiles = len(self.dat.odoeEvalList)
        for i in range(numFiles):
            if self.odoe_eval_table.cellWidget(i, self.selectCol).isChecked():
                eval_list.append(self.dat.odoeEvalList[i])

        return eval_list  # returns sample data structures

    def aggregateEvalList(self):
        eval_list = self.getEvalList()

        eval_csv_list = []
        for eval in eval_list:
            eval_path = os.path.join(self.odoe_dname, eval.getModelName())
            if not os.path.exists(eval_path):
                eval.writeToCsv(eval_path, inputsOnly=True)
            eval_csv_list.append(eval_path)

        hist_csv_list = []

        eval_agg, hist_agg = df_utils.check(eval_csv_list, hist_csv_list)
        return eval_agg

    def createAggEvalData(self):
        eval_agg = self.aggregateEvalList()  # this is a df

        eval_fname = os.path.join(self.odoe_dname, "aggregate_evaluations.csv")
        df_utils.write(eval_fname, eval_agg)
        evalData = LocalExecutionModule.readSampleFromCsvFile(
            eval_fname, askForNumInputs=False
        )

        return evalData

    def checkEvalCols(self, evalData):
        designVarsNames, designVarsIndex = self.input_table.getDesignVariables()
        evalInputNames = list(evalData.getInputNames())
        return designVarsNames == evalInputNames

    def checkOutputs(self):
        numOutputs = self.output_table.rowCount()
        count = 0
        for row in range(numOutputs):
            if self.output_table.cellWidget(
                row, self.outputCol_index["sel"]
            ).isChecked():
                count += 1

        return count > 0

    def on_output_checkbox_changed(self):
        self.validateRS_button.setEnabled(self.checkOutputs())

    def validateRS(self):
        QApplication.processEvents()
        self.freeze()
        y = {}
        rs1 = {}
        rs2 = {}
        numOutputs = self.output_table.rowCount()
        for row in range(numOutputs):
            if self.output_table.cellWidget(
                row, self.outputCol_index["sel"]
            ).isChecked():
                y[row] = row + 1
                rs1[row] = self.output_table.cellWidget(
                    row, self.outputCol_index["rs1"]
                )
                rs2[row] = self.output_table.cellWidget(
                    row, self.outputCol_index["rs2"]
                )

        rs = {}
        for row in y:
            rs[row] = RSCombos.lookupRS(rs1[row], rs2[row])

        rsOptions = {}
        for row in y:
            if rs[row].startswith("MARS"):
                rsOptions[row] = {
                    "marsBases": min([100, self.odoe_data.getNumSamples()]),
                    "marsInteractions": min([8, self.odoe_data.getNumVarInputs()]),
                }
            else:
                rsOptions[row] = None

        genRSCode = True

        for row in y:
            self.rsValidate(y[row], rs[row], rsOptions[row], genRSCode)

        msgBox = QMessageBox()
        msgBox.setWindowTitle("Response Surface Validation Plots")
        msgBox.setText(
            "Check the response surface validation plots for each one of your outputs."
            "If the generated response surfaces satisfy your needs, please confirm."
            "If not, please select a new response surface and validate again."
        )
        msgBox.exec_()
        self.confirmRS_button.setEnabled(True)
        self.unfreeze()
        QApplication.processEvents()

    def rsValidate(self, y, rs, rsOptions, genRSCode, odoe=True):
        self.freeze()

        data = self.odoe_data
        data = data.getValidSamples()  # filter out samples that have no output results

        # validate RS
        rsv = RSValidation(
            data,
            y,
            rs,
            rsOptions=rsOptions,
            genCodeFile=genRSCode,
            odoe=odoe,
            error_tol_percent=5,
        )
        mfile = rsv.analyze()

        self.unfreeze()
        return mfile

    def confirmRS(self):
        QApplication.processEvents()
        self.odoe_setup_groupBox.setEnabled(True)
        self.runRsEval()
        self.populateRsEvalTable()
        QApplication.processEvents()

    def runRsEval(self):
        cfname = os.path.join(self.odoe_dname, "aggregate_candidates.csv")
        cdata = LocalExecutionModule.readSampleFromCsvFile(
            cfname, askForNumInputs=False
        )
        pdata = self.odoe_priorData
        rsdata = self.odoe_data
        y = {}
        rs1 = {}
        rs2 = {}
        numOutputs = self.output_table.rowCount()
        for row in range(numOutputs):
            if self.output_table.cellWidget(
                row, self.outputCol_index["sel"]
            ).isChecked():
                y[row] = row + 1
                rs1[row] = self.output_table.cellWidget(
                    row, self.outputCol_index["rs1"]
                )
                rs2[row] = self.output_table.cellWidget(
                    row, self.outputCol_index["rs2"]
                )

        rs = {}
        for row in y:
            rs[row] = RSCombos.lookupRS(rs1[row], rs2[row])

        odoeu.rseval(rsdata, pdata, cdata, rs)

    def populateRsEvalTable(self):

        cfname = os.path.join(self.odoe_dname, "aggregate_candidates.csv")
        cdata = LocalExecutionModule.readSampleFromCsvFile(
            cfname, askForNumInputs=False
        )

        rsdata = self.odoe_data
        outputName = rsdata.getOutputNames()[0]
        rsevalfname = "odoeu_rseval.out"
        (
            inputData,
            outputData,
            numInputs,
            numOutputs,
        ) = LocalExecutionModule.readDataFromSimpleFile(rsevalfname)

        inputNames = cdata.getInputNames()

        # Set up table
        self.rsEval_table.setColumnCount(numInputs + 2)
        headers = inputNames + (
            "{} mean".format(outputName),
            "{} std".format(outputName),
        )
        self.rsEval_table.setRowCount(inputData.shape[0])

        c = 0
        for i, inputName in enumerate(headers):
            for r in range(inputData.shape[0]):
                item = self.rsEval_table.item(r, c)
                if item is None:
                    item = QTableWidgetItem("%f" % round(inputData[r][i], 5))
                    self.rsEval_table.setItem(r, c, item)
                else:
                    item.setText("%f" % round(inputData[r][i], 5))
            c = c + 1
        self.rsEval_table.setColumnCount(len(headers))
        self.rsEval_table.setHorizontalHeaderLabels(headers)
        self.rsEval_table.resizeColumnsToContents()

        # Disable input columns
        rows = self.rsEval_table.rowCount()
        columns = self.rsEval_table.columnCount()
        for r in range(rows):
            for c in range(columns):
                item = self.rsEval_table.item(r, c)
                item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

        # Make mean and std columns editable
        for r in range(rows):
            for c in range(columns - 2, columns):
                item = self.rsEval_table.item(r, c)
                item.setFlags(
                    QtCore.Qt.ItemIsSelectable
                    | QtCore.Qt.ItemIsEditable
                    | QtCore.Qt.ItemIsEnabled
                )

    def getRsEvalTableData(self):
        fname = os.path.join(self.odoe_dname, "CandidateSet")
        rows = self.rsEval_table.rowCount()
        columns = self.rsEval_table.columnCount()
        data = np.zeros([rows, columns])
        for r in range(rows):
            for c in range(columns):
                data[r, c] = self.rsEval_table.item(r, c).text()

        RSAnalyzer.writeRSsample(fname, data, row=True)
        return fname

    def runOdoe(self):
        QApplication.processEvents()

        # Create run outdir
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        outdir = os.path.join(self.odoe_dname, timestamp)
        os.makedirs(outdir, exist_ok=True)

        # Check user choices in the GUI
        if self.fisher_radioButton.isChecked():
            method = "fisher"
        elif self.bayesian_radioButton.isChecked():
            method = "bayesian"

        if self.Gopt_radioButton.isChecked():
            optCriterion = "G"
        elif self.Iopt_radioButton.isChecked():
            optCriterion = "I"
        elif self.Dopt_radioButton.isChecked():
            optCriterion = "D"
        elif self.Aopt_radioButton.isChecked():
            optCriterion = "A"
        elif self.Eopt_radioButton.isChecked():
            optCriterion = "E"

        designSize = self.odoeDesignSize_spin.value()

        numRestarts = int(self.restarts_comboBox.currentText())

        cfname = shutil.copy(
            os.path.join(self.odoe_dname, "aggregate_candidates.csv"), outdir
        )
        cdata = LocalExecutionModule.readSampleFromCsvFile(
            cfname, askForNumInputs=False
        )
        cfile_temp = self.getRsEvalTableData()
        cfile = shutil.copy(cfile_temp, outdir)
        pdata = self.odoe_priorData
        rsdata = self.odoe_data
        if os.path.exists(os.path.join(self.odoe_dname, "aggregate_evaluations.csv")):
            efname = shutil.copy(
                os.path.join(self.odoe_dname, "aggregate_evaluations.csv"), outdir
            )
            edata = LocalExecutionModule.readSampleFromCsvFile(
                efname, askForNumInputs=False
            )
        else:
            efname = None
            edata = None

        y = {}
        rs1 = {}
        rs2 = {}
        numOutputs = self.output_table.rowCount()
        for row in range(numOutputs):
            if self.output_table.cellWidget(
                row, self.outputCol_index["sel"]
            ).isChecked():
                y[row] = row + 1
                rs1[row] = self.output_table.cellWidget(
                    row, self.outputCol_index["rs1"]
                )
                rs2[row] = self.output_table.cellWidget(
                    row, self.outputCol_index["rs2"]
                )

        rs = {}
        for row in y:
            rs[row] = RSCombos.lookupRS(rs1[row], rs2[row])

        self.resultMessage = "===== ODoE RESULTS =====\n\n"
        time_list = []
        for nr in range(numRestarts):
            t0 = time.time()
            best_indices, best_optval = odoeu.odoeu(
                cdata,
                cfile,
                pdata,
                rsdata,
                rs,
                method,
                optCriterion,
                designSize,
                edata=edata,
            )
            time_list.append(time.time() - t0)
            self.resultMessage += "Results for Run #%d:\n" % (nr + 1)
            self.resultMessage += "Best Design(s): %s\n" % best_indices
            self.resultMessage += "Best %s-Optimality Value: %f\n\n" % (
                optCriterion,
                best_optval,
            )

        # Save results to text file
        resultsFile = os.path.join(outdir, "odoe_results.txt")
        f = open(resultsFile, "w")
        f.write(self.resultMessage)
        f.write("===== ODoE SETUP =====\n")
        f.write("Input variable types:\n")
        randNames, randIndices = self.input_table.getVariablesWithType("Variable")
        desNames, desIndices = self.input_table.getDesignVariables()
        randDict = dict(zip(randIndices, randNames))
        desDict = dict(zip(desIndices, desNames))
        inputDict = {**randDict, **desDict}
        for i in range(len(inputDict)):
            f.write("%s -- " % inputDict[i])
            if inputDict[i] in randNames:
                f.write("random\n")
            else:
                f.write("design\n")

        f.write("\n")
        f.write("Candidate set: %s\n" % cfname)
        f.write("Evaluation set: %s\n\n" % efname)

        f.write("Response surface:\n")
        rs_path = shutil.copy(os.path.join(self.odoe_dname, "RSTrainData"), outdir)
        f.write("Training Data: %s\n" % rs_path)
        f.write("RS type: %s \n" % rs[0])
        f.write("RS predictions: %s\n\n" % cfile)

        f.write("Statistical Method: %s\n" % method)
        f.write("Optimality type: %s\n" % optCriterion)
        f.write("Design size: %d\n" % designSize)
        f.write("Number of restarts: %d\n\n" % numRestarts)

        f.write("Total runtime: %d seconds\n" % sum(time_list))
        avg_time = sum(time_list) / len(time_list)
        f.write("Average runtime (per restart): %d seconds\n" % avg_time)
        f.close()

        self.resultMessage += "* Results saved to %s" % outdir
        msgBox = QMessageBox()
        msgBox.setText(self.resultMessage)
        msgBox.exec_()

        QApplication.processEvents()
