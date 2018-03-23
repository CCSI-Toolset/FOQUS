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
        hm = self.dat.flowsheet.results.headMap
        for h in hm:
            item = QListWidgetItem(h)
            item.setCheckState(QtCore.Qt.Checked)
            if h in self.dat.flowsheet.results.hiddenCols:
                item.setCheckState(QtCore.Qt.Unchecked)
            else:
                item.setCheckState(QtCore.Qt.Checked)
            if h.startswith('Input.'):
                self.inputColumnsList.addItem(item)
            elif h.startswith('Output.'):
                self.outputColumnsList.addItem(item)
            elif h.startswith('NodeSetting.'):
                self.settingsColumnsList.addItem(item)
            else:
                self.metadataColumnsList.addItem(item)

    def accept(self):
        self.close()
