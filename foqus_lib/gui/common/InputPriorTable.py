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
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QCheckBox,
    QMessageBox,
    QAbstractItemView,
    QSpinBox,
    QFileDialog,
)
from PyQt5.QtGui import QColor
import numpy as np

from foqus_lib.framework.uq.SampleData import *
from foqus_lib.framework.uq.LocalExecutionModule import *


class InputPriorTable(QTableWidget):
    typeChanged = pyqtSignal()
    pdfChanged = pyqtSignal()

    SIMSETUP, RSANALYSIS, INFERENCE, OUU, ODOE = list(range(5))

    def __init__(self, parent=None):
        super(InputPriorTable, self).__init__(parent)
        self.typeItems = []
        self.format = "%g"  # numeric format for table entries in UQ Toolbox
        self.paramColWidth = 126
        self.labelWidth = 62
        self.paramWidth = 62
        self.obsTableValues = {}
        self.sampleFiles = []
        self.dispSampleFiles = []
        self.sampleNumInputs = []
        self.epistemicMode = False
        self.rsEvalMode = False
        self.useTypeChangedSignal = True

        # You must call init() separately.

    # Put code to upgrade from QTableWidget to InputPriorTable here as well as init table
    def init(self, data, mode, wizardMode=False, viewOnly=False):
        self.blockSignals(True)
        self.data = data
        self.mode = mode
        # self.simSetup = (mode == InputPriorTable.SIMSETUP)
        # self.inferenceTable = (mode == InputPriorTable.INFERENCE)
        # self.rsAnalysis = (mode == InputPriorTable.RSANALYSIS)
        # self.ouu = (mode == InputPriorTable.OUU)
        self.wizardMode = wizardMode  # RSANALYSIS mode
        self.viewOnly = viewOnly  # SIMSETUP mode : Generate ensemble

        # populate prior table
        inVarNames = data.getInputNames()
        inVarTypes = data.getInputTypes()
        nInputs = data.getNumInputs()
        nVariableInputs = inVarTypes.count(Model.VARIABLE)
        self.dist = data.getInputDistributions()
        dist = self.dist
        self.setupLB()
        self.setupUB()
        self.defaults = data.getInputDefaults()
        self.setupDists()

        if self.mode == InputPriorTable.INFERENCE:
            col_index = {"name": 0, "type": 1, "check": 2, "value": 3}
            if not wizardMode:
                col_index.update({"pdf": 4, "p1": 5, "p2": 6, "min": 7, "max": 8})
        elif self.mode == InputPriorTable.SIMSETUP:
            col_index = {
                "name": 0,
                "type": 1,
                "value": 2,
                "min": 3,
                "max": 4,
                "pdf": 5,
                "p1": 6,
                "p2": 7,
            }
        elif self.mode == InputPriorTable.RSANALYSIS:  # RS Analysis
            col_index = {
                "name": 0,
                "type": 1,
                "value": 2,
                "pdf": 3,
                "p1": 4,
                "p2": 5,
                "min": 6,
                "max": 7,
            }
        elif self.mode == InputPriorTable.ODOE:  # ODOE
            col_index = {
                "name": 0,
                "type": 1,
                "value": 2,
                "pdf": 3,
                "p1": 4,
                "p2": 5,
                "min": 6,
                "max": 7,
            }
        else:  # OUU
            col_index = {
                "check": 0,
                "name": 1,
                "type": 2,
                "scale": 3,
                "min": 4,
                "max": 5,
                "value": 6,
                "pdf": 7,
                "p1": 8,
                "p2": 9,
            }
        self.col_index = col_index
        flowsheetFixed = data.getInputFlowsheetFixed()
        # rowCount = 0
        if self.mode == InputPriorTable.SIMSETUP:
            rowCount = nInputs
        else:
            rowCount = nVariableInputs
        # for i in xrange(nInputs):
        #     if not flowsheetFixed[i] and inVarTypes[i] != Model.FIXED:
        #         rowCount += 1
        self.setRowCount(rowCount)
        self.setColumnCount(len(col_index))
        if self.mode == InputPriorTable.RSANALYSIS:
            self.setColumnHidden(col_index["type"], True)
            self.setColumnHidden(col_index["value"], True)
        r = 0  # row index

        for i in range(nInputs):
            # do not add fixed input variables to table
            if self.mode != InputPriorTable.SIMSETUP and inVarTypes[i] == Model.FIXED:
                continue

            if not dist:
                dtype = Distribution.UNIFORM
                d = Distribution(dtype)
            else:
                d = dist[i]  # distribution
                dtype = d.getDistributionType()  # distribution type

            if dtype == Distribution.SAMPLE:
                sampleFile, sampleIndex = d.getParameterValues()
                if sampleFile.endswith(".csv"):
                    data = LocalExecutionModule.readSampleFromCsvFile(sampleFile, False)
                    sampleData = data.getInputData()
                else:
                    data = LocalExecutionModule.readDataFromSimpleFile(sampleFile)
                    sampleData = data[0]
                # compute min/max from sample file
                sdata = sampleData[:, sampleIndex - 1]
                # TO DO: insert error handling for if sampleData file does not exist or if incorrect # of columns
                xmin = np.min(sdata)
                xmax = np.max(sdata)
                sampleIndex += 1
            else:
                xmin = self.lb[i]
                xmax = self.ub[i]

            p1val, p2val = d.getParameterValues()  # distribution parameter values
            p1name, p2name = Distribution.getParameterNames(
                dtype
            )  # distribution parameter names

            nameMask = ~Qt.ItemIsEnabled
            # add input name
            item = QTableWidgetItem(inVarNames[i])
            flags = item.flags()
            item.setFlags(flags & nameMask)
            item.setForeground(Qt.black)
            self.setItem(r, col_index["name"], item)

            # add type
            comboFixed = False
            if "type" in col_index:
                combobox = QComboBox()
                combobox.addItems(self.typeItems)
                if self.mode == InputPriorTable.SIMSETUP:
                    if inVarTypes[i] == Model.FIXED:
                        combobox.setCurrentIndex(1)
                combobox.setProperty("row", r)
                combobox.setProperty("col", col_index["type"])
                combobox.setMinimumContentsLength(8)
                combobox.currentIndexChanged[int].connect(self.updatePriorTableRow)
                if self.viewOnly:
                    combobox.setEnabled(False)
                self.setCellWidget(r, col_index["type"], combobox)

                if combobox.currentText() == "Fixed":
                    comboFixed = True
                if self.mode == InputPriorTable.ODOE:
                    combobox.removeItem(1)
            # add display checkbox
            if "check" in col_index:
                chkbox = QCheckBox("")
                if self.mode == InputPriorTable.OUU:
                    chkbox.setChecked(False)
                else:
                    chkbox.setChecked(True)
                self.setCellWidget(r, col_index["check"], chkbox)

            # add fixed value column
            if "value" in col_index:
                if self.defaults[i] is None:
                    s = ""
                else:
                    s = self.format % self.defaults[i]
                if inVarTypes[i] == Model.FIXED or comboFixed:
                    item = QTableWidgetItem(s)
                    if self.viewOnly:
                        flags = item.flags()
                        item.setFlags(flags & ~Qt.ItemIsEnabled)
                        item.setForeground(Qt.black)
                    item.setBackground(Qt.white)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.setItem(r, col_index["value"], item)
                    self.obsTableValues[(r, col_index["value"])] = s
                else:
                    self.clearCell(r, col_index["value"], s, createItem=True)
            # add scale column
            if "scale" in col_index:
                self.clearCell(r, col_index["scale"], createItem=True)

            # add distribution
            if "pdf" in col_index:
                combobox = QComboBox()
                distNames = Distribution.fullNames
                # if self.mode in (InputPriorTable.INFERENCE, InputPriorTable.OUU):
                #     distNames = distNames[0:-1]    # omit SAMPLE (not currently supported)
                combobox.addItems(distNames)
                combobox.setCurrentIndex(dtype)
                combobox.setProperty("row", r)
                combobox.setProperty("col", col_index["pdf"])
                combobox.currentIndexChanged[int].connect(self.updatePriorTableRow)
                combobox.setMinimumContentsLength(10)
                typeCombo = self.cellWidget(r, col_index["type"])
                if self.viewOnly:
                    combobox.setEnabled(False)
                else:
                    text = typeCombo.currentText()
                    if (
                        "type" in col_index and self.isColumnHidden(col_index["type"])
                    ) or text in ["Variable", "Aleatory", "UQ: Continuous (Z4)"]:
                        combobox.setEnabled(True)
                    else:
                        combobox.setEnabled(False)
                self.setCellWidget(r, col_index["pdf"], combobox)
            # add param1
            if "p1" in col_index:
                if p1name is not None:
                    self.activateCell(r, col_index["p1"], "", True)
                    self.activateParamCell(r, 1, p1name, p1val)
                else:
                    self.clearParamCell(r, 1)
            # add param2
            if "p2" in col_index:
                if p2name is not None:
                    self.activateCell(r, col_index["p2"], "", True)
                    self.activateParamCell(r, 2, p2name, p2val)
                else:
                    self.clearParamCell(r, 2)

            # add min/max
            if dtype == Distribution.UNIFORM or self.mode == InputPriorTable.SIMSETUP:
                c = Qt.white
            else:
                c = Qt.lightGray

            if "min" in col_index:
                s = self.format % xmin
                if inVarTypes[i] == Model.FIXED or comboFixed:
                    self.clearCell(r, col_index["min"], s, createItem=True)
                else:
                    item = QTableWidgetItem(s)
                    if self.viewOnly:
                        flags = item.flags()
                        item.setFlags(flags & ~Qt.ItemIsEnabled)
                        item.setForeground(Qt.black)
                    if len(s.strip()) == 0:
                        item.setBackground(Qt.red)
                    else:
                        item.setBackground(c)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.setItem(r, col_index["min"], item)
                    self.obsTableValues[(r, col_index["min"])] = s

            if "max" in col_index:
                s = self.format % xmax
                if inVarTypes[i] == Model.FIXED or comboFixed:
                    self.clearCell(r, col_index["max"], s, createItem=True)
                else:
                    item = QTableWidgetItem(s)
                    if self.viewOnly:
                        flags = item.flags()
                        item.setFlags(flags & ~Qt.ItemIsEnabled)
                        item.setForeground(Qt.black)
                    if len(s.strip()) == 0:
                        item.setBackground(Qt.red)
                    else:
                        item.setBackground(c)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.setItem(r, col_index["max"], item)
                    self.obsTableValues[(r, col_index["max"])] = s

            r = r + 1  # increment row

        self.resizeColumns()
        self.cellChanged.connect(self.change)
        self.blockSignals(False)

    def setupLB(self):
        inVarTypes = self.data.getInputTypes()
        self.lb = self.data.getInputMins()
        self.lbVariable = [
            self.lb[i] for i in range(len(self.lb)) if inVarTypes[i] == Model.VARIABLE
        ]

    def setupUB(self):
        inVarTypes = self.data.getInputTypes()
        self.ub = self.data.getInputMaxs()
        self.ubVariable = [
            self.ub[i] for i in range(len(self.ub)) if inVarTypes[i] == Model.VARIABLE
        ]

    def setupDists(self):
        if self.dist == None:
            self.distVariable = None
        else:
            inVarTypes = self.data.getInputTypes()
            self.distVariable = [
                self.dist[i]
                for i in range(len(self.dist))
                if inVarTypes[i] == Model.VARIABLE
            ]

    def resizeColumns(self):
        col_index = self.col_index
        self.resizeColumnsToContents()
        if "p1" in col_index:
            self.setColumnWidth(col_index["p1"], self.paramColWidth)
        if "p2" in col_index:
            self.setColumnWidth(col_index["p2"], self.paramColWidth)

    def change(self, row, col, hideError=False):  # check values
        item = self.item(row, col)
        if item is not None:
            text = item.text()
            if (row, col) in self.obsTableValues and text == self.obsTableValues[
                (row, col)
            ]:
                return
            self.obsTableValues[(row, col)] = text
            if len(text) > 0 or (
                "min" in self.col_index
                and col in (self.col_index["min"], self.col_index["max"])
            ):
                if "min" in self.col_index:
                    minItem = self.item(row, self.col_index["min"])
                    maxItem = self.item(row, self.col_index["max"])

                showMessage = False
                outOfBounds = False
                minMoreThanMax = False
                if not self.isnumeric(text):
                    showMessage = True
                    message = "Value must be a number!"
                    outOfBounds = True
                else:
                    value = float(item.text())

                    if value < self.lbVariable[row] or value > self.ubVariable[row]:
                        showMessage = False
                        message = "Value outside bounds. Your response surface will be extrapolating, which could lead to lower accuracy. Your new bounds will not be saved to the flowsheet."
                        outOfBounds = False

                    if (
                        "min" in self.col_index
                        and "max" in self.col_index
                        and col in (self.col_index["min"], self.col_index["max"])
                    ):
                        if minItem is not None and maxItem is not None:
                            minVal = float(minItem.text())
                            maxVal = float(maxItem.text())

                            if minVal >= maxVal:
                                minMoreThanMax = True
                                showMessage = True
                                message = (
                                    "Minimum value must be less than maximum value!"
                                )

                if showMessage and not hideError:
                    msgbox = QMessageBox()
                    msgbox.setWindowTitle("UQ/Opt GUI Warning")
                    msgbox.setText(message)
                    msgbox.setIcon(QMessageBox.Warning)
                    response = msgbox.exec_()
                    self.setFocus()

                if outOfBounds:
                    # item.setForeground(QColor(192,0,0))
                    item.setBackground(QColor(255, 0, 0))
                    self.setCurrentCell(row, col)
                elif minMoreThanMax:
                    # minItem.setForeground(QColor(192,0,0))
                    # maxItem.setForeground(QColor(192,0,0))
                    minItem.setBackground(QColor(255, 0, 0))
                    maxItem.setBackground(QColor(255, 0, 0))
                else:
                    # item.setForeground(QColor(0,0,0))
                    item.setBackground(QColor(255, 255, 255))
                    if "min" in self.col_index and col in (
                        self.col_index["min"],
                        self.col_index["max"],
                    ):
                        if minItem is not None and maxItem is not None:
                            minVal = float(minItem.text())
                            maxVal = float(maxItem.text())
                            if self.mode == InputPriorTable.SIMSETUP:
                                # minItem.setForeground(QColor(0,0,0))
                                # maxItem.setForeground(QColor(0,0,0))
                                minItem.setBackground(QColor(255, 255, 255))
                                maxItem.setBackground(QColor(255, 255, 255))
                            else:
                                if (
                                    minVal < self.ubVariable[row]
                                    and maxVal > self.lbVariable[row]
                                ):
                                    # minItem.setForeground(QColor(0,0,0))
                                    # maxItem.setForeground(QColor(0,0,0))
                                    minItem.setBackground(QColor(255, 255, 255))
                                    maxItem.setBackground(QColor(255, 255, 255))

        self.resizeColumns()
        self.pdfChanged.emit()

    def setAleatoryEpistemicMode(self, on):
        if self.epistemicMode == on:
            return
        self.epistemicMode = on
        col_index = self.col_index

        self.setColumnHidden(col_index["type"], not on)
        self.setColumnHidden(col_index["value"], not on)
        self.setColumnHidden(col_index["pdf"], False)
        self.setColumnHidden(col_index["p1"], False)
        self.setColumnHidden(col_index["p2"], False)
        self.setColumnHidden(col_index["min"], False)
        self.setColumnHidden(col_index["max"], False)

        numRows = self.rowCount()
        # Disable typechanged signal
        self.useTypeChangedSignal = False
        for row in range(numRows):
            self.updateRow(row, col_index["type"])
        self.useTypeChangedSignal = True

    def setSolventFitMode(self, on):
        distNames = Distribution.fullNames
        if "pdf" in self.col_index:
            for r in range(self.rowCount()):
                combobox = self.cellWidget(r, self.col_index["pdf"])
                # Change distributions
                count = combobox.count()
                if on:  # solvent fit.  Only use first 3 items and fifth
                    if count > 4:
                        index = combobox.currentIndex()
                        if index == 3 or index > 4:
                            combobox.setCurrentIndex(0)
                        for i in range(count - 5):
                            combobox.removeItem(5)
                        combobox.removeItem(3)
                else:
                    if count < len(distNames):
                        combobox.insertItem(3, distNames[3])
                        for name in distNames[count + 1 :]:
                            combobox.addItem(name)

    def setRSEvalMode(self, on):
        if self.rsEvalMode == on:
            return
        self.rsEvalMode = on
        col_index = self.col_index

        self.setColumnHidden(col_index["value"], not on)
        self.setColumnHidden(col_index["type"], on)
        self.setColumnHidden(col_index["pdf"], on)
        self.setColumnHidden(col_index["p1"], on)
        self.setColumnHidden(col_index["p2"], on)
        self.setColumnHidden(col_index["min"], on)
        self.setColumnHidden(col_index["max"], on)

        numRows = self.rowCount()
        # Disable typechanged signal
        self.useTypeChangedSignal = False
        for row in range(numRows):
            self.updateRow(row, col_index["type"])
        self.useTypeChangedSignal = True

    def updatePriorTableRow(self):
        # identify the row of inputPrior_table that requires updating
        combobox = self.sender()  # the pdf combobox that sent the signal
        r = combobox.property("row")
        c = combobox.property("col")

        self.updateRow(r, c)

    def updateRow(self, r, c):
        try:
            self.cellChanged.disconnect(self.change)
        except:
            return
        col_index = self.col_index

        # get selected row of simulationTable
        data = self.data
        inVarNames = list(data.getInputNames())

        if "pdf" in col_index:
            pdfcombo = self.cellWidget(r, col_index["pdf"])

        # Type was changed
        if "type" in col_index and c == col_index["type"]:
            if self.useTypeChangedSignal:
                self.typeChanged.emit()

            combobox = self.cellWidget(r, col_index["type"])
            cbtext = combobox.currentText()
            if self.mode != InputPriorTable.OUU and "check" in col_index:
                # Disable view checkbox if not variable parameter
                checkbox = self.cellWidget(r, col_index["check"])
                checkbox.setEnabled(cbtext == "Variable")
            # Value column
            if cbtext == "Fixed" or self.rsEvalMode:
                self.activateCell(r, col_index["value"])
                if "min" in col_index:
                    self.clearMinMax(r)
            elif cbtext in [
                "Epistemic",
                "Opt: Primary Continuous (Z1)",
                "Opt: Primary Discrete (Z1d)",
                "Opt: Recourse (Z2)",
            ]:
                self.activateCell(r, col_index["value"])
                self.activateMinMax(r, inVarNames)
            elif cbtext == "UQ: Discrete (Z3)":
                self.clearCell(r, col_index["value"])
                self.clearMinMax(r)
            else:
                self.clearCell(r, col_index["value"])
                if "min" in col_index:
                    self.activateMinMax(r, inVarNames)

            # Scale column
            if "scale" in col_index:
                if "Primary" in cbtext:
                    self.activateCell(r, col_index["scale"])
                else:
                    self.clearCell(r, col_index["scale"])

            # PDF columns
            if "pdf" in col_index:
                if self.isColumnHidden(col_index["type"]) or cbtext in [
                    "Variable",
                    "Aleatory",
                    "UQ: Continuous (Z4)",
                ]:
                    pdfcombo.setEnabled(True)
                else:
                    pdfcombo.setEnabled(False)
                    self.clearParamCell(r, 1)
                    self.clearParamCell(r, 2)
                    self.cellChanged.connect(self.change)
                    return

        if "pdf" in col_index:
            # update the row in inputPrior_table
            d = pdfcombo.currentText()  # distribution type
            d = Distribution.getEnumValue(d)
            dist = Distribution(d)
            d1name, d2name = Distribution.getParameterNames(
                d
            )  # distribution parameter names

            # TO DO: handle the case 'd == Distribution.SAMPLE'
            if d == Distribution.UNIFORM:
                # clear and deactivate param1/param2
                self.clearParamCell(r, 1)
                self.clearParamCell(r, 2)
                self.activateMinMax(r, inVarNames)
            elif d == Distribution.SAMPLE:
                self.activateFileCells(r)
                self.clearMinMax(r)
            else:
                value1 = None
                value2 = None
                dists = self.dist
                if dists is not None:
                    defaultDist = dists[r]
                    if (
                        defaultDist is not None
                        and d == defaultDist.getDistributionType()
                    ):
                        (value1, value2) = defaultDist.getParameterValues()
                self.activateParamCell(r, 1, d1name, value1)
                if d2name is None:
                    self.clearParamCell(r, 2)
                else:
                    self.activateParamCell(r, 2, d2name, value2)
                if self.mode != InputPriorTable.SIMSETUP:
                    self.clearMinMax(r)

            self.setColumnWidth(col_index["p1"], self.paramColWidth)
            self.setColumnWidth(col_index["p2"], self.paramColWidth)

        if "pdf" in col_index and c == col_index["pdf"]:
            self.pdfChanged.emit()

        self.resizeColumns()
        self.cellChanged.connect(self.change)

    def clearCell(self, row, col, text=None, createItem=False):
        col_index = self.col_index
        if createItem:
            item = QTableWidgetItem("")
            self.setItem(row, col, item)
        else:
            item = self.item(row, col)
        item.setBackground(Qt.lightGray)
        if text is not None:
            item.setText(text)
            try:
                float(text)
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            except ValueError:
                pass
        mask = ~Qt.ItemIsEnabled
        flags = item.flags()
        item.setFlags(flags & mask)

    def activateCell(self, row, col, text=None, createItem=False):
        col_index = self.col_index
        if createItem:
            item = QTableWidgetItem("")
            self.setItem(row, col, item)
        else:
            item = self.item(row, col)
        item.setBackground(Qt.white)
        if text is not None and not item.text():
            item.setText(text)
            try:
                float(text)
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            except ValueError:
                pass
        mask = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        flags = item.flags()
        item.setFlags(flags | mask)

    def clearParamCell(self, row, paramNum):
        col_index = self.col_index
        if paramNum == 1:
            col = col_index["p1"]
        else:  # assume param 2
            col = col_index["p2"]

        self.removeCellWidget(row, col)
        self.clearCell(row, col, createItem=True)

    def activateParamCell(self, row, paramNum, text, value=None):
        col_index = self.col_index
        if paramNum == 1:
            col = col_index["p1"]
        else:  # assume param 2
            col = col_index["p2"]

        self.activateCell(row, col)

        # clear and activate
        nameMask = ~Qt.ItemIsEnabled
        pname = QTableWidgetItem(text)
        pname.setBackground(Qt.white)
        pname.setForeground(Qt.black)
        flags = pname.flags()
        pname.setFlags(flags & nameMask)

        # add 2-cell table
        cellTable = self.cellWidget(row, col)
        if isinstance(cellTable, QComboBox):  # combo from file selection
            self.removeCellWidget(row, col)
            cellTable = None
        if cellTable is None:
            cellTable = QTableWidget(self)
            self.setCellWidget(row, col, cellTable)
        cellTable.clear()
        cellTable.setRowCount(1)
        cellTable.setColumnCount(2)
        cellTable.horizontalHeader().setVisible(False)
        cellTable.verticalHeader().setVisible(False)
        cellTable.setProperty("row", row)
        cellTable.setProperty("col", col)
        cellTable.setItem(0, 0, pname)
        if value is not None:
            pval = QTableWidgetItem(str(value))
            cellTable.setItem(0, 1, pval)
            if self.viewOnly:
                flags = pval.flags()
                pval.setFlags(flags & ~Qt.ItemIsEnabled)
                pval.setForeground(Qt.black)
        cellTable.setColumnWidth(0, self.labelWidth)
        cellTable.setColumnWidth(1, self.paramWidth)
        cellTable.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        cellTable.cellChanged.connect(self.paramChange)
        cellTable.setEditTriggers(
            QAbstractItemView.AllEditTriggers
        )  # Allow single click to edit

        return cellTable

    def paramChange(self):
        cellTable = self.sender()
        cellTable.cellChanged.disconnect()
        row = cellTable.property("row")
        col = cellTable.property("col")
        pdfCombo = self.cellWidget(row, self.col_index["pdf"])
        dist = pdfCombo.currentIndex()

        outOfBounds = False
        showMessage = False
        item = cellTable.item(0, 1)
        # Value must not be less than 0
        if item is not None and item.text():
            if self.isnumeric(item.text()):
                value = float(item.text())
                if col == self.col_index["p2"] and dist in (
                    Distribution.NORMAL,
                    Distribution.LOGNORMAL,
                    Distribution.TRIANGLE,
                ):
                    if value <= 0:
                        message = "Value must be greater than 0!  Please fix it."
                        showMessage = True
                        outOfBounds = True
                if dist in (
                    Distribution.LOGNORMAL,
                    Distribution.GAMMA,
                    Distribution.BETA,
                    Distribution.WEIBULL,
                ):
                    if value < 0:
                        message = "Value must not be negative!  Please fix it."
                        showMessage = True
                        outOfBounds = True
            else:
                message = "Entry is not a number!  Please fix it."
                showMessage = True
                outOfBounds = True

        if showMessage:
            msgbox = QMessageBox()
            msgbox.setWindowTitle("UQ/Opt GUI Warning")
            msgbox.setText(message)
            msgbox.setIcon(QMessageBox.Warning)
            response = msgbox.exec_()

        if outOfBounds:
            # item.setForeground(QColor(192,0,0))
            item.setBackground(QColor(255, 0, 0))
            cellTable.setFocus()
        elif item is not None and item.text():
            # item.setForeground(QColor(0,0,0))
            item.setBackground(QColor(255, 255, 255))

        cellTable.cellChanged.connect(self.paramChange)
        self.pdfChanged.emit()

    def activateFileCells(self, row):
        col_index = self.col_index

        self.activateCell(row, col_index["p1"])
        self.activateCell(row, col_index["p2"])
        # File combo
        combobox = self.cellWidget(row, col_index["p1"])
        if isinstance(combobox, QTableWidget):  # cell table from other PDFs
            self.removeCellWidget(row, col_index["p1"])
            combobox = None
        if combobox is None:
            combobox = QComboBox()
            self.setCellWidget(row, col_index["p1"], combobox)
        items = ["Select File"]
        items.extend([os.path.basename(f) for f in self.dispSampleFiles])
        items.append("Browse...")
        for i, item in enumerate(items[: combobox.count()]):
            if i < combobox.count:
                combobox.setItemText(i, items[i])
        combobox.addItems(items[combobox.count() :])
        combobox.setProperty("row", row)
        combobox.currentIndexChanged[int].connect(self.setFile)

        # Index
        cellTable = self.activateParamCell(row, 2, "Input #")
        spinbox = cellTable.cellWidget(0, 1)
        if spinbox is None:
            spinbox = QSpinBox()
            cellTable.setCellWidget(0, 1, spinbox)
        spinbox.setMinimum(1)
        if self.sampleNumInputs:
            spinbox.setMaximum(self.sampleNumInputs[0])
        if combobox.currentText() in ("Browse...", "Select File"):
            cellTable.setEnabled(False)
        else:
            cellTable.setEnabled(True)

    def isSamplePDFChosen(self):
        col_index = self.col_index
        for row in range(self.rowCount()):
            combobox = self.cellWidget(row, col_index["pdf"])
            if combobox.currentText() == Distribution.getFullName(Distribution.SAMPLE):
                return True
        return False

    def setFile(self):
        col_index = self.col_index
        combobox = self.sender()
        combobox.blockSignals(True)
        currentRow = combobox.property("row")
        text = combobox.currentText()
        if text == "Browse...":
            if platform.system() == "Windows":
                allFiles = "*.*"
            else:
                allFiles = "*"
            fname, _ = QFileDialog.getOpenFileName(
                self,
                "Load Sample file",
                "",
                "Psuade Simple Files (*.smp);;CSV (Comma delimited) (*.csv);;All files (%s)"
                % allFiles,
            )

            if len(fname) == 0:  # Cancelled
                combobox.setCurrentIndex(0)
                combobox.blockSignals(False)
                return
            elif fname in self.sampleFiles:
                index = self.sampleFiles.index(fname) + 1
                combobox.setCurrentIndex(index)
                table = self.cellWidget(currentRow, col_index["p2"])
                table.setEnabled(True)
                spinbox = table.cellWidget(0, 1)
                spinbox.setMaximum(self.sampleNumInputs[index - 1])
            else:
                ##                try: # Full PSUADE format
                ##                    data = LocalExecutionModule.readSampleFromPsuadeFile(fname)
                ##                    inputData = data.getInputData()
                ##                    numInputs = data.getNumInputs()
                ##                except:
                dispFName = fname
                try:  # Simple format
                    if fname.endswith(".csv"):
                        data = LocalExecutionModule.readDataFromCsvFile(
                            fname, askForNumInputs=False
                        )
                        Common.initFolder(LocalExecutionModule.dname)
                        newFileName = (
                            LocalExecutionModule.dname
                            + os.sep
                            + os.path.basename(fname)[:-4]
                            + ".smp"
                        )
                        LocalExecutionModule.writeSimpleFile(newFileName, data[0])
                        fname = newFileName
                    else:
                        data = LocalExecutionModule.readDataFromSimpleFile(fname)
                    inputData = data[0]
                    numInputs = inputData.shape[1]
                except:  # Invalid file
                    import traceback

                    traceback.print_exc()
                    msgbox = QMessageBox()
                    msgbox.setWindowTitle("UQ/Opt GUI Warning")
                    msgbox.setText(
                        "File format not recognized!  File must be in PSUADE simple format."
                    )
                    msgbox.setIcon(QMessageBox.Warning)
                    msgbox.exec_()
                    combobox.setCurrentIndex(0)
                    combobox.blockSignals(False)
                    return

                # File format good
                self.sampleFiles.append(fname)
                self.dispSampleFiles.append(os.path.basename(dispFName))
                self.sampleNumInputs.append(numInputs)
                index = len(self.sampleFiles)
                combobox.setCurrentIndex(0)  # Prevent calling twice with Browse...
                combobox.insertItem(index, os.path.basename(dispFName))
                combobox.setCurrentIndex(index)
                for row in range(self.rowCount()):
                    if row != currentRow:
                        combo = self.cellWidget(row, col_index["p1"])
                        if combo is not None and isinstance(combo, QComboBox):
                            currentIndex = combo.currentIndex()
                            combo.setCurrentIndex(0)
                            combo.insertItem(index, os.path.basename(dispFName))
                            combo.setCurrentIndex(currentIndex)
                # Set max index number
                table = self.cellWidget(currentRow, col_index["p2"])
                table.setEnabled(True)
                spinbox = table.cellWidget(0, 1)
                spinbox.setMaximum(numInputs)
        elif text == "Select File":
            table = self.cellWidget(currentRow, col_index["p2"])
            table.setEnabled(False)
        else:  # File selected
            index = combobox.currentIndex()
            table = self.cellWidget(currentRow, col_index["p2"])
            table.setEnabled(True)
            spinbox = table.cellWidget(0, 1)
            spinbox.setMaximum(self.sampleNumInputs[index - 1])
            # Set index to next value if previous row has same file selected
            if (
                currentRow > 0
                and self.cellWidget(currentRow - 1, col_index["pdf"]).currentText()
                == "Sample"
            ):
                if (
                    self.cellWidget(currentRow - 1, col_index["p1"]).currentIndex()
                    == index
                ):
                    prevRowTable = self.cellWidget(currentRow - 1, col_index["p2"])
                    prevRowSpinbox = prevRowTable.cellWidget(0, 1)
                    spinbox.setValue(prevRowSpinbox.value() + 1)

        combobox.blockSignals(False)
        self.pdfChanged.emit()

    def clearMinMax(self, row):
        col_index = self.col_index
        # deactivate min/max
        self.clearCell(row, col_index["min"])
        self.clearCell(row, col_index["max"])

    def activateMinMax(self, row, inVarNames):
        col_index = self.col_index
        # activate min/max
        inVarName = self.item(row, col_index["name"])
        k = inVarNames.index(inVarName.text())
        self.activateCell(row, col_index["min"], self.format % self.lb[k])
        self.activateCell(row, col_index["max"], self.format % self.ub[k])

    def makeAllFixed(self):
        self.setAllToType(1)

    def makeAllVariable(self):
        self.setAllToType(0)

    def setAllToType(self, value):
        numRows = self.rowCount()
        for row in range(numRows):
            combobox = self.cellWidget(row, self.col_index["type"])
            combobox.setCurrentIndex(value)

    def setCheckedToType(self, type):
        QApplication.processEvents()
        col_index = self.col_index
        if isinstance(type, str):  # String
            if type not in self.typeItems:
                raise Exception("setCheckedToType value is not among accepted values")
        for r in range(self.rowCount()):
            checkbox = self.cellWidget(r, col_index["check"])
            combo = self.cellWidget(r, col_index["type"])
            if checkbox.isChecked():
                if isinstance(type, str):  # String
                    combo.setCurrentIndex(self.typeItems.index(type))
                else:  # Integer index
                    combo.setCurrentIndex(type)
                checkbox.setChecked(False)
                checkbox.setEnabled(True)
        QApplication.processEvents()

    def getNumDesignVariables(self):
        col_index = self.col_index
        col = col_index["type"]
        count = 0
        for row in range(self.rowCount()):
            combo = self.cellWidget(row, col)
            if combo.currentText() == "Design":
                count += 1
        return count

    def getNumVariables(self):
        col_index = self.col_index
        col = col_index["type"]
        count = 0
        for row in range(self.rowCount()):
            combo = self.cellWidget(row, col)
            if combo.currentText() == "Variable":
                count += 1
        return count

    def getMins(self):
        return self.lb

    def getMaxs(self):
        return self.ub

    def getFixedVariables(self):
        return self.getVariablesWithType("Fixed")

    def getDesignVariables(self):
        return self.getVariablesWithType("Design")

    def getEpistemicVariables(self):
        return self.getVariablesWithType("Epistemic")

    def getPrimaryVariables(self):
        return self.getVariablesWithType("Z1")

    def getRecourseVariables(self):
        return self.getVariablesWithType("Z2")

    def getUQDiscreteVariables(self):
        return self.getVariablesWithType("Z3")

    def getContinuousVariables(self):
        return self.getVariablesWithType("Z4")

    def getVariablesWithType(self, typeString):
        col_index = self.col_index
        names = []
        indices = []
        if "type" in col_index:
            col = col_index["type"]
            for row in range(self.rowCount()):
                combo = self.cellWidget(row, col)
                if typeString in combo.currentText():
                    names.append(self.item(row, col_index["name"]).text())
                    indices.append(row)
        return names, indices

    def getShowInputList(self):
        nInputs = self.rowCount()
        col_index = self.col_index
        showList = []
        for i in range(nInputs):
            chkbox = self.cellWidget(i, col_index["check"])
            if chkbox is not None and chkbox.isEnabled() and chkbox.isChecked():
                showList.append(i)

        return showList

    def getDistribution(self, row):
        col_index = self.col_index
        combobox = self.cellWidget(row, col_index["pdf"])
        distName = combobox.currentText()
        dtype = Distribution.getEnumValue(distName)
        widget = self.cellWidget(row, col_index["p1"])
        param1 = None
        param2 = None
        if widget:
            if dtype == Distribution.SAMPLE:  # file
                param1 = self.sampleFiles[widget.currentIndex() - 1]
            else:
                param1 = float(widget.item(0, 1).text())
        cellTable = self.cellWidget(row, col_index["p2"])
        if cellTable:
            if dtype == Distribution.SAMPLE:
                param2 = cellTable.cellWidget(0, 1).value()
            else:
                param2 = float(cellTable.item(0, 1).text())
        d = Distribution(dtype)
        d.setParameterValues(param1, param2)
        return d

    @staticmethod
    def isnumeric(str):
        if len(str.strip()) == 0:
            return False
        try:
            float(str)
            return True
        except ValueError:
            return False

    def checkValidInputs(self):

        b = False
        nInputs = self.rowCount()
        col_index = self.col_index
        for i in range(nInputs):
            inputName = self.item(i, col_index["name"]).text()
            type = "Variable"
            if "type" in col_index:
                combobox = self.cellWidget(i, col_index["type"])
                type = combobox.currentText()
            if type == "Variable" or "Z4" in type:
                if "pdf" in col_index:
                    combobox = self.cellWidget(i, col_index["pdf"])
                    distName = combobox.currentText()
                    dtype = Distribution.getEnumValue(distName)
                    if self.mode == InputPriorTable.SIMSETUP:
                        xmin = self.item(i, col_index["min"])
                        xmax = self.item(i, col_index["max"])
                        if (
                            (xmin is not None)
                            and self.isnumeric(xmin.text())
                            and (xmax is not None)
                            and self.isnumeric(xmax.text())
                        ):
                            minVal = float(xmin.text())
                            maxVal = float(xmax.text())
                            if minVal >= maxVal:
                                return (
                                    False,
                                    "Minimum value is not less than max value for %s!"
                                    % inputName,
                                )
                            b = True
                        else:
                            return (
                                False,
                                "Min or max value for %s is not a number!" % inputName,
                            )
                    if dtype == Distribution.UNIFORM:
                        xmin = self.item(i, col_index["min"])
                        xmax = self.item(i, col_index["max"])
                        if (
                            (xmin is not None)
                            and self.isnumeric(xmin.text())
                            and (xmax is not None)
                            and self.isnumeric(xmax.text())
                        ):
                            minVal = float(xmin.text())
                            maxVal = float(xmax.text())
                            if (
                                minVal >= self.ubVariable[i]
                                or maxVal <= self.lbVariable[i]
                                or minVal >= maxVal
                            ):
                                return (
                                    False,
                                    "Minimum value is not less than max value for %s!"
                                    % inputName,
                                )
                            b = True
                        else:
                            return (
                                False,
                                "Min or max value for %s is not a number!" % inputName,
                            )
                    elif dtype == Distribution.LOGNORMAL:  # Lognormal mean less than 0
                        cellTable = self.cellWidget(i, col_index["p1"])
                        param1 = cellTable.item(0, 1)
                        if (param1 is not None) and self.isnumeric(param1.text()):
                            if float(param1.text()) < 0:
                                return (
                                    False,
                                    "Mean value for %s cannot be negative!" % inputName,
                                )
                            b = True
                        else:
                            return (
                                False,
                                "Mean value for %s is not a number!" % inputName,
                            )
                    elif dtype == Distribution.EXPONENTIAL:
                        cellTable = self.cellWidget(i, col_index["p1"])
                        param1 = cellTable.item(0, 1)
                        if (param1 is not None) and self.isnumeric(param1.text()):
                            b = True
                        else:
                            return (
                                False,
                                "Lambda value for %s is not a number!" % inputName,
                            )
                    elif (
                        dtype == Distribution.GAMMA
                        or dtype == Distribution.BETA
                        or dtype == Distribution.WEIBULL
                    ):  # Parameters less than 0
                        cellTable = self.cellWidget(i, col_index["p1"])
                        param1 = cellTable.item(0, 1)
                        cellTable = self.cellWidget(i, col_index["p2"])
                        param2 = cellTable.item(0, 1)
                        if (
                            (param1 is not None)
                            and self.isnumeric(param1.text())
                            and (param2 is not None)
                            and self.isnumeric(param2.text())
                        ):
                            if float(param1.text()) < 0 or float(param2.text()) < 0:
                                return (
                                    False,
                                    "Distribution parameter value for %s cannot be negative!"
                                    % inputName,
                                )
                            b = True
                        else:
                            return (
                                False,
                                "Distribution parameter value for %s is not a number!"
                                % inputName,
                            )

                    elif dtype == Distribution.SAMPLE:
                        combo = self.cellWidget(i, col_index["p1"])
                        text = combo.currentText()
                        if text == "Browse..." or text == "Select File":
                            return False, "No file selected for %s!" % inputName
                        b = True

                    else:
                        cellTable = self.cellWidget(i, col_index["p1"])
                        param1 = cellTable.item(0, 1)  # param1 value
                        cellTable = self.cellWidget(i, col_index["p2"])
                        param2 = cellTable.item(0, 1)  # param2 value
                        if (
                            (param1 is not None)
                            and self.isnumeric(param1.text())
                            and (param2 is not None)
                            and self.isnumeric(param2.text())
                        ):
                            b = True
                        else:
                            return (
                                False,
                                "Distribution parameter value for %s is not a number!"
                                % inputName,
                            )
                else:
                    b = True
            elif type == "Fixed":
                value = self.item(i, col_index["value"])
                if value is not None and self.isnumeric(value.text()):
                    value = float(value.text())
                    b = True
                else:
                    return False, "Fixed value for %s is not a number!" % inputName
            else:  # Design
                b = True

        return b, None

    def getTableValues(self):
        nInputs = self.rowCount()
        col_index = self.col_index
        values = [None] * nInputs
        for i in range(nInputs):
            inType = "Variable"
            value = {}
            if "name" in col_index:
                item = self.item(i, col_index["name"])
                value["name"] = item.text()
            if "type" in col_index:
                combobox = self.cellWidget(i, col_index["type"])
                inType = combobox.currentText()
                value["type"] = inType
            if (
                self.mode == InputPriorTable.RSANALYSIS and not self.epistemicMode
            ) or inType != "Fixed":
                if (
                    "pdf" in col_index
                    and self.cellWidget(i, col_index["pdf"]).isEnabled()
                ):
                    combobox = self.cellWidget(i, col_index["pdf"])
                    distName = combobox.currentText()
                    dtype = Distribution.getEnumValue(distName)
                    xminText = self.item(i, col_index["min"]).text()
                    if xminText == self.format % self.lbVariable[i]:
                        xmin = self.lbVariable[i]
                    else:
                        xmin = float(xminText)
                    xmaxText = self.item(i, col_index["max"]).text()
                    if xmaxText == self.format % self.lbVariable[i]:
                        xmax = self.ubVariable[i]
                    else:
                        xmax = float(xmaxText)
                    widget = self.cellWidget(i, col_index["p1"])
                    if widget:
                        if dtype == Distribution.SAMPLE:  # file
                            param1 = self.sampleFiles[widget.currentIndex() - 1]
                        else:
                            param1 = float(widget.item(0, 1).text())
                    cellTable = self.cellWidget(i, col_index["p2"])
                    if cellTable:
                        if dtype == Distribution.SAMPLE:
                            param2 = cellTable.cellWidget(0, 1).value()
                        else:
                            param2 = float(cellTable.item(0, 1).text())
                else:  # No pdf setting.  Use default PDFs from data
                    if self.distVariable is None or len(self.distVariable) == 0:
                        dtype = Distribution.UNIFORM
                        param1 = None
                        param2 = None
                    else:
                        print(i)
                        dtype = self.distVariable[i].getDistributionType()
                        param1, param2 = self.distVariable[i].getParameterValues()
                    xmin = self.lbVariable[i]
                    xmax = self.ubVariable[i]

                value.update({"pdf": dtype})
                if dtype == Distribution.UNIFORM:
                    value.update(
                        {"param1": None, "param2": None, "min": xmin, "max": xmax}
                    )
                elif dtype == Distribution.EXPONENTIAL:
                    value.update(
                        {"param1": param1, "param2": None, "min": None, "max": None}
                    )
                elif dtype != None:
                    value.update(
                        {"param1": param1, "param2": param2, "min": None, "max": None}
                    )
            fixedVal = self.item(i, col_index["value"])
            if fixedVal.text() == "":
                value["value"] = None
            else:
                value["value"] = float(fixedVal.text())
            values[i] = value
        return values
