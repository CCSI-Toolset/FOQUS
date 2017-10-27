'''
    nodePanel.py

    * This is a node editor widget

    John Eslick, Carnegie Mellon University, 2014

    This Material was produced under the DOE Carbon Capture Simulation
    Initiative (CCSI), and copyright is held by the software owners:
    ORISE, LANS, LLNS, LBL, PNNL, CMU, WVU, et al. The software owners
    and/or the U.S. Government retain ownership of all rights in the
    CCSI software and the copyright and patents subsisting therein. Any
    distribution or dissemination is governed under the terms and
    conditions of the CCSI Test and Evaluation License, CCSI Master
    Non-Disclosure Agreement, and the CCSI Intellectual Property
    Management Plan. No rights are granted except as expressly recited
    in one of the aforementioned agreements.
'''
#from foqus_lib.gui.flowsheet.nodePanel_UI import *
from foqus_lib.gui.dialogs.tagSelectDialog import *
from foqus_lib.framework.graph.node import *
#from PySide import QtGui, QtCore
import foqus_lib.gui.helpers.guiHelpers as gh
import types
import platform
from ConfigParser import RawConfigParser
from StringIO import StringIO
from foqus_lib.gui.pysyntax_hl.pysyntax_hl import *
try:
    from dmf_lib.dmf_browser import DMFBrowser
    from dmf_lib.common.common import *
except:
    logging.getLogger("foqus." + __name__)\
        .exception('Failed to import or launch DMFBrowser')
from foqus_lib.framework.uq.Distribution import Distribution

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMessageBox
import os
from PyQt5 import uic
mypath = os.path.dirname(__file__)
_nodeDockUI, _nodeDock = \
        uic.loadUiType(os.path.join(mypath, "nodePanel_UI.ui"))
#super(, self).__init__(parent=parent)

class nodeDock(_nodeDock, _nodeDockUI):
    redrawFlowsheet = QtCore.pyqtSignal() # request flowsheet redraw
    waiting = QtCore.pyqtSignal() # indicates a task is going take a while
    notwaiting = QtCore.pyqtSignal() # indicates a wait is over
    def __init__(self, dat, parent=None):
        '''
            Node view/edit dock widget constructor
        '''
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
            "Variable, Opt + UQ"
        ]
        self.applyButton.clicked.connect(self.applyChanges)
        self.revertButton.clicked.connect(self.revert)
        self.modelTypeBox.currentIndexChanged.connect(
            self.updateSimulationList)
        self.simNameBox.currentIndexChanged.connect(self.simSet)
        self.addInputButton.clicked.connect(self.addInput)
        self.removeInputButton.clicked.connect(self.delInput)
        self.valuesToDeafultsButton.clicked.connect(self.valuesToDefaults)
        self.valuesToDeafultsButton.hide()
        self.addOutputButton.clicked.connect(self.addOutput)
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
        '''
            Set the node that is being viewed\edited
        '''
        gr = self.dat.flowsheet #shorter name for graph
        if name == None or name == '':
            self.clearContent()
        else:
            self.nodeName = name #set the original node name
            # Store a backup of node contents
            sd = gr.nodes[name].saveDict()
            self.nodeBkp = sd
            self.node = gr.nodes[name]
            gr.markConnectedInputs()
            self.parent().varBrowse.nodeMask = [name]
            self.checkSim()

    def checkSim(self):
        '''
            Check if the model assigned to the node exists.  This would
            mostly be a problem when someone passes a flowsheet to
            someone else who is using a differnt Turbine instance.  They
            may not have uploaded the models to Turbine, or may be using
            differnt model names.
        '''
        if self.node.modelType == nodeModelTypes.MODEL_NONE:
            pass
        elif self.node.modelType == nodeModelTypes.MODEL_TURBINE:
            try:
                sl = self.dat.flowsheet.turbConfig.getSimulationList()
            except:
                logging.getLogger("foqus." + __name__).debug(
                    "Could not connect to Turbine in checkSim()"\
                    " Is the Turbine web service running?")
                sl = []
            m = self.node.modelName
            if m not in sl:
                #show a warning message
                QtWidgets.QMessageBox.warning(
                    self,
                    "Turbine Model Not Available",
                    ("The Turbine model specified for this node is not "
                     "available from Turbine.  Model: {0}").format(m))

    def runNode(self):
        '''
            Run the nodes calculations; this is mostly just to test
            that a node is properly set up without running entire
            flowsheet
        '''
        self.parent().runSim(node=self.nodeName)

    def stopRun(self):
        '''
            Stop button on node panel calls this, this stop any running
            single simulation, does not stop optimization, uq, surrogate
            ...
        '''
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
        '''
            Opens up the tag browser to help add tags to input variables
        '''
        te = tagSelectDialog(self.dat, self)
        te.setWindowTitle("Input Tag Browser")
        def insertTagsFromBrowser():
            rows=set()
            for i in self.inputVarTable.selectedIndexes():
                rows.add(i.row())
            for r in rows:
                lst = gh.getCellJSON(
                    self.inputVarTable,
                    r,
                    self.ivCols["Tags"])
                if not isinstance(lst, list): lst = []
                lst += te.selectedTags
                gh.setCellJSON(
                    self.inputVarTable,
                    r,
                    self.ivCols["Tags"],
                    lst)
        te.sendTag.connect(insertTagsFromBrowser)
        te.show()

    def openTagBrowserOutputs(self):
        '''
            Opens up the tag browser to help add tags to
            output variables
        '''
        te = tagSelectDialog(self.dat, self)
        te.setWindowTitle("Output Tag Browser")
        def insertTagsFromBrowser():
            rows=set()
            for i in self.outputVarTable.selectedIndexes():
                rows.add(i.row())
            for r in rows:
                lst = gh.getCellJSON(
                    self.outputVarTable,
                    r,
                    self.ovCols["Tags"])
                if not isinstance(lst, list): lst = []
                lst += te.selectedTags
                gh.setCellJSON(
                    self.outputVarTable,
                    r,
                    self.ovCols["Tags"], lst)
        te.sendTag.connect(insertTagsFromBrowser)
        te.show()

    def revert(self):
        '''
            Reset the node to the state it was in when the node
            was first selected
        '''
        self.node.loadDict( self.nodeBkp )
        self.updateForm()
        self.redrawFlowsheet.emit()

    def applyChanges(self):
        '''
            Update the node with the settings in the forms
        '''
        if self.nodeName not in self.dat.flowsheet.nodes:
            return  #don't apply if node was deleted already
        #try:
        #    self.dat.flowsheet.renameNode(
        #        self.nodeName,
        #        str(self.nodeNameBox.currentText()))
        #    self.nodeName = str(self.nodeNameBox.text())
        #except:
        #    QtWidgets.QMessageBox.warning(
        #        self,
        #        "Invalid Name",
        #        ("The new node name is probably already being used. "
        #         " The node has not been renamed"))
        gr = self.dat.flowsheet # shorter name for graph
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
        for row in range( table.rowCount() ):
            name = gh.getCellText(table, row, self.ivCols["Name"])
            var = self.node.inVars[name]
            var.desc = gh.getCellText(table, row,
                self.ivCols["Description"])
            var.unit = gh.getCellText(table, row,
                self.ivCols["Unit"])
            var.setType(gh.getCellText(table, row,
                self.ivCols["Type"]))
            var.min = gh.getCellJSON(table, row,
                self.ivCols["Min"])
            var.max = gh.getCellJSON(table, row,
                self.ivCols["Max"])
            var.value = gh.getCellJSON(table, row,
                self.ivCols["Value"])
            var.tags = gh.getCellJSON(table, row,
                self.ivCols["Tags"])
            var.default = gh.getCellJSON(table, row,
                self.ivCols["Default"])
            distName = gh.getCellText(table, row,
                self.ivCols["Distribution"])
            var.dist.setDistributionType(distName)
            val = gh.getCellJSON(table, row,
                self.ivCols["Param 1"])
            var.dist.firstParamValue = val
            var.dist.secondParamValue = gh.getCellJSON(table, row,
                self.ivCols["Param 2"])
            var.toNumpy()
        table = self.outputVarTable
        for row in range( self.outputVarTable.rowCount() ):
            name = gh.getCellText(table, row, self.ovCols["Name"])
            var = self.node.outVars[name]
            var.value = gh.getCellJSON(table, row,
                self.ovCols["Value"])
            var.desc = gh.getCellText(table, row,
                self.ovCols["Description"])
            var.unit = gh.getCellText(table, row,
                self.ovCols["Unit"])
            var.setType(gh.getCellText(table, row,
                self.ovCols["Type"]))
            var.tags = gh.getCellJSON(table, row,
                self.ovCols["Tags"])
            var.toNumpy()
        table = self.simSettingsTable
        for row in range(table.rowCount()):
            name = gh.getCellText(table, row, 0)
            if self.node.options[name].dtype == bool:
                val = gh.isChecked(table, row, 1)
            elif len(self.node.options[name].validValues) > 0:
                val = gh.cellPulldownJSON(table,row,1)
            else:
                val = gh.getCellJSON(table, row, 1)
            self.node.options[name].value = val
        self.redrawFlowsheet.emit()

    def updateColIndexes(self):
        '''
            Update the dictionary of column indexes the key is the
            column heading name
        '''
        self.ivCols = dict()
        self.ovCols = dict()
        for col in range(self.inputVarTable.columnCount()):
            self.ivCols[
                self.inputVarTable.horizontalHeaderItem(col).text()]\
                = col
        for col in range(self.outputVarTable.columnCount()):
            self.ovCols[
                self.outputVarTable.horizontalHeaderItem(col).text()]\
                = col

    def updateForm(self):
        '''
            Update the form to reflect the current state of the node.
        '''
        self.updateNodeList()
        if self.nodeName != "":
            self.calcErrorBox.setText(str(self.node.calcError))
            self.errorMessageText.setText(
                self.node.errorLookup(self.node.calcError))
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
        self.nodeNameBox.addItems(
            sorted(
                self.dat.flowsheet.nodes.keys()
                ))
        i = self.nodeNameBox.findText(self.nodeName)
        if i<0:
            i = 0
        self.nodeNameBox.setCurrentIndex(i)
        self.setNodeName2(self.nodeNameBox.currentText())
        self.nodeNameBox.blockSignals(False)

    def updateLocation(self):
        '''
            Update the location information for a node.  This may be
            used by itself it the node is being dragged to a new
            location.
        '''
        self.xBox.setText(str(self.node.x))
        self.yBox.setText(str(self.node.y))
        self.zBox.setText(str(self.node.z))

    def getModelType(self):
        '''
            Get the enumerated node model type from the selection
            in the modelTypeBox
        '''
        if self.modelTypeBox.currentIndex()==0:
            # the model type is none os there are no models
            return nodeModelTypes.MODEL_NONE
        elif self.modelTypeBox.currentIndex()==1:
            # model type is turbine
            return nodeModelTypes.MODEL_TURBINE
        elif self.modelTypeBox.currentIndex()==2:
            # model type is plugin
            return nodeModelTypes.MODEL_PLUGIN
        elif self.modelTypeBox.currentIndex()==3:
            # model type is DMF
            return nodeModelTypes.MODEL_DMF_LITE
        elif self.modelTypeBox.currentIndex()==4:
            # model type is DMF
            return nodeModelTypes.MODEL_DMF_SERV
        else:
            # this shouldn't be
            return nodeModelTypes.MODEL_NONE

    def updateModelType(self):
        '''
            Set the model type to match the node; since changes to the
            model type pulldown are connected to the
            updateSimulationList function that will also happen if the
            index is changed
        '''
        if self.node == None:
            self.modelTypeBox.setCurrentIndex(0)
        elif self.node.modelType == nodeModelTypes.MODEL_NONE:
            self.modelTypeBox.setCurrentIndex(0)
        elif self.node.modelType == nodeModelTypes.MODEL_TURBINE:
            self.modelTypeBox.setCurrentIndex(1)
        elif self.node.modelType == nodeModelTypes.MODEL_PLUGIN:
            self.modelTypeBox.setCurrentIndex(2)
        elif self.node.modelType == nodeModelTypes.MODEL_DMF_LITE:
            self.modelTypeBox.setCurrentIndex(3)
        elif self.node.modelType == nodeModelTypes.MODEL_DMF_SERV:
            self.modelTypeBox.setCurrentIndex(4)
        self.updateSimulationList()

    def updateSimulationList(self):
        '''
            Update the simulation list.
        '''
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
                    "Could not connect to Turbine in checkSim()"\
                    " Is the Turbine web service running?")
                sl = []
            self.simNameBox.addItems(sorted(sl,key=lambda s: s.lower()))
        elif self.modelTypeBox.currentIndex() == 2:
            # model type is plugin
            sl = sorted(
                self.dat.pymodels.plugins.keys(),
                key=lambda s: s.lower())
            self.simNameBox.addItems(sl)
        elif self.modelTypeBox.currentIndex() == 3:
            # model type is from DMF lite
            try:
                browser_conf = {}
                browser_conf["conf"] = None
                browser_conf["repo"] = "DMF Lite"
                sim_names, sim_ids, sc_ids = DMFBrowser.getSimulationList(
                    self, browser_conf["conf"], browser_conf["repo"])
                self.sim_mapping = dict()
                if sim_names and sim_ids and sc_ids:
                    for sim_name, sim_id, sc_id in zip(
                            sim_names, sim_ids, sc_ids):
                        if not self.sim_mapping.get(sim_name, None):
                            self.sim_mapping[sim_name] = (
                                sim_id, sc_id, browser_conf)
                        else:
                            logging.getLogger("foqus." + __name__).debug(
                                "Same name sims but different IDs")
            except:
                logging.getLogger("foqus." + __name__).debug(
                    "Could not connect to DMF Lite.")
                sim_names = []
            self.simNameBox.addItems(
                sorted(sim_names, key=lambda s: s.lower()))

        elif self.modelTypeBox.currentIndex() == 4:
            # model type is from DMF server
            browser_conf = {}
            repo_props = []
            repo_name_list = []
            prop_list_paths = []
            try:
                # We are on Windows
                if platform.system().startswith(WINDOWS):
                    self.PROP_LOC = (os.environ[REPO_PROPERTIES_WIN_PATH]
                                     + WIN_PATH_SEPARATOR)
                else:
                    self.PROP_LOC = (os.environ[REPO_PROPERTIES_UNIX_PATH]
                                     + UNIX_PATH_SEPARATOR)
                config = StringIO()
                # Fake properties header to allow working with configParser
                config.write('[' + PROP_HEADER + ']\n')

                # Get a list of property files for repositories
                repo_props = [f for f in os.listdir(self.PROP_LOC)
                              if os.path.isfile(os.path.join(self.PROP_LOC, f))
                              and f.endswith(PROPERTIES_EXT)]
                if len(repo_props) == 0:
                    logging.getLogger("foqus." + __name__).debug(
                        "No properties file specified.")
                for p in repo_props:
                    config.write(
                        open(self.PROP_LOC + p).read())
                    config.seek(0, os.SEEK_SET)
                    rcp = RawConfigParser()
                    rcp.readfp(config)
                    repo_name = rcp.get(PROP_HEADER, "repo_name")
                    repo_name_list.append(repo_name)
                    prop_list_paths.append(
                        self.PROP_LOC + p)
                    browser_conf["conf"] = prop_list_paths
                    browser_conf["repo"] = repo_name_list

                for conf, repo in zip(browser_conf.get("conf"),
                                      browser_conf.get("repo")):
                    sim_names, sim_ids, sc_ids = DMFBrowser.getSimulationList(
                        self, conf, repo)
                    self.sim_mapping = dict()
                    if not (sim_names and sim_ids and sc_ids):
                        continue
                    for sim_name, sim_id, sc_id in zip(
                            sim_names, sim_ids, sc_ids):
                        if not self.sim_mapping.get(sim_name, None):
                            browser_conf = {}
                            browser_conf["conf"] = conf
                            browser_conf["repo"] = repo
                            self.sim_mapping[sim_name] = (
                                sim_id, sc_id, browser_conf)
                        else:
                            logging.getLogger("foqus." + __name__).debug(
                                "Same name sims but different IDs")
            except:
                logging.getLogger("foqus." + __name__)\
                       .exception("Cannot get properties information "
                                  "for DMF Server.")

            self.simNameBox.addItems(
                sorted(sim_names, key=lambda s: s.lower()))
        else:
            # this shouldn't be
            raise Exception("Bad model type selected")
        # Try to set the model name to match the node
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
        self.node.upadteSCDefaults()

    def updateInputVariables(self):
        '''
            Update the input variables table from the node contents
        '''
        table = self.inputVarTable
        vars = self.node.inVars
        table.clearContents()
        table.setRowCount( len(vars)  )
        row = 0
        for name in sorted(vars.keys(), key = lambda s: s.lower()):
            var = vars[name]
            if var.con == 1:
                bgColor = QtGui.QColor(255, 255, 200)
            elif var.con ==2:
                bgColor = QtGui.QColor(255, 220, 230)
            else:
                bgColor = QtGui.QColor(255, 255, 255)
            gh.setTableItem(table, row,
                self.ivCols["Name"],
                name,
                bgColor = bgColor)
            gh.setTableItem(table, row,
                self.ivCols["Value"],
                var.value,
                jsonEnc = True,
                bgColor = bgColor)
            gh.setTableItem(table, row,
                self.ivCols["Default"],
                var.default,
                jsonEnc = True,
                bgColor = bgColor)
            gh.setTableItem(table, row,
                self.ivCols["Min"],
                var.min,
                jsonEnc = True,
                bgColor = bgColor)
            gh.setTableItem(table, row,
                self.ivCols["Max"],
                var.max,
                jsonEnc = True,
                bgColor = bgColor)
            gh.setTableItem(table,
                row, self.ivCols["Tags"],
                var.tags,
                jsonEnc = True,
                bgColor = bgColor)
            gh.setTableItem(table, row,
                self.ivCols["Unit"],
                var.unit,
                bgColor = bgColor)
            gh.setTableItem(table, row,
                self.ivCols["Type"],
                pullDown= ["float", "int", "str"],
                text=var.typeStr(),
                bgColor = bgColor)
            gh.setTableItem(table, row,
                self.ivCols["Description"],
                var.desc,
                bgColor = bgColor)
            gh.setTableItem(table, row,
                self.ivCols["Distribution"],
                Distribution.getFullName(var.dist.type),
                pullDown=Distribution.fullNames,
                bgColor = bgColor)
            gh.setTableItem(table, row,
                self.ivCols["Param 1"],
                var.dist.firstParamValue,
                jsonEnc = True,
                bgColor = bgColor)
            gh.setTableItem(table, row,
                self.ivCols["Param 2"],
                var.dist.secondParamValue,
                jsonEnc = True,
                bgColor = bgColor)
            row += 1
        table.resizeColumnsToContents()
        self.inputVarTable.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection)
        self.inputVarTable.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)

    def updateOutputVariables(self):
        '''
            Update the output variables table from the node contents
        '''
        table = self.outputVarTable
        vars = self.node.outVars
        table.clearContents()
        table.setRowCount(len(vars))
        row = 0
        for name in sorted(vars.keys(), key = lambda s: s.lower()):
            var = vars[name]
            gh.setTableItem(table, row,
                self.ovCols["Name"],
                name)
            gh.setTableItem(table, row,
                self.ovCols["Value"],
                var.value,
                jsonEnc = True)
            gh.setTableItem(table, row,
                self.ovCols["Unit"],
                var.unit)
            gh.setTableItem(table, row,
                self.ovCols["Type"],
                pullDown= ["float", "int", "str"],
                text=var.typeStr())
            gh.setTableItem(table, row,
                self.ovCols["Description"],
                var.desc)
            gh.setTableItem(table, row,
                self.ovCols["Tags"],
                var.tags,
                jsonEnc = True)
            row += 1
        table.resizeColumnsToContents()
        self.outputVarTable.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection)
        self.outputVarTable.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)

    def updateSettingsTable(self):
        '''
            This table contains node/model options.  Sinter simulation
            options, turbine options, plugin options...
        '''
        table = self.simSettingsTable
        table.clearContents()
        opts = self.node.options
        table.setRowCount(len(opts))
        for row, opt in enumerate(opts.order):
            if opts[opt].disable:
                table.hideRow(row)
            gh.setTableItem(table,row,0,opt)
            gh.setTableItem(table,row,2,opts[opt].desc)
            #set the value column use a checkbox for bool options
            #and if there is a list of valid values use a combo box.
            if opts[opt].dtype == bool:
                # If the option is bool type use a check box
                gh.setTableItem(
                    table,
                    row,
                    1,
                    '',
                    check = opts[opt].value,
                    jsonEnc = False,
                    bgColor = QtGui.QColor(235, 255, 235))
            elif len(opts[opt].validValues) > 0:
                # if is a list type use a combo box
                gh.setTableItem(
                    table,
                    row,
                    1,
                    opts[opt].value,
                    jsonEnc = True,
                    pullDown = opts[opt].validValues,
                    bgColor = QtGui.QColor(235, 255, 235))
            else:
                # Otherwise you just have to type
                gh.setTableItem(
                    table,
                    row,
                    1,
                    opts[opt].value,
                    jsonEnc = True,
                    bgColor = QtGui.QColor(235, 255, 235))
            table.resizeColumnsToContents()

    def addInput(self, name=None):
        '''
            Add a new input variable
        '''
        if name is None:
            newName, ok = QtGui.QInputDialog.getText(
                self,
                "Input Name",
                "New input variable name:",
                QtGui.QLineEdit.Normal)
        else:
            newName = name
            ok = True
        if ok and newName != '':
            if newName in self.node.inVars:
                QtGui.QMessageBox.warning(
                    self,
                    "Invalid Name",
                    "That input already exists")
                return
            self.applyChanges()
            self.node.inVars[newName] = nodeInVars()
            self.updateInputVariables()

    def delInput(self):
        '''
            Delete selected variable
        '''
        table = self.inputVarTable
        if table.currentRow() < 0:
            return
        name = gh.getCellText(table,
            table.currentRow(),
            self.ivCols["Name"])
        self.applyChanges()
        del self.node.gr.input[self.node.name][name]
        self.updateInputVariables()

    def addOutput(self, name=None):
        '''
            Add an output variable
        '''
        if name==None:
            newName, ok = QtGui.QInputDialog.getText(
                self,
                "Output Name",
                "New output variable name:",
                QtGui.QLineEdit.Normal)
        else:
            newName = name
            ok = True
        if ok and newName != '':
            if newName in self.node.outVars:
                QtGui.QMessageBox.warning(
                    self,
                    "Invalid Name",
                    "That output already exists")
                return
            self.applyChanges()
            self.node.outVars[newName] = nodeOutVars()
            self.updateOutputVariables()

    def delOutput(self):
        '''
            Delete selected output variable
        '''
        table = self.outputVarTable
        if table.currentRow() < 0:
            return
        name = gh.getCellText(
            table,
            table.currentRow(),
            self.ivCols["Name"])
        self.applyChanges()
        del(self.node.outVars[name])
        self.updateOutputVariables()

    def showVex(self):
        '''
            Shows the variable explored for writing post code
        '''
        self.parent().varBrowse.format = "node"
        self.parent().varBrowse.nodeMask = [self.nodeName]
        self.parent().varBrowse.refreshVars()
        self.parent().varBrowse.show()

    def simSet(self):
        text = self.simNameBox.currentText()
        ids = {}
        browser_conf = None
        if self.sim_mapping:
            mapping = self.sim_mapping.get(text, None)
        else:
            mapping = None
        if mapping:
            ids["sim"] = mapping[0]
            ids["sc"] = mapping[1]
            browser_conf = mapping[2]
        self.node.setSim(
            newType=self.getModelType(),
            newModel=text,
            ids=ids,
            browser_conf=browser_conf)
        self.updateForm()

    def closeEvent(self, event):
        '''
            Intercept the close event and apply changes to node first
        '''
        self.applyChanges()
        event.accept()
        self.mw.toggleNodeEditorAction.setChecked(False)
