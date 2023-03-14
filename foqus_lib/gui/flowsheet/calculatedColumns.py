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
"""dataBrowserDialog.py

* Window to show the flowsheet data browser.

John Eslick, Carnegie Mellon University, 2014
"""
import os
import logging
from PyQt5 import QtCore, QtWidgets, uic

_log = logging.getLogger("foqus.{}".format(__name__))

mypath = os.path.dirname(__file__)
_calculatedColumnsUI, _calculatedColumns = uic.loadUiType(
    os.path.join(mypath, "calculatedColumns_UI.ui")
)


def _list_item_mime_to_text(mime_data, c=False):
    if mime_data.hasText():
        return
    data = mime_data.data("application/x-qabstractitemmodeldatalist")
    if not data:
        return
    ds = QtCore.QDataStream(data)
    ds.readInt32()  # read row (don't need)
    ds.readInt32()  # read col (don't need)
    value = None
    for i in range(ds.readInt32()):
        if QtCore.Qt.ItemDataRole(ds.readInt32()) == QtCore.Qt.DisplayRole:
            value = ds.readQVariant()
            break
    if value is None:
        return
    if c:
        value = 'c("{}")'.format(value)
    else:
        value = '"{}"'.format(value)
    mime_data.setText(value)


def _canInsertFromMimeData(data):
    try:
        _list_item_mime_to_text(data, True)
        if data.hasText():
            return True
        else:
            return False
    except:
        _log.exception("Drop could not convert mime type to text")
        return False


class calculatedColumnsDialog(_calculatedColumnsUI, _calculatedColumns):
    def __init__(self, dat, parent=None):
        super(calculatedColumnsDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.dat = dat
        cols = self.dat.flowsheet.results.columns
        self.colListWidget.addItems(cols)
        self.comboBox.addItems(
            list(self.dat.flowsheet.results.calculated_columns.keys())
        )
        self.newButton.clicked.connect(self.add_dialog)
        self.delButton.clicked.connect(self.del_current)
        self.doneButton.clicked.connect(self.close)
        self.comboBox.currentIndexChanged.connect(self.select_calc)
        self.colListWidget.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)
        self.expressionEdit.canInsertFromMimeData = _canInsertFromMimeData
        self._current = self.comboBox.currentText()
        if len(self._current) < 1:
            self._current = None
        self.refreshContents()

    def closeEvent(self, event):
        self.apply_changes()
        event.accept()

    def del_current(self):
        self.dat.flowsheet.results.delete_calculation(self._current)
        self._current = None
        self.comboBox.removeItem(self.comboBox.currentIndex())

    @QtCore.pyqtSlot(int)
    def select_calc(self, i):
        name = self.comboBox.currentText()
        self._current = name
        self.refreshContents()

    def refreshContents(self):
        if self._current is None or self._current == "":
            return
        e = self.dat.flowsheet.results.calculated_columns.get(self._current, "")
        self.expressionEdit.setPlainText(e)

    def apply_changes(self):
        if self._current is None or self._current == "":
            return
        self.dat.flowsheet.results.set_calculated_column(
            self._current, self.expressionEdit.toPlainText()
        )

    def add_calc(self, name, expr=""):
        self.apply_changes()
        self._current = name
        self.comboBox.addItem(name)
        self.dat.flowsheet.results.set_calculated_column(self._current, expr)
        self.comboBox.setCurrentText(self._current)

    def add_dialog(self):
        newName, ok = QtWidgets.QInputDialog.getText(
            self, "Column Name", "New column name:"
        )
        if ok and newName != "":  # if name supplied and not canceled
            if newName in self.dat.flowsheet.results.calculated_columns:
                QtWidgets.QMessageBox.information(
                    self, "Error", "The column already exists."
                )
            else:
                self.add_calc(newName)
