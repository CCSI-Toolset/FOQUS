'''
    dataModel.py

    * This is a data model for displaying flowsheet results in a
      table view.

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
#from PySide import QtGui, QtCore
from PyQt5 import QtGui, QtCore
import json

class dataModel(QtCore.QAbstractTableModel):
    '''
        A data model for displaying flowsheet results in a QTableView
    '''
    def __init__(self, results, parent = None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.results = results

    def rowCount(self, parent=QtCore.QModelIndex()):
        '''
            Return the number of rows in a column
        '''
        return self.results.rowCount(filtered=True)

    def columnCount(self, parent=QtCore.QModelIndex()):
        '''
            Returns the number of columns in a table
        '''
        return self.results.colCount()

    def flags(self, index):
        '''
            If the result header column has a set function add the
            editable flag to the cell flags.
        '''
        flags = QtCore.QAbstractTableModel.flags(self, index) \
            |  QtCore.Qt.ItemIsEditable
        return flags

    def data(
        self, index=QtCore.QModelIndex(),
        role=QtCore.Qt.DisplayRole):
        '''
            Return the data to display in a cell.  Should return a json
            string dump of the value.
        '''
        if  role == QtCore.Qt.DisplayRole:
            try:
                return json.dumps(self.results.tableData(
                    index.row(), index.column(), filtered = True))
            except:
                return "error"
        elif role == QtCore.Qt.EditRole:
           return json.dumps(self.results.tableData(
               index.row(), index.column(), filtered = True))
        else:
            return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        '''
            Called to set the value of a cell.  This will edit the result
            data
        '''
        if role == QtCore.Qt.EditRole:
            self.results.setTableData(
                index.row(),
                index.column(),
                value,
                filtered = True)
            return True

    def headerData(self, i, orientation, role=QtCore.Qt.DisplayRole):
        '''
            Return the column headings for the horizontal header and
            index numbers for the vertical header.
        '''
        if orientation == QtCore.Qt.Horizontal and \
            role == QtCore.Qt.DisplayRole:
            return self.results.tableHeaderDataH(i)
        elif orientation == QtCore.Qt.Vertical and \
            role == QtCore.Qt.DisplayRole:
            return self.results.tableHeaderDataV(i, filtered=True)
        return None
