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
"""guiHelpers.py

* This file contains some functions to help do some common things with tables
  to save time avoid mistakes.

John Eslick, Carnegie Mellon University, 2014
"""
from PyQt5 import QtCore
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QTableWidgetItem, QComboBox
import numpy
import json
import copy


def setColHeaderIntem(table, col, text=None):
    if text is None:
        text = col
    item = QTableWidgetItem(str(text))
    table.setHorizontalHeaderItem(col, item)


def setTableItem(
    table,
    row,
    col,
    text,
    check=None,
    pullDown=None,
    jsonEnc=False,
    editable=True,
    alignH=QtCore.Qt.AlignLeft,
    alignV=QtCore.Qt.AlignVCenter,
    bgColor=QColor(255, 255, 255),
    grayOdd=True,
):
    """
    Sets the contents of a cell in a table, and allows adding check
    boxes and pull-down selection boxes in cells.  Can't use check
    box and pull-down together

    table:  the table to add or update contents
    row:  the cell row
    col:  the cell column
    text:  the text to display or currently item for pulldown
    check:  if true add a check box to the column
    pullDown:  if is a list make a pulldown box
    json:  use json encoder to write text for a cell
    """
    if grayOdd and row % 2:
        # the first row is 0 (not gray) make rows darker
        red = max(bgColor.red() - 25, 0)
        green = max(bgColor.green() - 25, 0)
        blue = max(bgColor.blue() - 25, 0)
        bgColor = QColor(red, green, blue)
    item = None
    if type(text).__module__ == numpy.__name__:
        text = text.tolist()
    if pullDown == None:
        # just add text to a cell
        if jsonEnc:
            text = json.dumps(text)
        item = QTableWidgetItem(str(text))
        item.setBackground(bgColor)
        item.setTextAlignment(alignH | alignV)
        if check != None:
            if editable:
                item.setFlags(
                    QtCore.Qt.ItemIsUserCheckable
                    | QtCore.Qt.ItemIsEnabled
                    | QtCore.Qt.ItemIsEditable
                    | QtCore.Qt.ItemIsSelectable
                )
            else:
                item.setFlags(
                    QtCore.Qt.ItemIsUserCheckable
                    | QtCore.Qt.ItemIsEnabled
                    | QtCore.Qt.ItemIsSelectable
                )
            if check == True:
                item.setCheckState(QtCore.Qt.Checked)
            else:
                item.setCheckState(QtCore.Qt.Unchecked)
        else:
            if editable:
                item.setFlags(
                    QtCore.Qt.ItemIsEditable
                    | QtCore.Qt.ItemIsEnabled
                    | QtCore.Qt.ItemIsSelectable
                )
            else:
                item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        table.setItem(row, col, item)
    elif pullDown != None:
        # add a pulldown and try to set current to text
        if jsonEnc:
            pullDown = copy.copy(pullDown)
            for i, o in enumerate(pullDown):
                pullDown[i] = json.dumps(o)
            text = json.dumps(text)
        item = QComboBox()
        item.addItems(pullDown)
        i = item.findText(text)
        if i < 0:
            i = 0
        if not editable:
            item.setEnabled(False)
        item.setCurrentIndex(i)
        table.setCellWidget(row, col, item)
    return item


def cellPulldownJSON(table, row, col):
    """
    Get the current value in a pull-down cell, will cause exception
    if the is no pull-down in the cell.  Value is decoded with JSON
    """
    return json.loads(table.cellWidget(row, col).currentText())


def cellPulldownValue(table, row, col):
    """
    Get the current text in a pull-down cell, will cause exception
    if the is no pull-down in the cell
    """
    return table.cellWidget(row, col).currentText()


def cellPulldownIndex(table, row, col):
    """
    Get the current index in a pull-down cell, will cause exception
    if the is no pull-down in the cell
    """
    return table.cellWidget(row, col).currentIndex()


def cellPulldownSetIndex(table, row, col, ind):
    """
    Set the index of the selected item in a pull-down cell, will
    cause exception if the is no pull-down in the cell
    """
    table.cellWidget(row, col).setCurrentIndex(ind)


def cellPulldownSetText(table, row, col, val):
    pulldown = table.cellWidget(row, col)
    i = pulldown.findText(val)
    if i < 0:
        i = 0
    pulldown.setCurrentIndex(i)


def cellPulldownSetJSON(table, row, col, val):
    pulldown = table.cellWidget(row, col)
    text = json.dumps(val)
    i = pulldown.findText(text)
    if i < 0:
        i = 0
    pulldown.setCurrentIndex(i)


def cellPulldownSetItemsJSON(table, row, col, l=[]):
    pulldown = table.cellWidget(row, col)
    l = copy.copy(l)
    for i, el in enumerate(l):
        l[i] = json.dumps(el)
    cur = pulldown.currentText()
    pulldown.clear()
    pulldown.addItems(l)
    i = pulldown.findText(cur)
    if i < 0:
        i = 0
    pulldown.setCurrentIndex(i)


def isCellChecked(table, row, col):
    """
    Return a list the first element in True if the box is checked
    and False otherwise. The second element is the text in the cell.
    This will cause an exception if the cell doesn't contain
    a check box.
    """
    state = table.item(row, col).checkState()
    if state == QtCore.Qt.Checked:
        c = True
    else:
        c = False
    t = table.item(row, col).text()
    return [c, t]


def isChecked(table, row, col):
    state = table.item(row, col).checkState()
    if state == QtCore.Qt.Checked:
        c = True
    else:
        c = False
    return c


def setCellChecked(table, row, col, check=True):
    """
    Set the check box in a cell to True if checked = True or False
    if checked = False.
    """
    if check:
        table.item(row, col).setCheckState(QtCore.Qt.Checked)
    else:
        table.item(row, col).setCheckState(QtCore.Qt.Unchecked)


def setCellText(table, row, col, value):
    """
    Set the cells text
    """
    text = str(value)
    try:
        table.item(row, col).setText(text)
    except:
        table.setItem(row, col, QTableWidgetItem(text))


def setCellJSON(table, row, col, value):
    """
    Use json encoder on value then set the cell text to the json
    """
    text = json.dumps(value)
    try:
        table.item(row, col).setText(text)
    except:
        table.setItem(row, col, QTableWidgetItem(text))


def getCellText(table, row, col):
    """
    Return the text value in the cell
    """
    item = table.item(row, col)
    widget = table.cellWidget(row, col)
    if isinstance(widget, QComboBox):
        text = widget.currentText()
    else:
        try:
            text = item.text()
        except:
            text = ""
    return text


def getCellJSON(table, row, col):
    """
    Return the json decoded text from a cell.
    """
    try:
        text = getCellText(table, row, col)
        if text.strip().startswith("."):
            text = "0" + text
        return json.loads(text)
    except:
        return 0


def colIndexes(table):
    """
    Make a dictionary of column indexes for the header
    """
    d = dict()
    for col in range(table.columnCount()):
        d[table.horizontalHeaderItem(col).text()] = col
    return d


def addColumns(table, colNames, s=True):
    if s:
        colNames = sorted(colNames)
    for n in colNames:
        table.insertColumn(table.columnCount())
        item = QTableWidgetItem(n)
        table.setHorizontalHeaderItem(table.columnCount() - 1, item)
    return colNames
