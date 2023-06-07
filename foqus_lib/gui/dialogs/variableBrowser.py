#################################################################################
# FOQUS Copyright (c) 2012 - 2023, by the software owners: Oak Ridge Institute
# for Science and Education (ORISE), TRIAD National Security, LLC., Lawrence
# Livermore National Security, LLC., The Regents of the University of
# California, through Lawrence Berkeley National Laboratory, Battelle Memorial
# Institute, Pacific Northwest Division through Pacific Northwest National
# Laboratory, Carnegie Mellon University, West Virginia University, Boston
# University, the Trustees of Princeton University, The University of Texas at
# Austin, URS Energy & Construction, Inc., et al.  All rights reserved.
#
# Please see the file LICENSE.md for full copyright and license information,
# respectively. This file is also available online at the URL
# "https://github.com/CCSI-Toolset/FOQUS".
#################################################################################
import os

from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import QTreeWidgetItem

mypath = os.path.dirname(__file__)
_variableBrowserUI, _variableBrowser = uic.loadUiType(
    os.path.join(mypath, "variableBrowser_UI.ui")
)


class variableBrowser(_variableBrowser, _variableBrowserUI):
    def __init__(self, dat, parent=None, lock=None):
        """
        Constructor for model setup dialog
        """
        super(variableBrowser, self).__init__(parent=parent)
        self.setupUi(self)  # Create the widgets
        self.dat = dat  # all of the session data
        self.nodeMask = None
        self.refreshButton.clicked.connect(self.refreshVars)
        self.closeButton.clicked.connect(self.close)
        self.treeWidget.currentItemChanged.connect(self.itemSelect)
        self.format = "optimization"

    def itemSelect(self, item, prev):
        if item:
            nkey = item.text(0)
            mode = item.text(1)
            vkey = item.text(2)
            if mode == "input":
                mode = "x"
            else:
                mode = "f"
            if self.format == "node":
                text = '%s["%s"]' % (mode, vkey)
            elif self.format == "optimization":
                text = '%s["%s"]["%s"]' % (mode, nkey, vkey)
            self.varText.setText(text)

    def refreshVars(self):
        """
        Put the graph node variables into the tree
        """
        vars = dict()
        if self.nodeMask:
            nodes = sorted(self.nodeMask)
        else:
            nodes = sorted(self.dat.flowsheet.nodes.keys())
        items = []
        self.treeWidget.clear()
        for nkey in nodes:
            node = self.dat.flowsheet.nodes[nkey]
            items.append(QTreeWidgetItem(self.treeWidget))
            items[-1].setText(0, nkey)
            inputItems = QTreeWidgetItem(items[-1])
            inputItems.setText(0, nkey)
            inputItems.setText(1, "input")
            outputItems = QTreeWidgetItem(items[-1])
            outputItems.setText(0, nkey)
            outputItems.setText(1, "output")
            for vkey, var in node.inVars.items():
                vItem = QTreeWidgetItem(inputItems)
                vItem.setText(0, nkey)
                vItem.setText(1, "input")
                vItem.setText(2, vkey)
            for vkey, var in node.outVars.items():
                vItem = QTreeWidgetItem(outputItems)
                vItem.setText(0, nkey)
                vItem.setText(1, "output")
                vItem.setText(2, vkey)
        self.treeWidget.insertTopLevelItems(0, items)
