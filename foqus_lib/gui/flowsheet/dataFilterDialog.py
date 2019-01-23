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
        self.colList.itemDoubleClicked.connect(self.copyCol2)
        self.newFilterButton.clicked.connect(self.addFilter)
        self.deleteFilterButton.clicked.connect(self.delFilter)
        self.doneButton.clicked.connect(self.doneClicked)
        self.updateFilterBox()
        self.updateForm()
        self.prevFilter = None
        headings = self.results.columns
        self.colList.addItems(headings)

    def copyCol(self):
        self.copyCol2(self.colList.currentItem())

    def copyCol2(self, ci=None):
        clipboard = QApplication.clipboard()
        if ci is not None:
            clipboard.setText('"{}"'.format(ci.text()))

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

    def updateFilterBox(self, fltr=None):
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
        fltrName = self.selectFilterBox.currentText()
        fltr = self.results.filters[fltrName]
        self.sortTermEdit.setText(fltr.sortTerm)
        self.filterTermEdit.setText(fltr.filterTerm)
        self.noResultsCheckBox.setChecked(fltr.no_results)

    def applyChanges(self, usePrev=False):
        if usePrev:
            fltrName = self.prevFilter
        else:
            fltrName = self.selectFilterBox.currentText()
        if fltrName == None or fltrName == "":
            return
        r = self.results
        r.filters[fltrName] = dataFilter()
        fltr = r.filters[fltrName]
        fltr.sortTerm = self.sortTermEdit.text()
        fltr.filterTerm = self.filterTermEdit.text()
        fltr.no_results = self.noResultsCheckBox.isChecked()
        return 0
