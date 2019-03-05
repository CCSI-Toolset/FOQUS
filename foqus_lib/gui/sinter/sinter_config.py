import os
import json
import logging
from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5.QtWidgets import QFileDialog, QDialog, QMessageBox
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

        self.show()

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
        d["inputs"] = {}
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
