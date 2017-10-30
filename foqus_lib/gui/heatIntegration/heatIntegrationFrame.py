import os
from PyQt5 import uic
mypath = os.path.dirname(__file__)
_heatIntegrationFrameUI, _heatIntegrationFrame = \
        uic.loadUiType(os.path.join(mypath, "heatIntegrationFrame_UI.ui"))


class heatIntegrationFrame(_heatIntegrationFrame, _heatIntegrationFrameUI):
    def __init__(self, dat, parent=None):
        super(heatIntegrationFrame, self).__init__(parent=parent)
        self.setupUi(self)
        self.dat = dat

    def applyChanges(self):
        heatIntObject.hrat = float(hratEdit.text())
