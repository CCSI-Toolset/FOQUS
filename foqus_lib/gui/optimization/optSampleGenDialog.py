'''
    optSampleGenDialog.py
    
    * dialog generate samples to be used in calculation of objective 
      function

    John Eslick, Carnegie Mellon University, 2014

    This Material was produced under the DOE Carbon Capture Simulation
    Initiative (CCSI), and copyright is held by the software owners:
    ORISE, LANS, LLNS, LBL, PNNL, CMU, WVU, et al. The software owners
    and/or the U.S. Government retain ownership of all rights in the 
    CCSI software and the copyright and patents subsisting therein. Any
    distribution or dissemination is governed under the terms and 
    conditions of the CCSI Test and Evaluation License, CCSI Master
    Non-Disclosure Agreement, and the CCSI Intellectual Property 
    Management Plan. No rights are granted except as expressly recited
    in one of the aforementioned agreements.
'''
from optSampleGenDialog_UI import *
from PySide import QtGui, QtCore
import foqus_lib.gui.helpers.guiHelpers as gh

class optSampleGenDialog(QtGui.QDialog, Ui_optSampleGenDialog):
    SAMPLE_FULL_FACT = 0
    SAMPLE_FILE = 1
    
    def __init__(self, varNames):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        self.varNames = varNames
        self.okayButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        self.FileButton.clicked.connect(self.fileBrowse)
        self.ffactTable.setRowCount(len(varNames))
        self.sampleType = self.SAMPLE_FULL_FACT
        self.sampleSettings = {}
        for row, var in enumerate(varNames):
            gh.setTableItem(self.ffactTable,row,0,var)
    
    def fileBrowse(self):
        fileName, filtr = QtGui.QFileDialog.getOpenFileName(
            self,
            "Open Sample File",
            "",
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*)")
        if fileName:
            self.FileEdit.setText(fileName)
    
    def reject(self):
        self.done(QtGui.QDialog.Rejected)
        
    def accept(self):
        self.sampleType = self.typeCombo.currentIndex()
        if self.sampleType == self.SAMPLE_FULL_FACT:
            for row, var in enumerate(self.varNames):
                self.sampleSettings[var] = gh.getCellJSON(
                    self.ffactTable, row, 1)
        if self.sampleType == self.SAMPLE_FILE:
            self.sampleSettings = self.FileEdit.text()
        self.done(QtGui.QDialog.Accepted)
