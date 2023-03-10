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
import sys
import os

from foqus_lib.framework.uq.Model import Model
from foqus_lib.framework.uq.SampleData import SampleData
from foqus_lib.framework.uq.Visualizer import Visualizer
from foqus_lib.framework.uq.Common import *
from foqus_lib.framework.uq.RSInference import RSInferencer

# from Preview_UI import Ui_Dialog

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFileDialog,
    QListWidgetItem,
    QAbstractItemView,
    QDialogButtonBox,
    QApplication,
    QTableWidgetItem,
)
from PyQt5.QtGui import QCursor, QColor

mypath = os.path.dirname(__file__)
_PreviewUI, _Preview = uic.loadUiType(os.path.join(mypath, "Preview_UI.ui"))


class Preview(_Preview, _PreviewUI):
    def __init__(self, data, parent=None):
        super(Preview, self).__init__(parent)
        self.setupUi(self)
        self.data = data

        inputTypes = data.getInputTypes()
        count = inputTypes.count(Model.FIXED)
        if count == 0:
            self.fixedInputsCheck.setHidden(True)

        self.inputList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.inputList.itemClicked.connect(self.checkItemSelected)
        self.fixedInputsCheck.toggled.connect(self.refresh)
        self.graph1DButton.clicked.connect(self.graph1D)
        self.graph2DDistButton.clicked.connect(self.graph2DDist)
        self.graph2DScatterButton.clicked.connect(self.graph2DScatter)
        self.checkItemSelected(QListWidgetItem())  # Enable or disable graph button

        self.refresh()

    def freeze(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

    def semifreeze(self):
        QApplication.setOverrideCursor(QCursor(Qt.BusyCursor))

    def unfreeze(self):
        QApplication.restoreOverrideCursor()

    class listItem(QListWidgetItem):
        def __init__(self, text, inputIndex):
            super(Preview.listItem, self).__init__(text)
            self.inputIndex = inputIndex

        def getInputIndex(self):
            return self.inputIndex

    def checkItemSelected(self, item):
        items = self.inputList.selectedItems()
        enable = len(items) != 0
        self.graph1DButton.setEnabled(enable)
        self.graph2DDistButton.setEnabled(enable)
        enable = len(items) == 2
        self.graph2DScatterButton.setEnabled(enable)

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
                        item = QTableWidgetItem("%g" % inputData[r][i])
                        if r >= inputData.shape[0] - numSamplesAdded:
                            item.setBackground(refinedColor)
                        self.table.setItem(r, c, item)
                    else:
                        item.setText("%g" % inputData[r][i])
                c = c + 1
                if inputType == Model.VARIABLE:
                    item = Preview.listItem(inputNames[i], i)
                    self.inputList.addItem(item)
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.resizeColumnsToContents()

        QApplication.restoreOverrideCursor()

    def graph1D(self):
        selected = self.inputList.selectedItems()
        indices = [0] * len(selected)
        for i, item in enumerate(selected):
            indices[i] = item.getInputIndex() + 1
        self.data.writeToPsuade("previewData")
        Common.initFolder(Visualizer.dname)
        # self.setModal(False)

        # number of samples added from adaptive sampling
        numSamplesAdded = self.data.getNumSamplesAdded()
        newSamples = None
        if numSamplesAdded > 0:
            numSamples = self.data.getNumSamples()
            samples = list(range(numSamples))
            k = numSamples - numSamplesAdded
            newSamples = samples[k:]

        # plot
        cmd = "iplot1"
        Visualizer.xScatter("previewData", indices, cmd, newSamples)
        # self.setModal(False)

    def graph2DDist(self):
        self.freeze()
        inputNames = self.data.getInputNames()

        indices = [
            index.row() for index in self.inputList.selectionModel().selectedIndexes()
        ]

        self.data.writeToPsuade("previewData")
        Common.initFolder(Visualizer.dname)
        self.setModal(False)

        mfile = RSInferencer.genheatmap("previewData")
        RSInferencer.infplot_prior(mfile, "previewData", indices)
        self.setModal(True)
        self.unfreeze()

    def graph2DScatter(self):
        inputNames = self.data.getInputNames()

        # Need indices corresponding to data, not just list
        selected = self.inputList.selectedItems()
        indices = [0] * len(selected)
        for i, item in enumerate(selected):
            indices[i] = item.getInputIndex() + 1

        self.data.writeToPsuade("previewData")
        Common.initFolder(Visualizer.dname)
        self.setModal(False)

        # number of samples added from adaptive sampling
        numSamplesAdded = self.data.getNumSamplesAdded()

        newSamples = None
        if numSamplesAdded > 0:
            numSamples = self.data.getNumSamples()
            samples = list(range(numSamples))
            k = numSamples - numSamplesAdded
            newSamples = samples[k:]

        # plot
        cmd = "iplot2"
        Visualizer.xScatter("previewData", indices, cmd, newSamples)
        self.setModal(True)
