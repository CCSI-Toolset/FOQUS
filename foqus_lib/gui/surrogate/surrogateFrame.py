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
"""surrogateFrame.py

* This frame is a container for surrogate model forms
* It also contains things common to all surrogate methods
    - Data selection
    - Subgraph selection

John Eslick, Carnegie Mellon University, 2014
"""

import time
import math
import traceback
import os
import shutil
from foqus_lib.gui.flowsheet.dataBrowserFrame import *
import foqus_lib.gui.helpers.guiHelpers as gh
from foqus_lib.framework.session.hhmmss import *
from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QTableWidget
from PyQt5.QtGui import QColor
from PyQt5 import uic

mypath = os.path.dirname(__file__)
_surrogateFrameUI, _surrogateFrame = uic.loadUiType(
    os.path.join(mypath, "surrogateFrame_UI.ui")
)


class surrogateFrame(_surrogateFrame, _surrogateFrameUI):
    """
    This is the frame for setting up surrogate model methods
    """

    setStatusBar = QtCore.pyqtSignal(str)

    def __init__(self, dat, parent=None):
        """ """
        super(surrogateFrame, self).__init__(parent=parent)
        self.mainWin = parent
        self.setupUi(self)
        self.dat = dat
        self.blockapply = False
        self.tools = sorted(
            list(dat.surrogateMethods.plugins.keys()), key=lambda s: s.lower()
        )
        self.toolSelectBox.clear()
        self.toolSelectBox.addItems(self.tools)
        self.createOptionsTables()
        self.toolSelectBox.currentIndexChanged.connect(self.selectTool)
        self.toolBox.setCurrentIndex(1)
        self.dataBrowser = dataBrowserFrame(dat, self.toolBox.currentWidget())
        self.dataBrowser.editFiltersButton.clicked.connect(self.updateFilters)
        self.toolBox.currentWidget().layout().addWidget(self.dataBrowser)
        self.runButton.clicked.connect(self.run)
        self.inputCols = gh.colIndexes(self.inputTable)
        self.outputCols = gh.colIndexes(self.outputTable)
        self.refreshContents()
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.updateStatus)
        self.updateDelay = 500
        self.runButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.stopButton.clicked.connect(self.stop)
        self.addAllInButton.clicked.connect(self.selectAllInputs)
        self.addAllOutButton.clicked.connect(self.selectAllOutputs)
        self.delAllInButton.clicked.connect(self.selectNoInputs)
        self.delAllOutButton.clicked.connect(self.selectNoOutputs)
        self.ivGeneralButton1.clicked.connect(self.ivGeneralButton1Click)
        self.ivGeneralButton2.clicked.connect(self.ivGeneralButton2Click)
        self.ovGeneralButton1.clicked.connect(self.ovGeneralButton1Click)
        self.ovGeneralButton2.clicked.connect(self.ovGeneralButton2Click)
        self.addSamplesButton.clicked.connect(self.addSamples)
        self.prevTool = None
        try:
            self.selectTool(0)
        except:
            pass
        self.toolBox.setCurrentIndex(0)

    def selectAllInputs(self):
        table = self.inputTable
        for row in range(table.rowCount()):
            gh.setCellChecked(table, row, 0, check=True)

    def selectAllOutputs(self):
        table = self.outputTable
        for row in range(table.rowCount()):
            if gh.getCellText(table, row, 0) != "graph.error":
                gh.setCellChecked(table, row, 0, check=True)

    def selectNoInputs(self):
        table = self.inputTable
        for row in range(table.rowCount()):
            gh.setCellChecked(table, row, 0, check=False)

    def selectNoOutputs(self):
        table = self.outputTable
        for row in range(table.rowCount()):
            gh.setCellChecked(table, row, 0, check=False)

    def clearOld(self):
        """
        Clear old run messages.
        """
        self.monitorTextBox.setPlainText("")

    def stop(self):
        self.pg.terminate()

    def run(self):
        """
        Start making the surrogate models
        """
        self.monitorTextBox.setPlainText("")
        self.applyChanges()
        self.toolBox.setCurrentIndex(4)
        if self.dat.surrogateProblem == None:
            return
        tool = self.toolSelectBox.currentText()
        pg = self.dat.surrogateMethods.plugins[tool].surrogateMethod(self.dat)
        pg.loadDict(self.dat.surrogateProblem[tool])
        pg.start()
        self.pg = pg
        self.a = True
        self.timer.start(self.updateDelay)
        self.timeRunning = time.time()
        self.runButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.setStatusBar.emit("Surrogate Generation Running")

    def addSamples(self):
        n0 = len(self.dat.uqSimList)
        self.mainWin.uqSetupFrame.runsFinishedSignal.connect(self.refreshData)
        self.mainWin.uqSetupFrame.addSimulation()
        n1 = len(self.dat.uqSimList)
        if n1 - n0 == 1:
            # get launch button row and column
            row = n1 - 1
            col = self.mainWin.uqSetupFrame.launchCol
            # get launch button
            lb = self.mainWin.uqSetupFrame.simulationTable.cellWidget(row, col)
            lb.clicked.emit()
        wd = self.dat.foqusSettings.working_dir
        src_psuade_data_file = os.path.join(wd, "psuadeData")
        # dest_psuade_data_file = os.path.join(
        #    iREVEAL_work_dir, 'psuadeData')
        # shutil.copyfile(src_psuade_data_file, dest_psuade_data_file)
        src_psuade_in_file = os.path.join(wd, "psuade.in")
        # dest_psuade_in_file = os.path.join(iREVEAL_work_dir, 'psuade.in')
        # shutil.copyfile(src_psuade_in_file, dest_psuade_in_file)
        self.refreshData()

    def refreshData(self):
        self.dataBrowser.refreshContents()

    def selectTool(self, i):
        """
        This is called to when the tool pull down is used to select
        a different tool
        """
        tool = self.toolSelectBox.currentText()
        self.applyChanges(tool=self.prevTool)
        self.prevTool = tool
        pg = self.dat.surrogateMethods.plugins[tool].surrogateMethod(self.dat)
        self.dat.surrogateCurrent = pg.name
        self.settingsStack.setCurrentIndex(i)
        self.methodDescriptionBox.setHtml(pg.methodDescription)
        self.refreshContents()

    def updateFilters(self):
        self.applyChanges()
        self.refreshContents()

    def createOptionsTables(self):
        """
        Get the options for all the surrogate method plugins and
        make oftion tables for them.  These go into a stack
        widget that switches when you change the tool selection
        """
        self.optTable = {}
        for tool in self.tools:
            pg = self.dat.surrogateMethods.plugins[tool].surrogateMethod(self.dat)
            self.optTable[tool] = QTableWidget(self)
            self.settingsStack.addWidget(self.optTable[tool])
            self.optTable[tool].setColumnCount(3)
            self.optTable[tool].setHorizontalHeaderLabels(
                ["Setting Name", "Value", "Description"]
            )
            self.optTable[tool].setRowCount(len(pg.options.order))
            for i, opt in enumerate(pg.options.order):
                gh.setTableItem(self.optTable[tool], i, 0, opt, editable=False)
                gh.setTableItem(
                    self.optTable[tool], i, 2, pg.options[opt].desc, editable=False
                )
                pg.options[opt].dtype
                if pg.options[opt].dtype == bool:
                    # If the option is bool type use a check box
                    gh.setTableItem(
                        self.optTable[tool],
                        i,
                        1,
                        "",
                        check=pg.options[opt].value,
                        jsonEnc=False,
                        bgColor=QColor(235, 255, 235),
                    )
                elif len(pg.options[opt].validValues) > 0:
                    # if is a list type use a combo box
                    gh.setTableItem(
                        self.optTable[tool],
                        i,
                        1,
                        pg.options[opt].default,
                        jsonEnc=True,
                        pullDown=pg.options[opt].validValues,
                        bgColor=QColor(235, 255, 235),
                    )
                else:
                    # Otherwise you just have to type
                    gh.setTableItem(
                        self.optTable[tool],
                        i,
                        1,
                        pg.options[opt].value,
                        jsonEnc=True,
                        bgColor=QColor(235, 255, 235),
                    )
            self.optTable[tool].resizeColumnsToContents()
        self.settingsStack.setCurrentIndex(0)

    def ivGeneralButton1Click(self):
        self.applyChanges()
        tool = self.toolSelectBox.currentText()
        pg = self.dat.surrogateMethods.plugins[tool].surrogateMethod(self.dat)
        pg.loadFromSession()
        pg.updateOptions()
        pg.inputVarButtons[0][1]()
        self.refreshContents()

    def ivGeneralButton2Click(self):
        self.applyChanges()
        tool = self.toolSelectBox.currentText()
        pg = self.dat.surrogateMethods.plugins[tool].surrogateMethod(self.dat)
        pg.loadFromSession()
        pg.updateOptions()
        pg.inputVarButtons[1][1]()
        self.refreshContents()

    def ovGeneralButton1Click(self):
        self.applyChanges()
        tool = self.toolSelectBox.currentText()
        pg = self.dat.surrogateMethods.plugins[tool].surrogateMethod(self.dat)
        pg.loadFromSession()
        pg.updateOptions()
        pg.outputVarButtons[0][1]()
        self.refreshContents()

    def ovGeneralButton2Click(self):
        self.applyChanges()
        tool = self.toolSelectBox.currentText()
        pg = self.dat.surrogateMethods.plugins[tool].surrogateMethod(self.dat)
        pg.loadFromSession()
        pg.updateOptions()
        pg.outputVarButtons[1][1]()
        self.refreshContents()

    def refreshContents(self):
        """
        Update the contents of the surrogate for to reflect the
        current state of the foqus session.
        """
        self.ivGeneralButton1.hide()
        self.ivGeneralButton2.hide()
        self.ovGeneralButton1.hide()
        self.ovGeneralButton2.hide()
        self.dataBrowser.refreshContents()
        inputNames = self.dat.flowsheet.input.compoundNames()
        self.dat.flowsheet.markConnectedInputs()
        delList = []
        for i in range(len(inputNames)):
            if self.dat.flowsheet.input.get(inputNames[i]).con == True:
                delList.append(inputNames[i])
        for n in delList:
            inputNames.remove(n)
        outputNames = self.dat.flowsheet.output.compoundNames()
        if self.dat.surrogateCurrent is not None:
            i = self.toolSelectBox.findText(self.dat.surrogateCurrent)
            if i >= 0:
                self.blockapply = True
                self.toolSelectBox.setCurrentIndex(i)
                self.blockapply = False
        tool = self.toolSelectBox.currentText()
        if tool == "":
            return
        pg = self.dat.surrogateMethods.plugins[tool].surrogateMethod(self.dat)
        pg.loadFromSession()
        pg.updateOptions()

        for i, btn in enumerate(pg.inputVarButtons):
            # this is because I am beeing lazy there are two
            # preexisting buttons
            if i == 0:
                self.ivGeneralButton1.setText(btn[0])
                self.ivGeneralButton1.show()
            elif i == 1:
                self.ivGeneralButton2.setText(btn[0])
                self.ivGeneralButton2.show()

        for i, btn in enumerate(pg.outputVarButtons):
            if i == 0:
                self.ovGeneralButton1.setText(btn[0])
                self.ovGeneralButton1.show()
            elif i == 1:
                self.ovGeneralButton2.setText(btn[0])
                self.ovGeneralButton2.show()

        for i in range(self.optTable[tool].rowCount()):
            oname = gh.getCellText(self.optTable[tool], i, 0)
            if oname in pg.options:
                if pg.options[oname].dtype == bool:
                    gh.setCellChecked(
                        self.optTable[tool], i, 1, pg.options[oname].value
                    )
                elif len(pg.options[oname].validValues) > 0:
                    gh.cellPulldownSetItemsJSON(
                        self.optTable[tool], i, 1, pg.options[oname].validValues
                    )
                    gh.cellPulldownSetJSON(
                        self.optTable[tool], i, 1, pg.options[oname].value
                    )
                else:
                    gh.setCellJSON(self.optTable[tool], i, 1, pg.options[oname].value)
        self.inputTable.setRowCount(0)
        self.inputTable.setColumnCount(3 + len(pg.inputCols))
        for i, item in enumerate(pg.inputCols):
            gh.setColHeaderIntem(self.inputTable, i + 3, item[0])
        self.outputTable.setRowCount(0)
        self.outputTable.setColumnCount(1 + len(pg.outputCols))
        for i, item in enumerate(pg.outputCols):
            gh.setColHeaderIntem(self.outputTable, i + 1, item[0])
        self.inputTable.setRowCount(len(inputNames))
        self.outputTable.setRowCount(len(outputNames))
        self.inputCols = gh.colIndexes(self.inputTable)
        self.outputCols = gh.colIndexes(self.outputTable)
        for i in range(len(inputNames)):
            var = self.dat.flowsheet.input.get(inputNames[i])
            gh.setTableItem(
                self.inputTable,
                row=i,
                col=self.inputCols["Name"],
                text=inputNames[i],
                check=inputNames[i] in pg.input,
                editable=False,
            )
            gh.setTableItem(
                self.inputTable,
                row=i,
                col=self.inputCols["Max"],
                text=var.max,
                jsonEnc=True,
            )
            gh.setTableItem(
                self.inputTable,
                row=i,
                col=self.inputCols["Min"],
                text=var.min,
                jsonEnc=True,
            )
            for item in pg.inputCols:
                val = pg.getInputVarOption(item[0], inputNames[i])
                gh.setTableItem(
                    self.inputTable,
                    row=i,
                    col=self.inputCols[item[0]],
                    text=val,
                    jsonEnc=True,
                )
        for i in range(len(outputNames)):
            var = self.dat.flowsheet.output.get(outputNames[i])
            gh.setTableItem(
                self.outputTable,
                row=i,
                col=self.outputCols["Name"],
                text=outputNames[i],
                check=outputNames[i] in pg.output,
                editable=False,
            )
            for item in pg.outputCols:
                val = pg.getOutputVarOption(item[0], outputNames[i])
                gh.setTableItem(
                    self.outputTable,
                    row=i,
                    col=self.outputCols[item[0]],
                    text=val,
                    jsonEnc=True,
                )
        self.inputTable.resizeColumnsToContents()
        self.outputTable.resizeColumnsToContents()

    def applyChanges(self, tool=None):
        """
        Save surrogate model setup in foqus session
        """
        if self.blockapply:
            return
        if tool is None:
            tool = self.toolSelectBox.currentText()
        pg = self.dat.surrogateMethods.plugins[tool].surrogateMethod(self.dat)
        inputs = []
        outputs = []
        dataFilter = self.dataBrowser.filterSelectBox.currentText()
        if dataFilter == "":
            dataFilter = None
        # inputs and input var options
        for i in range(self.inputTable.rowCount()):
            c = gh.isCellChecked(self.inputTable, i, 0)
            var = self.dat.flowsheet.input.get(c[1])
            var.setMin(gh.getCellJSON(self.inputTable, i, self.inputCols["Min"]))
            var.setMax(gh.getCellJSON(self.inputTable, i, self.inputCols["Max"]))
            if c[0]:
                inputs.append(c[1])
                for item in pg.inputCols:
                    col = self.inputCols[item[0]]
                    val = gh.getCellJSON(self.inputTable, i, col)
                    pg.setInputVarOption(item[0], c[1], val)
        # outputs and output var options
        for i in range(self.outputTable.rowCount()):
            c = gh.isCellChecked(self.outputTable, i, 0)
            if c[0]:
                outputs.append(c[1])
                for item in pg.outputCols:
                    col = self.outputCols[item[0]]
                    val = gh.getCellJSON(self.outputTable, i, col)
                    pg.setOutputVarOption(item[0], c[1], val)
        pg.input = inputs
        pg.output = outputs
        pg.dataFilter = dataFilter
        for i in range(self.optTable[tool].rowCount()):
            optName = gh.getCellText(self.optTable[tool], i, 0)
            if pg.options[optName].dtype == bool:
                optValue = gh.isChecked(self.optTable[tool], i, 1)
            elif len(pg.options[optName].validValues) > 0:
                optValue = gh.cellPulldownJSON(self.optTable[tool], i, 1)
            else:
                optValue = gh.getCellJSON(self.optTable[tool], i, 1)
            pg.options[optName].value = optValue
        pg.saveInSession()
        self.dat.surrogateCurrent = pg.name

    def updateStatus(self):
        """
        This function is called by the timer periodically and
        updates the surrogate generation status.  If finished it
        also stops the timer and resests the start/stop buttons.
        """
        done = False
        if not self.pg.is_alive():
            done = True
        while not self.pg.msgQueue.empty():
            msg = str(self.pg.msgQueue.get(False))
            self.monitorTextBox.append(msg)
        if done:
            self.timer.stop()
            self.pg.join()
            self.runButton.setEnabled(True)
            self.stopButton.setEnabled(False)
            if self.pg.ex:
                etype, evalue, etrace = self.pg.ex
                el = traceback.format_exception(etype, evalue, etrace)
                for line in el:
                    self.monitorTextBox.append(line)
                self.setStatusBar.emit(
                    "Surrogate Failed Elapsed Time: {0}".format(
                        hhmmss(math.floor(time.time() - self.timeRunning))
                    )
                )
            else:
                self.setStatusBar.emit(
                    "Surrogate Finished, Elapsed Time: {0}".format(
                        hhmmss(math.floor(time.time() - self.timeRunning))
                    )
                )
            if self.pg.driverFile != "":
                try:
                    df = os.path.abspath(self.pg.driverFile)
                except:
                    pass
                msgBox = QMessageBox()
                msgBox.setWindowTitle("Driver File Location")
                msgBox.setText(
                    "The surrogate model driver file path is: {0}".format(
                        os.path.abspath(df)
                    )
                )
                msgBox.exec_()
        else:
            self.refreshContents()
            self.setStatusBar.emit(
                "Surrogate Model Generation, Elapsed Time: {0}s".format(
                    math.floor(time.time() - self.timeRunning)
                )
            )
