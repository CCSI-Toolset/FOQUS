'''
    dataBrowserDialog.py

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
import os

from foqus_lib.gui.flowsheet.dataBrowserFrame import *
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
mypath = os.path.dirname(__file__)
_dataBrowserDialogUI, _dataBrowserDialog = \
        uic.loadUiType(os.path.join(mypath, "dataBrowserDialog_UI.ui"))


class dataBrowserDialog(_dataBrowserDialog, _dataBrowserDialogUI):
    def __init__(self, dat, parent=None):
        super(dataBrowserDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.dat = dat
        #self.closeButton.clicked.connect( self.closeButtonClick )
        self.dataFrame = dataBrowserFrame(dat, self)
        self.layout().addWidget(self.dataFrame)

    def show(self):
        self.dataFrame.refreshContents()
        self.dataFrame.updateFilterBox()
        QDialog.show(self)
        # if you resize the columns before showing Qt seems to
        # calculate the width of all the cells in the table
        # if you do it after showing Qt only uses the visible cells
        # so it a lot faster.  This arrangement is much better
        # if the table has a lot of rows there could be a few second
        # delay.
        #
        # Turned off takes too long with a lot of columns.
        #self.dataFrame.tableView.resizeColumnsToContents()

    def closeButtonClick(self):
        self.hide()
