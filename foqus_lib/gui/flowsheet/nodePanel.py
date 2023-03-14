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
"""nodePanel.py
* This is a node editor widget

John Eslick, Carnegie Mellon University, 2014
"""
import os
import types
import platform
from configparser import RawConfigParser
from io import StringIO
import ast

from foqus_lib.gui.dialogs.tagSelectDialog import *
from foqus_lib.framework.graph.node import *
from foqus_lib.framework.graph.node import *
import foqus_lib.gui.helpers.guiHelpers as gh
from foqus_lib.gui.pysyntax_hl.pysyntax_hl import *
from foqus_lib.framework.uq.Distribution import Distribution

from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QLineEdit, QAbstractItemView
from PyQt5.QtGui import QColor

mypath = os.path.dirname(__file__)
_nodeDockUI, _nodeDock = uic.loadUiType(os.path.join(mypath, "nodePanel_UI.ui"))


class nodeDock(_nodeDock, _nodeDockUI):
    redrawFlowsheet = QtCore.pyqtSignal()  # request flowsheet redraw
    waiting = QtCore.pyqtSignal()  # indicates a task is going take a while
    notwaiting = QtCore.pyqtSignal()  # indicates a wait is over

    def __init__(self, dat, parent=None):
        """
        Node view/edit dock widget constructor
        """
        super(nodeDock, self).__init__(parent=parent)
        self.setupUi(self)
        self.dat = dat
        self.mw = parent
        self.show()
        self.updateColIndexes()
        self.nodeName = ""
        self.node = None
        self.vcats = [
            "Fixed",
            "Variable, Opt Only",
            "Variable, UQ Only",
            "Variable, Opt + UQ",
        ]
        self.applyButton.clicked.connect(self.applyChanges)
        self.revertButton.clicked.connect(self.revert)
        self.modelTypeBox.currentIndexChanged.connect(self.updateSimulationList)
        self.simNameBox.currentIndexChanged.connect(self.simSet)
        self.addInputButton.clicked.connect(self.addInputClicked)
        self.removeInputButton.clicked.connect(self.delInput)
        self.valuesToDeafultsButton.clicked.connect(self.valuesToDefaults)
        self.valuesToDeafultsButton.hide()
        self.addOutputButton.clicked.connect(self.addOutputClicked)
        self.removeOutputButton.clicked.connect(self.delOutput)
        self.vexButton.clicked.connect(self.showVex)
        self.inputTagBrowser.clicked.connect(self.openTagBrowserInputs)
        self.outputTagBrowser.clicked.connect(self.openTagBrowserOutputs)
        self.runButton.clicked.connect(self.runNode)
        self.stopButton.clicked.connect(self.stopRun)
        self.nodeNameBox.currentIndexChanged.connect(self.changeNode)
        self.nodeNameBox.setEditable(False)
        self.synhi = PythonHighlighter(self.pyCode.document())
        self.sim_mapping = None

    def changeNode(self, index):
        newNode = self.nodeNameBox.currentText()
        self.applyChanges()
        self.setNodeName(newNode)

    def setNodeName(self, name):
        self.setNodeName2(name)
        self.updateForm()

    def setNodeName2(self, name):
        """
        Set the node that is being viewed\edited
        """
        gr = self.dat.flowsheet  # shorter name for graph
        if name == None or name == "":
            self.clearContent()
        else:
            self.nodeName = name  # set the original node name
            # Store a backup of node contents
            sd = gr.nodes[name].saveDict()
            self.nodeBkp = sd
            self.node = gr.nodes[name]
            gr.markConnectedInputs()
            self.parent().varBrowse.nodeMask = [name]
            self.checkSim()

    def checkSim(self):
        """
        Check if the model assigned to the node exists.  This would
        mostly be a problem when someone passes a flowsheet to
        someone else who is using a differnt Turbine instance.  They
        may not have uploaded the models to Turbine, or may be using
        differnt model names.
        """
        if self.node.modelType == nodeModelTypes.MODEL_NONE:
            pass
        elif self.node.modelType == nodeModelTypes.MODEL_TURBINE:
            try:
                sl = self.dat.flowsheet.turbConfig.getSimulationList()
            except:
                logging.getLogger("foqus." + __name__).debug(
                    "Could not connect to Turbine in checkSim()"
                    " Is the Turbine web service running?"
                )
                sl = []
            m = self.node.modelName
            if m not in sl:
                # show a warning message
                QMessageBox.warning(
                    self,
                    "Turbine Model Not Available",
                    (
                        "The Turbine model specified for this node is not "
                        "available from Turbine.  Model: {0}"
                    ).format(m),
                )

    def runNode(self):
        """
        Run the nodes calculations; this is mostly just to test
        that a node is properly set up without running entire
        flowsheet
        """
        self.parent().runSim(node=self.nodeName)

    def stopRun(self):
        """
        Stop button on node panel calls this, this stop any running
        single simulation, does not stop optimization, uq, surrogate
        ...
        """
        self.parent().stopSim()

    def clearContent(self):
        self.node = None
        self.nodeName = ""
        self.calcErrorBox.setText(str(-1))
        self.errorMessageText.setText("")
        self.updateModelType()
        self.inputVarTable.setRowCount(0)
        self.outputVarTable.setRowCount(0)
        self.simSettingsTable.setRowCount(0)
        self.pyCode.setPlainText("")

    def openTagBrowserInputs(self):
        """
        Opens up the tag browser to help add tags to input variables
        """
        te = tagSelectDialog(self.dat, self)
        te.setWindowTitle("Input Tag Browser")

        def insertTagsFromBrowser():
            rows = set()
            for i in self.inputVarTable.selectedIndexes():
                rows.add(i.row())
            for r in rows:
                lst = gh.getCellJSON(self.inputVarTable, r, self.ivCols["Tags"])
                if not isinstance(lst, list):
                    lst = []
                lst += te.selectedTags
                gh.setCellJSON(self.inputVarTable, r, self.ivCols["Tags"], lst)

        te.sendTag.connect(insertTagsFromBrowser)
        te.show()

    def openTagBrowserOutputs(self):
        """
        Opens up the tag browser to help add tags to
        output variables
        """
        te = tagSelectDialog(self.dat, self)
        te.setWindowTitle("Output Tag Browser")

        def insertTagsFromBrowser():
            rows = set()
            for i in self.outputVarTable.selectedIndexes():
                rows.add(i.row())
            for r in rows:
                lst = gh.getCellJSON(self.outputVarTable, r, self.ovCols["Tags"])
                if not isinstance(lst, list):
                    lst = []
                lst += te.selectedTags
                gh.setCellJSON(self.outputVarTable, r, self.ovCols["Tags"], lst)

        te.sendTag.connect(insertTagsFromBrowser)
        te.show()

    def revert(self):
        """
        Reset the node to the state it was in when the node
        was first selected
        """
        self.node.loadDict(self.nodeBkp)
        self.updateForm()
        self.redrawFlowsheet.emit()

    def applyChanges(self):
        """
        Update the node with the settings in the forms
        """
        if self.nodeName not in self.dat.flowsheet.nodes:
            return  # don't apply if node was deleted already
        gr = self.dat.flowsheet  # shorter name for graph
        gr.nodes[self.nodeName] = self.node
        self.node.x = float(self.xBox.text())
        self.node.y = float(self.yBox.text())
        self.node.z = float(self.zBox.text())
        self.node.pythonCode = self.pyCode.toPlainText()
        if self.postRadio.isChecked():
            self.node.scriptMode = "post"
        elif self.preRadio.isChecked():
            self.node.scriptMode = "pre"
        else:
            self.node.scriptMode = "total"
        table = self.inputVarTable
        for row in range(table.rowCount()):
            name = gh.getCellText(table, row, self.ivCols["Name"])
            var = self.node.inVars[name]
            var.desc = gh.getCellText(table, row, self.ivCols["Description"])
            var.unit = gh.getCellText(table, row, self.ivCols["Unit"])
            var.setType(gh.getCellText(table, row, self.ivCols["Type"]))
            var.min = gh.getCellJSON(table, row, self.ivCols["Min"])
            var.max = gh.getCellJSON(table, row, self.ivCols["Max"])
            var.value = gh.getCellJSON(table, row, self.ivCols["Value"])
            var.tags = gh.getCellJSON(table, row, self.ivCols["Tags"])
            var.default = gh.getCellJSON(table, row, self.ivCols["Default"])
            distName = gh.getCellText(table, row, self.ivCols["Distribution"])
            var.dist.setDistributionType(distName)
            val = gh.getCellJSON(table, row, self.ivCols["Param 1"])
            var.dist.firstParamValue = val
            var.dist.secondParamValue = gh.getCellJSON(
                table, row, self.ivCols["Param 2"]
            )
        table = self.outputVarTable
        for row in range(self.outputVarTable.rowCount()):
            name = gh.getCellText(table, row, self.ovCols["Name"])
            var = self.node.outVars[name]
            var.value = gh.getCellJSON(table, row, self.ovCols["Value"])
            var.desc = gh.getCellText(table, row, self.ovCols["Description"])
            var.unit = gh.getCellText(table, row, self.ovCols["Unit"])
            var.setType(gh.getCellText(table, row, self.ovCols["Type"]))
            var.tags = gh.getCellJSON(table, row, self.ovCols["Tags"])
        table = self.simSettingsTable
        for row in range(table.rowCount()):
            name = gh.getCellText(table, row, 0)
            if self.node.options[name].dtype == bool:
                val = gh.isChecked(table, row, 1)
            elif len(self.node.options[name].validValues) > 0:
                val = gh.cellPulldownJSON(table, row, 1)
            else:
                val = gh.getCellJSON(table, row, 1)
            self.node.options[name].value = val
        self.redrawFlowsheet.emit()

    def updateColIndexes(self):
        """
        Update the dictionary of column indexes the key is the
        column heading name
        """
        self.ivCols = dict()
        self.ovCols = dict()
        for col in range(self.inputVarTable.columnCount()):
            self.ivCols[self.inputVarTable.horizontalHeaderItem(col).text()] = col
        for col in range(self.outputVarTable.columnCount()):
            self.ovCols[self.outputVarTable.horizontalHeaderItem(col).text()] = col

    def updateForm(self):
        """
        Update the form to reflect the current state of the node.
        """
        self.updateNodeList()
        if self.nodeName != "":
            self.calcErrorBox.setText(str(self.node.calcError))
            self.errorMessageText.setText(self.node.errorLookup(self.node.calcError))
            self.updateLocation()
            self.updateModelType()
            self.pyCode.setPlainText(self.node.pythonCode)
            if self.node.scriptMode == "post":
                self.postRadio.setChecked(True)
            elif self.node.scriptMode == "pre":
                self.preRadio.setChecked(True)
            else:
                self.totalRadio.setChecked(True)
            self.updateInputVariables()
            self.updateOutputVariables()
            self.updateSettingsTable()
        else:
            self.clearContent()

    def updateNodeList(self):
        self.prevName = self.nodeNameBox.currentText()
        self.nodeNameBox.blockSignals(True)
        self.nodeNameBox.clear()
        self.nodeNameBox.addItems(sorted(self.dat.flowsheet.nodes.keys()))
        i = self.nodeNameBox.findText(self.nodeName)
        if i < 0:
            i = 0
        self.nodeNameBox.setCurrentIndex(i)
        self.setNodeName2(self.nodeNameBox.currentText())
        self.nodeNameBox.blockSignals(False)

    def updateLocation(self):
        """
        Update the location information for a node.  This may be
        used by itself it the node is being dragged to a new
        location.
        """
        self.xBox.setText(str(self.node.x))
        self.yBox.setText(str(self.node.y))
        self.zBox.setText(str(self.node.z))

    def getModelType(self):
        """
        Get the enumerated node model type from the selection
        in the modelTypeBox
        """
        if self.modelTypeBox.currentIndex() == 0:
            # the model type is none os there are no models
            return nodeModelTypes.MODEL_NONE
        elif self.modelTypeBox.currentIndex() == 1:
            # model type is turbine
            return nodeModelTypes.MODEL_TURBINE
        elif self.modelTypeBox.currentIndex() == 2:
            # model type is plugin
            return nodeModelTypes.MODEL_PLUGIN
        elif self.modelTypeBox.currentIndex() == 5:
            # model type is ml_ai
            return nodeModelTypes.MODEL_ML_AI
        else:
            # this shouldn't be
            return nodeModelTypes.MODEL_NONE

    def updateModelType(self):
        """
        Set the model type to match the node; since changes to the
        model type pulldown are connected to the
        updateSimulationList function that will also happen if the
        index is changed
        """
        if self.node == None:
            self.modelTypeBox.setCurrentIndex(0)
        elif self.node.modelType == nodeModelTypes.MODEL_NONE:
            self.modelTypeBox.setCurrentIndex(0)
        elif self.node.modelType == nodeModelTypes.MODEL_TURBINE:
            self.modelTypeBox.setCurrentIndex(1)
        elif self.node.modelType == nodeModelTypes.MODEL_PLUGIN:
            self.modelTypeBox.setCurrentIndex(2)
        elif self.node.modelType == nodeModelTypes.MODEL_ML_AI:
            self.modelTypeBox.setCurrentIndex(5)
        self.updateSimulationList()

    def updateSimulationList(self):
        """
        Update the simulation list.
        """
        self.simNameBox.blockSignals(True)
        self.simNameBox.clear()
        self.simNameBox.addItem("")
        # check the model type
        if self.modelTypeBox.currentIndex() == 0:
            # the model type is none os there are no models
            pass
        elif self.modelTypeBox.currentIndex() == 1:
            # model type is turbine
            try:
                sl = self.dat.flowsheet.turbConfig.getSimulationList()
            except:
                logging.getLogger("foqus." + __name__).debug(
                    "Could not connect to Turbine in checkSim()"
                    " Is the Turbine web service running?"
                )
                sl = []
            self.simNameBox.addItems(sorted(sl, key=lambda s: s.lower()))
        elif self.modelTypeBox.currentIndex() == 2:
            # model type is plugin
            sl = sorted(list(self.dat.pymodels.plugins.keys()), key=lambda s: s.lower())
            self.simNameBox.addItems(sl)
        elif self.modelTypeBox.currentIndex() == 5:
            # model type is ml_ai
            sl = sorted(
                list(self.dat.pymodels_ml_ai.ml_ai_models.keys()),
                key=lambda s: s.lower(),
            )
            self.simNameBox.addItems(sl)
        try:
            i = self.simNameBox.findText(self.node.modelName)
        except:
            i = 0
        self.simNameBox.setCurrentIndex(i)
        self.simNameBox.blockSignals(False)
        self.simNameBox.setMaxVisibleItems(20)

    def valuesToDefaults(self):
        table = self.inputVarTable
        for row in range(table.rowCount()):
            val = gh.getCellJSON(table, row, self.ivCols["Value"])
            gh.setCellJSON(table, row, self.ivCols["Default"], val)
        self.node.updateSCDefaults()

    def updateInputVariables(self):
        """
        Update the input variables table from the node contents
        """
        table = self.inputVarTable
        vars = self.node.inVars
        table.clearContents()
        table.setRowCount(len(vars))
        row = 0
        for name in sorted(list(vars.keys()), key=lambda s: s.lower()):
            var = vars[name]
            if var.con == 1:
                bgColor = QColor(255, 255, 200)
            elif var.con == 2:
                bgColor = QColor(255, 220, 230)
            else:
                bgColor = QColor(255, 255, 255)
            gh.setTableItem(
                table, row, self.ivCols["Name"], name, bgColor=bgColor, editable=False
            )
            gh.setTableItem(
                table,
                row,
                self.ivCols["Value"],
                var.value,
                jsonEnc=True,
                bgColor=bgColor,
            )
            gh.setTableItem(
                table,
                row,
                self.ivCols["Default"],
                var.default,
                jsonEnc=True,
                bgColor=bgColor,
            )
            gh.setTableItem(
                table, row, self.ivCols["Min"], var.min, jsonEnc=True, bgColor=bgColor
            )
            gh.setTableItem(
                table, row, self.ivCols["Max"], var.max, jsonEnc=True, bgColor=bgColor
            )
            gh.setTableItem(
                table, row, self.ivCols["Tags"], var.tags, jsonEnc=True, bgColor=bgColor
            )
            gh.setTableItem(table, row, self.ivCols["Unit"], var.unit, bgColor=bgColor)
            gh.setTableItem(
                table,
                row,
                self.ivCols["Type"],
                pullDown=["float", "int", "str", "object"],
                text=var.typeStr(),
                bgColor=bgColor,
            )
            gh.setTableItem(
                table, row, self.ivCols["Description"], var.desc, bgColor=bgColor
            )
            gh.setTableItem(
                table,
                row,
                self.ivCols["Distribution"],
                Distribution.getFullName(var.dist.type),
                pullDown=Distribution.fullNames,
                bgColor=bgColor,
            )
            gh.setTableItem(
                table,
                row,
                self.ivCols["Param 1"],
                var.dist.firstParamValue,
                jsonEnc=True,
                bgColor=bgColor,
            )
            gh.setTableItem(
                table,
                row,
                self.ivCols["Param 2"],
                var.dist.secondParamValue,
                jsonEnc=True,
                bgColor=bgColor,
            )
            row += 1
        table.resizeColumnsToContents()
        self.inputVarTable.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.inputVarTable.setSelectionBehavior(QAbstractItemView.SelectRows)

    def updateOutputVariables(self):
        """
        Update the output variables table from the node contents
        """
        table = self.outputVarTable
        vars = self.node.outVars
        table.clearContents()
        table.setRowCount(len(vars))
        row = 0
        for name in sorted(list(vars.keys()), key=lambda s: s.lower()):
            var = vars[name]
            gh.setTableItem(table, row, self.ovCols["Name"], name, editable=False)
            gh.setTableItem(table, row, self.ovCols["Value"], var.value, jsonEnc=True)
            gh.setTableItem(table, row, self.ovCols["Unit"], var.unit)
            gh.setTableItem(
                table,
                row,
                self.ovCols["Type"],
                pullDown=["float", "int", "str", "object"],
                text=var.typeStr(),
            )
            gh.setTableItem(table, row, self.ovCols["Description"], var.desc)
            gh.setTableItem(table, row, self.ovCols["Tags"], var.tags, jsonEnc=True)
            row += 1
        table.resizeColumnsToContents()
        self.outputVarTable.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.outputVarTable.setSelectionBehavior(QAbstractItemView.SelectRows)

    def updateSettingsTable(self):
        """
        This table contains node/model options.  Sinter simulation
        options, turbine options, plugin options...
        """
        table = self.simSettingsTable
        table.clearContents()
        opts = self.node.options
        table.setRowCount(len(opts))
        for row, opt in enumerate(opts.order):
            if opts[opt].disable:
                table.hideRow(row)
            gh.setTableItem(table, row, 0, opt, editable=False)
            gh.setTableItem(table, row, 2, opts[opt].desc)
            # set the value column use a checkbox for bool options
            # and if there is a list of valid values use a combo box.
            if opts[opt].dtype == bool:
                # If the option is bool type use a check box
                gh.setTableItem(
                    table,
                    row,
                    1,
                    "",
                    check=opts[opt].value,
                    jsonEnc=False,
                    bgColor=QColor(235, 255, 235),
                )
            elif len(opts[opt].validValues) > 0:
                # if is a list type use a combo box
                gh.setTableItem(
                    table,
                    row,
                    1,
                    opts[opt].value,
                    jsonEnc=True,
                    pullDown=opts[opt].validValues,
                    bgColor=QColor(235, 255, 235),
                )
            else:
                # Otherwise you just have to type
                gh.setTableItem(
                    table,
                    row,
                    1,
                    opts[opt].value,
                    jsonEnc=True,
                    bgColor=QColor(235, 255, 235),
                )
            table.resizeColumnsToContents()

    def addInputClicked(self):
        """
        The clicked signal contains will send a checked argumnet to the callback
        which will go into name if I directly use addInput as the callback
        """
        self.addInput()

    def addInput(self, name=None, s=0, minv=0, maxv=1, val=0):
        """
        Add a new input variable, is a name is given, don't ask user for name,
        just go ahead and add it.
        """
        ip = True
        if name is None:
            newName, ok = QInputDialog.getText(
                self, "Input Name", "New input variable name:", QLineEdit.Normal
            )
            size, ok = QInputDialog.getText(
                self, "Input Size", "New input variable size:", QLineEdit.Normal
            )
            minval, ok = QInputDialog.getText(
                self,
                "Input min value",
                "New input variable min value:",
                QLineEdit.Normal,
            )
            maxval, ok = QInputDialog.getText(
                self,
                "Input max Value",
                "New input variable max value:",
                QLineEdit.Normal,
            )
            value, ok = QInputDialog.getText(
                self, "Input Value", "New input variable value:", QLineEdit.Normal
            )
            if int(size) > 1:
                minvalevaluate = ast.literal_eval(minval)
                if type(minvalevaluate) in [float, int]:
                    minval = [minvalevaluate for i in range(int(size))]
                else:
                    minval = ast.literal_eval(minval)
                maxvalevaluate = ast.literal_eval(maxval)
                if type(maxvalevaluate) in [float, int]:
                    maxval = [maxvalevaluate for i in range(int(size))]
                else:
                    maxval = ast.literal_eval(maxval)
                valueevaluate = ast.literal_eval(value)
                if type(valueevaluate) in [float, int]:
                    value = [valueevaluate for i in range(int(size))]
                else:
                    value = ast.literal_eval(value)
        else:
            newName = name
            size = s
            minval = minv
            maxval = maxv
            value = val
            ok = True

        if ok and newName != "":
            if newName in self.node.inVars:
                QMessageBox.warning(self, "Invalid Name", "That input already exists")
                return
            # size condition
            if int(size) > 1:
                self.node.gr.input.addVectorVariableScalars(
                    self.node.name, newName, ip, size, minval, maxval, value
                )
                nvlist = self.node.gr.input
                self.node.gr.input_vectorlist.addVectorVariable(
                    self.node.name, newName, ip, size, nvlist
                )
            else:
                self.node.gr.input.addVariable(self.node.name, newName)
                nodevar = self.node.gr.input.get(self.node.name, newName)
                nodevar.min = float(minval)
                nodevar.max = float(maxval)
                nodevar.value = float(value)

            self.applyChanges()
            self.updateInputVariables()

    def delInput(self):
        """
        Delete selected variable
        """
        table = self.inputVarTable
        if table.currentRow() < 0:
            return
        name = gh.getCellText(table, table.currentRow(), self.ivCols["Name"])
        self.applyChanges()
        for vname in self.node.gr.input_vectorlist[self.node.name].keys():
            if vname in name:
                for i in range(
                    len(self.node.gr.input_vectorlist[self.node.name][vname].vector)
                ):
                    del self.node.gr.input[self.node.name][vname + "_{0}".format(i)]
                del self.node.gr.input_vectorlist[self.node.name][vname]
                break
            else:
                continue
        if name in self.node.gr.input[self.node.name].keys():
            del self.node.gr.input[self.node.name][name]
        self.updateInputVariables()

    def addOutputClicked(self):
        """
        The clicked signal contains will send a checked argumnet to the callback
        which will go into name if I directly use addInput as the callback
        """
        self.addOutput()

    def addOutput(self, name=None, s=0):
        """
        Add an output variable
        """
        ip = False
        if name == None:
            newName, ok = QInputDialog.getText(
                self, "Output Name", "New output variable name:", QLineEdit.Normal
            )
            size, ok = QInputDialog.getText(
                self, "Output Size", "New output variable size:", QLineEdit.Normal
            )
        else:
            newName = name
            size = s
            ok = True
        if ok and newName != "":
            if newName in self.node.outVars:
                QMessageBox.warning(self, "Invalid Name", "That output already exists")
                return
            # size condition
            if int(size) > 1:
                self.node.gr.output.addVectorVariableScalars(
                    self.node.name, newName, ip, size, value=None
                )
                nvlist = self.node.gr.output
                self.node.gr.output_vectorlist.addVectorVariable(
                    self.node.name, newName, ip, size, nvlist
                )
            else:
                self.node.gr.output.addVariable(self.node.name, newName)
            self.applyChanges()
            self.updateOutputVariables()

    def delOutput(self):
        """
        Delete selected output variable
        """
        table = self.outputVarTable
        if table.currentRow() < 0:
            return
        name = gh.getCellText(table, table.currentRow(), self.ivCols["Name"])
        self.applyChanges()
        for vname in self.node.gr.output_vectorlist[self.node.name].keys():
            if vname in name:
                for i in range(
                    len(self.node.gr.output_vectorlist[self.node.name][vname].vector)
                ):
                    del self.node.gr.output[self.node.name][vname + "_{0}".format(i)]
                del self.node.gr.output_vectorlist[self.node.name][vname]
                break
            else:
                continue
        if name in self.node.gr.output[self.node.name].keys():
            del self.node.gr.output[self.node.name][name]
        # del(self.node.outVars[name])
        self.updateOutputVariables()

    def showVex(self):
        """
        Shows the variable explored for writing post code
        """
        self.parent().varBrowse.format = "node"
        self.parent().varBrowse.nodeMask = [self.nodeName]
        self.parent().varBrowse.refreshVars()
        self.parent().varBrowse.show()

    def simSet(self):
        """TODO:  CleanUP Need to follow references back to the flowsheet
        in order to trip errors
        """
        text = self.simNameBox.currentText()
        self.parent().setStatus("Setting Simulation %s" % (text))
        try:

            self.node.setSim(newType=self.getModelType(), newModel=text)
        except NodeEx as ex:
            # ERROR Code is posted but Allowing Run button
            # But should disable it
            self.parent().handleNodeException(ex)
        else:
            self.parent().handleNodeSimulationReady()
        self.updateForm()

    def closeEvent(self, event):
        """
        Intercept the close event and apply changes to node first
        """
        self.applyChanges()
        event.accept()
        self.mw.toggleNodeEditorAction.setChecked(False)
