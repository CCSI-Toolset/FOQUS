"""dataBrowserDialog.py

* Window to show the flowsheet data browser.

John Eslick, Carnegie Mellon University, 2014
See LICENSE.md for license and copyright details.
"""
import os

from foqus_lib.gui.flowsheet.dataBrowserFrame import *
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
mypath = os.path.dirname(__file__)
_dataBrowserDialogUI, _dataBrowserDialog = \
        uic.loadUiType(os.path.join(mypath, "dataBrowserDialog_UI.ui"))


class dataBrowserDialog(_dataBrowserDialog, _dataBrowserDialogUI):
    def __init__(self, dat, parent=None, flags=QtCore.Qt.WindowCloseButtonHint):
        super(dataBrowserDialog, self).__init__(parent=parent, flags=flags)
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
