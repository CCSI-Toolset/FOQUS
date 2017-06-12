from saveMetadataDialog_UI import *
from PySide import QtGui, QtCore

class saveMetadataDialog(QtGui.QDialog, Ui_saveMetadataDialog):
    sendTag = QtCore.Signal( )     
    
    def __init__(self, dat, parent = None):
        '''
            Constructor for model setup dialog
        '''
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self) # Create the widgets
        self.cancelButton.clicked.connect(self.reject)
        self.continueButton.clicked.connect(self.accept)
    
    def accept(self):
        self.entry = self.changeLogEntryText.toPlainText()
        self.done(1)
        
    def reject(self):
        self.done(0)

