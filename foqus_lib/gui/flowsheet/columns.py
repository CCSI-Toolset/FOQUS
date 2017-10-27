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
#import foqus_lib.gui.flowsheet.columns_UI
#from PySide import QtGui, QtCore
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMessageBox
import os
from PyQt5 import uic
mypath = os.path.dirname(__file__)
_columnsDialogUI, _columnsDialog = \
        uic.loadUiType(os.path.join(mypath, "columns_UI.ui"))
#super(, self).__init__(parent=parent)


class columnsDialog(_columnsDialog, _columnsDialogUI):
    def __init__(self, dat, parent=None):
        super(columnsDialog, self).__init__(parent=parent)
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
