import sys
import os
import numpy
import shutil
import textwrap

from foqus_lib.framework.uq.SampleData import *
from foqus_lib.framework.uq.Model import *
from foqus_lib.framework.uq.SamplingMethods import *
from foqus_lib.framework.uq.Visualizer import Visualizer
from foqus_lib.framework.uq.Common import *
from foqus_lib.framework.sdoe import sdoe
from foqus_lib.gui.common.InputPriorTable import InputPriorTable
from foqus_lib.gui.uq.AnalysisInfoDialog import AnalysisInfoDialog
from foqus_lib.gui.sdoe.sdoeSetupFrame import *

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox, QFileDialog, QCheckBox, \
    QTableWidgetItem, QAbstractItemView, QGridLayout, QDialog, QLabel, \
    QPushButton
from PyQt5.QtGui import QCursor

mypath = os.path.dirname(__file__)
_sdoeAnalysisDialogUI, _sdoeAnalysisDialog = \
    uic.loadUiType(os.path.join(mypath, "sdoeAnalysisDialog_UI.ui"))


class sdoeAnalysisDialog(_sdoeAnalysisDialog, _sdoeAnalysisDialogUI):
    # Info table
    numInputsRow = 0
    candidateFileRow = 1
    historyFileRow = 2
    outputDirRow = 3

    # input SDOE Table
    displayCol = 0
    includeCol = 1
    nameCol = 2
    typeCol = 3
    minCol = 4
    maxCol = 5

    # Analysis table
    numberCol = 0
    designCol = 1
    sampleCol = 2
    runtimeCol = 3
    plotCol = 4


    def __init__(self, candidateData, historyData, dname, parent=None):
        super(sdoeAnalysisDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.candidateData = candidateData
        self.historyData = historyData
        self.dname = dname

        self.setWindowTitle('Sequential Design of Experiments')


        ## Info table
        mask = ~(Qt.ItemIsEnabled)

        # Num inputs
        item = QTableWidgetItem(str(historyData.getNumInputs()))
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        flags = item.flags()
        item.setFlags(flags & mask)
        item.setForeground(Qt.black)
        self.infoTable.setItem(self.numInputsRow, 0, item)

        # Candidate File
        item = QTableWidgetItem(candidateData.getModelName())
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        flags = item.flags()
        item.setFlags(flags & mask)
        item.setForeground(Qt.black)
        self.infoTable.setItem(self.candidateFileRow, 0, item)

        # History File
        item = QTableWidgetItem(historyData.getModelName())
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        flags = item.flags()
        item.setFlags(flags & mask)
        item.setForeground(Qt.black)
        self.infoTable.setItem(self.historyFileRow, 0, item)

        # Output Directory
        dname = self.dname
        item = QTableWidgetItem(dname)
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        flags = item.flags()
        item.setFlags(flags & mask)
        item.setForeground(Qt.black)
        self.infoTable.setItem(self.outputDirRow, 0, item)

        ## Connections here
        self.deleteAnalysisButton.clicked.connect(self.deleteAnalysis)
        self.analysisTableGroup.setEnabled(False)
        self.progress_groupBox.setEnabled(False)

        # Initialize inputSdoeTable
        self.updateInputSdoeTable()
        self.testSdoeButton.clicked.connect(self.testSdoe)
        #self.testSdoeButton.setEnabled(False)
        self.runSdoeButton.clicked.connect(self.runSdoe)

        # Resize tables
        self.infoTable.resizeColumnsToContents()
        self.analysisTable.resizeColumnsToContents()
        self.inputSdoeTable.resizeColumnsToContents()
        self.show()

        width = 2 + self.infoTable.verticalHeader().width() + self.infoTable.columnWidth(0)
        if self.infoTable.verticalScrollBar().isVisible():
            width += self.infoTable.verticalScrollBar().width()
        self.infoTable.setMaximumWidth(width)
        maxHeight = 4
        for i in range(6):
            maxHeight += self.infoTable.rowHeight(i)
        self.infoTable.setMaximumHeight(maxHeight)

        width = 2 + self.inputSdoeTable.verticalHeader().width()
        for i in range(self.inputSdoeTable.columnCount()):
            width += self.inputSdoeTable.columnWidth(i)
        if self.inputSdoeTable.verticalScrollBar().isVisible():
            width += self.inputSdoeTable.verticalScrollBar().width()
        self.inputSdoeTable.setMinimumWidth(width)
        self.inputSdoeTable.setMaximumWidth(width)

        width = 2 + self.analysisTable.verticalHeader().width()
        for i in range(self.analysisTable.columnCount()):
            width += self.analysisTable.columnWidth(i)
        #            print self.analysisTable.columnWidth(i)
        if self.analysisTable.verticalScrollBar().isVisible():
            width += self.analysisTable.verticalScrollBar().width()
        self.analysisTable.setMinimumWidth(width)
        self.analysisTable.setMaximumWidth(width)
        self.analysisTable.setRowCount(0)
        self.analysisTable.itemSelectionChanged.connect(self.analysisSelected)
        self.analysisTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.analysisTable.setWordWrap(True)
        # self.refreshAnalysisTable()
        # self.analysisSelected()

    def updateInputSdoeTable(self):
        numInputs = self.historyData.getNumInputs()
        self.inputSdoeTable.setRowCount(numInputs)
        for row in range(numInputs):
            self.updateInputSdoeTableRow(row)

    def updateInputSdoeTableRow(self, row):
        # set names for inputs
        inputNames = self.historyData.getInputNames()
        item = self.inputSdoeTable.item(row, self.nameCol)
        if item is None:
            item = QTableWidgetItem()
        item.setText(inputNames[row])
        self.inputSdoeTable.setItem(row, self.nameCol, item)

        # create checkboxes for display and include columns
        checkbox1 = QCheckBox()
        checkbox2 = QCheckBox()
        self.inputSdoeTable.setCellWidget(row, self.displayCol, checkbox1)
        self.inputSdoeTable.setCellWidget(row, self.includeCol, checkbox2)
        checkbox1.setProperty('row', row)
        checkbox2.setProperty('row', row)

        # create comboboxes for type column
        combo = QComboBox()
        combo.addItems(['Index', 'Space-filling', 'Response', 'Weight'])
        self.inputSdoeTable.setCellWidget(row, self.typeCol, combo)
        combo.model().item(2).setEnabled(False)
        combo.model().item(3).setEnabled(False)


        # Min column
        minValue = min(min(self.historyData.getInputData()[:,row]), min(self.candidateData.getInputData()[:,row]))
        item = self.inputSdoeTable.item(row, self.minCol)
        if item is None:
            item = QTableWidgetItem()
        item.setText(str(minValue))
        self.inputSdoeTable.setItem(row, self.minCol, item)

        # Max column
        maxValue = max(max(self.historyData.getInputData()[:,row]), max(self.candidateData.getInputData()[:,row]))
        item = self.inputSdoeTable.item(row, self.maxCol)
        if item is None:
            item = QTableWidgetItem()
        item.setText(str(maxValue))
        self.inputSdoeTable.setItem(row, self.maxCol, item)


    def analysisSelected(self):
        selectedIndexes = self.analysisTable.selectedIndexes()
        if not selectedIndexes:
            self.deleteAnalysisButton.setEnabled(False)
            return
        row = selectedIndexes[0].row()
        analysis = self.data.getAnalysisAtIndex(row)
        info = analysis.getAdditionalInfo()
        self.deleteAnalysisButton.setEnabled(True)

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

        # Design Size
        item = self.analysisTable.item(row, self.designCol)
        if item is None:
            item = QTableWidgetItem()
            self.analysisTable.setItem(row, self.designCol, item)
        designSize = analysis.getDesignSize()
        item.setText(str(designSize))

        # Sample Size
        item = self.analysisTable.item(row, self.sampleCol)
        if item is None:
            item = QTableWidgetItem()
            self.analysisTable.setItem(row, self.sampleCol, item)
        sampleSize = analysis.getSampleSize()
        item.setText(str(sampleSize))

        # Runtime
        item = self.analysisTable.item(row, self.runtimeCol)
        if item is None:
            item = QTableWidgetItem()
            self.analysisTable.setItem(row, self.runtimeCol, item)
            runtime = analysis.getRunTime()
            item.setText(str(runtime))

        # Plot SDOE
        plotButton = self.analysisTable.cellWidget(row, self.plotCol)
        newPlotButton = False
        if plotButton is None:
            newPlotButton = True
            plotButton = QPushButton()
            plotButton.setText('Plot SDOE')

        plotButton.setProperty('row', row)
        if newPlotButton:
            plotButton.clicked.connect(self.Plotter.plotSDOE())
            self.analysisTable.setCellWidget(row, self.plotCol, plotButton)

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


    def deleteAnalysis(self):
        row = self.analysisTable.selectedIndexes()[0].row()

        # Delete simulation
        self.data.removeAnalysisByIndex(row)
        self.refreshAnalysisTable()
        numAnalyses = self.data.getNumAnalyses()
        if numAnalyses > 0:
            if row >= numAnalyses:
                self.analysisTable.selectRow(numAnalyses - 1)

    def writeConfigFile(self):
        dname = '/Users/sotorrio1/PycharmProjects/FOQUS-sotorrio1/SDOE_files'
        configFile = os.path.join(dname, 'config.ini')
        f = open(configFile, 'w')
        ## METHOD
        f.write('[METHOD]\n')

        if self.Minimax_radioButton.isChecked():
            f.write('mode = minimax\n')
        elif self.Maximin_radioButton.isChecked():
            f.write('mode = maximin\n')

        f.write('min_design_size = %d\n' % self.minDesignSize_spin.value())
        f.write('max_design_size = %d\n' % self.maxDesignSize_spin.value())
        f.write('\n')
        ## INPUT
        f.write('[INPUT]\n')
        f.write('history_file = /Users/sotorrio1/PycharmProjects/FOQUS-sotorrio1/examples/SDOE/historical_data.csv\n')
        f.write('candidate_file = /Users/sotorrio1/PycharmProjects/FOQUS-sotorrio1/examples/SDOE/candidate.csv\n')
        f.write('min_vals = ')
        for row in range(self.historyData.getNumInputs()-1):
            f.write((self.inputSdoeTable.item(row, self.minCol).text()) + ', ')
        f.write(self.inputSdoeTable.item(self.historyData.getNumInputs()-1, self.minCol).text())
        f.write('\n')

        f.write('max_vals = ')
        for row in range(self.historyData.getNumInputs() - 1):
            f.write((self.inputSdoeTable.item(row, self.maxCol).text()) + ', ')
        f.write(self.inputSdoeTable.item(self.historyData.getNumInputs() - 1, self.maxCol).text())
        f.write('\n')
        f.write('\n')

        ## OUTPUT
        f.write('[OUTPUT]\n')
        f.write('results_dir = %s\n' %dname)
        f.write('\n')

        ## TEST
        f.write('[TEST]\n')
        f.write('number_random_starts = %d\n' %(pow(10,int(self.sampleSize_spin.value()))))

        f.close()

        return configFile

    def runSdoe(self):
        sdoe.run(self.writeConfigFile())
        self.analysisTableGroup.setEnabled(True)

    def testSdoe(self):
        sdoe.test(self.writeConfigFile())
        self.testSdoeButton.setEnabled(False)
        self.progress_groupBox.setEnabled(True)

    def freeze(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

    def semifreeze(self):
        QApplication.setOverrideCursor(QCursor(Qt.BusyCursor))

    def unfreeze(self):
        QApplication.restoreOverrideCursor()