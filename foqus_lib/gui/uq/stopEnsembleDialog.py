import os
from PyQt5 import uic
mypath = os.path.dirname(__file__)
_stopEnsembleDialogUI, _stopEnsembleDialog = \
        uic.loadUiType(os.path.join(mypath, "stopEnsembleDialog_UI.ui"))
        

class stopEnsembleDialog(_stopEnsembleDialog, _stopEnsembleDialogUI):
    def __init__(self, dat, parent=None):
        '''
            Constructor for model setup dialog
        '''
        super(stopEnsembleDialog, self).__init__(parent=parent)
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
