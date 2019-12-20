import os

from foqus_lib.framework.uq.Model import Model
from foqus_lib.framework.sdoe import plot_utils

#from Preview_UI import Ui_Dialog

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QListWidgetItem, QAbstractItemView, \
     QApplication, QTableWidgetItem
from PyQt5.QtGui import QCursor, QColor
mypath = os.path.dirname(__file__)
_sdoePreviewUI, _sdoePreview = \
        uic.loadUiType(os.path.join(mypath, "sdoePreview_UI.ui"))


class sdoePreview(_sdoePreview, _sdoePreviewUI):
    def __init__(self, data, hname, dirname, nusf, scatterLabel, parent=None):
        super(sdoePreview, self).__init__(parent)
        self.setupUi(self)
        self.data = data
        self.dirname = dirname
        self.hname = hname
        self.nusf = nusf
        self.scatterLabel = scatterLabel
        inputTypes = data.getInputTypes()
        count = inputTypes.count(Model.FIXED)
        if count == 0:
            self.fixedInputsCheck.setHidden(True)

        self.inputList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.fixedInputsCheck.toggled.connect(self.refresh)
        self.plotSdoeButton.clicked.connect(self.plotSdoe)

        self.refresh()
        self.inputList.selectAll()

    def freeze(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

    def semifreeze(self):
        QApplication.setOverrideCursor(QCursor(Qt.BusyCursor))

    def unfreeze(self):
        QApplication.restoreOverrideCursor()

    class listItem(QListWidgetItem):
        def __init__(self, text, inputIndex):
            super(sdoePreview.listItem, self).__init__(text)
            self.inputIndex = inputIndex

        def getInputIndex(self):
            return self.inputIndex

    def selectAll(self):
        numItems = self.inputList.count()
        for i in range(numItems):
            self.inputList.item(i).setSelected(True)

    def checkItemSelected(self, item):
        items = self.inputList.selectedItems()
        itemsName = []
        for item in items:
            itemsName.append(item.text())
        return itemsName

    def refresh(self):

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        inputData = self.data.getInputData()
        inputTypes = self.data.getInputTypes()
        inputNames = self.data.getInputNames()
        numSamplesAdded = self.data.getNumSamplesAdded()

        # Set up table
        self.table.setColumnCount(self.data.getNumInputs())
        headers = []
        self.table.setRowCount(inputData.shape[0])
        showFixed = self.fixedInputsCheck.checkState()

        refinedColor = QColor(255, 255, 0, 100)

        self.inputList.clear()
        c = 0
        for i, inputName in enumerate(inputNames):
            inputType = inputTypes[i]
            if showFixed or inputType == Model.VARIABLE:
                headers.append(inputName)
                for r in range(inputData.shape[0]):
                    item = self.table.item(r, c)
                    if item is None:
                        item = QTableWidgetItem('%g' % inputData[r][i])
                        if r >= inputData.shape[0] - numSamplesAdded:
                            item.setBackground(refinedColor)
                        self.table.setItem(r, c, item)
                    else:
                        item.setText('%g' % inputData[r][i])
                c = c + 1
                if inputType == Model.VARIABLE:
                    item = sdoePreview.listItem(inputNames[i], i)
                    self.inputList.addItem(item)
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.resizeColumnsToContents()

        QApplication.restoreOverrideCursor()

    def plotSdoe(self):
        show = self.checkItemSelected(QListWidgetItem())
        fname = os.path.join(self.dirname, self.data.getModelName())
        hname = self.hname
        nusf = self.nusf
        scatterLabel = self.scatterLabel
        plot_utils.plot(fname, scatterLabel, hname=hname, show=show, nusf=nusf)
        self.setModal(True)