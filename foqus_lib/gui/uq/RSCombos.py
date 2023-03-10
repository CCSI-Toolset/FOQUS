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
import time
import numpy
from PyQt5.QtWidgets import QComboBox, QFileDialog, QSpinBox
from PyQt5.QtCore import pyqtSignal

from foqus_lib.framework.uq.LocalExecutionModule import *
from foqus_lib.framework.uq.ResponseSurfaces import *
from foqus_lib.framework.uq.RSAnalyzer import *


class RSCombo1(QComboBox):
    checkTime = None
    foundLibs = None

    def __init__(self, parent=None):
        super(RSCombo1, self).__init__(parent)
        self.combo2 = None

    def init(
        self,
        data,
        combo2,
        combo2SetFile=False,
        removeDisabled=False,
        marsBasisSpin=None,
        marsBasisCaption=None,
        marsDegreeSpin=None,
        marsDegreeCaption=None,
        odoe=False,
    ):
        # Call this after combo2 init()

        self.setEnabled(True)
        self.combo2SetFile = combo2SetFile
        self.marsBasisSpin = marsBasisSpin
        self.marsBasisCaption = marsBasisCaption
        self.marsDegreeSpin = marsDegreeSpin
        self.marsDegreeCaption = marsDegreeCaption

        nSamples = data.getNumSamples()
        nInputs = data.getNumInputs()
        self.combo2 = combo2

        rs = ["Polynomial ->", "MARS ->"]
        # rs.append(ResponseSurfaces.getFullName(ResponseSurfaces.SVM))
        rs.append(ResponseSurfaces.getFullName(ResponseSurfaces.GP))
        rs.append(ResponseSurfaces.getFullName(ResponseSurfaces.KRIGING))
        rs.append(ResponseSurfaces.getFullName(ResponseSurfaces.SOT))
        rs.append(ResponseSurfaces.getFullName(ResponseSurfaces.KNN))
        rs.append(ResponseSurfaces.getFullName(ResponseSurfaces.RBF))
        rs.append(ResponseSurfaces.getFullName(ResponseSurfaces.USER))
        # poly, mars, svm, krig, sot, knn, rbf, user = range(0, len(rs))
        poly, mars, gp, krig, sot, knn, rbf, user = list(range(0, len(rs)))
        # ... disable polynomial RS if not sufficient samples for linear regression
        disable = []
        items = [None] * len(rs)

        # Reset all items to default text and enable before disabling
        self.clear()
        self.addItems(rs)
        model = self.model()
        for i in range(len(rs)):
            # self.setItemText(i, rs[i])
            index = model.index(i, 0)
            item = model.itemFromIndex(index)
            item.setEnabled(True)
        if odoe:
            for i in range(3, 8):
                index = model.index(i, 0)
                item = model.itemFromIndex(index)
                item.setEnabled(False)
        i = poly
        if not RSAnalyzer.checkSampleSize(nSamples, nInputs, ResponseSurfaces.LINEAR):
            disable.append(i)
            order = 1
            nMinSamples = ResponseSurfaces.getPolynomialMinSampleSize(nInputs, order)
            items[i] = "%s (Requires at least %d samples)" % (rs[i], nMinSamples)
        # ... disable non-polynomial RS if nSamples < 100 or not installed
        currentTime = time.time()
        if RSCombo1.foundLibs == None or currentTime - RSCombo1.checkTime > 10:
            RSCombo1.foundLibs = LocalExecutionModule.getPsuadeInstalledModules()
            RSCombo1.checkTime = currentTime
        foundMARS = RSCombo1.foundLibs.get("MARS", False)
        # foundSVM = RSCombo1.foundLibs.get('SVM', False)
        i = mars
        if not foundMARS:
            disable.append(i)
            items[i] = "%s (Not installed)" % rs[i][:-3]
        elif nSamples < 50:
            disable.append(i)
            items[i] = "%s (Requires at least 50 samples)" % rs[i][:-3]
        # i = svm
        # if not foundSVM:
        #     disable.append(i)
        #     items[i] = '%s (Not installed)' % rs[i]
        # else:
        #     if nSamples < 100:
        #         disable.append(i)
        #         items[i] = '%s (Requires at least 100 samples)' % rs[i]
        i = krig
        if nSamples < 10:
            disable.append(i)
            items[i] = "%s (Requires at least 10 samples)" % rs[i]
        if removeDisabled:
            disable.reverse()
            for i in disable:
                self.removeItem(i)
        else:
            for i in disable:
                self.setItemText(i, items[i])
                model = self.model()
                index = model.index(i, 0)
                item = model.itemFromIndex(index)
                item.setEnabled(False)
        if len(disable) == len(rs):
            self.setEnabled(False)
            combo2.showNothing()
        else:
            # enableSet = set([poly, mars, svm, krig, sot, knn, rbf, user]) - set(disable)
            enableSet = set([poly, mars, gp, krig, sot, knn, rbf, user]) - set(disable)
            enableFirstItem = min(enableSet)
            showMarsWidgets = False
            # populate combo2 as needed
            if poly == enableFirstItem:
                combo2.showPolynomial()
            elif mars == enableFirstItem:
                combo2.showMars()
                showMarsWidgets = True
            else:
                combo2.showNothing()

            if not removeDisabled:
                self.setCurrentIndex(enableFirstItem)
            self.setEnabled(True)
            for widget in [
                marsBasisSpin,
                marsBasisCaption,
                marsDegreeSpin,
                marsDegreeCaption,
            ]:
                if widget is not None:
                    widget.setEnabled(showMarsWidgets)

        self.currentIndexChanged[int].connect(self.change)

    def change(self):
        if self.combo2 == None:
            raise RuntimeError("Not initialized properly")
        rs = self.currentText()
        if rs.startswith("Polynomial"):
            self.combo2.showPolynomial()
        elif rs.startswith("MARS"):
            self.combo2.showMars()
        elif (
            rs == ResponseSurfaces.getFullName(ResponseSurfaces.USER)
            and self.combo2SetFile
        ):
            self.combo2.showFiles()
        else:
            self.combo2.showNothing()

        # show Mars components
        showMarsWidgets = rs.startswith("MARS")
        for widget in [
            self.marsBasisSpin,
            self.marsBasisCaption,
            self.marsDegreeSpin,
            self.marsDegreeCaption,
        ]:
            if widget is not None:
                widget.setEnabled(showMarsWidgets)


class RSCombo2(QComboBox):
    userFiles = []
    fileAdded = pyqtSignal()

    def __init__(self, parent=None):
        super(RSCombo2, self).__init__(parent)
        self.data = None
        self.legendreSpin = None
        self.legendreCaption = None
        self.useShortNames = False
        self.fileMode = False
        self.odoe = False

    def init(
        self, data, legendreSpin, legendreCaption=None, useShortNames=False, odoe=False
    ):
        self.data = data
        self.legendreSpin = legendreSpin
        self.legendreCaption = legendreCaption
        self.useShortNames = useShortNames
        self.odoe = odoe

        self.currentIndexChanged[int].connect(self.change)
        self.isSetFileSignal = False

    def showPolynomial(self):
        self.fileMode = False
        if self.receivers(self.currentIndexChanged[int]) > 0 and self.isSetFileSignal:
            self.currentIndexChanged[int].disconnect(self.setFile)
        if self.data == None:
            raise RuntimeError("Not initialized properly")
        self.clear()
        enable = self.checkPolynomialRS()
        for poly in enable:
            s = ResponseSurfaces.getFullName(poly)
            if self.useShortNames:
                s = s.replace(" Regression", "")
                s = s.replace(" Polynomial", "")
            self.addItem(s)
        self.setCurrentIndex(0)
        self.setEnabled(True)

    def checkPolynomialRS(self):
        data = self.data
        data = data.getValidSamples()  # filter out samples that have no output results
        nSamples = data.getNumSamples()
        nInputs = data.getNumInputs()

        polyRS = [
            ResponseSurfaces.LINEAR,
            ResponseSurfaces.QUADRATIC,
            ResponseSurfaces.CUBIC,
            ResponseSurfaces.QUARTIC,
        ]
        enable = []
        for rs in polyRS:
            if RSAnalyzer.checkSampleSize(nSamples, nInputs, rs):
                enable.append(rs)
        rs = ResponseSurfaces.LEGENDRE
        if RSAnalyzer.checkSampleSize(nSamples, nInputs, rs, legendreOrder=1):
            enable.append(rs)

        if self.odoe:
            enable = [
                ResponseSurfaces.LINEAR,
                ResponseSurfaces.QUADRATIC,
                ResponseSurfaces.CUBIC,
            ]
        return enable

    def showMars(self):
        if self.receivers(self.currentIndexChanged[int]) > 0 and self.isSetFileSignal:
            self.currentIndexChanged[int].disconnect(self.setFile)
        self.clear()
        self.addItem(ResponseSurfaces.getFullName(ResponseSurfaces.MARS))
        if self.useShortNames:
            self.addItem("With Bagging")
        else:
            self.addItem(ResponseSurfaces.getFullName(ResponseSurfaces.MARSBAG))
        self.setEnabled(True)
        if self.odoe:
            self.removeItem(1)
        self.enableLegendre(False)
        self.fileMode = False

    def showFiles(self):
        self.fileMode = True
        self.refresh()
        self.currentIndexChanged[int].connect(self.setFile)
        self.isSetFileSignal = True
        self.setEnabled(True)

    def setFile(self):
        text = self.currentText()
        if text == "Browse...":
            fname, selectedFilter = QFileDialog.getOpenFileName(
                self, "Browse to sample file:", "", "Python files (*.py)"
            )
            if len(fname) == 0:  # Cancelled
                self.setCurrentIndex(0)
                return
            elif fname in self.userFiles:
                index = self.userFiles.index(fname) + 1
                self.setCurrentIndex(index)
            else:
                self.userFiles.append(fname)
                index = self.count() - 1
                self.setCurrentIndex(0)  # Prevent calling twice with Browse...
                self.insertItem(index, os.path.basename(fname))
                self.setCurrentIndex(index)
                self.fileAdded.emit()

    def refresh(self):
        if self.fileMode:
            index = self.currentIndex()
            items = ["Select File"]
            items.extend([os.path.basename(f) for f in self.userFiles])
            items.append("Browse...")
            self.clear()
            self.addItems(items)
            self.setCurrentIndex(index)
            self.setEnabled(True)

    def getFile(self):
        index = self.currentIndex()
        return self.userFiles[index - 1]

    def showNothing(self):
        if self.receivers(self.currentIndexChanged[int]) > 0 and self.isSetFileSignal:
            self.currentIndexChanged[int].disconnect(self.setFile)
        self.clear()
        self.setEnabled(False)
        self.enableLegendre(False)
        self.fileMode = False

    def change(self):
        # self.legendreSpin.setValue(1)
        rs = self.currentText()
        self.enableLegendre(rs.startswith("Legendre"))

    def enableLegendre(self, enable):
        if self.legendreCaption is not None:
            self.legendreCaption.setEnabled(enable)
        self.legendreSpin.setEnabled(enable)


class MarsBasisSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super(MarsBasisSpinBox, self).__init__(parent)

    def init(self, data):
        nSamples = data.getNumSamples()
        self.setRange(min([50, nSamples]), nSamples)
        self.setValue(min([100, nSamples]))


class MarsDegreeSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super(MarsDegreeSpinBox, self).__init__(parent)

    def init(self, data):
        nVarInputs = data.getNumVarInputs()
        self.setRange(min([2, nVarInputs]), nVarInputs)
        self.setValue(min([8, nVarInputs]))


class LegendreSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super(LegendreSpinBox, self).__init__(parent)

    def init(self, data):
        data = data.getValidSamples()  # filter out samples that have no output results
        nSamples = data.getNumSamples()
        nInputs = data.getNumInputs()

        maxOrder = ResponseSurfaces.getLegendreMaxOrder(nInputs, nSamples)
        self.setRange(1, maxOrder)
        self.setSingleStep(1)
        self.setValue(1)
        self.setEnabled(False)


def lookupRS(combo1, combo2):
    rs1 = combo1.currentText()
    rs2 = combo2.currentText()

    otherRS = []
    # otherRS.append(ResponseSurfaces.getFullName(ResponseSurfaces.SVM))
    otherRS.append(ResponseSurfaces.getFullName(ResponseSurfaces.GP))
    otherRS.append(ResponseSurfaces.getFullName(ResponseSurfaces.KRIGING))
    otherRS.append(ResponseSurfaces.getFullName(ResponseSurfaces.SOT))
    otherRS.append(ResponseSurfaces.getFullName(ResponseSurfaces.KNN))
    otherRS.append(ResponseSurfaces.getFullName(ResponseSurfaces.RBF))
    otherRS.append(ResponseSurfaces.getFullName(ResponseSurfaces.USER))
    if rs1.startswith("Polynomial") or rs1.startswith("MARS"):
        if "Legendre" in rs2:
            rs = ResponseSurfaces.getPsuadeName(ResponseSurfaces.LEGENDRE)
        elif rs2.endswith("Bagging"):
            rs = ResponseSurfaces.getPsuadeName(ResponseSurfaces.MARSBAG)
        else:
            if rs2 not in ResponseSurfaces.fullNames:
                rs2 += " Regression"
            rs = ResponseSurfaces.getPsuadeName(ResponseSurfaces.getEnumValue(rs2))
    elif rs1 in otherRS:
        rs = ResponseSurfaces.getPsuadeName(ResponseSurfaces.getEnumValue(rs1))
    else:
        rs = None

    return rs
