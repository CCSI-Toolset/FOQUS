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
"""columns.py
* Window to show the flowsheet data browser.

John Eslick, Carnegie Mellon University, 2014
"""
import os
from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import QDialogButtonBox, QListWidgetItem

mypath = os.path.dirname(__file__)
_columnsDialogUI, _columnsDialog = uic.loadUiType(os.path.join(mypath, "columns_UI.ui"))


class columnsDialog(_columnsDialog, _columnsDialogUI):
    def __init__(self, dat, parent=None):
        super(columnsDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.dat = dat
        self.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.accept)
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
            if h.startswith("input."):
                self.inputColumnsList.addItem(item)
            elif h.startswith("output."):
                self.outputColumnsList.addItem(item)
            elif h.startswith("setting."):
                self.settingsColumnsList.addItem(item)
            else:
                self.metadataColumnsList.addItem(item)

    def accept(self):
        self.dat.flowsheet.results.hidden_cols = []
        for col in self.items:
            if not self.items[col].checkState():
                self.dat.flowsheet.results.hidden_cols.append(col)
        self.close()
