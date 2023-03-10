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
"""dataFilterDialog.py

* This contains the workings of the dialog to create filters for result data

John Eslick, Carnegie Mellon University, 2014
"""

import json
import logging
import os

_log = logging.getLogger("foqus.{}".format(__name__))

from foqus_lib.framework.sampleResults.results import *
import foqus_lib.gui.helpers.guiHelpers as gh
from foqus_lib.gui.flowsheet.calculatedColumns import calculatedColumnsDialog

from PyQt5 import uic
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QObject, QEvent, QDataStream, QSize, Qt
from PyQt5.QtWidgets import (
    QApplication,
    QMessageBox,
    QSplitter,
    QInputDialog,
    QLineEdit,
    QAbstractItemView,
)

mypath = os.path.dirname(__file__)
_dataFilterDialogUI, _dataFilterDialog = uic.loadUiType(
    os.path.join(mypath, "dataFilterDialog_UI.ui")
)


def _list_item_mime_to_text(mime_data, c=False):
    if mime_data.hasText():
        return mime_data
    data = mime_data.data("application/x-qabstractitemmodeldatalist")
    if not data:
        return mime_data
    ds = QDataStream(data)
    ds.readInt32()  # read row (don't need)
    ds.readInt32()  # read col (don't need)
    value = None
    for i in range(ds.readInt32()):
        if Qt.ItemDataRole(ds.readInt32()) == Qt.DisplayRole:
            value = ds.readQVariant()
            break
    if value is None:
        return mime_data
    if c:
        value = 'c("{}")'.format(value)
    else:
        value = '"{}"'.format(value)
    mime_data.setText(value)
    return mime_data


class _DropHandler(QObject):
    def __init__(self, parent=None, c=False):
        super(_DropHandler, self).__init__(parent=parent)
        self.c = c

    def eventFilter(self, obj, event):
        if event.type() == QEvent.DragEnter:
            event.accept()
        elif event.type() == QEvent.Drop:
            try:
                _list_item_mime_to_text(event.mimeData(), self.c)
            except:
                _log.exception("Drop could not convert mime type to text")
                event.ignore()
            event.accept()
        else:
            event.accept()

        return QObject.eventFilter(self, obj, event)


class dataFilterDialog(_dataFilterDialog, _dataFilterDialogUI):
    def __init__(self, dat, parent=None, results=None):
        """
        Constructor for data filter dialog
        """
        super(dataFilterDialog, self).__init__(parent=parent)
        self.setupUi(self)  # Create the widgets
        self.dat = dat  # all of the session data
        if results is None:
            self.results = self.dat.flowsheet.results
        else:
            self.results = results

        self.selectFilterBox.currentIndexChanged.connect(self.selectFilter)
        self.newFilterButton.clicked.connect(self.addFilter)
        self.deleteFilterButton.clicked.connect(self.delFilter)
        self.doneButton.clicked.connect(self.doneClicked)
        self.addCalcButton.clicked.connect(self.showCalcEdit)
        self.prevFilter = None
        # Set up column list widget for help selecting fileter and sort terms
        self.updateColList()
        self.colList.itemDoubleClicked.connect(self.copyCol2)
        self.colList.setDragDropMode(QAbstractItemView.DragOnly)
        # When draging into sort and filter text boxes add text to mimedata
        self.filterTermEdit.installEventFilter(_DropHandler(self, True))
        self.sortTermEdit.installEventFilter(_DropHandler(self, False))
        # Initially populate the dialog
        self.updateFilterBox()
        self.updateForm()

    def updateColList(self):
        self.colList.clear()
        self.colList.addItems(self.results.columns)

    def showCalcEdit(self):
        calculatedColumnsDialog(self.dat, parent=self).exec_()
        self.results.calculate_columns()
        self.updateColList()

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
        self.updateFilterBox()
        self.updateForm()

    def selectFilter(self, i=None):
        self.applyChanges(True)
        self.prevFilter = self.selectFilterBox.currentText()
        self.updateForm()

    def addFilter(self):
        """
        Add a new filter to the results
        """
        # Get the name
        newName, ok = QInputDialog.getText(
            self, "Filter Name", "New filter name:", QLineEdit.Normal
        )
        msgBox = QMessageBox(self)
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setWindowTitle("Data Filter Instructions")
        msgBox.setText(
            """Within Filter Expression, the filter can be applied in Python format to each column of the Flowsheet Results table.
        Single Filter Criteria Syntax: c(“column name”) ==,!=,<= or >= “ string_value” or numeric_value
        String value can be a simulation set or result name, or time.
        Numeric values are for simulation graph error, input and output variable values.
        Multiple Filter Criteria Syntax: NumPy Logical Operators.
        For 2 conditions: np.logical_and(condition_1, condition_2), np.logical_or(condition_1, condition_2)
        For more than 2 conditions: np.logical_and.reduce((condition_1, condition_2…)), np.logical_or.reduce((condition_1, condition_2…))
        Each ‘condition’ has the same syntax as that for single filter criteria"""
        )
        #        msgBox.setInformativeText(text)
        msgBox.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        msgBox.setDefaultButton(QMessageBox.Ok)
        msgBox.setFixedSize(500, 500)
        #        msgBox.resize(800, 200)
        msgBox.exec()
        #        QMessageBox.setBaseSize(QSize(550, 275))
        #        QMessageBox.information(
        #                    self, "Data Filter Instructions", """Within Filter Expression, the filter can be applied in Python format to each column of the Flowsheet Results table.
        #                    Single Filter Criteria Syntax: c(“column name”) ==,!=,<= or >= “ string_value” or numeric_value
        #                    String value can be a simulation set or result name, or time.
        #                    Numeric values are for simulation graph error, input and output variable values.
        #                    Multiple Filter Criteria Syntax: NumPy Logical Operators.
        #                    For 2 conditions: np.logical_and(condition_1, condition_2), np.logical_or(condition_1, condition_2)
        #                    For more than 2 conditions: np.logical_and.reduce((condition_1, condition_2…)), np.logical_or.reduce((condition_1, condition_2…))
        #                    Each ‘condition’ has the same syntax as that for single filter criteria""")
        #        QMessageBox.setBaseSize(QSize(550, 275))
        # if name supplied and not canceled
        if ok and newName != "":
            # check if the name is in use
            if newName in self.results.filters:
                # filter already exists
                # just do nothing for now
                QMessageBox.information(
                    self, "Error", "The filter name already exists."
                )
            else:
                self.applyChanges(True)
                self.results.filters[newName] = dataFilter()
        self.updateFilterBox(newName)

    def updateFilterBox(self, fltr=None):
        """
        Update the list of filters in the combo box
        """
        if fltr == None:
            fltr = self.results.current_filter()
        self.selectFilterBox.blockSignals(True)
        self.selectFilterBox.clear()
        items = list(sorted(self.results.filters.keys()))
        self.selectFilterBox.addItems([i for i in items if i not in ["all", "none"]])
        i = self.selectFilterBox.findText(fltr)
        if i > 0:
            self.selectFilterBox.setCurrentIndex(i)
        self.selectFilterBox.blockSignals(False)
        self.prevFilter = self.selectFilterBox.currentText()

    def updateForm(self):
        fltrName = self.selectFilterBox.currentText()
        if not fltrName:
            return
        fltr = self.results.filters[fltrName]
        self.sortTermEdit.setText(fltr.sortTerm)
        self.filterTermEdit.setText(fltr.filterTerm)

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
        return 0
