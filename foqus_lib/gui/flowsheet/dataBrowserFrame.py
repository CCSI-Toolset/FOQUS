'''
    dataBrowserFrame.py

    * Displays tabulated flowsheet data

    John Eslick, Carnegie Mellon University, 2014

    This Material was produced under the DOE Carbon Capture Simulation
    Initiative (CCSI), and copyright is held by the software owners:
    ORISE, LANS, LLNS, LBL, PNNL, CMU, WVU, et al. The software owners
    and/or the U.S. Government retain ownership of all rights in the
    CCSI software and the copyright and patents subsisting therein. Any
    distribution or dissemination is governed under the terms and
    conditions of the CCSI Test and Evaluation License, CCSI Master
    Non-Disclosure Agreement, and the CCSI Intellectual Property
    Management Plan. No rights are granted except as expressly recited
    in one of the aforementioned agreements.
'''

#from PySide import QtGui, QtCore
#from foqus_lib.gui.flowsheet.dataBrowserFrame_UI import *
from foqus_lib.gui.flowsheet.columns import *
import dataFilterDialog
from foqus_lib.gui.flowsheet.dataModel import *
import json
from foqus_lib.gui.flowsheet.runRowsDialog import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMessageBox
import os
from PyQt5 import uic
mypath = os.path.dirname(__file__)
_dataBrowserFrameUI, _dataBrowserFrame = \
        uic.loadUiType(os.path.join(mypath, "dataBrowserFrame_UI.ui"))
#super(, self).__init__(parent=parent)


class dataBrowserFrame(_dataBrowserFrame, _dataBrowserFrameUI):
    def __init__(self, dat, parent):
        super(dataBrowserFrame, self).__init__(parent=parent)
        self.setupUi(self)
        self.dat = dat  # session data
        self.menu = QtWidgets.QMenu()
        self.impMenu = self.menu.addMenu("Import")
        self.expMenu = self.menu.addMenu("Export")
        self.editMenu = self.menu.addMenu("Edit")
        self.viewMenu = self.menu.addMenu("View")
        self.runMenu = self.menu.addMenu("Run")
        self.addMenuActions()
        self.menuButton.setMenu(self.menu)
        self.editFiltersButton.clicked.connect(self.editFilters)
        self.filterSelectBox.currentIndexChanged.connect(
            self.selectFilter)
        self.tableView.setAlternatingRowColors(True)
        self.columnsButton.clicked.connect(self.columnSelect)

    def columnSelect(self):
        cd = columnsDialog(self.dat, self)
        cd.show()

    def addMenuActions(self):
        # export csv
        self.exportCsvAct = QtWidgets.QAction(
            'Export to CSV File...',
            self)
        self.exportCsvAct.triggered.connect(self.saveResultsToCSV)
        self.expMenu.addAction(self.exportCsvAct)
        # copy to clipboard
        self.toClipAct = QtWidgets.QAction(
            'Copy Data to Clipboard',
            self)
        self.toClipAct.triggered.connect(self.toClipboard)
        self.expMenu.addAction(self.toClipAct)
        # Export PSUADE sample file
        self.toPsuadeAct = QtWidgets.QAction(
            'Export to PSUADE File...',
            self)
        self.toPsuadeAct.triggered.connect(self.toPsuade)
        self.expMenu.addAction(self.toPsuadeAct)
        # import from csv
        self.importCsvAct = QtWidgets.QAction(
            'Import from CSV file...',
            self)
        self.importCsvAct.triggered.connect(self.importCSV)
        self.impMenu.addAction(self.importCsvAct)
        # paste from clipboard
        self.fromClipAct = QtWidgets.QAction(
            'Paste Data from Clipboard',
            self)
        self.fromClipAct.triggered.connect(self.importClip)
        self.impMenu.addAction(self.fromClipAct)
        # copy selected row to flowsheet.
        self.getRowAct = QtWidgets.QAction(
            'Row to Flowsheet',
            self)
        self.getRowAct.triggered.connect(self.rowToFlow)
        self.editMenu.addAction(self.getRowAct)
        # clear data
        self.clearDataAct = QtWidgets.QAction(
            'Clear All Data',
            self)
        self.clearDataAct.triggered.connect(self.clearResults)
        self.editMenu.addAction(self.clearDataAct)
        #
        self.deleteDataAct = QtWidgets.QAction(
            'Delete Rows',
            self)
        self.deleteDataAct.triggered.connect(self.deleteResults)
        self.editMenu.addAction(self.deleteDataAct)
        # Add blank result
        self.addResultAct = QtWidgets.QAction(
            'Add Empty Result',
            self)
        self.addResultAct.triggered.connect(self.addEmptyResult)
        self.editMenu.addAction(self.addResultAct)
        # edit Set
        self.editSetAct = QtWidgets.QAction(
            'Edit Set for Selected Rows',
            self)
        self.editSetAct.triggered.connect(self.editDataSet)
        self.editMenu.addAction(self.editSetAct)
        # add tags
        self.addTagsAct = QtWidgets.QAction(
            'Add Tags to Selected Rows', self)
        self.addTagsAct.triggered.connect(self.addDataTags)
        self.editMenu.addAction(self.addTagsAct)
        # edit tags
        self.editTagsAct = QtWidgets.QAction(
            'Edit Tags for Selected Rows',
            self)
        self.editTagsAct.triggered.connect(self.editDataTags)
        self.editMenu.addAction(self.editTagsAct)
        # hide columns
        self.hideDataColsAct = QtWidgets.QAction(
            'Hide Selected Columns',
            self)
        self.hideDataColsAct.triggered.connect(self.hideCols)
        self.viewMenu.addAction(self.hideDataColsAct)
        # un-hide columns
        self.unhideDataColsAct = QtWidgets.QAction(
            'Show All Columns',
            self)
        self.unhideDataColsAct.triggered.connect(self.unhideCols)
        self.viewMenu.addAction(self.unhideDataColsAct)
        # resize columns
        self.resizeColumnsAct = QtWidgets.QAction(
            'Resize Columns',
            self)
        self.resizeColumnsAct.triggered.connect(self.autoResizeCols)
        self.viewMenu.addAction(self.resizeColumnsAct)
        self.flattenAct = QtWidgets.QAction(
            'Flatten Table',
            self)
        self.flattenAct.setCheckable(True)
        self.flattenAct.triggered.connect(self.flattenTable)
        self.viewMenu.addAction(self.flattenAct)
        #Run menu
        self.runRowsAct = QtWidgets.QAction('Run Selected Rows', self)
        self.runRowsAct.triggered.connect(self.runSelectedRows)
        self.runMenu.addAction(self.runRowsAct)

    def rowToFlow(self):
        rows = self.selectedRows()
        if len(rows) < 1:
            return
        self.dat.flowsheet.results.rowToFlowsheet(
            rows[0], self.dat.flowsheet, fltr=True)
        self.dat.mainWin.refresh()

    def runSelectedRows(self):
        rows = self.selectedRows()
        n = len(rows)
        if n < 1:
            return
        elif n == 1:
            s = ""
        else:
            s = "s"
        msgBox = QtWidgets.QMessageBox()
        msgBox.setText("Do you want to run {} sample{}?".format(n, s))
        msgBox.setStandardButtons(
            QtWidgets.QMessageBox.No |
            QtWidgets.QMessageBox.Yes)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
        ret = msgBox.exec_()
        if ret == QtWidgets.QMessageBox.No: return
        if self.dat.foqusSettings.runFlowsheetMethod == 1:
            useTurbine=True
        else:
            useTurbine=False
        rows, valList = self.dat.flowsheet.results.runSet(rows)
        self.dat.mainWin.runSim(rows=rows, valList=valList)

    def refreshContents(self):
        self.tableView.setModel(
            dataModel(self.dat.flowsheet.results, self))
        self.updateFilterBox()
        self.flattenAct.setChecked(self.dat.flowsheet.results.flatTable)
        self.numRowsBox.setText(str(
            self.dat.flowsheet.results.rowCount(filtered=True)))

    def flattenTable(self):
        if self.flattenAct.isChecked():
            self.dat.flowsheet.results.setFlatTable(True)
        else:
            self.dat.flowsheet.results.setFlatTable(False)
        self.refreshContents()

    def autoResizeCols(self):
        # if you resize the columns before showing Qt seems to
        # calculate the width of all the cells in the table
        # if you do it after showing Qt only uses the visible cells
        # so it a lot faster.  This arrangement is much better
        # if the table has a lot of rows there could be a few second
        # delay.
        self.tableView.resizeColumnsToContents()

    def deleteResults(self):
        '''
            Delete selected rows from the results table.
        '''
        msgBox = QtWidgets.QMessageBox()
        msgBox.setText("Delete selected data?")
        msgBox.setInformativeText(
            "If you select yes, the selected rows will be deleted. ")
        msgBox.setStandardButtons(
            QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
        ret = msgBox.exec_()
        if ret == QtWidgets.QMessageBox.Yes:
            rows = self.selectedRows()
            rl = self.dat.flowsheet.results
            rl.deleteRows(rows, fltr=True)
            self.refreshContents()

    def editDataTags(self):
        '''

        '''
        rl = self.dat.flowsheet.results
        rows = self.selectedRows()
        name, ok = QtWidgets.QInputDialog.getText(
            self,
            "Change Row Tags",
            'Enter new tags (e.g. ["Tag1", "Tag2"]):',
            QtWidgets.QLineEdit.Normal)
        if ok and name != '':
            tags = json.loads(name)
            if isinstance(tags, basestring):
                tags = [tags]
            for row in rows:
                rl.setTags(tags, row, add=False, fltr=True)

    def addDataTags(self):
        '''

        '''
        rl = self.dat.flowsheet.results
        rows = self.selectedRows()
        name, ok = QtWidgets.QInputDialog.getText(
            self,
            "Add Row Tags",
            'Enter tags to add (e.g. ["Tag1", "Tag2"]):',
            QtWidgets.QLineEdit.Normal)
        if ok and name != '':
            tags = json.loads(name)
            if isinstance(tags, basestring):
                tags = [tags]
            for row in rows:
                rl.setTags(tags, row, add=True, fltr=True)

    def editDataSet(self):
        rl = self.dat.flowsheet.results
        rows = self.selectedRows()
        name, ok = QtWidgets.QInputDialog.getText(
            self,
            "Set Name",
            'Enter new set name:',
            QtWidgets.QLineEdit.Normal)
        if ok and name != '':
            for row in rows:
                rl.setSetName(name, row, fltr=True)

    def importCSV(self):
        fileName, filtr = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Import CSV Result File",
            "",
            "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)")
        if fileName:
            self.dat.flowsheet.results.importCSV(fileName)
            self.refreshContents()

    def addEmptyResult(self):
        self.dat.flowsheet.results.addResult( )
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
        msgBox = QtWidgets.QMessageBox()
        msgBox.setText("Delete all data?")
        msgBox.setInformativeText(
            ("If you select yes, all flowsheet result data in this "
             "session will be deleted. "))
        msgBox.setStandardButtons(
            QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
        ret = msgBox.exec_()
        if ret == QtWidgets.QMessageBox.Yes:
            self.dat.flowsheet.results.clearData()
            self.refreshContents()

    def editFilters(self):
        df = dataFilterDialog.dataFilterDialog(self.dat, self)
        df.exec_()
        self.updateFilterBox()
        self.selectFilter()

    def updateFilterBox(self):
        self.filterSelectBox.blockSignals(True)
        self.filterSelectBox.clear()
        items = [''] + sorted(self.dat.flowsheet.results.filters.keys())
        self.filterSelectBox.addItems(items)
        i=-1
        if self.dat.flowsheet.results.currentFilter() != None:
            i = self.filterSelectBox.findText(
                self.dat.flowsheet.results.currentFilter())
        if i != -1:
            self.filterSelectBox.setCurrentIndex(i)
        else:
            self.filterSelectBox.setCurrentIndex(-1)
        self.filterSelectBox.blockSignals(False)

    def selectFilter(self, i = 0):
        filterName = self.filterSelectBox.currentText()
        if filterName == '':
            self.dat.flowsheet.results.setFilter(None)
        elif not filterName in self.dat.flowsheet.results.filters:
            print "error"
        else:
            self.dat.flowsheet.results.setFilter(filterName)
        self.tableView.setModel(
            dataModel(self.dat.flowsheet.results, self))
        self.numRowsBox.setText(str(
            self.dat.flowsheet.results.rowCount(filtered=True)))

    def saveResultsToCSV(self):
        fileName, filtr = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save CSV Result File",
            "",
            "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)")
        if fileName:
            self.dat.flowsheet.results.dumpCSV(fileName)

    def toPsuade(self):
        fileName, filtr = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save CSV Result File",
            "",
            "PSUADE Files (*.dat);;Text Files (*.txt);;All Files (*)")
        if fileName:
            self.dat.flowsheet.results.exportPSUADE(fileName)

    def toClipboard(self):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self.dat.flowsheet.results.dumpString())

    def importClip(self):
        clipboard = QtWidgets.QApplication.clipboard()
        s = str(clipboard.text())
        self.dat.flowsheet.results.importCSVString(s)
        self.refreshContents()
