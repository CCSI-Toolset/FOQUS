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
_runRowsDialogUI, _runRowsDialog = uic.loadUiType(
    os.path.join(mypath, "runRowsDialog_UI.ui")
)


class runRowsDialog(_runRowsDialog, _runRowsDialogUI):
    def __init__(self, parent, dat):
        super(runRowsDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.dat = dat
        self.stop_now = False
        self.disconnect_now = False
        self.samples = 0
        self.success = 0
        self.error = 0
        self.time = 0
        self.allDone = False
        self.stopButton.clicked.connect(self.stopPress)
        self.disButton.clicked.connect(self.disPress)

    def stopPress(self):
        if self.allDone:
            self.close()
        self.stop_now = True

    def disPress(self):
        self.disconnect_now = True

    def update(self):
        self.samplesLine.setText(str(self.samples))
        self.successLine.setText(str(self.success))
        self.errorLine.setText(str(self.error))
        self.timeLine.setText(str(self.time))
        if self.allDone:
            self.stopButton.setText("Done")
        # WHY pylint reports this error because mainWin is added to self.dat after its initialization
        # this could result in a runtime error unless mainWin is always present and always the correct type
        self.dat.mainWin.app.processEvents()  # TODO pylint: disable=no-member

    def closeEvent(self, event):
        """
        Intercept close main window close event
        make sure you really want to quit
        """
        if self.allDone:
            event.accept()
        else:
            event.ignore()
