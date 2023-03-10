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
import logging

from PyQt5 import QtCore, uic

import foqus_lib.gui.helpers.guiHelpers as gh

_log = logging.getLogger("foqus.{}".format(__name__))
mypath = os.path.dirname(__file__)

_edgeDockUI, _edgeDock = uic.loadUiType(os.path.join(mypath, "edgePanel_UI.ui"))


class edgeDock(_edgeDock, _edgeDockUI):
    """
    Dock widget for editing an edge.  In FOQUS an edge connects variables in
    two nodes.
    """

    redrawFlowsheet = QtCore.pyqtSignal()

    def __init__(self, dat, parent=None):
        """
        Initialize the edge edit dock widget

        Args:
            parent: parent widget
        Returns:
            None
        """
        super().__init__(parent=parent)
        self.setupUi(self)
        self.dat = dat
        self.mw = parent
        self.index = None
        self.addConButton.clicked.connect(self.clickAddConnection)
        self.deleteConButton.clicked.connect(self.delConnection)
        self.autoButton.clicked.connect(self.autoConnect)
        self.fromBox.currentIndexChanged.connect(self.updateConnections)
        self.toBox.currentIndexChanged.connect(self.updateConnections)
        self.indexBox.currentIndexChanged.connect(self.changeIndex)
        self.show()
        self.edge = None

    def clickAddConnection(self):
        """
        For PyQt5 buttons also send a checked argument to the callback even when
        they are not checkable. You can't set a callback that takes args unless
        you account for the checked argument.  So this just drops the checked
        arg and calls addConection().
        """
        self.addConnection()

    def applyChanges(self):
        """
        Update the edge with the parameters shown on the form
        """
        if self.edge == None:
            return
        if self.tearBox.isChecked():
            self.edge.tear = True
        else:
            self.edge.tear = False
        if self.activeBox.isChecked():
            self.edge.active = True
        else:
            self.edge.active = False
        try:
            self.edge.curve = float(self.curveBox.text())
        except:
            print("Curve must be a number")
        self.edge.start = self.fromBox.currentText()
        self.edge.end = self.toBox.currentText()
        self.edge.con = []
        for row in range(self.connectTable.rowCount()):
            f = gh.cellPulldownValue(self.connectTable, row, 0)
            t = gh.cellPulldownValue(self.connectTable, row, 1)
            a = gh.isCellChecked(self.connectTable, row, 2)[0]
            self.edge.addConnection(f, t, a)
        self.redrawFlowsheet.emit()

    def changeIndex(self, index):
        """
        Callback to update when a differnt edge is selected from the edge index
        pulldown.

        Args:
            index: the new pulldown selection index
        Returns:
            None
        """
        if self.index != None:
            self.applyChanges()
        self.setEdgeIndex(index)

    def setEdgeIndex(self, index):
        """
        Set the index of the edge to display/edit

        Args:
            index: the index of the edge in the graph
        """
        if index == None:
            # if there are edges in the for clearContent will update the
            # form with edge 0 selected
            self.edge = None
            self.clearContent()
        else:
            # Update the form with the specified index
            self.index = index
            self.edge = self.dat.flowsheet.edges[self.index]
            self.updateForm()

    def clearContent(self):
        """
        Clears the edge editor.

        Args:
            None
        Return:
            None
        """
        self.index = None
        self.updateIndexBox()
        if self.index < 0:
            self.index = None
        if self.index != None:
            self.edge = self.dat.flowsheet.edges[self.index]
            self.updateForm()
        else:
            self.tearBox.setChecked(False)
            self.activeBox.setChecked(True)
            self.curveBox.setText(str(0.0))
            self.connectTable.clearContents()
            self.updateNodeSelection()

    def updateForm(self):
        """
        Synchronize the edge edit form with the current edge index

        Args:
            None
        Returns:
            None
        """
        # self.indexBox.setText(str(self.index))
        self.updateIndexBox()
        if self.index == None or self.index < 0:
            self.clearContent()
        else:
            self.tearBox.setChecked(self.edge.tear)
            self.activeBox.setChecked(self.edge.active)
            self.curveBox.setText(str(self.edge.curve))
            self.updateNodeSelection()
            self.updateConnections()

    def updateIndexBox(self):
        """
        Add all edge indexes to the index combo and set the current text to the
        current index. If the current index is not in the list set the index to
        the first thing on the list.

        Args:
            None
        Returns:
            None
        """
        self.indexBox.blockSignals(True)
        self.indexBox.clear()
        self.indexBox.addItems(
            list(map(str, list(range(len(self.dat.flowsheet.edges)))))
        )
        if self.index is not None and self.index >= 0:
            self.indexBox.setCurrentIndex(self.index)
        self.index = self.indexBox.currentIndex()
        if len(self.dat.flowsheet.edges) > 0:
            self.edge = self.dat.flowsheet.edges[self.index]
        self.indexBox.blockSignals(False)

    def updateNodeSelection(self):
        """
        Fill in the to and from node selection boxes and set the current
        selection to match the selected edge.

        Args:
            None
        Returns:
            None
        """
        self.fromBox.blockSignals(True)
        self.toBox.blockSignals(True)
        self.fromBox.clear()
        self.toBox.clear()
        nodes = sorted(self.dat.flowsheet.nodes.keys())
        self.fromBox.addItems(nodes)
        self.toBox.addItems(nodes)
        if self.edge != None:
            index = self.fromBox.findText(self.edge.start)
            if index < 0:
                index = 0
            self.fromBox.setCurrentIndex(index)
            index = self.toBox.findText(self.edge.end)
            if index < 0:
                index = 0
            self.toBox.setCurrentIndex(index)
        self.fromBox.blockSignals(False)
        self.toBox.blockSignals(False)

    def updateConnections(self):
        """
        Update the connection table from the currently selected edge.

        Args:
            None
        Returns:
            None
        """
        n1 = self.fromBox.currentText()
        n2 = self.toBox.currentText()
        self.connectTable.clearContents()
        vars1in = sorted(self.dat.flowsheet.nodes[n1].inVars.keys())
        vars1out = sorted(self.dat.flowsheet.nodes[n1].outVars.keys())
        vars2 = sorted(self.dat.flowsheet.nodes[n2].inVars.keys())
        if self.edge.start == n1 and self.edge.end == n2:
            self.connectTable.setRowCount(len(self.edge.con))
            for i in range(len(self.edge.con)):
                gh.setTableItem(
                    self.connectTable,
                    i,
                    0,
                    self.edge.con[i].fromName,
                    pullDown=vars1out + vars1in,
                )
                self.connectTable.cellWidget(i, 0).insertSeparator(len(vars1out))
                gh.setTableItem(
                    self.connectTable, i, 1, self.edge.con[i].toName, pullDown=vars2
                )
                gh.setTableItem(
                    self.connectTable,
                    i,
                    2,
                    "",
                    check=self.edge.con[i].active,
                    editable=False,
                )
        else:
            self.connectTable.setRowCount(0)
        self.connectTable.resizeColumnsToContents()

    def autoConnect(self):
        """
        Add connections to the connection table that connect variables with the
        same name in from node to the to node.  The vaiables can be inputs or
        outputs in the from node, but only inputs in the to node.

        Args:
            None
        Returns:
            None
        """
        n1 = self.fromBox.currentText()
        n2 = self.toBox.currentText()
        N1In = sorted(self.dat.flowsheet.nodes[n1].inVars.keys())
        N1Out = sorted(self.dat.flowsheet.nodes[n1].outVars.keys())
        N2In = sorted(self.dat.flowsheet.nodes[n2].inVars.keys())
        for var in N1Out:
            if var in N2In:
                self.addConnection(fv=var, tv=var)
        for var in N1In:
            if var in N2In:
                self.addConnection(tv=var, fv=var)

    def addConnection(self, fv="", tv=""):
        """
        Add a new row to the connection table, if fv and/or tv are supplied
        and fv and tv are valid variable names, initally create the row with
        the specified connection.

        Args
            fv (str): Input or output var in from node, "" for user selection
            tv (str): Input var in to node, "" for user selection later
        Returns:
            None
        """
        n1 = self.fromBox.currentText()
        n2 = self.toBox.currentText()
        _log.debug("Adding connection from {}.{} to {}.{}".format(n1, fv, n2, tv))
        # Add row
        self.connectTable.setRowCount(self.connectTable.rowCount() + 1)
        # get variable names, can connect in and out vars in n1 to in vars in n2
        vars1in = sorted(self.dat.flowsheet.nodes[n1].inVars.keys())
        vars1out = sorted(self.dat.flowsheet.nodes[n1].outVars.keys())
        vars2 = sorted(self.dat.flowsheet.nodes[n2].inVars.keys())
        # Fill in the pull down boxes
        row = self.connectTable.rowCount() - 1
        gh.setTableItem(self.connectTable, row, 0, fv, pullDown=vars1out + vars1in)
        # Put a seperator between output and input vars in from vars
        self.connectTable.cellWidget(row, 0).insertSeparator(len(vars1out))
        gh.setTableItem(self.connectTable, row, 1, tv, pullDown=vars2)
        gh.setTableItem(  # This is the active checkbox
            self.connectTable, row, 2, "", check=True, editable=False
        )
        # make columns wide enough to see what's goning on
        self.connectTable.resizeColumnsToContents()

    def delConnection(self):
        """
        Delete the selected rows from the connection table

        Args:
            None
        Returns:
            None
        """
        indexes = self.connectTable.selectedIndexes()
        delRowSet = sorted(list(set([index.row() for index in indexes])), reverse=True)
        for row in delRowSet:
            self.connectTable.removeRow(row)

    def closeEvent(self, event):
        """
        Intercept the close event and apply changes to node before closing

        Args:
            event (QEvent): The triggering event
        Returns:
            None
        """
        self.applyChanges()
        self.lockConnection.setChecked(True)
        event.accept()
        self.mw.toggleEdgeEditorAction.setChecked(False)
