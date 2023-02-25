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
import numpy
import copy
from foqus_lib.gui.uq.updateUQModelDialog import *
from foqus_lib.gui.uq.SimSetup import *
from foqus_lib.gui.uq.stopEnsembleDialog import *
from foqus_lib.gui.uq.uqDataBrowserFrame import uqDataBrowserFrame
from foqus_lib.framework.uq.SampleData import *
from foqus_lib.framework.uq.Model import *
from foqus_lib.framework.uq.SamplingMethods import *
from foqus_lib.framework.uq.ResponseSurfaces import *
from foqus_lib.framework.uq.DataProcessor import *
from foqus_lib.framework.uq.RawDataAnalyzer import *
from foqus_lib.framework.uq.RSAnalyzer import *
from foqus_lib.framework.uq.Visualizer import *
from foqus_lib.framework.uq.SampleRefiner import *
from foqus_lib.framework.uq.Common import *
from foqus_lib.framework.uq.LocalExecutionModule import *
from foqus_lib.framework.sampleResults.results import Results
from .AnalysisDialog import AnalysisDialog

from PyQt5 import QtCore, uic, QtGui
from PyQt5.QtWidgets import (
    QStyledItemDelegate,
    QApplication,
    QButtonGroup,
    QTableWidgetItem,
    QProgressBar,
    QPushButton,
    QStyle,
    QDialog,
    QMessageBox,
    QInputDialog,
    QMenu,
)
from PyQt5.QtCore import QCoreApplication, QSize, QRect, QEvent
from PyQt5.QtGui import QCursor, QColor

from PyQt5 import uic

mypath = os.path.dirname(__file__)
_uqSetupFrameUI, _uqSetupFrame = uic.loadUiType(
    os.path.join(mypath, "uqSetupFrame_UI.ui")
)


class checkingThread(QtCore.QThread):
    runsFinishedSignal = QtCore.pyqtSignal()

    def __init__(self, row, parent=None):
        super(checkingThread, self).__init__()
        self.row = row
        self.parent = parent
        self.stop = False
        self.rtDisconnect = False

    class Communicate(QtCore.QObject):
        resizeColumnSignal = QtCore.pyqtSignal()
        progressBarSignal = QtCore.pyqtSignal(int)
        # progressBarSignal = QtCore.pyqtSignal(QProgressBar, int, int, int)
        progressBarErrorSignal = QtCore.pyqtSignal(QProgressBar, int)
        editButtonSignal = QtCore.pyqtSignal(bool)
        launchButtonSignal = QtCore.pyqtSignal(bool)
        analyzeButtonSignal = QtCore.pyqtSignal(bool)
        resultsSignal = QtCore.pyqtSignal(int, int)
        simSelectedSignal = QtCore.pyqtSignal()
        updateSessionSignal = QtCore.pyqtSignal(int, str)

    def run(self):
        c = self.Communicate()
        row = self.row
        sim = self.parent.dat.uqSimList[row]
        runType = sim.getRunType()
        runState = sim.getRunState()
        unfinishedRuns = numpy.where(runState == False)[0]
        unfinishedRuns = unfinishedRuns.tolist()
        numUnfinished = len(unfinishedRuns)
        editButton = self.parent.simulationTable.cellWidget(row, self.parent.editCol)
        c.editButtonSignal.connect(editButton.setEnabled)
        launchButton = self.parent.simulationTable.cellWidget(
            row, self.parent.launchCol
        )
        # c.launchButtonSignal.connect(launchButton.setEnabled)
        analyzeButton = self.parent.simulationTable.cellWidget(
            row, self.parent.analyzeCol
        )
        c.analyzeButtonSignal.connect(analyzeButton.setEnabled)
        c.resizeColumnSignal.connect(self.parent.resizeColumns)
        progressBar = self.parent.simulationTable.cellWidget(row, self.parent.statusCol)
        c.progressBarSignal.connect(progressBar.setValue)
        c.progressBarErrorSignal.connect(self.parent.setProgressBarNumErrors)
        # c.progressBarSignal.connect(uqSetupFrame.setProgressBarErrorStyle)
        c.resultsSignal.connect(self.parent.resultsBox)
        c.simSelectedSignal.connect(self.parent.simSelected)
        c.editButtonSignal.emit(False)
        c.launchButtonSignal.emit(False)
        c.updateSessionSignal.connect(self.parent.updateSession)
        # editButton.setEnabled(False)
        numSamples = sim.getNumSamples()
        xnames = []
        inputNames = sim.getInputNames()
        for name in inputNames:
            xnames.append(sim.getModelName() + "." + name)
        ynames = []
        outputNames = sim.getOutputNames()
        for name in outputNames:
            ynames.append(sim.getModelName() + "." + name)
        runState = runState.tolist()
        errors = [True] * numUnfinished
        outData = [None] * len(runState)
        for i, s in enumerate(runState):
            if s:
                outData[i] = sim.getOutputData()[i]
            else:
                outData[i] = [0.0] * len(outputNames)
        # outData = sim.getOutputData()
        # if len(outData) == 0:
        #    for i in xrange(numUnfinished):
        #        outData.append([])
        numTries = 0
        numSuccessful = 0
        numError = 0
        maxRuns = 1
        if runType == Model.EMULATOR:
            runStatus = sim.getEmulatorOutputStatus()
            maxRuns = runStatus.count(Model.NEED_TO_CALCULATE)
            # print 'maximum runs: ' + str(maxRuns)
            self.updateSessionSignal.emit(row, "Emulator")
        runIDToDisplay = -1
        numCompleteToDisplay = -1
        runID = 0
        okToIncreaseID = True
        if runType == Model.GATEWAY:
            setName = sim.getModelName()
            runMap = self.parent.runMap
            gt = self.parent.gThread
            numUnfinishedPrev = len(gt.res)
            readres = [False] * len(gt.res)
            if sim.turbineSession is not None:
                c.updateSessionSignal.emit(row, sim.turbineSession)
            elif gt.turbSession is not None:
                c.updateSessionSignal.emit(row, "Submitting...")
            else:
                c.updateSessionSignal.emit(row, "Local")
        goagain = False
        while (
            numTries < 10000000 and (numUnfinished > 0 or runID < maxRuns)
        ) or goagain:
            if runType != Model.GATEWAY:
                if runType == Model.LOCAL:
                    time.sleep(0.5)
                else:
                    time.sleep(0.1)
                try:
                    numUnfinished = LocalExecutionModule.getNumUnfinishedRunSamples()
                    # print numUnfinished
                except:
                    pass
            else:  # Model is gateway
                setName = sim.getModelName()
                if sim.turbineSession is None and gt.allSubmitted:
                    sim.turbineSession = gt.turbSession
                    sim.turbineJobIds = gt.jobIds
                    sim.turbineResub = gt.res_re  # whether sample has been resubmitted
                    if gt.turbSession is not None:
                        c.updateSessionSignal.emit(row, gt.turbSession)
                if self.stop:
                    gt.terminate()
                    # wait a bit for thread graph thread to terminate
                    # if it doesn't shut down fast that's okay,
                    # it will eventually just keep going
                    gt.join(2)
                    break  # leave checking loop
                elif self.rtDisconnect:
                    gt.remoteDisconnect()
                    gt.join()
                    sim.turbineJobIds = gt.jobIds
                    sim.turbineResub = gt.res_re  # whether sample has been resubmitted
                    break
                gt.join(2)
                with gt.statLock:
                    # get lock and copy status dict to keep it from
                    # changing while I am using it.
                    status = copy.copy(gt.status)
                if not gt.is_alive():
                    if gt.errorStat == 19:
                        raise Exception("Exception in graph thread (see log)")
                    numSuccessful = status["success"]
                    numError = numSamples - numSuccessful
                    numUnfinished = 0
                    goagain = False
                else:
                    numError = status["error"]
                    numSuccessful = status["success"]
                    numUnfinished = status["unfinished"]
                    goagain = True
                if numUnfinishedPrev != numUnfinished or not gt.is_alive():
                    numUnfinishedPrev = numUnfinished
                    with gt.resLock:
                        for i in range(len(gt.res)):
                            if not readres[i] and gt.res_fin[i] != -1:
                                readres[i] = True
                                sampleNum = runMap[i]
                                outputValues = [0] * len(ynames)
                                if not runState[sampleNum]:
                                    self.parent.dat.flowsheet.results.addFromSavedValues(
                                        setName=setName,
                                        name="uq_{0:06d}".format(sampleNum),
                                        valDict=gt.res[i],
                                    )
                                r = gt.res[i]
                                for j, name in enumerate(outputNames):
                                    key = name.split(".", 1)
                                    nkey = key[0]
                                    vkey = key[1]
                                    try:
                                        outputValues[j] = r["output"][nkey][vkey]
                                        errcode = r["graphError"]
                                    except:
                                        # no output available.
                                        # Run failed and got no output
                                        outputValues[j] = numpy.nan
                                        errcode = -2
                                    # Error or not set the run flag to
                                    # true once it has been run.
                                    # Originally if run resulted in
                                    # error this was set to false.
                                    # Usually as many times as you run
                                    # an error sample it won't succeed
                                    runState[sampleNum] = True
                                    # if errcode == 0:
                                    #    errors[sampleNum] = False
                                    # else:
                                    #    errors[sampleNum] = True
                                outData[sampleNum] = outputValues
                    # updatae sim so intermediate results can be saved
                    sim.setRunState(runState)
                    sim.setOutputData(outData)
                    errorIndex = sim.getOutputNames().index("graph.error")
                    numErrors = sum([row[errorIndex] > 0 for row in outData])
                    c.progressBarErrorSignal.emit(progressBar, numErrors)
            numTries += 1
            if runType == Model.EMULATOR:
                runID = LocalExecutionModule.getEmulatorOutputsFinished()
                numUnfinished = 0
                # print runID
            elif numUnfinished == 0 and okToIncreaseID:
                runID = runID + 1
                okToIncreaseID = False
            elif numUnfinished > 0:
                okToIncreaseID = True
            else:
                pass
            if runType == Model.EMULATOR:
                if runIDToDisplay != runID:
                    runIDToDisplay = runID
                    c.progressBarSignal.emit(runID)
            else:
                numComplete = numSamples - numUnfinished
                if numCompleteToDisplay != numComplete:
                    numCompleteToDisplay = numComplete
                    c.progressBarSignal.emit(numComplete)
        editButton.setText("View")
        c.editButtonSignal.emit(True)
        # if sim.getSampleMethod() == SamplingMethods.METIS:
        if numUnfinished == 0:
            launchButton.setText("Sample Refinement")
            c.launchButtonSignal.emit(True)
        else:
            launchButton.setText("Launch")
            c.launchButtonSignal.emit(False)
        c.analyzeButtonSignal.emit(True)
        c.resizeColumnSignal.emit()
        if runType == Model.LOCAL:
            self.parent.dat.uqSimList[row] = LocalExecutionModule.getRunData()
        elif runType == Model.GATEWAY:
            numSuccessful = runState.count(True)
            result = c.resultsSignal.emit(numSuccessful, numSamples)
            sim.setRunState(runState)
            sim.setOutputData(outData)
        else:  # emulator
            self.parent.dat.uqSimList[row] = LocalExecutionModule.getEmulatorRunData()
        QApplication.restoreOverrideCursor()
        # Update UI items if this was the selected sim
        indexes = self.parent.simulationTable.selectedIndexes()
        if len(indexes) > 0:
            selectedRow = indexes[0].row()
            if selectedRow == row:
                c.simSelectedSignal.emit()
        self.runsFinishedSignal.emit()


class uqSetupFrame(_uqSetupFrame, _uqSetupFrameUI):
    runsFinishedSignal = QtCore.pyqtSignal()
    addDataSignal = QtCore.pyqtSignal(SampleData)
    changeDataSignal = QtCore.pyqtSignal(SampleData)
    format = "%.5f"  # numeric format for table entries in UQ Toolbox
    drawDataDeleteTable = True  # flag to track whether delete table needs to be redrawn

    numberCol = 0
    statusCol = 1
    editCol = 2
    launchCol = 3
    analyzeCol = 4
    nameCol = 5
    sessCol = 6

    numInputsRow = 0
    numOutputsRow = 1
    schemeRow = 2
    sampleSizeRow = 3

    progressBarDefaultStyle = """
QProgressBar:horizontal {
border: 1px solid gray;
border-radius: 3px;
background: lightgrey;
padding: 1px;
text-align: center;
}

QProgressBar::chunk:horizontal {
background: qlineargradient(spread:pad, x1: 0, y1: 0.5, x2: 1, y2: 0.5, stop: 0 rgba(128, 255, 128 , 255), stop: 0.5 rgba(0, 226, 0, 255), stop: 1 rgba(0, 192, 0, 255));
}
"""

    ## This delegate is used to make the checkboxes in the delete table centered
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
        super(uqSetupFrame, self).__init__(parent=parent)
        self.setupUi(self)
        self.dat = dat
        LocalExecutionModule.session = dat
        self.filterWidget = uqDataBrowserFrame(self)
        self.filterWidget.indicesSelectedSignal.connect(self.createFilteredEnsemble)
        self.filterFrame.layout().addWidget(self.filterWidget)

        ###### Set up simulation ensembles section
        self.addSimulationButton.clicked.connect(self.addSimulation)
        self.addDataSignal.connect(self.addDataToSimTable)

        self.cloneSimulationButton.clicked.connect(self.cloneSimulation)
        self.cloneSimulationButton.setEnabled(False)
        self.loadSimulationButton.clicked.connect(self.loadSimulation)
        self.deleteSimulationButton.clicked.connect(self.deleteSimulation)
        self.deleteSimulationButton.setEnabled(False)
        self.saveSimulationButton.clicked.connect(self.saveSimulation)
        self.saveSimulationButton.setEnabled(False)

        self.simulationTable.resizeColumnsToContents()
        self.simulationTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.simulationTable.itemSelectionChanged.connect(self.simSelected)
        self.simulationTable.cellChanged.connect(self.simDescriptionChanged)

        # WHY pylint reports `row` as an undefined variable,
        # but this would cause a NameError only when the signal callback is run (as opposed to here, where it is defined)
        # this signal is redefined (with all the correct variables) in editSim(),
        # so it's possible that this line here is redundant and could be deleted
        # TODO pylint: disable=undefined-variable
        self.changeDataSignal.connect(lambda data: self.changeDataInSimTable(data, row))
        # TODO pylint: enable=undefined-variable

        self.infoGroupBox.hide()

        ##### Set up UQ toolbox
        self.dataTabs.setEnabled(False)
        # self.initFilter()

        ##        ### Set up tooltips for ...
        ##        # Parameter Screening
        ##        self.analysisTabs.setTabToolTip(0, 'For large input dimensions (>20, for example), ' +
        ##                                        'you may want to perform a relatively inexpensive \n' +
        ##                                        '(and thus qualitative) input parameter screening to ' +
        ##                                        'reduce the number of inputs for more detailed analyses.')
        ##        # Ensemble Data Analysis
        ##        self.analysisTabs.setTabToolTip(1, 'All analyses in this section are performed directly ' +
        ##                                        'on the ensemble data (that is, not relying on response ' +
        ##                                        'surfaces).')
        ##
        ##        # Response Surface based Analysis
        ##        self.analysisTabs.setTabToolTip(2, 'All analyses in this section are performed on the ' +
        ##                                        'response surface constructed from the ensemble data.')

        ### Perform all connects here
        # ........ DATA PAGE ..............
        self.dataTabs.setCurrentIndex(0)
        self.dataTabs.currentChanged[int].connect(self.getDataTab)
        # ........ DATA PAGE: FILTER TAB ...................
        # self.filterInput_radio.toggled.connect(self.activateInputFilter)
        # self.filterOutput_radio.toggled.connect(self.activateOutputFilter)
        # self.filterInput_combo.currentIndexChanged[int].connect(self.activateFilterButton)
        # self.filterInputMin_edit.editingFinished.connect(self.activateFilterButton)
        # self.filterInputMax_edit.editingFinished.connect(self.activateFilterButton)
        # self.filterOutput_combo.currentIndexChanged[int].connect(self.activateFilterButton)
        # self.filterOutputMin_edit.editingFinished.connect(self.activateFilterButton)
        # self.filterOutputMax_edit.editingFinished.connect(self.activateFilterButton)
        # self.filter_button.clicked.connect(self.filter)
        # ........ DATA PAGE: DELETE TAB ...................
        self.delete_button.clicked.connect(self.delete)
        self.changeOutputs_button.clicked.connect(self.updateOutputValues)
        self.resetDeleteTable_button.clicked.connect(self.redrawDeleteTable)
        self.delete_table.itemChanged.connect(self.deleteTableCellChanged)
        self.delete_table.verticalScrollBar().valueChanged.connect(
            self.scrollDeleteTable
        )
        self.delegate = uqSetupFrame.MyItemDelegate(self)
        self.delete_table.setItemDelegate(self.delegate)

        self._analysis_dialog = None
        self._results_box = None

    def refresh(self):
        numSims = len(self.dat.uqSimList)
        self.simulationTable.setRowCount(numSims)
        for i in range(numSims):
            self.updateSimTableRow(i)

        if numSims == 0:
            # self.initFilter()
            self.dataTabs.setEnabled(False)

    def simSelected(self):
        selectedIndexes = self.simulationTable.selectedIndexes()
        if not selectedIndexes:
            self.infoGroupBox.hide()
            self.infoTable.setEnabled(False)
            self.cloneSimulationButton.setEnabled(False)
            self.deleteSimulationButton.setEnabled(False)
            self.saveSimulationButton.setEnabled(False)
            self.dataTabs.setEnabled(False)
            self.delete_table.clear()
            self.delete_table.setRowCount(0)
            self.delete_table.setColumnCount(0)
            return
        self.infoGroupBox.show()
        self.dataTabs.setEnabled(False)  # Prevent uq toolbox changes
        self.infoTable.setEnabled(True)
        self.cloneSimulationButton.setEnabled(True)
        self.deleteSimulationButton.setEnabled(True)
        self.saveSimulationButton.setEnabled(True)

        row = selectedIndexes[0].row()
        sim = self.dat.uqSimList[row]

        # Num inputs
        item = QTableWidgetItem(str(sim.getNumInputs()))
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        flags = item.flags()
        mask = ~(Qt.ItemIsEditable)
        item.setFlags(flags & mask)
        self.infoTable.setItem(self.numInputsRow, 0, item)

        # Num outputs
        item = QTableWidgetItem(str(sim.getNumOutputs()))
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        flags = item.flags()
        mask = ~(Qt.ItemIsEditable)
        item.setFlags(flags & mask)
        self.infoTable.setItem(self.numOutputsRow, 0, item)

        # Sample size
        item = QTableWidgetItem(str(sim.getNumSamples()))
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        flags = item.flags()
        mask = ~(Qt.ItemIsEditable)
        item.setFlags(flags & mask)
        self.infoTable.setItem(self.sampleSizeRow, 0, item)

        # Sampling scheme
        item = QTableWidgetItem(SamplingMethods.getFullName(sim.getSampleMethod()))
        flags = item.flags()
        mask = ~(Qt.ItemIsEditable)
        item.setFlags(flags & mask)
        self.infoTable.setItem(self.schemeRow, 0, item)

        # Resize table
        self.infoTable.resizeColumnsToContents()
        maxWidth = (
            2 + self.infoTable.verticalHeader().width() + self.infoTable.columnWidth(0)
        )
        if self.infoTable.verticalScrollBar().isVisible():
            maxWidth += self.infoTable.verticalScrollBar().width()
        self.infoTable.setMaximumWidth(maxWidth)
        self.infoGroupBox.setMaximumWidth(maxWidth + 22)
        maxHeight = 4
        for i in range(4):
            maxHeight += self.infoTable.rowHeight(i)
        self.infoTable.setMaximumHeight(maxHeight)

        self.freeze()
        self.initUQToolBox()
        self.dataTabs.setEnabled(True)
        self.unfreeze()
        QCoreApplication.processEvents()

    def simDescriptionChanged(self, row, column):
        if column == uqSetupFrame.nameCol:
            sim = self.dat.uqSimList[row]
            item = self.simulationTable.item(row, column)
            newName = item.text()
            sim.setModelName(newName)

    def setProgressBarNumErrors(self, progressBar, value):
        formatString = "%v / %m  # errors: " + str(value)
        progressBar.setFormat(formatString)

    def setProgressBarErrorStyle(self, progressBar, numGood, numError, numTotal):
        styleLeft = """
QProgressBar:horizontal {
border: 1px solid gray;
border-radius: 3px;
background: qlineargradient(spread:pad, x1: 0, y1: 0.5, x2: 1, y2: 0.5, """

        styleRight = """);
padding: 1px;
text-align: center;
}

QProgressBar::chunk:horizontal {
background: qlineargradient(spread:pad, x1: 0, y1: 0.5, x2: 1, y2: 0.5, stop: 0 rgba(128, 255, 128 , 255), stop: 0.5 rgba(0, 226, 0, 255), stop: 1 rgba(0, 192, 0, 255));
}
"""
        progressBar.setValue(numGood)
        if numError == 0:
            styleMiddle = "stop: 0 lightgrey stop: 1 lightgrey"
        else:
            if numGood == 0:
                styleMiddle = "stop: 0 red, "
            else:
                styleMiddle = (
                    "stop: 0 lightgrey, stop: %g lightgrey, stop: %g red, "
                    % ((numGood - 0.4) / numTotal, (numGood + 0.4) / numTotal)
                )

            if numGood + numError == numTotal:
                styleMiddle = styleMiddle + "stop: 1 red"
            else:
                styleMiddle = (
                    styleMiddle
                    + "stop: %g red, stop: %g lightgrey, stop: 1 lightgrey"
                    % (
                        (numGood + numError - 0.4) / numTotal,
                        (numGood + numError + 0.4) / numTotal,
                    )
                )

        style = styleLeft + styleMiddle + styleRight

        progressBar.setStyleSheet(style)

    def addSimulation(self):
        nodes = list(self.dat.flowsheet.nodes.keys())

        updateDialog = updateUQModelDialog(self.dat, self)
        result = updateDialog.exec_()
        if result == QDialog.Rejected:
            return

        simDialog = SimSetup(
            # WHY self.dat.uqModel is set in updateUQModelDialog.accept(),
            # but this is not detected by pylint, causing the error
            self.dat.uqModel,  # pylint: disable=no-member
            self.dat,
            returnDataSignal=self.addDataSignal,
            parent=self,
        )
        # result = simDialog.exec_()
        simDialog.show()
        # if result == QDialog.Rejected:
        #    return
        # data = simDialog.getData()
        # data.setSession(self.dat)
        # self.dat.uqSimList.append(data)

        # Update table
        # self.updateSimTable()

    def cloneSimulation(self):
        # Get selected row
        row = self.simulationTable.selectedIndexes()[0].row()
        sim = copy.deepcopy(self.dat.uqSimList[row])  # Create copy of sim
        sim.clearRunState()
        sim.turbineSession = None
        sim.turbineJobIds = []
        self.dat.uqSimList.append(sim)  # Add to simulation list
        res = Results()
        res.uq_add_result(sim)
        self.dat.uqFilterResultsList.append(sim)

        # Update table
        self.updateSimTable()

    def loadSimulation(self):

        self.freeze()

        # Get file name
        if platform.system() == "Windows":
            allFiles = "*.*"
        else:
            allFiles = "*"
        fileName, selectedFilter = QFileDialog.getOpenFileName(
            self,
            "Open Simulation Ensemble",
            "",
            "Psuade Files (*.dat *.psuade *.filtered);;CSV (Comma delimited) (*.csv);;All files (%s)"
            % allFiles,
        )
        if len(fileName) == 0:
            self.unfreeze()
            return

        if fileName.endswith(".csv"):
            data = LocalExecutionModule.readSampleFromCsvFile(fileName)
        else:
            try:
                data = LocalExecutionModule.readSampleFromPsuadeFile(fileName)
            except:
                import traceback

                traceback.print_exc()
                QMessageBox.critical(
                    self,
                    "Incorrect format",
                    "File does not have the correct format! Please consult the users manual about the format.",
                )
                logging.getLogger("foqus." + __name__).exception(
                    "Error loading psuade file."
                )
                self.unfreeze()
                return
        data.setSession(self.dat)
        self.dat.uqSimList.append(data)

        res = Results()
        res.uq_add_result(data)
        self.dat.uqFilterResultsList.append(res)

        # Update table
        self.updateSimTable()
        self.dataTabs.setEnabled(True)
        self.unfreeze()

    def updateSimTable(self):
        # Update table
        numSims = len(self.dat.uqSimList)
        self.simulationTable.setRowCount(numSims)
        self.updateSimTableRow(numSims - 1)
        self.simulationTable.selectRow(numSims - 1)

    def deleteSimulation(self):
        # Get selected row
        row = self.simulationTable.selectedIndexes()[0].row()

        # Delete simulation
        self.dat.uqSimList.pop(row)
        self.dat.uqFilterResultsList.pop(row)
        self.dataTabs.setCurrentIndex(0)
        self.refresh()
        numSims = len(self.dat.uqSimList)
        if numSims > 0:
            if row >= numSims:
                self.simulationTable.selectRow(numSims - 1)
                row = numSims - 1
            sim = self.dat.uqSimList[row]

    def saveSimulation(self):
        psuadeFilter = "Psuade Files (*.dat)"
        csvFilter = "Comma-Separated Values (Excel) (*.csv)"

        # Get selected row
        row = self.simulationTable.selectedIndexes()[0].row()

        sim = self.dat.uqSimList[row]
        fileName, selectedFilter = QFileDialog.getSaveFileName(
            self, "File to Save Ensemble", "", psuadeFilter + ";;" + csvFilter
        )
        if fileName == "":
            return
        if selectedFilter == psuadeFilter:
            sim.writeToPsuade(fileName)
        else:
            sim.writeToCsv(fileName)

    def editSim(self):
        sender = self.sender()
        row = sender.property("row")

        viewOnly = True
        if sender.text() == "Revise":
            viewOnly = False
        self.changeDataSignal.disconnect()
        self.changeDataSignal.connect(lambda data: self.changeDataInSimTable(data, row))
        simDialog = SimSetup(
            self.dat.uqSimList[row],
            self.dat,
            viewOnly,
            returnDataSignal=self.changeDataSignal,
            parent=self,
        )
        # result = simDialog.exec_()
        result = simDialog.show()
        # if result == QDialog.Rejected:
        #     return

    def addDataToSimTable(self, data):
        if data is None:
            return
        # data = simDialog.getData()
        self.dat.uqSimList.append(data)
        res = Results()
        res.uq_add_result(data)
        self.dat.uqFilterResultsList.append(res)

        self.updateSimTable()

    def changeDataInSimTable(self, data, row):
        if data is None:
            return
        # data = simDialog.getData()
        self.dat.uqSimList[row] = data
        res = Results()
        res.uq_add_result(data)
        self.dat.uqFilterResultsList[row] = res

        self.updateSimTableRow(row)

    def updateSession(self, row, s):
        item = self.simulationTable.item(row, self.sessCol)
        if item is None:
            item = QTableWidgetItem()
        item.setText(s)
        self.simulationTable.setItem(row, self.sessCol, item)
        self.resizeColumns()

    def updateSimTableRow(self, row):
        data = self.dat.uqSimList[row]
        # Ensemble number
        # print 'ensemble'
        item = self.simulationTable.item(row, self.numberCol)
        if item is None:
            item = QTableWidgetItem()
        item.setText(str(row + 1))
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        flags = item.flags()
        mask = ~(Qt.ItemIsEditable)
        item.setFlags(flags & mask)
        self.simulationTable.setItem(row, self.numberCol, item)

        item = self.simulationTable.item(row, self.sessCol)
        if item is None:
            item = QTableWidgetItem()
        if data.turbineSession is not None:
            item.setText(data.turbineSession)
        else:
            item.setText("")
        self.simulationTable.setItem(row, self.sessCol, item)
        # Name
        # print 'name'
        item = self.simulationTable.item(row, self.nameCol)
        if item is None:
            item = QTableWidgetItem()
        item.setText(data.getModelName())
        self.simulationTable.setItem(row, self.nameCol, item)
        # Status
        # print 'status'
        progressBar = self.simulationTable.cellWidget(row, self.statusCol)
        newProgressBar = False
        if progressBar is None:
            newProgressBar = True
            progressBar = QProgressBar()
        progressBar.setStyleSheet(self.progressBarDefaultStyle)
        progressBar.setMinimum(0)
        if data.getRunType() == Model.EMULATOR:
            progressBar.setMaximum(data.getNumOutputs())
            formatString = "%v / %m output(s) computed"
        else:
            progressBar.setMaximum(data.getNumSamples())
            try:
                index = data.getOutputNames().index("graph.error")
                errorCount = sum(row[index] > 0 for row in data.getOutputData())
                # errorCount = np.count_nonzero(outDataErrors)
                formatString = "%v / %m  # errors: " + str(errorCount)
            except:
                formatString = "%v / %m"
        progressBar.setFormat(formatString)
        runState = data.getRunState().tolist()
        runCount = runState.count(True)
        progressBar.setValue(runCount)
        if newProgressBar:
            self.simulationTable.setCellWidget(row, self.statusCol, progressBar)

        # Edit
        # print 'edit'
        editButton = self.simulationTable.cellWidget(row, self.editCol)
        newEditButton = False
        if editButton is None:
            newEditButton = True
            editButton = QPushButton()
        if (
            runCount == data.getNumSamples()
            or data.getFromFile() == True
            or data.getNumSamplesAdded() > 0
        ):  # Samples added from refinement
            editButton.setText("View")
        else:
            editButton.setText("Revise")

        editButton.setProperty("row", row)
        if newEditButton:
            editButton.clicked.connect(self.editSim)
            self.simulationTable.setCellWidget(row, self.editCol, editButton)

        # Launch
        # print 'launch'
        launchButton = self.simulationTable.cellWidget(row, self.launchCol)
        newLaunchButton = False
        if launchButton is None:
            newLaunchButton = True
            launchButton = QPushButton()
        launchButton.setText("Launch")
        # if data.getFromFile() == True:
        #     launchButton.setEnabled(False)
        if runCount == data.getNumSamples():
            if data.getSampleMethod() == SamplingMethods.METIS or data.getFromFile():
                launchButton.setText("Sample Refinement")
            else:
                launchButton.setEnabled(False)
        elif (
            data.getFromFile()
        ):  # Should not be able to launch or refine sample loaded from file that is not complete
            launchButton.setEnabled(False)
        launchButton.setProperty("row", row)
        if newLaunchButton:
            launchButton.clicked.connect(self.launchSim)
            self.simulationTable.setCellWidget(row, self.launchCol, launchButton)

        # Analyze
        # print 'analyze'
        analyzeButton = self.simulationTable.cellWidget(row, self.analyzeCol)
        newAnalyzeButton = False
        if analyzeButton is None:
            newAnalyzeButton = True
            analyzeButton = QPushButton()
        analyzeButton.setText("Analyze")
        analyzeButton.setEnabled(runCount == data.getNumSamples())
        analyzeButton.setProperty("row", row)
        if newAnalyzeButton:
            analyzeButton.clicked.connect(self.analyzeSim)
            self.simulationTable.setCellWidget(row, self.analyzeCol, analyzeButton)

        # Resize table
        # print 'resize'
        self.resizeColumns()
        minWidth = (
            2
            + self.simulationTable.columnWidth(0)
            + self.simulationTable.columnWidth(1)
            + self.simulationTable.columnWidth(2)
            + self.simulationTable.columnWidth(3)
            + self.simulationTable.columnWidth(4)
        )
        if self.simulationTable.verticalScrollBar().isVisible():
            minWidth += self.simulationTable.verticalScrollBar().width()
        self.simulationTable.setMinimumWidth(minWidth)

    def launchSim(self):
        sender = self.sender()
        row = sender.property("row")
        sim = self.dat.uqSimList[row]
        if sender.text() == "Launch":
            logging.getLogger("foqus." + __name__).debug(
                "Lauch button pressed, launching UQ ensemble"
            )
            sender.setText("Stop")
            # self.freeze()
            runType = sim.getRunType()
            if runType == Model.LOCAL:
                LocalExecutionModule.startRun(sim)
                time.sleep(0.5)
            elif runType == Model.EMULATOR:
                LocalExecutionModule.startEmulatorRun(sim)
            else:
                # Start flowsheet calculations
                inputNames = sim.getInputNames()
                inputs = sim.getInputData().tolist()
                runState = sim.getRunState()
                nodeKey = sim.getModelName()
                rList = []
                self.runMap = []
                # save current graph inputs
                # will coly this and overwrite sample inputs
                inpDict = self.dat.flowsheet.saveValues()["input"]
                # create the input list for samples to run
                for i in range(len(inputs)):
                    runAlready = runState[i]
                    if not runAlready:
                        # sample not run already
                        # get values
                        vals = self.dat.flowsheet.input.unflatten(
                            inputNames, inputs[i], unScale=False
                        )
                        # append a sample to the run list
                        rList.append(copy.deepcopy(inpDict))
                        # replace input values in added sample
                        for nkey in vals:
                            for vkey in vals[nkey]:
                                rList[-1][nkey][vkey] = vals[nkey][vkey]
                        self.runMap.append(i)
                if self.dat.foqusSettings.runFlowsheetMethod == 1:
                    # run with turbine/foqus to allow parallel jobs
                    # first need to upload the simulation to Turbine
                    fname = "tmp_to_turbine_uq"
                    if sim.turbineSession is not None:
                        self.runMap = list(range(len(inputs)))
                        self.gThread = self.dat.flowsheet.runListAsThread(
                            sid=sim.turbineSession,
                            jobIds=sim.turbineJobIds,
                            useTurbine=True,
                            resubs=sim.turbineResub,
                        )
                    else:
                        self.dat.flowsheet.uploadFlowseetToTurbine(
                            dat=self.dat, reset=False
                        )
                        self.gThread = self.dat.flowsheet.runListAsThread(
                            rList, useTurbine=True
                        )
                elif self.dat.foqusSettings.runFlowsheetMethod == 0:
                    # local runs
                    self.gThread = self.dat.flowsheet.runListAsThread(
                        rList, useTurbine=False
                    )
                else:
                    raise Exception("Invalid Run Mode")
            self.checkThread = checkingThread(row, self)
            self.checkThread.runsFinishedSignal.connect(self.runsFinishedSignal.emit)
            self.checkThread.start()
        elif sender.text() == "Stop":
            if self.dat.foqusSettings.runFlowsheetMethod == 1:
                stopDialog = stopEnsembleDialog(self)
                if not self.gThread.allSubmitted:
                    stopDialog.disconnectButton.setEnabled(False)
                stopDialog.exec_()
                if stopDialog.buttonCode == 0:
                    pass
                elif stopDialog.buttonCode == 1:
                    logging.getLogger("foqus." + __name__).debug(
                        "Stop button pressed, disconnecting from Turbine"
                        "leaving Turbine session running"
                    )
                    self.checkThread.rtDisconnect = True
                elif stopDialog.buttonCode == 2:
                    logging.getLogger("foqus." + __name__).debug(
                        "Stop button pressed, stopping UQ ensemble"
                    )
                    self.checkThread.stop = True
                stopDialog.destroy()
            else:
                logging.getLogger("foqus." + __name__).debug(
                    "Stop button pressed, stopping UQ ensemble"
                )
                self.checkThread.stop = True
        else:  # Adaptive Sampling
            # Get number of samples to add
            numToAdd, ok = QInputDialog.getInt(
                self,
                "Samples to Add",
                "Number of samples to add:",
                min([100, sim.getNumSamples()]),
                1,
                sim.getNumSamples(),
            )
            if not ok:
                return

            # Get output for refinement
            y = 1
            if sim.getNumOutputs() > 1:
                output, ok = QInputDialog.getItem(
                    self,
                    "Output Selection",
                    "Select Output to refine:",
                    sim.getOutputNames(),
                )
                if not ok:
                    return
                y = sim.getOutputNames().index(output) + 1

            self.freeze()
            Common.initFolder(SampleRefiner.dname)
            fname = Common.getLocalFileName(
                SampleRefiner.dname, sim.getModelName().split()[0], ".dat"
            )
            sim.writeToPsuade(fname)
            # Common.restoreFromArchive('psuadeMetisInfo', sim.getID())
            if sim.existsInArchive("psuadeMetisInfo"):
                sim.restoreFromArchive("psuadeMetisInfo")
            if sim.existsInArchive("psuadeGMetisInfo"):
                sim.restoreFromArchive("psuadeGMetisInfo")

            outfile = SampleRefiner.adaptiveSample(
                fname, y, sim.getOrigNumSamples(), numToAdd
            )
            if outfile is None:
                return
            newdata = LocalExecutionModule.readSampleFromPsuadeFile(outfile)
            newdata.setModelName(sim.getModelName())
            newdata.setOrigNumSamples(sim.getOrigNumSamples())
            newdata.setNumSamplesAdded(numToAdd)
            newdata.setFromFile(sim.getFromFile())
            newdata.setRunType(sim.getRunType())
            newdata.setDriverName(sim.getDriverName())
            newdata.setSampleRSType(sim.getSampleRSType())
            emulatorOutputStatus = sim.getEmulatorOutputStatus()
            for i, status in enumerate(emulatorOutputStatus):
                newdata.setEmulatorOutputStatus(i, status)
            newdata.setEmulatorTrainingFile(sim.getEmulatorTrainingFile())
            newdata.setInputDistributions(sim.getInputDistributions())
            # Common.archiveFile('psuadeMetisInfo', newdata.getID())
            newdata.setSession(sim.getSession())
            if os.path.exists("psuadeMetisInfo"):
                newdata.archiveFile("psuadeMetisInfo")
                os.remove("psuadeMetisInfo")
            if os.path.exists("psuadeGMetisInfo"):
                newdata.archiveFile("psuadeGMetisInfo")
                os.remove("psuadeGMetisInfo")

            # add to simulation table, select new data
            self.dat.uqSimList.append(newdata)
            res = Results()
            res.uq_add_result(newdata)
            # WHY the fact that self.dat.uqFilterResultsList is being called directly seems to be a real error,
            # which suggests that this part of the code is not being executed
            # it's possible that the append() method should be called instead
            self.dat.uqFilterResultsList(res)  # TODO pylint: disable=not-callable

            # print 'here1'
            self.updateSimTable()
            # print 'here2'
            # reset components
            self.unfreeze()

    def analyzeSim(self):
        sender = self.sender()
        row = sender.property("row")
        sim = self.dat.uqSimList[row]

        dialog = AnalysisDialog(row + 1, sim, self)

        self._analysis_dialog = dialog
        res = dialog.open()

    def resizeColumns(self):
        self.simulationTable.resizeColumnsToContents()
        self.simulationTable.setColumnWidth(self.statusCol, 200)

    def resultsBox(self, numSuccessful, numSamples):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setWindowTitle("FOQUS Run Finished")
        msgBox.setText("%d of %d runs were successful!" % (numSuccessful, numSamples))
        result = msgBox.open()
        self.refreshFilterData(updateResult=True)
        return result

    # =========================== START Brenda's stuff =========================

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
        row = self.simulationTable.selectedIndexes()[0].row()
        data = self.dat.uqSimList[row]

        newdata = data.getSubSample(indices)

        newdata.setModelName(data.getModelName().split(".")[0] + ".filtered")
        newdata.setSession(self.dat)

        # add to simulation table, select new data
        self.dat.uqSimList.append(newdata)
        res = Results()
        res.uq_add_result(newdata)
        self.dat.uqFilterResultsList.append(res)

        self.updateSimTable()

        # reset components
        self.unfreeze()

    def refreshFilterData(self, updateResult=False):
        indexes = self.simulationTable.selectedIndexes()
        if len(indexes) == 0:
            return
        row = indexes[0].row()
        data = self.dat.uqSimList[row]

        if updateResult or not self.dat.uqFilterResultsList:
            if not self.dat.uqFilterResultsList:
                self.dat.uqFilterResultsList = [None] * len(self.dat.uqSimList)
            res = Results()
            res.uq_add_result(data)
            self.dat.uqFilterResultsList[row] = res
        else:
            res = self.dat.uqFilterResultsList[row]

        # newDat = copy.deepcopy(self.dat)
        # newDat.flowsheet.results = res
        # self.filterWidget.init(newDat)
        self.filterWidget.init(self.dat)
        self.filterWidget.setResults(res)
        self.filterWidget.refreshContents()

    # ........ DATA PAGE: DELETE TAB ...................
    def initDelete(self):

        # TO DO: call initDelete() only if the delete tab is selected

        Common.initFolder(DataProcessor.dname)

        self.freeze()

        # get selected row
        row = self.simulationTable.selectedIndexes()[0].row()
        data = self.dat.uqSimList[row]
        # data = data.getValidSamples() # filter out samples that have no output results

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
        self.delete_table.cellClicked.connect(self.activateDeleteButton)
        self.delete_table.setColumnCount(self.nInputs + self.nOutputs + 1)
        self.delete_table.setRowCount(self.nSamples + 1)
        self.delete_table.setHorizontalHeaderLabels(
            ("Variables",) + inputNames + outputNames
        )
        self.delete_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.delete_table.customContextMenuRequested.connect(self.popup)
        self.delete_table.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.delete_table.verticalHeader().customContextMenuRequested.connect(
            self.popup
        )
        sampleLabels = tuple([str(i) for i in range(1, self.nSamples + 1)])
        self.delete_table.setVerticalHeaderLabels(("Sample #",) + sampleLabels)
        inputColor = QtGui.QColor(255, 0, 0, 50)  # translucent red
        inputRefinedColor = QtGui.QColor(255, 0, 0, 100)
        #        mask = ~(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
        mask = ~(Qt.ItemIsEditable)
        checkboxMask = ~(Qt.ItemIsSelectable | Qt.ItemIsEditable)
        end = self.nSamples

        # Blank corner cell
        item = QTableWidgetItem()
        flags = item.flags()
        item.setFlags(flags & mask)
        self.delete_table.setItem(0, 0, item)

        self.deleteScrollRow = 1
        if end > 15:
            end = 15
        for r in range(end):
            item = QTableWidgetItem()
            flags = item.flags()
            item.setFlags(flags & checkboxMask)
            item.setCheckState(Qt.Unchecked)
            self.delete_table.setItem(r + 1, 0, item)

        for c in range(self.nInputs):  # populate input values
            item = QTableWidgetItem()
            flags = item.flags()
            item.setFlags(flags & mask)
            self.delete_table.setItem(0, c + 1, item)
            for r in range(end):
                item = QTableWidgetItem(self.format % self.inputData[r][c])
                flags = item.flags()
                item.setFlags(flags & mask)
                if r < self.nSamples - self.nSamplesAdded:
                    color = inputColor
                else:
                    color = inputRefinedColor
                item.setBackground(color)
                self.delete_table.setItem(r + 1, c + 1, item)
        for c in range(self.nOutputs):  # output values populated in redrawDeleteTable()
            item = self.delete_table.item(0, self.nInputs + c + 1)
            if item is None:
                item = QTableWidgetItem()
                self.delete_table.setItem(0, self.nInputs + c + 1, item)
            flags = item.flags()
            item.setFlags(flags & mask)
            item.setCheckState(Qt.Unchecked)

            for r in range(end):
                item = self.delete_table.item(r + 1, self.nInputs + c + 1)
                if item is None:
                    item = QTableWidgetItem()
                    self.delete_table.setItem(r + 1, self.nInputs + c + 1, item)
        self.redrawDeleteTable()

        self.unfreeze()

    def popup(self, pos):
        menu = QMenu()
        checkAction = menu.addAction("Check selected rows")
        unCheckAction = menu.addAction("Uncheck selected rows")
        action = menu.exec_(self.delete_table.mapToGlobal(pos))
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
                    for i in self.delete_table.selectionModel().selection().indexes()
                ]
            )
            nSamples = self.delete_table.rowCount() - 1
            for r in rows:
                item = self.delete_table.item(r, 0)
                if item is None:
                    item = QTableWidgetItem()
                    flags = item.flags()
                    mask = ~(Qt.ItemIsSelectable | Qt.ItemIsEditable)
                    item.setFlags(flags & mask)
                    item.setCheckState(check)
                    self.delete_table.setItem(r, 0, item)
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
        mask = ~(Qt.ItemIsEditable)
        checkboxMask = ~(Qt.ItemIsSelectable | Qt.ItemIsEditable)
        numRows = self.delete_table.rowCount()
        end = first + 15
        if end > numRows:
            end = numRows
        for r in range(first, end):
            item = self.delete_table.item(r, 0)
            if item is None:
                item = QTableWidgetItem()
                flags = item.flags()
                item.setFlags(flags & checkboxMask)
                item.setCheckState(Qt.Unchecked)
                self.delete_table.setItem(r, 0, item)
            for c in range(self.nInputs):  # populate input values
                item = self.delete_table.item(r, c + 1)
                if item is None:
                    item = QTableWidgetItem(self.format % self.inputData[r - 1][c])
                    flags = item.flags()
                    item.setFlags(flags & mask)
                    if r - 1 < self.nSamples - self.nSamplesAdded:
                        color = inputColor
                    else:
                        color = inputRefinedColor
                    item.setBackground(color)
                    self.delete_table.setItem(r, c + 1, item)
            if isinstance(self.outputData, numpy.ndarray):
                for c in range(self.nOutputs):  # populate output values
                    item = self.delete_table.item(r, self.nInputs + c + 1)
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
                        self.delete_table.setItem(r, self.nInputs + c + 1, item)

        self.isDrawingDeleteTable = False

    def redrawDeleteTable(self):
        # Does not rewrite input values for speed purposes.  These never change

        self.isDrawingDeleteTable = True
        self.freeze()

        # get selected row
        row = self.simulationTable.selectedIndexes()[0].row()
        data = self.dat.uqSimList[row]
        data = data.getValidSamples()  # filter out samples that have no output results

        # populate table
        ##        nInputs = data.getNumInputs()
        ##        nOutputs = data.getNumOutputs()
        ##        nSamples = data.getNumSamples()

        outputColor = QtGui.QColor(255, 255, 0, 50)  # translucent yellow
        outputRefinedColor = QtGui.QColor(255, 255, 0, 100)  # translucent yellow
        for c in range(self.nInputs):
            item = self.delete_table.item(0, c + 1)
            item.setCheckState(Qt.Unchecked)
            for r in range(self.nSamples):
                item = self.delete_table.item(r + 1, 0)
                if item is not None:
                    item.setCheckState(Qt.Unchecked)

        for c in range(self.nOutputs):  # populate output values
            item = self.delete_table.item(0, self.nInputs + c + 1)
            item.setCheckState(Qt.Unchecked)
            # for r in xrange(self.nSamples):
            for r in range(self.deleteScrollRow - 1, self.deleteScrollRow + 14):
                item = self.delete_table.item(r + 1, self.nInputs + c + 1)
                if item is not None:
                    if isinstance(self.outputData, numpy.ndarray) and not numpy.isnan(
                        self.outputData[r][c]
                    ):
                        item.setText(self.format % self.outputData[r][c])
                    else:
                        item.setText("")
                    if r < self.nSamples - self.nSamplesAdded:
                        color = outputColor
                    else:
                        color = outputRefinedColor
                    item.setBackground(outputColor)

        self.delete_table.resizeRowsToContents()
        self.delete_table.resizeColumnsToContents()

        self.delete_table.setEnabled(True)
        self.delete_button.setEnabled(False)
        self.changeOutputs_button.setEnabled(False)

        self.isDrawingDeleteTable = False
        self.unfreeze()

    def getDeleteSelections(self):

        nSamples = self.delete_table.rowCount() - 1
        nVars = self.delete_table.columnCount() - 1

        # get selected row
        row = self.simulationTable.selectedIndexes()[0].row()
        data = self.dat.uqSimList[row]
        data = data.getValidSamples()  # filter out samples that have no output results

        # get data info
        nInputs = data.getNumInputs()
        nOutputs = data.getNumOutputs()

        # get selections
        samples = []
        vars = []
        for i in range(1, nSamples + 1):
            item = self.delete_table.item(i, 0)
            if (item is not None) and item.checkState() == Qt.Checked:
                samples.append(i - 1)
        for i in range(1, nVars + 1):
            item = self.delete_table.item(0, i)
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
                if (
                    (nSamples - len(samples) > 0)
                    and (nInputs - len(inVars) > 0)
                    and (nOutputs - len(outVars) > 0)
                ):
                    b = True

            self.delete_button.setEnabled(b)
            return b

    def enableDelete(self, b):
        self.delete_table.setEnabled(b)
        self.delete_button.setEnabled(b)

    def delete(self):

        # check arguments
        if not self.activateDeleteButton(0, 0):
            return

        self.enableDelete(False)
        self.freeze()

        # get selected row
        row = self.simulationTable.selectedIndexes()[0].row()
        data = self.dat.uqSimList[row]
        # data = data.getValidSamples() # filter out samples that have no output results
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

        # outfile = DataProcessor.delete(fname, nInputs, nOutputs, nSamples, inVars, outVars, samples)
        #
        # newdata = LocalExecutionModule.readSampleFromPsuadeFile(outfile)
        newdata.setModelName(data.getModelName().split(".")[0] + ".deleted")
        newdata.setSession(self.dat)

        # add to simulation table, select new data
        self.dat.uqSimList.append(newdata)
        res = Results()
        res.uq_add_result(newdata)
        self.dat.uqFilterResultsList.append(res)
        self.updateSimTable()

        self.delete_table.resizeColumnsToContents()

        # reset components
        self.unfreeze()

    def deleteTableCellChanged(self, item):
        if self.isDrawingDeleteTable:
            return

        index = self.delete_table.indexFromItem(item)
        row = index.row()
        col = index.column()

        # print 'modified row %s col %s' % (row, col)

        modifiedColor = QtGui.QColor(0, 250, 0, 100)  # translucent green

        # get selected row
        simRow = self.simulationTable.selectedIndexes()[0].row()
        # origData = self.dat.uqSimList[simRow]
        # data = origData.getValidSamples() # filter out samples that have no output results
        data = self.dat.uqSimList[simRow]

        nInputs = data.getNumInputs()
        outputData = data.getOutputData()
        nOutputs = data.getNumOutputs()
        nSamples = data.getNumSamples()

        if col <= nInputs or row == 0:
            return

        if len(outputData) == 0:
            item.setBackground(modifiedColor)
        else:
            origValue = outputData[row - 1, col - nInputs - 1]
            value = float(item.text())

            if value != origValue:
                item.setBackground(modifiedColor)

        self.changeOutputs_button.setEnabled(True)

    def updateOutputValues(self):
        # Warn user
        button = QMessageBox.question(
            self,
            "Change output values?",
            "You are about to permanently change the output values.  This cannot be undone.  Do you want to proceed?",
            QMessageBox.Yes,
            QMessageBox.No,
        )
        if button != QMessageBox.Yes:
            return

        # get selected row
        row = self.simulationTable.selectedIndexes()[0].row()
        origData = self.dat.uqSimList[row]
        # data = origData.getValidSamples() # filter out samples that have no output results
        data = self.dat.uqSimList[row]

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
                item = self.delete_table.item(sampleNum + 1, outputNum + nInputs + 1)
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
