from variableBrowser_UI import *
from PySide import QtGui, QtCore

class variableBrowser(QtGui.QDialog, Ui_variableBrowser): 
    def __init__(self, dat, parent=None, lock = None):
        '''
            Constructor for model setup dialog
        '''
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self) # Create the widgets
        self.dat = dat     # all of the session data
        self.nodeMask = None
        self.refreshButton.clicked.connect( self.refreshVars )
        self.closeButton.clicked.connect( self.close )
        self.treeWidget.currentItemChanged.connect( self.itemSelect )
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
                text = "%s[\"%s\"]" % (mode, vkey)
            elif self.format == "optimization":
                text = "%s[\"%s\"][\"%s\"][0]" % (mode, nkey, vkey)
            self.varText.setText(text)
        
    def refreshVars(self):
        '''
            Put the graph node variables into the tree
        '''
        vars = dict()
        if self.nodeMask:
            nodes = sorted( self.nodeMask )
        else:
            nodes = sorted( self.dat.flowsheet.nodes.keys() )
        items = []
        self.treeWidget.clear()
        for nkey in nodes:
            node = self.dat.flowsheet.nodes[nkey]
            items.append( QtGui.QTreeWidgetItem(self.treeWidget) )
            items[-1].setText(0, nkey)
            inputItems = QtGui.QTreeWidgetItem( items[-1] )
            inputItems.setText(0, nkey)
            inputItems.setText(1, "input")
            outputItems = QtGui.QTreeWidgetItem( items[-1] )
            outputItems.setText(0, nkey)			
            outputItems.setText(1, "output")
            for vkey, var in node.inVars.iteritems():
                vItem = QtGui.QTreeWidgetItem( inputItems )
                vItem.setText(0, nkey)
                vItem.setText(1, "input")
                vItem.setText(2, vkey)
            for vkey, var in node.outVars.iteritems():
                vItem = QtGui.QTreeWidgetItem( outputItems )
                vItem.setText(0, nkey)
                vItem.setText(1, "output")
                vItem.setText(2, vkey)
        self.treeWidget.insertTopLevelItems( 0, items )
    
        
            
        
    
