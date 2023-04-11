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
"""flowsheetSettingsDialog.py
* Dialog to change flowsheet solver settings.

John Eslick, Carnegie Mellon University, 2014
"""
import os
from PyQt5 import uic

mypath = os.path.dirname(__file__)
_flowsheetSettingsDialogUI, _flowsheetSettingsDialog = uic.loadUiType(
    os.path.join(mypath, "flowsheetSettingsDialog_UI.ui")
)


class flowsheetSettingsDialog(_flowsheetSettingsDialog, _flowsheetSettingsDialogUI):
    def __init__(self, dat, parent=None, lock=None):
        super(flowsheetSettingsDialog, self).__init__(parent=parent)
        self.setupUi(self)  # Create the widgets
        self.gr = dat.flowsheet
        self.okayButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.cancel)
        # Fill in the form with the current settings
        i = self.tearSolverBox.findText(self.gr.tearSolver)
        self.tearSolverBox.setCurrentIndex(i)
        self.tearTolEdit.setText(str(self.gr.tearTol))
        self.tearItLimitEdit.setText(str(self.gr.tearMaxIt))
        self.wegAccMinEdit.setText(str(self.gr.wegAccMin))
        self.wegAccMaxEdit.setText(str(self.gr.wegAccMax))
        self.staggerTimeEdit.setText(str(self.gr.staggerStart))
        self.logTearCheckBox.setChecked(self.gr.tearLog)
        self.logTearStubEdit.setText(self.gr.tearLogStub)
        self.tearBoundCheckBox.setChecked(self.gr.tearBound)
        if self.gr.tearTolType == "abs":
            self.tearAbsTolRadioButton.setChecked(True)
        elif self.gr.tearTolType == "rng":
            self.tearFracTolRadioButton.setChecked(True)

    def accept(self):
        self.gr.tearSolver = self.tearSolverBox.currentText()
        self.gr.tearTol = float(self.tearTolEdit.text())
        self.gr.tearMaxIt = int(float(self.tearItLimitEdit.text()))
        self.gr.wegAccMin = float(self.wegAccMinEdit.text())
        self.gr.wegAccMax = float(self.wegAccMaxEdit.text())
        self.gr.staggerStart = float(self.staggerTimeEdit.text())
        self.gr.tearLog = self.logTearCheckBox.isChecked()
        self.gr.tearLogStub = self.logTearStubEdit.text()
        self.gr.tearBound = self.tearBoundCheckBox.isChecked()
        if self.tearAbsTolRadioButton.isChecked():
            self.gr.tearTolType = "abs"
        elif self.tearFracTolRadioButton.isChecked():
            self.gr.tearTolType = "rng"
        self.done(0)

    def cancel(self):
        self.done(0)
