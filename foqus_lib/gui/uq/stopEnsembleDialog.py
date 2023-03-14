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
from PyQt5 import uic

mypath = os.path.dirname(__file__)
_stopEnsembleDialogUI, _stopEnsembleDialog = uic.loadUiType(
    os.path.join(mypath, "stopEnsembleDialog_UI.ui")
)


class stopEnsembleDialog(_stopEnsembleDialog, _stopEnsembleDialogUI):
    def __init__(self, dat, parent=None):
        """
        Constructor for model setup dialog
        """
        super(stopEnsembleDialog, self).__init__(parent=parent)
        self.setupUi(self)  # Create the widgets
        self.buttonCode = 0
        self.terminateButton.clicked.connect(self.terminateEnsemble)
        self.disconnectButton.clicked.connect(self.disconnect)
        self.continueButton.clicked.connect(self.doNothing)

    def terminateEnsemble(self):
        self.buttonCode = 2
        self.close()

    def disconnect(self):
        self.buttonCode = 1
        self.close()

    def doNothing(self):
        self.buttonCode = 0
        self.close()
