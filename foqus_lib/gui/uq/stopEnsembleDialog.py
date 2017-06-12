from stopEnsembleDialog_UI import *
from PySide import QtGui, QtCore

class stopEnsembleDialog(QtGui.QDialog, Ui_stopEnsembleDialog):
    def __init__(self, dat, parent=None):
        '''
            Constructor for model setup dialog
        '''
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self) # Create the widgets
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
        
