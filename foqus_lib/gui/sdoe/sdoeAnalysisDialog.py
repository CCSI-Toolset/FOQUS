import sys
import os
import numpy
import shutil
import textwrap
from datetime import datetime
from tqdm import tqdm


from foqus_lib.framework.uq.SampleData import *
from foqus_lib.framework.uq.Model import *
from foqus_lib.framework.uq.SamplingMethods import *
from foqus_lib.framework.uq.Visualizer import Visualizer
from foqus_lib.framework.uq.Common import *
from foqus_lib.framework.sdoe import sdoe, df_utils
from foqus_lib.gui.common.InputPriorTable import InputPriorTable
from foqus_lib.gui.uq.AnalysisInfoDialog import AnalysisInfoDialog
from .sdoeSetupFrame import *
from .sdoePreview import sdoePreview

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
    includeCol = 0
    nameCol = 1
    typeCol = 2
    minCol = 3
    maxCol = 4

    # Analysis table
    methodCol = 0
    designCol = 1
    sampleCol = 2
    runtimeCol = 3
    plotCol = 4

    testRuntime = []
    analysis = []

    def __init__(self, candidateData, dname, historyData=None, parent=None):
        super(sdoeAnalysisDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.candidateData = candidateData
        self.historyData = historyData
        self.dname = dname

        self.setWindowTitle('Sequential Design of Experiments')


        ## Info table
        mask = ~(Qt.ItemIsEnabled)

        # Num inputs
        item = QTableWidgetItem(str(candidateData.getNumInputs()))
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        flags = item.flags()
        item.setFlags(flags & mask)
        item.setForeground(Qt.black)
        self.infoTable.setItem(self.numInputsRow, 0, item)

        # Candidate File
        item = QTableWidgetItem(candidateData.getModelName())
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        flags = item.flags()
        item.setFlags(flags & mask)
        item.setForeground(Qt.black)
        self.infoTable.setItem(self.candidateFileRow, 0, item)

        # History File
        if historyData == None:
            item = QTableWidgetItem('None')
        else:
            item = QTableWidgetItem(historyData.getModelName())
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        flags = item.flags()
        item.setFlags(flags & mask)
        item.setForeground(Qt.black)
        self.infoTable.setItem(self.historyFileRow, 0, item)

        # Output Directory
        dname = self.dname
        item = QTableWidgetItem(dname)
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        flags = item.flags()
        item.setFlags(flags & mask)
        item.setForeground(Qt.black)
        self.infoTable.setItem(self.outputDirRow, 0, item)

        ## Connections here
        self.loadAnalysisButton.clicked.connect(self.populateAnalysis)
        self.deleteAnalysisButton.clicked.connect(self.deleteAnalysis)
        self.analysisTableGroup.setEnabled(False)
        self.progress_groupBox.setEnabled(False)

        # spin box bounds
        self.maxDesignSize_spin.setMaximum(len(candidateData.getInputData()))

        # Initialize inputSdoeTable
        self.updateInputSdoeTable()
        self.testSdoeButton.clicked.connect(self.testSdoe)
        self.minDesignSize_spin.valueChanged.connect(self.on_min_design_spinbox_changed)
        self.maxDesignSize_spin.valueChanged.connect(self.on_max_design_spinbox_changed)
        self.sampleSize_spin.valueChanged.connect(self.on_sample_size_spinbox_changed)
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

        width = 30 + self.analysisTable.verticalHeader().width()
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

    def updateInfoTable(self, candidateData, historyData):

        item = QTableWidgetItem(str(candidateData.getNumInputs()))
        self.infoTable.setItem(self.numInputsRow, 0, item)

        item = QTableWidgetItem(candidateData.getModelName())
        self.infoTable.setItem(self.candidateFileRow, 0, item)

        if historyData == None:
            item = QTableWidgetItem('None')
        else:
            item = QTableWidgetItem(historyData.getModelName())
        self.infoTable.setItem(self.historyFileRow, 0, item)

        dname = self.dname
        item = QTableWidgetItem(dname)
        self.infoTable.setItem(self.outputDirRow, 0, item)

    def updateInputSdoeTable(self):
        numInputs = self.candidateData.getNumInputs()
        self.inputSdoeTable.setRowCount(numInputs)
        for row in range(numInputs):
            self.updateInputSdoeTableRow(row)

    def updateInputSdoeTableRow(self, row):
        # set names for inputs
        inputNames = self.candidateData.getInputNames()
        item = self.inputSdoeTable.item(row, self.nameCol)
        if item is None:
            item = QTableWidgetItem()
        item.setText(inputNames[row])
        self.inputSdoeTable.setItem(row, self.nameCol, item)

        # create checkboxes for include column
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        self.inputSdoeTable.setCellWidget(row, self.includeCol, checkbox)
        checkbox.setProperty('row', row)


        # create comboboxes for type column
        combo = QComboBox()
        combo.addItems(['Index', 'Space-filling', 'Response', 'Weight'])
        self.inputSdoeTable.setCellWidget(row, self.typeCol, combo)
        combo.model().item(2).setEnabled(False)
        combo.model().item(3).setEnabled(False)


        # Min column
        minValue = min(self.candidateData.getInputData()[:,row])
        item = self.inputSdoeTable.item(row, self.minCol)
        if item is None:
            item = QTableWidgetItem()
        item.setText(str(minValue))
        self.inputSdoeTable.setItem(row, self.minCol, item)

        # Max column
        maxValue = max(self.candidateData.getInputData()[:,row])
        item = self.inputSdoeTable.item(row, self.maxCol)
        if item is None:
            item = QTableWidgetItem()
        item.setText(str(maxValue))
        self.inputSdoeTable.setItem(row, self.maxCol, item)


    def analysisSelected(self):
        selectedIndexes = self.analysisTable.selectedIndexes()
        if not selectedIndexes:
            self.loadAnalysisButton.setEnabled(False)
            self.deleteAnalysisButton.setEnabled(False)
            return
        self.loadAnalysisButton.setEnabled(True)
        self.deleteAnalysisButton.setEnabled(True)

    def updateAnalysisTable(self):
        numAnalysis = len(self.analysis)
        self.analysisTable.setRowCount(numAnalysis)
        for row in range(numAnalysis):
            self.updateAnalysisTableRow(row)

    def updateAnalysisTableRow(self, row):

        # Optimality Method
        item = self.analysisTable.item(row, self.methodCol)
        if item is None:
            item = QTableWidgetItem()
            self.analysisTable.setItem(row, self.methodCol, item)
        optMethod = self.analysis[row][0]
        item.setText(str(optMethod))

        # Design Size
        item = self.analysisTable.item(row, self.designCol)
        if item is None:
            item = QTableWidgetItem()
            self.analysisTable.setItem(row, self.designCol, item)
        designSize = self.analysis[row][1]
        item.setText(str(designSize))

        # Sample Size
        item = self.analysisTable.item(row, self.sampleCol)
        if item is None:
            item = QTableWidgetItem()
            self.analysisTable.setItem(row, self.sampleCol, item)
        sampleSize = self.analysis[row][2]
        item.setText(str(sampleSize))

        # Runtime
        item = self.analysisTable.item(row, self.runtimeCol)
        if item is None:
            item = QTableWidgetItem()
            self.analysisTable.setItem(row, self.runtimeCol, item)
            runtime = round(self.analysis[row][3], 2)
            item.setText(str(runtime))

        # Plot SDOE
        viewButton = self.analysisTable.cellWidget(row, self.plotCol)
        newViewButton = False
        if viewButton is None:
            newViewButton = True
            viewButton = QPushButton()
            viewButton.setText('View')

        viewButton.setProperty('row', row)
        if newViewButton:
            viewButton.clicked.connect(self.editSdoe)
            self.analysisTable.setCellWidget(row, self.plotCol, viewButton)

        self.analysisTable.resizeColumnsToContents()
        self.analysisTable.resizeRowsToContents()

    def deleteAnalysis(self):
        row = self.analysisTable.selectedIndexes()[0].row()
        self.analysis.pop(row)
        self.updateAnalysisTable()

    def populateAnalysis(self):
        self.analysisGroup.setEnabled(True)
        row = self.analysisTable.selectedIndexes()[0].row()
        config_file = self.analysis[row][5]
        self.loadFromConfigFile(config_file)

    def checkInclude(self):
        numInputs = self.candidateData.getNumInputs()
        min_vals = []
        max_vals = []
        include_list = []
        for row in range(numInputs):
            if self.inputSdoeTable.cellWidget(row, self.includeCol).isChecked():
                min_vals.append(self.inputSdoeTable.item(row, self.minCol).text())
                max_vals.append(self.inputSdoeTable.item(row, self.maxCol).text())
                include_list.append(self.inputSdoeTable.item(row, self.nameCol).text())
        return min_vals, max_vals, include_list

    def writeConfigFile(self, test=False):
        timestamp = datetime.now().isoformat()
        outdir = os.path.join(self.dname, timestamp)
        os.makedirs(outdir, exist_ok=False)
        configFile = os.path.join(outdir, 'config.ini')
        f = open(configFile, 'w')

        ## METHOD
        f.write('[METHOD]\n')

        if self.Minimax_radioButton.isChecked():
            f.write('mode = minimax\n')
        elif self.Maximin_radioButton.isChecked():
            f.write('mode = maximin\n')

        f.write('min_design_size = %d\n' % self.minDesignSize_spin.value())
        f.write('max_design_size = %d\n' % self.maxDesignSize_spin.value())
        if test:
            f.write('number_random_starts = 200\n')
        else:
            f.write('number_random_starts = %d\n' % 10**(self.sampleSize_spin.value()))
        f.write('\n')
        ## INPUT
        f.write('[INPUT]\n')
        if self.historyData is None:
            f.write('history_file = \n')
        else:
            f.write('history_file = %s\n' % os.path.join(self.dname, self.historyData.getModelName()))
        f.write('candidate_file = %s\n' % os.path.join(self.dname, self.candidateData.getModelName()))
        min_vals, max_vals, include_list = self.checkInclude()
        f.write('min_vals = %s\n' % ','.join(min_vals))
        f.write('max_vals = %s\n' % ','.join(max_vals))
        f.write('include = %s' % ','.join(include_list))
        f.write('\n')
        f.write('\n')

        ## OUTPUT
        f.write('[OUTPUT]\n')
        f.write('results_dir = %s\n' %outdir)
        f.write('\n')

        f.close()

        return configFile

    def runSdoe(self):

        min_size = self.minDesignSize_spin.value()
        max_size = self.maxDesignSize_spin.value()
        numIter = (max_size + 1) - min_size
        f = open(os.path.join(self.dname, 'tqdm_progress.txt'), 'w')
        for nd in tqdm(range(min_size, max_size+1), file = f):
            config_file = self.writeConfigFile()
            mode, design_size, num_restarts, elapsed_time, outfile = sdoe.run(config_file, nd)
            self.analysis.append([mode, design_size, num_restarts, elapsed_time, outfile, config_file])
            self.analysisTableGroup.setEnabled(True)
            self.updateAnalysisTable()
            self.SDOE_progressBar.setValue((100/numIter) * (nd-min_size+1))
        f.close()
        self.SDOE_progressBar.setValue(0)
        self.analysisGroup.setEnabled(False)


    def testSdoe(self):
        #test using max design size and nd=200
        self.testRuntime = []
        runtime = sdoe.run(self.writeConfigFile(test=True), self.maxDesignSize_spin.value(), test=True)
        self.testSdoeButton.setEnabled(False)
        self.progress_groupBox.setEnabled(True)
        self.updateRunTime(runtime)
        self.testRuntime.append(runtime)

    def on_min_design_spinbox_changed(self):
        # self.updateRunTime(self.testRuntime[0])
        self.designInfo_dynamic.setText('d = %d, n = %d' %(int(self.minDesignSize_spin.value()),
                                                           10 ** int(self.sampleSize_spin.value())))

    def on_max_design_spinbox_changed(self):
        # self.updateRunTime(self.testRuntime[0])
        self.testSdoeButton.setEnabled(True)
        self.designInfo_dynamic.setText('d = %d, n = %d' %(int(self.minDesignSize_spin.value()),
                                                           10 ** int(self.sampleSize_spin.value())))

    def on_sample_size_spinbox_changed(self):
        self.updateRunTime(self.testRuntime[0])
        self.designInfo_dynamic.setText('d = %d, n = %d' %(int(self.minDesignSize_spin.value()),
                                                           10 ** int(self.sampleSize_spin.value())))

    def updateRunTime(self, runtime):
        delta = runtime/200
        estimateTime = int(delta * (10 ** int(self.sampleSize_spin.value())) * \
                       int(self.maxDesignSize_spin.value()-self.minDesignSize_spin.value()+1))
        if estimateTime < 60:
            self.time_dynamic.setText('%d seconds' % estimateTime)
        elif estimateTime < 3600:
            self.time_dynamic.setText('%d min, %d s' % (int(estimateTime/60), estimateTime%60))

        elif estimateTime > 3600:
            timeHr = int(estimateTime/3600)
            timeMin = int((estimateTime - (timeHr*3600))/60)
            timeSec = (estimateTime - (timeHr*3600))%60
            self.time_dynamic.setText('%d h, %d min, %d s' % (timeHr, timeMin, timeSec))

    def editSdoe(self):
        sender = self.sender()
        row = sender.property('row')
        sdoeData = LocalExecutionModule.readSampleFromCsvFile(self.analysis[row][4], False)
        tempdir = os.path.join(*self.analysis[row][4].split(os.sep)[0:-1])
        dirname = os.path.join(os.sep, tempdir)
        dialog = sdoePreview(sdoeData, dirname, self)
        dialog.show()

    def loadFromConfigFile(self, config_file):
        ## Read from config file
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file)
        mode = config['METHOD']['mode']
        min_size = int(config['METHOD']['min_design_size'])
        max_size = int(config['METHOD']['max_design_size'])
        nr = int(config['METHOD']['number_random_starts'])
        hfile = config['INPUT']['history_file']
        cfile = config['INPUT']['candidate_file']
        include = [s.strip() for s in config['INPUT']['include'].split(',')]
        max_vals = [float(s) for s in config['INPUT']['max_vals'].split(',')]
        min_vals = [float(s) for s in config['INPUT']['min_vals'].split(',')]
        outdir = config['OUTPUT']['results_dir']

        ## Populate gui fields with config file info
        if mode == 'minimax':
            self.Minimax_radioButton.setChecked(True)
        elif mode == 'maximin':
            self.Maximin_radioButton.setChecked(True)

        self.minDesignSize_spin.setValue(min_size)
        self.maxDesignSize_spin.setValue(max_size)

        if hfile == '':
            self.historyData = None
        else:
            self.historyData = LocalExecutionModule.readSampleFromCsvFile(hfile, False)
        self.candidateData = LocalExecutionModule.readSampleFromCsvFile(cfile, False)
        self.updateInfoTable(self.candidateData, self.historyData)
        self.updateInputSdoeTable()
        numInputs = self.candidateData.getNumInputs()
        for row in range(numInputs):
            if self.inputSdoeTable.item(row, self.nameCol).text() in include:
                self.inputSdoeTable.cellWidget(row, self.includeCol).setChecked(True)
            else:
                self.inputSdoeTable.cellWidget(row, self.includeCol).setChecked(False)

        self.sampleSize_spin.setValue(int(np.log10(nr)))
        self.updateRunTime(self.testRuntime[0])
        self.designInfo_dynamic.setText('d = %d, n = %d' %(int(self.minDesignSize_spin.value()),
                                                           10 ** int(self.sampleSize_spin.value())))

    def freeze(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

    def semifreeze(self):
        QApplication.setOverrideCursor(QCursor(Qt.BusyCursor))

    def unfreeze(self):
        QApplication.restoreOverrideCursor()