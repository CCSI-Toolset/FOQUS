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
"""dataBrowserFrame.py

* Displays tabulated flowsheet data

John Eslick, Carnegie Mellon University, 2014
"""
import json
import os

from foqus_lib.gui.flowsheet.columns import *
from . import dataFilterDialog
from foqus_lib.gui.flowsheet.dataModel import *
from foqus_lib.gui.flowsheet.calculatedColumns import calculatedColumnsDialog

from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication,
    QMenu,
    QMessageBox,
    QAction,
    QLineEdit,
    QInputDialog,
    QFileDialog,
)

mypath = os.path.dirname(__file__)
_dataBrowserFrameUI, _dataBrowserFrame = uic.loadUiType(
    os.path.join(mypath, "dataBrowserFrame_UI.ui")
)


class dataBrowserFrame(_dataBrowserFrame, _dataBrowserFrameUI):
    def __init__(self, dat, parent):
        super(dataBrowserFrame, self).__init__(parent=parent)
        self.setupUi(self)
        self.dat = dat  # session data
        self.results = None
        self.menu = QMenu()
        self.impMenu = self.menu.addMenu("Import")
        self.expMenu = self.menu.addMenu("Export")
        self.editMenu = self.menu.addMenu("Edit")
        self.calcMenu = self.menu.addMenu("Calculate")
        self.viewMenu = self.menu.addMenu("View")
        self.addMenuActions()
        self.menuButton.setMenu(self.menu)
        self.editFiltersButton.clicked.connect(self.editFilters)
        self.filterSelectBox.currentIndexChanged.connect(self.selectFilter)
        self.tableView.setAlternatingRowColors(True)
        # self.columnsButton.clicked.connect(self.columnSelect)
        self.columnsButton.hide()
        self.saveEnsembleButton.hide()
        self.tableView.verticalHeader().show()
        # for col in range(self.results.count_cols()):
        #    self.tableView.setColumnHidden(col, False)
        # for col in self.results.hidden_cols:
        #    i = list(self.results.columns).index(col)
        #    self.tableView.hideColumn(i)

    def columnSelect(self):
        if self.results is None:
            self.results = self.dat.flowsheet.results
        else:
            if self.results.empty:
                self.results = self.dat.flowsheet.results

        cd = columnsDialog(self.dat, self)
        cd.show()
        for col in range(self.results.count_cols()):
            self.tableView.setColumnHidden(col, False)
        for col in self.results.hidden_cols:
            i = list(self.results.columns).index(col)
            self.tableView.hideColumn(i)

    def addMenuActions(self):
        # export csv
        self.exportCsvAct = QAction("Export to CSV File...", self)
        self.exportCsvAct.triggered.connect(self.saveResultsToCSV)
        self.expMenu.addAction(self.exportCsvAct)
        # copy to clipboard
        self.toClipAct = QAction("Copy Data to Clipboard", self)
        self.toClipAct.triggered.connect(self.toClipboard)
        self.expMenu.addAction(self.toClipAct)
        # import from csv
        self.importCsvAct = QAction("Import from CSV file...", self)
        self.importCsvAct.triggered.connect(self.importCSV)
        self.impMenu.addAction(self.importCsvAct)
        # paste from clipboard
        self.fromClipAct = QAction("Paste Data from Clipboard", self)
        self.fromClipAct.triggered.connect(self.importClip)
        self.impMenu.addAction(self.fromClipAct)
        # copy selected row to flowsheet.
        self.getRowAct = QAction("Row to Flowsheet", self)
        self.getRowAct.triggered.connect(self.rowToFlow)
        self.editMenu.addAction(self.getRowAct)
        # clear data
        self.clearDataAct = QAction("Clear All Data", self)
        self.clearDataAct.triggered.connect(self.clearResults)
        self.editMenu.addAction(self.clearDataAct)
        #
        self.deleteDataAct = QAction("Delete Rows", self)
        self.deleteDataAct.triggered.connect(self.deleteResults)
        self.editMenu.addAction(self.deleteDataAct)
        # Add blank result
        self.addResultAct = QAction("Add Empty Result", self)
        self.addResultAct.triggered.connect(self.addEmptyResult)
        self.editMenu.addAction(self.addResultAct)
        # edit Set
        self.editSetAct = QAction("Edit Set for Selected Rows", self)
        self.editSetAct.triggered.connect(self.editDataSet)
        self.editMenu.addAction(self.editSetAct)
        # hide columns
        self.hideDataColsAct = QAction("Hide Selected Columns", self)
        self.hideDataColsAct.triggered.connect(self.hideCols)
        self.viewMenu.addAction(self.hideDataColsAct)
        # un-hide columns
        self.unhideDataColsAct = QAction("Show All Columns", self)
        self.unhideDataColsAct.triggered.connect(self.unhideCols)
        self.viewMenu.addAction(self.unhideDataColsAct)
        # resize columns
        self.resizeColumnsAct = QAction("Resize Columns", self)
        self.resizeColumnsAct.triggered.connect(self.autoResizeCols)
        self.viewMenu.addAction(self.resizeColumnsAct)

        # Calculated columns menu
        self.calcCols = QAction("&Recalculate", self)
        self.editCalcCol = QAction("&Calculated columns", self)
        self.calcMenu.addAction(self.editCalcCol)
        self.calcMenu.addAction(self.calcCols)
        self.editCalcCol.triggered.connect(self.showCalcEdit)
        self.calcCols.triggered.connect(self.calculate_columns)

    def calculate_columns(self):
        if self.results is None:
            self.results = self.dat.flowsheet.results
        else:
            if self.results.empty:
                self.results = self.dat.flowsheet.results
        self.results.calculate_columns()
        self.refreshContents()

    def showCalcEdit(self):
        calculatedColumnsDialog(self.dat, parent=self).exec_()
        self.calculate_columns()

    def rowToFlow(self):
        if self.results is None:
            self.results = self.dat.flowsheet.results
        else:
            if self.results.empty:
                self.results = self.dat.flowsheet.results

        rows = self.selectedRows()
        if len(rows) < 1:
            return
        self.results.row_to_flow(self.dat.flowsheet, rows[0], filtered=True)
        self.dat.mainWin.refresh()  # pylint: disable=no-member

    def refreshContents(self):
        if self.results is None:
            self.results = self.dat.flowsheet.results
        else:
            if self.results.empty:
                self.results = self.dat.flowsheet.results

        self.updateFilterBox()
        self.tableView.setModel(dataModel(self.results, self))
        self.numRowsBox.setText(str(self.results.count_rows(filtered=True)))

    def autoResizeCols(self):
        # if you resize the columns before showing Qt seems to
        # calculate the width of all the cells in the table
        # if you do it after showing Qt only uses the visible cells
        # so it a lot faster.  This arrangement is much better
        # if the table has a lot of rows there could be a few second
        # delay.
        self.tableView.resizeColumnsToContents()

    def deleteResults(self):
        """Delete selected rows from the results table."""
        if self.results is None:
            self.results = self.dat.flowsheet.results
        else:
            if self.results.empty:
                self.results = self.dat.flowsheet.results

        msgBox = QMessageBox()
        msgBox.setText("Delete selected data?")
        msgBox.setInformativeText(
            "If you select yes, the selected rows will be deleted. "
        )
        msgBox.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        msgBox.setDefaultButton(QMessageBox.No)
        ret = msgBox.exec_()
        if ret == QMessageBox.Yes:
            rows = self.selectedRows()
            self.results.delete_rows(rows, filtered=True)
            self.refreshContents()

    def editDataSet(self):
        if self.results is None:
            self.results = self.dat.flowsheet.results
        else:
            if self.results.empty:
                self.results = self.dat.flowsheet.results

        rl = self.results
        rows = self.selectedRows()
        name, ok = QInputDialog.getText(
            self, "Set Name", "Enter new set name:", QLineEdit.Normal
        )
        if ok and name != "":
            rl.edit_set_name(name, rows, filtered=True)

    def importCSV(self):
        if self.results is None:
            self.results = self.dat.flowsheet.results
        else:
            if self.results.empty:
                self.results = self.dat.flowsheet.results

        fileName, filtr = QFileDialog.getOpenFileName(
            self,
            "Import CSV Result File",
            "",
            "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)",
        )
        if fileName:
            self.results.read_csv(fileName)
            self.refreshContents()

    def addEmptyResult(self):
        if self.results is None:
            self.results = self.dat.flowsheet.results
        else:
            if self.results.empty:
                self.results = self.dat.flowsheet.results

        self.results.add_result(
            sd=self.dat.flowsheet.saveValues(), result_name="empty", empty=True
        )
        self.refreshContents()

    def selectedRows(self):
        rows = set()
        for i in self.tableView.selectedIndexes():
            rows.add(i.row())
        return list(rows)

    def hideCols(self):
        cols = set()
        for i in self.tableView.selectedIndexes():
            cols.add(i.column())
        for col in cols:
            self.tableView.hideColumn(col)

    def unhideCols(self):
        for col in range(self.tableView.model().columnCount()):
            self.tableView.setColumnHidden(col, False)

    def clearResults(self):
        if self.results is None:
            self.results = self.dat.flowsheet.results
        else:
            if self.results.empty:
                self.results = self.dat.flowsheet.results

        msgBox = QMessageBox()
        msgBox.setText("Delete all data?")
        msgBox.setInformativeText(
            (
                "If you select yes, all flowsheet result data in this "
                "session will be deleted. "
            )
        )
        msgBox.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        msgBox.setDefaultButton(QMessageBox.No)
        ret = msgBox.exec_()
        if ret == QMessageBox.Yes:
            self.results.clearData()
            self.refreshContents()

    def editFilters(self):
        if self.results is None:
            self.results = self.dat.flowsheet.results
        else:
            if self.results.empty:
                self.results = self.dat.flowsheet.results

        df = dataFilterDialog.dataFilterDialog(self.dat, self, results=self.results)
        df.exec_()
        self.updateFilterBox()
        self.selectFilter()

    def updateFilterBox(self):
        if self.results is None:
            self.results = self.dat.flowsheet.results
        else:
            if self.results.empty:
                self.results = self.dat.flowsheet.results

        self.filterSelectBox.blockSignals(True)
        self.filterSelectBox.clear()
        items = [""] + sorted(self.results.filters.keys())
        self.filterSelectBox.addItems(items)
        i = -1
        if self.results.current_filter() != None:
            i = self.filterSelectBox.findText(self.results.current_filter())
        if i != -1:
            self.filterSelectBox.setCurrentIndex(i)
        else:
            self.filterSelectBox.setCurrentIndex(-1)
        self.filterSelectBox.blockSignals(False)

    def selectFilter(self, i=0):
        if self.results is None:
            self.results = self.dat.flowsheet.results
        else:
            if self.results.empty:
                self.results = self.dat.flowsheet.results

        filterName = self.filterSelectBox.currentText()
        if filterName == "":
            self.results.set_filter(None)
        elif not filterName in self.results.filters:
            print("error")
        else:
            self.results.set_filter(filterName)
        self.tableView.setModel(dataModel(self.results, self))
        self.numRowsBox.setText(str(self.results.count_rows(filtered=True)))

    def saveResultsToCSV(self):
        if self.results is None:
            self.results = self.dat.flowsheet.results
        else:
            if self.results.empty:
                self.results = self.dat.flowsheet.results

        fileName, filtr = QFileDialog.getSaveFileName(
            self,
            "Save CSV Result File",
            "",
            "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)",
        )
        if fileName:
            self.results.to_csv(fileName)

    def toPsuade(self):
        if self.results is None:
            self.results = self.dat.flowsheet.results
        else:
            if self.results.empty:
                self.results = self.dat.flowsheet.results

        fileName, filtr = QFileDialog.getSaveFileName(
            self,
            "Save CSV Result File",
            "",
            "PSUADE Files (*.dat);;Text Files (*.txt);;All Files (*)",
        )
        if fileName:
            self.results.to_psuade(fileName)

    def toClipboard(self):
        if self.results is None:
            self.results = self.dat.flowsheet.results
        else:
            if self.results.empty:
                self.results = self.dat.flowsheet.results

        clipboard = QApplication.clipboard()
        clipboard.setText(self.results.to_csv(sep="\t"))

    def importClip(self):
        if self.results is None:
            self.results = self.dat.flowsheet.results
        else:
            if self.results.empty:
                self.results = self.dat.flowsheet.results

        clipboard = QApplication.clipboard()
        s = str(clipboard.text())
        self.results.read_csv(s=s, sep="\t")
        self.refreshContents()
