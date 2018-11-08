"""dataFilterDialog.py

* This contains the workings of the dialog to create filters for result data

John Eslick, Carnegie Mellon University, 2014
See LICENSE.md for license and copyright details.
"""

import json
import logging
import os

from foqus_lib.framework.sampleResults.results import *
import foqus_lib.gui.helpers.guiHelpers as gh

from PyQt5 import uic
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplitter, QInputDialog,\
    QLineEdit
mypath = os.path.dirname(__file__)
_dataFilterDialogUI, _dataFilterDialog = \
        uic.loadUiType(os.path.join(mypath, "dataFilterDialog_UI.ui"))


class dataFilterDialog(_dataFilterDialog, _dataFilterDialogUI):
    def __init__(self, dat, parent=None, results = None):
        '''
            Constructor for data filter dialog
        '''
        super(dataFilterDialog, self).__init__(parent=parent)
        self.setupUi(self) # Create the widgets
        self.dat = dat     # all of the session data
        if results is None:
            self.results = self.dat.flowsheet.results
        else:
            self.results = results

        self.newFilterButton.clicked.connect(self.addFilter)
        self.deleteFilterButton.clicked.connect(self.delFilter)
        self.addOpButton.clicked.connect(self.addOp)
        self.addRuleButton.clicked.connect(self.addRule)
        self.doneButton.clicked.connect(self.doneClicked)
        #self.copyButton.clicked.connect(self.copyCol)
        self.colList.itemDoubleClicked.connect(self.copyCol2)
        self.muButton.clicked.connect(self.moveUp)
        self.mdButton.clicked.connect(self.moveDown)
        self.sortCheck.clicked.connect(self.enableSortTerm)
        self.deleteButton.clicked.connect(self.deleteRows)
        self.selectFilterBox.currentIndexChanged.connect(
            self.selectFilter)
        self.copList = ["NOT", "AND", "OR", "XOR"]
        self.ropList = ["=", "!=", "<", ">", "<=", ">=", "IN", "APPROX"]
        self.ropDict = {
            "=":dataFilterRule.OP_EQ,
            "!=":dataFilterRule.OP_NEQ,
            "<":dataFilterRule.OP_L,
            ">":dataFilterRule.OP_G,
            "<=":dataFilterRule.OP_LE,
            ">=":dataFilterRule.OP_GE,
            "IN":dataFilterRule.OP_IN,
            "APPROX":dataFilterRule.OP_AEQ}
        self.copDict = {
            "NOT":dataFilter.DF_NOT,
            "AND":dataFilter.DF_AND,
            "OR":dataFilter.DF_OR,
            "XOR":dataFilter.DF_XOR}
        self.ropDictRev = {}
        for key, item in self.ropDict.items():
            self.ropDictRev[item] = key
        self.copDictRev = {}
        for key, item in self.copDict.items():
            self.copDictRev[item] = key
        self.updateFilterBox()
        self.updateForm()
        self.prevFilter = None
        self.split = QSplitter(self.splitFrame)
        self.split.addWidget(self.ruleTable)
        self.split.addWidget(self.TreeFrame)
        self.splitFrame.layout().addWidget(self.split)
        self.splitFrame.layout().activate()
        headings = self.results.columns
        self.colList.addItems(headings)

    def copyCol(self):
        self.copyCol2(self.colList.currentItem())

    def copyCol2(self, ci=None):
        clipboard = QApplication.clipboard()
        if ci is not None:
            clipboard.setText(ci.text())

    def enableSortTerm(self):
        if self.sortCheck.isChecked():
            self.sortTermEdit.setEnabled(True)
        else:
            self.sortTermEdit.setEnabled(False)

    def selectedRows(self):
        items = self.ruleTable.selectedItems()
        rows = set()
        for item in items:
            rows.add(item.row())
        return rows

    def rowSwap(self, row1, row2):
        table = self.ruleTable
        row1Items = [
            table.takeItem(row1, 0),
            table.cellWidget(row1, 1),
            table.takeItem(row1, 2)]
        row2Items = [
            table.takeItem(row2, 0),
            table.cellWidget(row2, 1),
            table.takeItem(row2, 2)]
        table.setItem(row1, 0, row2Items[0])
        table.setItem(row2, 0, row1Items[0])
        table.setItem(row1, 2, row2Items[2])
        table.setItem(row2, 2, row1Items[2])
        r1ct = row1Items[1].currentText()
        r2ct = row2Items[1].currentText()
        r1it = [row1Items[1].itemText(i) \
            for i in range(row1Items[1].count())]
        r2it = [row2Items[1].itemText(i) \
            for i in range(row2Items[1].count())]
        #assigning new widgets will delete old
        gh.setTableItem(table, row1, 1, r2ct, pullDown=r2it)
        gh.setTableItem(table, row2, 1, r1ct, pullDown=r1it)

    def moveUp(self):
        rows = self.selectedRows()
        if len(rows) == 0:
            return
        row = sorted(rows)[0]
        if row == 0:
            row2 = self.ruleTable.rowCount() - 1
        else:
            row2 = row-1
        self.rowSwap(row, row2)
        self.ruleTable.clearSelection()
        self.ruleTable.selectRow(row2)

    def moveDown(self):
        rows = self.selectedRows()
        if len(rows) == 0:
            return
        row = sorted(rows)[0]
        if row == self.ruleTable.rowCount() - 1:
            row2 = 0
        else:
            row2 = row+1
        self.rowSwap(row, row2)
        self.ruleTable.clearSelection()
        self.ruleTable.selectRow(row2)

    def deleteRows(self):
        rows = list(self.selectedRows())
        rows = reversed(sorted(rows))
        self.ruleTable.clearSelection()
        for row in rows:
            self.ruleTable.removeRow(row)

    def addOp(self, op=None):
        r = self.results
        if op is not None:
            op = self.copDictRev[op]
        else:
            op="AND"
        table = self.ruleTable
        row = table.rowCount()
        table.setRowCount(row + 1)
        bg = QColor(200, 200, 200)
        gh.setTableItem(table, row, 0, "", bgColor=bg, editable=False)
        gh.setTableItem(table, row, 2, "", bgColor=bg, editable=False)
        gh.setTableItem(table, row, 1, op, pullDown=self.copList)

    def addRule(self, rule=None):
        r = self.results
        if rule:
            term1 = json.dumps(rule.term1)
            term2 = json.dumps(rule.term2)
            op = self.ropDictRev[rule.op]
        else:
            term1 = "err"
            term2 = "0"
            op = "="
        table = self.ruleTable
        row = table.rowCount()
        table.setRowCount(row + 1)
        gh.setTableItem(table, row, 0, term1, editable=True)
        gh.setTableItem(table, row, 2, term2, editable=True)
        gh.setTableItem(table, row, 1, op, pullDown=self.ropList)

    def doneClicked(self):
        self.applyChanges()
        self.done(0)

    def delFilter(self):
        fname = self.selectFilterBox.currentText()
        if fname in self.results.filters:
            del self.results.filters[fname]
        if self.results.current_filter() == fname:
            self.results.set_filter(None)
        self.updateFilterBox( )
        self.updateForm()

    def selectFilter(self, i=None):
        self.applyChanges(True)
        self.prevFilter = self.selectFilterBox.currentText()
        self.updateForm()

    def addFilter(self):
        '''
            Add a new filter to the results
        '''
        # Get the name
        newName, ok = QInputDialog.getText(
            self,
            "Filter Name",
            "New filter name:",
            QLineEdit.Normal)
        # if name supplied and not canceled
        if ok and newName != '':
            # check if the name is in use
            if newName in self.results.filters:
                # filter already exists
                # just do nothing for now
                QMessageBox.information(
                    self, "Error", "The filter name already exists.")
            else:
                self.applyChanges(True)
                self.results.filters[newName] = \
                    dataFilter()
        self.updateFilterBox(newName)
        self.ruleTable.setRowCount(0)

    def updateFilterBox(self, fltr = None):
        '''
            Update the list of filters in the combo box
        '''
        if fltr == None:
            fltr = self.results.current_filter()
        self.selectFilterBox.blockSignals(True)
        self.selectFilterBox.clear()
        items = sorted(self.results.filters.keys())
        self.selectFilterBox.addItems(items)
        i = self.selectFilterBox.findText(fltr)
        if i > 0:
            self.selectFilterBox.setCurrentIndex(i)
        self.selectFilterBox.blockSignals(False)
        self.prevFilter = self.selectFilterBox.currentText()

    def updateForm(self):
        self.ruleTable.setRowCount(0)
        fltrName = self.selectFilterBox.currentText()
        if fltrName == None or fltrName == "":
            return
        r = self.results
        f = r.filters[fltrName]
        self.sortCheck.setChecked(f.sortTerm != None)
        if f.sortTerm:
            self.sortTermEdit.setText(str(f.sortTerm))
        self.enableSortTerm()
        for item in f.fstack:
            if item[0] < f.DF_END_OP:
                self.addOp(item[0])
            elif item[0] == f.DF_RULE:
                self.addRule(item[1])
            else:
                raise Exception("unknown filter item")

    def applyChanges(self, usePrev = False):
        if usePrev:
            fltrName = self.prevFilter
        else:
            fltrName = self.selectFilterBox.currentText()
        if fltrName == None or fltrName == "":
            return
        r = self.results
        r.filters[fltrName] = dataFilter()
        fltr = r.filters[fltrName]
        if self.sortCheck.isChecked():
            fltr.sortTerm = self.sortTermEdit.text()
        else:
            fltr.sortTerm = None
        table = self.ruleTable
        for row in range(table.rowCount()):
            term1 = gh.getCellText(table, row, 0)
            term2 = gh.getCellText(table, row, 2)
            op = gh.getCellText(table, row, 1)
            if term1 == "" and term2 == "" and op in self.copList:
                # operator that operates on rules.
                op = self.copDict[op]
                fltr.fstack.append([op])
            elif term1 != "" and term2 != "" and op in self.ropList:
                # rule
                rule = dataFilterRule()
                try:
                    rule.term1 = json.loads(term1)
                except ValueError:
                    rule.term1 = term1
                try:
                    rule.term2 = json.loads(term2)
                except ValueError:
                    rule.term2 = term2
                rule.op = self.ropDict[op]
                fltr.fstack.append([dataFilter.DF_RULE, rule])
            else:
                #something wrong
                print("message box here")
                return 1
        return 0
