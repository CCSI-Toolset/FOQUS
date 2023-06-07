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
"""gatewayUploadDialog.py
* dialog to upload files to Turbine gatwaye

John Eslick, Carnegie Mellon University, 2014
"""
import json
import os
import sys
import subprocess
import logging
import foqus_lib.gui.helpers.guiHelpers as gh
from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import QMessageBox, QDialog, QInputDialog, QFileDialog, QLineEdit

mypath = os.path.dirname(__file__)
_gatewayUploadDialogUI, _gatewayUploadDialog = uic.loadUiType(
    os.path.join(mypath, "gatewayUploadDialog_UI.ui")
)


class gatewayUploadDialog(_gatewayUploadDialog, _gatewayUploadDialogUI):
    """
    This class provides a dialog box that allows you to create,
    upload and update simulations on the Turbine Science Gateway.
    """

    waiting = QtCore.pyqtSignal()  # signal for start waiting on long task
    notwaiting = QtCore.pyqtSignal()  # signal the task is done

    def __init__(self, dat, turbConfig, parent=None):
        """
        Initialize dialog
        """
        super(gatewayUploadDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.dat = dat
        # Connect buttons
        self.turb = turbConfig
        self.configFileButton.clicked.connect(self.browseSinter)
        self.sinterConfigGUIButton.clicked.connect(self.showSinterConfigGUI)
        self.addFileButton.clicked.connect(self.addFile)
        self.removeFileButton.clicked.connect(self.removeFile)
        self.relpathButton.clicked.connect(self.setResRelPath)
        self.deleteSimButton.clicked.connect(self.deleteSim)
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        self.files = [["configuration", ""], ["model", ""]]
        self.updateFileTable()
        self.enableSinterConfigGUI(None)
        try:
            simList = self.turb.getSimulationList()
            self.simNameEdit.addItem("")
            self.simNameEdit.addItems(simList)
        except:
            pass
        self.currentRadio.clicked.connect(self.updateTurbineTable)
        self.remoteRadio.clicked.connect(self.updateTurbineTable)
        self.localRadio.clicked.connect(self.updateTurbineTable)
        self.lrRadio.clicked.connect(self.updateTurbineTable)
        self.multiRadio.clicked.connect(self.updateTurbineTable)
        self.addConfigButton.clicked.connect(self.addTurbineConf)
        self.removeConfigButton.clicked.connect(self.delTurbineConf)
        self.updateTurbineTable()

    def deleteSim(self):
        simName = self.simNameEdit.currentText()
        if simName == "":
            return
        try:
            # try to delete Sim
            self.waiting.emit()
            self.turb.deleteSimulation(simName)
        except Exception as e:
            QMessageBox.information(self, "Error", str(e))
            self.notwaiting.emit()
            return
        self.notwaiting.emit()
        self.simNameEdit.removeItem(self.simNameEdit.currentIndex())

    def updateFileTable(self):
        self.fileTable.setRowCount(0)
        self.fileTable.setRowCount(len(self.files))
        for row, f in enumerate(self.files):
            gh.setTableItem(self.fileTable, row, 0, text=f[0], editable=False)
            gh.setTableItem(self.fileTable, row, 1, text=f[1], editable=False)
        self.fileTable.resizeColumnsToContents()

    def enableSinterConfigGUI(self, b=True):
        """
        Enable or disable the sinter config gui launch button
        should be enabled in sinterConfigGui path is set right and
        you are on windows.  SinterConfigGUI is windows only
        """
        if b == None:
            # automatically decide whether to enable it
            if os.name == "nt":
                # is a windows only feature
                exepath = str(self.dat.foqusSettings.simsinter_path)
                exepath = os.path.join(exepath, "SinterConfigGUI.exe")
                if os.path.isfile(exepath):
                    # only if config points to a file
                    b = True
                else:
                    b = False
            else:
                b = False
        self.sinterConfigGUIButton.setEnabled(b)

    def showSinterConfigGUI(self):
        """
        Run sinter config gui so you can create or edit a
        sinter config file
        """
        # need to find a way to prevent clicking this button several
        # times after this function returns any button clicks that were
        # stored up sent signals.  But they happen after fnction returns
        # so can't figure out how to block them.  launch process in a
        # seperate thread?
        exepath = str(self.dat.foqusSettings.simsinter_path)
        exepath = os.path.join(exepath, "SinterConfigGUI.exe")
        tmp_file = os.path.abspath("temp\\sc_out.txt")
        try:
            sinterConfigPath = self.files[0][1]
        except:
            sinterConfigPath = '""'
        self.sinterConfigGUIButton.blockSignals(True)  # this isn't working
        self.waiting.emit()
        process = subprocess.Popen([exepath, sinterConfigPath, tmp_file])
        process.wait()
        self.notwaiting.emit()
        try:
            with open(tmp_file, "r") as f:
                fileName = f.readline().strip()
        except:
            fileName = ""
        try:
            os.remove(tmp_file)
        except:
            pass
        if fileName != "":
            try:
                tc = self.dat.flowsheet.turbConfig
                m, r, a, oth = tc.sinterConfigGetResource(fileName)
                di = os.path.dirname(os.path.abspath(m))
                self.files[0] = ["configuration", fileName]
                self.files[1] = [r, m]
                for f in oth:
                    f = f.get("file", None)
                    if f is not None:
                        self.files.append([f, os.path.join(di, f)])
                self.updateFileTable()
                self.appEdit.setText(a)
            except:
                logging.getLogger("foqus." + __name__).exception(
                    "Error setting sinter config file"
                )
        self.sinterConfigGUIButton.blockSignals(False)

    def addTurbineConf(self):
        # Browse for a file
        fileNames, filtr = QFileDialog.getOpenFileNames(
            self,
            "Additional Files",
            "",
            "Config files (*.cfg);;Text Files (*.txt);;All Files (*)",
        )
        if fileNames:
            tbl = self.tableWidget
            tc = self.dat.flowsheet.turbConfig
            for fn in fileNames:
                i = tbl.rowCount()
                tbl.setRowCount(tbl.rowCount() + 1)
                gh.setTableItem(tbl, i, 0, tc.readConfigPeek(fn), editable=False)
                gh.setTableItem(tbl, i, 1, fn, editable=False)

    def delTurbineConf(self):
        rows = self.selectedTCRows()
        for i in rows:
            self.tableWidget.removeRow(i)

    def selectedTCRows(self):
        indx = reversed(
            sorted(set([item.row() for item in self.tableWidget.selectedItems()]))
        )
        return indx

    def updateTurbineTable(self):
        tc = self.dat.flowsheet.turbConfig
        localFile = self.dat.foqusSettings.turbConfig
        remoteFile = self.dat.foqusSettings.turbConfigCluster
        localAddress = tc.readConfigPeek(localFile)
        remoteAddress = tc.readConfigPeek(remoteFile)
        if self.multiRadio.isChecked():
            self.addConfigButton.setEnabled(True)
            self.removeConfigButton.setEnabled(True)
        else:
            self.addConfigButton.setEnabled(False)
            self.removeConfigButton.setEnabled(False)
        if self.currentRadio.isChecked():
            self.tableWidget.clearContents()
            self.tableWidget.setRowCount(1)
            gh.setTableItem(self.tableWidget, 0, 0, tc.address, editable=False)
            gh.setTableItem(self.tableWidget, 0, 1, tc.path, editable=False)
            self.tableWidget.resizeColumnsToContents()
        elif self.remoteRadio.isChecked():
            self.tableWidget.clearContents()
            self.tableWidget.setRowCount(1)
            gh.setTableItem(self.tableWidget, 0, 0, remoteAddress, editable=False)
            gh.setTableItem(self.tableWidget, 0, 1, remoteFile, editable=False)
            self.tableWidget.resizeColumnsToContents()
        elif self.localRadio.isChecked():
            self.tableWidget.clearContents()
            self.tableWidget.setRowCount(1)
            gh.setTableItem(self.tableWidget, 0, 0, localAddress, editable=False)
            gh.setTableItem(self.tableWidget, 0, 1, localFile, editable=False)
            self.tableWidget.resizeColumnsToContents()
        elif self.lrRadio.isChecked():
            self.tableWidget.clearContents()
            self.tableWidget.setRowCount(2)
            gh.setTableItem(self.tableWidget, 0, 0, localAddress, editable=False)
            gh.setTableItem(self.tableWidget, 0, 1, localFile, editable=False)
            gh.setTableItem(self.tableWidget, 1, 0, remoteAddress, editable=False)
            gh.setTableItem(self.tableWidget, 1, 1, remoteFile, editable=False)
            self.tableWidget.resizeColumnsToContents()
        elif self.multiRadio.isChecked():
            self.tableWidget.clearContents()
            self.tableWidget.setRowCount(0)

    def accept(self):
        """
        If the okay button is press, use the simulation name and
        sinter configuration file path from the dialog to attempt
        to upload simulation files.  The Turbine configuration file
        is a global setting stored in self.dat.turbineConfFile. I'm
        assuming you will want to use the same gateway for a session
        """
        simName = self.simNameEdit.currentText()
        sinterConfigPath = self.files[0][1]
        if len(self.files) > 2:
            # First update from table in case user edited resource name
            for i in range(2, len(self.files)):
                self.files[i][0] = gh.getCellText(self.fileTable, i, 0)
                self.files[i][1] = gh.getCellText(self.fileTable, i, 1)
            other = self.files[2:]
        else:
            other = []
        tcfgs = []
        for i in range(self.tableWidget.rowCount()):
            tcfgs.append(gh.getCellText(self.tableWidget, i, 1))
        for tcfg in tcfgs:
            self.waiting.emit()
            try:
                # try to upload config, simulation, and any extra files
                self.turb.updateSettings(altConfig=tcfg)
                self.turb.uploadSimulation(
                    simName, sinterConfigPath, update=True, otherResources=other
                )
            except Exception as e:
                QMessageBox.information(self, "Error", str(e))
                self.notwaiting.emit()
                self.turb.updateSettings()
                return
            finally:
                self.notwaiting.emit()
        # If uploaded to a Turbine gatway other that the current,
        # make sure the turbine version is set back to proper value.
        self.turb.updateSettings()
        self.done(QDialog.Accepted)

    def reject(self):
        """
        If cancel just do nothing and close dialog
        """
        self.done(QDialog.Rejected)

    def browseSinter(self):
        """
        Browse for a Sinter configuration file.
        """
        fileName, filtr = QFileDialog.getOpenFileName(
            self,
            "Open Sinter Configuration File",
            "",
            "JSON Files (*.json);;All Files (*)",
        )
        if fileName:
            fileName = os.path.normpath(fileName)
            try:
                tc = self.dat.flowsheet.turbConfig
                m, r, a, oth = tc.sinterConfigGetResource(fileName)
                self.files[0] = ["configuration", fileName]
                self.files[1] = [r, m]
                di = os.path.dirname(os.path.abspath(m))
                for f in oth:
                    f = f.get("file", None)
                    if f is not None:
                        self.files.append([f, os.path.join(di, f)])
                self.updateFileTable()
                self.appEdit.setText(a)
            except Exception as e:
                QMessageBox.information(self, "Error", str(e))
                logging.getLogger("foqus." + __name__).exception(
                    "Error reading sinter config"
                )
            if self.simNameEdit.currentText() == "":
                simNameGuess = os.path.basename(fileName)
                simNameGuess = simNameGuess.rsplit(".")[0]
                self.simNameEdit.addItem(simNameGuess)
                i = self.simNameEdit.findText(simNameGuess)
                self.simNameEdit.setCurrentIndex(i)
            self.simNameEdit.setFocus()

    def addFile(self):
        """
        Add additional files required for a simulation
        """
        # Browse for a file
        fileNames, filtr = QFileDialog.getOpenFileNames(
            self, "Additional Files", "", "All Files (*)"
        )
        if fileNames:
            for fileName in fileNames:
                fileName = os.path.normpath(fileName)
                self.files.append([os.path.basename(fileName), fileName])
        self.updateFileTable()

    def removeFile(self):
        indx = reversed(
            sorted(
                set(
                    [
                        item.row()
                        for item in self.fileTable.selectedItems()
                        if item.row() > 1
                    ]
                )
            )
        )
        for i in indx:
            self.files.pop(i)
        self.updateFileTable()

    def setResRelPath(self):
        rows = set()
        for item in self.fileTable.selectedItems():
            rows.add(item.row())
        # Can't set relative path of the config or sim files so warn
        # if selected and drop the indexes for those rows
        if 0 in rows:
            QMessageBox.information(
                self, "Warning", "Won't set releative path for configuration"
            )
        if 1 in rows:
            QMessageBox.information(
                self, "Warning", "Won't set releative path for model"
            )
        rows.discard(0)
        rows.discard(1)
        if len(rows) == 0:
            return
        relpath, ok = QInputDialog.getText(
            self,
            "Relative path",
            "Enter a relative path for selected resources:",
            QLineEdit.Normal,
        )
        if ok:
            relpath = relpath.strip()
            relpath = relpath.strip("\\/")
        for row in rows:
            gh.setCellText(
                self.fileTable, row, 0, "\\".join([relpath, self.files[row][0]])
            )
