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

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QCursor
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QHBoxLayout,
    QListWidgetItem,
    QTableWidgetItem,
    QVBoxLayout,
)

from foqus_lib.framework.sdoe import plot_utils
from foqus_lib.framework.uq.Model import Model

mypath = os.path.dirname(__file__)
_sdoePreviewUI, _sdoePreview = uic.loadUiType(os.path.join(mypath, "sdoePreview_UI.ui"))


class sdoePreview(_sdoePreview, _sdoePreviewUI):
    def __init__(
        self, data, hname, dirname, usf, nusf, irsf, scatterLabel, nImpPts, parent=None
    ):
        super(sdoePreview, self).__init__(parent)
        self.setupUi(self)
        self.data = data
        self.dirname = dirname
        self.hname = hname
        self.usf = usf
        self.nusf = nusf
        self.irsf = irsf
        self.scatterLabel = scatterLabel
        self.nImpPts = nImpPts
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
                        item = QTableWidgetItem("%g" % inputData[r][i])
                        if r >= inputData.shape[0] - numSamplesAdded:
                            item.setBackground(refinedColor)
                        self.table.setItem(r, c, item)
                    else:
                        item.setText("%g" % inputData[r][i])
                c = c + 1
                if inputType == Model.VARIABLE:
                    item = sdoePreview.listItem(inputNames[i], i)
                    self.inputList.addItem(item)
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.resizeColumnsToContents()

        QApplication.restoreOverrideCursor()

    def plotSdoe(self):
        temp = self.checkItemSelected(QListWidgetItem())
        show = []
        for item in temp:
            show.append(item.strip())
        fname = os.path.join(self.dirname, self.data.getModelName())
        hname = self.hname
        usf = self.usf
        nusf = self.nusf
        irsf = self.irsf
        scatterLabel = self.scatterLabel
        nImpPts = self.nImpPts

        if nusf:
            fig1, fig2 = plot_utils.plot(
                fname,
                scatterLabel,
                hname=hname,
                show=show,
                usf=usf,
                nusf=nusf,
                irsf=irsf,
                nImpPts=nImpPts,
            )
        else:
            fig1 = plot_utils.plot(
                fname,
                scatterLabel,
                hname=hname,
                show=show,
                usf=usf,
                nusf=nusf,
                irsf=irsf,
                nImpPts=nImpPts,
            )
            fig2 = None

        dialog = Window(fig1, fig2, self)
        if nusf:
            title = "SDoE (NUSF) Weights and Designs Visualization"
        elif usf:
            title = "SDoE (USF) Designs Visualization"
        else:
            title = "SDoE Candidates Visualization"

        dialog.setWindowTitle(title)
        dialog.show()


class Window(QDialog):
    def __init__(self, fig1, fig2, parent=None):
        super(Window, self).__init__(parent)

        # a figure instance to plot on
        self.fig1 = fig1
        if fig2 is not None:
            self.fig2 = fig2

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas1 = FigureCanvas(self.fig1)
        if fig2 is not None:
            self.canvas2 = FigureCanvas(self.fig2)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar1 = NavigationToolbar(self.canvas1, self)
        if fig2 is not None:
            self.toolbar2 = NavigationToolbar(self.canvas2, self)

        # set the layout
        layout1 = QVBoxLayout()
        layout1.addWidget(self.toolbar1)
        layout1.addWidget(self.canvas1)
        if fig2 is not None:
            main_layout = QHBoxLayout()
            layout2 = QVBoxLayout()
            layout2.addWidget(self.toolbar2)
            layout2.addWidget(self.canvas2)
            main_layout.addLayout(layout2)
            main_layout.addLayout(layout1)
            self.setLayout(main_layout)
        else:
            self.setLayout(layout1)
