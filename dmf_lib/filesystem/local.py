'''
   local.py

    * The main script dealing with handling the filesystem that is
    * stored using git. This is the file system associated with DMF lite

    You-Wei Cheah, Lawrence Berkeley National Laboratory, 2015

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

import os
import sys
import json
import time
import shutil
import urllib
import logging
import platform
import mimetypes
import traceback
import collections

from PySide.QtGui import QWidget
from PySide.QtGui import QStandardItemModel
from PySide.QtGui import QStandardItem
from PySide.QtGui import QFileDialog
from PySide.QtGui import QLabel
from PySide.QtGui import QLineEdit
from PySide.QtGui import QComboBox
from PySide.QtGui import QBoxLayout
from PySide.QtGui import QGridLayout
from PySide.QtGui import QVBoxLayout
from PySide.QtGui import QHBoxLayout
from PySide.QtGui import QTreeView
from PySide.QtGui import QPushButton
from PySide.QtGui import QSpacerItem
from PySide.QtGui import QDesktopWidget
from PySide.QtGui import QIcon
from PySide.QtGui import QMenu
from PySide.QtGui import QPixmap
from PySide.QtGui import QAction
from PySide.QtGui import QScrollArea
from PySide.QtGui import QSplitter
from PySide.QtCore import QSize
from PySide.QtCore import Qt
from PySide.QtCore import QEventLoop

from dmf_lib.dialogs.select_repo_dialog import SelectRepoDialog
from dmf_lib.dialogs.save_file_handler_dialog import SaveFileHandlerDialog
from dmf_lib.dialogs.login import LoginDialog
from dmf_lib.dialogs.new_folder_dialog import FolderDialog
from dmf_lib.dialogs.status_dialog import StatusDialog
from dmf_lib.dialogs.save_file_dialog import SaveFileDialog
from dmf_lib.dialogs.save_file_dialog import SaveOverwriteFileDialog
from dmf_lib.dialogs.select_ver_dialog import SelectVersionDialog
from dmf_lib.dialogs.detailed_info_dialog import DetailedInfoDialog
from dmf_lib.git.ops import GitOps
from dmf_lib.common.methods import Common
from dmf_lib.filesystem.tree_ops import TreeOps
from dmf_lib.filesystem.shared_ops import SharedOps
from py4j.java_gateway import JavaGateway
from dmf_lib.graph.graph_viewer import Grapher

# Import global variables
from dmf_lib.git.meta_dict import DISPLAY_NAME
from dmf_lib.git.meta_dict import ORIGINAL_NAME
from dmf_lib.git.meta_dict import DESCRIPTION
from dmf_lib.git.meta_dict import MIMETYPE
from dmf_lib.git.meta_dict import CONFIDENCE
from dmf_lib.git.meta_dict import CREATOR
from dmf_lib.git.meta_dict import EXTERNAL
from dmf_lib.git.meta_dict import MAJOR_VERSION
from dmf_lib.git.meta_dict import MINOR_VERSION
from dmf_lib.git.meta_dict import DEPENDENCIES
from dmf_lib.git.meta_dict import VERSION_REQ

from dmf_lib.common.common import CANCEL
from dmf_lib.common.common import CCSI_EMBEDDED_METADATA
from dmf_lib.common.common import CCSI_SIM_ID_KEY
from dmf_lib.common.common import DATE_MOD_COLUMN
from dmf_lib.common.common import DEFAULT_DMF_MIMETYPE
from dmf_lib.common.common import DEFAULT_NAME_COLUMN_WIDTH
from dmf_lib.common.common import DMF_HOME
from dmf_lib.common.common import DMF_CREATOR
from dmf_lib.common.common import DOCUMENT_DISPLAY_STRING
from dmf_lib.common.common import FIND_SINTER_INDICATOR
from dmf_lib.common.common import FOLDER_DISPLAY_STRING
from dmf_lib.common.common import GATEWAY_ENTRYPOINT_CONNECTION_RETRY
from dmf_lib.common.common import GRAPH
from dmf_lib.common.common import KIND_COLUMN
from dmf_lib.common.common import NA_VER
from dmf_lib.common.common import NUM_COLUMN
from dmf_lib.common.common import NODE_PREFIX
from dmf_lib.common.common import NAME_COLUMN
from dmf_lib.common.common import NODE_ID_COLUMN
from dmf_lib.common.common import OPEN
from dmf_lib.common.common import PRINT_COLON
from dmf_lib.common.common import PROPERTIES_EXT
from dmf_lib.common.common import REQUESTS_TIMEOUT
from dmf_lib.common.common import REPO_PROPERTIES_UNIX_PATH
from dmf_lib.common.common import REPO_PROPERTIES_WIN_PATH
from dmf_lib.common.common import RETRY_SLEEP_DURATION
from dmf_lib.common.common import SAVE
from dmf_lib.common.common import SC_TITLE
from dmf_lib.common.common import SC_TYPE
from dmf_lib.common.common import SC_TYPENAME
from dmf_lib.common.common import SEMI_COLON
from dmf_lib.common.common import SHARE_LOGIN_EXT
from dmf_lib.common.common import SINTER_CONFIG_EXT
from dmf_lib.common.common import UTF8
from dmf_lib.common.common import UNIX_PATH_SEPARATOR
from dmf_lib.common.common import WINDOWS
from dmf_lib.common.common import WIN_PATH_SEPARATOR

from dmf_lib.gui.path import ACTION_IMAGE_PATH
from dmf_lib.gui.path import FILETYPE_IMAGE_PATH
from dmf_lib.gui.path import EDIT
from dmf_lib.gui.path import FILE_UPLOAD
from dmf_lib.gui.path import FOLDER_UPLOAD
from dmf_lib.gui.path import UPLOAD
from dmf_lib.gui.path import DOWNLOAD
from dmf_lib.gui.path import PERMISSIONS
from dmf_lib.gui.path import RELOAD
from dmf_lib.gui.path import CREATE_FOLDER
from dmf_lib.gui.path import FOLDER_OPENED
from dmf_lib.gui.path import FOLDER_CLOSED
from dmf_lib.gui.path import TEXT_FILE

from dmf_lib.filesystem.file_filters import FILE_FILTERS
from dmf_lib.filesystem.file_filters import FILE_FILTER_VALUES

from urllib2 import urlopen

try:
    from foqus_lib.framework.graph.nodeModelTypes import nodeModelTypes
    print "Successfully imported nodeModelTypes..."
except Exception, e:
    print traceback.print_exc()

__author__ = 'You-Wei Cheah <ycheah@lbl.gov>'


class LocalFileSystem(QWidget):
    FOQUS_SESSION_TYPE = "FOQUS_Session"
    IS_OPEN_MODE = False
    IS_BROWSER_MODE = False
    SYNC_COMMENT = "Uploaded from DMF lite"

    def __init__(self, parent=None):
        '''
        Constructor that sets up GUI elements for the
        DMF Lite filesystem
        '''
        super(LocalFileSystem, self).__init__(parent)
        self.common = Common()
        self.verbose = parent.verbose if parent else False
        self.root = parent if parent else None

        if self.root:
            self.user = self.root.user

        LocalFileSystem.IS_OPEN_MODE = True if parent.IS_OPEN_MODE else False
        LocalFileSystem.IS_BROWSER_MODE = True \
            if parent.IS_BROWSER_MODE else False
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, \
                "OPEN_MODE", PRINT_COLON, LocalFileSystem.IS_OPEN_MODE
            print self.__class__.__name__, PRINT_COLON, \
                "BROWSER_MODE", PRINT_COLON, LocalFileSystem.IS_BROWSER_MODE

        # We are on Windows
        if platform.system().startswith(WINDOWS):
            self.PATH_SEPARATOR = WIN_PATH_SEPARATOR
            self.home = os.environ[REPO_PROPERTIES_WIN_PATH] \
                + WIN_PATH_SEPARATOR
        else:
            self.PATH_SEPARATOR = UNIX_PATH_SEPARATOR
            self.home = os.environ[REPO_PROPERTIES_UNIX_PATH] \
                + UNIX_PATH_SEPARATOR

        self.DMF_HOME = os.environ[DMF_HOME]
        try:
            os.environ[DMF_HOME]
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, \
                    os.environ[DMF_HOME]
        except KeyError:
            print "Please set the environment for", DMF_HOME
            return

        self.repo_fname = "dmflite_repo"
        self.dmflite_repo = os.path.join(self.home, self.repo_fname)
        self.git_ops = GitOps(self, self.user)
        if not self.git_ops.isGitInstalled():
            StatusDialog.displayStatus(
                "Git is not installed. "
                "DMF will not function properly.")
            self.closeRootDialog()
        self.git_ops.createRepo(self.dmflite_repo)

        self.folder_opened_icon = QIcon(
            self.DMF_HOME + FILETYPE_IMAGE_PATH + FOLDER_OPENED)
        self.folder_closed_icon = QIcon(
            self.DMF_HOME + FILETYPE_IMAGE_PATH + FOLDER_CLOSED)
        self.document_icon_url = (
            self.DMF_HOME + FILETYPE_IMAGE_PATH + TEXT_FILE)
        self.document_icon = QIcon(self.document_icon_url)

        # ------------------------------------------------------------------- #
        # Initialize model for tree view                                      #
        # ------------------------------------------------------------------- #
        self.default_model = QStandardItemModel(self)
        self.model = self.default_model
        self.model.setColumnCount(NUM_COLUMN)

        # Create header
        self.tree_ops = TreeOps(self)
        self.tree_ops.setModelHeaders(self.model)

        self.tree_view = QTreeView(self)
        self.tree_ops.setupTreeViewWithModel(self.tree_view, self.model)
        self.tree_view.clicked.connect(self.onTreeViewClicked)
        self.tree_view.expanded.connect(self.expanded)
        self.tree_view.collapsed.connect(self.collapsed)
        self.tree_view_selected = self.tree_view.selectionModel()
        self.tree_view_selected.selectionChanged.connect(
            self.handleSelectionChanged)

        self.tree_view.setColumnWidth(0, 300)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.setIconSize(QSize(16, 16))
        self.cancel_button = QPushButton(CANCEL)
        self.cancel_button.clicked.connect(self.cancelClicked)

        # ------------------------------------------------------------------- #
        # File Name text field used to display selected file here             #
        # ------------------------------------------------------------------- #
        self.label_file_name = QLabel(self)
        self.label_file_name.setText("File Name:")
        self.target_file_name = QLineEdit(self)
        self.target_file_name.setReadOnly(True)

        self.filters = FILE_FILTERS
        self.filter_values = FILE_FILTER_VALUES

        self.file_name_filter = QComboBox(self)
        for i in xrange(len(self.filters)):
            self.file_name_filter.addItem(
                self.filters[i], self.filter_values[i])

        self.file_name_layout = QGridLayout()
        self.file_name_layout.addWidget(self.label_file_name, 0, 0)
        self.file_name_layout.addWidget(self.target_file_name, 0, 1)
        self.file_name_layout.addWidget(self.file_name_filter, 0, 2)
        self.file_name_filter.currentIndexChanged['QString'].connect(
            self.handleFilterChange)

        if not LocalFileSystem.IS_OPEN_MODE:
            self.file_name_filter.hide()
            self.label_file_name.hide()
            self.target_file_name.hide()
            # Set to select all for Browser mode
            self.file_name_filter.setCurrentIndex(len(self.filters))

        # ------------------------------------------------------------------- #
        # Main DMF lite file browser buttons here                             #
        # ------------------------------------------------------------------- #
        if not (LocalFileSystem.IS_OPEN_MODE
                or LocalFileSystem.IS_BROWSER_MODE):
            self.save_button = QPushButton(SAVE, self)
            self.new_folder_button = QPushButton("New Folder", self)
        else:
            if LocalFileSystem.IS_OPEN_MODE:
                self.open_button = QPushButton(OPEN, self)
            else:
                self.cancel_button.hide()
                self.open_button = QPushButton(GRAPH, self)
                self.new_folder_button = QPushButton("Create Folder", self)
                self.edit_button = QPushButton("Edit Properties", self)
                self.upload_button = QPushButton("Commit... ", self)
                self.download_button = QPushButton("Retrieve", self)
                self.permissions_button = QPushButton(
                    "Manage Permissions", self)
                # Not ready for release
                self.permissions_button.setEnabled(False)
                self.sync_button = QPushButton(self)
                self.refresh_button = QPushButton(self)
                self.hbox_spacer2 = QSpacerItem(
                    QDesktopWidget().screenGeometry().width(), 0)
            self.fs_ops_hbox_spacer = QSpacerItem(
                QDesktopWidget().screenGeometry().width(), 0)

        # Set button sizes and functionality and connect to functions
        if not (LocalFileSystem.IS_OPEN_MODE or
                LocalFileSystem.IS_BROWSER_MODE):
            self.save_button.setMaximumWidth(100)
            self.save_button.setMinimumWidth(100)
            self.save_button.clicked.connect(self.saveClicked)
            self.new_folder_button.setMaximumWidth(120)
            self.new_folder_button.setMinimumWidth(120)
            self.new_folder_button.clicked.connect(self.newFolderClicked)
        else:
            self.open_button.setMaximumWidth(100)
            self.open_button.setMinimumWidth(100)
            self.open_button.clicked.connect(self.openClicked)
            if LocalFileSystem.IS_BROWSER_MODE:
                self.open_button.setVisible(False)
                self.cancel_button.setVisible(False)

                self.new_folder_button.setMaximumWidth(120)
                self.new_folder_button.setMaximumHeight(25)
                self.new_folder_button.setIcon(
                    QIcon(self.DMF_HOME + ACTION_IMAGE_PATH + CREATE_FOLDER))
                self.new_folder_button.setToolTip("Create Folder")
                self.new_folder_button.setEnabled(True)
                self.new_folder_button.clicked.connect(self.newFolderClicked)
                self.new_folder_button.setStyleSheet(
                    "background-color: white;")

                self.edit_button.setMaximumWidth(120)
                self.edit_button.setMaximumHeight(25)
                self.edit_button.setIcon(
                    QIcon(self.DMF_HOME + ACTION_IMAGE_PATH + EDIT))
                self.edit_button.setToolTip("Edit")
                self.edit_button.setEnabled(True)
                self.edit_button.clicked.connect(self.editClicked)
                self.edit_button.setStyleSheet("background-color: white;")

                upload_menu = QMenu(self)
                upload_file_pic = QPixmap(
                    self.DMF_HOME + ACTION_IMAGE_PATH + FILE_UPLOAD)
                upload_folder_pic = QPixmap(
                    self.DMF_HOME + ACTION_IMAGE_PATH + FOLDER_UPLOAD)
                upload_file_icon = QIcon(upload_file_pic)
                upload_folder_icon = QIcon(upload_folder_pic)
                self.upload_file = QAction(
                    upload_file_icon, "   Commit File", self)
                self.upload_folder = QAction(
                    upload_folder_icon, "   Commit Folder", self)
                upload_menu.addAction(self.upload_file)
                upload_menu.addAction(self.upload_folder)

                self.upload_file.triggered.connect(self.uploadFileClicked)
                self.upload_folder.triggered.connect(self.uploadFolderClicked)

                self.upload_button.setMaximumWidth(120)
                self.upload_button.setMaximumHeight(25)
                self.upload_button.setIcon(
                    QIcon(self.DMF_HOME + ACTION_IMAGE_PATH + UPLOAD))
                self.upload_button.setToolTip("Commit")
                self.upload_button.setEnabled(True)
                self.upload_button.setMenu(upload_menu)
                self.upload_button.setStyleSheet("background-color: white;")

                self.download_button.setMaximumWidth(120)
                self.download_button.setMaximumHeight(25)
                self.download_button.setIcon(
                    QIcon(self.DMF_HOME + ACTION_IMAGE_PATH + DOWNLOAD))
                self.download_button.setToolTip("Retrieve")
                self.download_button.clicked.connect(self.downloadClicked)
                self.download_button.setStyleSheet("background-color: white;")

                self.permissions_button.setMaximumWidth(150)
                self.permissions_button.setMaximumHeight(25)
                self.permissions_button.setIcon(
                    QIcon(self.DMF_HOME + ACTION_IMAGE_PATH + PERMISSIONS))
                self.permissions_button.setToolTip(
                    "Manage Permissions (Upcoming feature)")
                self.permissions_button.setVisible(False)
                # self.permissions_button.clicked.connect(self.permissionsClicked)
                self.permissions_button.setStyleSheet(
                    "background-color: white;")

                self.refresh_button.setMaximumWidth(25)
                self.refresh_button.setMaximumHeight(25)
                self.refresh_button.setToolTip("Refresh")
                self.refresh_button.setIcon(
                    QIcon(self.DMF_HOME + ACTION_IMAGE_PATH + RELOAD))
                self.refresh_button.clicked.connect(self.tree_ops.refreshTree)

                self.sync_button.setMaximumWidth(25)
                self.sync_button.setMaximumHeight(25)
                self.sync_button.setToolTip("Upload to DMF Server")
                self.sync_button.setIcon(
                    QIcon(self.DMF_HOME + ACTION_IMAGE_PATH + UPLOAD))
                self.sync_button.clicked.connect(self.upload_to_alfresco)
                try:
                    if not self.root.has_min_java or \
                       not self.root.has_dependencies:
                        self.sync_button.setToolTip(
                            self.sync_button.toolTip() +
                            " (Disabled due to problems with Java)")
                        self.sync_button.setEnabled(False)
                except:
                    pass

        self.cancel_button.setMaximumWidth(100)
        self.cancel_button.setMinimumWidth(100)

        # Add layout to main widget layout
        if LocalFileSystem.IS_BROWSER_MODE:
            try:
                self.button_bar = QHBoxLayout()
                self.button_bar.addWidget(self.new_folder_button)
                self.button_bar.addWidget(self.edit_button)
                self.button_bar.addWidget(self.upload_button)
                self.button_bar.addWidget(self.download_button)
                self.button_bar.addWidget(self.permissions_button)
                self.button_bar.addItem(self.hbox_spacer2)
                self.button_bar.addWidget(self.sync_button)
                self.button_bar.addWidget(self.refresh_button)
            except Exception, e:
                if self.verbose:
                    print self.__class__.__name__, PRINT_COLON, \
                        "Error", PRINT_COLON, e

        # --- end added buttons
        self.detailed_info_dialog = DetailedInfoDialog(self)
        self.detailed_info_scroll = QScrollArea(self)
        palette = self.detailed_info_scroll.palette()
        palette.setColor(self.detailed_info_scroll.backgroundRole(), Qt.white)
        self.detailed_info_scroll.setAutoFillBackground(True)
        self.detailed_info_scroll.setPalette(palette)
        self.detailed_info_scroll.setWidget(self.detailed_info_dialog)
        self.detailed_info_scroll.setWidgetResizable(True)

        self.fs_splitter = QSplitter()
        self.fs_splitter.splitterMoved.connect(self.splitterMoved)
        if LocalFileSystem.IS_BROWSER_MODE:
            self.fs_splitter.addWidget(self.tree_view)
            self.fs_splitter.addWidget(self.detailed_info_scroll)
            pos = self.fs_splitter.getRange(1)[1] / 3
            self.fs_splitter.moveSplitter(pos, 1)
        else:
            self.fs_splitter.addWidget(self.tree_view)
            self.fs_splitter.addWidget(self.detailed_info_scroll)
            # Uncommenting for now
            # Hide detailed info tab on initialize
            self.fs_splitter.moveSplitter(0, 0)

        self.fs_ops_vbox = QVBoxLayout()
        self.fs_ops_hbox = QHBoxLayout()
        self.fs_ops_hbox.setDirection(QBoxLayout.RightToLeft)
        self.fs_ops_hbox.addWidget(self.cancel_button)

        if LocalFileSystem.IS_OPEN_MODE or LocalFileSystem.IS_BROWSER_MODE:
            if LocalFileSystem.IS_OPEN_MODE:
                self.fs_ops_hbox.addWidget(self.open_button)
                self.fs_ops_hbox.addItem(self.fs_ops_hbox_spacer)
            else:
                self.fs_ops_vbox.addLayout(self.button_bar)
        else:
            self.fs_ops_hbox.addWidget(self.save_button)
            self.fs_ops_hbox.addWidget(
                self.new_folder_button, alignment=Qt.AlignLeft)

        self.fs_ops_vbox.addWidget(self.fs_splitter)
        self.fs_ops_vbox.addLayout(self.file_name_layout)
        self.fs_ops_vbox.addLayout(self.fs_ops_hbox)

        self.layout = QVBoxLayout(self)
        self.layout.addLayout(self.fs_ops_vbox)

        # ------------------------------------------------------------------- #
        # Graph viewer                                                        #
        # ------------------------------------------------------------------- #
        if LocalFileSystem.IS_BROWSER_MODE:
            self.grapher = Grapher(
                self.git_ops,
                None,
                None,
                self.detailed_info_dialog.view,
                self.DMF_HOME,
                is_dmf_lite=True)
        # ------------------------------------------------------------------- #

        # Include mimetype dict
        self.mimetype_dict = dict()
        mimetype_dict_loc = os.path.join(
            self.DMF_HOME, "dmf_lib/mimetype_dict/mimetype.json")
        with open(mimetype_dict_loc, 'r') as f:
            mimetypes = json.loads(f.read())
        mimetype_data = mimetypes["data"]
        self.mimetype_dict = dict()
        for k in mimetype_data.keys():
            self.mimetype_dict.update(
                {mimetype_data[k]["description"]: k})
            self.mimetype_dict = collections.OrderedDict(
                sorted(self.mimetype_dict.items()))

        self.tree_view.sortByColumn(0, Qt.AscendingOrder)

        self.user_root = os.path.join(os.path.join(
            self.home, 'dmflite_repo'), self.user)
        self.sim_folder = os.path.join(self.user_root, "Simulation")
        self.setupTree()

    def onTreeViewClicked(self, index):
        node_path = index.model().itemFromIndex(
            index.sibling(index.row(), NODE_ID_COLUMN)).text()
        if os.path.isfile(node_path):
            self.target_file_name.setText(os.path.basename(node_path))
        else:
            self.target_file_name.setText('')
            if self.last_clicked_index == index.sibling(
                    index.row(), NAME_COLUMN):
                if self.tree_view.isExpanded(self.last_clicked_index):
                    self.tree_view.collapse(index)
                else:
                    self.tree_view.expand(index)
        self.last_clicked_index = index.sibling(index.row(), NAME_COLUMN)
        self.target_path = node_path
        self.target_index = index if os.path.isdir(self.target_path) else None

    def openClicked(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Open button clicked."

        if self.target_index is None:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, \
                    "Opening", self.target_path
            with open(str(self.target_path), "rb") as f:
                self.setSession(bytearray(f.read()), self.target_path)
            self.closeRootDialog()
            return
        else:
            self.tree_view.expand(self.target_index)

    def saveClicked(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Save Button Clicked."
        try:
            if not os.path.isdir(self.target_path):
                # Select parent element in tree view if file is selected
                self.tree_view.setCurrentIndex(
                    self.tree_view.selectedIndexes()[0].parent())
            data = json.loads(self.getByteArrayStream().decode(UTF8))
            try:
                type = data["Type"]
            except:
                type = None
                StatusDialog.displayStatus("JSON Data does not have Type")
                # self.dereference()
                self.closeRootDialog()
                return

            if type in (LocalFileSystem.FOQUS_SESSION_TYPE, "Session"):
                nodes = data["flowsheet"]["nodes"]
                turbineSims = []
                for nkey, node in nodes.iteritems():
                    if node['modelType'] == nodeModelTypes.MODEL_TURBINE:
                        sim = node['modelName']
                        if sim != "" and sim is not None:
                            turbineSims.append(sim)
                if self.verbose:
                    print "Turbine model references:"
                    print turbineSims
                metaData = data.get("CCSIFileMetaData", None)
                if metaData:
                    display_name = metaData.get("DisplayName", '')
                    original_name = metaData.get("OriginalFilename", '')
                    description = metaData.get("Description", '')
                    mimetype = metaData.get("MIMEType", '')
                    confidence = metaData.get("Confidence", '')
                    external = None
                    version_requirements = None
                else:  # missing metadata this should not happen
                    # foqus catch and show a message box with tace
                    # and log the exception
                    raise("Missing metadata")

                # TODO: Check write permissions here
                file_path = os.path.join(
                    self.target_path, display_name + '.foqus')
                version = None
                if os.path.exists(file_path):
                    result, is_major_version, overwrite = \
                        SaveOverwriteFileDialog.getSaveFileProperties(
                            "Upload New File Dialog", self)
                    if result:
                        version = self.git_ops.getNewVersion(
                            file_path, is_major_version)
                    else:
                        return
                isSuccess = False
                status_msg = ''
                isSuccess, err_msg = self.git_ops.createVersionedDocument(
                    self.getByteArrayStream(),
                    file_path,
                    original_name,
                    description,
                    mimetype,
                    external,
                    confidence,
                    version_requirements,
                    self.user,
                    version=version,
                    dependencies=self.getParents())
                if isSuccess:
                    StatusDialog.displayStatus(
                        "Successfully stored 1 file.")
                    self.setSavedMetadata(
                        status_msg.replace(NODE_PREFIX, ""))
                else:
                    output = []
                    output.extend(
                        ("Report:\n\n", "Error encountered:\n\n",
                         "\t%10s : %s\n" %
                         (display_name, err_msg)))
                    StatusDialog.displayStatus(''.join(output))
                self.closeRootDialog()
        except AttributeError, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, e
            StatusDialog.displayStatus(traceback.format_exc())
        except Exception, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, e
            StatusDialog.displayStatus(traceback.format_exc())

    def cancelClicked(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON,
            "Cancel button clicked."
        self.closeRootDialog()

    def newFolderClicked(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, \
                "New folder button clicked."
        self.setEnabled(False)
        if not os.path.isdir(self.target_path):
            # Select parent element in tree view if file is selected
            self.tree_view.setCurrentIndex(
                self.tree_view.selectedIndexes()[0].parent())

        folder_name, description, _, status = \
            FolderDialog.getNewFolderProperties(self)
        if status:
            new_folder_path = os.path.join(self.target_path, str(folder_name))
            if folder_name == '':
                StatusDialog.displayStatus("New folder name unspecified!")
            else:
                try:
                    status = self.git_ops.createFolder(
                        new_folder_path, folder_name, description)
                    if status is not True:
                        raise status
                    StatusDialog.displayStatus("Create new folder successful!")
                except Exception, e:
                    StatusDialog.displayStatus(str(e))
        self.tree_ops.refreshTree()
        self.setEnabled(True)

    def expanded(self, index):
        if self.verbose:
            print "Expanded"
        try:
            main_row_index = index.sibling(index.row(), NAME_COLUMN)
            main_row_item = self.model.itemFromIndex(main_row_index)
            number_of_children = main_row_item.rowCount()
            for n in xrange(number_of_children):
                if main_row_item.child(n, 0).isEnabled():
                    main_row_item.setIcon(self.folder_opened_icon)
                    break
            self.createChildNode(index)
            self.tree_view.resizeColumnToContents(NAME_COLUMN)
            self.tree_view.resizeColumnToContents(DATE_MOD_COLUMN)
            if self.tree_view.columnWidth(
                    NAME_COLUMN) < DEFAULT_NAME_COLUMN_WIDTH:
                self.tree_view.setColumnWidth(
                    NAME_COLUMN, DEFAULT_NAME_COLUMN_WIDTH)
        except Exception, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, e

    def collapsed(self, index):
        if self.verbose:
            print "Collapse"
        self.model.itemFromIndex(index.sibling(
            index.row(), NAME_COLUMN)).setIcon(self.folder_closed_icon)
        self.tree_view.resizeColumnToContents(NAME_COLUMN)
        if self.tree_view.columnWidth(
                NAME_COLUMN) < DEFAULT_NAME_COLUMN_WIDTH:
            self.tree_view.setColumnWidth(
                NAME_COLUMN, DEFAULT_NAME_COLUMN_WIDTH)

    def handleSelectionChanged(self, selected, deselected):
        if self.verbose:
            print "Selection Changed"

        indexes = selected.indexes()
        if len(indexes) > 0:
            index = indexes[0]
            index = selected.indexes()[0]
            self.last_clicked_index = None
            node_path = index.model().itemFromIndex(
                index.sibling(index.row(), NODE_ID_COLUMN)).text()
            kind = index.model().itemFromIndex(
                index.sibling(index.row(), KIND_COLUMN)).text()

            if self.verbose and index:
                print self.__class__.__name__, PRINT_COLON, (
                    "Node %s selected." % node_path)

            if kind == DOCUMENT_DISPLAY_STRING:
                self.target_index = None
                preview = open(
                    os.path.normpath(os.path.join(
                        self.DMF_HOME, "dmf_lib/gui/doc-64.png")), 'rb')
            elif kind == FOLDER_DISPLAY_STRING:
                preview = open(
                    os.path.normpath(os.path.join(
                        self.DMF_HOME, "dmf_lib/gui/folder-64.png")), 'rb')
                self.target_index = index
            else:
                if self.verbose:
                    print "Data object is not a file/folder " + \
                        "(This should never print)."
            self.target_path = node_path
            preview_content = preview.read()
            preview.close()
            if kind == DOCUMENT_DISPLAY_STRING:
                ver_list = self.git_ops.getVersionList(node_path)
                self.target_file_name.setText(os.path.basename(node_path))
            else:
                ver_list = None
                self.target_file_name.setText('')
            meta = self.git_ops.getLatestMeta(node_path)
            self.detailed_info_dialog.setData(
                display_name=meta.get(DISPLAY_NAME) if meta else None,
                original_name=meta.get(ORIGINAL_NAME) if meta else None,
                description=meta.get(DESCRIPTION) if meta else None,
                mimetype=meta.get(MIMETYPE) if meta else None,
                external='' if meta else None,
                version_req=meta.get(VERSION_REQ) if meta else None,
                confidence=meta.get(CONFIDENCE) if meta else None,
                creator=meta.get(CREATOR) if meta else None,
                creation_date=self.git_ops.getCreationDate(node_path),
                last_modified_date=self.git_ops.getLastModifiedDate(node_path),
                ver_list=ver_list,
                preview=preview_content,
                update_ver_list=True)
            if kind == DOCUMENT_DISPLAY_STRING:
                try:
                    if LocalFileSystem.IS_BROWSER_MODE:
                        node_obj = meta
                        node_obj["path"] = node_path
                        self.grapher.displayGraph(node_obj)
                except Exception, e:
                    if self.verbose:
                        print self.__class__.__name__, PRINT_COLON, e
            else:
                if LocalFileSystem.IS_BROWSER_MODE:
                    self.detailed_info_dialog.view.hide()

    def setSourceFileName(self, file_name):
        self.source_name = file_name

    def getSourceFileName(self):
        return self.source_name

    def setSession(self, session_byte_array_stream, session_path):
        self.session_byte_array_stream = session_byte_array_stream
        self.session_path = session_path

    def setByteArrayStream(self, byte_array_stream):
        self.byte_array_stream = byte_array_stream

    def splitterMoved(self, pos, index):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Splitter moved."
        if (self.detailed_info_dialog and
                self.detailed_info_dialog.view and
                self.detailed_info_dialog.view.view):
            self.detailed_info_dialog.view.view.reload()

    def editClicked(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Edit button clicked."
        self.setEnabled(False)
        # index = self.tree_view.currentIndex()

        if os.path.isdir(self.target_path):
            meta = self.git_ops.getLatestMeta(self.target_path)

            if meta.get(CREATOR) == DMF_CREATOR:
                StatusDialog.displayStatus(
                    "Cannot edit DMF created data objects.")
                self.setEnabled(True)
                return
            folder_name, description, fixed_form, status = \
                FolderDialog.setFolderProperties(
                    meta.get(DISPLAY_NAME),
                    meta.get(DESCRIPTION),
                    None,
                    self)
            if not status:  # Save canceled
                self.setEnabled(True)
                return
            elif (meta.get(DISPLAY_NAME) == folder_name and
                  meta.get(DESCRIPTION) == description):
                StatusDialog.displayStatus(
                    "No new properties to be added.")
                self.setEnabled(True)
                return
            else:
                self.git_ops.editFolderMeta(
                    self.target_path, folder_name, description, fixed_form)
                new_name = os.path.join(os.path.dirname(
                    self.target_path), folder_name)
        else:
            meta = self.git_ops.getLatestMeta(self.target_path)
            display_name, original_name, description, external, \
                mimetype, version_requirements, confidence, parent_ids, status \
                = SaveFileDialog.getSaveFileProperties(
                    '',
                    os.path.basename(self.target_path),
                    original_name=meta.get(ORIGINAL_NAME),
                    description=meta.get(DESCRIPTION),
                    mimetype=meta.get(MIMETYPE),
                    external=meta.get(EXTERNAL),
                    confidence=meta.get(CONFIDENCE),
                    version_requirements=meta.get(VERSION_REQ),
                    parent_ids=None,
                    id='',
                    parent=self)

            if not status:  # Save canceled
                self.setEnabled(True)
                return
            elif (display_name == meta.get(DISPLAY_NAME) and
                  original_name == meta.get(ORIGINAL_NAME) and
                  description == meta.get(DESCRIPTION) and
                  mimetype == meta.get(MIMETYPE) and
                  external == meta.get(EXTERNAL) and
                  confidence == meta.get(CONFIDENCE) and
                  parent_ids == meta.get(DEPENDENCIES) and
                  version_requirements == meta.get(VERSION_REQ)):
                StatusDialog.displayStatus(
                    "No new properties to be added.")
                self.setEnabled(True)
                return
            else:
                self.git_ops.editDocumentMetadata(
                    self.target_path, display_name, original_name,
                    description, mimetype, external, version_requirements,
                    confidence, parent_ids,
                    meta.get(MAJOR_VERSION), meta.get(MINOR_VERSION))
                new_name = os.path.join(os.path.dirname(
                    self.target_path), display_name)
        current_index = self.tree_view.selectedIndexes()[0]
        current_index.model().itemFromIndex(current_index.sibling(
            current_index.row(), NODE_ID_COLUMN)).setText(new_name)
        StatusDialog.displayStatus("Edit successful!")
        self.tree_ops.refreshTree()
        self.setEnabled(True)

    def uploadFileClicked(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Upload file clicked."
        nsuccesses = 0
        nerrors = 0
        err_statuses = {}
        try:
            self.target_path
            if not os.path.isdir(self.target_path):
                # Select parent element of tree view
                self.tree_view.setCurrentIndex(
                    self.tree_view.selectedIndexes()[0].parent())
        except Exception, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, e
            StatusDialog.displayStatus(str(e))
        self.setEnabled(False)
        uploadFileDialog = QFileDialog(self)
        fnames, filter = uploadFileDialog.getOpenFileNames(
            self, "Commit File(s)")

        for src_path in fnames:
            try:
                original_name = os.path.basename(src_path)
                f = open(str(src_path), 'rb')
                try:
                    if self.verbose:
                        t_start_millis = int(round(time.time() * 1000))
                    while True:
                        display_name, original_name, description, external, \
                            mimetype, version_requirements, confidence, parent_ids, status \
                            = SaveFileDialog.getSaveFileProperties(
                                '',
                                original_name,
                                original_name,
                                description='',
                                mimetype=mimetypes.guess_type(
                                    urllib.pathname2url(src_path))[0],
                                external='',
                                confidence='',
                                version_requirements='',
                                parent_ids=None,
                                id='',
                                parent=self)
                        if not status:  # Save canceled
                            self.setEnabled(True)
                            return
                        elif self.hasSaveFileDialogRequired(
                                display_name, mimetype):
                            break
                    self.target_file = os.path.join(
                        self.target_path, display_name)
                    version = None
                    src_bytestream = f.read()
                    isSuccess = True
                    if os.path.exists(self.target_file):
                        if self.git_ops.isFileContentsIdentical(
                                src_bytestream, self.target_file):
                            isSuccess = False
                            err_msg = "Previous file has identical contents."
                        else:
                            result, is_major_ver, _ = \
                                SaveOverwriteFileDialog.getSaveFileProperties(
                                    "Commit New File Dialog", self)
                            if result:
                                version = self.git_ops.getNewVersion(
                                    self.target_file, is_major_ver)
                            else:
                                self.setEnabled(True)
                                return
                    if isSuccess:
                        isSuccess, err_msg = \
                            self.git_ops.createVersionedDocument(
                                src_bytestream,
                                self.target_file,
                                original_name,
                                description,
                                mimetype,
                                external,
                                confidence,
                                version_requirements,
                                self.user,
                                version)
                    if isSuccess:
                        nsuccesses += 1
                    else:
                        nerrors += 1
                        err_statuses[original_name] = err_msg
                    if self.verbose:
                        t_end_millis = int(round(time.time() * 1000))
                        print "t-uploadfile: ", (t_end_millis - t_start_millis)
                except Exception, e:
                    nerrors += 1
                    err_statuses[original_name] = e
                    if self.verbose:
                        print e.__class_.__name__, PRINT_COLON, \
                            "Error", PRINT_COLON, e
                finally:
                    if self.verbose:
                        print "Closed file"
                    f.close()
            except Exception, e:
                if self.verbose:
                    print e.__class__.__name__, PRINT_COLON, e
                StatusDialog.displayStatus(str(e))

        if nerrors > 0:
            output = []
            output.extend(
                ("Report:\n\nSuccessfully stored ",
                 "%d file(s).\n%d errors encountered:\n\n" %
                 (nsuccesses, nerrors)))
            for id, e in err_statuses.items():
                if self.verbose:
                    print id, e
                output.append("\t%10s : %s\n" % (id, e))
            StatusDialog.displayStatus(''.join(output))
        elif nsuccesses > 0:
            StatusDialog.displayStatus(
                "Successfully stored %d file(s)." % nsuccesses)
        self.tree_ops.refreshTree()
        self.setEnabled(True)

    def uploadFolderClicked(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, \
                "Upload folder clicked."
        self.setEnabled(False)
        if not os.path.isdir(self.target_path):
            # Select parent element in tree view if file is selected
            self.tree_view.setCurrentIndex(
                self.tree_view.selectedIndexes()[0].parent())

        uploadFolderDialog = QFileDialog(self)
        uploadFolderDialog.setFileMode(QFileDialog.Directory)
        fname = QFileDialog.getExistingDirectory(self, "Commit Directory")
        if fname == '':
            self.setEnabled(True)
            return
        try:
            # Iterate through contents
            status = self.getAllFolderObjects(
                self.target_path,
                fname,
                description='',
                initial=True)
            if status is False:
                StatusDialog.displayStatus(
                    "Folder commit incomplete or unsuccessful.")
            else:
                StatusDialog.displayStatus("Folder commit completed!")
        except Exception, e:
            print e
        self.tree_ops.refreshTree()
        self.setEnabled(True)

    def getAllFolderObjects(
            self,
            parent_folder,
            path,
            description,
            initial=False,
            fixed_form=False):
        folder_name = os.path.basename(path)
        if initial:
            while True:
                folder_name, description, fixed_form, status \
                    = FolderDialog.setFolderProperties(
                        folder_name, description, fixed_form)
                if not status:  # Save canceled
                    return None
                elif self.hasSaveFolderDialogRequired(folder_name):
                    dialog = StatusDialog(
                        "Begin bulk uploading of folder " +
                        folder_name + " ...",
                        use_padding=True,
                        parent=self)
                    dialog.show()
                    break
        else:
            try:
                dialog.close()
                dialog.deleteLater()
            except:
                pass
            dialog = StatusDialog(
                "Uploading folder " + folder_name + " ...",
                use_padding=True,
                parent=self)
            dialog.show()
        try:
            target_folder_path = os.path.join(parent_folder, folder_name)
            create_folder_status = self.git_ops.createFolder(
                target_folder_path, folder_name, description)
            if create_folder_status:
                parent_folder = target_folder_path
                try:
                    dialog.close()
                    dialog.deleteLater()
                except:
                    pass
            else:
                dialog.close()
                dialog.deleteLater()
                StatusDialog.displayStatus(
                    create_folder_status.getStatusMessage())
                return False

            if initial:
                description = (
                    "Uploaded through bulk upload of " +
                    folder_name +
                    " folder")

            for f in os.listdir(path):
                f_path = os.path.join(path, f)
                if os.path.isdir(f_path):
                    self.getAllFolderObjects(
                        parent_folder, f_path, description)
                else:
                    file_bytestream = open(str(f_path), 'rb')
                    try:
                        original_name = os.path.basename(f_path)
                        target_path = os.path.join(
                            parent_folder, original_name)
                        try:
                            dialog.close()
                            dialog.deleteLater()
                        except:
                            pass
                        dialog = StatusDialog(
                            "Uploading file " + original_name + " ...",
                            use_padding=True,
                            parent=self)
                        dialog.show()
                        self.git_ops.createVersionedDocument(
                            file_bytestream.read(),
                            target_path=target_path,
                            original_name=original_name,
                            description=description,
                            mimetype=mimetypes.guess_type(
                                urllib.pathname2url(f_path))[0],
                            external='',
                            confidence='experimental',
                            version_requirements='',
                            creator=self.user,
                            version=None)
                        # Save file
                        dialog.close()
                        dialog.deleteLater()

                    except Exception, e:
                        if self.verbose:
                            print self.__class__.__name__, PRINT_COLON, e
                        StatusDialog.displayStatus(str(e))
                    finally:
                        file_bytestream.close()
        except Exception, e:
            try:
                dialog.close()
                dialog.deleteLater()
            except:
                pass
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, e
            raise

    def hasSaveFileDialogRequired(self, display_name, mimetype):
        # Check that all required fields are populated
        if display_name == '':
            StatusDialog.displayStatus("Display Name is not set!")
            return False
        elif mimetype == '':
            StatusDialog.displayStatus("Mimetype is not set!")
            return False
        else:
            return True

    def hasSaveFolderDialogRequired(self, folder_name):
        # Check that all required fields are populated
        if folder_name == '':
            StatusDialog.displayStatus("Folder Name is not set!")
            return False
        else:
            return True

    def changeDetailedInfoVersion(self, text):
        if self.verbose:
            print "Change detailed info version."
        major_version, minor_version = self.common.splitVersion(text)
        latest_major_version, latest_minor_version = \
            self.git_ops.getLatestVersion(self.target_path)
        if latest_major_version == major_version and \
           latest_minor_version == minor_version:
            creation_date = self.git_ops.getCreationDate(self.target_path)
            last_modified_date = self.git_ops.getLastModifiedDate(
                self.target_path)
        else:
            creation_date = self.git_ops.getCreationDateByVersion(
                self.target_path, major_version, minor_version)
            last_modified_date = creation_date
        preview = open(
            os.path.normpath(
                os.path.join(self.DMF_HOME, "dmf_lib/gui/doc-64.png")), 'rb')
        preview_content = preview.read()
        preview.close()
        meta = self.git_ops.getMetaByPath(
            self.target_path, major_version, minor_version)
        self.detailed_info_dialog.setData(
            display_name=meta.get(DISPLAY_NAME) if meta else None,
            original_name=meta.get(ORIGINAL_NAME) if meta else None,
            description=meta.get(DESCRIPTION) if meta else None,
            mimetype=meta.get(MIMETYPE) if meta else None,
            external=meta.get(EXTERNAL) if meta else None,
            version_req=meta.get(VERSION_REQ) if meta else None,
            confidence=meta.get(CONFIDENCE) if meta else None,
            creator=meta.get(CREATOR) if meta else None,
            creation_date=creation_date,
            last_modified_date=last_modified_date,
            ver_list=None,
            preview=preview_content,
            update_ver_list=False)
        index = self.tree_view.selectedIndexes()[0]
        kind = index.model().itemFromIndex(
            index.sibling(index.row(), KIND_COLUMN)).text()
        if kind == DOCUMENT_DISPLAY_STRING:
            try:
                if LocalFileSystem.IS_BROWSER_MODE:
                    node_obj = meta
                    node_obj["path"] = self.target_path
                    self.grapher.displayGraph(node_obj)
            except Exception, e:
                if self.verbose:
                    print self.__class__.__name__, PRINT_COLON, e
        else:
            if LocalFileSystem.IS_BROWSER_MODE:
                self.detailed_info_dialog.view.hide()

    def setupTree(self):
        if LocalFileSystem.IS_BROWSER_MODE:
            self.root.updateSplash("Setting up user filesystem structure...")
        if self.verbose:
            t_start_millis = int(round(time.time() * 1000))
        self.last_clicked_index = None
        # Only display user space and shared space contents
        self.addDisplayNodeProperties(self.user_root, self.model)
        self.tree_ops.setupTreeViewWithModel(self.tree_view, self.model)

        for i in xrange(self.model.rowCount()):
            cur_index = self.model.item(i, 0).index()
            self.addChildNode(cur_index)

        self.tree_view.sortByColumn(0, Qt.AscendingOrder)
        self.tree_view.setCurrentIndex(
            self.model.index(0, 0))  # Select first element of tree view
        self.tree_ops.importTree(self.tree_view)
        if self.verbose:
            t_end_millis = int(round(time.time() * 1000))
            print "t-setup-tree: ", (t_end_millis - t_start_millis)

    def addDisplayNodeProperties(self, path, model, index=None):
        id = path
        name = os.path.basename(path)
        size = "--"
        type = FOLDER_DISPLAY_STRING \
            if os.path.isdir(path) else DOCUMENT_DISPLAY_STRING

        if type == DOCUMENT_DISPLAY_STRING:
            size = self.common.convertBytesToReadable(
                os.path.getsize(path), True)

        name = QStandardItem(name)

        if type == DOCUMENT_DISPLAY_STRING:
            name.setIcon(self.document_icon)
        else:
            name.setIcon(self.folder_closed_icon)

        size = QStandardItem(size)
        size.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        type = QStandardItem(type)
        date = QStandardItem(time.ctime(
            os.path.getmtime(path)))
        id = QStandardItem(path)
        new_row = [name, size, type, date, id]
        filter = self.filter_values[self.file_name_filter.currentIndex()]

        for r in new_row:
            r.setEditable(False)
            if str(type.text()) == \
               DOCUMENT_DISPLAY_STRING \
               and filter is not None \
               and not str(name.text()).endswith(filter):
                for r in new_row:
                    r.setEnabled(False)
                    r.setSelectable(False)

        if index is not None:
            stack = []
            parent = index
            item = ''

            while not parent.row() < 0:
                stack.append(parent.row())
                parent = parent.parent()
            if stack:
                s = stack.pop()
                item = model.item(s, 0)
                while len(stack) > 0:
                    s = stack.pop()
                    item = item.child(s, 0)
            if index.parent().row() >= 0:
                item.appendRow(new_row)
                filter_row = item.rowCount() - 1
                filter_index = item.index()
            else:
                model.item(index.row(), 0).appendRow(new_row)
                parent = model.item(index.row(), 0)
                filter_row = parent.rowCount() - 1
                filter_index = parent.index()
        else:
            model.appendRow(new_row)
            parent = model.item(model.rowCount() - 1).parent()
            filter_row = model.rowCount() - 1
            if parent is None:
                filter_index = model.invisibleRootItem().index()
            else:
                filter_index = parent.index()

        if self.tree_ops.isNodeNeedsFilter(
                str(type.text()), filter, str(name.text())):
            self.tree_view.setRowHidden(
                filter_row, filter_index, True)

    def createChildNode(self, index):
        if index.column() == 0:
            if index.model().itemFromIndex(index).rowCount() <= 0:
                self.addChildNode(index)
                for i in xrange(index.model().itemFromIndex(index).rowCount()):
                    self.addChildNode(index.child(i, 0))
            else:
                for i in xrange(index.model().itemFromIndex(index).rowCount()):
                    if index.model().itemFromIndex(
                            index.child(i, 0)).rowCount() <= 0:
                        self.addChildNode(index.child(i, 0))
        self.tree_view.sortByColumn(0, Qt.AscendingOrder)

    def addChildNode(self, index):
        node_path = index.model().itemFromIndex(
            index.sibling(index.row(), NODE_ID_COLUMN)).text()
        if node_path is not None:
            try:
                if os.path.isdir(node_path):
                    children = os.listdir(node_path)
                    while children:
                        current_child = children.pop()
                        if current_child.startswith('.'):
                            continue
                        else:
                            current_child_path = os.path.join(
                                node_path, current_child)
                            self.addDisplayNodeProperties(
                                current_child_path, index.model(), index)

            except Exception, e:
                if self.verbose:
                    print e.__class__.__name__, PRINT_COLON, e

    def downloadClicked(self):
        if self.verbose:
            print self.__class__.__name__, \
                PRINT_COLON, "Download button clicked"

        index = self.tree_view.currentIndex()
        name = self.model.itemFromIndex(
            index.sibling(index.row(), NAME_COLUMN)).text()
        node_path = self.model.itemFromIndex(
            index.sibling(index.row(), NODE_ID_COLUMN)).text()
        kind = self.model.itemFromIndex(
            index.sibling(index.row(), KIND_COLUMN)).text()

        if kind == DOCUMENT_DISPLAY_STRING:
            ver_list = self.git_ops.getVersionList(node_path)
            selected_ver, result = SelectVersionDialog.getVersion(
                ver_list, self)
            if result:
                saveFileDialog = QFileDialog(self)
                fname, filter = saveFileDialog.getSaveFileName(
                    self, "Save file", name)
                if fname != "":
                    try:
                        if os.path.isdir(fname):
                            StatusDialog.displayStatus(
                                "Existing folder with name exists!")
                        else:
                            os.remove(fname)
                    except OSError, e:
                        if self.verbose:
                            print "Non-fatal:", e.__class__.__name__, \
                                PRINT_COLON, e
                    # Handle documents
                    dialog = StatusDialog(
                        "Retrieving " + os.path.basename(fname) + " ...",
                        use_padding=True,
                        parent=self)
                    dialog.show()
                    status, status_msg = self.git_ops.downloadFile(
                        node_path, selected_ver, fname)
                    dialog.close()
                    dialog.deleteLater()
                    if status_msg:
                        StatusDialog.displayStatus("Error: " + str(status_msg))
                    else:
                        status_msg = (
                            "Downloaded " + os.path.basename(fname) + " !")
                        StatusDialog.displayStatus(status_msg)
        else:
            # This is for handling folders
            saveFolderDialog = QFileDialog(self)
            saveFolderDialog.setFileMode(QFileDialog.Directory)
            folder_path, filter = QFileDialog.getSaveFileName(
                self, "Save Directory", name)
            if folder_path is None or folder_path == '':
                return
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
            dialog = StatusDialog(
                "Retrieving " + os.path.basename(folder_path) + " ...",
                use_padding=True,
                parent=self)
            dialog.show()
            status, status_msg = self.git_ops.downloadFolder(
                node_path, folder_path)
            dialog.close()
            dialog.deleteLater()
            if status_msg:
                StatusDialog.displayStatus("Error: " + str(status_msg))
            else:
                status_msg = (
                    "Downloaded folder " +
                    os.path.basename(folder_path) +
                    " !")
                StatusDialog.displayStatus(status_msg)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Enter or key == Qt.Key_Return:
            if self.verbose:
                print "Enter detected in LocalFileSystem"
            if LocalFileSystem.IS_OPEN_MODE:
                self.open_button.click()
            else:
                self.tree_view.expand(self.tree_view.currentIndex())

        elif key == Qt.Key_Escape:
            self.closeRootDialog()

    def closeEvent(self, event):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Close event invoked."
        self.tree_ops.exportTree()
        if LocalFileSystem.IS_BROWSER_MODE:
            self.grapher.cleanup()
        self.closeRootDialog()

    def closeRootDialog(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Close root dialog."
        if self.IS_BROWSER_MODE:
            try:
                self.detailed_info_dialog.view.close()
                self.detailed_info_dialog.view.deleteLater()
            except:
                pass
        else:
            self.detailed_info_dialog.close()
        try:
            self.dereference()
        except:
            pass
        self.root.close()

    def dereference(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Dereferencing..."

        self.fs_ops_hbox.removeWidget(self.cancel_button)
        if self.IS_OPEN_MODE or self.IS_BROWSER_MODE:
            self.fs_ops_hbox.removeWidget(self.open_button)
            self.fs_ops_hbox.removeItem(self.fs_ops_hbox_spacer)
            if self.verbose:
                self.fs_ops_hbox.removeWidget(self.test_button)
        else:
            self.fs_ops_hbox.removeWidget(self.save_button)
            self.fs_ops_hbox.removeWidget(self.new_folder_button)

        self.file_name_layout.removeWidget(self.target_file_name)
        self.file_name_layout.removeWidget(self.label_file_name)

        self.model.clear()
        # ------------------------------------------------------------------- #
        # Delete QT elements                                                  #
        # ------------------------------------------------------------------- #
        try:
            if self.IS_OPEN_MODE or self.IS_BROWSER_MODE:
                self.open_button.deleteLater()
                if self.IS_BROWSER_MODE:
                    self.new_folder_button.deleteLater()
                    self.edit_button.deleteLater()
                    self.upload_button.deleteLater()
                    self.download_button.deleteLater()
                    self.permissions_button.deleteLater()
                    self.refresh_button.deleteLater()
                    self.detailed_info_dialog.view.view.deleteLater()
                    self.detailed_info_dialog.view.deleteLater()
                    self.detailed_info_dialog.g_pop.deleteLater()
                    if self.verbose:
                        self.test_button.deleteLater()
            else:
                self.save_button.deleteLater()
                self.new_folder_button.deleteLater()

            self.cancel_button.deleteLater()
            self.target_file_name.deleteLater()
            self.label_file_name.deleteLater()
            self.file_name_layout.deleteLater()
            self.file_name_filter.deleteLater()

            self.detailed_info_dialog.deleteLater()
            self.detailed_info_scroll.deleteLater()

            self.tree_view.deleteLater()
            self.model.deleteLater()
            self.button_bar.deleteLater()
            self.fs_ops_vbox.deleteLater()
            self.fs_ops_hbox.deleteLater()
            self.fs_splitter.deleteLater()
            self.detailed_info_scroll.deleteLater()
            self.layout.deleteLater()
        except:
            raise
        # ------------------------------------------------------------------- #

        # ------------------------------------------------------------------- #
        # Nullify deleted QT elements and other unused variables              #
        # ------------------------------------------------------------------- #
        if self.IS_OPEN_MODE or self.IS_BROWSER_MODE:
            self.open_button = None
            self.fs_ops_hbox_spacer = None
            if self.IS_BROWSER_MODE:
                self.refresh_button = None
                self.logout_button = None
                self.download_button = None
                self.upload_button = None
                self.edit_button = None
                self.new_folder_button = None
                self.permissions_button = None
                self.detailed_info_dialog.view.view = None
                self.detailed_info_dialog.view = None
                self.detailed_info_dialog.g_pop = None
                if self.verbose:
                    self.test_button = None
        else:
            self.save_button = None
            self.new_folder_button = None

        self.cancel_button = None
        self.target_file_name = None
        self.label_file_name = None
        self.file_name_layout = None
        self.file_name_filter = None

        self.button_bar = None
        self.fs_ops_hbox = None
        self.fs_ops_vbox = None
        self.fs_splitter = None
        self.detailed_info_scroll = None
        self.layout = None
        self.tree_view = None
        self.model = None

        # ------------------------------------------------------------------- #

    # Takes in a list.
    # Returns a list of True, False, or None (error case)
    def doesFileExist(self, dmf_id):
        if self.verbose:
            print "Does file exist..."
        dmf_id, _ = self.common.splitDMFID(dmf_id)
        return self.git_ops.doesDMFIDExist(dmf_id)

    # Returns DMF ID for a simulation name
    def getSimIDByName(self, sim_name):
        sim_path = os.path.join(self.sim_folder, sim_name)
        if os.path.exists(sim_path):
            return self.git_ops.getDMFID(sim_path)
        else:
            return None

    def uploadSimulationFiles(
            self,
            sinter_config_bytestream,
            sinter_config_name,
            check_in_comment,
            confidence,
            sim_bytestream=None,
            sim_id=None,
            sim_name=None,
            resource_bytestream_list=None,
            resource_name_list=None,
            version_reqs=None,
            description=None,
            sim_title=None,
            disable_save_dialog=False):
        logging.getLogger("foqus." + __name__).debug(
            "Upload simulation...")
        # Initial check
        if None in (sinter_config_name,
                    sinter_config_bytestream,
                    resource_name_list):
            if sinter_config_name is None:
                StatusDialog.displayStatus(
                    "Sinter configuration name is undefined.")
            if resource_name_list is None:
                StatusDialog.displayStatus("Resource name list is undefined.")
            if sinter_config_bytestream is None:
                StatusDialog.displayStatus(
                    "Sinter configuration bytestream is undefined.")
            return (None, ) * 3

        mimetype = DEFAULT_DMF_MIMETYPE
        success_status = []
        failure_status = []

        # Simulation exists
        sim_title = '_'.join(sim_title.split(' '))
        sim_path = os.path.join(self.sim_folder, sim_title)
        if sim_id:
            if not os.path.exists(sim_path):
                create_folder_status = self.git_ops.createFolder(
                    sim_path, sim_title, description)
                if not create_folder_status:
                    err_msg = ("Unable to create subdirectory "
                               "at path: {p}.".format(
                                   p=self.sim_folder))
                    StatusDialog.displayStatus(err_msg)
                    if self.verbose:
                        print err_msg
            tmp_s_stats, tmp_f_stats, r_id_list, r_name_list = \
                self.updateResources(
                    resource_bytestream_list, resource_name_list, mimetype,
                    None, confidence, version_reqs, sim_path, check_in_comment)
            SharedOps().aggregateStatuses(
                success_status, failure_status, tmp_s_stats, tmp_f_stats)
            tmp_s_stats, tmp_f_stats, sim_id = self.updateSimulation(
                sim_bytestream, sim_name, mimetype, confidence, version_reqs,
                r_id_list, sim_path, check_in_comment, sim_id)
            SharedOps().aggregateStatuses(
                success_status, failure_status, tmp_s_stats, tmp_f_stats)
        else:
            if sinter_config_bytestream is None:
                err_msg = ("Initial upload of simulation must "
                           "include sinter configuration file.")
                if self.verbose:
                    print err_msg
                StatusDialog.displayStatus(str(err_msg))
                return (None, ) * 3

            # Applies for all simulation files
            save_file_dialog_title = "Save Simulation Files Metadata Dialog"
            while True:
                if disable_save_dialog:
                    display_name = sim_name
                    mimetype = DEFAULT_DMF_MIMETYPE
                    confidence = 'experimental'
                    external = None
                    break
                display_name, original_name, description, external, \
                    mimetype, version_reqs, confidence, _, status \
                    = SaveFileDialog.getSaveFileProperties(
                        save_file_dialog_title, (sim_title, True), sim_name,
                        description, mimetype, None, confidence,
                        version_reqs, parent=self)
                if not status:  # Save canceled
                    return (None, ) * 3
                elif self.hasSaveFileDialogRequired(display_name, mimetype):
                    break

            if not os.path.exists(sim_path):
                create_folder_status = self.git_ops.createFolder(
                    sim_path, sim_title, description)
                if not create_folder_status:
                    err_msg = ("Unable to create subdirectory "
                               "at path: {p}.".format(
                                   p=self.sim_folder))
                    StatusDialog.displayStatus(err_msg)
                    if self.verbose:
                        print err_msg

            tmp_s_stats, tmp_f_stats, r_id_list, r_name_list = \
                self.createResources(
                    resource_bytestream_list, resource_name_list, description,
                    mimetype, external, confidence,
                    version_reqs, sim_path)
            SharedOps().aggregateStatuses(
                success_status, failure_status, tmp_s_stats, tmp_f_stats)
            tmp_s_stats, tmp_f_stats, sim_id = self.createSimulation(
                sim_bytestream, sim_name, description, mimetype, external,
                confidence, version_reqs, r_id_list, sim_path)
            SharedOps().aggregateStatuses(
                success_status, failure_status, tmp_s_stats, tmp_f_stats)

        scf_bytestream = SharedOps().editSinterConfigFileMetadata(
            sinter_config_bytestream, sim_id, display_name,
            r_id_list, r_name_list)
        scf_path = os.path.join(sim_path, sinter_config_name)
        if os.path.exists(scf_path):
            tmp_s_stats, tmp_f_stats, scf_id = self.updateSinterConf(
                scf_bytestream, sinter_config_name, mimetype,
                confidence, version_reqs, [sim_id], sim_path)
        else:
            tmp_s_stats, tmp_f_stats, scf_id = self.createSinterConf(
                scf_bytestream, sinter_config_name, description, mimetype,
                None, confidence, version_reqs, [sim_id], sim_path)
        SharedOps().aggregateStatuses(
            success_status, failure_status, tmp_s_stats, tmp_f_stats)
        aggregate_status = []
        if success_status:
            aggregate_status.append("Successfully stored:\n")
            for s in success_status:
                aggregate_status.extend(s)
            StatusDialog.displayStatus(''.join(aggregate_status))
        if failure_status:
            aggregate_status.append("Error encoutered:\n")
            for s in failure_status:
                aggregate_status.extend(s)
            StatusDialog.displayStatus(''.join(aggregate_status))
        if not success_status and not failure_status:
            StatusDialog.displayStatus("No changes occured or were updated.")
        return sim_id, scf_id, scf_bytestream

    def updateResources(self, resource_bytestream_list, resource_name_list,
                        mimetype, external, confidence, version_reqs,
                        target_folder_path, check_in_comment=None):
        success_status = []
        failure_status = []
        r_id_list = []
        r_name_list = []

        logging.getLogger("foqus." + __name__).debug(
            "Updating resources...")
        for r, r_name in zip(resource_bytestream_list, resource_name_list):
            r_path = os.path.join(target_folder_path, r_name)
            self.createSubDir(r_name, target_folder_path)
            if self.git_ops.isFileContentsIdentical(
                    r, r_path):
                # Nothing to do but append to dependencies
                r_id = self.git_ops.getDMFID(r_path)
                r_id_list.append(r_id)
                r_name_list.append(r_name)
            else:
                result, is_major_ver, _ = \
                    SaveOverwriteFileDialog.getSaveFileProperties(
                        "Upload New Resource Dialog", self)
                if not result:
                    r_id = self.git_ops.getDMFID(r_path)
                    r_id_list.append(r_id)
                    r_name_list.append(r_name)
                    continue
                isSuccess, err_msg = self.updateFiles(
                    r, r_path, is_major_ver, version_reqs, [],
                    check_in_comment)
                if isSuccess:
                    r_id = self.git_ops.getDMFID(r_path)
                    r_id_list.append(r_id)
                    success_status.append(("\tResource: ", str(r_name), "\n"))
                else:
                    failure_status.append("\t%10s : %s\n" % (r_name, err_msg))
                    if self.verbose:
                        print err_msg
        return success_status, failure_status, r_id_list, r_name_list

    def updateSimulation(self, sim_bytestream, sim_name, mimetype, confidence,
                         version_reqs, resource_id_list, target_folder_path,
                         check_in_comment=None, sim_id=None):
        success_status = []
        failure_status = []

        logging.getLogger("foqus." + __name__).debug(
            "Update simulation...")
        sim_path = os.path.join(target_folder_path, sim_name)
        self.createSubDir(sim_name, target_folder_path)
        latest_ver = self.common.concatVersion(
            *self.git_ops.getLatestVersion(sim_path))
        if not sim_id:
            if self.git_ops.isFileContentsIdentical(
                    sim_bytestream, sim_path):
                sim_id = self.git_ops.getDMFID(sim_path)
        else:
            obj_id, ver = self.common.splitDMFID(sim_id)
            if obj_id is None and ver is None:
                err = "ID: " + sim_id + " has incorrect format!"
                StatusDialog.displayStatus(err)
                return success_status, failure_status, None
            if not self.common.isVersion1OlderThanVersion2(
                    latest_ver, ver):
                # If version is same or older do nothing
                return success_status, failure_status, sim_id
            if self.verbose:
                print "Newer version exists. Upload as newer version?"
            result, is_major_ver, _ = \
                SaveOverwriteFileDialog.getSaveFileProperties(
                    "Upload New Simulation Dialog", self)
            if not result:
                return success_status, failure_status, sim_id
            isSuccess, err_msg = self.updateFiles(
                sim_bytestream, sim_path, is_major_ver, version_reqs,
                resource_id_list, check_in_comment)
            if isSuccess:
                sim_id = self.git_ops.getDMFID(sim_path)
                success_status.append(("\tSimulation: ", str(sim_name), "\n"))
            else:
                sim_id = None
                failure_status.append("\t%10s : %s\n" % (sim_name, err_msg))
                if self.verbose:
                    print err_msg
        return success_status, failure_status, sim_id

    def updateSinterConf(self, scf_bytestream, scf_name, mimetype,
                         confidence, version_reqs, sim_id_list,
                         target_folder_path, check_in_comment=None):
        success_status = []
        failure_status = []

        logging.getLogger("foqus." + __name__).debug(
            "Update sinter config...")
        scf_path = os.path.join(target_folder_path, scf_name)
        self.createSubDir(scf_name, target_folder_path)
        if self.git_ops.isFileContentsIdentical(
                scf_bytestream, scf_path):
            scf_id = self.git_ops.getDMFID(scf_path)
        else:
            if self.verbose:
                print "Newer version exists. Upload as newer version?"
            result, is_major_version, overwrite = \
                SaveOverwriteFileDialog.getSaveFileProperties(
                    "Upload New Sinter Config Dialog", self)
            if not result:
                scf_id = self.git_ops.getDMFID(scf_path)
                return success_status, failure_status, scf_id
            isSuccess, err_msg = self.updateFiles(
                scf_bytestream, scf_path, is_major_version, version_reqs,
                sim_id_list, check_in_comment)
            if isSuccess:
                scf_id = self.git_ops.getDMFID(scf_path)
                success_status.append(
                    ("\tSinter config: ", str(scf_name), "\n"))
            else:
                scf_id = None
                failure_status.append("\t%10s : %s\n" % (scf_name, err_msg))
                if self.verbose:
                    print err_msg
        return success_status, failure_status, scf_id

    def updateFiles(self, bytestream, path, is_major_version, version_reqs,
                    dependencies, check_in_comment):
        new_version = self.git_ops.getNewVersion(
            path, is_major_version)
        meta = self.git_ops.getLatestMeta(path)
        isSuccess, err_msg = self.git_ops.createVersionedDocument(
            bytestream, path, meta.get(ORIGINAL_NAME),
            meta.get(DESCRIPTION), meta.get(MIMETYPE), meta.get(EXTERNAL),
            meta.get(CONFIDENCE), version_reqs, self.user,
            version=new_version, dependencies=dependencies,
            check_in_comment=check_in_comment)
        return isSuccess, err_msg

    def createSimulation(self, sim_bytestream, sim_name, description, mimetype,
                         external, confidence, version_reqs, resource_id_list,
                         target_folder_path):
        logging.getLogger("foqus." + __name__).debug(
            "create simulation...")
        success_status = []
        failure_status = []
        sim_path = os.path.join(target_folder_path, sim_name)
        self.createSubDir(sim_name, target_folder_path)
        if os.path.exists(sim_path):
            return self.updateSimulation(
                sim_bytestream, sim_name, mimetype, confidence,
                version_reqs, resource_id_list, target_folder_path)

        isSuccess, err_msg = self.git_ops.createVersionedDocument(
            sim_bytestream, sim_path, sim_name, description,
            mimetype, external, confidence, version_reqs,
            creator=self.user, dependencies=resource_id_list)
        if isSuccess:
            sim_id = self.git_ops.getDMFID(sim_path)
            success_status.append(
                ("\tSimulation: ", str(sim_name), "\n"))
            if self.verbose:
                print "Success storing {s}.".format(s=sim_name)
        else:
            sim_id = None
            failure_status.append("\t%10s : %s\n" % (sim_name, err_msg))
        return success_status, failure_status, sim_id

    def createResources(self, resource_bytestream_list, resource_name_list,
                        description, mimetype, external,
                        confidence, version_reqs, target_folder_path):
        success_status = []
        failure_status = []
        r_id_list = []
        r_name_list = []
        for r, r_name in zip(resource_bytestream_list, resource_name_list):
            r_path = os.path.join(target_folder_path, r_name)
            self.createSubDir(r_name, target_folder_path)
            if os.path.exists(r_path):
                tmp_s_stats, tmp_f_stats, tmp_r_id_list, tmp_r_name_list = \
                    self.updateResources(
                        [r], [r_name], mimetype, external,
                        confidence, version_reqs, target_folder_path)
                SharedOps().aggregateStatuses(success_status, failure_status,
                                              tmp_s_stats, tmp_f_stats)
                r_id_list += tmp_r_id_list
                r_name_list += tmp_r_name_list
                continue
            isSuccess, err_msg = self.git_ops.createVersionedDocument(
                r, r_path, r_name, None,
                mimetype, None, confidence, None,
                creator=self.user, version=None)
            if isSuccess:
                r_id = self.git_ops.getDMFID(r_path)
                r_id_list.append(r_id)
                r_name_list.append(r_name)
                success_status.append(
                    ("\tResource: ", str(r_name), "\n"))
                if self.verbose:
                    print "Success storing {r}.".format(r=r_name)
            else:
                failure_status.append(
                    "\t%10s : %s\n" % (r_name, err_msg))
        return success_status, failure_status, r_id_list, r_name_list

    def createSinterConf(self, scf_bytestream, scf_name, description, mimetype,
                         external, confidence, version_reqs, sim_id_list,
                         target_folder_path):
        logging.getLogger("foqus." + __name__).debug(
            "Upload sinter config...")
        success_status = []
        failure_status = []
        scf_path = os.path.join(target_folder_path, scf_name)
        self.createSubDir(scf_name, target_folder_path)
        if os.path.exists(scf_path):
            return self.updateSinterConf(
                scf_bytestream, scf_name, mimetype, confidence, version_reqs,
                sim_id_list, target_folder_path)
        isSuccess, err_msg = self.git_ops.createVersionedDocument(
            scf_bytestream, scf_path, scf_name, description,
            mimetype, external, confidence, version_reqs,
            creator=self.user, dependencies=sim_id_list)
        if isSuccess:
            scf_id = self.git_ops.getDMFID(scf_path)
            success_status.append(("\tSinter config: ", str(scf_name), "\n"))
            if self.verbose:
                print "Success storing {s}.".format(s=scf_name)
        else:
            scf_id = None
            failure_status.append("\t%10s : %s\n" % (scf_name, err_msg))
        return success_status, failure_status, scf_id

    def createSubDir(self, file_path, target_path):
        path_split = file_path.split(os.sep)
        if len(path_split[:-1]) == 0:
            return
        for d in path_split[:-1]:
            target_path = os.path.join(target_path, d)
            if os.path.exists(target_path):
                if self.verbose:
                    print "Folder exists for path {p}.".format(p=target_path)
                continue
            create_folder_status = self.git_ops.createFolder(
                target_path, d, '')
            if not create_folder_status:
                if self.verbose:
                    print "Unable to create subdirectory at path: {p}.".format(
                        p=target_path)
                break
            else:
                if self.verbose:
                    print "Success creating subdir with path: {p}".format(
                        p=target_path)

    def isLatestVersion(self, dmf_id):
        if self.verbose:
            print "Checking if dmf_id is latest version..."
        return self.git_ops.doesDMFIDHaveLatestVersion(dmf_id)

    def getSession(self):
        if self.verbose:
            print "Getting session byte array stream and path..."
        try:
            return (self.session_byte_array_stream, self.session_path)
        except:
            return (None, ) * 2

    def getByteArrayStream(self):
        if self.verbose:
            print "Getting byte array stream..."
        try:
            return self.byte_array_stream
        except:
            return None

    def getByteArrayStreamById(self, dmf_id):
        if self.verbose:
            print "Get byte array stream by id..."
        try:
            if dmf_id is None:
                StatusDialog.displayStatus("ID argument is None.")
                return None
            if not isinstance(dmf_id, str):
                StatusDialog.displayStatus("ID is not of str instance")
                return None
            dmf_id_only, dmf_ver = self.common.splitDMFID(dmf_id)
            maj_ver, min_ver = self.common.splitVersion(dmf_ver)
            path = self.git_ops.getPathByDMFID(dmf_id_only, maj_ver, min_ver)
            with open(path, 'rb') as f:
                return bytearray(f.read())

        except Exception, e:
            if self.verbose:
                print e.__class__.__name__, \
                    PRINT_COLON, traceback.format_exc()
            StatusDialog.displayStatus(str(e))

    def getSimFileByteArrayStreamByName(self, name):
        if self.verbose:
            print "Getting sim file byte array stream by name..."
        if name is None:
            StatusDialog.displayStatus("Name argument is None.")
            return None
        if not isinstance(name, str):
            StatusDialog.displayStatus("Name is not of str instance")
            return None

        sim_folder = os.path.join(self.user_root, "Simulation")
        sim_path = os.path.join(sim_folder, name)
        try:
            major_version, minor_version = self.git_ops.getLatestVersion(
                sim_path)
            version = self.common.concatVersion(major_version, minor_version)
            return self.git_ops.downloadFile(sim_path, version, dst_path=None)
        except Exception, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, traceback.format_exc()
            StatusDialog.displayStatus(str(e))
            return None

    def upload_to_alfresco(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, \
                "Upload to Alfresco clicked."
        remote_username = ''
        remote_password = ''
        user_label = None
        password_label = None

        if platform.system().startswith(WINDOWS):  # We are on Windows
            PROP_LOC = os.environ[REPO_PROPERTIES_WIN_PATH] \
                + WIN_PATH_SEPARATOR
        else:
            PROP_LOC = os.environ[REPO_PROPERTIES_UNIX_PATH] \
                + UNIX_PATH_SEPARATOR
        self.setEnabled(False)
        while True:
            repo_properties = [
                PROP_LOC + f for f in os.listdir(PROP_LOC)
                if os.path.isfile(os.path.join(PROP_LOC, f)) and
                f.endswith(PROPERTIES_EXT)]
            repo_name_list = []
            status_list = []
            for p in repo_properties:
                is_valid, return_vals = self.common.validateAndGetKeyProps(
                    os.path.join(PROP_LOC, p))
                if is_valid:
                    try:
                        status_code = urlopen(
                            return_vals[1] + SHARE_LOGIN_EXT,
                            timeout=REQUESTS_TIMEOUT).getcode()
                    except:
                        status_code = 500
                    repo_name_list.append(return_vals[0])
                    status_list.append(status_code)
                else:
                    repo_properties.remove(p)

            select_repo_dialog = SelectRepoDialog()
            result, index, repo_name = select_repo_dialog.getDialog(
                repo_name_list, status_list, self.DMF_HOME)

            if index < len(repo_name_list):
                config = repo_properties[index]
            else:
                config = None
            if result:
                break
            else:
                self.setEnabled(True)
                return

        while True:
            remote_username, remote_password, _, result = \
                LoginDialog.getCredentials(
                    remote_username,
                    remote_password,
                    user_label,
                    password_label,
                    save_option=False,
                    parent=self)

            if not result:
                self.setEnabled(True)
                return '', ''
            if remote_username != '' and remote_password != '':
                break
            else:
                if remote_username == '':
                    user_label = "<font color='Red'>Username:*</font>"
                else:
                    user_label = None
                if remote_password == '':
                    password_label = "<font color='Red'>Password:*</font>"
                else:
                    password_label = None

        entry_point = None
        self.gateway = JavaGateway()
        if entry_point is None:
            if self.verbose:
                print "Java Gateway not initialized."
                sys.stdout.write("Trying.")
            for i in xrange(GATEWAY_ENTRYPOINT_CONNECTION_RETRY):
                # Retry a number of times until gateway is activated
                try:
                    entry_point = self.gateway.entry_point
                    data_folder_map = \
                        self.gateway.jvm.ccsi.dm.data.DataFolderMap
                    self.data_model_vars = \
                        self.gateway.jvm.ccsi.dm.data.DataModelVars

                    self.data_operator = entry_point.getDataOperationsImpl()
                    if self.verbose:
                        sys.stdout.write('\n')
                        sys.stdout.flush()
                        print "Java Gateway now initialized."
                    break
                except Exception, e:
                    time.sleep(RETRY_SLEEP_DURATION)
                    if i == GATEWAY_ENTRYPOINT_CONNECTION_RETRY - 1:
                        self.setEnabled(True)
                        StatusDialog.displayStatus(
                            "Failed to initialize Java Gateway!")
                        raise
                    else:
                        if self.verbose:
                            sys.stdout.write('.')
                            sys.stdout.flush()

        if entry_point is not None:
            conn = entry_point.getConnectionClient(
                config, remote_username, remote_password)
            conn.createAtomSession()
            self.session = conn.getAtomSession()
            root_folder = self.data_operator.getHighLevelFolder(
                self.session, data_folder_map.USER_HOMES)
            user_folder = self.data_operator.getTargetFolderInParentFolder(
                self.session, root_folder.getPath(), remote_username, True)
            try:
                self.buildDependencyMap(self.user_root, initial=True)
                status = self.uploadAllDataObjects(user_folder)
                if status:
                    msg = "Uploading to Alfresco completed!"
                    StatusDialog.displayStatus(str(msg))
                else:
                    StatusDialog.displayStatus(
                        "Upload to Alfresco completed with errors.")
            except Exception, e:
                if self.verbose:
                    print self.__class__.__name__, PRINT_COLON, e
                StatusDialog.displayStatus(
                    "Upload to Alfresco completed with errors.")

        self.session = None
        entry_point = None
        data_folder_map = None
        self.data_operator = None
        self.gateway = None
        self.setEnabled(True)

    def buildDependencyMap(self, path, initial=False):
        if initial:
            self.file_dep_map = {}
            self.folder_list = []
        f = os.listdir(path)
        for f in os.listdir(path):
            if f.startswith('.'):
                continue
            f_path = os.path.join(path, f)
            if os.path.isdir(f_path):
                if initial and f_path.endswith("Simulation"):
                    self.folder_list.insert(0, f_path)
                else:
                    self.folder_list.append(f_path)
                self.buildDependencyMap(f_path)
            else:
                meta = self.git_ops.getLatestMeta(f_path)
                dependencies = meta.get(DEPENDENCIES)
                self.file_dep_map[f_path] = dependencies if dependencies \
                    else None

    def uploadAllDataObjects(self, target_folder):
        is_succeed = True
        sync_comment = self.SYNC_COMMENT

        dialog = StatusDialog(
            "Begin bulk uploading of folder " + self.user_root + " ...",
            use_padding=True,  parent=self)
        dialog.show()
        # Create folders first
        while self.folder_list:
            dialog.close()
            dialog.deleteLater()
            path = self.folder_list.pop(0)
            meta = self.git_ops.getLatestMeta(path)
            folder_name = meta.get(DISPLAY_NAME)
            target_path = (
                target_folder.getPath() + UNIX_PATH_SEPARATOR +
                os.path.relpath(path, self.user_root))
            does_folder_exist = self.data_operator.doesCmisObjectExist(
                self.session, target_path)
            if does_folder_exist:
                # TODO: Update description if possible
                pass
            else:
                dialog = StatusDialog(
                    "Creating folder " +
                    folder_name +
                    " ...",
                    use_padding=True,
                    parent=self)
                dialog.show()
                description = '(' + sync_comment + ')'
                if len(meta.get(DESCRIPTION)) > 0:
                    folder_description = (
                        meta.get(DESCRIPTION) + '\n' + description)
                else:
                    folder_description = description
                create_folder_status = self.data_operator.createFolder(
                    self.session.getObjectByPath(os.path.dirname(target_path)),
                    meta.get(DISPLAY_NAME),
                    folder_description,
                    False)
                if create_folder_status.isOperationSuccessful():
                    self.session.getObject(
                        create_folder_status.getDataObjectID())
                else:
                    err_msg = create_folder_status.getStatusMessage()
                    dialog.close()
                    StatusDialog.displayStatus(err_msg)
                    return False
        dialog.close()
        dialog.deleteLater()

        # Handle files here
        keys = self.file_dep_map.keys()
        processed = {}
        while self.file_dep_map:
            f_path = keys[0]
            dep = self.file_dep_map.get(f_path)
            f_path_dmf_id = self.git_ops.getDMFID(f_path)
            dialog = StatusDialog(
                "Begin processing upload of file " +
                os.path.basename(f_path) + " ...",
                use_padding=True,  parent=self)
            dialog.show()

            if dep is None:
                self.file_dep_map.pop(keys.pop(0))
                f_id, _ = self.common.splitDMFID(f_path_dmf_id)
                processed[f_id] = None
            else:
                has_processed_dep = True
                for dep_id in dep:
                    dep_id, _ = self.common.splitDMFID(dep_id)
                    if not processed.get(dep_id):
                        keys.append(keys.pop(0))
                        has_processed_dep = False
                        break
                if not has_processed_dep:
                    try:
                        dialog.close()
                        dialog.deleteLater()
                    except:
                        pass
                    continue
                else:
                    f_id, _ = self.common.splitDMFID(f_path_dmf_id)
                    processed[f_id] = None
                    self.file_dep_map.pop(keys.pop(0))

            # Create and update map
            meta = self.git_ops.getLatestMeta(f_path)
            target_path = (
                target_folder.getPath() + UNIX_PATH_SEPARATOR +
                os.path.relpath(f_path, self.user_root).replace(
                    WIN_PATH_SEPARATOR, UNIX_PATH_SEPARATOR))
            with open(str(f_path), "rb") as f:
                pwc = None
                does_file_exist = \
                    self.data_operator.doesCmisObjectExist(
                        self.session, target_path)
                if does_file_exist:
                    original_doc = self.session.getObjectByPath(
                        target_path)
                    if original_doc.isVersionSeriesCheckedOut():
                        if self.verbose:
                            print "File checked out. Skipping."
                        StatusDialog.displayStatus(
                            f_path + " is checked out. Skipping.")
                        o_id, _ = self.common.splitDMFID(
                            original_doc.getId().replace(NODE_PREFIX, ''))
                        processed[f_id] = (o_id + SEMI_COLON + NA_VER)
                        try:
                            dialog.close()
                            dialog.deleteLater()
                        except:
                            pass
                        continue
                    else:
                        checkout_id = original_doc.checkOut()
                        pwc = self.session.getObject(checkout_id)

                try:
                    description = (
                        sync_comment + "\nData object: " + f_path_dmf_id)
                    if meta.get(DESCRIPTION) is None or len(
                            meta.get(DESCRIPTION)) > 0:
                        file_description = description
                    else:
                        file_description = (
                            meta.get(DESCRIPTION) + "\n" + description)
                    parents = self.gateway.jvm.java.util.ArrayList()
                    if target_path.endswith(SINTER_CONFIG_EXT):
                        try:
                            f_json = json.loads(f.read().decode(UTF8))
                            f.seek(0)  # reset
                        except:
                            pass

                    if meta.get(DEPENDENCIES):
                        for d in meta.get(DEPENDENCIES):
                            d_id, _ = self.common.splitDMFID(d)
                            new_d_id = processed.get(d_id)
                            parents.add(new_d_id)
                            if target_path.endswith(SINTER_CONFIG_EXT):
                                f_json["CCSIFileMetaData"][
                                    "Simulation ID"] = new_d_id
                    if len(parents) == 0:
                        parents = None
                    if self.verbose:
                        print "Debug (dependencies): ", parents
                    try:
                        bytearray_content = bytearray(
                            json.dumps(
                                f_json,
                                UTF8,
                                sort_keys=True,
                                indent=4,
                                separators=(',', ': ')))
                    except:
                        bytearray_content = bytearray(f.read())
                    handler = SaveFileHandlerDialog(
                        self,
                        bytearray_content,
                        self.session.getObjectByPath(
                            os.path.dirname(target_path)),
                        meta.get(DISPLAY_NAME),
                        meta.get(ORIGINAL_NAME),
                        file_description,
                        meta.get(MIMETYPE),
                        meta.get(EXTERNAL),
                        meta.get(CONFIDENCE),
                        parents=parents,
                        isMajorVersion=True,
                        pwc=pwc,
                        check_in_comment=sync_comment,
                        display_status=True,
                        refresh_at_end=False)
                    self.uploadWait()
                except:
                    if self.verbose:
                        print sys.exc_traceback.tb_lineno
                    raise
                if handler.status.isOperationSuccessful():
                    doc_id = self.session.getObjectByPath(
                        target_path).getId().replace(NODE_PREFIX, '')
                    f_id, _ = self.common.splitDMFID(
                        self.git_ops.getDMFID(f_path))
                    processed[f_id] = doc_id
                    if self.verbose:
                        print "Success in storing file.", doc_id
                else:
                    err_msg = handler.status.getStatusMessage()
                    StatusDialog.displayStatus(err_msg)
                    if self.verbose:
                        print err_msg
                    break
            try:
                dialog.close()
                dialog.deleteLater()
            except:
                pass
        return is_succeed

    # Needed to work with save_file_handler_dialog
    def uploadWait(self):
        if self.verbose:
            print "Waiting for upload to complete..."
        self.wait_loop = QEventLoop(self)
        self.wait_loop.exec_()
        self.wait_loop.deleteLater()

    def setUpdateComment(self, update_comment):
        self.update_comment = update_comment

    def getParents(self):
        try:
            return self.parents
        except:
            return None

    def setParents(self, parents):
        logging.getLogger("foqus." + __name__).debug(
            "Parents: {p}".format(p=parents))
        new_parents = []
        for parent in parents:
            if not parent:
                continue
            elif parent.startswith(FIND_SINTER_INDICATOR):
                try:
                    sim_id = parent.replace(FIND_SINTER_INDICATOR, '')
                    sim_id, sim_version = self.common.splitDMFID(sim_id)
                    sim_major_version, sim_minor_version = self.common.\
                        splitVersion(sim_version)
                    # get simulation meta
                    sim_path = self.git_ops.getPathByDMFID(
                        sim_id, sim_major_version, sim_minor_version)
                    sim_path_no_ext = os.path.splitext(sim_path)[0]
                    sinter_config_path = sim_path_no_ext + SINTER_CONFIG_EXT
                    new_parents.append(self.git_ops.getDMFID(
                        sinter_config_path))
                except Exception, e:
                    _, _, tb = sys.exc_info()
                    logging.getLogger("foqus." + __name__).error(
                        "Exception at line {n}: {e}".format(
                            n=traceback.tb_lineno(tb),
                            e=str(e)))
                    if self.verbose:
                        print e.__class__.__name__, PRINT_COLON, \
                            traceback.format_exc()
            else:
                new_parents.append(parent)
        self.parents = new_parents

    def setSavedMetadata(self, id):
        self.return_dmf_id = id

    def getSavedMetadata(self):
        try:
            return self.return_dmf_id
        except:
            return None

    def handleFilterChange(self, text):
        for i in xrange(self.model.rowCount()):
            self.tree_ops.filterDocuments(
                self.tree_view,
                self.model.item(i, 0),
                self.model,
                self.filter_values[self.filters.index(str(text))])

    def getSimulationList(self, path=None):
        sim_names = []
        sim_ids = []
        sc_ids = []

        if not path:
            path = self.sim_folder
        if os.path.isfile(path):
            self.appendSimAttr(sim_names, sim_ids, sc_ids,
                               *self.getSimAttr(path))
        elif os.path.isdir(path):
            path_files = [f for f in os.listdir(path) if not f.startswith('.')]
            for f in path_files:
                f_path = os.path.join(path, f)
                if os.path.isdir(f_path):
                    tmp_names, tmp_ids, tmp_sc_ids = self.getSimulationList(
                        f_path)
                    sim_ids += tmp_ids
                    sim_names += tmp_names
                    sc_ids += tmp_sc_ids
                else:
                    self.appendSimAttr(sim_names, sim_ids, sc_ids,
                                       *self.getSimAttr(f_path))
        return sim_names, sim_ids, sc_ids

    def appendSimAttr(self, sim_names, sim_ids, sc_ids,
                      sim_name, sim_id, sc_id):
        if sim_name and sim_id and sc_id:
            sim_names.append(sim_name)
            sim_ids.append(sim_id)
            sc_ids.append(sc_id)
        return sim_names, sim_ids, sc_ids

    def getSimAttr(self, f_path):
        sim_name = None
        sim_id = None
        sc_id = None
        if f_path.endswith(".json"):
            with open(f_path, 'rb') as f:
                f_json = json.loads(f.read().decode(UTF8))
                if f_json[SC_TYPE] == SC_TYPENAME:
                    sc_ccsi_meta = f_json.get(CCSI_EMBEDDED_METADATA)
                    sim_id = sc_ccsi_meta.get(CCSI_SIM_ID_KEY)
                    sim_name = f_json.get(SC_TITLE)
                    sc_id = self.git_ops.getDMFID(f_path)
        return sim_name, sim_id, sc_id

    def turbineSync(self, turbine_config, session_sim_list, turbine_sim_list):
        for sim_name in session_sim_list:
            update_turbine_sim = False
            if sim_name not in turbine_sim_list:
                # Simulation not in turbine: upload
                update_turbine_sim = True
                StatusDialog.displayStatus(
                    "The simulation " + sim_name +
                    " is not available on Turbine attempting to add it " +
                    "from the DMF")
            else:
                # Check if newer simulation is available
                sinter_config = turbine_config.getSinterConfig(sim_name)
                sc_meta = sinter_config.get(CCSI_EMBEDDED_METADATA, None)
                if sc_meta:
                    sim_id = sc_meta["Simulation ID"]
                    if sim_id:
                        is_latest = self.isLatestVersion(sim_id)
                    else:
                        is_latest = False
                else:
                    is_latest = False

                if not is_latest:
                    # TODO: Set message box to prompt user whether updating
                    # to newer turbine sim is desired
                    update_turbine_sim = True

            if update_turbine_sim:
                # Get sinter config
                sc = self.getSimFileByteArrayStreamByName(
                    str(sim_name + SINTER_CONFIG_EXT))
                if sc:
                    sc_file = "temp/sinter_config.json"
                    with open(sc_file, 'wb') as f:
                        f.write(sc)
                    sc_json = json.loads(sc.decode(UTF8))
                    sim_id = sc_json[CCSI_EMBEDDED_METADATA]["Simulation ID"]
                    input_files = sc_json[CCSI_EMBEDDED_METADATA].get(
                        "InputFiles", [])
                    sim_file, sim_resource, a = \
                        turbine_config.sinterConfigGetResource(
                            sc_file, checkExists=False)
                    sim_file = os.path.join("temp", sim_file)
                    with open(sim_file, 'wb') as f:
                        f.write(self.getByteArrayStreamById(str(sim_id)))

                    resources = []
                    resource_files = []
                    resource_bytestreams = []

                    for resource_data in input_files:
                        resource_data = resource_data[CCSI_EMBEDDED_METADATA]
                        rid = resource_data.get("Resource ID", None)
                        rdn = resource_data.get("Resource Display Name", None)
                        if not rid or not rdn:
                            continue
                        resource_bytestreams.append(
                            self.getByteArrayStreamById(str(rid)))
                        resource_files.append(os.path.join("temp", rdn))
                        resources.append([rdn, os.path.join("temp", rdn)])
                        for i, fname in enumerate(resource_files):
                            with open(fname, 'wb') as f:
                                f.write(resource_bytestreams[i])

                turbine_config.uploadSimulation(
                    sim_name,
                    sc_file,
                    update=True,
                    otherResources=resources)
