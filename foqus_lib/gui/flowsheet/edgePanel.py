from foqus_lib.gui.flowsheet.edgePanel_UI import *
from PySide import QtGui, QtCore

import foqus_lib.gui.helpers.guiHelpers as gh
import types

class edgeDock(QtGui.QDockWidget, Ui_edgeDock):
    redrawFlowsheet = QtCore.Signal()

    def __init__(self, dat, parent=None):
        '''
            Initialize the edge edit dock widget
        '''
        QtGui.QDockWidget.__init__(self, parent)
        self.setupUi(self)
        self.dat = dat
        self.mw = parent
        self.index = None
        self.addConButton.clicked.connect(self.addConnection)
        self.deleteConButton.clicked.connect(self.delConnection)
        self.autoButton.clicked.connect(self.autoConnect)
        self.fromBox.currentIndexChanged.connect(self.updateConnections)
        self.toBox.currentIndexChanged.connect(self.updateConnections)
        self.indexBox.currentIndexChanged.connect(self.changeIndex)
        self.show()
        self.edge = None

    def applyChanges(self):
        '''
            Update the edge with the parameters shown on the form
        '''
        if self.edge == None:
            return
        if self.tearBox.isChecked(): self.edge.tear = True
        else: self.edge.tear = False
        if self.activeBox.isChecked(): self.edge.active = True
        else: self.edge.active = False
        try:
            self.edge.curve = float( self.curveBox.text() )
        except:
            print "Curve must be a number"
        self.edge.start = self.fromBox.currentText()
        self.edge.end = self.toBox.currentText()
        self.edge.con = []
        for row in range( self.connectTable.rowCount() ):
            f = gh.cellPulldownValue(self.connectTable, row, 0)
            t = gh.cellPulldownValue(self.connectTable, row, 1)
            a = gh.isCellChecked(self.connectTable, row, 2)[0]
            self.edge.addConnection(f, t, a)
        self.redrawFlowsheet.emit()
        
    def changeIndex(self, index):
        if self.index != None:
            self.applyChanges()
        self.setEdgeIndex(index)
        
    def setEdgeIndex(self, index):
        '''
            Set the index of the edge to display/edit
            
            index:  the index of the edge in the graph
        '''
        if index == None:
            #if there are edges in the for clearContent will update the
            #form with edge 0 selected
            self.edge = None
            self.clearContent()
        else:
            #Update the form with the specified index
            self.index = index
            self.edge = self.dat.flowsheet.edges[self.index]
            self.updateForm()

    def clearContent(self):
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
        '''
            Synchronize the edge edit form with the current edge index
        '''
        #self.indexBox.setText(str(self.index))
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
        '''
            Add all edge indexes to the index combo and set the current
            text to the current index.  If the current index is not in
            the list set the index to the first thing on the list.
        '''
        self.indexBox.blockSignals(True)
        self.indexBox.clear()
        self.indexBox.addItems(
            map(str, range(len(self.dat.flowsheet.edges))))
        if self.index >= 0 and self.index != None:
            self.indexBox.setCurrentIndex(self.index)
        self.index = self.indexBox.currentIndex()
        if len(self.dat.flowsheet.edges) > 0:
            self.edge = self.dat.flowsheet.edges[self.index]
        self.indexBox.blockSignals(False)
        
    def updateNodeSelection(self):
        '''
            Fill in the to and from node selection boxes and set the 
            current selection to match the selected edge
        '''
        self.fromBox.blockSignals( True )
        self.toBox.blockSignals( True )
        self.fromBox.clear()
        self.toBox.clear()
        nodes = sorted( self.dat.flowsheet.nodes.keys() )
        self.fromBox.addItems( nodes )
        self.toBox.addItems( nodes )
        if self.edge != None:
            index = self.fromBox.findText( self.edge.start )
            if index < 0: index = 0
            self.fromBox.setCurrentIndex(index)
            index = self.toBox.findText( self.edge.end )
            if index < 0: index = 0
            self.toBox.setCurrentIndex(index)
        self.fromBox.blockSignals( False )
        self.toBox.blockSignals( False )
        
    def updateConnections(self):
        '''
            Update the connection table from the currently selected edge.
        '''
        self.connectTable.clearContents()
        vars1in = sorted(self.dat.flowsheet.nodes[ self.fromBox.currentText() ].inVars.keys())
        vars1out = sorted(self.dat.flowsheet.nodes[ self.fromBox.currentText() ].outVars.keys())
        vars2 = sorted(self.dat.flowsheet.nodes[ self.toBox.currentText() ] .inVars.keys())
        if self.edge.start == self.fromBox.currentText() and self.edge.end == self.toBox.currentText():
            self.connectTable.setRowCount( len(self.edge.con) )
            for i in range( len(self.edge.con) ):
                gh.setTableItem( self.connectTable, i, 0, self.edge.con[i].fromName, pullDown = vars1out + vars1in )
                self.connectTable.cellWidget(  i,  0  ).insertSeparator( len(vars1out) )
                gh.setTableItem( self.connectTable, i, 1, self.edge.con[i].toName, pullDown = vars2 )
                gh.setTableItem( self.connectTable, i, 2, "", check = self.edge.con[i].active, editable = False )
        else:
            self.connectTable.setRowCount( 0 )
        self.connectTable.resizeColumnsToContents()
        
    def autoConnect(self):
        N1In  = sorted(self.dat.flowsheet.nodes[ self.fromBox.currentText() ].inVars.keys())
        N1Out = sorted(self.dat.flowsheet.nodes[ self.fromBox.currentText() ].outVars.keys())
        N2In  = sorted(self.dat.flowsheet.nodes[ self.toBox.currentText() ].inVars.keys())
        for var in N1Out:
            if var in N2In:  self.addConnection(var, var)
        for var in N1In:
            if var in N2In:  self.addConnection(var, var)
                
    def addConnection(self, fv ="", tv=""):
        self.connectTable.setRowCount( self.connectTable.rowCount() + 1 )
        vars1in = sorted(self.dat.flowsheet.nodes[ self.fromBox.currentText() ].inVars.keys())
        vars1out = sorted(self.dat.flowsheet.nodes[ self.fromBox.currentText() ].outVars.keys())
        vars2 = sorted(self.dat.flowsheet.nodes[ self.toBox.currentText() ] .inVars.keys())
        i = self.connectTable.rowCount() - 1
        gh.setTableItem( self.connectTable, i, 0, fv, pullDown = vars1out + vars1in )
        self.connectTable.cellWidget(  i,  0  ).insertSeparator( len(vars1out) )
        gh.setTableItem( self.connectTable, i, 1, tv, pullDown = vars2 )
        gh.setTableItem( self.connectTable, i, 2, "", check = True, editable = False )
        self.connectTable.resizeColumnsToContents()
    
    def delConnection(self):
        indexes = self.connectTable.selectedIndexes()
        delRowSet = sorted(list(set([index.row() for index in indexes])), reverse = True)
        for row in delRowSet:
            self.connectTable.removeRow(row)

    def closeEvent(self, event):
        '''
            Intercept the close event and apply changes to node before closing
        '''
        self.applyChanges()
        self.lockConnection.setChecked(True)
        event.accept()
        self.mw.toggleEdgeEditorAction.setChecked(False)  
