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
"""optSetupFrame.py
* This contains workings of the optimization screen in FOQUS

John Eslick, Carnegie Mellon University, 2014
"""

import json
import copy
import os

from foqus_lib.framework.graph.graph import *
from foqus_lib.framework.graph.node import *
from foqus_lib.framework.graph.nodeVars import *
import foqus_lib.gui.helpers.guiHelpers as gh
from foqus_lib.gui.optimization.optMonitor import *
from foqus_lib.gui.optimization.optSampleGenDialog import *
from foqus_lib.gui.pysyntax_hl.pysyntax_hl import *

from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import QMessageBox, QDialog
from PyQt5.QtGui import QColor

mypath = os.path.dirname(__file__)
_optSetupFrameUI, _optSetupFrame = uic.loadUiType(
    os.path.join(mypath, "optSetupFrame_UI.ui")
)


class optSetupFrame(_optSetupFrame, _optSetupFrameUI):
    setStatusBar = QtCore.pyqtSignal(str)
    updateGraph = QtCore.pyqtSignal()

    def __init__(self, dat, parent=None):
        super(optSetupFrame, self).__init__(parent=parent)
        self.setupUi(self)
        self.lastSolver = None
        self.dat = dat
        self.updateColIndexes()
        # Connect signals
        self.fAddButton.clicked.connect(self.addF)
        self.fDelButton.clicked.connect(self.delF)
        self.gAddButton.clicked.connect(self.addG)
        self.gDelButton.clicked.connect(self.delG)
        self.vexButton.clicked.connect(self.showVex)
        self.checkInputButton.clicked.connect(self.checkInput)
        self.solverBox.currentIndexChanged.connect(self.selectSolver)
        self.addSampleButton.clicked.connect(self.addSample)
        self.clearSamplesButton.clicked.connect(self.clearSamples)
        self.deleteSampleButton.clicked.connect(self.deleteSamples)
        self.generateSamplesButton.clicked.connect(self.genSamples)
        #
        self.scalingOpts = ivarScales
        self.penForms = ["None", "Quadratic", "Linear", "Step"]
        #
        self.osolvers = sorted(
            list(self.dat.optSolvers.plugins.keys()), key=lambda s: s.lower()
        )
        self.methods = self.dat.optSolvers.plugins  # dict of solvers
        self.optMonitorFrame = optMonitor(self.dat, self)
        self.tabWidget.addTab(self.optMonitorFrame, "Run")
        self.optMonitorFrame.setStatusBar.connect(self.setStatusBar)
        self.optMonitorFrame.updateGraph.connect(self.updateGraph)
        self.tabWidget.currentChanged.connect(self.switchTab)
        self.running = False
        self.synhi = PythonHighlighter(self.customCodeEdit.document())

    def clearOld(self):
        """
        Clear messages from old optimzation runs
        """
        self.optMonitorFrame.clearMessages()
        try:
            self.optMonitorFrame.clearPlots()
        except:
            pass

    def genSamples(self):
        self.applyChanges()
        prob = self.dat.optProblem
        genDialog = optSampleGenDialog(sorted(prob.vs), self)
        r = genDialog.exec_()
        if r == QDialog.Accepted:
            # call the appropriate method to generate samples
            if genDialog.sampleType == genDialog.SAMPLE_FULL_FACT:
                prob.fullfactorial(genDialog.sampleSettings)
            elif genDialog.sampleType == genDialog.SAMPLE_FILE:
                prob.loadSamples(genDialog.sampleSettings)
            self.updateSampleVarsTable()

    def deleteSamples(self):
        rows = set()
        for item in self.sampleTable.selectedItems():
            rows.add(item.row())
        self.dat.optProblem.deleteSamples(rows)
        self.updateSampleVarsTable()

    def clearSamples(self):
        self.dat.optProblem.clearSamples()
        self.updateSampleVarsTable()

    def addSample(self):
        self.sampleTable.setRowCount(self.sampleTable.rowCount() + 1)

    def updateSampleVarsTable(self):
        prob = self.dat.optProblem
        table = self.sampleTable
        table.setColumnCount(0)
        vs = gh.addColumns(table, prob.vs, s=True)
        table.setRowCount(prob.numSamples())
        ci = gh.colIndexes(table)
        for name in ci:
            for row in range(prob.numSamples()):
                if name in prob.samp:
                    gh.setCellJSON(table, row, ci[name], prob.samp[name][row])
                else:
                    gh.setCellJSON(table, row, ci[name], float("nan"))
        table.resizeColumnsToContents()

    def switchTab(self, i):
        self.applyChanges()

    def showVex(self):
        self.parent().parent().varBrowse.format = "optimization"
        self.parent().parent().varBrowse.nodeMask = None
        self.parent().parent().varBrowse.refreshVars()
        self.parent().parent().varBrowse.show()

    def insertVar(self, v):
        if v == None:
            return
        if len(v) != 3:
            return
        nkey = v[0]
        isInput = v[1] == "input"
        vkey = v[2]

    def updateColIndexes(self):
        """
        Setup dictionaries to look up column indexes.  Makes it easy
        to rearrange the table columns.  The dictionary keys are the
        column headings and the dictionary stores the corresponding
        column index. If the columns are renamed the functions that
        use these column indexes will need to be updated also.
        """
        self.vtCols = dict()  # Variable column indexes
        self.ofCols = dict()  # Objective function column indexes
        self.icCols = dict()  # Inequality constraints column indexes
        for col in range(self.varForm.columnCount()):
            self.vtCols[self.varForm.horizontalHeaderItem(col).text()] = col
        for col in range(self.fTable.columnCount()):
            self.ofCols[self.fTable.horizontalHeaderItem(col).text()] = col
        for col in range(self.gTable.columnCount()):
            self.icCols[self.gTable.horizontalHeaderItem(col).text()] = col

    def revert(self):
        """
        return form contents to current optimization options
        """
        self.refreshContents()

    def applyChanges(self):
        """
        Use information stored in this form to update the
        optimization options
        """
        #
        # Delete optimization settings and rebuild them from the form
        if self.running:
            return
        prob = self.dat.optProblem
        gr = self.dat.flowsheet
        prob.solver = self.solverBox.currentText()
        # Get solver options
        s = self.lastSolver
        prob.solverOptions[s] = {}
        opts = self.methods[s].opt().options
        for row in range(self.solverOptionTable.rowCount()):
            settingName = self.solverOptionTable.item(row, 0).text()
            if opts[settingName].dtype == bool:
                setting = gh.isChecked(self.solverOptionTable, row, 1)
            elif len(opts[settingName].validValues) > 0:
                setting = gh.cellPulldownJSON(self.solverOptionTable, row, 1)
            else:
                setting = gh.getCellJSON(self.solverOptionTable, row, 1)
            prob.solverOptions[s][settingName] = setting
        # Get objective functions
        prob.obj = []
        table = self.fTable
        for row in range(self.fTable.rowCount()):
            pc = gh.getCellText(table, row, self.ofCols["Expression"])
            ps = gh.getCellJSON(table, row, self.ofCols["Penalty Scale"])
            fv = gh.getCellJSON(table, row, self.ofCols["Value for Failure"])
            prob.obj.append(optimObj(pc, ps, fv))
        # Get constraints
        prob.g = []
        table = self.gTable
        for row in range(self.gTable.rowCount()):
            pc = gh.getCellText(table, row, self.icCols["Expression"])
            ps = gh.getCellJSON(table, row, self.icCols["Penalty Factor"])
            pf = gh.getCellText(table, row, self.icCols["Form"])
            prob.g.append(optimInEq(pc, ps, pf))
        # Get decision variables
        prob.v = []
        prob.vs = []
        table = self.varForm
        for row in range(self.varForm.rowCount()):
            name = gh.getCellText(table, row, self.vtCols["Variable"])
            gr.x[name].scaling = gh.getCellText(table, row, self.vtCols["Scale"])
            gr.x[name].min = gh.getCellJSON(table, row, self.vtCols["Min"])
            gr.x[name].max = gh.getCellJSON(table, row, self.vtCols["Max"])
            gr.x[name].value = gh.getCellJSON(table, row, self.vtCols["Value"])
            vt = gh.cellPulldownValue(table, row, self.vtCols["Type"])
            if vt == "Decision":
                prob.v.append(name)
                gr.x[name].optVar = True
            elif vt == "Sample":
                prob.vs.append(name)
            else:
                gr.x[name].optVar = False
        # Get sample information
        table = self.sampleTable
        ci = gh.colIndexes(table)
        n = prob.numSamples()
        for row in range(table.rowCount()):
            if row < n:  # re-set sample data
                for name in ci:
                    if name in prob.samp:
                        prob.samp[name][row] = gh.getCellJSON(table, row, ci[name])
                    else:
                        prob.addSampleVar(name)
                        prob.samp[name][row] = gh.getCellJSON(table, row, ci[name])
            else:
                s = ci.copy()
                for name in s:
                    s[name] = gh.getCellJSON(table, row, ci[name])
                prob.addSample(s)
        # Get objective type
        if self.objTypeCombo.currentIndex() == 0:
            prob.objtype = prob.OBJ_TYPE_EVAL
        elif self.objTypeCombo.currentIndex() == 1:
            prob.objtype = prob.OBJ_TYPE_CUST
        # Get custom code
        prob.custpy = self.customCodeEdit.toPlainText()
        self.updateSampleVarsTable()

    def scaleHelper(self, ind=0):
        """
        If a descision variable has a none scale type set the scale
        to lineae.  For other variables set the scale type to none
        and disable the scale selection.
        """
        table = self.varForm
        typeCol = self.vtCols["Type"]
        scaleCol = self.vtCols["Scale"]
        for row in range(table.rowCount()):
            vtype = gh.getCellText(table, row, typeCol)
            stype = gh.getCellText(table, row, scaleCol)
            if vtype == "Decision":
                if stype == "None":
                    gh.cellPulldownSetText(table, row, scaleCol, "Linear")
                table.cellWidget(row, scaleCol).setEnabled(True)
            else:
                gh.cellPulldownSetText(table, row, scaleCol, "None")
                table.cellWidget(row, scaleCol).setEnabled(False)

    def refreshContents(self):
        """ """
        self.dat.flowsheet.generateGlobalVariables()
        prob = self.dat.optProblem
        x = self.dat.flowsheet.x
        # Set up problem selection combo box
        o = self.dat.optProblem
        # Setup optimization solver selection box
        self.solverBox.blockSignals(True)
        self.solverBox.clear()
        self.solverBox.addItems(self.osolvers)
        if self.osolvers:  # at least on solver available
            indx = self.solverBox.findText(o.solver)
            if indx == -1:
                indx = 0
            self.solverBox.setCurrentIndex(indx)
            self.lastSolver = self.solverBox.currentText()
            self.setSolver(self.lastSolver)
            self.solverBox.blockSignals(False)
        else:  # if no solvers are available
            pass
        # put data into variable table
        row = 0
        self.varForm.clearContents()
        self.varForm.setRowCount(0)
        table = self.varForm
        for vkey in x:
            # only list inputs that are not set by other variables
            if not x[vkey].con:
                self.varForm.setRowCount(self.varForm.rowCount() + 1)
                scale = x[vkey].scaling
                gh.setTableItem(table, row, self.vtCols["Variable"], vkey)
                gh.setTableItem(
                    table,
                    row,
                    self.vtCols["Type"],
                    "Fixed",
                    pullDown=["Fixed", "Decision", "Sample"],
                )
                if vkey in prob.v:
                    gh.cellPulldownSetText(table, row, self.vtCols["Type"], "Decision")
                elif vkey in prob.vs:
                    gh.cellPulldownSetText(table, row, self.vtCols["Type"], "Sample")
                table.cellWidget(row, self.vtCols["Type"]).currentIndexChanged.connect(
                    self.scaleHelper
                )
                gh.setTableItem(
                    table,
                    row,
                    self.vtCols["Scale"],
                    x[vkey].scaling,
                    pullDown=self.scalingOpts,
                )
                gh.setTableItem(
                    table, row, self.vtCols["Min"], x[vkey].min, jsonEnc=True
                )
                gh.setTableItem(
                    table, row, self.vtCols["Max"], x[vkey].max, jsonEnc=True
                )
                gh.setTableItem(
                    table, row, self.vtCols["Value"], x[vkey].value, jsonEnc=True
                )
                row += 1
        self.scaleHelper()
        table.resizeColumnsToContents()
        if not o:
            self.fTable.setRowCount(0)
            self.gTable.setRowCount(0)
            return
        # put data in objective function table
        self.fTable.setRowCount(len(o.obj))
        row = 0
        table = self.fTable
        for f in o.obj:
            gh.setTableItem(table, row, self.ofCols["Expression"], f.pycode)
            gh.setTableItem(
                table, row, self.ofCols["Penalty Scale"], f.penScale, jsonEnc=True
            )
            gh.setTableItem(
                table, row, self.ofCols["Value for Failure"], f.fail, jsonEnc=True
            )
            row += 1
        table.resizeColumnsToContents()
        # put data in inequality constraint table
        self.gTable.setRowCount(len(o.g))
        row = 0
        table = self.gTable
        for f in o.g:
            gh.setTableItem(table, row, self.icCols["Expression"], f.pycode)
            gh.setTableItem(
                table, row, self.icCols["Penalty Factor"], f.penalty, jsonEnc=True
            )
            gh.setTableItem(
                table, row, self.icCols["Form"], f.penForm, pullDown=self.penForms
            )
            row += 1
        table.resizeColumnsToContents()
        # Get objective type
        if prob.objtype == prob.OBJ_TYPE_EVAL:
            self.objTypeCombo.setCurrentIndex(0)
        elif prob.objtype == prob.OBJ_TYPE_CUST:
            self.objTypeCombo.setCurrentIndex(1)
        # Get custom code
        self.customCodeEdit.setPlainText(prob.custpy)
        self.updateSampleVarsTable()

    def setSolver(self, name):
        """
        Set the current solver

        name: the name of the solver to make active
        """
        slvr = self.methods[name].opt()
        self.methodDescriptionBox.setHtml(slvr.methodDescription)
        opts = slvr.options
        ovals = self.dat.optProblem.solverOptions.get(name, None)
        if ovals:
            opts.loadValues(ovals)
        self.solverOptionTable.clearContents()
        self.solverOptionTable.setRowCount(len(opts))
        row = 0
        table = self.solverOptionTable
        for i, opt in enumerate(opts.order):
            gh.setTableItem(table, i, 0, opt, editable=False)
            gh.setTableItem(table, i, 2, opts[opt].desc, editable=False)
            if opts[opt].dtype == bool:
                # If the option is bool type use a check box
                gh.setTableItem(
                    table,
                    i,
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
                    i,
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
                    i,
                    1,
                    opts[opt].value,
                    jsonEnc=True,
                    bgColor=QColor(235, 255, 235),
                )
        table.resizeColumnsToContents()

    def selectSolver(self, indx):
        """
        Called when a solver is selected in the solver combobox
        index:  the combo box index of current selection
            (ignored. is just needed by combo box change signal)
        """
        self.applyChanges()
        self.setSolver(self.solverBox.currentText())
        self.lastSolver = self.solverBox.currentText()

    def addF(self):
        """
        Add an objective function
        """
        self.fTable.setRowCount(self.fTable.rowCount() + 1)

    def delF(self):
        """
        Delete an objective function
        """
        row = self.fTable.currentRow()
        self.fTable.removeRow(row)

    def addG(self):
        """
        Add a new inequality constraint
        """
        self.gTable.setRowCount(self.gTable.rowCount() + 1)
        gh.setTableItem(
            self.gTable,
            self.gTable.rowCount() - 1,
            self.icCols["Form"],
            "Linear",
            pullDown=self.penForms,
        )

    def delG(self):
        """
        Remove an inequality constraint
        """
        row = self.gTable.currentRow()
        self.gTable.removeRow(row)

    def checkInput(self):
        """
        This function checks several things
        1.  At least on optimization variable
        2.  Max > Min for all variables
        3.  Variable scaling other than none for all optimization
            variables
        4.  Python code evaluates without errors
        """
        # New objective types mean this needs fixed.  Commented out checks
        # for now.

        self.applyChanges()
        # self.dat.flowsheet.generateGlobalVariables()
        # pg = self.dat.optSolvers.plugins[self.dat.optProblem.solver].opt(self.dat)
        # e = self.dat.optProblem.check(self.dat.flowsheet, pg.minVars, pg.maxVars)
        # if not e[0] == 0:
        #    QMessageBox.information(self, "Error", "There is an error in the problem definition:\n" + e[1])
        #    return 1
        # QMessageBox.information(self, "Okay", "No Errors detected in problem definition.")
        return 0  # if it gets here no error.
