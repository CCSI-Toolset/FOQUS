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
import json
import logging
from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QFileDialog,
    QDialog,
    QMessageBox,
    QAbstractItemView,
    QTableWidgetItem,
)
import hashlib
import foqus_lib.gui.helpers.guiHelpers as gh

_log = logging.getLogger(__name__)

mypath = os.path.dirname(__file__)
_sinterConfigUI, _sinterConfig = uic.loadUiType(
    os.path.join(mypath, "sinter_config.ui")
)


class SinterConfigMainWindow(_sinterConfigUI, _sinterConfig):
    def __init__(
        self, parent=None, title="SimSinter Configuration editor", width=800, height=600
    ):
        super().__init__(parent=None)
        self.setupUi(self)
        self.actionQuit.triggered.connect(self.close)
        self.actionSave.triggered.connect(self._save_dialog)
        self.actionLoad.triggered.connect(self._load_dialog)
        self.set_working_dir.clicked.connect(self._browse_for_working_dir)
        self.model_browse.clicked.connect(self._model_browse)
        self.digest_calculate.clicked.connect(self._calc_model_digest)
        self.add_input_file.clicked.connect(self._add_input_file)
        self.del_input_file.clicked.connect(self._del_input_file)
        self.add_input.clicked.connect(self._add_input)
        self.add_output.clicked.connect(self._add_output)
        self.delete_input.clicked.connect(self._del_input)
        self.delete_output.clicked.connect(self._del_output)
        self.outputs_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.inputs_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.input_files_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.outputs_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.inputs_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.input_files_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.inputs_table.setRowCount(0)
        self.outputs_table.setRowCount(0)
        self.input_files_table.setRowCount(0)
        self.show()

    def _add_input_file(self):
        dialog = QFileDialog(self, "Model File", directory=os.getcwd())
        if dialog.exec_() == QDialog.Accepted:
            res = dialog.selectedFiles()[0]
            file = os.path.relpath(res)
            row = self.input_files_table.rowCount()
            self.input_files_table.setRowCount(row + 1)
            gh.setTableItem(self.input_files_table, row, 0, file)
            with open(file, "rb") as fp:
                h = hashlib.sha1(fp.read()).hexdigest()
            gh.setTableItem(self.input_files_table, row, 1, h)
            gh.setTableItem(self.input_files_table, row, 2, "sha1", pullDown=["sha1"])
            self.input_files_table.resizeColumnsToContents()

    def _add_blank_input_file(self):
        row = self.input_files_table.rowCount()
        self.input_files_table.setRowCount(row + 1)
        gh.setTableItem(self.input_files_table, row, 0, "")
        gh.setTableItem(self.input_files_table, row, 1, "")
        gh.setTableItem(self.input_files_table, row, 2, "sha1", pullDown=["sha1"])

    def _del_input_file(self):
        if len(self.input_files_table.selectedIndexes()) == 0:
            return
        row = self.input_files_table.selectedIndexes()[0].row()
        self.input_files_table.removeRow(row)

    def _model_browse(self):
        dialog = QFileDialog(self, "Model File", directory=os.getcwd())
        if dialog.exec_() == QDialog.Accepted:
            res = dialog.selectedFiles()[0]
            self.model_file.setText(os.path.relpath(res))

    def _add_input(self):
        row = self.inputs_table.rowCount()
        self.inputs_table.setRowCount(row + 1)
        for i in range(8):
            if i == 2:
                gh.setTableItem(
                    self.inputs_table,
                    row,
                    i,
                    "double",
                    pullDown=["double", "int", "string"],
                )
            else:
                gh.setTableItem(self.inputs_table, row, i, "")

    def _add_output(self):
        row = self.outputs_table.rowCount()
        self.outputs_table.setRowCount(row + 1)
        for i in range(6):
            if i == 2:
                gh.setTableItem(
                    self.outputs_table,
                    row,
                    i,
                    "double",
                    pullDown=["double", "int", "string"],
                )
            else:
                gh.setTableItem(self.outputs_table, row, i, "")

    def _del_input(self):
        if len(self.inputs_table.selectedIndexes()) == 0:
            return
        row = self.inputs_table.selectedIndexes()[0].row()
        self.inputs_table.removeRow(row)

    def _del_output(self):
        if len(self.outputs_table.selectedIndexes()) == 0:
            return
        row = self.outputs_table.selectedIndexes()[0].row()
        self.outputs_table.removeRow(row)

    def _calc_model_digest(self):
        file = self.model_file.text()
        try:
            with open(file, "rb") as fp:
                self.model_digest_value.setText(hashlib.sha1(fp.read()).hexdigest())
        except:
            _log.exception("Failed to has model file {}".format(file))

    def _save_dialog(self):
        file = "{}{}".format(self.model_file.text().split(".")[0], ".json")
        dialog = QFileDialog(self, "Save Config", directory=os.getcwd())
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.selectFile(file)
        if dialog.exec_() == QDialog.Accepted:
            self._save(file=dialog.selectedFiles()[0])
            return True
        return False

    def _load_dialog(self):
        dialog = QFileDialog(self, "Load Config", directory=os.getcwd())
        if dialog.exec_() == QDialog.Accepted:
            self._load(file=dialog.selectedFiles()[0])
            return True
        return False

    def _load(self, file="test.json"):
        try:
            with open(file, "r") as fp:
                d = json.load(fp)
        except:
            _log.exception("Couldn't load file {}".format(file))
            return

        # Currently doesn't load these because you can't change them
        # filetype, filetype-version, and SignatureMethodAlgorithm
        index = self.application_name.findText(d["application"].get("name", ""))
        if index >= 0:
            self.application_name.setCurrentIndex(index)
        self.application_version.setText(d["application"].get("version", ""))
        self.title.setText(d.get("title", ""))
        self.author.setText(d.get("author", ""))
        self.date.setText(d.get("date", ""))
        self.description.setText(d.get("description", ""))
        self.config_version.setText(d.get("config-version", "1.0"))
        if "model" in d:
            self.model_file.setText(d["model"].get("file", ""))
            self.model_digest_value.setText(d["model"].get("DigestValue", ""))
        tbl = self.settings_table
        for row in range(tbl.rowCount()):
            if not "settings" in d:
                break
            sname = tbl.verticalHeaderItem(row).text()
            if sname in d["settings"]:
                gh.setCellText(tbl, row, 0, d["settings"][sname]["type"])
                gh.setCellText(tbl, row, 1, d["settings"][sname]["default"])
                gh.setCellText(tbl, row, 2, d["settings"][sname]["description"])
        files = d.get("input-files", [])
        tbl = self.input_files_table
        tbl.setRowCount(0)
        for row, file in enumerate(files):
            self._add_blank_input_file()
            gh.setCellText(tbl, row, 0, file["file"])
            gh.setCellText(tbl, row, 1, file["DigestValue"])
            gh.cellPulldownSetText(tbl, row, 2, file["SignatureMethodAlgorithm"])
        tbl = self.inputs_table
        tbl.setRowCount(0)
        for x, xd in d.get("inputs", {}).items():
            row = tbl.rowCount()
            self._add_input()
            gh.setCellText(tbl, row, 0, x)
            gh.setCellText(tbl, row, 1, xd.get("path", [""])[0])
            gh.cellPulldownSetText(tbl, row, 2, xd.get("type", "double"))
            gh.setCellText(tbl, row, 3, xd.get("default", ""))
            gh.setCellText(tbl, row, 4, xd.get("max", ""))
            gh.setCellText(tbl, row, 5, xd.get("min", ""))
            units = xd.get("units", "")
            if units is None:
                units = ""
            gh.setCellText(tbl, row, 6, units)
            gh.setCellText(tbl, row, 7, xd.get("description", ""))
        tbl = self.outputs_table
        tbl.setRowCount(0)
        for x, xd in d.get("outputs", {}).items():
            row = tbl.rowCount()
            self._add_output()
            gh.setCellText(tbl, row, 0, x)
            gh.setCellText(tbl, row, 1, xd.get("path", [""])[0])
            gh.cellPulldownSetText(tbl, row, 2, xd.get("type", "double"))
            gh.setCellText(tbl, row, 3, xd.get("default", ""))
            units = xd.get("units", "")
            if units is None:
                units = ""
            gh.setCellText(tbl, row, 4, units)
            gh.setCellText(tbl, row, 5, xd.get("description", ""))

    def _save(self, file="test.json"):
        d = {}
        d["application"] = {}
        d["application"]["name"] = self.application_name.currentText()
        d["application"]["version"] = self.application_version.text()
        d["application"]["constraint"] = self.application_constraint.currentText()
        d["filetype"] = self.filetype.currentText()
        d["filetype-version"] = float(self.filetype_version.currentText())
        d["title"] = self.title.text()
        d["author"] = self.author.text()
        d["date"] = self.date.text()
        d["description"] = self.description.text()
        d["config-version"] = self.config_version.text()
        d["model"] = {}
        d["model"]["file"] = self.model_file.text()
        d["model"]["DigestValue"] = self.model_digest_value.text()
        d["input-files"] = []
        tbl = self.input_files_table
        for row in range(tbl.rowCount()):
            d2 = {}
            d2["file"] = gh.getCellText(tbl, row, 0)
            d2["DigestValue"] = gh.getCellText(tbl, row, 1)
            d2["SignatureMethodAlgorithm"] = gh.getCellText(tbl, row, 2)
            d["input-files"].append(d2)
        d["settings"] = {}
        tbl = self.settings_table
        for row in range(tbl.rowCount()):
            sname = tbl.verticalHeaderItem(row).text()
            d["settings"][sname] = {}
            d["settings"][sname]["type"] = gh.getCellText(tbl, row, 0)
            d["settings"][sname]["default"] = gh.getCellText(tbl, row, 1)
            d["settings"][sname]["description"] = gh.getCellText(tbl, row, 2)
        d["inputs"] = {}
        tbl = self.inputs_table
        for row in range(tbl.rowCount()):
            name = gh.getCellText(tbl, row, 0)
            d["inputs"][name] = {}
            d["inputs"][name]["path"] = [gh.getCellText(tbl, row, 1)]
            d["inputs"][name]["type"] = gh.getCellText(tbl, row, 2)
            d["inputs"][name]["default"] = gh.getCellText(tbl, row, 3)
            d["inputs"][name]["max"] = gh.getCellText(tbl, row, 4)
            d["inputs"][name]["min"] = gh.getCellText(tbl, row, 5)
            d["inputs"][name]["units"] = gh.getCellText(tbl, row, 6)
            d["inputs"][name]["description"] = gh.getCellText(tbl, row, 7)
            if d["inputs"][name]["units"] == "":
                d["inputs"][name]["units"] = None
            if d["inputs"][name]["type"] in ["int", "double"]:
                if d["inputs"][name]["default"] == "":
                    d["inputs"][name]["default"] = 0
                if d["inputs"][name]["min"] == "":
                    d["inputs"][name]["min"] = 0
                if d["inputs"][name]["max"] == "":
                    d["inputs"][name]["max"] = 0
            if d["inputs"][name]["type"] == "int":
                try:
                    d["inputs"][name]["default"] = int(d["inputs"][name]["default"])
                    d["inputs"][name]["min"] = int(d["inputs"][name]["min"])
                    d["inputs"][name]["max"] = int(d["inputs"][name]["max"])
                except:
                    _log.exception("Error converting to int")
            elif d["inputs"][name]["type"] == "double":
                try:
                    d["inputs"][name]["default"] = float(d["inputs"][name]["default"])
                    d["inputs"][name]["min"] = float(d["inputs"][name]["min"])
                    d["inputs"][name]["max"] = float(d["inputs"][name]["max"])
                except:
                    _log.exception("Error converting to double")
            elif d["inputs"][name]["type"] == "string":
                del d["inputs"][name]["min"]
                del d["inputs"][name]["max"]
        d["outputs"] = {}
        tbl = self.outputs_table
        for row in range(tbl.rowCount()):
            name = gh.getCellText(tbl, row, 0)
            d["outputs"][name] = {}
            d["outputs"][name]["path"] = [gh.getCellText(tbl, row, 1)]
            d["outputs"][name]["type"] = gh.getCellText(tbl, row, 2)
            d["outputs"][name]["default"] = gh.getCellText(tbl, row, 3)
            d["outputs"][name]["units"] = gh.getCellText(tbl, row, 4)
            d["outputs"][name]["description"] = gh.getCellText(tbl, row, 5)
            if d["outputs"][name]["units"] == "":
                d["outputs"][name]["units"] = None
            if d["outputs"][name]["type"] in ["int", "double"]:
                if d["outputs"][name]["default"] == "":
                    d["outputs"][name]["default"] = 0
            if d["outputs"][name]["type"] == "int":
                try:
                    d["outputs"][name]["default"] = int(d["outputs"][name]["default"])
                except:
                    _log.exception("Error converting to int")
            elif d["outputs"][name]["type"] == "double":
                try:
                    d["outputs"][name]["default"] = float(d["outputs"][name]["default"])
                except:
                    _log.exception("Error converting to double")
        with open(file, "w") as fp:
            json.dump(d, fp, indent=2)

    def _browse_for_working_dir(self):
        dialog = QFileDialog(self, "Working Directory", directory=os.getcwd())
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        if dialog.exec_() == QDialog.Accepted:
            res = dialog.selectedFiles()[0]
            self._set_working_dir(res)

    def _set_working_dir(self, wdir):
        os.chdir(wdir)

    def closeEvent(self, event):
        """
        Intercept close main window close event, make sure you really want to quit
        """
        msgBox = QMessageBox()
        msgBox.setText("Do you want to save the session before exiting?")
        msgBox.setStandardButtons(QMessageBox.No | QMessageBox.Yes | QMessageBox.Cancel)
        msgBox.setDefaultButton(QMessageBox.No)
        ret = msgBox.exec_()
        if ret == QMessageBox.No:  # close and don't save
            event.accept()
        elif ret == QMessageBox.Yes:  # close and save
            if self._save_dialog():
                event.accept()
            else:
                event.ignore()
        else:  # Cancel
            event.ignore()
