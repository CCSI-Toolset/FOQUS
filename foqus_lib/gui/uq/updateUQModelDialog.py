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
import platform
import os

from foqus_lib.framework.graph.graph import *
from foqus_lib.framework.uq.flowsheetToUQModel import *
from foqus_lib.framework.uq.Model import *
from foqus_lib.framework.uq.LocalExecutionModule import *
from foqus_lib.framework.uq.ResponseSurfaces import *
from foqus_lib.framework.uq.Common import Common

from PyQt5 import uic
from PyQt5.QtWidgets import (
    QFileDialog,
    QListWidgetItem,
    QAbstractItemView,
    QDialogButtonBox,
    QDialog,
)

mypath = os.path.dirname(__file__)
_updateUQModelDialogUI, _updateUQModelDialog = uic.loadUiType(
    os.path.join(mypath, "updateUQModelDialog_UI.ui")
)


class updateUQModelDialog(_updateUQModelDialog, _updateUQModelDialogUI):
    def __init__(self, dat, parent=None):
        super(updateUQModelDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.dat = dat

        # Init options
        self.nodeRadioButton.toggled.connect(self.showNodeOption)
        self.emulatorRadioButton.toggled.connect(self.showEmulatorOption)
        nodes = sorted(dat.flowsheet.nodes.keys())
        if len(nodes) > 0:
            self.nodeRadioButton.setChecked(True)
        else:
            self.emulatorRadioButton.setChecked(True)
            self.nodeRadioButton.setEnabled(False)
        self.browseButton.clicked.connect(self.getDataFileName)
        self.outputList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.outputList.itemClicked.connect(self.checkItemSelected)

        self.show()

    class listItem(QListWidgetItem):
        def __init__(self, text, inputIndex):
            super(updateUQModelDialog.listItem, self).__init__(text)
            self.inputIndex = inputIndex

        def getInputIndex(self):
            return self.inputIndex

    def showNodeOption(self):
        if self.nodeRadioButton.isChecked():
            self.dataFileLabel.setEnabled(False)
            self.dataFileEdit.setEnabled(False)
            self.browseButton.setEnabled(False)
            self.outputLabel.setEnabled(False)
            self.outputList.setEnabled(False)
            self.fileStatsLabel.setEnabled(False)

            button = self.buttonBox.button(QDialogButtonBox.Ok)
            button.setEnabled(True)

    def showEmulatorOption(self):
        if self.emulatorRadioButton.isChecked():
            self.dataFileLabel.setEnabled(True)
            self.dataFileEdit.setEnabled(True)
            self.browseButton.setEnabled(True)

            enableSelection = len(self.dataFileEdit.text()) > 0
            self.outputLabel.setEnabled(enableSelection)
            self.outputList.setEnabled(enableSelection)
            self.fileStatsLabel.setEnabled(enableSelection)

            items = self.outputList.selectedItems()
            outputsChosen = len(items) != 0
            button = self.buttonBox.button(QDialogButtonBox.Ok)
            # print enableSelection, outputsChosen
            button.setEnabled(enableSelection and outputsChosen)

    def getDataFileName(self):
        if platform.system() == "Windows":
            allFiles = "*.*"
        else:
            allFiles = "*"
        # Get file name
        fileName, selectedFilter = QFileDialog.getOpenFileName(
            self,
            "Open Simulation Ensemble",
            "",
            "Psuade Files (*.dat *.filtered);; All files (%s)" % allFiles,
        )
        if len(fileName) == 0:
            return

        self.browseButton.setEnabled(True)
        self.outputLabel.setEnabled(True)
        self.outputList.setEnabled(True)
        self.fileStatsLabel.setEnabled(True)

        self.dataFileEdit.setText(fileName)
        data = LocalExecutionModule.readSampleFromPsuadeFile(fileName)
        self.outputList.clear()
        for i, name in enumerate(data.getOutputNames()):
            item = updateUQModelDialog.listItem(name, i)
            self.outputList.addItem(item)
        RSType = data.getSampleRSType()
        legendreOrder = None
        if RSType == ResponseSurfaces.LEGENDRE:
            legendreOrder = data.getLegendreOrder()

        statsText = "Response Surface Type: " + ResponseSurfaces.getFullName(RSType)
        if legendreOrder:
            statsText = statsText + "\nLegendre Order: " + str(legendreOrder)
        self.fileStatsLabel.setText(statsText)

    def checkItemSelected(self, item):
        items = self.outputList.selectedItems()
        enable = len(items) != 0
        button = self.buttonBox.button(QDialogButtonBox.Ok)
        # print enableSelection, outputsChosen
        button.setEnabled(enable)

    def accept(self):
        if self.nodeRadioButton.isChecked():
            self.dat.uqModel = flowsheetToUQModel(self.dat.flowsheet)
            # printUQModel(self.dat.uqModel)
        else:
            fileName = self.dataFileEdit.text()
            data = LocalExecutionModule.readSampleFromPsuadeFile(fileName)
            origOutputNames = data.getOutputNames()
            origOutputData = data.getOutputData()
            selectedItems = self.outputList.selectedItems()
            indices = []
            outputNames = []
            for item in selectedItems:
                index = item.getInputIndex()
                indices.append(index)
                outputNames.append(origOutputNames[index])
            outputData = origOutputData[:, indices]

            data.model.setRunType(Model.EMULATOR)
            data.model.setOutputNames(outputNames)
            data.model.setSelectedOutputs(list(range(len(outputNames))))
            data.model.setEmulatorOutputStatus(
                list(range(len(outputNames))), Model.NEED_TO_CALCULATE
            )
            data.setOutputData(outputData)
            fnameRoot = Common.getFileNameRoot(fileName)
            data.model.setName(fnameRoot + ".emulatorTestData")
            newFileName = fnameRoot + ".emulatorTrainData"
            data.writeToPsuade(newFileName)
            data.setEmulatorTrainingFile(newFileName)
            self.dat.uqModel = data.model
        self.done(QDialog.Accepted)

    def reject(self):
        self.done(QDialog.Rejected)
