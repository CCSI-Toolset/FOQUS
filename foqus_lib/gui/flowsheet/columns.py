'''
    columns.py
     
    * Window to show the flowsheet data browser.

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
import foqus_lib.gui.flowsheet.columns_UI 
from PySide import QtGui, QtCore
 
class columnsDialog(
    QtGui.QDialog, foqus_lib.gui.flowsheet.columns_UI.Ui_Dialog):
    def __init__(self, dat, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.dat = dat
        self.buttonBox.button(
            QtGui.QDialogButtonBox.Ok).clicked.connect(self.accept)
        hm = self.dat.flowsheet.results.headMap
        for h in hm:
            item = QtGui.QListWidgetItem(h)
            item.setCheckState(QtCore.Qt.Checked)
            if h in self.dat.flowsheet.results.hiddenCols:
                item.setCheckState(QtCore.Qt.Unchecked)
            else:
                item.setCheckState(QtCore.Qt.Checked)
            if h.startswith('Input.'):
                self.inputColumnsList.addItem(item)
            elif h.startswith('Output.'):
                self.outputColumnsList.addItem(item)
            elif h.startswith('NodeSetting.'):
                self.settingsColumnsList.addItem(item)
            else:
                self.metadataColumnsList.addItem(item)
            
    
    def accept(self):
        print "hi"
        self.close()


        
