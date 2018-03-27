"""columns.py
* Window to show the flowsheet data browser.

John Eslick, Carnegie Mellon University, 2014
See LICENSE.md for license and copyright details.
"""
import os
from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import QDialogButtonBox, QListWidgetItem
mypath = os.path.dirname(__file__)
_columnsDialogUI, _columnsDialog = \
        uic.loadUiType(os.path.join(mypath, "columns_UI.ui"))


class columnsDialog(_columnsDialog, _columnsDialogUI):
    def __init__(self, dat, parent=None):
        super(columnsDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.dat = dat
        self.buttonBox.button(
            QDialogButtonBox.Ok).clicked.connect(self.accept)
        hm = self.dat.flowsheet.results.columns
        self.items = {}
        for h in hm:
            item = QListWidgetItem(h)
            self.items[h] = item
            item.setCheckState(QtCore.Qt.Checked)
            if h in self.dat.flowsheet.results.hidden_cols:
                item.setCheckState(QtCore.Qt.Unchecked)
            else:
                item.setCheckState(QtCore.Qt.Checked)
            if h.startswith('input.'):
                self.inputColumnsList.addItem(item)
            elif h.startswith('output.'):
                self.outputColumnsList.addItem(item)
            elif h.startswith('setting.'):
                self.settingsColumnsList.addItem(item)
            else:
                self.metadataColumnsList.addItem(item)

    def accept(self):
        self.dat.flowsheet.results.hidden_cols = []
        for col in self.items:
            if not self.items[col].checkState():
                self.dat.flowsheet.results.hidden_cols.append(col)
        self.close()
