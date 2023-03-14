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
"""
John Eslick, Carnegie Mellon University, 2013
"""

from foqus_lib.framework.session.hhmmss import *

import numpy as np
import time
import math
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from .optMessageWindow import *
import os
from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import QWidget, QMessageBox, QVBoxLayout

mypath = os.path.dirname(__file__)
_optMonitorUI, _optMonitor = uic.loadUiType(os.path.join(mypath, "optMonitor_UI.ui"))


class noCloseWidget(QWidget):
    def __init__(self, parent=None):
        super(noCloseWidget, self).__init__(parent=parent)

    def closeEvent(self, e):
        e.ignore()


class optMonitor(_optMonitor, _optMonitorUI):
    setStatusBar = QtCore.Signal(str)
    updateGraph = QtCore.Signal()

    def __init__(self, dat, parent=None):
        """
        Constructor for model set up dialog
        """
        super(optMonitor, self).__init__(parent=parent)
        self.settingsForm = parent
        self.setupUi(self)  # Create the widgets
        self.dat = dat  # all of the session data

        self.msgSubwindow = optMessageWindow(self)
        self.plotSubwindow = noCloseWidget(self)
        self.plotSubwindow.setLayout(QVBoxLayout())
        self.coordPlotSubwindow = noCloseWidget(self)
        self.coordPlotSubwindow.setLayout(QVBoxLayout())

        self.plotSubwindow.setMaximumSize(5000, 3000)
        self.coordPlotSubwindow.setMaximumSize(5000, 3000)

        self.mdiArea.addSubWindow(self.plotSubwindow)
        self.plotSubwindow.setWindowTitle("Objective Function Plot")
        self.mdiArea.addSubWindow(self.coordPlotSubwindow)
        self.coordPlotSubwindow.setWindowTitle("Best Solution Parallel Coordinate Plot")
        self.mdiArea.addSubWindow(self.msgSubwindow)
        self.msgSubwindow.setWindowTitle("Optimization Solver Messages")

        self.startButton.clicked.connect(self.startOptimization)
        self.stopButton.clicked.connect(self.stopOptimization)
        self.msgSubwindow.clearMsgButton.clicked.connect(self.clearMessages)

        # setup plot the plots
        self.objFig = Figure(
            figsize=(600, 600),
            dpi=72,
            facecolor=(1, 1, 1),
            edgecolor=(0, 0, 0),
            tight_layout=True,
        )
        self.coordFig = Figure(
            figsize=(600, 600),
            dpi=72,
            facecolor=(1, 1, 1),
            edgecolor=(0, 0, 0),
            tight_layout=True,
        )
        self.objFigAx = self.objFig.add_subplot(211)
        self.objbestFigAx = self.objFig.add_subplot(212)
        self.coordFigAx = self.coordFig.add_subplot(111)
        self.objCanvas = FigureCanvas(self.objFig)
        self.coordCanvas = FigureCanvas(self.coordFig)
        self.plotSubwindow.layout().addWidget(self.objCanvas)
        self.objCanvas.setParent(self.plotSubwindow)
        self.coordPlotSubwindow.layout().addWidget(self.coordCanvas)
        self.coordCanvas.setParent(self.coordPlotSubwindow)
        self.timer = QtCore.QTimer(self)
        # self.connect(
        #    self.timer,
        #    QtCore.SIGNAL("timeout()"),
        #    self.updateStatus)
        self.timer.timeout.connect(self.updateStatus)
        self.updateDelay = 500
        self.delayEdit.setText(str(self.updateDelay))
        self.delayEdit.textChanged.connect(self.updateDelayChange)
        self.opt = None
        self.bestObj = 0
        self.bestCoord = None
        self.iteration = 0
        self.mdiArea.tileSubWindows()
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)

    def createMessageWindow(self):
        pass

    def createParallelAxisPlot(self):
        pass

    def createObjectivePlot(self):
        pass

    def updateDelayChange(self):
        if self.delayEdit.text() == "":
            self.updateDelay = 0
        else:
            try:
                self.updateDelay = int(float(self.delayEdit.text()))
            except:
                self.delayEdit.setText(str(self.updateDelay))

    def clearMessages(self):
        self.msgSubwindow.clearMessages()
        self.msgSubwindow.statusLine.setText("")

    def clearPlots(self):
        self.objFigAx.clear()
        self.objbestFigAx.clear()
        self.coordFigAx.clear()
        self.objFigAx.set_xlabel("Iteration")
        self.objFigAx.set_ylabel("Objective Value Solver Progression")
        self.objbestFigAx.set_xlabel("Iteration")
        self.objbestFigAx.set_ylabel("Best Objective Function Values")
        # self.objCanvas.draw()
        # self.coordCanvas.draw()

    def coordAxSetup(self):
        self.coordFigAx.clear()
        self.xnames = []
        gr = self.dat.flowsheet
        for name in self.opt.prob.v:
            self.xnames.append(name)
        self.coordFigAx.set_xlabel("Variable")
        self.coordFigAx.set_ylabel("Scaled Value")
        self.coordFigAx.set_ylim(-0.1, 10.1, auto=False)
        self.coordFigAx.set_xlim(0.75, len(self.xnames) + 0.25, auto=False)
        self.coordFigAx.set_yticks(list(range(11)))
        self.coordFigAx.set_xticks(list(range(1, len(self.xnames) + 1)))
        self.coordFigAx.set_xticklabels(self.xnames, rotation="vertical")
        self.bestX = [11] * len(self.xnames)
        self.sampLim = [[11] * len(self.xnames), [11] * len(self.xnames)]
        self.coordXCoord = list(range(1, (len(self.bestX) + 1)))
        self.coorFigLine1 = self.coordFigAx.plot(self.coordXCoord, self.bestX)
        self.coorFigLine2 = self.coordFigAx.plot(
            self.coordXCoord, self.sampLim[0], "bo"
        )
        self.coorFigLine3 = self.coordFigAx.plot(
            self.coordXCoord, self.sampLim[1], "bo"
        )

    def startOptimization(self):
        self.dat.flowsheet.generateGlobalVariables()
        pg = self.dat.optSolvers.plugins[self.dat.optProblem.solver].opt(self.dat)
        e = self.dat.optProblem.check(self.dat.flowsheet, pg.minVars, pg.maxVars)
        if not e[0] == 0:
            QMessageBox.information(
                self,
                "Error",
                "The optimization will not be started there is an error in the set up:\n"
                + e[1],
            )
            return
        self.dat.save("backupBeforeOpt.json", False)
        self.clearPlots()
        self.objCanvas.draw()
        self.settingsForm.running = True
        self.opt = self.dat.optProblem.run(self.dat)
        time.sleep(0.5)  # give the optimization function a little time to get started
        self.coordAxSetup()
        self.a = True
        self.timer.start(self.updateDelay)
        self.timeRunning = time.time()
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.setStatusBar.emit("Optimization Running")

    def stopOptimization(self):
        self.opt.terminate()

    def updateStatus(self):
        done = False
        if self.opt.updateGraph:
            self.opt.updateGraph = False
            self.updateGraph.emit()
        if not self.opt.is_alive():
            done = True
        while not self.opt.msgQueue.empty():
            msg = str(self.opt.msgQueue.get(False))
            self.msgSubwindow.msgTextBrowser.append(msg)
        bestChange = False
        itChange = False
        updateStatusLine = False
        objPoints = [[], []]
        while not self.opt.resQueue.empty():
            msg = self.opt.resQueue.get(False)
            #            print(msg)
            if msg[0] == "BEST":
                self.iteration += 1
                self.bestiter = self.iteration
                self.bestObj = msg[1][0]
                self.bestX = msg[2]
                bestChange = True
            elif msg[0] == "SAMP":
                if self.a:
                    self.samp = np.array(msg[1])
                    self.sampLim = [[0] * len(self.xnames), [10] * len(self.xnames)]
                    for i in range(len(self.xnames)):
                        self.sampLim[0][i] = np.min(self.samp[:, i])
                        self.sampLim[1][i] = np.max(self.samp[:, i])
                    bestChange = True
            elif msg[0] == "IT":
                self.iteration = msg[1]
                itChange = True
                objPoints[0].append(msg[1])
                objPoints[1].append(msg[2])
            elif msg[0] == "PROG":
                itJobsComplete = msg[1]
                itTotalJobs = msg[2]
                itErrors = msg[3]
                it = msg[4]
                totalRead = msg[5]
                totalErrors = msg[6]
                updateStatusLine = True
        if bestChange:
            self.coorFigLine1[0].set_data(self.coordXCoord, self.bestX)
            self.coorFigLine2[0].set_data(self.coordXCoord, self.sampLim[0])
            self.coorFigLine3[0].set_data(self.coordXCoord, self.sampLim[1])
            self.coordCanvas.draw()
            self.objbestFigAx.plot(self.bestiter, self.bestObj, "-bo")
            self.objCanvas.draw()
        if itChange:
            self.objFigAx.plot(objPoints[0], objPoints[1], "ro")
            self.objCanvas.draw()
        if updateStatusLine:
            self.msgSubwindow.statusLine.setText(
                "".join(
                    [
                        "ITERATION ",
                        str(it),
                        ": ",
                        str(itJobsComplete),
                        "/",
                        str(itTotalJobs),
                        "  Err: ",
                        str(itErrors),
                        " TOTAL Complete: ",
                        str(totalRead),
                        " Err:",
                        str(totalErrors),
                    ]
                )
            )
        if done:
            self.timer.stop()
            self.startButton.setEnabled(True)
            self.stopButton.setEnabled(False)
            self.setStatusBar.emit(
                "Optimization Finished, Elapsed Time: "
                + hhmmss(math.floor(time.time() - self.timeRunning))
            )
            self.settingsForm.refreshContents()
            self.settingsForm.running = False
        else:
            self.setStatusBar.emit(
                "Optimization Running, Elapsed Time: "
                + hhmmss(math.floor(time.time() - self.timeRunning))
            )
