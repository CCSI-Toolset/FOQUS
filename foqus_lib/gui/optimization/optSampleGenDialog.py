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
"""optSampleGenDialog.py
* dialog generate samples to be used in calculation of objective function

John Eslick, Carnegie Mellon University, 2014
"""
import os
import foqus_lib.gui.helpers.guiHelpers as gh
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox

mypath = os.path.dirname(__file__)
_optSampleGenDialogUI, _optSampleGenDialog = uic.loadUiType(
    os.path.join(mypath, "optSampleGenDialog_UI.ui")
)


class optSampleGenDialog(_optSampleGenDialog, _optSampleGenDialogUI):
    SAMPLE_FULL_FACT = 0
    SAMPLE_FILE = 1

    def __init__(self, varNames, parent=None):
        super(optSampleGenDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.varNames = varNames
        self.okayButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        self.FileButton.clicked.connect(self.fileBrowse)
        self.ffactTable.setRowCount(len(varNames))
        self.sampleType = self.SAMPLE_FULL_FACT
        self.sampleSettings = {}
        for row, var in enumerate(varNames):
            gh.setTableItem(self.ffactTable, row, 0, var)

    def fileBrowse(self):
        fileName, filtr = QFileDialog.getOpenFileName(
            self,
            "Open Sample File",
            "",
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*)",
        )
        if fileName:
            self.FileEdit.setText(fileName)

    def reject(self):
        self.done(QDialog.Rejected)

    def accept(self):
        self.sampleType = self.typeCombo.currentIndex()
        if self.sampleType == self.SAMPLE_FULL_FACT:
            for row, var in enumerate(self.varNames):
                self.sampleSettings[var] = gh.getCellJSON(self.ffactTable, row, 1)
                if not isinstance(self.sampleSettings[var], list):
                    QMessageBox.warning(
                        self,
                        "Error",
                        "A list of number is need for each variable "
                        "(e.g. [1.0, 2.0])",
                    )
                    return
        if self.sampleType == self.SAMPLE_FILE:
            self.sampleSettings = self.FileEdit.text()
        self.done(QDialog.Accepted)
