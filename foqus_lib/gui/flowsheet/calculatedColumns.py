"""dataBrowserDialog.py

* Window to show the flowsheet data browser.

John Eslick, Carnegie Mellon University, 2014
See LICENSE.md for license and copyright details.
"""
import os

from PyQt5 import uic
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtCore import pyqtSlot
mypath = os.path.dirname(__file__)
_calculatedColumnsUI, _calculatedColumns = \
        uic.loadUiType(os.path.join(mypath, "calculatedColumns_UI.ui"))


class calculatedColumnsDialog(_calculatedColumnsUI, _calculatedColumns):
    def __init__(self, dat, parent=None):
        super(calculatedColumnsDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.dat = dat
        cols = self.dat.flowsheet.results.columns
        self.colListWidget.addItems(cols)
        self.comboBox.addItems(
            list(self.dat.flowsheet.results.calculated_columns.keys()))
        self.newButton.clicked.connect(self.add_dialog)
        self.delButton.clicked.connect(self.del_current)
        self.doneButton.clicked.connect(self.close)
        self.comboBox.currentIndexChanged.connect(self.select_calc)
        self.colListWidget.itemClicked.connect(self.click_column)
        self._current = self.comboBox.currentText()
        if len(self._current) < 1:
            self._current = None
        self.refreshContents()

    def closeEvent(self, event):
        self.apply_changes()
        event.accept()

    def del_current(self):
        self.dat.flowsheet.results.delete_calculation(self._current)
        self._current = None
        self.comboBox.removeItem(self.comboBox.currentIndex())

    def click_column(self, item):
        self.expressionEdit.insertPlainText('c("{}")'.format(item.text()))

    @pyqtSlot(int)
    def select_calc(self, i):
        name = self.comboBox.currentText()
        self._current = name
        self.refreshContents()

    def refreshContents(self):
        if self._current is None or self._current == "": return
        e = self.dat.flowsheet.results.calculated_columns.get(self._current, "")
        self.expressionEdit.setPlainText(e)

    def apply_changes(self):
        if self._current is None or self._current == "": return
        self.dat.flowsheet.results.set_calculated_column(
            self._current, self.expressionEdit.toPlainText())

    def add_calc(self, name, expr=""):
        self.apply_changes()
        self._current = name
        self.comboBox.addItem(name)
        self.dat.flowsheet.results.set_calculated_column(self._current, expr)
        self.comboBox.setCurrentText(self._current)

    def add_dialog(self):
        newName, ok = QInputDialog.getText(
            self, "Column Name", "New column name:")
        if ok and newName != '': # if name supplied and not canceled
            if newName in self.dat.flowsheet.results.calculated_columns:
                QMessageBox.information(
                    self, "Error", "The column already exists.")
            else:
                self.add_calc(newName)
