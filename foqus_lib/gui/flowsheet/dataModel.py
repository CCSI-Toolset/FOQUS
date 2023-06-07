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
"""dataModel.py

* This is a data model for displaying flowsheet results in a table view.

John Eslick, Carnegie Mellon University, 2014
"""
from PyQt5 import QtCore
import json
import logging
import numpy as np


class dataModel(QtCore.QAbstractTableModel):
    """
    A data model for displaying flowsheet results in a QTableView
    """

    def __init__(self, results, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.results = results

    def rowCount(self, parent=QtCore.QModelIndex()):
        """
        Return the number of rows in a column
        """
        return self.results.count_rows(filtered=True)

    def columnCount(self, parent=QtCore.QModelIndex()):
        """
        Returns the number of columns in a table
        """
        return self.results.count_cols()

    def flags(self, index):
        """
        If the result header column has a set function add the
        editable flag to the cell flags.
        """
        flags = QtCore.QAbstractTableModel.flags(self, index) | QtCore.Qt.ItemIsEditable
        return flags

    def data(self, index=QtCore.QModelIndex(), role=QtCore.Qt.DisplayRole):
        """
        Return the data to display in a cell.  Should return a json
        string dump of the value.
        """
        row = self.results.get_indexes(filtered=True)[index.row()]
        col = self.results.columns[index.column()]
        if role == QtCore.Qt.DisplayRole:
            try:
                return json.dumps(self.results.loc[row, col])
            except TypeError as e:
                try:
                    x = self.results.loc[row, col]
                    if isinstance(x, np.bool_):
                        return json.dumps(bool(x))
                    else:
                        return "error {}".format(str(e))
                except:
                    return "error {}".format(str(e))
            except Exception as e:
                return "error {}".format(str(e))
        elif role == QtCore.Qt.EditRole:
            return json.dumps(self.results.loc[row, col])
        else:
            return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """
        Called to set the value of a cell.  This will edit the result
        data
        """
        row = index.row()
        col = self.results.columns[index.column()]
        if role == QtCore.Qt.EditRole:
            self.results.loc[row, col] = json.loads(value)
            return True

    def headerData(self, i, orientation, role=QtCore.Qt.DisplayRole):
        """
        Return the column headings for the horizontal header and
        index numbers for the vertical header.
        """
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.results.columns[i]
        elif orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return list(self.results.index)[i]
        else:
            return None
