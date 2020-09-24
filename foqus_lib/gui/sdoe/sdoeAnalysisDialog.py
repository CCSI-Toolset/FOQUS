import os
from datetime import datetime
import configparser

from foqus_lib.framework.sdoe import order, sdoe
from foqus_lib.framework.sdoe.df_utils import load
from .sdoeSetupFrame import *
from .sdoePreview import sdoePreview

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox, QCheckBox, \
    QTableWidgetItem, QAbstractItemView, QPushButton
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
    criterionCol = 4
    plotCol = 5

    testRuntime = []

    def __init__(self, candidateData, dname, analysis = None, historyData=None, type = None, parent=None):
        super(sdoeAnalysisDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.candidateData = candidateData
        self.analysis = []
        self.historyData = historyData
        self.dname = dname
        self.type = type

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
        self.orderAnalysisButton.clicked.connect(self.orderDesign)
        self.deleteAnalysisButton.clicked.connect(self.deleteAnalysis)
        self.testSdoeButton.setEnabled(False)
        self.analysisTableGroup.setEnabled(False)
        self.progress_groupBox.setEnabled(False)
        self.progressNUSF_groupBox.setEnabled(False)

        #USF vs NUSF conditions
        if type == 'NUSF':
            self.Minimax_radioButton.setEnabled(False)
            self.Maximin_radioButton.setChecked(True)
            self.range_groupBox.setHidden(True)
            self.progress_groupBox.setHidden(True)
            self.analysisTable.setHorizontalHeaderLabels(['MWR Value', 'Design Size, d', '# of Random Starts, n', 'Runtime (in sec)', 'Criterion Value', 'Plot SDOE'])
        else:
            self.scalingGroup.setHidden(True)
            self.rangeNUSF_groupBox.setHidden(True)
            self.progressNUSF_groupBox.setHidden(True)

        # spin box bounds
        self.minDesignSize_spin.setMaximum(len(candidateData.getInputData()))
        self.maxDesignSize_spin.setMaximum(len(candidateData.getInputData()))
        self.designSize_spin.setMaximum(len(candidateData.getInputData()))


        # MWR combo boxes
        self.MWR1_comboBox.addItems(['', '2', '3', '4', '5', '6', '7', '8', '9', '10', '12', '15', '20', '25', '30', '35', '40', '50', '60'])
        self.MWR2_comboBox.addItems(['', '2', '3', '4', '5', '6', '7', '8', '9', '10', '12', '15', '20', '25', '30', '35', '40', '50', '60'])
        self.MWR3_comboBox.addItems(['', '2', '3', '4', '5', '6', '7', '8', '9', '10', '12', '15', '20', '25', '30', '35', '40', '50', '60'])
        self.MWR4_comboBox.addItems(['', '2', '3', '4', '5', '6', '7', '8', '9', '10', '12', '15', '20', '25', '30', '35', '40', '50', '60'])
        self.MWR5_comboBox.addItems(['', '2', '3', '4', '5', '6', '7', '8', '9', '10', '12', '15', '20', '25', '30', '35', '40', '50', '60'])
        self.MWR1_comboBox.setCurrentIndex(4)

        comboList = [self.MWR1_comboBox, self.MWR2_comboBox, self.MWR3_comboBox, self.MWR4_comboBox, self.MWR5_comboBox]
        for combo in comboList:
            combo.currentTextChanged.connect(self.on_MWR_combobox_changed)

        # Sample Size NUSF Combo Box
        self.sampleSizeNUSF_comboBox.addItems(['10', '20', '30', '40', '50', '60', '75', '100', '150', '200', '500', '1000'])
        self.sampleSizeNUSF_comboBox.setCurrentIndex(4)
        self.sampleSizeNUSF_comboBox.currentTextChanged.connect(self.on_size_combobox_changed)

        # Initialize inputSdoeTable
        self.updateInputSdoeTable()
        self.inputSdoeTable.cellWidget(0, self.typeCol).setCurrentIndex(1)
        if self.type == 'USF':
            self.testSdoeButton.clicked.connect(self.testSdoe)
        else:
            self.testSdoeButton.clicked.connect(self.testSdoeNUSF)

        self.testSdoeButton.setEnabled(self.hasSpaceFilling())
        self.minDesignSize_spin.valueChanged.connect(self.on_min_design_spinbox_changed)
        self.maxDesignSize_spin.valueChanged.connect(self.on_max_design_spinbox_changed)
        self.designSize_spin.valueChanged.connect(self.on_design_spinbox_changed)
        self.sampleSize_spin.valueChanged.connect(self.on_sample_size_spinbox_changed)
        self.runSdoeButton.clicked.connect(self.runSdoe)
        self.runSdoeNUSFButton.clicked.connect(self.runSdoeNUSF)

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
        if self.analysisTable.verticalScrollBar().isVisible():
            width += self.analysisTable.verticalScrollBar().width()
        self.analysisTable.setMinimumWidth(width)
        self.analysisTable.setMaximumWidth(width)
        self.analysisTable.setRowCount(0)
        self.analysisTable.itemSelectionChanged.connect(self.analysisSelected)
        self.analysisTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.analysisTable.setWordWrap(True)

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
        combo.addItems(['Input', 'Index', 'Response', 'Weight'])
        self.inputSdoeTable.setCellWidget(row, self.typeCol, combo)
        if self.type == 'USF':
            combo.model().item(2).setEnabled(False)
            combo.model().item(3).setEnabled(False)
        else:
            combo.model().item(2).setEnabled(False)
        combo.currentTextChanged.connect(self.on_combobox_changed)
        combo.setMinimumContentsLength(7)

        # Min column
        minValue = round(min(self.candidateData.getInputData()[:, row]), 2)
        item = self.inputSdoeTable.item(row, self.minCol)
        if item is None:
            item = QTableWidgetItem()
        item.setText(str(minValue))
        self.inputSdoeTable.setItem(row, self.minCol, item)

        # Max column
        maxValue = round(max(self.candidateData.getInputData()[:, row]), 2)
        item = self.inputSdoeTable.item(row, self.maxCol)
        if item is None:
            item = QTableWidgetItem()
        item.setText(str(maxValue))
        self.inputSdoeTable.setItem(row, self.maxCol, item)

    def analysisSelected(self):
        selectedIndexes = self.analysisTable.selectedIndexes()
        if not selectedIndexes:
            self.loadAnalysisButton.setEnabled(False)
            self.orderAnalysisButton.setEnabled(False)
            self.deleteAnalysisButton.setEnabled(False)
            return
        self.loadAnalysisButton.setEnabled(True)
        self.orderAnalysisButton.setEnabled(True)
        self.deleteAnalysisButton.setEnabled(True)

    def updateAnalysisTable(self):
        numAnalysis = len(self.analysis)
        self.analysisTable.setRowCount(numAnalysis)
        for row in range(numAnalysis):
            self.updateAnalysisTableRow(row)

    def updateAnalysisTableRow(self, row):

        # Optimality Method or MWR Value (it depends if USF or NUSF)
        item = self.analysisTable.item(row, self.methodCol)
        if item is None:
            item = QTableWidgetItem()
            self.analysisTable.setItem(row, self.methodCol, item)
        value = self.analysis[row][0]
        item.setText(str(value))


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

        # Criterion
        item = self.analysisTable.item(row, self.criterionCol)
        if item is None:
            item = QTableWidgetItem()
            self.analysisTable.setItem(row, self.criterionCol, item)
            criterion = round(self.analysis[row][6], 2)
            item.setText(str(criterion))

        # Plot SDOE
        viewButton = self.analysisTable.cellWidget(row, self.plotCol)
        newViewButton = False
        if viewButton is None:
            newViewButton = True
            viewButton = QPushButton()
            viewButton.setText('View')
            viewButton.setToolTip("View table and plot the design.")

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
        QApplication.processEvents()
        self.analysisGroup.setEnabled(True)
        self.testSdoeButton.setEnabled(True)
        row = self.analysisTable.selectedIndexes()[0].row()
        config_file = self.analysis[row][5]
        if self.type == 'USF':
            self.loadFromConfigFile(config_file)
        elif self.type =='NUSF':
            self.loadFromConfigFileNUSF(config_file)
        QApplication.processEvents()

    def checkInclude(self):
        numInputs = self.candidateData.getNumInputs()
        min_vals = []
        max_vals = []
        include_list = []
        type_list = []
        for row in range(numInputs):
            if self.inputSdoeTable.cellWidget(row, self.includeCol).isChecked():
                min_vals.append(self.inputSdoeTable.item(row, self.minCol).text())
                max_vals.append(self.inputSdoeTable.item(row, self.maxCol).text())
                include_list.append(self.inputSdoeTable.item(row, self.nameCol).text())
                type_list.append(str(self.inputSdoeTable.cellWidget(row, self.typeCol).currentText()))
        return min_vals, max_vals, include_list, type_list

    def writeConfigFile(self, test=False):
        timestamp = datetime.now().strftime('%Y%m%dT%H%M%S')
        outdir = os.path.join(self.dname, timestamp)
        os.makedirs(outdir, exist_ok=True)
        configFile = os.path.join(outdir, 'config.ini')
        f = open(configFile, 'w')

        ## METHOD
        f.write('[METHOD]\n')

        if self.Minimax_radioButton.isChecked():
            f.write('mode = minimax\n')
        elif self.Maximin_radioButton.isChecked():
            f.write('mode = maximin\n')

        if self.type == 'USF':
            f.write('min_design_size = %d\n' % self.minDesignSize_spin.value())
            f.write('max_design_size = %d\n' % self.maxDesignSize_spin.value())
        else:
            f.write('design_size = %d\n' % self.designSize_spin.value())

        if test:
            if self.type == 'USF':
                f.write('number_random_starts = 200\n')
            else:
                f.write('number_random_starts = 2\n')
        else:
            if self.type == 'USF':
                f.write('number_random_starts = %d\n' % 10**(self.sampleSize_spin.value()))
            else:
                f.write('number_random_starts = %d\n' % int(self.sampleSizeNUSF_comboBox.currentText()))

        f.write('\n')

        ## INPUT
        f.write('[INPUT]\n')
        if self.historyData is None:
            f.write('history_file = \n')
        else:
            f.write('history_file = %s\n' % os.path.join(self.dname, self.historyData.getModelName()))
        f.write('candidate_file = %s\n' % os.path.join(self.dname, self.candidateData.getModelName()))
        min_vals, max_vals, include_list, type_list = self.checkInclude()
        f.write('min_vals = %s\n' % ','.join(min_vals))
        f.write('max_vals = %s\n' % ','.join(max_vals))
        f.write('include = %s\n' % ','.join(include_list))
        f.write('types = %s\n' % ','.join(type_list))
        f.write('\n')

        ###NUSF ONLY
        ##WEIGHT
        if self.type == 'NUSF':
            f.write('[WEIGHT]\n')
            f.write('weight_mode = by_user\n')
            f.write('\n')

        ##SPACE FILLING
            f.write('[SF]\n')
            f.write('sf_method = nusf\n')
            if self.Direct_radioButton.isChecked():
                f.write('scale_method = direct_mwr\n')
            elif self.Ranked_radioButton.isChecked():
                f.write('scale_method = ranked_mwr\n')
            mwr_list = []
            for item in [self.MWR1_comboBox.currentText(), self.MWR2_comboBox.currentText(), self.MWR3_comboBox.currentText(), self.MWR4_comboBox.currentText(), self.MWR5_comboBox.currentText()]:
                if item != "":
                    mwr_list.append(item)
            if test:
                f.write('mwr_values = %s\n' %mwr_list[0])
                f.write('\n')
            else:
                f.write('mwr_values = %s\n' % ','.join(mwr_list))
                f.write('\n')

        ## OUTPUT
        f.write('[OUTPUT]\n')
        f.write('results_dir = %s\n' %outdir)
        f.write('\n')

        f.close()

        return configFile

    def runSdoe(self):
        if self.hasNoIndex():
            reply = self.showIndexWarning()
            if reply == QMessageBox.Yes:
                pass
            else:
                return
        if self.hasIndex():
            self.showIndexBlock()
            return
        self.runSdoeButton.setText('Stop SDOE')
        min_size = self.minDesignSize_spin.value()
        max_size = self.maxDesignSize_spin.value()
        numIter = (max_size + 1) - min_size
        QApplication.processEvents()
        self.freeze()
        for nd in range(min_size, max_size+1):
            config_file = self.writeConfigFile()
            fnames, results, elapsed_time = sdoe.run(config_file, nd)
            self.analysis.append([results['mode'], results['design_size'], results['num_restarts'], elapsed_time, fnames,
                                                                                   config_file, results['best_val']])
            self.analysisTableGroup.setEnabled(True)
            self.loadAnalysisButton.setEnabled(False)
            self.orderAnalysisButton.setEnabled(False)
            self.deleteAnalysisButton.setEnabled(False)
            self.updateAnalysisTable()
            self.designInfo_dynamic.setText('d = %d, n = %d' % (nd, results['num_restarts']))
            self.SDOE_progressBar.setValue((100/numIter) * (nd-min_size+1))
            QApplication.processEvents()

        self.unfreeze()
        self.SDOE_progressBar.setValue(0)
        self.runSdoeButton.setText('Run SDOE')
        self.analysisGroup.setEnabled(False)

    def testSdoe(self):
        if self.hasNoIndex():
            reply = self.showIndexWarning()
            if reply == QMessageBox.Yes:
                pass
            else:
                return
        if self.hasIndex():
            self.showIndexBlock()
            return
        QApplication.processEvents()
        #test using max design size and nd=200
        self.testRuntime = []
        runtime = sdoe.run(self.writeConfigFile(test=True), self.maxDesignSize_spin.value(), test=True)
        self.testSdoeButton.setEnabled(False)
        self.progress_groupBox.setEnabled(True)
        self.updateRunTime(runtime)
        self.testRuntime.append(runtime)
        QApplication.processEvents()

    def runSdoeNUSF(self):
        if self.hasNoIndex():
            reply = self.showIndexWarning()
            if reply == QMessageBox.Yes:
                pass
            else:
                return
        if self.hasNoWeight():
            self.showWeightWarning()
            return
        if self.hasWeight():
            self.showWeightBlock()
            return
        if self.hasIndex():
            self.showIndexBlock()
            return
        self.runSdoeNUSFButton.setText('Stop SDOE')
        size = self.designSize_spin.value()
        mwr_list = []
        for item in [self.MWR1_comboBox.currentText(), self.MWR2_comboBox.currentText(),
                     self.MWR3_comboBox.currentText(), self.MWR4_comboBox.currentText(),
                     self.MWR5_comboBox.currentText()]:
            if item != "":
                mwr_list.append(int(item))

        config_file = self.writeConfigFile()
        QApplication.processEvents()
        self.freeze()
        fnames, results, elapsed_time = sdoe.run(config_file, size)
        self.analysisTableGroup.setEnabled(True)
        self.loadAnalysisButton.setEnabled(False)
        self.orderAnalysisButton.setEnabled(False)
        self.deleteAnalysisButton.setEnabled(False)

        count = 0
        QApplication.processEvents()
        for mwr in mwr_list:
            self.analysis.append([mwr, results[mwr]['design_size'], results[mwr]['num_restarts'], results[mwr]['elapsed_time'], fnames[mwr],
                                  config_file, results[mwr]['best_val'], results[mwr]])

            self.updateAnalysisTable()
            self.designInfoNUSF_dynamic.setText('mwr = %d, n = %d' % (mwr, results[mwr]['num_restarts']))
            count += 1
            self.SDOENUSF_progressBar.setValue((100/len(mwr_list)) * count)
        QApplication.processEvents()

        self.unfreeze()
        self.SDOENUSF_progressBar.setValue(0)
        self.runSdoeNUSFButton.setText('Run SDOE')
        self.analysisGroup.setEnabled(False)
        QApplication.processEvents()

    def testSdoeNUSF(self):
        if self.hasNoIndex():
            reply = self.showIndexWarning()
            if reply == QMessageBox.Yes:
                pass
            else:
                return
        if self.hasNoWeight():
            self.showWeightWarning()
            return
        if self.hasWeight():
            self.showWeightBlock()
            return
        if self.hasIndex():
            self.showIndexBlock()
            return
        #test using nr=2
        QApplication.processEvents()
        self.testRuntime = []
        runtime = sdoe.run(self.writeConfigFile(test=True), self.designSize_spin.value(), test=True)
        self.testSdoeButton.setEnabled(False)
        self.progressNUSF_groupBox.setEnabled(True)
        self.updateRunTimeNUSF(runtime)
        self.testRuntime.append(runtime)
        QApplication.processEvents()

    def on_min_design_spinbox_changed(self):
        self.designInfo_dynamic.setText('d = %d, n = %d' %(int(self.minDesignSize_spin.value()),
                                                           10 ** int(self.sampleSize_spin.value())))

    def on_max_design_spinbox_changed(self):
        self.testSdoeButton.setEnabled(True)
        self.designInfo_dynamic.setText('d = %d, n = %d' %(int(self.minDesignSize_spin.value()),
                                                           10 ** int(self.sampleSize_spin.value())))
    def on_design_spinbox_changed(self):
        if len(self.testRuntime) > 0:
            self.updateRunTimeNUSF(self.testRuntime[0])
        self.designInfoNUSF_dynamic.setText('mwr = %d, n = %d' %(int(self.MWR1_comboBox.currentText()),
                                                           int(self.sampleSizeNUSF_comboBox.currentText())))

    def on_sample_size_spinbox_changed(self):
        self.updateRunTime(self.testRuntime[0])
        self.designInfo_dynamic.setText('d = %d, n = %d' %(int(self.minDesignSize_spin.value()),
                                                           10 ** int(self.sampleSize_spin.value())))
    def on_combobox_changed(self):
        self.testSdoeButton.setEnabled(self.hasSpaceFilling())
        if self.hasIndex():
            self.showIndexBlock()
        if self.hasWeight():
            self.showWeightBlock()
        self.checkType()

    def on_size_combobox_changed(self):
        self.updateRunTimeNUSF(self.testRuntime[0])
        self.designInfoNUSF_dynamic.setText('mwr = %d, n = %d' % (int(self.MWR1_comboBox.currentText()),
                                                                int(self.sampleSizeNUSF_comboBox.currentText())))
    def on_MWR_combobox_changed(self):
        if len(self.testRuntime) > 0:
            self.updateRunTimeNUSF(self.testRuntime[0])
        self.designInfoNUSF_dynamic.setText('mwr = %d, n = %d' % (int(self.MWR1_comboBox.currentText()),
                                                                  int(self.sampleSizeNUSF_comboBox.currentText())))

    def checkType(self):
        numInputs = self.candidateData.getNumInputs()
        for i in range(numInputs):
            if str(self.inputSdoeTable.cellWidget(i, self.typeCol).currentText()) == 'Index':
                self.clearMinMax(i)
            else:
                self.activateMinMax(i)

    def clearMinMax(self, row):
        item = self.inputSdoeTable.item(row, self.minCol)
        mask = ~Qt.ItemIsEnabled
        item.setBackground(Qt.lightGray)
        flags = item.flags()
        item.setFlags(flags & mask)

        item = self.inputSdoeTable.item(row, self.maxCol)
        mask = ~Qt.ItemIsEnabled
        item.setBackground(Qt.lightGray)
        flags = item.flags()
        item.setFlags(flags & mask)


    def activateMinMax(self, row):
        item = self.inputSdoeTable.item(row, self.minCol)
        mask = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        item.setForeground(Qt.black)
        item.setBackground(Qt.white)
        flags = item.flags()
        item.setFlags(flags | mask)

        item = self.inputSdoeTable.item(row, self.maxCol)
        mask = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        item.setForeground(Qt.black)
        item.setBackground(Qt.white)
        flags = item.flags()
        item.setFlags(flags | mask)

    def hasSpaceFilling(self):
        numInputs = self.candidateData.getNumInputs()
        spaceFilling = 0
        for i in range(numInputs):
            if str(self.inputSdoeTable.cellWidget(i, self.typeCol).currentText()) == 'Input':
                spaceFilling += 1

        return(spaceFilling > 0)

    def hasNoIndex(self):
        numInputs = self.candidateData.getNumInputs()
        index = 0
        for i in range(numInputs):
            if str(self.inputSdoeTable.cellWidget(i, self.typeCol).currentText()) == 'Index':
                index += 1
        return index == 0

    def hasIndex(self):
        numInputs = self.candidateData.getNumInputs()
        index = 0
        for i in range(numInputs):
            if str(self.inputSdoeTable.cellWidget(i, self.typeCol).currentText()) == 'Index':
                index += 1
        return index > 1

    def hasNoWeight(self):
        numInputs = self.candidateData.getNumInputs()
        weight = 0
        for i in range(numInputs):
            if str(self.inputSdoeTable.cellWidget(i, self.typeCol).currentText()) == 'Weight':
                weight += 1
        return weight == 0

    def hasWeight(self):
        numInputs = self.candidateData.getNumInputs()
        weight = 0
        for i in range(numInputs):
            if str(self.inputSdoeTable.cellWidget(i, self.typeCol).currentText()) == 'Weight':
                weight += 1
        return weight > 1

    def showIndexWarning(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle('Index not selected.')
        msg.setText('You have not set an index. The index is a unique identifier for the input combination. It is not required, but encouraged.')
        msg.setInformativeText('Do you want to continue?')
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        reply = msg.exec_()
        return reply

    def showIndexBlock(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle('Index already selected.')
        msg.setText('You have already set an index. The index is a unique identifier for the input combination. It is not required, but encouraged. Please select only one index for your design.')
        msg.setStandardButtons(QMessageBox.Ok)
        reply = msg.exec_()
        return reply

    def showWeightWarning(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle('Weight not selected.')
        msg.setText('You have not set a weight. Please select a weight to continue.')
        msg.setStandardButtons(QMessageBox.Ok)
        reply = msg.exec_()
        return reply

    def showWeightBlock(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle('Weight already selected.')
        msg.setText('You have already set a weight. Please select only one weight for your design.')
        msg.setStandardButtons(QMessageBox.Ok)
        reply = msg.exec_()
        return reply

    def updateRunTime(self, runtime):
        delta = runtime/200
        estimateTime = int(delta * (10 ** int(self.sampleSize_spin.value())) * \
                       int(self.maxDesignSize_spin.value()-self.minDesignSize_spin.value()+1))
        if estimateTime < 60:
            self.time_dynamic.setText(f"{estimateTime:2d} seconds")
        elif estimateTime < 3600:
            self.time_dynamic.setText(f"{int(estimateTime/60):2d}:{estimateTime%60:02d}")

        elif estimateTime > 3600:
            timeHr = int(estimateTime/3600)
            timeMin = int((estimateTime - (timeHr*3600))/60)
            timeSec = (estimateTime - (timeHr*3600))%60
            self.time_dynamic.setText(f"{timeHr:2d}:{timeMin:02d}:{timeSec:02d}")

    def updateRunTimeNUSF(self, runtime):
        delta = runtime/2
        mwr_list = []
        for item in [self.MWR1_comboBox.currentText(), self.MWR2_comboBox.currentText(),
                     self.MWR3_comboBox.currentText(), self.MWR4_comboBox.currentText(),
                     self.MWR5_comboBox.currentText()]:
            if item != "":
                mwr_list.append(int(item))
        estimateTime = int(delta * (int(self.sampleSizeNUSF_comboBox.currentText())) * len(mwr_list))
        if estimateTime < 60:
            self.timeNUSF_dynamic.setText(f"{estimateTime:2d} seconds")
        elif estimateTime < 3600:
            self.timeNUSF_dynamic.setText(f"{int(estimateTime/60):2d}:{estimateTime%60:02d}")

        elif estimateTime > 3600:
            timeHr = int(estimateTime/3600)
            timeMin = int((estimateTime - (timeHr*3600))/60)
            timeSec = (estimateTime - (timeHr*3600))%60
            self.timeNUSF_dynamic.setText(f"{timeHr:2d}:{timeMin:02d}:{timeSec:02d}")

    def editSdoe(self):
        sender = self.sender()
        row = sender.property('row')
        fullName = self.analysis[row][4]['cand']
        dirname, filename = os.path.split(fullName)
        config_file = self.analysis[row][5]
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file)
        hfile = config['INPUT']['history_file']
        cfile = config['INPUT']['candidate_file']
        include = [s.strip() for s in config['INPUT']['include'].split(',')]
        types = [s.strip() for s in config['INPUT']['types'].split(',')]

        if hfile == '':
            hname = None
        else:
            hname = hfile
        sdoeData = LocalExecutionModule.readSampleFromCsvFile(fullName, False)
        if self.type == 'NUSF':
            scale_method = config['SF']['scale_method']
            cand = load(cfile)
            i = types.index('Weight')
            wcol = include[i]  # weight column name
            nusf = {'cand': cand, 'wcol': wcol, 'scale_method': scale_method, 'results': self.analysis[row][7]}
        else:
            nusf = None
        scatterLabel = 'Design Points'
        dialog = sdoePreview(sdoeData, hname, dirname, nusf, scatterLabel, self)
        dialog.show()

    def loadFromConfigFile(self, config_file):
        QApplication.processEvents()
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
        types = [s.strip() for s in config['INPUT']['types'].split(',')]

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
        for i in range(len(types)):
            self.inputSdoeTable.cellWidget(i, self.typeCol).setCurrentText(types[i])

        self.sampleSize_spin.setValue(int(np.log10(nr)))
        self.updateRunTime(self.testRuntime[0])
        self.designInfo_dynamic.setText('d = %d, n = %d' %(int(self.minDesignSize_spin.value()),
                                                           10 ** int(self.sampleSize_spin.value())))

        QApplication.processEvents()

    def loadFromConfigFileNUSF(self, config_file):
        QApplication.processEvents()
        ## Read from config file
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file)
        design_size = int(config['METHOD']['design_size'])
        nr = int(config['METHOD']['number_random_starts'])
        hfile = config['INPUT']['history_file']
        cfile = config['INPUT']['candidate_file']
        include = [s.strip() for s in config['INPUT']['include'].split(',')]
        types = [s.strip() for s in config['INPUT']['types'].split(',')]
        scale_method = config['SF']['scale_method']
        mwr_vals = [int(s) for s in config['SF']['mwr_values'].split(',')]

        ## Populate gui fields with config file info
        self.Minimax_radioButton.setEnabled(False)
        self.Maximin_radioButton.setChecked(True)
        if scale_method == 'direct_mwr':
            self.Direct_radioButton.setChecked(True)
        elif scale_method == 'ranked_mwr':
            self.Ranked_radioButton.setChecked(True)
        self.designSize_spin.setValue(design_size)
        MWRcomboList = [self.MWR1_comboBox, self.MWR2_comboBox, self.MWR3_comboBox, self.MWR4_comboBox, self.MWR5_comboBox]
        for i in range(len(mwr_vals)):
            combo = MWRcomboList[i]
            combo.setCurrentText(str(mwr_vals[i]))

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
        for i in range(len(types)):
            self.inputSdoeTable.cellWidget(i, self.typeCol).setCurrentText(types[i])

        self.sampleSizeNUSF_comboBox.setCurrentText(str(nr))
        self.updateRunTimeNUSF(self.testRuntime[0])
        self.designInfoNUSF_dynamic.setText('mwr = %d, n = %d' %(int(self.MWR1_comboBox.currentText()),
                                                           int(self.sampleSizeNUSF_comboBox.currentText())))

        QApplication.processEvents()

    def showOrderFileLoc(self, fname):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle('Order design completed.')
        msg.setText('Ordered candidates saved to \n{}'.format(fname))
        msg.setInformativeText('Continue?')
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        reply = msg.exec_()
        return reply

    def orderDesign(self):
        self.freeze()
        row = self.analysisTable.selectedIndexes()[0].row()
        outfiles = self.analysis[row][4]
        fname = order.rank(outfiles)
        if fname:
            self.showOrderFileLoc(fname)

        self.unfreeze()
        
    def freeze(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

    def semifreeze(self):
        QApplication.setOverrideCursor(QCursor(Qt.BusyCursor))

    def unfreeze(self):
        QApplication.restoreOverrideCursor()
