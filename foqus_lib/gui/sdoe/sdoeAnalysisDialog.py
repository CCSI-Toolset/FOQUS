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
from datetime import datetime
import configparser

from foqus_lib.framework.sdoe import order, sdoe
from foqus_lib.framework.sdoe.df_utils import load
from foqus_lib.framework.sdoe.plot_utils import plot_pareto
from .sdoeSetupFrame import *
from .sdoePreview import sdoePreview

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QMessageBox,
    QCheckBox,
    QTableWidgetItem,
    QAbstractItemView,
    QPushButton,
)
from PyQt5.QtGui import QCursor

mypath = os.path.dirname(__file__)
_sdoeAnalysisDialogUI, _sdoeAnalysisDialog = uic.loadUiType(
    os.path.join(mypath, "sdoeAnalysisDialog_UI.ui")
)


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

    def __init__(
        self,
        candidateData,
        dname,
        analysis=[],
        historyData=None,
        type=None,
        parent=None,
    ):
        super(sdoeAnalysisDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.candidateData = candidateData
        self.analysis = analysis
        self.historyData = historyData
        self.dname = dname
        self.type = type

        self.setWindowTitle("Sequential Design of Experiments")

        # Info table
        mask = ~Qt.ItemIsEnabled

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
        if historyData is None:
            item = QTableWidgetItem("None")
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

        # Connections here
        self.loadAnalysisButton.clicked.connect(self.populateAnalysis)
        self.orderAnalysisButton.clicked.connect(self.orderDesign)
        self.deleteAnalysisButton.clicked.connect(self.deleteAnalysis)
        self.testSdoeButton.setEnabled(False)
        self.analysisTableGroup.setEnabled(False)
        self.progress_groupBox.setEnabled(False)
        self.progress2_groupBox.setEnabled(False)

        # USF, NUSF, IRSF conditions
        if self.type == "NUSF":
            self.Minimax_radioButton.setEnabled(False)
            self.Maximin_radioButton.setChecked(True)
            self.range_groupBox.setHidden(True)
            self.rangeIRSF_groupBox.setHidden(True)
            self.progress_groupBox.setHidden(True)
            self.analysisTable.setHorizontalHeaderLabels(
                [
                    "MWR Value",
                    "Design Size, d",
                    "# of Random Starts, n",
                    "Runtime (in sec)",
                    "Criterion Value",
                    "Plot SDOE",
                ]
            )

        elif self.type == "IRSF":
            self.Minimax_radioButton.setEnabled(False)
            self.Maximin_radioButton.setChecked(True)
            self.scalingGroup.setHidden(True)
            self.range_groupBox.setHidden(True)
            self.rangeNUSF_groupBox.setHidden(True)
            self.progress_groupBox.setHidden(True)
            self.analysisTable.setHorizontalHeaderLabels(
                [
                    "",
                    "Design Size, d",
                    "# of Random Starts, n",
                    "Runtime (in sec)",
                    "# of Designs",
                    "Plot SDOE",
                ]
            )

        elif self.type == "USF":
            self.scalingGroup.setHidden(True)
            self.rangeNUSF_groupBox.setHidden(True)
            self.rangeIRSF_groupBox.setHidden(True)
            self.progress2_groupBox.setHidden(True)

        # spin box bounds
        self.minDesignSize_spin.setMaximum(len(candidateData.getInputData()))
        self.maxDesignSize_spin.setMaximum(len(candidateData.getInputData()))
        self.designSize_spin.setMaximum(len(candidateData.getInputData()))
        self.designSizeIRSF_spin.setMaximum(len(candidateData.getInputData()))
        self.ncand_samplesIRSF_spin.setRange(1, len(candidateData.getInputData()))
        self.ncand_samplesIRSF_spin.setValue(0.1 * len(candidateData.getInputData()))

        # If Monte Carlo sampling is not used, we hide ncand_samples spinBox and its label
        self.ncand_samplesIRSF_spin.hide()
        self.ncand_samplesIRSF_static.hide()

        # MWR combo boxes
        self.MWR1_comboBox.addItems(
            [
                "",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "12",
                "15",
                "20",
                "25",
                "30",
                "35",
                "40",
                "50",
                "60",
            ]
        )
        self.MWR2_comboBox.addItems(
            [
                "",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "12",
                "15",
                "20",
                "25",
                "30",
                "35",
                "40",
                "50",
                "60",
            ]
        )
        self.MWR3_comboBox.addItems(
            [
                "",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "12",
                "15",
                "20",
                "25",
                "30",
                "35",
                "40",
                "50",
                "60",
            ]
        )
        self.MWR4_comboBox.addItems(
            [
                "",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "12",
                "15",
                "20",
                "25",
                "30",
                "35",
                "40",
                "50",
                "60",
            ]
        )
        self.MWR5_comboBox.addItems(
            [
                "",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "12",
                "15",
                "20",
                "25",
                "30",
                "35",
                "40",
                "50",
                "60",
            ]
        )
        self.MWR1_comboBox.setCurrentIndex(4)

        comboList = [
            self.MWR1_comboBox,
            self.MWR2_comboBox,
            self.MWR3_comboBox,
            self.MWR4_comboBox,
            self.MWR5_comboBox,
        ]
        for combo in comboList:
            combo.currentTextChanged.connect(self.on_MWR_combobox_changed)

        # Sample Size NUSF and IRSF Combo Box
        if self.type == "NUSF":
            self.sampleSize_comboBox.addItems(
                [
                    "10",
                    "20",
                    "30",
                    "40",
                    "50",
                    "60",
                    "75",
                    "100",
                    "150",
                    "200",
                    "500",
                    "1000",
                ]
            )
            self.sampleSize_comboBox.setCurrentIndex(2)
            self.sampleSize_comboBox.currentTextChanged.connect(
                self.on_size_combobox_changed
            )

        if self.type == "IRSF":
            self.sampleSize_comboBox.addItems(
                ["5", "10", "20", "30", "50", "75", "100", "150", "200", "500"]
            )
            self.sampleSize_comboBox.setCurrentIndex(2)
            self.sampleSize_comboBox.currentTextChanged.connect(
                self.on_size_IRSF_combobox_changed
            )

        # Initialize inputSdoeTable
        self.updateInputSdoeTable()
        self.inputSdoeTable.cellWidget(0, self.typeCol).setCurrentIndex(1)
        if self.type == "USF":
            self.testSdoeButton.clicked.connect(self.testSdoe)
        elif self.type == "NUSF":
            self.testSdoeButton.clicked.connect(self.testSdoeNUSF)
        elif self.type == "IRSF":
            self.testSdoeButton.clicked.connect(self.testSdoeIRSF)

        self.testSdoeButton.setEnabled(self.hasSpaceFilling())
        self.minDesignSize_spin.valueChanged.connect(self.on_min_design_spinbox_changed)
        self.maxDesignSize_spin.valueChanged.connect(self.on_max_design_spinbox_changed)
        self.designSize_spin.valueChanged.connect(self.on_design_spinbox_changed)
        self.designSizeIRSF_spin.valueChanged.connect(
            self.on_design_IRSF_spinbox_changed
        )
        self.sampleSize_spin.valueChanged.connect(self.on_sample_size_spinbox_changed)
        self.runSdoeButton.clicked.connect(self.runSdoe)
        if self.type == "NUSF":
            self.runSdoe2Button.clicked.connect(self.runSdoeNUSF)
        elif self.type == "IRSF":
            self.runSdoe2Button.clicked.connect(self.runSdoeIRSF)

        # Resize tables
        self.infoTable.resizeColumnsToContents()
        self.analysisTable.resizeColumnsToContents()
        self.inputSdoeTable.resizeColumnsToContents()
        self.show()

        width = (
            2 + self.infoTable.verticalHeader().width() + self.infoTable.columnWidth(0)
        )
        if self.infoTable.verticalScrollBar().isVisible():
            width += self.infoTable.verticalScrollBar().width()
        self.infoTable.setMaximumWidth(width)
        maxHeight = 4
        for i in range(6):
            maxHeight += self.infoTable.rowHeight(i)
        self.infoTable.setMaximumHeight(maxHeight)

        width = 4 + self.inputSdoeTable.verticalHeader().width()
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

        if historyData is None:
            item = QTableWidgetItem("None")
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
        checkbox.setProperty("row", row)

        # create comboboxes for type column
        combo = QComboBox()
        combo.addItems(["Input", "Index", "Response", "Weight"])
        self.inputSdoeTable.setCellWidget(row, self.typeCol, combo)
        if self.type == "USF":
            combo.model().item(2).setEnabled(False)
            combo.model().item(3).setEnabled(False)
        elif self.type == "NUSF":
            combo.model().item(2).setEnabled(False)
        elif self.type == "IRSF":
            combo.model().item(3).setEnabled(False)

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
            # self.loadAnalysisButton.setEnabled(False)
            self.orderAnalysisButton.setEnabled(False)
            self.deleteAnalysisButton.setEnabled(False)
            return
        # self.loadAnalysisButton.setEnabled(True)
        self.orderAnalysisButton.setEnabled(True)
        if self.type == "IRSF":
            self.orderAnalysisButton.setEnabled(False)
        self.deleteAnalysisButton.setEnabled(True)

    def updateAnalysisTable(self):
        numAnalysis = len(self.analysis)
        self.analysisTable.setRowCount(numAnalysis)
        for row in range(numAnalysis):
            self.updateAnalysisTableRow(row)

    def updateAnalysisTableRow(self, row):

        # Optimality Method for USF, MWR Value for NUSF
        item = self.analysisTable.item(row, self.methodCol)
        if item is None:
            item = QTableWidgetItem()
            self.analysisTable.setItem(row, self.methodCol, item)
        if self.analysis[row].sf_method == "usf":
            value = self.analysis[row].optimality
        elif self.analysis[row].sf_method == "nusf":
            value = self.analysis[row].mwr
        elif self.analysis[row].sf_method == "irsf":
            value = ""
        item.setText(str(value))

        # Design Size
        item = self.analysisTable.item(row, self.designCol)
        if item is None:
            item = QTableWidgetItem()
            self.analysisTable.setItem(row, self.designCol, item)
        designSize = self.analysis[row].d
        item.setText(str(designSize))

        # Number of restarts
        item = self.analysisTable.item(row, self.sampleCol)
        if item is None:
            item = QTableWidgetItem()
            self.analysisTable.setItem(row, self.sampleCol, item)
        sampleSize = self.analysis[row].nr
        item.setText(str(sampleSize))

        # Runtime
        item = self.analysisTable.item(row, self.runtimeCol)
        if item is None:
            item = QTableWidgetItem()
            self.analysisTable.setItem(row, self.runtimeCol, item)
            runtime = round(self.analysis[row].runtime, 2)
            item.setText(str(runtime))

        # Criterion
        item = self.analysisTable.item(row, self.criterionCol)
        if item is None:
            item = QTableWidgetItem()
            self.analysisTable.setItem(row, self.criterionCol, item)
            if self.analysis[row].sf_method == "irsf":
                value = self.analysis[row].designs
            else:
                value = round(self.analysis[row].criterion, 2)
            item.setText(str(value))

        # Plot SDOE
        viewButton = self.analysisTable.cellWidget(row, self.plotCol)
        newViewButton = False
        if viewButton is None:
            newViewButton = True
            viewButton = QPushButton()
            viewButton.setText("View")
            viewButton.setToolTip("View table and plot the design.")

        viewButton.setProperty("row", row)
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
        # row = self.analysisTable.selectedIndexes()[0].row()
        # config_file = self.analysis[row].config_file
        # if self.type == 'USF':
        #     self.loadFromConfigFile(config_file)
        # elif self.type =='NUSF':
        #     self.loadFromConfigFileNUSF(config_file)
        # elif self.type == 'IRSF':
        #     self.loadFromConfigFileIRSF(config_file)

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
                type_list.append(
                    str(self.inputSdoeTable.cellWidget(row, self.typeCol).currentText())
                )
        return min_vals, max_vals, include_list, type_list

    def writeConfigFile(self, test=False):
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        outdir = os.path.join(self.dname, timestamp)
        os.makedirs(outdir, exist_ok=True)
        configFile = os.path.join(outdir, "config.ini")
        f = open(configFile, "w")

        # METHOD
        f.write("[METHOD]\n")

        if self.Minimax_radioButton.isChecked():
            f.write("mode = minimax\n")
        elif self.Maximin_radioButton.isChecked():
            f.write("mode = maximin\n")

        if self.type == "USF":
            f.write("min_design_size = %d\n" % self.minDesignSize_spin.value())
            f.write("max_design_size = %d\n" % self.maxDesignSize_spin.value())
        elif self.type == "NUSF":
            f.write("design_size = %d\n" % self.designSize_spin.value())
        elif self.type == "IRSF":
            f.write("design_size = %d\n" % self.designSizeIRSF_spin.value())

        if test:
            if self.type == "USF":
                f.write("number_random_starts = 200\n")
            else:
                f.write("number_random_starts = 2\n")
        else:
            if self.type == "USF":
                f.write(
                    "number_random_starts = %d\n" % 10 ** (self.sampleSize_spin.value())
                )
            else:
                f.write(
                    "number_random_starts = %d\n"
                    % int(self.sampleSize_comboBox.currentText())
                )

        f.write("\n")

        # INPUT
        f.write("[INPUT]\n")
        if self.historyData is None:
            f.write("history_file = \n")
        else:
            f.write(
                "history_file = %s\n"
                % os.path.join(self.dname, self.historyData.getModelName())
            )
        f.write(
            "candidate_file = %s\n"
            % os.path.join(self.dname, self.candidateData.getModelName())
        )
        min_vals, max_vals, include_list, type_list = self.checkInclude()
        f.write("min_vals = %s\n" % ",".join(min_vals))
        f.write("max_vals = %s\n" % ",".join(max_vals))
        f.write("include = %s\n" % ",".join(include_list))
        f.write("types = %s\n" % ",".join(type_list))
        f.write("\n")

        # USF ONLY
        # SPACE FILLING
        if self.type == "USF":
            f.write("[SF]\n")
            f.write("sf_method = usf\n")

        # NUSF ONLY
        # WEIGHT
        if self.type == "NUSF":
            f.write("[WEIGHT]\n")
            f.write("weight_mode = by_user\n")
            f.write("\n")

            # SPACE FILLING
            f.write("[SF]\n")
            f.write("sf_method = nusf\n")
            if self.Direct_radioButton.isChecked():
                f.write("scale_method = direct_mwr\n")
            elif self.Ranked_radioButton.isChecked():
                f.write("scale_method = ranked_mwr\n")
            mwr_list = []
            for item in [
                self.MWR1_comboBox.currentText(),
                self.MWR2_comboBox.currentText(),
                self.MWR3_comboBox.currentText(),
                self.MWR4_comboBox.currentText(),
                self.MWR5_comboBox.currentText(),
            ]:
                if item != "":
                    mwr_list.append(item)
            if test:
                f.write("mwr_values = %s\n" % mwr_list[0])
                f.write("\n")
            else:
                f.write("mwr_values = %s\n" % ",".join(mwr_list))
                f.write("\n")

        # IRSF ONLY
        # SPACE FILLING
        if self.type == "IRSF":
            f.write("[SF]\n")
            f.write("sf_method = irsf\n")

        # OUTPUT
        f.write("[OUTPUT]\n")
        f.write("results_dir = %s\n" % outdir)
        f.write("\n")

        f.close()

        return configFile

    def runSdoe(self):
        # if self.hasNoIndex():
        #     reply = self.showIndexWarning()
        #     if reply == QMessageBox.Yes:
        #         pass
        #     else:
        #         return
        # if self.hasIndex():
        #     self.showIndexBlock()
        #     return
        self.runSdoeButton.setText("Stop SDOE")
        min_size = self.minDesignSize_spin.value()
        max_size = self.maxDesignSize_spin.value()
        numIter = (max_size + 1) - min_size
        QApplication.processEvents()
        self.freeze()
        for nd in range(min_size, max_size + 1):
            config_file = self.writeConfigFile()
            fnames, results, elapsed_time = sdoe.run(config_file, nd)
            new_analysis = SdoeAnalysisData()
            new_analysis.sf_method = "usf"
            new_analysis.optimality = results["mode"]
            new_analysis.d = results["design_size"]
            new_analysis.nr = results["num_restarts"]
            new_analysis.runtime = elapsed_time
            new_analysis.criterion = results["best_val"]
            new_analysis.config_file = config_file
            new_analysis.fnames = fnames

            self.analysis.append(new_analysis)
            self.analysisTableGroup.setEnabled(True)
            self.analysisGroup.setEnabled(False)
            # self.loadAnalysisButton.setEnabled(False)
            self.orderAnalysisButton.setEnabled(False)
            self.deleteAnalysisButton.setEnabled(False)
            self.updateAnalysisTable()
            self.designInfo_dynamic.setText(
                "d = %d, n = %d" % (nd, results["num_restarts"])
            )
            self.SDOE_progressBar.setValue((100 / numIter) * (nd - min_size + 1))
            QApplication.processEvents()

        self.unfreeze()
        self.SDOE_progressBar.setValue(0)
        self.runSdoeButton.setText("Run SDOE")

    def testSdoe(self):
        # if self.hasNoIndex():
        #     reply = self.showIndexWarning()
        #     if reply == QMessageBox.Yes:
        #         pass
        #     else:
        #         return
        # if self.hasIndex():
        #     self.showIndexBlock()
        #     return
        QApplication.processEvents()
        # test using max design size and nd=200
        self.testRuntime = []
        runtime = sdoe.run(
            self.writeConfigFile(test=True), self.maxDesignSize_spin.value(), test=True
        )
        self.testSdoeButton.setEnabled(False)
        self.progress_groupBox.setEnabled(True)
        self.updateRunTime(runtime)
        self.testRuntime.append(runtime)
        QApplication.processEvents()

    def runSdoeNUSF(self):
        # if self.hasNoIndex():
        #     reply = self.showIndexWarning()
        #     if reply == QMessageBox.Yes:
        #         pass
        #     else:
        #         return
        if self.hasNoWeight():
            self.showWeightWarning()
            return
        if self.hasWeight():
            self.showWeightBlock()
            return
        # if self.hasIndex():
        #     self.showIndexBlock()
        #     return

        self.runSdoe2Button.setText("Stop SDOE")
        size = self.designSize_spin.value()
        mwr_list = []
        for item in [
            self.MWR1_comboBox.currentText(),
            self.MWR2_comboBox.currentText(),
            self.MWR3_comboBox.currentText(),
            self.MWR4_comboBox.currentText(),
            self.MWR5_comboBox.currentText(),
        ]:
            if item != "":
                mwr_list.append(int(item))

        config_file = self.writeConfigFile()
        QApplication.processEvents()
        self.freeze()
        fnames, results, elapsed_time = sdoe.run(config_file, size)
        self.analysisTableGroup.setEnabled(True)
        self.analysisGroup.setEnabled(False)
        # self.loadAnalysisButton.setEnabled(False)
        self.orderAnalysisButton.setEnabled(False)
        self.deleteAnalysisButton.setEnabled(False)

        count = 0
        QApplication.processEvents()
        for mwr in mwr_list:
            new_analysis = SdoeAnalysisData()
            new_analysis.sf_method = "nusf"
            new_analysis.optimality = "maximin"
            new_analysis.mwr = mwr
            new_analysis.d = results[mwr]["design_size"]
            new_analysis.nr = results[mwr]["num_restarts"]
            new_analysis.runtime = results[mwr]["elapsed_time"]
            new_analysis.criterion = results[mwr]["best_val"]
            new_analysis.config_file = config_file
            new_analysis.fnames = fnames[mwr]
            new_analysis.results = results[mwr]

            self.analysis.append(new_analysis)

            self.updateAnalysisTable()
            self.designInfo2_dynamic.setText(
                "mwr = %d, n = %d" % (mwr, results[mwr]["num_restarts"])
            )
            count += 1
            self.SDOE2_progressBar.setValue((100 / len(mwr_list)) * count)
            QApplication.processEvents()

        self.unfreeze()
        self.SDOE2_progressBar.setValue(0)
        self.runSdoe2Button.setText("Run SDOE")
        QApplication.processEvents()

    def testSdoeNUSF(self):
        # if self.hasNoIndex():
        #     reply = self.showIndexWarning()
        #     if reply == QMessageBox.Yes:
        #         pass
        #     else:
        #         return
        if self.hasNoWeight():
            self.showWeightWarning()
            return
        if self.hasWeight():
            self.showWeightBlock()
            return
        # if self.hasIndex():
        #     self.showIndexBlock()
        #     return
        # test using nr=2
        QApplication.processEvents()
        self.testRuntime = []
        runtime = sdoe.run(
            self.writeConfigFile(test=True), self.designSize_spin.value(), test=True
        )
        self.testSdoeButton.setEnabled(False)
        self.progress2_groupBox.setEnabled(True)
        self.updateRunTimeNUSF(runtime)
        self.testRuntime.append(runtime)
        QApplication.processEvents()

    def runSdoeIRSF(self):
        # if self.hasNoIndex():
        #     reply = self.showIndexWarning()
        #     if reply == QMessageBox.Yes:
        #         pass
        #     else:
        #         return
        if self.hasNoResponse():
            self.showResponseWarning()
            return
        # if self.hasIndex():
        #     self.showIndexBlock()
        #     return

        QApplication.processEvents()
        self.runSdoe2Button.setText("Stop SDOE")
        size = self.designSizeIRSF_spin.value()

        config_file = self.writeConfigFile()
        fnames, results, elapsed_time = sdoe.run(config_file, size)
        new_analysis = SdoeAnalysisData()
        new_analysis.sf_method = "irsf"
        new_analysis.optimality = "maximin"
        new_analysis.d = results["design_size"]
        new_analysis.nr = results["num_restarts"]
        new_analysis.runtime = elapsed_time
        new_analysis.designs = results["num_designs"]
        new_analysis.config_file = config_file
        new_analysis.fnames = fnames
        new_analysis.results = results

        self.analysis.append(new_analysis)

        self.updateAnalysisTable()

        self.analysisTableGroup.setEnabled(True)
        self.analysisGroup.setEnabled(False)
        # self.loadAnalysisButton.setEnabled(False)
        self.orderAnalysisButton.setEnabled(False)
        self.deleteAnalysisButton.setEnabled(False)

        self.SDOE2_progressBar.setValue(0)
        self.runSdoe2Button.setText("Run SDOE")
        QApplication.processEvents()

    def testSdoeIRSF(self):
        # if self.hasNoIndex():
        #     reply = self.showIndexWarning()
        #     if reply == QMessageBox.Yes:
        #         pass
        #     else:
        #         return
        if self.hasNoResponse():
            self.showResponseWarning()
            return
        # if self.hasIndex():
        #     self.showIndexBlock()
        #     return

        QApplication.processEvents()

        # test using nr=2
        self.testRuntime = []
        t1, t2 = sdoe.run(
            self.writeConfigFile(test=True), self.designSizeIRSF_spin.value(), test=True
        )
        runtime = t1 + (5 * (t2 / 2))
        self.testSdoeButton.setEnabled(False)
        self.progress2_groupBox.setEnabled(True)
        self.updateRunTimeIRSF(runtime)
        self.testRuntime.append(runtime)

        QApplication.processEvents()

    def on_min_design_spinbox_changed(self):
        self.designInfo_dynamic.setText(
            "d = %d, n = %d"
            % (
                int(self.minDesignSize_spin.value()),
                10 ** int(self.sampleSize_spin.value()),
            )
        )

    def on_max_design_spinbox_changed(self):
        self.testSdoeButton.setEnabled(True)
        self.designInfo_dynamic.setText(
            "d = %d, n = %d"
            % (
                int(self.minDesignSize_spin.value()),
                10 ** int(self.sampleSize_spin.value()),
            )
        )

    def on_design_spinbox_changed(self):
        if len(self.testRuntime) > 0:
            self.updateRunTimeNUSF(self.testRuntime[0])
        self.designInfo2_dynamic.setText(
            "mwr = %d, n = %d"
            % (
                int(self.MWR1_comboBox.currentText()),
                int(self.sampleSize_comboBox.currentText()),
            )
        )

    def on_design_IRSF_spinbox_changed(self):
        if len(self.testRuntime) > 0:
            self.updateRunTimeIRSF(self.testRuntime[0])
        self.designInfo2_dynamic.setText(
            "d = %d, n = %d"
            % (
                int(self.designSizeIRSF_spin.value()),
                int(self.sampleSize_comboBox.currentText()),
            )
        )

    def on_sample_size_spinbox_changed(self):
        self.updateRunTime(self.testRuntime[0])
        self.designInfo_dynamic.setText(
            "d = %d, n = %d"
            % (
                int(self.minDesignSize_spin.value()),
                10 ** int(self.sampleSize_spin.value()),
            )
        )

    def on_combobox_changed(self):
        self.testSdoeButton.setEnabled(self.hasSpaceFilling())
        if self.hasIndex():
            self.showIndexBlock()
        if self.hasWeight():
            self.showWeightBlock()
        self.checkType()

    def on_size_combobox_changed(self):
        self.updateRunTimeNUSF(self.testRuntime[0])
        self.designInfo2_dynamic.setText(
            "mwr = %d, n = %d"
            % (
                int(self.MWR1_comboBox.currentText()),
                int(self.sampleSize_comboBox.currentText()),
            )
        )

    def on_size_IRSF_combobox_changed(self):
        self.updateRunTimeIRSF(self.testRuntime[0])
        self.designInfo2_dynamic.setText(
            "d = %d, n = %d"
            % (
                int(self.designSizeIRSF_spin.value()),
                int(self.sampleSize_comboBox.currentText()),
            )
        )

    def on_MWR_combobox_changed(self):
        if len(self.testRuntime) > 0:
            self.updateRunTimeNUSF(self.testRuntime[0])
        self.designInfo2_dynamic.setText(
            "mwr = %d, n = %d"
            % (
                int(self.MWR1_comboBox.currentText()),
                int(self.sampleSize_comboBox.currentText()),
            )
        )

    def checkType(self):
        numInputs = self.candidateData.getNumInputs()
        for i in range(numInputs):
            if (
                str(self.inputSdoeTable.cellWidget(i, self.typeCol).currentText())
                == "Index"
            ):
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
            if (
                str(self.inputSdoeTable.cellWidget(i, self.typeCol).currentText())
                == "Input"
            ):
                spaceFilling += 1

        return spaceFilling > 0

    def hasNoIndex(self):
        numInputs = self.candidateData.getNumInputs()
        index = 0
        for i in range(numInputs):
            if (
                str(self.inputSdoeTable.cellWidget(i, self.typeCol).currentText())
                == "Index"
            ):
                index += 1
        return index == 0

    def hasIndex(self):
        numInputs = self.candidateData.getNumInputs()
        index = 0
        for i in range(numInputs):
            if (
                str(self.inputSdoeTable.cellWidget(i, self.typeCol).currentText())
                == "Index"
            ):
                index += 1
        return index > 1

    def hasNoWeight(self):
        numInputs = self.candidateData.getNumInputs()
        weight = 0
        for i in range(numInputs):
            if (
                str(self.inputSdoeTable.cellWidget(i, self.typeCol).currentText())
                == "Weight"
            ):
                weight += 1
        return weight == 0

    def hasWeight(self):
        numInputs = self.candidateData.getNumInputs()
        weight = 0
        for i in range(numInputs):
            if (
                str(self.inputSdoeTable.cellWidget(i, self.typeCol).currentText())
                == "Weight"
            ):
                weight += 1
        return weight > 1

    def hasNoResponse(self):
        numInputs = self.candidateData.getNumInputs()
        response = 0
        for i in range(numInputs):
            if (
                str(self.inputSdoeTable.cellWidget(i, self.typeCol).currentText())
                == "Response"
            ):
                response += 1
        return response == 0

    def hasResponse(self):
        numInputs = self.candidateData.getNumInputs()
        response = 0
        for i in range(numInputs):
            if (
                str(self.inputSdoeTable.cellWidget(i, self.typeCol).currentText())
                == "Response"
            ):
                response += 1
        return response

    def showIndexWarning(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Index not selected.")
        msg.setText(
            "You have not set an index. The index is a unique identifier for the input combination. "
            "It is not required, but encouraged."
        )
        msg.setInformativeText("Do you want to continue?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        reply = msg.exec_()
        return reply

    def showIndexBlock(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Index already selected.")
        msg.setText(
            "You have already set an index. The index is a unique identifier for the input combination. "
            "It is not required, but encouraged. Please select only one index for your design."
        )
        msg.setStandardButtons(QMessageBox.Ok)
        reply = msg.exec_()
        return reply

    def showWeightWarning(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Weight not selected.")
        msg.setText("You have not set a weight. Please select a weight to continue.")
        msg.setStandardButtons(QMessageBox.Ok)
        reply = msg.exec_()
        return reply

    def showWeightBlock(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Weight already selected.")
        msg.setText(
            "You have already set a weight. Please select only one weight for your design."
        )
        msg.setStandardButtons(QMessageBox.Ok)
        reply = msg.exec_()
        return reply

    def showResponseWarning(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Response not selected.")
        msg.setText(
            "You have not set a response. Please select response/s to continue."
        )
        msg.setStandardButtons(QMessageBox.Ok)
        reply = msg.exec_()
        return reply

    def updateRunTime(self, runtime):
        delta = runtime / 200
        estimateTime = int(
            delta
            * (10 ** int(self.sampleSize_spin.value()))
            * int(self.maxDesignSize_spin.value() - self.minDesignSize_spin.value() + 1)
        )
        if estimateTime < 60:
            self.time_dynamic.setText(f"{estimateTime:2d} seconds")
        elif estimateTime < 3600:
            self.time_dynamic.setText(
                f"{int(estimateTime/60):2d}:{estimateTime%60:02d}"
            )

        elif estimateTime > 3600:
            timeHr = int(estimateTime / 3600)
            timeMin = int((estimateTime - (timeHr * 3600)) / 60)
            timeSec = (estimateTime - (timeHr * 3600)) % 60
            self.time_dynamic.setText(f"{timeHr:2d}:{timeMin:02d}:{timeSec:02d}")

    def updateRunTimeNUSF(self, runtime):
        delta = runtime / 2
        mwr_list = []
        for item in [
            self.MWR1_comboBox.currentText(),
            self.MWR2_comboBox.currentText(),
            self.MWR3_comboBox.currentText(),
            self.MWR4_comboBox.currentText(),
            self.MWR5_comboBox.currentText(),
        ]:
            if item != "":
                mwr_list.append(int(item))
        estimateTime = int(
            delta * (int(self.sampleSize_comboBox.currentText())) * len(mwr_list)
        )
        if estimateTime < 60:
            self.time2_dynamic.setText(f"{estimateTime:2d} seconds")
        elif estimateTime < 3600:
            self.time2_dynamic.setText(
                f"{int(estimateTime/60):2d}:{estimateTime%60:02d}"
            )

        elif estimateTime > 3600:
            timeHr = int(estimateTime / 3600)
            timeMin = int((estimateTime - (timeHr * 3600)) / 60)
            timeSec = (estimateTime - (timeHr * 3600)) % 60
            self.time2_dynamic.setText(f"{timeHr:2d}:{timeMin:02d}:{timeSec:02d}")

    def updateRunTimeIRSF(self, runtime):

        estimateTime = int(runtime * (int(self.sampleSize_comboBox.currentText())))
        if estimateTime < 60:
            self.time2_dynamic.setText(f"{estimateTime:2d} seconds")
        elif estimateTime < 3600:
            self.time2_dynamic.setText(
                f"{int(estimateTime/60):2d}:{estimateTime%60:02d}"
            )

        elif estimateTime > 3600:
            timeHr = int(estimateTime / 3600)
            timeMin = int((estimateTime - (timeHr * 3600)) / 60)
            timeSec = (estimateTime - (timeHr * 3600)) % 60
            self.time2_dynamic.setText(f"{timeHr:2d}:{timeMin:02d}:{timeSec:02d}")

    def editSdoe(self):
        sender = self.sender()
        row = sender.property("row")

        config_file = self.analysis[row].config_file
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file)
        hfile = config["INPUT"]["history_file"]
        cfile = config["INPUT"]["candidate_file"]
        include = [s.strip() for s in config["INPUT"]["include"].split(",")]
        types = [s.strip() for s in config["INPUT"]["types"].split(",")]

        if hfile == "":
            hname = None
        else:
            hname = hfile

        if self.type == "IRSF":
            pf = self.analysis[row].results["pareto_front"]
            results = self.analysis[row].results
            cand = load(cfile)
            irsf = {"cand": cand}
            plot_pareto(pf, results, irsf["cand"], hname)
            return

        fullName = self.analysis[row].fnames["cand"]
        dirname, filename = os.path.split(fullName)

        sdoeData = LocalExecutionModule.readSampleFromCsvFile(fullName, False)
        if self.type == "NUSF":
            scale_method = config["SF"]["scale_method"]
            cand = load(cfile)
            i = types.index("Weight")
            wcol = include[i]  # weight column name
            usf = None
            nusf = {
                "cand": cand,
                "wcol": wcol,
                "scale_method": scale_method,
                "results": self.analysis[row].results,
            }
            irsf = None

        elif self.type == "USF":
            cand = load(cfile)
            usf = {"cand": cand}
            nusf = None
            irsf = None

        scatterLabel = "Design points"
        nImpPts = 0
        dialog = sdoePreview(
            sdoeData, hname, dirname, usf, nusf, irsf, scatterLabel, nImpPts, self
        )
        dialog.show()

    def loadFromConfigFile(self, config_file):
        QApplication.processEvents()
        # Read from config file
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file)
        mode = config["METHOD"]["mode"]
        min_size = int(config["METHOD"]["min_design_size"])
        max_size = int(config["METHOD"]["max_design_size"])
        nr = int(config["METHOD"]["number_random_starts"])
        hfile = config["INPUT"]["history_file"]
        cfile = config["INPUT"]["candidate_file"]
        include = [s.strip() for s in config["INPUT"]["include"].split(",")]
        types = [s.strip() for s in config["INPUT"]["types"].split(",")]

        # Populate gui fields with config file info
        if mode == "minimax":
            self.Minimax_radioButton.setChecked(True)
        elif mode == "maximin":
            self.Maximin_radioButton.setChecked(True)

        self.minDesignSize_spin.setValue(min_size)
        self.maxDesignSize_spin.setValue(max_size)

        if hfile == "":
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
        self.designInfo_dynamic.setText(
            "d = %d, n = %d"
            % (
                int(self.minDesignSize_spin.value()),
                10 ** int(self.sampleSize_spin.value()),
            )
        )

        QApplication.processEvents()

    def loadFromConfigFileNUSF(self, config_file):
        QApplication.processEvents()
        # Read from config file
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file)
        design_size = int(config["METHOD"]["design_size"])
        nr = int(config["METHOD"]["number_random_starts"])
        hfile = config["INPUT"]["history_file"]
        cfile = config["INPUT"]["candidate_file"]
        include = [s.strip() for s in config["INPUT"]["include"].split(",")]
        types = [s.strip() for s in config["INPUT"]["types"].split(",")]
        scale_method = config["SF"]["scale_method"]
        mwr_vals = [int(s) for s in config["SF"]["mwr_values"].split(",")]

        # Populate gui fields with config file info
        self.Minimax_radioButton.setEnabled(False)
        self.Maximin_radioButton.setChecked(True)
        if scale_method == "direct_mwr":
            self.Direct_radioButton.setChecked(True)
        elif scale_method == "ranked_mwr":
            self.Ranked_radioButton.setChecked(True)
        self.designSize_spin.setValue(design_size)
        MWRcomboList = [
            self.MWR1_comboBox,
            self.MWR2_comboBox,
            self.MWR3_comboBox,
            self.MWR4_comboBox,
            self.MWR5_comboBox,
        ]
        for i in range(len(mwr_vals)):
            combo = MWRcomboList[i]
            combo.setCurrentText(str(mwr_vals[i]))

        if hfile == "":
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

        self.sampleSize_comboBox.setCurrentText(str(nr))
        self.updateRunTimeNUSF(self.testRuntime[0])
        self.designInfo2_dynamic.setText(
            "mwr = %d, n = %d"
            % (
                int(self.MWR1_comboBox.currentText()),
                int(self.sampleSize_comboBox.currentText()),
            )
        )

    def loadFromConfigFileIRSF(self, config_file):
        # Read from config file
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file)
        design_size = int(config["METHOD"]["design_size"])
        nr = int(config["METHOD"]["number_random_starts"])
        hfile = config["INPUT"]["history_file"]
        cfile = config["INPUT"]["candidate_file"]
        include = [s.strip() for s in config["INPUT"]["include"].split(",")]
        type = [s.strip() for s in config["INPUT"]["types"].split(",")]

        # Populate gui fields with config file info

        self.Minimax_radioButton.setEnabled(False)
        self.Maximin_radioButton.setChecked(True)
        self.designSizeIRSF_spin.setValue(design_size)

        if hfile == "":
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
        for i in range(len(type)):
            self.inputSdoeTable.cellWidget(i, self.typeCol).setCurrentText(type[i])

        self.sampleSize_comboBox.setCurrentText(str(nr))
        self.updateRunTimeIRSF(self.testRuntime[0])
        self.designInfo2_dynamic.setText(
            "d = %d, n = %d"
            % (
                int(self.designSizeIRSF_spin.value()),
                int(self.sampleSize_comboBox.currentText()),
            )
        )

        QApplication.processEvents()

    def showOrderFileLoc(self, fname):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Order design completed.")
        msg.setText("Ordered candidates saved to \n{}".format(fname))
        msg.setInformativeText("Continue?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        reply = msg.exec_()
        return reply

    def orderDesign(self):
        self.freeze()
        row = self.analysisTable.selectedIndexes()[0].row()
        outfiles = self.analysis[row].fnames
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


class SdoeAnalysisData:
    def __init__(
        self,
        sf_method=None,
        optimality=None,
        mwr=None,
        d=None,
        nr=None,
        runtime=None,
        criterion=None,
        designs=None,
        config_file=None,
        fnames=None,
        results=None,
    ):
        self.sf_method = sf_method
        self.optimality = optimality
        self.mwr = mwr
        self.d = d
        self.nr = nr
        self.runtime = runtime
        self.criterion = criterion
        self.designs = designs
        self.config_file = config_file
        self.fnames = fnames
        self.results = results
