import os
import json
import logging
from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5.QtWidgets import QFileDialog, QDialog, QMessageBox, QAbstractItemView
import hashlib

_log = logging.getLogger(__name__)

mypath = os.path.dirname(__file__)
_sinterConfigUI, _sinterConfig = \
        uic.loadUiType(os.path.join(mypath, "sinter_config.ui"))

class SinterConfigMainWindow(_sinterConfigUI, _sinterConfig):
    def __init__(self, parent=None,
        title="SimSinter Configuration editor", width=800, height=600):
        super().__init__(parent=None)
        self.setupUi(self)
        self.actionQuit.triggered.connect(self.close)
        self.actionSave.triggered.connect(self._save_dialog)
        self.actionLoad.triggered.connect(self._load_dialog)
        self.set_working_dir.clicked.connect(self._browse_for_working_dir)
        self.digest_calculate.clicked.connect(self._calc_model_digest)
        self.add_input.clicked.connect(self._add_input)
        self.add_output.clicked.connect(self._add_output)
        self.delete_input.clicked.connect(self._del_input)
        self.delete_output.clicked.connect(self._del_output)
        self.outputs_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.inputs_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.outputs_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.inputs_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.show()

    def _add_input(self):
        self.inputs_table.setRowCount(self.inputs_table.rowCount() + 1)

    def _add_output(self):
        self.outputs_table.setRowCount(self.outputs_table.rowCount() + 1)

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
        self._save()
        return True

    def _load_dialog(self):
        self._load()
        return True

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
            self.model_digest_value.setText(d["model"].get("DigestValue",""))
        for row in range(self.settings_table.rowCount()):
            if not "settings" in d:
                break
            sname = self.settings_table.verticalHeaderItem(row).text()
            if sname in d["settings"]:
                self.settings_table.item(row, 0).setText(
                    d["settings"][sname]["type"])
                self.settings_table.item(row, 1).setText(
                    d["settings"][sname]["default"])
                self.settings_table.item(row, 2).setText(
                    d["settings"][sname]["description"])

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
        d["settings"] = {}
        for row in range(self.settings_table.rowCount()):
            sname = self.settings_table.verticalHeaderItem(row).text()
            d["settings"][sname] = {}
            d["settings"][sname]["type"] = \
                self.settings_table.item(row, 0).text()
            d["settings"][sname]["default"] = \
                self.settings_table.item(row, 1).text()
            d["settings"][sname]["description"] = \
                self.settings_table.item(row, 2).text()
        d["inputs"] = {}
        for i in range(self.inputs_table.rowCount()):
            name = self.inputs_table.item(i, 0).text()
            d["inputs"][name] = {}
            d["inputs"][name]["path"] = [self.inputs_table.item(i, 1).text()]
            d["inputs"][name]["type"] = self.inputs_table.item(i, 2).text()
            if d["inputs"][name]["type"] == "float":
                d["inputs"][name]["type"] = "double"
            d["inputs"][name]["default"] = self.inputs_table.item(i, 3).text()
            d["inputs"][name]["max"] = self.inputs_table.item(i, 4).text()
            d["inputs"][name]["min"] = self.inputs_table.item(i, 5).text()
            d["inputs"][name]["units"] = self.inputs_table.item(i, 6).text()
            d["inputs"][name]["description"] = self.inputs_table.item(i, 7).text()
            if d["inputs"][name]["type"] == "int":
                d["inputs"][name]["default"] = int(d["inputs"][name]["default"])
                d["inputs"][name]["min"] = int(d["inputs"][name]["min"])
                d["inputs"][name]["max"] = int(d["inputs"][name]["max"])
            elif d["inputs"][name]["type"] == "double":
                d["inputs"][name]["default"] = float(d["inputs"][name]["default"])
                d["inputs"][name]["min"] = float(d["inputs"][name]["min"])
                d["inputs"][name]["max"] = float(d["inputs"][name]["max"])

        d["outputs"] = {}
        with open(file, "w") as fp:
            json.dump(d, fp, indent=2)

    def _browse_for_working_dir(self):
        dialog = QFileDialog(self, 'Working Directory', directory=os.getcwd())
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
        msgBox.setText(
            "Do you want to save the session before exiting?")
        msgBox.setStandardButtons(QMessageBox.No|QMessageBox.Yes
                                  |QMessageBox.Cancel)
        msgBox.setDefaultButton(QMessageBox.No)
        ret = msgBox.exec_()
        if ret == QMessageBox.No: #close and don't save
            event.accept()
        elif ret == QMessageBox.Yes: #close and save
            if self._save_dialog():
                event.accept()
            else:
                event.ignore()
        else: # Cancel
            event.ignore()
