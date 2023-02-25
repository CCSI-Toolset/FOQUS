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
import os
from PyQt5 import uic, QtCore

mypath = os.path.dirname(__file__)
_saveMetadataDialogUI, _saveMetadataDialog = uic.loadUiType(
    os.path.join(mypath, "saveMetadataDialog_UI.ui")
)
# super(, self).__init__(parent=parent)


class saveMetadataDialog(_saveMetadataDialog, _saveMetadataDialogUI):
    sendTag = QtCore.pyqtSignal()

    def __init__(self, dat, parent=None):
        """
        Constructor for model setup dialog
        """
        super(saveMetadataDialog, self).__init__(parent=parent)
        self.setupUi(self)  # Create the widgets
        self.cancelButton.clicked.connect(self.reject)
        self.continueButton.clicked.connect(self.accept)

    def accept(self):
        self.entry = self.changeLogEntryText.toPlainText()
        self.done(1)

    def reject(self):
        self.done(0)
