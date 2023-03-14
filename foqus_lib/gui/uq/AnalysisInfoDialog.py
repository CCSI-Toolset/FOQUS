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
import copy
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QPushButton,
    QDialog,
)
from PyQt5.QtGui import QFont
from collections import OrderedDict
from foqus_lib.framework.uq.Distribution import Distribution
from foqus_lib.framework.uq.ResponseSurfaces import ResponseSurfaces


class AnalysisInfoDialog(QDialog):
    def __init__(self, info, parent=None):
        super(AnalysisInfoDialog, self).__init__(parent)
        self.setWindowTitle("Analysis Additional Info")
        self.resize(400, 400)
        self.gridLayout = QGridLayout(self)
        self.table = QTableWidget()
        self.table.setRowCount(len(list(info.keys())))
        self.table.setColumnCount(1)

        boldFont = QFont()
        boldFont.setWeight(75)
        boldFont.setBold(True)

        totalHeight = 20
        totalWidth = 50
        row = 0
        for key in list(info.keys()):
            if key in ("xprior", "xtable", "ytable", "obsTable"):
                continue
            # item = QTableWidgetItem(key)
            # self.table.setItem(row, 0, item)
            if isinstance(info[key], (list, tuple)):
                strings = []
                for strItem in info[key]:
                    if isinstance(strItem, dict):
                        ks = list(strItem.keys())
                        for k in ks:
                            if strItem[k] is None:
                                del strItem[k]
                    strings.append(str(strItem))

                item = QTableWidgetItem("\n".join(strings))
            else:
                item = QTableWidgetItem(str(info[key]))
            self.table.setItem(row, 0, item)
            row += 1
        if row > 0:
            label = QLabel("Additional Info")
            label.setFont(boldFont)
            self.gridLayout.addWidget(label)

            self.gridLayout.addWidget(self.table)
            self.table.horizontalHeader().setHidden(True)
            self.table.setRowCount(row)
            self.table.setVerticalHeaderLabels(
                [
                    key
                    for key in list(info.keys())
                    if key not in ("xprior", "xtable", "ytable", "obsTable")
                ]
            )
            # self.table.verticalHeader().setHidden(True)
            self.table.setWordWrap(True)
            self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()

            self.show()  # Needed for headers to be correctly sized
            width = 2 + self.table.verticalHeader().width() + self.table.columnWidth(0)
            if self.table.verticalScrollBar().isVisible():
                width += self.table.verticalScrollBar().width()
            self.table.setMinimumWidth(width)
            maxHeight = 3
            for i in range(row):
                maxHeight += self.table.rowHeight(i)
            self.table.setMinimumHeight(maxHeight)

            totalHeight += maxHeight + 20
            if width + 20 > totalWidth:
                totalWidth = width + 20

        # Show table
        for key in info:
            if key in ("xprior", "xtable", "ytable", "obsTable"):
                # self.resize(800, 400)
                values = info[key]
                for d in values:
                    if d is not None and "type" in d and d["type"] == "Design":
                        keys = list(d.keys())
                        for k in keys:
                            if k not in ("name", "type"):
                                del d[k]

                if key == "ytable":
                    labelString = "Outputs"
                elif key == "obsTable":
                    labelString = "Experiments"
                else:
                    labelString = "Inputs"
                label = QLabel(labelString)
                label.setFont(boldFont)
                self.gridLayout.addWidget(label)
                table = QTableWidget()
                self.gridLayout.addWidget(table)
                table.setRowCount(
                    len([1 for i in range(len(values)) if values[i] is not None])
                )

                # column headers
                if key == "obsTable":
                    inputInfo = info["xtable"]
                    designVars = []
                    for d in inputInfo:
                        if "type" in d and d["type"] == "Design":
                            designVars.append(d["name"])
                    columnHeaders = [name + " Value" for name in designVars]
                    outputInfo = info["ytable"]
                    outputVars = [d["name"] for d in outputInfo if d is not None]
                    for out in outputVars:
                        columnHeaders.append(out + " Mean")
                        columnHeaders.append(out + " Std Dev")
                    table.setColumnCount(len(columnHeaders))
                    table.setHorizontalHeaderLabels(columnHeaders)
                    table.setVerticalHeaderLabels(
                        ["Experiment " + str(num) for num in range(1, len(values) + 1)]
                    )
                else:
                    columnSet = set()
                    if key == "ytable":
                        valuesKeys = [
                            "name",
                            "rsIndex",
                            "legendreOrder",
                            "marsBases",
                            "marsInteractions",
                            "userRegressionFile",
                        ]
                        columnHeaders = [
                            "Output Name",
                            "RS Type",
                            "Legendre Order",
                            "MARS # Basis Functions",
                            "MARS Deg. of Interaction",
                            "User Regression File",
                        ]
                    else:  # xprior, xtable
                        valuesKeys = [
                            "name",
                            "type",
                            "value",
                            "pdf",
                            "param1",
                            "param2",
                            "min",
                            "max",
                        ]
                        columnHeaders = [
                            "Input Name",
                            "Type",
                            "Fixed Value",
                            "PDF",
                            "PDF Param 1",
                            "PDF Param 2",
                            "Min",
                            "Max",
                        ]
                    for d in values:
                        if d is not None:
                            d2 = copy.deepcopy(d)
                            for key in d2:
                                if d2[key] is None:
                                    del d[key]
                            columnSet = columnSet.union(set(d.keys()))
                    table.setColumnCount(len(columnSet))
                    usedColumns = []
                    usedHeaders = []
                    columnIndices = {}
                    for i, (valuesKey, header) in enumerate(
                        zip(valuesKeys, columnHeaders)
                    ):
                        if valuesKey in columnSet:
                            usedColumns.append(valuesKey)
                            usedHeaders.append(header)
                            columnIndices[valuesKey] = i
                    table.setHorizontalHeaderLabels(usedHeaders)
                    table.verticalHeader().setHidden(True)
                table.setWordWrap(True)

                r = 0
                for i in range(len(values)):
                    if key == "obsTable":
                        for c, string in enumerate(values[r][1:]):
                            item = QTableWidgetItem(string)
                            table.setItem(r, c, item)
                        r += 1
                    elif values[r] is not None:
                        for c, colName in enumerate(usedColumns):
                            if colName in values[r]:
                                if colName == "pdf":
                                    string = Distribution.getFullName(
                                        values[r][colName]
                                    )
                                elif colName == "rsIndex":
                                    string = ResponseSurfaces.getFullName(
                                        values[r][colName]
                                    )
                                else:
                                    string = str(values[r][colName])
                                item = QTableWidgetItem(string)
                                table.setItem(r, c, item)
                        r += 1
                table.resizeColumnsToContents()

                QtCore.QCoreApplication.processEvents()
                width = 2
                if key == "obsTable":
                    width += table.verticalHeader().width()
                for i in range(table.columnCount()):
                    width += table.columnWidth(i)
                if table.verticalScrollBar().isVisible():
                    width += table.verticalScrollBar().width()
                if width > 800:
                    width = 800
                table.setMinimumWidth(width)
                maxHeight = 3 + table.horizontalHeader().height()
                for i in range(table.rowCount()):
                    maxHeight += table.rowHeight(i)
                maxHeight = min([maxHeight, 400])
                table.setMinimumHeight(maxHeight)

                totalHeight += maxHeight + 20
                if width + 20 > totalWidth:
                    totalWidth = width + 20

        self.okButton = QPushButton(self)
        self.okButton.setText("OK")
        self.okButton.clicked.connect(self.close)
        self.gridLayout.addWidget(self.okButton)
        self.show()
        self.resize(totalWidth, totalHeight)
