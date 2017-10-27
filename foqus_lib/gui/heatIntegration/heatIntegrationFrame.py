
#from foqus_lib.gui.heatIntegration.heatIntegrationFrame_UI import *
#from PySide import QtGui, QtCore

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QStyledItemDelegate
import os
from PyQt5 import uic
mypath = os.path.dirname(__file__)
_heatIntegrationFrameUI, _heatIntegrationFrame = \
        uic.loadUiType(os.path.join(mypath, "heatIntegrationFrame_UI.ui"))
#super(, self).__init__(parent=parent)

class heatIntegrationFrame(_heatIntegrationFrame, _heatIntegrationFrameUI):
    def __init__(self, dat, parent=None):
                super(heatIntegrationFrame, self).__init__(parent=parent)
                self.setupUi(self)
                self.dat = dat

    def applyChanges(self):
        heatIntObject.hrat = float(hratEdit.text())
