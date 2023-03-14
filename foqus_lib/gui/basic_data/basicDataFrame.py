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
import logging
import platform
import subprocess
from urllib.request import urlopen

from io import StringIO

if os.name == "nt":
    try:
        import win32process
    except:
        pass

from PyQt5 import uic
from PyQt5.QtWidgets import QFileDialog

mypath = os.path.dirname(__file__)
_basicDataFrameUI, _basicDataFrame = uic.loadUiType(
    os.path.join(mypath, "basicDataFrame_UI.ui")
)


class basicDataFrame(_basicDataFrame, _basicDataFrameUI):
    def __init__(self, dat, parent=None):
        super(basicDataFrame, self).__init__(parent)
        self.setupUi(self)
        self.dat = dat
        self.folderBrowse_button.clicked.connect(self.chooseInputFolder)
        # self.ingest_button.clicked.connect(self.ingest)
        """
        config = StringIO()
        # Fake properties header to allow working with configParser
        config.write('[' + PROP_HEADER + ']\n')
        # Get a list of property files for repositories
        if platform.system().startswith(WINDOWS):
            self.PROP_LOC = os.environ[REPO_PROPERTIES_WIN_PATH] + \
                WIN_PATH_SEPARATOR
        else:
            self.PROP_LOC = os.environ[REPO_PROPERTIES_UNIX_PATH] + \
                UNIX_PATH_SEPARATOR
        self.repo_properties = [f for f in os.listdir(self.PROP_LOC)
                                if os.path.isfile(os.path.join(
                                    self.PROP_LOC, f))
                                and f.endswith(PROPERTIES_EXT)]"""

    def chooseInputFolder(self):
        self.fname = QFileDialog.getExistingDirectory(self, "Input Directory")
        if self.fname == "":
            return
        else:
            self.selected_folder.setText(self.fname)

    """
    def ingest(self):
        try:
            self.fname
            if self.fname == '':
                raise AttributeError
            if platform.system().startswith(WINDOWS):
                ingest_script_loc = os.path.join(
                    os.environ[DMF_HOME], "DMF_BasicDataIngest.exe")
            else:
                ingest_script_loc = os.path.join(
                    os.environ[DMF_HOME], "DMF_BasicDataIngest.py")

            i = 0
            repo_name_list = []
            url_list = []
            status_list = []
            while i < len(self.repo_properties):
                is_valid, return_val = Common().validateAndGetKeyProps(
                    self.PROP_LOC + self.repo_properties[i])
                if is_valid:
                    repo_name_list.append(return_val[0])
                    url_list.append(return_val[1])
                    try:
                        response = urlopen(
                            return_val[1] + SHARE_LOGIN_EXT,
                            timeout=REQUESTS_TIMEOUT)
                        status_code = response.getcode()
                        response.close()
                    except:
                        status_code = 500
                    status_list.append(status_code)
                    i += 1
                else:
                    self.repo_properties.remove(self.repo_properties[i])
            if len(repo_name_list) == 1:
                index = 0
            elif len(repo_name_list) > 1:
                dialog = SelectRepoDialog()
                result, index, repo_name = dialog.getDialog(
                    repo_name_list, status_list, os.environ[DMF_HOME])
                if not result:
                    return
            username, password, is_info_save, result = \
                LoginDialog.getCredentials(
                    '', '',  None, None,
                    save_option=False, parent=self)
            if username and password and result:
                self.ingest_button.setText("Processing...")
                QApplication.processEvents()
                status = []
                if platform.system().startswith(WINDOWS):
                    proc = subprocess.Popen(
                        [ingest_script_loc, self.fname,
                         "-u", username, "-p", password, "-i", str(index)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=win32process.CREATE_NO_WINDOW)
                else:
                    proc = subprocess.Popen(
                        ["python", ingest_script_loc, self.fname,
                         "-u", username, "-p", password, "-i", str(index)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
                while proc.poll() is None:
                    output = proc.stdout.readline()
                    status.append(output.strip())
                output = proc.communicate()[0]
                status.append(output.strip())
                self.ingest_button.setText("Ingest")
                StatusDialog.displayStatus('\n'.join(filter(None, status)))
            else:
                return
        except AttributeError, e:
            logging.getLogger("foqus." + __name__).exception(e)
            StatusDialog.displayStatus("Please select a directory to ingest.")
            self.ingest_button.setText("Ingest")"""
