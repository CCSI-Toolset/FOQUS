import platform
import os
import logging
import copy
from foqus_lib.gui.sdoe.updateSDOEModelDialog import *
from foqus_lib.gui.sdoe.sdoeSimSetup import *
from foqus_lib.gui.uq.uqDataBrowserFrame import uqDataBrowserFrame
from foqus_lib.framework.uq.DataProcessor import *
from foqus_lib.framework.uq.RSAnalyzer import *
from foqus_lib.framework.uq.Common import *
from foqus_lib.framework.uq.LocalExecutionModule import *
from foqus_lib.framework.sampleResults.results import Results
from foqus_lib.framework.sdoe import df_utils
from .sdoeAnalysisDialog import sdoeAnalysisDialog
from .sdoePreview import sdoePreview

from PyQt5 import QtCore, uic, QtGui
from PyQt5.QtWidgets import QStyledItemDelegate, QApplication, QTableWidgetItem, \
    QPushButton, QStyle, QDialog, QMessageBox, QMenu, QAbstractItemView
from PyQt5.QtCore import QCoreApplication, QSize, QRect, QEvent
from PyQt5.QtGui import QCursor

from PyQt5 import uic
mypath = os.path.dirname(__file__)
_sdoeSetupFrameUI, _sdoeSetupFrame = \
        uic.loadUiType(os.path.join(mypath, "sdoeSetupFrame_UI.ui"))


class sdoeSetupFrame(_sdoeSetupFrame, _sdoeSetupFrameUI):
    runsFinishedSignal = QtCore.pyqtSignal()
    addDataSignal = QtCore.pyqtSignal(SampleData)
    changeDataSignal = QtCore.pyqtSignal(SampleData)
    format = '%.5f'             # numeric format for table entries in UQ Toolbox
    drawDataDeleteTable = True  # flag to track whether delete table needs to be redrawn

    numberCol = 0
    typeCol = 1
    setupCol = 2
    nameCol = 3

    descriptorCol = 0
    viewCol = 1

    dname = os.path.join(os.getcwd(), 'SDOE_files')

    # This delegate is used to make the checkboxes in the delete table centered
    class MyItemDelegate(QStyledItemDelegate):

        def paint(self, painter, option, index):
            if index.row() == 0 or index.column() == 0:
                textMargin = QApplication.style().pixelMetric(QStyle.PM_FocusFrameHMargin) + 1
                newRect = QStyle.alignedRect(option.direction, Qt.AlignCenter,
                                             QSize(option.decorationSize.width() + 5,
                                                   option.decorationSize.height()),
                                             QRect(option.rect.x() + textMargin, option.rect.y(),
                                                   option.rect.width() - (2 * textMargin),
                                                   option.rect.height()))
                option.rect = newRect
            QStyledItemDelegate.paint(self, painter, option, index)

        def editorEvent(self, event, model, option, index):
            # make sure that the item is checkable
            flags = model.flags(index)
            if not (flags & Qt.ItemIsUserCheckable) or not(flags & Qt.ItemIsEnabled):
                return False
            # make sure that we have a check state
            value = index.data(Qt.CheckStateRole)
            if value is None:
                return False
            # make sure that we have the right event type
            if event.type() == QEvent.MouseButtonRelease:
                textMargin = QApplication.style().pixelMetric(QStyle.PM_FocusFrameHMargin) + 1
                checkRect = QStyle.alignedRect(option.direction, Qt.AlignCenter, option.decorationSize,
                                               QRect(option.rect.x() + (2 * textMargin), option.rect.y(),
                                                     option.rect.width() - (2 * textMargin),
                                                     option.rect.height()))
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

        # Set up simulation ensembles section
        self.addSimulationButton.clicked.connect(self.addSimulation)
        self.addSimulationButton.setEnabled(True)
        self.addDataSignal.connect(self.addDataToSimTable)
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

        self.changeDataSignal.connect(lambda data: self.changeDataInSimTable(data, row))

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
        self.deleteTable.verticalScrollBar().valueChanged.connect(self.scrollDeleteTable)
        self.delegate = sdoeSetupFrame.MyItemDelegate(self)
        self.deleteTable.setItemDelegate(self.delegate)

        # Create SDOE directory
        Common.initFolder(self.dname)

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
        
    def getEnsembleList(self):
        cand_list = []
        hist_list = []
        numFiles = len(self.dat.sdoeSimList)
        for i in range(numFiles):
            if str(self.filesTable.cellWidget(i, self.typeCol).currentText()) == 'Candidate':
                cand_list.append(self.dat.sdoeSimList[i])
            elif str(self.filesTable.cellWidget(i, self.typeCol).currentText()) == 'Previous Data':
                hist_list.append(self.dat.sdoeSimList[i])
        return cand_list, hist_list   # returns sample data structures

    def aggregateEnsembleList(self):
        cand_list, hist_list = self.getEnsembleList()

        cand_csv_list = []
        for cand in cand_list:
            cand_path = os.path.join(self.dname, cand.getModelName())
            if not os.path.exists(cand_path):
                cand.writeToCsv(cand_path, inputsOnly=True)
            cand_csv_list.append(cand_path)

        hist_csv_list = []
        for hist in hist_list:
            hist_path = os.path.join(self.dname, hist.getModelName())
            if not os.path.exists(hist_path):
                hist.writeToCsv(hist_path, inputsOnly=True)
            hist_csv_list.append(hist_path)

        cand_agg, hist_agg = df_utils.check(cand_csv_list, hist_csv_list)
        return cand_agg, hist_agg

    def createAggData(self):
        cand_agg, hist_agg = self.aggregateEnsembleList()  # these are dfs
        cand_agg.insert(0, "__id", range(1, cand_agg.shape[0] + 1), True)

        cand_fname = os.path.join(self.dname, 'aggregate_candidates.csv')
        df_utils.write(cand_fname, cand_agg)
        candidateData = LocalExecutionModule.readSampleFromCsvFile(cand_fname, askForNumInputs=False)

        hist_fname = os.path.join(self.dname, 'aggregate_previousData.csv')
        if len(hist_agg) == 0:
            historyData = None
        else:
            hist_agg.insert(0, "__id",  range(cand_agg.shape[0]+1, cand_agg.shape[0]+hist_agg.shape[0]+1), True)
            df_utils.write(hist_fname, hist_agg)
            historyData = LocalExecutionModule.readSampleFromCsvFile(hist_fname, askForNumInputs=False)

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

        simDialog = sdoeSimSetup(self.dat.model, self.dat, returnDataSignal=self.addDataSignal, parent=self)
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
        if platform.system() == 'Windows':
            _allFiles = '*.*'
        else:
            _allFiles = '*'
        fileName, selectedFilter = QFileDialog.getOpenFileName(self, "Open Ensemble", '',
                                                               "CSV (Comma delimited) (*.csv)")
        if len(fileName) == 0:
            self.unfreeze()
            return

        if fileName.endswith('.csv'):
            data = LocalExecutionModule.readSampleFromCsvFile(fileName, False)
        else:
            try:
                data = LocalExecutionModule.readSampleFromPsuadeFile(fileName)
            except:
                import traceback
                traceback.print_exc()
                QtGui.QMessageBox.critical(self, 'Incorrect format',
                                           'File does not have the correct format! Please consult the users manual '
                                           'about the format.')
                logging.getLogger("foqus." + __name__).exception(
                    "Error loading psuade file.")
                self.unfreeze()
                return
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
        psuadeFilter = 'Psuade Files (*.dat)'
        csvFilter = 'Comma-Separated Values (Excel) (*.csv)'

        # Get selected row
        row = self.filesTable.selectedIndexes()[0].row()

        sim = self.dat.sdoeSimList[row]
        fileName, selectedFilter = QFileDialog.getSaveFileName(self,
                                                               "File to Save Ensemble",
                                                               '',
                                                               psuadeFilter + ';;' + csvFilter)
        if fileName == '':
            return
        if selectedFilter == psuadeFilter:
            sim.writeToPsuade(fileName)
        else:
            sim.writeToCsv(fileName, inputsOnly=True)

    def editSim(self):
        sender = self.sender()
        row = sender.property('row')

        self.changeDataSignal.disconnect()
        self.changeDataSignal.connect(lambda data: self.changeDataInSimTable(data, row))

        previewData = self.dat.sdoeSimList[row]
        hname = None
        usf = None
        nusf = None
        irsf = None
        scatterLabel = 'Candidates'
        dialog = sdoePreview(previewData, hname, self.dname, usf, nusf, irsf, scatterLabel, self)
        dialog.show()

    def editAgg(self):
        sender = self.sender()
        _row = sender.property('row')
        candidateData, historyData = self.createAggData()

        previewData = candidateData
        if historyData is not None:
            hname = os.path.join(self.dname, historyData.getModelName())
        else:
            hname = None
        usf = None
        nusf = None
        irsf = None
        scatterLabel = 'Candidates'
        dialog = sdoePreview(previewData, hname, self.dname, usf, nusf, irsf, scatterLabel, self)
        dialog.show()

    def hasCandidates(self):
        cand_list, hist_list = self.getEnsembleList()
        return len(cand_list) > 0

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

        item = self.filesTable.item(row, self.nameCol)
        if item is None:
            item = QTableWidgetItem()
        item.setText(data.getModelName())
        self.filesTable.setItem(row, self.nameCol, item)

        combo = QComboBox()
        combo.addItems(['Candidate', 'Previous Data'])
        self.filesTable.setCellWidget(row, self.typeCol, combo)
        combo.currentTextChanged.connect(self.on_combobox_changed)
        combo.setMinimumContentsLength(13)

        viewButton = self.filesTable.cellWidget(row, self.setupCol)
        newViewButton = False
        if viewButton is None:
            newViewButton = True
            viewButton = QPushButton()
            viewButton.setText('View')
            viewButton.setToolTip('View and plot the candidate set or previous data.')

        viewButton.setProperty('row', row)
        if newViewButton:
            viewButton.clicked.connect(self.editSim)
            self.filesTable.setCellWidget(row, self.setupCol, viewButton)

        # Resize table
        self.resizeColumns()
        minWidth = 2 + self.filesTable.columnWidth(0) + self.filesTable.columnWidth(1) + \
                   self.filesTable.columnWidth(2) + self.filesTable.columnWidth(3)
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
            viewButton.setText('View')

        viewButton.setProperty('row', row)
        if newViewButton:
            viewButton.clicked.connect(self.editAgg)
            self.aggFilesTable.setCellWidget(2, self.viewCol, viewButton)

        candidateData, historyData = self.createAggData()

        item = self.aggFilesTable.item(0, self.descriptorCol)
        item.setText(candidateData.getModelName())
        self.aggFilesTable.setItem(0, self.descriptorCol, item)

        item = self.aggFilesTable.item(1, self.descriptorCol)
        if historyData is None:
            item.setText('None')
        else:
            item.setText(historyData.getModelName())
        self.aggFilesTable.setItem(1, self.descriptorCol, item)

        item = self.aggFilesTable.item(2, self.descriptorCol)
        item.setText(self.dname)
        self.aggFilesTable.setItem(2, self.descriptorCol, item)

        combo = QComboBox()
        combo.addItems(['Uniform Space Filling (USF)', 'Non-Uniform Space Filling (NUSF)',
                        'Input-Response Space Filling (IRSF)'])
        self.aggFilesTable.setCellWidget(3, self.descriptorCol, combo)
        combo.setEnabled(True)

        combo.setToolTip("<ul>"
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
                         "</ul>")

        # Resize table
        self.resizeColumns()
        minWidth = 2 + self.aggFilesTable.columnWidth(0) + self.aggFilesTable.columnWidth(1) + \
                   self.aggFilesTable.columnWidth(2)
        if self.aggFilesTable.verticalScrollBar().isVisible():
            minWidth += self.aggFilesTable.verticalScrollBar().width()
        self.aggFilesTable.setMinimumWidth(minWidth)

    def launchSdoe(self):
        candidateData, historyData = self.createAggData()
        dname = self.dname
        if str(self.aggFilesTable.cellWidget(3, self.descriptorCol).currentText()) == 'Uniform Space Filling (USF)':
            type = 'USF'
        elif str(self.aggFilesTable.cellWidget(3, self.descriptorCol).currentText()) == 'Non-Uniform Space ' \
                                                                                        'Filling (NUSF)':
            type = 'NUSF'
        elif str(self.aggFilesTable.cellWidget(3, self.descriptorCol).currentText()) == 'Input-Response Space ' \
                                                                                        'Filling (IRSF)':
            type = 'IRSF'
        analysis = []

        dialog = sdoeAnalysisDialog(candidateData, dname, analysis, historyData, type, self)
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

        newdata.setModelName(data.getModelName().split('.')[0] + '.filtered')
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
        self.deleteTable.setHorizontalHeaderLabels(('Variables',) + inputNames + outputNames)
        self.deleteTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.deleteTable.customContextMenuRequested.connect(self.popup)
        self.deleteTable.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.deleteTable.verticalHeader().customContextMenuRequested.connect(self.popup)
        sampleLabels = tuple([str(i) for i in range(1, self.nSamples+1)])
        self.deleteTable.setVerticalHeaderLabels(('Sample #',) + sampleLabels)
        inputColor = QtGui.QColor(255, 0, 0, 50)      # translucent red
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
            self.deleteTable.setItem(r+1, 0, item)

        for c in range(self.nInputs):         # populate input values
            item = QTableWidgetItem()
            flags = item.flags()
            item.setFlags(flags & mask)
            self.deleteTable.setItem(0, c+1, item)
            for r in range(end):
                item = QTableWidgetItem(self.format % self.inputData[r][c])
                flags = item.flags()
                item.setFlags(flags & mask)
                if r < self.nSamples - self.nSamplesAdded:
                    color = inputColor
                else:
                    color = inputRefinedColor
                item.setBackground(color)
                self.deleteTable.setItem(r+1, c+1, item)
        for c in range(self.nOutputs):        # output values populated in redrawDeleteTable()
            item = self.deleteTable.item(0, self.nInputs+c+1)
            if item is None:
                item = QTableWidgetItem()
                self.deleteTable.setItem(0, self.nInputs+c+1, item)
            flags = item.flags()
            item.setFlags(flags & mask)
            item.setCheckState(Qt.Unchecked)

            for r in range(end):
                item = self.deleteTable.item(r+1, self.nInputs+c+1)
                if item is None:
                    item = QTableWidgetItem()
                    self.deleteTable.setItem(r+1, self.nInputs+c+1, item)
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
            rows = set([i.row() for i in self.deleteTable.selectionModel().selection().indexes()])
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

        inputColor = QtGui.QColor(255, 0, 0, 50)      # translucent red
        inputRefinedColor = QtGui.QColor(255, 0, 0, 100)
        outputColor = QtGui.QColor(255, 255, 0, 50)   # translucent yellow
        outputRefinedColor = QtGui.QColor(255, 255, 0, 100)   # translucent yellow
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
            for c in range(self.nInputs):         # populate input values
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
                    self.deleteTable.setItem(r, c+1, item)
            if isinstance(self.outputData, numpy.ndarray):
                for c in range(self.nOutputs):        # populate output values
                    item = self.deleteTable.item(r, self.nInputs + c + 1)
                    if item is None:
                        if math.isnan(self.outputData[r-1][c]):
                            item = QTableWidgetItem()
                        else:
                            item = QTableWidgetItem(self.format % self.outputData[r - 1][c])
                        if r - 1 < self.nSamples - self.nSamplesAdded:
                            color = outputColor
                        else:
                            color = outputRefinedColor
                        item.setBackground(color)
                        self.deleteTable.setItem(r, self.nInputs+c+1, item)

        self.isDrawingDeleteTable = False

    def redrawDeleteTable(self):
        # Does not rewrite input values for speed purposes.  These never change

        self.isDrawingDeleteTable = True
        self.freeze()

        # get selected row
        row = self.filesTable.selectedIndexes()[0].row()
        data = self.dat.sdoeSimList[row]
        _data = data.getValidSamples()  # filter out samples that have no output results

        outputColor = QtGui.QColor(255, 255, 0, 50)   # translucent yellow
        outputRefinedColor = QtGui.QColor(255, 255, 0, 100)   # translucent yellow
        for c in range(self.nInputs):
            item = self.deleteTable.item(0, c+1)
            item.setCheckState(Qt.Unchecked)
            for r in range(self.nSamples):
                item = self.deleteTable.item(r+1, 0)
                if item is not None:
                    item.setCheckState(Qt.Unchecked)

        for c in range(self.nOutputs):        # populate output values
            item = self.deleteTable.item(0, self.nInputs+c+1)
            item.setCheckState(Qt.Unchecked)
            for r in range(self.deleteScrollRow - 1, self.deleteScrollRow + 14):
                item = self.deleteTable.item(r+1, self.nInputs+c+1)
                if item is not None:
                    if isinstance(self.outputData, numpy.ndarray) and not numpy.isnan(self.outputData[r][c]):
                        item.setText(self.format % self.outputData[r][c])
                    else:
                        item.setText('')
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
        for i in range(1, nSamples+1):
            item = self.deleteTable.item(i, 0)
            if (item is not None) and item.checkState() == Qt.Checked:
                samples.append(i - 1)
        for i in range(1, nVars+1):
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
            outVars = [x-nInputs for x in outVars]

        return samples, inVars, outVars, nSamples, nInputs, nOutputs  # first 3 output args are 1-indexed

    def activateDeleteButton(self, row, column):

        if row == 0 or column == 0:
            b = False
            samples, inVars, outVars, nSamples, nInputs, nOutputs = self.getDeleteSelections()
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
        fname = Common.getLocalFileName(DataProcessor.dname, data.getModelName().split()[0], '.dat')
        data.writeToPsuade(fname)

        # perform deletion
        samples, inVars, outVars, nSamples, nInputs, nOutputs = self.getDeleteSelections()
        if samples:
            samplesToKeep = [i for i in range(nSamples) if i not in samples]
            newdata = data.getSubSample(samplesToKeep)
        else:
            newdata = copy.deepcopy(data)
        if inVars:
            newdata.deleteInputs(inVars)
        if outVars:
            newdata.deleteOutputs(outVars)

        newdata.setModelName(data.getModelName().split('.')[0] + '.deleted')
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

        modifiedColor = QtGui.QColor(0, 250, 0, 100)      # translucent green

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
        button = QMessageBox.question(self, 'Change output values?',
                                      'You are about to permanently change the output values.  '
                                      'This cannot be undone.  Do you want to proceed?',
                                      QMessageBox.Yes, QMessageBox.No)
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
