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

    # Analysis table
    numberCol = 0
    designCol = 1
    sampleCol = 2
    runtimeCol = 3
    plotCol = 4


    def __init__(self, candidateData, historyData, parent=None):
        super(sdoeAnalysisDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.candidateData = candidateData
        self.historyData = historyData

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
        dname = '~/SDOE_files/'
        item = QTableWidgetItem(dname)
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        flags = item.flags()
        item.setFlags(flags & mask)
        item.setForeground(Qt.black)
        self.infoTable.setItem(self.outputDirRow, 0, item)

        # Resize tables
        self.infoTable.resizeColumnsToContents()
        self.analysisTable.resizeColumnsToContents()
        self.inputSdoeTable.resizeColumnsToContents()
        self.show()

        width = 2 + self.infoTable.verticalHeader().width() + self.infoTable.columnWidth(0)
        if self.infoTable.verticalScrollBar().isVisible():
            width += self.infoTable.verticalScrollBar().width()
        self.infoTable.setMaximumWidth(width)
        #self.infoGroup.setMinimumWidth(width + 22)
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
        self.inputSdoeTable.setRowCount(0)


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
        self.refreshAnalysisTable()
        self.analysisSelected()

        self.deleteAnalysisButton.clicked.connect(self.deleteAnalysis)


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

    def freeze(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

    def semifreeze(self):
        QApplication.setOverrideCursor(QCursor(Qt.BusyCursor))

    def unfreeze(self):
        QApplication.restoreOverrideCursor()