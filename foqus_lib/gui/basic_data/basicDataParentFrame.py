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
import sys
import os

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow

mypath = os.path.dirname(__file__)
_basicDataParentFrameUI, _basicDataParentFrame = uic.loadUiType(
    os.path.join(mypath, "basicDataParentFrame_UI.ui")
)


class basicDataParentFrame(_basicDataParentFrame, _basicDataParentFrameUI):
    format = "%.5f"  # numeric format for table entries in UQ Toolbox

    def __init__(self, parent=None):
        super(basicDataParentFrame, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)
        self.dmfGroup.hide()
        self.solventFitFrame.init(parent=self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    MainWindow = QMainWindow(parent=None)

    MainFrame = basicDataParentFrame()
    MainWindow.setCentralWidget(MainFrame)

    MainWindow.show()
    sys.exit(app.exec_())
