


from foqus_lib.gui.heatIntegration.heatIntegrationFrame_UI import *
from PySide import QtGui, QtCore

class heatIntegrationFrame(QtGui.QFrame, Ui_heatIntegrationFrame):
    def __init__(self, dat, parent=None):
                QtGui.QFrame.__init__(self, parent)
                self.setupUi(self)
                self.dat = dat
        
    def applyChanges(self):
        heatIntObject.hrat = float(hratEdit.text())
