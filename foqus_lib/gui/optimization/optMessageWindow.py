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
"""
John Eslick, Carnegie Mellon University, 2013
"""
import os
from PyQt5 import uic

mypath = os.path.dirname(__file__)
_optMessageWindowUI, _optMessageWindow = uic.loadUiType(
    os.path.join(mypath, "optMessageWindow_UI.ui")
)


class optMessageWindow(_optMessageWindow, _optMessageWindowUI):
    def __init__(self, parent=None):
        """
        Constructor for optimization message window
        """
        super(optMessageWindow, self).__init__(parent=parent)
        self.setupUi(self)  # Create the widgets

    def closeEvent(self, e):
        e.ignore()

    def clearMessages(self):
        self.msgTextBrowser.clear()
