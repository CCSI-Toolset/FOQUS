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
_heatIntegrationFrameUI, _heatIntegrationFrame = uic.loadUiType(
    os.path.join(mypath, "heatIntegrationFrame_UI.ui")
)


class heatIntegrationFrame(_heatIntegrationFrame, _heatIntegrationFrameUI):
    def __init__(self, dat, parent=None):
        super(heatIntegrationFrame, self).__init__(parent=parent)
        self.setupUi(self)
        self.dat = dat

    def applyChanges(self):
        # WHY pylint correctly reports these two as missing variables;
        # the fact that this does not cause a runtime error suggests that this function is not being called
        # TODO pylint: disable=undefined-variable
        heatIntObject.hrat = float(hratEdit.text())
