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
import foqus_lib.gui.helpers.guiHelpers as gh
import os
import json
import logging
import platform
import subprocess

try:
    # pylint: disable=import-error
    from dmf_lib.dmf_browser import DMFBrowser
    from dmf_lib.dialogs.select_repo_dialog import SelectRepoDialog
    from dmf_lib.dialogs.status_dialog import StatusDialog
    from dmf_lib.common.methods import Common
    from dmf_lib.common.common import DMF_HOME
    from dmf_lib.common.common import DMF_LITE_REPO_NAME
    from dmf_lib.common.common import PROP_HEADER
    from dmf_lib.common.common import PROPERTIES_EXT
    from dmf_lib.common.common import REPO_PROPERTIES_UNIX_PATH
    from dmf_lib.common.common import REPO_PROPERTIES_WIN_PATH
    from dmf_lib.common.common import REQUESTS_TIMEOUT
    from dmf_lib.common.common import SC_TITLE
    from dmf_lib.common.common import SHARE_LOGIN_EXT
    from dmf_lib.common.common import UNIX_PATH_SEPARATOR
    from dmf_lib.common.common import UTF8
    from dmf_lib.common.common import WIN_PATH_SEPARATOR
    from dmf_lib.common.common import WINDOWS

    useDMF = True
except ImportError:
    logging.getLogger("foqus." + __name__).exception(
        "Failed to import or launch DMFBrowser"
    )
    useDMF = False
from urllib.request import urlopen
from io import StringIO

from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import QMessageBox, QDialog, QInputDialog, QFileDialog, QLineEdit

mypath = os.path.dirname(__file__)
_dmfUploadDialogUI, _dmfUploadDialog = uic.loadUiType(
    os.path.join(mypath, "dmfUploadDialog_UI.ui")
)


class dmfUploadDialog(_dmfUploadDialog, _dmfUploadDialogUI):
    """
    This class provides a dialog box that allows you to create,
    upload and update simulations to the DMF.
    """

    waiting = QtCore.pyqtSignal()  # signal for start waiting on long task
    notwaiting = QtCore.pyqtSignal()  # signal the task is done

    def __init__(self, dat, turbConfig, parent=None):
        """Initialize dialog"""
        super(dmfUploadDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.root = parent
        self.dat = dat
        # Connect buttons
        self.turb = turbConfig
        self.configFileButton.clicked.connect(self.browseSinter)
        self.sinterConfigGUIButton.clicked.connect(self.showSinterConfigGUI)
        self.addFileButton.clicked.connect(self.addFile)
        self.removeFileButton.clicked.connect(self.removeFile)
        self.relpathButton.clicked.connect(self.setResRelPath)
        self.selectDMFRepoButton.clicked.connect(self.selectDMFRepo)
        self.clearTableButton.clicked.connect(self.clearTable)
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        self.files = [["configuration", ""], ["model", ""]]
        self.updateFileTable()
        self.enableSinterConfigGUI(None)
        if platform.system().startswith(WINDOWS):
            self.PROP_LOC = os.environ[REPO_PROPERTIES_WIN_PATH] + WIN_PATH_SEPARATOR
        else:
            self.PROP_LOC = os.environ[REPO_PROPERTIES_UNIX_PATH] + UNIX_PATH_SEPARATOR
        _, _, repo_props = self.getDMFRepoProperties()
        if self.root.last_dmf_repo and self.root.last_repo_props == repo_props:
            self.currentPropList, repo_name = self.root.last_dmf_repo
        else:
            self.currentPropList = None
            repo_name = DMF_LITE_REPO_NAME
        self.dmfRepo.setText(repo_name)
        if not useDMF:
            QMessageBox.information(self, "Error", "Unable to setup DMF.")

    def getDMFRepoProperties(self):
        config = StringIO()
        # Fake properties header to allow working with configParser
        config.write("[" + PROP_HEADER + "]\n")
        # Get a list of property files for repositories
        repo_props = [
            f
            for f in os.listdir(self.PROP_LOC)
            if os.path.isfile(os.path.join(self.PROP_LOC, f))
            and f.endswith(PROPERTIES_EXT)
        ]
        repo_name_list = []
        status_list = []

        i = 0
        if len(repo_props) > 0:
            print("Validating the following properties file(s):")
        while i < len(repo_props):
            is_valid, return_vals = Common().validateAndGetKeyProps(
                os.path.join(self.PROP_LOC, repo_props[i])
            )
            if is_valid:
                try:
                    response = urlopen(
                        return_vals[1] + SHARE_LOGIN_EXT, timeout=REQUESTS_TIMEOUT
                    )
                    status_code = response.getcode()
                    response.getcode()
                except:
                    status_code = 500
                repo_name_list.append(return_vals[0])
                status_list.append(status_code)
                i += 1
            else:
                repo_props.remove(repo_props[i])
        repo_props = [self.PROP_LOC + e for e in repo_props]
        return repo_name_list, status_list, repo_props

    def selectDMFRepo(self):
        repo_name_list, status_list, repo_props = self.getDMFRepoProperties()
        n_repos = len(repo_props)
        dmf_home = os.environ[DMF_HOME]
        if n_repos == 0:
            config = None
            repo_name = DMF_LITE_REPO_NAME
            self.currentPropList = config
            self.dmfRepo.setText(repo_name)
            StatusDialog.displayStatus(
                "No DMF properties file detected. Defaulting to DMF Lite."
            )
        else:
            dialog = SelectRepoDialog()
            result, index, repo_name = dialog.getDialog(
                repo_name_list, status_list, dmf_home, show_dmf_lite=True
            )
            if not result:
                return
            if index < len(repo_name_list):
                config = repo_props[index]
            else:
                config = None
            self.currentPropList = config
            self.dmfRepo.setText(repo_name)
        self.root.last_dmf_repo = (config, repo_name)  # Save state
        self.root.last_repo_props = repo_props

    def removeSim(self):
        simName = self.simNameEdit.currentText()
        if simName == "":
            return
        self.simNameEdit.removeItem(self.simNameEdit.currentIndex())
        self.fileTable.resizeColumnsToContents()

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
        if not b:
            # automatically decide whether to enable it
            if os.name == "nt":
                # Windows only feature
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
                m, r, a = tc.sinterConfigGetResource(fileName)
                self.files[0] = ["configuration", fileName]
                self.files[1] = [r, m]
                self.updateFileTable()
                self.appEdit.setText(a)
            except:
                logging.getLogger("foqus." + __name__).exception(
                    "Error setting sinter config file"
                )
        self.sinterConfigGUIButton.blockSignals(False)

    def selectedTCRows(self):
        indx = reversed(
            sorted(set([item.row() for item in self.tableWidget.selectedItems()]))
        )
        return indx

    def accept(self):
        """
        If the okay button is press, use the simulation name and
        sinter configuration file path from the dialog to attempt
        to upload simulation files.  The Turbine configuration file
        is a global setting stored in self.dat.turbineConfFile. I'm
        assuming you will want to use the same gateway for a session
        """
        simulation_keys = ["aspenfile", "spreadsheet", "model"]
        sim_name = self.simNameEdit.currentText()
        sinter_config_path = self.files[0][1]
        sinter_config_dir = os.path.dirname(sinter_config_path)
        sinter_config_name = os.path.basename(sinter_config_path)
        resource_bytestream_list = []
        resource_name_list = []

        try:
            if not sinter_config_path:
                raise Exception("No sinter configuration path found.")
            with open(sinter_config_path, "rb") as scf:
                sc_data = json.loads(scf.read())
                for k in simulation_keys:
                    sim_name = sc_data.get(k, None)
                    if isinstance(sim_name, dict):
                        sim_name = sim_name.get("file", None)
                    if sim_name:
                        sim_path = os.path.join(sinter_config_dir, sim_name)
                        break
            if not sim_path:
                raise Exception("No simulation path found.")
            with open(sinter_config_path, "rb") as scf, open(sim_path, "rb") as sim:
                confidence = "experimental"
                sim_id = DMFBrowser.getSimIDByName(
                    self, self.currentPropList, self.dmfRepo.text(), sim_name
                )
                DMFBrowser.uploadSimulation(
                    self,
                    self.currentPropList,
                    self.dmfRepo.text(),
                    sim_bytestream=bytearray(sim.read()),
                    sim_id=sim_id,
                    sim_name=sim_name,
                    update_comment=None,
                    confidence=confidence,
                    sinter_config_bytestream=bytearray(scf.read()),
                    sinter_config_name=sinter_config_name,
                    resource_bytestream_list=resource_bytestream_list,
                    resource_name_list=resource_name_list,
                )
        except Exception as e:
            print(e)
            QMessageBox.information(self, "Error", str(e))
            return
        finally:
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
            isNewSinterConfFmt = False
            try:
                tc = self.dat.flowsheet.turbConfig
                m, r, a = tc.sinterConfigGetResource(fileName)
                self.files[0] = ["configuration", fileName]
                self.files[1] = [r, m]
                self.updateFileTable()
                self.appEdit.setText(a)
            except Exception as e:
                isNewSinterConfFmt = True
            if isNewSinterConfFmt:
                try:
                    self.files[0] = ["configuration", fileName]
                    with open(str(fileName), "rb") as f:
                        scf = json.loads(f.read().decode("utf-8"))
                        print(scf["model"]["file"])
                        m = scf["model"]["file"]
                        m_path = os.path.join(os.path.dirname(fileName), m)
                        _, m_ext = os.path.splitext(m_path)
                        a = tc.appExtensions.get(m_ext, None)
                        self.files[1] = ["model", m_path]
                    self.updateFileTable()
                    self.appEdit.setText(a)
                except Exception as e:
                    QMessageBox.information(self, "Error", str(e))
                    logging.getLogger("foqus." + __name__).exception(
                        "Error reading sinter config"
                    )

            if self.simNameEdit.currentText() == "":
                try:
                    with open(fileName, "r") as f:
                        sc_json = json.loads(f.read().decode(UTF8))
                        simNameGuess = sc_json[SC_TITLE]
                except Exception as e:
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

    def clearTable(self):
        # Reinitialize
        self.files = [["configuration", ""], ["model", ""]]
        self.simNameEdit.clear()
        self.appEdit.clear()
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
