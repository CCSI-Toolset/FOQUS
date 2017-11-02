import os
from PyQt5 import uic, QtCore
mypath = os.path.dirname(__file__)
_saveMetadataDialogUI, _saveMetadataDialog = \
        uic.loadUiType(os.path.join(mypath, "saveMetadataDialog_UI.ui"))
#super(, self).__init__(parent=parent)

class saveMetadataDialog(_saveMetadataDialog, _saveMetadataDialogUI):
    sendTag = QtCore.pyqtSignal( )

    def __init__(self, dat, parent = None):
        '''
            Constructor for model setup dialog
        '''
        super(saveMetadataDialog, self).__init__(parent=parent)
        self.setupUi(self) # Create the widgets
        self.cancelButton.clicked.connect(self.reject)
        self.continueButton.clicked.connect(self.accept)

    def accept(self):
        self.entry = self.changeLogEntryText.toPlainText()
        self.done(1)

    def reject(self):
        self.done(0)
