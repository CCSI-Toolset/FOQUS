'''
    alfresco.py

    * The main script dealing with handling the filesystem that is
    * stored using the Alfresco repository

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
import logging
import platform
import traceback
import collections
from datetime import datetime

from PySide.QtGui import (
    QWidget,
    QIcon,
    QLineEdit,
    QLabel,
    QMenu,
    QPixmap,
    QAction,
    QComboBox,
    QStandardItem,
    QStandardItemModel,
    QTreeView,
    QVBoxLayout,
    QHBoxLayout,
    QBoxLayout,
    QGridLayout,
    QPushButton,
    QFileDialog,
    QSpacerItem,
    QSplitter,
    QScrollArea,
    QDesktopWidget
)

from PySide.QtCore import (
    Qt,
    QEventLoop,
    QModelIndex,
    Slot
)

from py4j.java_gateway import (
    JavaGateway,
    Py4JError,
    Py4JJavaError,
    Py4JNetworkError
)

from dmf_lib.common.common import (
    SU,
    PWC,
    OPEN,
    SAVE,
    QUIT,
    CANCEL,
    GRAPH,
    LOGOUT,
    SEMI_COLON,
    PRINT_COLON,
    DMF_HOME,
    WINDOWS,
    WIN_PATH_SEPARATOR,
    UNIX_PATH_SEPARATOR,
    REPO_PROPERTIES_WIN_PATH,
    REPO_PROPERTIES_UNIX_PATH,
    GATEWAY_ENTRYPOINT_CONNECTION_RETRY,
    RETRY_SLEEP_DURATION,
    HTTP_SUCCESS_CODE,
    KEYS_EXT,
    TMP_KEYS_EXT,
    NODE_PREFIX,
    DMFSERV_PATH_PREFIX,
    CCSI_EMBEDDED_METADATA,
    FIND_SINTER_INDICATOR,
    SC_TITLE,
    SC_TYPE,
    SC_TYPENAME,
    CCSI_SIM_ID_KEY,
    SINTER_CONFIG_EXT,
    NUM_COLUMN,
    NAME_COLUMN,
    KIND_COLUMN,
    DATE_MOD_COLUMN,
    NODE_ID_COLUMN,
    DEFAULT_NAME_COLUMN_WIDTH,
    DOCUMENT_DISPLAY_STRING,
    FOLDER_DISPLAY_STRING,
    DEFAULT_DMF_MIMETYPE,
    UTF8
)

from dmf_lib.gui.path import (
    ACTION_IMAGE_PATH,
    FILETYPE_IMAGE_PATH,
    FOLDER_OPENED,
    FOLDER_CLOSED,
    TEXT_FILE,
    LOCKED_FILE,
    LOCK,
    EDIT,
    UNLOCK,
    UPLOAD,
    DOWNLOAD,
    PERMISSIONS,
    RELOAD,
    FILE_UPLOAD,
    FOLDER_UPLOAD,
    CREATE_FOLDER,
    FILE_PREVIEW_HEADER,
    FILE_PREVIEW_TAIL,
    FOLDER_PREVIEW
)

from dmf_lib.filesystem.file_filters import (
    FILE_FILTERS,
    FILE_FILTER_VALUES
)

from dmf_lib.dialogs.new_folder_dialog import FolderDialog
from dmf_lib.dialogs.status_dialog import StatusDialog
from dmf_lib.dialogs.select_ver_dialog import SelectVersionDialog
from dmf_lib.dialogs.progress_dialog import ProgressDialog
from dmf_lib.dialogs.permissions_dialog import PermissionsDialog
from dmf_lib.dialogs.save_file_dialog import SaveFileDialog
from dmf_lib.dialogs.save_file_dialog import SaveOverwriteFileDialog
from dmf_lib.dialogs.detailed_info_dialog import DetailedInfoDialog
from dmf_lib.dialogs.save_file_handler_dialog import SaveFileHandlerDialog
from dmf_lib.alfresco.share.adaptor import AlfrescoShareAdaptor
from dmf_lib.alfresco.service.adaptor import AlfrescoServiceAdaptor
from dmf_lib.common.methods import Common
from dmf_lib.filesystem.tree_ops import TreeOps
from dmf_lib.filesystem.shared_ops import SharedOps
from dmf_lib.graph.graph_viewer import Grapher

try:
    from dmf_lib.test.test import Test
except:
    pass
try:
    from foqus_lib.framework.graph.nodeModelTypes import nodeModelTypes
    print "Successfully imported nodeModelTypes..."
except Exception, e:
    print traceback.print_exc()

__author__ = 'You-Wei Cheah <ycheah@lbl.gov>'


class AlfrescoFileSystem(QWidget):
    # Static variables
    FOQUS_SESSION_TYPE = "FOQUS_Session"
    JVM_CONN_MSG = "Unable to connect to JVM!"
    JVM_RESET_CONN_MSG = "Connection to JVM was reset. Please relogin."
    REPO_CONN_MSG = "Unable to connect to Repository!"
    SHARE_FTS_MSG = "Unable to connect to Alfresco Share FTS!"
    IS_OPEN_MODE = False
    IS_BROWSER_MODE = False

    def __init__(self, parent=None):
        super(AlfrescoFileSystem, self).__init__(parent)
        self.common = Common()
        self.verbose = parent.verbose if parent else False
        self.root = parent if parent else None
        self.gateway = JavaGateway()
        if self.root:
            self.user = self.root.user
            self.repo_fname = self.root.repo_fname

        if parent.IS_OPEN_MODE:
            AlfrescoFileSystem.IS_OPEN_MODE = True
        else:
            AlfrescoFileSystem.IS_OPEN_MODE = False
        if parent.IS_BROWSER_MODE:
            AlfrescoFileSystem.IS_BROWSER_MODE = True
        else:
            AlfrescoFileSystem.IS_BROWSER_MODE = False

        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "OPEN_MODE", \
                PRINT_COLON, AlfrescoFileSystem.IS_OPEN_MODE
            print self.__class__.__name__, PRINT_COLON, "BROWSER_MODE", \
                PRINT_COLON, AlfrescoFileSystem.IS_BROWSER_MODE

        if platform.system().startswith(WINDOWS):  # We are on Windows
            self.PATH_SEPARATOR = WIN_PATH_SEPARATOR
        else:
            self.PATH_SEPARATOR = UNIX_PATH_SEPARATOR

        self.DMF_HOME = os.environ[DMF_HOME]

        try:
            os.environ[DMF_HOME]
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, \
                    os.environ[DMF_HOME]
        except KeyError:
            print "Please set the environment for", DMF_HOME
            return

        self.folder_opened_icon = QIcon(
            self.DMF_HOME + FILETYPE_IMAGE_PATH + FOLDER_OPENED)
        self.folder_closed_icon = QIcon(
            self.DMF_HOME + FILETYPE_IMAGE_PATH + FOLDER_CLOSED)
        self.document_icon_url = (
            self.DMF_HOME + FILETYPE_IMAGE_PATH + TEXT_FILE)
        self.document_icon = QIcon(self.document_icon_url)
        self.locked_document_icon_url = (
            self.DMF_HOME + FILETYPE_IMAGE_PATH + LOCKED_FILE)
        self.locked_document_icon = QIcon(self.locked_document_icon_url)
        self.lock_icon_url = self.DMF_HOME + FILETYPE_IMAGE_PATH + LOCK
        self.lock_icon = QIcon(self.lock_icon_url)

        # Initialize necessary session and gateway variables
        self.entry_point = None
        self.session = None

        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)
        if AlfrescoFileSystem.IS_BROWSER_MODE:
            self.root.updateSplash("Connecting to Java Gateway...")
        if self.entry_point is None:
            if self.verbose:
                print "Java Gateway not initialized."
                sys.stdout.write("Trying.")
            for i in xrange(GATEWAY_ENTRYPOINT_CONNECTION_RETRY):
                # Retry a number of times until gateway is activated
                try:
                    self.initJavaGatewayEntryPoint()
                    if self.verbose:
                        sys.stdout.write('\n')
                        sys.stdout.flush()
                        print "Java Gateway now initialized."
                    break
                except Exception, e:
                    time.sleep(RETRY_SLEEP_DURATION)
                    if i == GATEWAY_ENTRYPOINT_CONNECTION_RETRY - 1:
                        print (AlfrescoFileSystem.JVM_CONN_MSG + " " +
                               traceback.format_exc())
                        StatusDialog.displayStatus(
                            AlfrescoFileSystem.JVM_CONN_MSG +
                            " " + traceback.format_exc())
                        self.logoutClicked()
                        raise
                    else:
                        if self.verbose:
                            sys.stdout.write('.')
                            sys.stdout.flush()
                        pass

        if self.entry_point is not None:
            try:
                self.conn = self.entry_point.getConnectionClient(
                    self.root.config, self.root.user, self.root.password)
                # Use this code to verify login instantaneously
                status = self.conn.login()
                if status:
                    self.conn.logout()
                else:
                    raise
                self.conn.createAtomSession()
                self.session = self.conn.getAtomSession()
                self.connURL = self.conn.getAlfrescoURL()
                self.user = self.conn.getUser()
                self.password = self.conn.getPassword()
            except Exception, e:
                if self.verbose:
                    print "Error logging in."
                    print self.root.config
                    print e
                # Since parent widgets differ,
                # order in which status dialog appears is important
                # dependending on operation mode
                if "Connection refused" in str(e):
                    err_message = (
                        "Connection refused from repo " +
                        self.root.repo_fname + '.')
                else:
                    err_message = "Error logging in to Alfresco."
                if not AlfrescoFileSystem.IS_BROWSER_MODE:
                    StatusDialog.displayStatus(err_message)
                self.logoutClicked()
                self.closeRootDialog()
                if AlfrescoFileSystem.IS_BROWSER_MODE:
                    StatusDialog.displayStatus(err_message)
                return None
        try:
            if self.verbose:
                t_start_millis = int(round(time.time() * 1000))
            self.cmisBrowserSetup()
            if self.verbose:
                t_end_millis = int(round(time.time() * 1000))
                print "t-browser-setup: ", (t_end_millis - t_start_millis)

        except Exception, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, e

    def initJavaGatewayEntryPoint(self):
        try:
            self.entry_point = self.gateway.entry_point
            self.java_io = self.gateway.jvm.java.io
            self.data_model_vars = self.gateway.jvm.ccsi.dm.data.DataModelVars
            self.data_folder_map = self.gateway.jvm.ccsi.dm.data.DataFolderMap
            apache_chemistry = self.gateway.jvm.org.apache.chemistry
            opencmis_commons = apache_chemistry.opencmis.commons
            self.property_ids = opencmis_commons.PropertyIds
            self.basetype_id = opencmis_commons.enums.BaseTypeId
            self.basic_permissions = opencmis_commons.BasicPermissions
            self.role = self.gateway.jvm.ccsi.dm.accesscontrol.Role
            self.CMIS_FOLDER = str(self.basetype_id.CMIS_FOLDER)
            self.CMIS_DOCUMENT = str(self.basetype_id.CMIS_DOCUMENT)

        except:
            self.entry_point = None
            raise

    def dereference(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Dereferencing..."
        self.session = None
        self.fs_ops_hbox.removeWidget(self.cancel_button)
        if self.isOpenOrBrowserMode():
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
        try:
            self.cookiejar.clear()
        except:
            if self.verbose:
                print "Cookie jar not present."

        # ------------------------------------------------------------------- #
        # Delete QT elements                                                  #
        # ------------------------------------------------------------------- #
        try:
            if self.isOpenOrBrowserMode():
                self.open_button.deleteLater()
                if AlfrescoFileSystem.IS_BROWSER_MODE:
                    self.refresh_button.deleteLater()
                    self.logout_button.deleteLater()
                    self.download_button.deleteLater()
                    self.upload_button.deleteLater()
                    self.edit_button.deleteLater()
                    self.lock_button.deleteLater()
                    self.new_folder_button.deleteLater()
                    self.permissions_button.deleteLater()
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
            self.fs_ops_hbox.deleteLater()
            self.fs_splitter.deleteLater()

            self.search.deleteLater()
        except:
            raise
        # ------------------------------------------------------------------- #

        # ------------------------------------------------------------------- #
        # Nullify deleted QT elements and other unused variables              #
        # ------------------------------------------------------------------- #
        if self.isOpenOrBrowserMode():
            self.open_button = None
            self.fs_ops_hbox_spacer = None
            if AlfrescoFileSystem.IS_BROWSER_MODE:
                self.refresh_button = None
                self.logout_button = None
                self.download_button = None
                self.upload_button = None
                self.edit_button = None
                self.lock_button = None
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

        self.fs_ops_hbox = None
        self.fs_display_hbox = None
        self.tree_view = None
        self.model = None

        self.fs_ops = None
        self.fs_display = None

        self.connURL = None
        self.entry_point = None
        self.cookiejar = None
        self.search = None
        # ------------------------------------------------------------------- #

    def cmisBrowserSetup(self):
        if AlfrescoFileSystem.IS_BROWSER_MODE:
            self.root.updateSplash("Creating GUI components...")
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Search Repository")
        self.search.setAlignment(Qt.AlignLeft)
        self.search.returnPressed.connect(self.onSearchClicked)
        self.search.textChanged.connect(self.onSearchClicked)

        # ------------------------------------------------------------------- #
        # Initialize model for tree view                                      #
        # ------------------------------------------------------------------- #
        self.default_model = QStandardItemModel(self)
        self.model = self.default_model
        self.model.setColumnCount(NUM_COLUMN)

        # Create header
        self.tree_ops = TreeOps(self)
        self.tree_ops.setModelHeaders(self.model)
        # ------------------------------------------------------------------- #

        # ------------------------------------------------------------------- #
        # Initialize tree view and set appropriate settings                   #
        # ------------------------------------------------------------------- #
        self.tree_view = QTreeView(self)
        self.tree_ops.setupTreeViewWithModel(self.tree_view, self.model)
        self.tree_view.clicked.connect(self.onTreeViewClicked)
        self.tree_view.expanded.connect(self.expanded)
        self.tree_view.collapsed.connect(self.collapsed)
        self.tree_view_selected = self.tree_view.selectionModel()
        self.tree_view_selected.selectionChanged.connect(
            self.handleSelectionChanged)
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
            self.handleComboBoxChange)

        if not AlfrescoFileSystem.IS_OPEN_MODE:
            self.file_name_filter.hide()
            self.label_file_name.hide()
            self.target_file_name.hide()
            # Set to select all for Browser mode
            self.file_name_filter.setCurrentIndex(len(self.filters))

        # ------------------------------------------------------------------- #
        # Main Alfresco file browser buttons here                             #
        # ------------------------------------------------------------------- #
        if self.isOpenOrBrowserMode():
            if AlfrescoFileSystem.IS_OPEN_MODE:
                self.open_button = QPushButton(OPEN, self)
            else:
                self.open_button = QPushButton(GRAPH, self)
                self.new_folder_button = QPushButton("Create Folder", self)
                self.edit_button = QPushButton("Edit Properties", self)
                self.upload_button = QPushButton("Upload... ", self)
                self.download_button = QPushButton("Download", self)
                self.lock_button = QPushButton("Lock", self)
                self.permissions_button = QPushButton(
                    "Manage Permissions", self)
                # Not ready for release
                self.permissions_button.setEnabled(False)
                self.logout_button = QPushButton(LOGOUT, self)
                self.refresh_button = QPushButton(self)
                self.hbox_spacer2 = QSpacerItem(
                    QDesktopWidget().screenGeometry().width(), 0)
            self.fs_ops_hbox_spacer = QSpacerItem(
                QDesktopWidget().screenGeometry().width(), 0)
        else:
            self.new_folder_button = QPushButton("New Folder", self)
            self.save_button = QPushButton(SAVE, self)

        if AlfrescoFileSystem.IS_BROWSER_MODE:
            self.cancel_button = QPushButton(QUIT, self)
            if self.verbose:
                self.test_button = QPushButton("Test", self)
                self.test_button.clicked.connect(self.testClicked)
        else:
            self.cancel_button = QPushButton(CANCEL, self)

        # Set button sizes, also other graphical attributes
        # and connect buttons to functions
        if self.isOpenOrBrowserMode():
            self.open_button.setMaximumWidth(100)
            self.open_button.setMinimumWidth(100)
            self.open_button.clicked.connect(self.openClicked)
            if AlfrescoFileSystem.IS_BROWSER_MODE:
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
                self.edit_button.setEnabled(False)
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
                    upload_file_icon, "   Upload File", self)
                self.upload_folder = QAction(
                    upload_folder_icon, "   Upload Folder", self)
                upload_menu.addAction(self.upload_file)
                upload_menu.addAction(self.upload_folder)

                self.upload_file.triggered.connect(self.uploadFileClicked)
                self.upload_folder.triggered.connect(self.uploadFolderClicked)

                self.upload_button.setMaximumWidth(120)
                self.upload_button.setMaximumHeight(25)
                self.upload_button.setIcon(
                    QIcon(self.DMF_HOME + ACTION_IMAGE_PATH + UPLOAD))
                self.upload_button.setToolTip("Upload")
                self.upload_button.setEnabled(False)
                self.upload_button.setMenu(upload_menu)
                self.upload_button.setStyleSheet("background-color: white;")

                self.download_button.setMaximumWidth(120)
                self.download_button.setMaximumHeight(25)
                self.download_button.setIcon(
                    QIcon(self.DMF_HOME + ACTION_IMAGE_PATH + DOWNLOAD))
                self.download_button.setToolTip("Download")
                self.download_button.clicked.connect(self.downloadClicked)
                self.download_button.setStyleSheet("background-color: white;")

                self.lock_button.setMaximumWidth(120)
                self.lock_button.setMaximumHeight(25)
                self.lock_button.setIcon(
                    QIcon(self.DMF_HOME + ACTION_IMAGE_PATH + LOCK))
                self.lock_button.setToolTip("Lock/Unlock")
                self.lock_button.setEnabled(False)
                self.lock_button.clicked.connect(self.lockClicked)
                self.lock_button.setStyleSheet("background-color: white;")

                self.permissions_button.setMaximumWidth(150)
                self.permissions_button.setMaximumHeight(25)
                self.permissions_button.setIcon(
                    QIcon(self.DMF_HOME + ACTION_IMAGE_PATH + PERMISSIONS))
                self.permissions_button.setToolTip(
                    "Manage Permissions (Upcoming feature)")
                self.permissions_button.setVisible(False)
                self.permissions_button.clicked.connect(
                    self.permissionsClicked)
                self.permissions_button.setStyleSheet(
                    "background-color: white;")

                self.refresh_button.setMaximumWidth(25)
                self.refresh_button.setMaximumHeight(25)
                self.refresh_button.setIcon(
                    QIcon(self.DMF_HOME + ACTION_IMAGE_PATH + RELOAD))
                self.refresh_button.clicked.connect(self.tree_ops.refreshTree)

                self.logout_button.clicked.connect(self.logoutClicked)
        else:
            self.save_button.setMaximumWidth(100)
            self.save_button.setMinimumWidth(100)
            self.save_button.clicked.connect(self.saveClicked)
            self.new_folder_button.setMaximumWidth(120)
            self.new_folder_button.setMinimumWidth(120)
            self.new_folder_button.clicked.connect(self.newFolderClicked)

        self.cancel_button.setMaximumWidth(100)
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.clicked.connect(self.cancelClicked)
        # ------------------------------------------------------------------- #

        # ------------------------------------------------------------------- #
        # Detailed info pane related                                          #
        # ------------------------------------------------------------------- #
        self.detailed_info_dialog = DetailedInfoDialog(self)
        self.detailed_info_scroll = QScrollArea()
        palette = self.detailed_info_scroll.palette()
        palette.setColor(self.detailed_info_scroll.backgroundRole(), Qt.white)
        self.detailed_info_scroll.setAutoFillBackground(True)
        self.detailed_info_scroll.setPalette(palette)
        self.detailed_info_scroll.setWidget(self.detailed_info_dialog)
        self.detailed_info_scroll.setWidgetResizable(True)
        # ------------------------------------------------------------------- #

        # ------------------------------------------------------------------- #
        # Add created QT elements and display                                 #
        # ------------------------------------------------------------------- #
        # Splitter and box layout for Alfresco file browser and preview pane
        self.fs_splitter = QSplitter()
        self.fs_splitter.splitterMoved.connect(self.splitterMoved)
        if AlfrescoFileSystem.IS_BROWSER_MODE:
            self.fs_splitter.addWidget(self.tree_view)
            self.fs_splitter.addWidget(self.detailed_info_scroll)
            pos = self.fs_splitter.getRange(1)[1] / 3
            self.fs_splitter.moveSplitter(pos, 1)
        else:
            self.fs_splitter.addWidget(self.tree_view)
            self.fs_splitter.addWidget(self.detailed_info_scroll)
            # Uncommenting the following for now
            # Hide detailed info tab on initialize
            self.fs_splitter.moveSplitter(0, 0)

        # Widget and box layout for bottom row of buttons
        self.fs_ops_hbox = QHBoxLayout()
        self.fs_ops_hbox.setDirection(QBoxLayout.RightToLeft)
        self.fs_ops_hbox.addWidget(self.cancel_button)
        if self.isOpenOrBrowserMode():
            self.fs_ops_hbox.addWidget(self.open_button)
            self.fs_ops_hbox.addItem(self.fs_ops_hbox_spacer)
            if self.verbose:
                self.fs_ops_hbox.addWidget(self.test_button)
        else:
            self.fs_ops_hbox.addWidget(self.save_button)
            self.fs_ops_hbox.addWidget(
                self.new_folder_button, alignment=Qt.AlignLeft)

        # Add layout to main widget layout
        if AlfrescoFileSystem.IS_BROWSER_MODE:
            try:
                self.hbox = QHBoxLayout()
                self.hbox.setDirection(QBoxLayout.LeftToRight)
                self.hbox.addWidget(self.search)
                self.hbox_spacer = QSpacerItem(5, 0)
                self.hbox.addItem(self.hbox_spacer)
                self.hbox.addWidget(self.logout_button)
                self.vbox.addLayout(self.hbox)
                self.hbox2 = QHBoxLayout()
                self.hbox2.addWidget(self.new_folder_button)
                self.hbox2.addWidget(self.edit_button)
                self.hbox2.addWidget(self.upload_button)
                self.hbox2.addWidget(self.download_button)
                self.hbox2.addWidget(self.lock_button)
                self.hbox2.addWidget(self.permissions_button)
                self.hbox2.addItem(self.hbox_spacer2)
                self.hbox2.addWidget(self.refresh_button)
                self.vbox.addLayout(self.hbox2)
                self.vbox.addWidget(self.fs_splitter)
                self.vbox.addLayout(self.file_name_layout)
                if self.verbose:
                    self.vbox.addLayout(self.fs_ops_hbox)
            except Exception, e:
                if self.verbose:
                    print self.__class__.__name__, PRINT_COLON, "Error: ", e
        else:
            self.vbox.addWidget(self.search)
            self.vbox.addWidget(self.fs_splitter)
            self.vbox.addLayout(self.file_name_layout)
            self.vbox.addLayout(self.fs_ops_hbox)
        # ------------------------------------------------------------------- #

        # ------------------------------------------------------------------- #
        # Graph viewer                                                        #
        # ------------------------------------------------------------------- #
        if AlfrescoFileSystem.IS_BROWSER_MODE:
            self.grapher = Grapher(
                self.session,
                self.property_ids,
                self.data_model_vars,
                self.detailed_info_dialog.view,
                self.DMF_HOME)
        # ------------------------------------------------------------------- #

        if self.session is not None:
            self.download_pool = []
            try:
                self.share_adaptor = AlfrescoShareAdaptor()
                self.service_adaptor = AlfrescoServiceAdaptor()
                response, status_code = self.service_adaptor.\
                    getAlfrescoMimetypes(self.connURL)
                if status_code == HTTP_SUCCESS_CODE:
                    mimetypes = json.loads(response)
                    mimetype_data = mimetypes["data"]
                    self.mimetype_dict = dict()
                    for k in mimetype_data.keys():
                        self.mimetype_dict.update(
                            {mimetype_data[k]["description"]: k})
                    self.mimetype_dict = collections.OrderedDict(
                        sorted(self.mimetype_dict.items()))
                else:
                    self.mimetype_dict = None
                self.cookiejar = self.share_adaptor.alfrescoShareLogin(
                    self.connURL, self.user, self.password)
            except Exception, e:
                StatusDialog.displayStatus(str(e))
                self.closeRootDialog()
                raise

            self.data_op = self.entry_point.getDataOperationsImpl()
            self.user_operator = self.entry_point.getUserOperationsImpl()
            self.access_controller = self.entry_point.getAccessControlImpl()
            t_start_millis = int(round(time.time() * 1000))
            self.root_folder = self.data_op.getHighLevelFolder(
                self.session, self.data_folder_map.USER_HOMES)
            if self.verbose:
                t_end_millis = int(round(time.time() * 1000))
                print "t-root-folder: ", (t_end_millis - t_start_millis)
                t_start_millis = int(round(time.time() * 1000))
            self.shared_folder = self.data_op.getHighLevelFolder(
                self.session, self.data_folder_map.SHARED)
            self.sim_folder = self.data_op.getTargetFolderInParentFolder(
                self.session, self.shared_folder.getPath(),
                self.data_folder_map.SIMULATIONS, True)

            if self.verbose:
                t_end_millis = int(round(time.time() * 1000))
                print "t-shared-folder: ", (t_end_millis - t_start_millis)

            self.setupTree()

    def splitterMoved(self, pos, index):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Splitter moved."
        if self.detailed_info_dialog \
                and self.detailed_info_dialog.view \
                and self.detailed_info_dialog.view.view:
            self.detailed_info_dialog.view.view.reload()

    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key_Enter or key == Qt.Key_Return:
            if self.verbose:
                print "Enter detected in AlfrescoFileSystem"
            if self.isOpenOrBrowserMode():
                self.open_button.click()
            else:
                self.tree_view.expand(self.tree_view.currentIndex())
            # Simulate button press in GUI

        elif key == Qt.Key_Escape:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, \
                    "Escape key clicked."
            # self.dereference()
            self.closeRootDialog()

    def closeRootDialog(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Close root dialog."
        if AlfrescoFileSystem.IS_BROWSER_MODE:
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

    def closeEvent(self, event):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Close event invoked."
        if platform.system().startswith(WINDOWS):  # We are on Windows
            PROP_LOC = os.environ[
                REPO_PROPERTIES_WIN_PATH] + WIN_PATH_SEPARATOR
        else:
            PROP_LOC = os.environ[
                REPO_PROPERTIES_UNIX_PATH] + UNIX_PATH_SEPARATOR
        keys = [f for f in os.listdir(PROP_LOC)
                if os.path.isfile(os.path.join(PROP_LOC, f)) and
                f.endswith(self.root.repo_fname + KEYS_EXT)]
        if len(keys) > 0:
            if self.search.text() == '':
                self.tree_ops.exportTree()
        else:
            self.tree_ops.deleteCachedTree()

        for i in xrange(len(self.download_pool)):
            try:
                dialog = self.download_pool[i]
                dialog.close()
                dialog.deleteLater()
            except Exception, e:
                if self.verbose:
                    print self.__class__.__name__, PRINT_COLON, \
                        "No progress dialog detected ---", e
        if AlfrescoFileSystem.IS_BROWSER_MODE:
            self.grapher.cleanup()
        self.closeRootDialog()

    def handleComboBoxChange(self, text):
        if self.verbose:
            if text == '':
                print "Filter is disabled."
            else:
                print "Filter is now", text, '.'
        try:
            model = self.search_res_model
        except:
            model = self.model

        for i in xrange(model.rowCount()):
            self.tree_ops.filterDocuments(
                self.tree_view,
                model.item(i, 0),
                model,
                self.filter_values[self.filters.index(str(text))])

    def openClicked(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, \
                "Open button clicked."
        try:
            if None not in (self.session, self.open_target_id):
                if isinstance(self.open_target_id, str):
                    if AlfrescoFileSystem.IS_OPEN_MODE:
                        doc = self.data_op.cmisObject2Document(
                            self.session.getObject(self.open_target_id))
                        doc_path = doc.getPaths()[0]
                        self.download_pool.append(
                            ProgressDialog(self, doc, False))
                        self.setSession(
                            self.getProgressDialogByteArrayStream(), doc_path)
                        # self.dereference()
                        self.closeRootDialog()
                        if self.verbose:
                            print self.getByteArrayStream()
#                         parents = doc.getProperty(
#                             self.data_model_vars.CCSI_PARENTS).getValue()
#                         if len(parents) > 0:
#                             sim_ids = []  # Keep track of all simulation IDs
#                             sim_byte_array_stream_list = []
#                             for id in parents:
#                                 self.addSimParentsByteStream(
#                                    id, sim_ids, sim_byte_array_stream_list)
#                             self.setSimByteArrayStreamList(sim_byte_array_stream_list)

                    elif AlfrescoFileSystem.IS_BROWSER_MODE:
                        self.grapher.displayGraph(
                            self.session.getObject(self.open_target_id))
                else:
                    self.tree_view.expand(self.tree_view.currentIndex())
                    if AlfrescoFileSystem.IS_BROWSER_MODE:
                        self.detailed_info_dialog.view.hide()
            else:
                StatusDialog.displayStatus("No active session recorded!")

        except Py4JNetworkError, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, \
                    traceback.format_exc()
            StatusDialog.displayStatus(
                e.__class__.__name__ + PRINT_COLON + self.JVM_CONN_MSG)
        except Exception, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, traceback.format_exc()
            StatusDialog.displayStatus(traceback.format_exc())

    def saveClicked(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Save Button Clicked."
        try:
            self.parent_id
            # Select parent element in tree view
            self.tree_view.setCurrentIndex(self.parent.index())
            if self.session is None:
                StatusDialog.displayStatus("No active session recorded")
                return

            parents = self.gateway.jvm.java.util.ArrayList()
            if self.getParents() is not None:
                for p in self.getParents():
                    parents.add(p)
            data = json.loads(self.getByteArrayStream().decode(UTF8))
            folder = self.session.getObject(self.parent_id)
            try:
                type = data["Type"]
            except:
                type = None
                StatusDialog.displayStatus("JSON Data does not have Type")
                # self.dereference()
                self.closeRootDialog()
                return

            if type in (AlfrescoFileSystem.FOQUS_SESSION_TYPE, "Session"):
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

                # contents, id, description = \
                # self.json_parser.getKeyValueFromJobs(data)
                metaData = data.get(CCSI_EMBEDDED_METADATA, None)
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
                isSuccess = False
                status_msg = ''
                isSuccess, display_name, status_msg = self.saveFile(
                    self.getByteArrayStream(),
                    folder,
                    display_name + '.foqus',
                    original_name,
                    description,
                    mimetype,
                    external,
                    confidence,
                    version_requirements,
                    parents)

                if status_msg is not None:
                    if isSuccess:
                        StatusDialog.displayStatus(
                            "Successfully stored 1 file.")
                        if self.verbose:
                            print status_msg
                        self.setSavedMetadata(
                            status_msg.replace(NODE_PREFIX, ""))
                    else:
                        output = []
                        output.extend(
                            ("Report:\n\n", "Error encountered:\n\n",
                             "\t%10s : %s\n" %
                             (display_name, status_msg)))
                        StatusDialog.displayStatus(''.join(output))
                    self.closeRootDialog()

        except Py4JNetworkError, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, traceback.format_exc()
            StatusDialog.displayStatus(
                AlfrescoFileSystem.JVM_CONN_MSG +
                " " +
                traceback.format_exc())
        except Py4JJavaError, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, e
            StatusDialog.displayStatus(traceback.format_exc())
        except AttributeError, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, e
            StatusDialog.displayStatus(traceback.format_exc())
        except Py4JError, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, e
            StatusDialog.displayStatus(
                # CHECK: Unsure if other exceptions fall into this class
                AlfrescoFileSystem.JVM_RESET_CONN_MSG +
                " " +
                traceback.format_exc())
        except Exception, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, e
            StatusDialog.displayStatus(traceback.format_exc())

    def saveFile(
            self,
            byte_array_stream,
            folder,
            display_name,
            original_name,
            description,
            mimetype,
            external,
            confidence,
            version_requirements,
            parents,
            save_file_dialog_title=None,
            suppress_dialog=False,
            result=None,
            isMajorVersion=False,
            overwrite=None,
            display_status=True):

        isSuccess = False
        status_msg = None

        if save_file_dialog_title is None:
            save_file_dialog_title = "Save File Dialog"

        if not suppress_dialog:
            while True:
                display_name, original_name, description, external, \
                    mimetype, version_requirements, confidence, parent_ids, status \
                    = SaveFileDialog.getSaveFileProperties(
                        save_file_dialog_title,
                        display_name,
                        original_name,
                        description,
                        mimetype,
                        external,
                        confidence,
                        version_requirements,
                        parent_ids=None,
                        id=None,
                        parent=self)
                if not status:  # Save canceled
                    return isSuccess, display_name, status_msg
                elif self.hasSaveFileDialogRequired(display_name, mimetype):
                    break

        does_file_exist = self.data_op.doesCmisObjectExist(
            self.session,
            folder.getPath() + UNIX_PATH_SEPARATOR + display_name)
        if not does_file_exist:
            try:
                handler = SaveFileHandlerDialog(
                    self, byte_array_stream, folder, display_name,
                    original_name, description, mimetype, external,
                    version_requirements, confidence, parents, True,
                    display_status=display_status)
                self.uploadWait()
            except:
                raise
            if handler.status.isOperationSuccessful():
                isSuccess = True
                if self.verbose:
                    print "Success in storing file."
                cmis_object = self.session.getObject(
                    handler.status.getDataObjectID())
                status_msg = handler.status.getDataObjectID()
            else:
                isSuccess = False
                status_msg = handler.status.getStatusMessage()
        else:
            if not suppress_dialog:
                result, isMajorVersion, overwrite = \
                    SaveOverwriteFileDialog.getSaveFileProperties(
                        "Upload New File Dialog")
            if result:
                # Alfresco uses UNIX convention
                object_path = str(
                    folder.getPath()) + UNIX_PATH_SEPARATOR + display_name
                original_doc = self.data_op.cmisObject2Document(
                    self.session.getObjectByPath(object_path))
                if overwrite is None:
                    if original_doc.isVersionSeriesCheckedOut():
                        lock_after_update = True
                        lock_owner = self.data_op.\
                            getSinglePropertyAsString(
                                original_doc.getProperty(
                                    self.data_model_vars.CM_LOCKOWNER))
                        if lock_owner == self.user or self.user == SU:
                            pwc = self.session.getObject(original_doc.getId())
                        else:
                            status_msg = (
                                "You do not have permissions to "
                                "overwrite locked file!")
                            return False, display_name, status_msg
                    else:
                        lock_after_update = False
                        checkout_object_id = original_doc.checkOut()
                        pwc = self.session.getObject(checkout_object_id)
                    check_in_comment = self.getUpdateComment()
                    try:
                        handler = SaveFileHandlerDialog(
                            self, byte_array_stream, folder, display_name,
                            original_name, description, mimetype, external,
                            version_requirements, confidence, parents,
                            isMajorVersion, pwc, check_in_comment,
                            display_status=display_status,
                            refresh_at_end=(not lock_after_update))
                        self.uploadWait()
                    except Exception, e:
                        print e
                        raise
                    if handler.status.isOperationSuccessful():
                        isSuccess = True
                        cmis_object = self.session.getObject(
                            handler.status.getDataObjectID())
                        status_msg = handler.status.getDataObjectID()
                        if lock_after_update:
                            checkout_object_id = cmis_object.checkOut()
                            self.tree_ops.refreshTree()
                        if self.verbose:
                            print "Success in storing new version of file."
                    else:
                        isSuccess = False
                        status_msg = handler.status.getStatusMessage()
                else:
                    # This case is disabled, just kept for future reference.
                    # Files are never overwritten in our case.
                    ver_id = original_doc.getProperty(
                        self.property_ids.VERSION_LABEL)
                    if ver_id is not None and \
                       ver_id.getFirstValue() is not None:
                        if float(ver_id.getFirstValue()) == 1.0:
                            self.data_op.deleteDocument(
                                original_doc, True)
                            dialog = StatusDialog(
                                "Uploading file: " + display_name,
                                use_padding=True,
                                parent=self)
                            dialog.show()
                            try:
                                create_doc_status = \
                                    self.data_op.createVersionedDocument(
                                        folder,
                                        display_name,
                                        mimetype,
                                        confidence,
                                        self.java_io.ByteArrayInputStream(
                                            byte_array_stream),
                                        True,
                                        original_name,
                                        description,
                                        parents,
                                        external,
                                        version_requirements)
                            except Exception, e:
                                print e
                                raise
                            finally:
                                dialog.close()
                                dialog.deleteLater()
                            if create_doc_status.isOperationSuccessful():
                                isSuccess = True
                                cmis_object = self.session.getObject(
                                    create_doc_status.getDataObjectID())
                                status_msg = \
                                    create_doc_status.getDataObjectID()
                                if self.verbose:
                                    print (
                                        "Success in overwriting current "
                                        "version of file.")
                        else:
                            subVer = ver_id.getFirstValue().split('.')[1]
                            if int(subVer) != 0:
                                isMajorVersion = False
                            else:
                                isMajorVersion = True
                            check_in_comment = self.getUpdateComment()
                            self.data_op.deleteDocument(
                                original_doc, False)
                            original_doc = self.data_op.cmisObject2Document(
                                self.session.getObjectByPath(object_path))
                            checkout_object_id = original_doc.checkOut()
                            pwc = self.session.getObject(checkout_object_id)
                            dialog = StatusDialog(
                                "Uploading file: " + display_name,
                                use_padding=True,
                                parent=self)
                            dialog.show()
                            try:
                                update_doc_status = \
                                    self.data_op.uploadNewDocumentVersion(
                                        folder,
                                        pwc,
                                        display_name,
                                        mimetype,
                                        confidence,
                                        isMajorVersion,
                                        check_in_comment,
                                        self.java_io.ByteArrayInputStream(
                                            byte_array_stream),
                                        original_name,
                                        description,
                                        parents,
                                        external)
                            except:
                                raise
                            finally:
                                dialog.close()
                                dialog.deleteLater()
                            if update_doc_status.isOperationSuccessful():
                                isSuccess = True
                                status_msg = \
                                    update_doc_status.getDataObjectID()
                                if self.verbose:
                                    print (
                                        "Success in overwriting current "
                                        "version of file.")
        return isSuccess, display_name, status_msg

    def uploadWait(self):
        if self.verbose:
            print "Waiting for upload to complete..."
        self.wait_loop = QEventLoop(self)
        self.wait_loop.exec_()
        self.wait_loop.deleteLater()

    def testClicked(self):
        # This is for generating tests
        self.test_screen_width = QDesktopWidget().screenGeometry().width()
        self.test_screen_height = QDesktopWidget().screenGeometry().height()
        dialog = StatusDialog("Testing commencing...")
        dialog.show()
        time.sleep(2)
        dialog.close()
        try:
            Test(parent=self).runGUITests()
        except Exception, e:
            print self.__class__.__name__, PRINT_COLON, e

    def cancelClicked(self):
        if self.verbose:
            print "Canceled"
        self.session = None
        self.closeRootDialog()

    def logoutClicked(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Logout clicked."
        if platform.system().startswith(WINDOWS):  # We are on Windows
            PROP_LOC = os.environ[
                REPO_PROPERTIES_WIN_PATH] + WIN_PATH_SEPARATOR
        else:
            PROP_LOC = os.environ[
                REPO_PROPERTIES_UNIX_PATH] + UNIX_PATH_SEPARATOR
        keys = [f for f in os.listdir(PROP_LOC)
                if os.path.isfile(os.path.join(PROP_LOC, f)) and
                (f.endswith(self.repo_fname + KEYS_EXT) or
                 f.endswith(self.repo_fname + TMP_KEYS_EXT))]
        if len(keys) > 0:
            try:
                os.remove(PROP_LOC + keys[0])
                if self.verbose:
                    print PROP_LOC + keys[0]
                    print self.__class__.__name__, PRINT_COLON, \
                        "Removed saved credentials."
            except OSError, e:
                print self.__class__.__name__, PRINT_COLON, e

        self.root.EXIT_FLAG = False
        self.closeRootDialog()

    def newFolderClicked(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, \
                "New Folder button clicked."
        self.setEnabled(False)
        try:
            self.parent_id
            # Select parent element in tree view
            self.tree_view.setCurrentIndex(self.parent.index())
            while True:
                folder_name, description, fixed_form, status \
                    = FolderDialog.getNewFolderProperties(self)

                if not status:  # Save canceled
                    self.setEnabled(True)
                    return None
                elif self.hasSaveFolderDialogRequired(folder_name):
                    break

            if status:
                if folder_name == '':
                    StatusDialog.displayStatus("Name not specified!")
                else:
                    parent_folder = self.session.getObject(self.parent_id)
                    create_folder_status = self.data_op.createFolder(
                        parent_folder, folder_name, description, fixed_form)
                    if create_folder_status.isOperationSuccessful():
                        cmis_object = self.session.getObject(
                            create_folder_status.getDataObjectID())
                        self.addDisplayNodeProperties(
                            cmis_object, self.model, self.parent.index())
                        self.collapsed(self.parent.index())
                        self.expanded(self.parent.index())
                        StatusDialog.displayStatus(
                            "Create new folder successful!")
                    else:
                        StatusDialog.displayStatus(
                            create_folder_status.getStatusMessage())
        except Exception, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, e
            StatusDialog.displayStatus(
                "No permission to create new folder here!")
        self.setEnabled(True)

    @Slot(QModelIndex)
    def editClicked(self):
        # Under construction
        if self.verbose:
            print "Edit button clicked"
        index = self.tree_view.currentIndex()
        name = self.model.itemFromIndex(
            index.sibling(index.row(), NAME_COLUMN)).text()
        object_id = self.model.itemFromIndex(
            index.sibling(index.row(), NODE_ID_COLUMN)).text()
        kind = self.model.itemFromIndex(
            index.sibling(index.row(), KIND_COLUMN)).text()
        cmis_object = self.session.getObject(str(object_id))
        self.setEnabled(False)

        if kind == DOCUMENT_DISPLAY_STRING:
            original_name = self.data_op.getSinglePropertyAsString(
                cmis_object.getProperty(self.data_model_vars.CM_TITLE))
            description = self.data_op.getSinglePropertyAsString(
                cmis_object.getProperty(self.data_model_vars.CM_DESCRIPTION))
            mimetype = self.data_op.getSinglePropertyAsString(
                cmis_object.getProperty(self.data_model_vars.CCSI_MIMETYPE))
            external = self.data_op.getSinglePropertyAsString(
                cmis_object.getProperty(self.data_model_vars.CCSI_EXT_LINK))
            confidence = self.data_op.getSinglePropertyAsString(
                cmis_object.getProperty(self.data_model_vars.CCSI_CONFIDENCE))
            version_requirements = self.data_op.getSinglePropertyAsString(
                cmis_object.getProperty(self.data_model_vars.CCSI_VER_REQ))
            parents = cmis_object.getProperty(
                self.data_model_vars.CCSI_PARENTS)
            parent_ids = []
            if parents:
                for v in parents.getValues():
                    parent_ids.append(str(v))

            while True:
                new_display_name, new_original_name, new_description, new_external, \
                    new_mimetype, new_version_requirements, new_confidence, new_parent_ids, status \
                    = SaveFileDialog.getSaveFileProperties(
                        "Edit metadata",
                        name,
                        original_name,
                        description,
                        mimetype,
                        external,
                        confidence,
                        version_requirements,
                        parent_ids=parent_ids,
                        id=object_id,
                        parent=self)

                raw_object_id = object_id.replace(NODE_PREFIX, '')
                if raw_object_id in new_parent_ids:
                    StatusDialog.displayStatus(
                        "Error: Document cannot depend on itself. "
                        "Corresponding dependency will be removed.")
                    new_parent_ids.remove(raw_object_id)

                if not status:  # Save canceled
                    self.setEnabled(True)
                    return None
                elif new_display_name == name \
                        and new_original_name == original_name \
                        and new_description == description \
                        and new_mimetype == mimetype \
                        and new_confidence == confidence \
                        and new_parent_ids == parent_ids \
                        and new_external == external \
                        and new_version_requirements == version_requirements:
                    if self.verbose:
                        print self.__class__.__name__, PRINT_COLON, \
                            "Nothing new for edit."
                    StatusDialog.displayStatus(
                        "No new properties to be added.")
                    self.setEnabled(True)
                    return None
                elif self.hasSaveFileDialogRequired(
                        new_display_name, new_mimetype):
                    break

            parent_ids_array_ls = self.gateway.jvm.java.util.ArrayList()
            if len(new_parent_ids) > 0:
                for p in new_parent_ids:
                    parent_ids_array_ls.add(p)

            doc = self.data_op.cmisObject2Document(cmis_object)
            update_prop_status = self.data_op.updateDocumentProperties(
                doc,
                new_display_name,
                new_original_name,
                new_description,
                new_mimetype,
                new_confidence,
                parent_ids_array_ls,
                new_external,
                new_version_requirements)
        else:
            folder = self.data_op.cmisObject2Folder(cmis_object)
            folder_type = self.data_op.getSinglePropertyAsString(
                cmis_object.getProperty(self.property_ids.OBJECT_TYPE_ID))
            folder_description = folder.getProperty(
                self.data_model_vars.CM_DESCRIPTION).getValue()
            folder_form = folder.getProperty(
                self.data_model_vars.CCSI_FIXED_FORM).getValue()

            if folder_type != (
                    self.data_model_vars.F_PREFIX +
                    self.data_model_vars.CCSI_FOLDER):
                StatusDialog.displayStatus(
                    "Selected folder is a system generated "
                    "folder and is not editable.")
                self.setEnabled(True)
                return
            while True:
                folder_name, description, fixed_form, status \
                    = FolderDialog.setFolderProperties(
                        folder.getName(), folder_description, folder_form)

                if not status:  # Save canceled
                    self.setEnabled(True)
                    return None
                elif folder_name == folder.getName() \
                        and description == folder_description \
                        and fixed_form == folder_form:
                    if self.verbose:
                        print self.__class__.__name__, PRINT_COLON, \
                            "Nothing new for edit."
                    StatusDialog.displayStatus(
                        "No new properties to be added.")
                    self.setEnabled(True)
                    return None
                elif self.hasSaveFolderDialogRequired(folder_name):
                    break

            update_prop_status = self.data_op.updateFolderProperties(
                folder, folder_name, description, fixed_form)

        if update_prop_status.isOperationSuccessful():
            StatusDialog.displayStatus("Edit successful!")
            if kind == DOCUMENT_DISPLAY_STRING:
                id, ver = self.common.splitDMFID(
                    update_prop_status.getDataObjectID())
            else:
                id = update_prop_status.getDataObjectID()
            self.editNodeProperties(index, id)
        else:
            StatusDialog.displayStatus(
                "Edit failed: " + update_prop_status.getStatusMessage())
        self.setEnabled(True)

    @Slot(QModelIndex)
    def permissionsClicked(self):
        if self.verbose:
            print "Manage permissions clicked"
        index = self.tree_view.currentIndex()
        object_id = self.model.itemFromIndex(
            index.sibling(index.row(), NODE_ID_COLUMN)).text()
        operation_context = self.gateway.jvm.org.apache.chemistry.\
            opencmis.client.runtime.OperationContextImpl()
        operation_context.setIncludeAcls(True)
        cmis_object = self.session.getObject(str(object_id), operation_context)
        parent_folder = self.session.getObject(
            self.parent_id, operation_context)
        result, new_roles, delete = PermissionsDialog.displayPermissions(
            cmis_object.getAcl().getAces(),
            parent_folder.getAcl().getAces(),
            self)

        if result:
            for username in delete:
                if self.verbose:
                    print "Deleting permissions for:", username
                self.access_controller.deletePermissions(
                    self.session, username, object_id)
            for username in new_roles.keys():
                role_name = new_roles.get(username)
                role = None
                for r in self.role.values():
                    if role_name in r.name():
                        role = r
                if role:
                    if self.verbose:
                        print "Adding permissions for:", username
                    self.access_controller.addPermissions(
                        self.session, username, object_id, role)

    @Slot(QModelIndex)
    def lockClicked(self):
        if self.verbose:
            print "Lock button clicked"
        index = self.tree_view.currentIndex()
        name_item = self.model.itemFromIndex(
            index.sibling(index.row(), NAME_COLUMN))
        name = name_item.text()
        object_id = self.model.itemFromIndex(
            index.sibling(index.row(), NODE_ID_COLUMN)).text()
        cmis_object = self.session.getObject(object_id)
        lock_owner = self.data_op.getSinglePropertyAsString(
            cmis_object.getProperty(self.data_model_vars.CM_LOCKOWNER))
        if lock_owner is None:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, "Locking", name
            # Do locking and checkout
            try:
                self.data_op.cmisObject2Document(cmis_object).checkOut()
                name_item.setIcon(self.locked_document_icon)
                self.lock_button.setIcon(QIcon(
                    self.DMF_HOME + ACTION_IMAGE_PATH + UNLOCK))
                self.lock_button.setText("Unlock")
                self.edit_button.setEnabled(False)
            except Exception, e:
                StatusDialog.displayStatus(
                    "Lock file error: "
                    "You no longer have permissions to edit this file!")
                self.tree_ops.refreshTree()
                if self.verbose:
                    print self.__class__.__name__, PRINT_COLON, e
        else:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, \
                    "Unlocking", name
            try:
                self.data_op.cmisObject2Document(
                    cmis_object).cancelCheckOut()
                name_item.setIcon(self.document_icon)
                self.lock_button.setIcon(
                    QIcon(self.DMF_HOME + ACTION_IMAGE_PATH + LOCK))
                self.lock_button.setText("Lock")
                self.updateOnSelect(
                    self.tree_view.selectionModel().selection())
            except Exception, e:
                StatusDialog.displayStatus(str(e))
                if self.verbose:
                    print self.__class__.__name__, PRINT_COLON, e

    @Slot(QModelIndex)
    def downloadClicked(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON,\
                "Download button clicked"
        index = self.tree_view.currentIndex()
        name = self.model.itemFromIndex(
            index.sibling(index.row(), NAME_COLUMN)).text()
        object_id = self.model.itemFromIndex(
            index.sibling(index.row(), NODE_ID_COLUMN)).text()
        kind = self.model.itemFromIndex(
            index.sibling(index.row(), KIND_COLUMN)).text()
        if kind == DOCUMENT_DISPLAY_STRING:
            # raw_id, ver = Common().splitDMFID(object_id)
            cmis_object = self.session.getObject(object_id)
            if self.verbose:
                t_start_millis = int(round(time.time() * 1000))
            ver_list = self.data_op.getVersionHistoryLabels(
                self.session, cmis_object)
            if self.verbose:
                t_end_millis = int(round(time.time() * 1000))
                print "t-get-versions: ", (t_end_millis - t_start_millis)

            selected_ver, result = SelectVersionDialog.getVersion(
                ver_list, self)
            if result:
                try:
                    cmis_object = self.session.getObject(object_id)
                    saveFileDialog = QFileDialog(self)
                    fname, filter = saveFileDialog.getSaveFileName(
                        self, "Save file", name)
                    if fname != "":
                        doc = self.data_op.cmisObject2Document(
                            self.session.getObject(object_id))
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
                            pass
                        self.download_pool.append(
                            ProgressDialog(self, doc, fname))
                except Exception, e:
                    if self.verbose:
                        print e.__class__.__name__, PRINT_COLON, e
                    StatusDialog.displayStatus(str(e))
        else:
            saveFileDialog = QFileDialog(self)
            saveFileDialog.setDefaultSuffix(".zip")
            fname, filter = saveFileDialog.getSaveFileName(
                self, "Save folder", name, "Archive (*.zip)")

            if fname != '':
                try:
                    node_ids = self.gateway.jvm.java.util.ArrayList()
                    node_ids.add(object_id)
                    dialog = StatusDialog(
                        "Setting up zip archive. "
                        "Download will start shortly...",
                        use_padding=True, parent=self)
                    dialog.show()
                    # Download as zip
                    zip_file = self.data_op.downloadZipFolder(
                        self.session, node_ids)
                    input_stream = self.java_io.FileInputStream(zip_file)
                    try:
                        os.remove(fname)
                    except OSError:
                        pass
                    dialog.close()
                    dialog.deleteLater()
                    self.download_pool.append(ProgressDialog(
                        self, input_stream, fname, zip_file.length()))
                    if zip_file:
                        zip_file.delete()
                except Exception, e:
                    if self.verbose:
                        print e.__class__.__name__, PRINT_COLON, e
                    StatusDialog.displayStatus(str(e))

    def downloadFolderByPath(self, folder_path, target_path):
        node_ids = self.gateway.jvm.java.util.ArrayList()
        node_ids.add(self.session.getObjectByPath(folder_path).getId())
        zip = self.data_op.downloadZipFolder(
            self.session, node_ids)
        input = self.java_io.FileInputStream(zip)
        self.download_pool.append(ProgressDialog(
            self, input, target_path, zip.length(), auto_close=True))
        if zip:
            zip.delete()

    @Slot(QModelIndex)
    def uploadFolderClicked(self):
        if self.verbose:
            print "Upload folder clicked"
        # Select parent element in tree view
        self.tree_view.setCurrentIndex(self.parent.index())
        self.setEnabled(False)
        uploadFolderDialog = QFileDialog(self)
        uploadFolderDialog.setFileMode(QFileDialog.Directory)
        fname = QFileDialog.getExistingDirectory(self, "Upload Directory")
        if fname == '':
            self.setEnabled(True)
            return
        try:
            parent_folder = self.session.getObject(self.parent_id)
            res = self.uploadAllFolderObjects(parent_folder, fname, '', True)
        except Exception, e:
            res = False
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, e
        self.setEnabled(True)
        if not res:
            StatusDialog.displayStatus(
                "Folder upload incomplete or unsuccessful.")
        else:
            StatusDialog.displayStatus("Folder upload completed!")
        self.tree_ops.refreshTree()

    @Slot(QModelIndex)
    def uploadFileClicked(self):
        if self.verbose:
            print "Upload file clicked"
        nsuccesses = 0
        nerrors = 0
        err_statuses = {}
        try:
            self.parent_id
            # Select parent element of tree view
            self.tree_view.setCurrentIndex(self.parent.index())
            if self.session is None:
                StatusDialog.displayStatus("No active session recorded")
                return
        except Exception, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, e
            StatusDialog.displayStatus(str(e))
        self.setEnabled(False)
        uploadFileDialog = QFileDialog(self)
        fnames, filter = uploadFileDialog.getOpenFileNames(
            self, "Upload File(s)")
        for file_path in fnames:
            try:
                folder = self.session.getObject(self.parent_id)
                original_name = os.path.basename(file_path)
                with open(str(file_path), "rb") as f:
                    try:
                        if self.verbose:
                            t_start_millis = int(round(time.time() * 1000))
                        isSuccess, display_name, status_msg \
                            = self.saveFile(
                                bytearray(f.read()),
                                folder,
                                original_name,
                                original_name,
                                description='',
                                mimetype='',
                                external='',
                                confidence='',
                                version_requirements='',
                                parents=None)
                        if self.verbose:
                            t_end_millis = int(round(time.time() * 1000))
                            print "t-uploadfile: ", (
                                t_end_millis - t_start_millis)
                        if status_msg is not None:
                            if isSuccess:
                                nsuccesses += 1
                            else:
                                nerrors += 1
                                err_statuses[display_name] = status_msg
                    except Exception, e:
                        nerrors += 1
                        err_statuses[original_name] = e
                        if self.verbose:
                            print e.__class_.__name__, PRINT_COLON, \
                                "Error: ", e
            except Exception, e:
                if self.verbose:
                    print e.__class__.__name__, PRINT_COLON, e
                StatusDialog.displayStatus(str(e))

        if nerrors > 0:
            output = []
            output.extend(
                ("Report:\n\n",
                 "Successfully stored "
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
        self.setEnabled(True)

    @Slot(QModelIndex)
    def expanded(self, index):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Expanded"
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

    @Slot(QModelIndex)
    def collapsed(self, index):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Collapse"
        self.model.itemFromIndex(index.sibling(
            index.row(), NAME_COLUMN)).setIcon(self.folder_closed_icon)
        self.tree_view.resizeColumnToContents(NAME_COLUMN)
        if self.tree_view.columnWidth(NAME_COLUMN) < DEFAULT_NAME_COLUMN_WIDTH:
            self.tree_view.setColumnWidth(
                NAME_COLUMN, DEFAULT_NAME_COLUMN_WIDTH)

    @Slot(QModelIndex)
    def onTreeViewClicked(self, index):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Clicked"
        main_row_index = index.sibling(index.row(), NAME_COLUMN)
        data_object = index.model().itemFromIndex(main_row_index)
        kind = index.model().itemFromIndex(
            index.sibling(index.row(), KIND_COLUMN)).text()
        if kind == DOCUMENT_DISPLAY_STRING and data_object.isEnabled():
            self.target_file_name.setText(data_object.text())
            self.open_target_id = str(index.model().itemFromIndex(
                index.sibling(index.row(), NODE_ID_COLUMN)).text())
        else:
            self.target_file_name.setText('')
            self.open_target_id = index
            if self.last_clicked_index == main_row_index:
                if self.tree_view.isExpanded(main_row_index):
                    self.tree_view.collapse(index)
                else:
                    self.tree_view.expand(index)
        self.last_clicked_index = main_row_index

    def onSearchClicked(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Search text entered"

        if self.search.text() == '':
            if AlfrescoFileSystem.IS_BROWSER_MODE:
                self.refresh_button.setEnabled(True)
            try:
                self.search_res_model.clear()
                self.search_res_model.deleteLater()

                self.tree_ops.setupTreeViewWithModel(
                    self.tree_view, self.default_model)
                self.model = self.default_model
                self.tree_view_selected = self.tree_view.selectionModel()
                self.tree_view_selected.selectionChanged.connect(
                    self.handleSelectionChanged)
                self.tree_view.sortByColumn(0, Qt.AscendingOrder)
                # Select first element of tree view
                self.tree_view.setCurrentIndex(
                    self.model.index(0, 0))
                if not self.detailed_info_dialog.isVisible():
                    self.detailed_info_dialog.show()
                dialog = StatusDialog(
                    "Refreshing...", use_padding=True, parent=self)
                dialog.show()
                self.tree_ops.importTree(self.tree_view)
                dialog.close()
                dialog.deleteLater()
            except:
                # Search never initiated
                pass
        else:
            try:
                for c in self.cookiejar:
                    if c.is_expired(int(time.time())):
                        self.cookiejar = self.share_adaptor.alfrescoShareLogin(
                            self.connURL, self.user, self.password)
                        break
                # Only gets first 50 results
                res, status_code = \
                    self.share_adaptor.alfrescoShareFullTextSearch(
                        self.connURL, self.search.text(), self.cookiejar)
                if AlfrescoFileSystem.IS_BROWSER_MODE:
                    self.refresh_button.setEnabled(False)
                jres = json.loads(res)
                jres_len = jres["totalRecords"]

                if self.verbose:
                    print "Number of records: ", jres_len
                    print "Total number of records: ", \
                        jres["totalRecordsUpper"]
                try:
                    self.search_res_model
                    self.search_res_model.clear()
                    self.search_res_model.setColumnCount(NUM_COLUMN)
                    self.tree_ops.setModelHeaders(self.search_res_model)
                    self.tree_ops.setupTreeViewWithModel(
                        self.tree_view, self.search_res_model)
                except:
                    self.tree_ops.exportTree()
                    self.search_res_model = QStandardItemModel(self)
                    self.search_res_model.setColumnCount(NUM_COLUMN)
                    self.tree_ops.setModelHeaders(self.search_res_model)
                    self.tree_ops.setupTreeViewWithModel(
                        self.tree_view, self.search_res_model)
                    self.tree_view_selected = self.tree_view.selectionModel()
                    self.tree_view_selected.selectionChanged.connect(
                        self.handleSelectionChanged)
                self.model = self.search_res_model
                if jres_len > 0:
                    self.populateSearchResultModel(jres)
                if self.search_res_model.rowCount() == 0:
                    self.detailed_info_dialog.hide()
                else:
                    self.detailed_info_dialog.show()

                self.tree_view.sortByColumn(0, Qt.AscendingOrder)
                # self.tree_view.clearSelection()
                # Select first element of tree view
                self.tree_view.setCurrentIndex(
                    self.search_res_model.index(0, 0))
            except Py4JError, e:
                if self.verbose:
                    print e.__class__.__name__, PRINT_COLON, e
                StatusDialog.displayStatus(AlfrescoFileSystem.REPO_CONN_MSG)
            except Exception, e:
                if self.verbose:
                    print e.__class__.__name__, PRINT_COLON, e
                if status_code == 500:
                    StatusDialog.displayStatus(
                        AlfrescoFileSystem.SHARE_FTS_MSG)
                else:
                    StatusDialog.displayStatus(str(e))

    def createChildNode(self, index):
        try:
            # This is a dummy test to check if connection is alive
            id = index.model().itemFromIndex(index.sibling(
                index.row(), NODE_ID_COLUMN)).text()
            self.session.getObject(str(id))
            if index.column() == 0:
                if index.model().itemFromIndex(index).rowCount() <= 0:
                    self.addChildNode(index)
                    for i in xrange(
                            index.model().itemFromIndex(index).rowCount()):
                        self.addChildNode(index.child(i, 0))
                else:
                    for i in xrange(
                            index.model().itemFromIndex(index).rowCount()):
                        if index.model().itemFromIndex(
                                index.child(i, 0)).rowCount() <= 0:
                            self.addChildNode(index.child(i, 0))
            self.tree_view.sortByColumn(0, Qt.AscendingOrder)
        except Py4JNetworkError, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, traceback.format_exc()
            StatusDialog.displayStatus(
                AlfrescoFileSystem.JVM_CONN_MSG +
                " " + traceback.format_exc())

    def addChildNode(self, index):
        node_id = index.model().itemFromIndex(
            index.sibling(index.row(), NODE_ID_COLUMN)).text()
        if node_id is not None:
            try:
                # Supposedly, setting the operation_context
                # will improve response time
                operation_context = self.gateway.jvm.org.apache.chemistry.\
                    opencmis.client.runtime.OperationContextImpl()
                operation_context.setCacheEnabled(False)
                operation_context.setIncludePolicies(False)
                operation_context.setIncludePathSegments(False)
                operation_context.setIncludeAllowableActions(False)
                operation_context.setLoadSecondaryTypeProperties(False)
                relationship = self.gateway.jvm.org.apache.chemistry.\
                    opencmis.commons.enums.IncludeRelationships
                operation_context.setIncludeRelationships(relationship.NONE)
                ###############################################################
                if FOLDER_DISPLAY_STRING == index.model().itemFromIndex(
                        index.sibling(index.row(), KIND_COLUMN)).text():
                    if self.verbose:
                        t_start_millis = int(round(time.time() * 1000))
                    cmis_object = self.session.getObject(
                        str(node_id), operation_context)
                    if self.verbose:
                        t_end_millis = int(round(time.time() * 1000))
                        print "t-get-object: ", (t_end_millis - t_start_millis)
                    children = cmis_object.getChildren()
                    children_iterator = children.iterator()

                    while children_iterator.hasNext():
                        current_child = children_iterator.next()
                        self.addDisplayNodeProperties(
                            current_child, index.model(), index)

            except Exception, e:
                if self.verbose:
                    print e.__class__.__name__, PRINT_COLON, e

    def addDisplayNodeProperties(self, cmis_object, model, index=None):
        id = cmis_object.getId()
        if id.endswith(PWC):
            return
        if SEMI_COLON in id:
            id, ver = self.common.splitDMFID(id)
        name = cmis_object.getName()
        size = "--"
        type = str(cmis_object.getType().getBaseTypeId())
        last_modified_date_formatted = self.formatTimestampInMillis(
            cmis_object.getLastModificationDate().getTimeInMillis())

        if type == self.CMIS_DOCUMENT:
            size = self.common.convertBytesToReadable(
                cmis_object.getContentStreamLength(), True)

        name = QStandardItem(name)

        if type == self.CMIS_DOCUMENT:
            type = DOCUMENT_DISPLAY_STRING
            lock_owner = self.data_op.getSinglePropertyAsString(
                cmis_object.getProperty(self.data_model_vars.CM_LOCKOWNER))
            if lock_owner is None:
                name.setIcon(self.document_icon)
            elif lock_owner == self.user:
                name.setIcon(self.locked_document_icon)
            else:
                name.setIcon(self.lock_icon)
        elif type == self.CMIS_FOLDER:
            type = FOLDER_DISPLAY_STRING
            name.setIcon(self.folder_closed_icon)
        else:
            print self.__class__.__name__, PRINT_COLON, "Unrecognized type", \
                PRINT_COLON, type

        size = QStandardItem(size)
        size.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        type = QStandardItem(type)
        date = QStandardItem(last_modified_date_formatted)
        id = QStandardItem(id)
        new_row = [name, size, type, date, id]
        filter = self.filter_values[self.file_name_filter.currentIndex()]

        for r in new_row:
            r.setEditable(False)
            if str(type.text()) == DOCUMENT_DISPLAY_STRING \
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

    def editNodeProperties(self, index, id):
        operation_context = self.gateway.jvm.org.apache.chemistry.\
            opencmis.client.runtime.OperationContextImpl()
        operation_context.setIncludeAcls(True)
        cmis_object = self.session.getObject(str(id), operation_context)
        last_modified_date_formatted = self.formatTimestampInMillis(
            cmis_object.getLastModificationDate().getTimeInMillis())
        kind = index.model().itemFromIndex(
            index.sibling(index.row(), KIND_COLUMN)).text()

        self.model.itemFromIndex(index.sibling(
            index.row(), NAME_COLUMN)).setText(cmis_object.getName())
        self.model.itemFromIndex(
            index.sibling(index.row(), DATE_MOD_COLUMN)).setText(
            last_modified_date_formatted)
        self.updateDetailedInfo(cmis_object, kind)

    def changeDetailedInfoVersion(self, ver):
        index = self.tree_view.selectionModel().selection().indexes()[0]
        object_id = index.model().itemFromIndex(index.sibling(
            index.row(), NODE_ID_COLUMN)).text()
        kind = index.model().itemFromIndex(index.sibling(
            index.row(), KIND_COLUMN)).text()
        object_id += ';'+ver
        operation_context = self.gateway.jvm.org.apache.chemistry.\
            opencmis.client.runtime.OperationContextImpl()
        operation_context.setIncludeAcls(True)
        cmis_object = self.session.getObject(str(object_id), operation_context)
        self.updateDetailedInfo(cmis_object, kind, False)

    def updateDetailedInfo(self, cmis_object, kind, update_ver_list=True):
        name = cmis_object.getName()
        object_id = cmis_object.getId()
        last_modified_date_formatted = self.formatTimestampInMillis(
            cmis_object.getLastModificationDate().getTimeInMillis())

        # Force update of detailed info pane.
        original_name = self.data_op.getSinglePropertyAsString(
            cmis_object.getProperty(self.data_model_vars.CM_TITLE))
        description = self.data_op.getSinglePropertyAsString(
            cmis_object.getProperty(self.data_model_vars.CM_DESCRIPTION))
        mimetype = self.data_op.getSinglePropertyAsString(
            cmis_object.getProperty(self.data_model_vars.CCSI_MIMETYPE))
        confidence = self.data_op.getSinglePropertyAsString(
            cmis_object.getProperty(self.data_model_vars.CCSI_CONFIDENCE))
        external = self.data_op.getSinglePropertyAsString(
            cmis_object.getProperty(self.data_model_vars.CCSI_EXT_LINK))
        version_requirements = self.data_op.getSinglePropertyAsString(
            cmis_object.getProperty(self.data_model_vars.CCSI_VER_REQ))
        creation_date = cmis_object.getProperty(
            self.property_ids.CREATION_DATE).getFirstValue()

#         if ver_id is not None and ver_id.getFirstValue() is not None:
#             new_name = []
#             new_name.append(str(name))
#             new_name.append(" ver.")
#             new_name.append(str(ver_id.getFirstValue()))
#             name = ''.join(new_name)

        creation_date_millis = creation_date.getTimeInMillis()
        creation_date = self.formatTimestampInMillis(creation_date_millis)
        creator = cmis_object.getCreatedBy()

        if kind == DOCUMENT_DISPLAY_STRING:
            ver_list = self.data_op.getVersionHistoryLabels(
                self.session, cmis_object)
            object_id, _ = self.common.splitDMFID(object_id)
            try:
                preview_url = (
                    self.connURL +
                    FILE_PREVIEW_HEADER +
                    object_id.replace('://', '/') +
                    FILE_PREVIEW_TAIL)
                preview_content, status_code = \
                    self.share_adaptor.getAlfrescoSharePreview(
                        preview_url, self.cookiejar)
            except Exception, e:
                if self.verbose:
                    print self.__class__.__name__, PRINT_COLON, e
                preview_content = None
            try:
                if AlfrescoFileSystem.IS_BROWSER_MODE:
                    self.grapher.displayGraph(cmis_object)
            except Exception, e:
                if self.verbose:
                    print self.__class__.__name__, PRINT_COLON, e
        else:
            ver_list = None
            preview_url = self.connURL + FOLDER_PREVIEW
            preview_content, status_code = \
                self.share_adaptor.getAlfrescoSharePreview(
                    preview_url, self.cookiejar)

        self.detailed_info_dialog.setData(
            name,
            original_name,
            description,
            mimetype,
            external,
            version_requirements,
            confidence,
            creator,
            creation_date,
            last_modified_date_formatted,
            ver_list,
            preview_content,
            update_ver_list)

    def handleSelectionChanged(self, selected, deselected):
        try:
            self.last_clicked_index = None
            if self.verbose:
                init_start_millis = int(round(time.time() * 1000))
            self.updateOnSelect(selected)
            if self.verbose:
                init_end_millis = int(round(time.time() * 1000))
                print "t-update-on-select:", \
                    (init_end_millis-init_start_millis)
        except Py4JNetworkError, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, traceback.format_exc()
            StatusDialog.displayStatus(
                AlfrescoFileSystem.JVM_CONN_MSG +
                " " + traceback.format_exc())

    def updateOnSelect(self, selected):
        if self.session is None:
            return
        try:
            index = selected.indexes()[0]
            object = index.model().itemFromIndex(
                index.sibling(index.row(), NAME_COLUMN))
            object_name = object.text()
            object_id = index.model().itemFromIndex(
                index.sibling(index.row(), NODE_ID_COLUMN)).text()
            kind = index.model().itemFromIndex(
                index.sibling(index.row(), KIND_COLUMN)).text()
            if self.verbose and index:
                print self.__class__.__name__, PRINT_COLON, \
                    ("Node %s selected." % object_id)

            operation_context = self.gateway.jvm.org.apache.chemistry.\
                opencmis.client.runtime.OperationContextImpl()
            operation_context.setIncludeAcls(True)
            cmis_object = self.session.getObject(
                str(object_id), operation_context)
            name = cmis_object.getName()
            original_name = self.data_op.getSinglePropertyAsString(
                cmis_object.getProperty(self.data_model_vars.CM_TITLE))
            description = self.data_op.getSinglePropertyAsString(
                cmis_object.getProperty(self.data_model_vars.CM_DESCRIPTION))
            mimetype = self.data_op.getSinglePropertyAsString(
                cmis_object.getProperty(self.data_model_vars.CCSI_MIMETYPE))
            external = self.data_op.getSinglePropertyAsString(
                cmis_object.getProperty(self.data_model_vars.CCSI_EXT_LINK))
            version_requirements = self.data_op.getSinglePropertyAsString(
                cmis_object.getProperty(self.data_model_vars.CCSI_VER_REQ))
            confidence = self.data_op.getSinglePropertyAsString(
                cmis_object.getProperty(self.data_model_vars.CCSI_CONFIDENCE))
            lock_owner = self.data_op.getSinglePropertyAsString(
                cmis_object.getProperty(self.data_model_vars.CM_LOCKOWNER))

            creation_date = cmis_object.getProperty(
                self.property_ids.CREATION_DATE).getFirstValue()
            last_modified_date = cmis_object.getLastModificationDate()
#            ver_id = cmis_object.getProperty(self.property_ids.VERSION_LABEL)
            creator = cmis_object.getCreatedBy()

            ver_list = None
            user_groups = []
            can_edit = False
            can_add = False
            can_manage = False

            if self.user == SU:
                can_edit = True
                can_add = True
                can_manage = True
            elif self.user == creator:
                can_edit = True
                can_add = True
                can_manage = True
            else:
                for g in self.user_operator.getUser(
                        self.conn, self.user).get("groups"):
                    user_groups.append(
                        str(g.get("itemName").toString()).replace('"', ''))

                for a in cmis_object.getAcl().getAces():
                    a_id = a.getPrincipalId()
                    if a_id == self.user or (a_id.startswith("GROUP") and (
                            a_id in user_groups or a_id == "GROUP_EVERYONE")):
                        permissions = a.getPermissions()
                        if self.verbose:
                            print self.__class__.__name__, PRINT_COLON, \
                                a_id, PRINT_COLON, permissions
                        for permission in permissions:
                            p = str(permission)
                            if p.endswith(self.role.Coordinator.name()) or \
                                    p.endswith(self.role.Collaborator.name()) or \
                                    p.endswith(self.role.Editor.name()) or \
                                    p == self.basic_permissions.WRITE or \
                                    p == self.basic_permissions.ALL:
                                can_edit = True
                            if p.endswith(self.role.Coordinator.name()) or \
                                    p.endswith(self.role.Collaborator.name()) or \
                                    p.endswith(self.role.Contributor.name()) or \
                                    p == self.basic_permissions.WRITE or \
                                    p == self.basic_permissions.ALL:
                                can_add = True
                            if p.endswith(self.role.Coordinator.name()) or \
                                    p == self.basic_permissions.ALL:
                                can_manage = True
                    else:
                        continue
            if kind == DOCUMENT_DISPLAY_STRING:
                try:
                    if AlfrescoFileSystem.IS_BROWSER_MODE:
                        self.grapher.displayGraph(cmis_object)
                except Exception, e:
                    if self.verbose:
                        print "Error with displaying provenance graph: ", \
                            str(e)
                try:
                    parent = index.model().itemFromIndex(
                        index.sibling(index.row(), NODE_ID_COLUMN)).parent()
                    parent_id = parent.model().itemFromIndex(
                        parent.index().sibling(
                            parent.row(), NODE_ID_COLUMN)).text()
                    if parent is not None:
                        self.parent_id = str(parent_id)
                        self.parent = parent
                        parent_object = self.session.getObject(
                            str(self.parent_id), operation_context)

                except Exception, e:
                    if self.verbose:
                        print "Search case, no parent in tree view"
                    # Search case, no parent
                    path = self.data_op.cmisObject2Document(
                        cmis_object).getPaths().get(0)
                    parent_path = UNIX_PATH_SEPARATOR.join(
                        path.split(UNIX_PATH_SEPARATOR)[:-1])
                    parent_object = self.session.getObjectByPath(
                        parent_path, operation_context)
                    self.parent_id = None

                fixed_form = self.common.convertJavaBool2PyBool(
                    self.data_op.getSinglePropertyAsString(
                        parent_object.getProperty(
                            self.data_model_vars.CCSI_FIXED_FORM)))
                can_add_to_parent = False
                for a in parent_object.getAcl().getAces():
                    a_id = a.getPrincipalId()
                    if (a_id == self.user or
                        (a_id.startswith("GROUP") and
                         (a_id in user_groups or a_id == "GROUP_EVERYONE"))):
                        permissions = a.getPermissions()
                        if self.verbose:
                            print self.__class__.__name__, PRINT_COLON, \
                                a_id, PRINT_COLON, permissions
                        for permission in permissions:
                            p = str(permission)
                            if p.endswith(self.role.Coordinator.name()) or \
                                    p.endswith(self.role.Collaborator.name()) or \
                                    p.endswith(self.role.Contributor.name()) or \
                                    p == self.basic_permissions.WRITE or \
                                    p == self.basic_permissions.ALL:
                                can_add_to_parent = True
                    else:
                        continue

                ver_list = self.data_op.getVersionHistoryLabels(
                    self.session, cmis_object)
                self.target_file_name.setText(object_name)
                self.open_target_id = str(object_id)
                if AlfrescoFileSystem.IS_BROWSER_MODE:
                    if fixed_form:
                        self.new_folder_button.setEnabled(False)
                        self.edit_button.setEnabled(False)
                        self.upload_button.setEnabled(False)
                        self.lock_button.setEnabled(False)
                    else:
                        if self.parent_id is not None:
                            self.upload_button.setEnabled(True)
                        else:
                            # This should happen only during search case.
                            if self.verbose:
                                print self.__class__.__name__, PRINT_COLON, \
                                    "Check here..."
                            self.upload_button.setEnabled(False)
                        if can_add_to_parent:
                            self.upload_folder.setEnabled(True)
                            self.new_folder_button.setEnabled(True)
                        else:
                            self.upload_folder.setEnabled(False)
                            self.new_folder_button.setEnabled(False)
                        if lock_owner is None:
                            self.lock_button.setIcon(QIcon(
                                self.DMF_HOME + ACTION_IMAGE_PATH + LOCK))
                            self.lock_button.setText("Lock")
                            if can_edit:
                                self.edit_button.setEnabled(True)
                                self.lock_button.setEnabled(True)
                                self.upload_file.setEnabled(True)
                            else:
                                self.edit_button.setEnabled(False)
                                self.lock_button.setEnabled(False)
                                self.upload_file.setEnabled(False)
                        elif lock_owner == self.user or self.user == SU:
                            self.edit_button.setEnabled(False)
                            self.lock_button.setEnabled(True)
                            self.lock_button.setIcon(QIcon(
                                self.DMF_HOME + ACTION_IMAGE_PATH + UNLOCK))
                            self.lock_button.setText("Unlock")
                            self.upload_file.setEnabled(True)
                        else:
                            self.edit_button.setEnabled(False)
                            self.lock_button.setEnabled(False)
                            self.lock_button.setIcon(QIcon(
                                self.DMF_HOME + ACTION_IMAGE_PATH + LOCK))
                            self.lock_button.setText("Lock")
                            self.upload_file.setEnabled(False)
                        if not self.upload_file.isEnabled() and \
                           not self.upload_folder.isEnabled():
                            self.upload_button.setEnabled(False)
                        else:
                            self.upload_button.setEnabled(True)
                        if can_manage:
                            # Disable for now
                            self.permissions_button.setVisible(False)
                        else:
                            self.permissions_button.setVisible(False)
                elif (not AlfrescoFileSystem.IS_OPEN_MODE and
                      not AlfrescoFileSystem.IS_BROWSER_MODE):
                    if fixed_form:
                        self.save_button.setEnabled(False)
                    else:
                        self.save_button.setEnabled(True)
                try:
                    preview_url = (
                        self.connURL +
                        FILE_PREVIEW_HEADER +
                        object_id.replace('://', '/') +
                        FILE_PREVIEW_TAIL)
                    preview_content, status_code = self.share_adaptor.\
                        getAlfrescoSharePreview(preview_url, self.cookiejar)
                except Exception, e:
                    if self.verbose:
                        print e.__class__.__name__, PRINT_COLON, e
                    preview_content = None
            else:
                self.parent_id = str(object_id)
                self.parent = object
                self.target_file_name.setText('')
                self.open_target_id = index
                parent_object = self.session.getObject(str(self.parent_id))
                fixed_form = self.common.convertJavaBool2PyBool(
                    self.data_op.getSinglePropertyAsString(
                        parent_object.getProperty(
                            self.data_model_vars.CCSI_FIXED_FORM)))
                if AlfrescoFileSystem.IS_BROWSER_MODE:
                    try:
                        self.detailed_info_dialog.view.hide()
                    except:
                        pass
                    folder_type = self.data_op.getSinglePropertyAsString(
                        cmis_object.getProperty(
                            self.property_ids.OBJECT_TYPE_ID))
                    if can_edit and not fixed_form:
                        if folder_type != (
                                self.data_model_vars.F_PREFIX +
                                self.data_model_vars.CCSI_FOLDER):
                            self.edit_button.setEnabled(False)
                        else:
                            self.edit_button.setEnabled(True)
                    else:
                        self.edit_button.setEnabled(False)
                    if can_add and not fixed_form:
                        self.new_folder_button.setEnabled(True)
                        self.upload_button.setEnabled(True)
                        self.upload_folder.setEnabled(True)
                        self.upload_file.setEnabled(True)
                    else:
                        self.new_folder_button.setEnabled(False)
                        self.upload_button.setEnabled(False)
                    if can_manage and not fixed_form:
                        # Disable for now
                        self.permissions_button.setVisible(False)
                    else:
                        self.permissions_button.setVisible(False)
                    self.lock_button.setEnabled(False)
                    self.lock_button.setIcon(QIcon(
                        self.DMF_HOME + ACTION_IMAGE_PATH + LOCK))
                    self.lock_button.setText("Lock")
                elif (not AlfrescoFileSystem.IS_OPEN_MODE and
                      not AlfrescoFileSystem.IS_BROWSER_MODE):
                    if can_add and not fixed_form:
                        self.new_folder_button.setEnabled(True)
                        self.save_button.setEnabled(True)
                    else:
                        self.new_folder_button.setEnabled(False)
                        self.save_button.setEnabled(False)

                preview_url = self.connURL + FOLDER_PREVIEW
                preview_content, status_code = \
                    self.share_adaptor.getAlfrescoSharePreview(
                        preview_url, self.cookiejar)

#             if ver_id is not None and ver_id.getFirstValue() is not None:
#                 new_name = []
#                 new_name.append(str(name))
#                 new_name.append(" ver.")
#                 new_name.append(str(ver_id.getFirstValue()))
#                 name = ''.join(new_name)

            creation_date_millis = creation_date.getTimeInMillis()
            creation_date = self.formatTimestampInMillis(creation_date_millis)
            last_modified_date = self.formatTimestampInMillis(
                last_modified_date.getTimeInMillis())
            creator = cmis_object.getCreatedBy()

            self.detailed_info_dialog.setData(
                name,
                original_name,
                description,
                mimetype,
                external,
                version_requirements,
                confidence,
                creator,
                creation_date,
                last_modified_date,
                ver_list,
                preview_content)
        except Py4JNetworkError, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, traceback.format_exc()
            StatusDialog.displayStatus(
                AlfrescoFileSystem.JVM_CONN_MSG +
                " " + traceback.format_exc())
        except Py4JJavaError, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, traceback.format_exc()
            StatusDialog.displayStatus(AlfrescoFileSystem.JVM_CONN_MSG)
        except IndexError, e:
            pass

    def formatTimestampInMillis(self, ms):
        return str(datetime.fromtimestamp(ms / 1000.0).strftime(
            "%m/%d/%Y %I:%M %p").lstrip("0").replace(" 0", " "))

    def populateSearchResultModel(self, jres):
        results = jres["items"]
        for i in xrange(0, jres["totalRecords"]):
            try:
                path = str(results[i]["path"])
                shared_folder_path = (
                    UNIX_PATH_SEPARATOR +
                    self.data_folder_map.COMPANY_HOME +
                    UNIX_PATH_SEPARATOR +
                    self.data_folder_map.SHARED)
                user_folder_path = (
                    UNIX_PATH_SEPARATOR +
                    self.data_folder_map.COMPANY_HOME +
                    UNIX_PATH_SEPARATOR +
                    self.data_folder_map.USER_HOMES +
                    UNIX_PATH_SEPARATOR +
                    self.user)

                if self.user == SU:
                    is_not_restricted = True
                else:
                    is_not_restricted = path.startswith(user_folder_path)
                if path.startswith(shared_folder_path) or is_not_restricted:
                    cmis_object = self.session.getObject(str(
                        results[i]["nodeRef"]))
                    ver_id = cmis_object.getProperty(
                        self.property_ids.VERSION_LABEL)
                    if ver_id is not None and \
                       ver_id.getFirstValue() is not None:
                        if PWC in str(ver_id.getFirstValue()):
                            continue
                    type = str(cmis_object.getType().getBaseTypeId())
                    self.addDisplayNodeProperties(
                        cmis_object, self.search_res_model)

                    if type == self.CMIS_FOLDER:
                        cmis_object = self.data_op.cmisObject2Folder(
                            cmis_object)
                        for i in xrange(self.search_res_model.rowCount()):
                            cur_index = self.search_res_model.item(
                                i, 0).index()
                            self.addChildNode(cur_index)
            except KeyError, e:
                pass
            except Exception, e:
                if self.verbose:
                    print e.__class__.__name__, PRINT_COLON, e

    # Takes in list, returns a list of True, False, or None (error case)
    def doesFileExist(self, dmf_id):
        if self.verbose:
            print "Does file exist..."
        id, ver = self.common.splitDMFID(dmf_id)
        if id is None and ver is None:
            return None
        try:
            self.session.getObject(id)
            return True
        except:
            return False

    # Returns DMF ID for a simulation name
    def getSimIDByName(self, sim_name):
        sim_folder_path = self.sim_folder.getPath()
        sim_path = (sim_folder_path + UNIX_PATH_SEPARATOR +
                    sim_name)
        try:
            raw_sim_id = self.session.getObjectByPath(sim_path).getId()
            sim_id = raw_sim_id.replace(NODE_PREFIX, '')
            return sim_id
        except:
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
            "Uploading simulation files...")

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

        # TODO: Create folders
        # Simulation exists
        sim_title = '_'.join(sim_title.split(' '))
        sim_path = self.sim_folder.getPath() + UNIX_PATH_SEPARATOR + sim_title
        if sim_id:
            does_folder_exist = self.data_op.doesCmisObjectExist(
                self.session, sim_path)
            if not does_folder_exist:
                create_folder_status = self.data_op.createFolder(
                    self.sim_folder, sim_title, description, False)
                if not create_folder_status:
                    err_msg = ("Unable to create subdirectory "
                               "at path: {p}.".format(p=self.sim_folder))
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
            display_name = sim_name
        else:
            if sinter_config_bytestream is None:
                err_msg = ("Initial upload of simulation must "
                           "include sinter configuration file.")
                if self.verbose:
                    print err_msg
                StatusDialog.displayStatus(str(err_msg))
                return (None, ) * 3
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
                        save_file_dialog_title, (sim_name, True), sim_name,
                        description, mimetype, None, confidence,
                        version_reqs, parent=self)
                if not status:  # Save canceled
                    return (None, ) * 3
                elif self.hasSaveFileDialogRequired(display_name, mimetype):
                    break

            does_folder_exist = self.data_op.doesCmisObjectExist(
                self.session, sim_path)
            if not does_folder_exist:
                create_folder_status = self.data_op.createFolder(
                    self.sim_folder, sim_title, description, False)
                if not create_folder_status:
                    err_msg = ("Unable to create subdirectory "
                               "at path: {p}.".format(p=self.sim_folder))
                    StatusDialog.displayStatus(err_msg)
                    if self.verbose:
                        print err_msg

            tmp_s_stats, tmp_f_stats, r_id_list, r_name_list = \
                self.createResources(
                    resource_bytestream_list, resource_name_list, description,
                    mimetype, external, confidence, version_reqs, sim_path)
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
        scf_path = sim_path + UNIX_PATH_SEPARATOR + sinter_config_name
        does_file_exist = self.data_op.doesCmisObjectExist(
            self.session, scf_path)
        if does_file_exist:
            tmp_s_stats, tmp_f_stats, scf_id = self.updateSinterConf(
                scf_bytestream, sinter_config_name, mimetype,
                confidence, version_reqs, [sim_id], sim_path)
        else:
            tmp_s_stats, tmp_f_stats, scf_id = self.createSinterConf(
                scf_bytestream, sinter_config_name, description, mimetype,
                external, confidence, version_reqs, [sim_id], sim_path)
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

    def createSubDir(self, file_path, target_path):
        path_split = file_path.split(os.sep)
        if len(path_split[:-1]) == 0:
            return
        for d in path_split[:-1]:
            parent_folder = self.session.getObjectByPath(target_path)
            target_path = target_path + UNIX_PATH_SEPARATOR + d
            does_folder_exist = self.data_op.doesCmisObjectExist(
                self.session, target_path)
            if does_folder_exist:
                if self.verbose:
                    print "Folder exists for path {p}.".format(p=target_path)
                continue
            create_folder_status = self.data_op.createFolder(
                parent_folder, d, '', False)
            if not create_folder_status:
                if self.verbose:
                    print "Unable to create subdirectory at path: {p}.".format(
                        p=target_path)
                    break
            else:
                if self.verbose:
                    print "Success creating subdir with path: {p}".format(
                        p=target_path)

    def createSimulation(self, sim_bytestream, sim_name, description, mimetype,
                         external, confidence, version_reqs, resource_id_list,
                         target_folder_path):
        logging.getLogger("foqus." + __name__).debug(
            "Upload simulation...")
        success_status = []
        failure_status = []
        sim_dependencies = self.gateway.jvm.java.util.ArrayList()
        for resource_id in resource_id_list:
            sim_dependencies.add(resource_id)
        sim_path = target_folder_path + UNIX_PATH_SEPARATOR + sim_name
        self.createSubDir(sim_name, target_folder_path)
        sim_parent_folder = self.session.getObjectByPath(target_folder_path)
        does_file_exist = self.data_op.doesCmisObjectExist(
            self.session, sim_path)
        if does_file_exist:
            return self.updateSimulation(
                sim_bytestream, sim_name, mimetype, confidence, version_reqs,
                resource_id_list, target_folder_path, check_in_comment=None)
        else:
            isSuccess, display_name, status_msg = self.saveFile(
                sim_bytestream, sim_parent_folder, sim_name, sim_name,
                description, mimetype, external, confidence,
                version_reqs, sim_dependencies, suppress_dialog=True)
            if isSuccess:
                sim_id = status_msg.replace(NODE_PREFIX, "")
                success_status.append(
                    ("\tSimulation: ", str(sim_name), "\n"))
                if self.verbose:
                    print status_msg
            else:
                sim_id = None
                failure_status.append("\t%10s : %s\n" % (sim_name, status_msg))
            return success_status, failure_status, sim_id

    def createResources(self, resource_bytestream_list, resource_name_list,
                        description, mimetype, external,
                        confidence, version_reqs, target_folder_path):
        logging.getLogger("foqus." + __name__).debug(
            "Upload resources...")
        success_status = []
        failure_status = []
        r_id_list = []
        r_name_list = []
        for r, r_name in zip(resource_bytestream_list, resource_name_list):
            r_path = target_folder_path + UNIX_PATH_SEPARATOR + r_name
            self.createSubDir(r_name, target_folder_path)
            does_file_exist = self.data_op.doesCmisObjectExist(
                self.session, r_path)
            if does_file_exist:
                tmp_s_stats, tmp_f_stats, tmp_r_id_list, tmp_r_name_list = \
                    self.updateResources(
                        [r], [r_name], mimetype, None, confidence,
                        version_reqs, target_folder_path)
                SharedOps().aggregateStatuses(success_status, failure_status,
                                              tmp_s_stats, tmp_f_stats)
                r_id_list += tmp_r_id_list
                r_name_list += tmp_r_name_list
                continue
            else:
                r_dependencies = self.gateway.jvm.java.util.ArrayList()
                # Hide popup dialog (handled at top)
                r_name_comp = r_name.split(UNIX_PATH_SEPARATOR)
                r_parent_path = target_folder_path + UNIX_PATH_SEPARATOR + \
                    UNIX_PATH_SEPARATOR.join(r_name_comp[:-1])
                r_disp_name = r_name_comp[-1]
                r_parent_folder = self.session.getObjectByPath(r_parent_path)
                isSuccess, display_name, status_msg = self.saveFile(
                    r, r_parent_folder, r_disp_name, r_disp_name, description,
                    mimetype, external, confidence, version_reqs,
                    r_dependencies, suppress_dialog=True)
                if isSuccess:
                    r_id = status_msg.replace(NODE_PREFIX, "")
                    r_id_list.append(r_id)
                    r_name_list.append(r_name)
                    success_status.append(
                        ("\tResource: ", str(r_name), "\n"))
                    if self.verbose:
                        print status_msg
                else:
                    failure_status.append(
                        "\t%10s : %s\n" % (r_name, status_msg))
        return success_status, failure_status, r_id_list, r_name_list

    def createSinterConf(self, scf_bytestream, scf_name, description, mimetype,
                         external, confidence, version_reqs, sim_id_list,
                         target_folder_path):
        logging.getLogger("foqus." + __name__).debug(
            "Upload sinter config...")
        success_status = []
        failure_status = []
        scf_dependencies = self.gateway.jvm.java.util.ArrayList()
        for sim_id in sim_id_list:
            scf_dependencies.add(sim_id)
        scf_path = target_folder_path + UNIX_PATH_SEPARATOR + scf_name
        self.createSubDir(scf_name, target_folder_path)
        scf_parent_folder = self.session.getObjectByPath(
            target_folder_path)
        does_file_exist = self.data_op.doesCmisObjectExist(
            self.session, scf_path)
        if does_file_exist:
            return self.updateSinterConf(
                scf_bytestream, scf_name, description, mimetype, confidence,
                version_reqs, sim_id_list, check_in_comment=None)
        else:
            isSuccess, display_name, status_msg = self.saveFile(
                scf_bytestream, scf_parent_folder, scf_name, scf_name,
                description, mimetype, external, confidence, version_reqs,
                scf_dependencies, None, True)
            if isSuccess:
                scf_id = status_msg.replace(NODE_PREFIX, "")
                success_status.append(
                    ("\tSinter config: ", str(scf_name), "\n"))
                if self.verbose:
                    print status_msg
            else:
                scf_id = None
                failure_status.append("\t%10s : %s\n" % (scf_name, status_msg))
            return success_status, failure_status, scf_id

    def updateResources(self, resource_bytestream_list, resource_name_list,
                        mimetype, external, confidence, version_reqs,
                        target_folder_path, check_in_comment=None):
        success_status = []
        failure_status = []
        r_id_list = []
        r_name_list = []
        dm_vars = self.data_model_vars
        logging.getLogger("foqus." + __name__).debug(
            "Updating resources...")
        for r, r_name in zip(resource_bytestream_list, resource_name_list):
            r_path = target_folder_path + UNIX_PATH_SEPARATOR + r_name
            self.createSubDir(r_name, target_folder_path)
            new_r_checksum = self.data_op.getChecksum(
                self.java_io.ByteArrayInputStream(r))
            r_cmis_object = self.session.getObjectByPath(r_path)
            old_r_checksum = self.data_op.getSinglePropertyAsString(
                r_cmis_object.getProperty(dm_vars.CCSI_CHECKSUM))
            if old_r_checksum == new_r_checksum:
                r_id = r_cmis_object.getId().replace(NODE_PREFIX, '')
                r_id_list.append(r_id)
                r_name_list.append(r_name)
                continue
            result, is_major_ver, _ = \
                SaveOverwriteFileDialog.getSaveFileProperties(
                    "Upload New Resource Dialog")
            if not result:
                r_id = r_cmis_object.getId()
                r_id_list.append(r_id)
                r_name_list.append(r_name)
                continue
            r_doc = self.data_op.cmisObject2Document(
                r_cmis_object)
            checkout_object_id = r_doc.checkOut()
            pwc = self.session.getObject(checkout_object_id)
            description = self.data_op.getSinglePropertyAsString(
                r_cmis_object.getProperty(dm_vars.CM_DESCRIPTION))
            external = self.data_op.getSinglePropertyAsString(
                r_cmis_object.getProperty(dm_vars.CCSI_EXT_LINK))
            try:
                handler = SaveFileHandlerDialog(
                    self, r, self.sim_folder, r_name, r_name, description,
                    mimetype, external, version_reqs, confidence,
                    self.gateway.jvm.java.util.ArrayList(),
                    True, pwc, check_in_comment)
                self.uploadWait()
            except:
                raise
            if handler.status.isOperationSuccessful():
                r_id = handler.status.getDataObjectID()
                r_id = r_id.replace(NODE_PREFIX, '')
                r_id_list.append(r_id)
                r_name_list.append(r_name)
                success_status.append(("\tResource: ", str(r_name), "\n"))
            else:
                err_msg = handler.status.getStatusMessage()
                failure_status.append("\t%10s : %s\n" % (r_name, err_msg))
                if self.verbose:
                    print err_msg
        return success_status, failure_status, r_id_list, r_name_list

    def updateSimulation(self, sim_bytestream, sim_name, mimetype, confidence,
                         version_reqs, resource_id_list, target_folder_path,
                         check_in_comment=None, sim_id=None):
        success_status = []
        failure_status = []
        dm_vars = self.data_model_vars
        logging.getLogger("foqus." + __name__).debug(
            "Updating simulation...")
        sim_path = target_folder_path + UNIX_PATH_SEPARATOR + sim_name
        self.createSubDir(sim_name, target_folder_path)
        new_sim_checksum = self.data_op.getChecksum(
            self.java_io.ByteArrayInputStream(sim_bytestream))
        sim_cmis_object = self.session.getObjectByPath(sim_path)
        old_sim_checksum = self.data_op.getSinglePropertyAsString(
            sim_cmis_object.getProperty(dm_vars.CCSI_CHECKSUM))
        if old_sim_checksum == new_sim_checksum:
            sim_id = sim_cmis_object.getId()
            sim_id = sim_id.replace(NODE_PREFIX, "")
            return success_status, failure_status, sim_id
        else:
            result, is_major_ver, _ = \
                SaveOverwriteFileDialog.getSaveFileProperties(
                    "Upload New Simulation Dialog")
            if not result:
                return success_status, failure_status, sim_id
            sim_doc = self.data_op.cmisObject2Document(
                sim_cmis_object)
            checkout_object_id = sim_doc.checkOut()
            pwc = self.session.getObject(checkout_object_id)
            description = self.data_op.getSinglePropertyAsString(
                sim_cmis_object.getProperty(dm_vars.CM_DESCRIPTION))
            external = self.data_op.getSinglePropertyAsString(
                sim_cmis_object.getProperty(dm_vars.CCSI_EXT_LINK))
            sim_dependencies = self.gateway.jvm.java.util.ArrayList()
            for r_id in resource_id_list:
                sim_dependencies.add(r_id)
            try:
                handler = SaveFileHandlerDialog(
                    self, sim_bytestream, self.sim_folder, sim_name, sim_name,
                    description, mimetype, external, version_reqs, confidence,
                    sim_dependencies, is_major_ver, pwc, check_in_comment)
                self.uploadWait()
            except:
                raise
            if handler.status.isOperationSuccessful():
                sim_id = handler.status.getDataObjectID()
                sim_id = sim_id.replace(NODE_PREFIX, '')
                success_status.append(("\tSimulation: ", str(sim_name), "\n"))
            else:
                sim_id = None
                err_msg = handler.status.getStatusMessage()
                failure_status.append("\t%10s : %s\n" % (sim_name, err_msg))
                if self.verbose:
                    print err_msg
        return success_status, failure_status, sim_id

    def updateSinterConf(self, scf_bytestream, scf_name, mimetype, confidence,
                         version_reqs, sim_id_list, target_folder_path,
                         check_in_comment=None):
        success_status = []
        failure_status = []
        dm_vars = self.data_model_vars
        logging.getLogger("foqus." + __name__).debug(
            "Updating sinter config...")
        scf_path = target_folder_path + UNIX_PATH_SEPARATOR + scf_name
        self.createSubDir(scf_name, target_folder_path)
        new_scf_checksum = self.data_op.getChecksum(
            self.java_io.ByteArrayInputStream(scf_bytestream))
        scf_cmis_object = self.session.getObjectByPath(scf_path)
        old_scf_checksum = self.data_op.getSinglePropertyAsString(
            scf_cmis_object.getProperty(dm_vars.CCSI_CHECKSUM))
        if old_scf_checksum == new_scf_checksum:
            scf_id = scf_cmis_object.getId()
            scf_id = scf_id.replace(NODE_PREFIX, "")
            return success_status, failure_status, scf_id
        else:
            result, is_major_ver, _ = \
                SaveOverwriteFileDialog.getSaveFileProperties(
                    "Upload New Sinter Configuration Dialog")
            if not result:
                return success_status, failure_status, scf_id
            scf_doc = self.data_op.cmisObject2Document(
                scf_cmis_object)
            checkout_object_id = scf_doc.checkOut()
            pwc = self.session.getObject(checkout_object_id)
            description = self.data_op.getSinglePropertyAsString(
                scf_cmis_object.getProperty(dm_vars.CM_DESCRIPTION))
            external = self.data_op.getSinglePropertyAsString(
                scf_cmis_object.getProperty(dm_vars.CCSI_EXT_LINK))
            scf_dependencies = self.gateway.jvm.java.util.ArrayList()
            for sim_id in sim_id_list:
                scf_dependencies.add(sim_id)
            try:
                handler = SaveFileHandlerDialog(
                    self, scf_bytestream, self.sim_folder, scf_name, scf_name,
                    description, mimetype, external, version_reqs, confidence,
                    scf_dependencies, is_major_ver, pwc, check_in_comment)
                self.uploadWait()
            except:
                raise
            if handler.status.isOperationSuccessful():
                scf_id = handler.status.getDataObjectID()
                scf_id = scf_id.replace(NODE_PREFIX, '')
                success_status.append(
                    ("\tSinter Config: ", str(scf_name), "\n"))
            else:
                scf_id = None
                err_msg = handler.status.getStatusMessage()
                failure_status.append("\t%10s : %s\n" % (scf_name, err_msg))
                if self.verbose:
                    print err_msg
        return success_status, failure_status, scf_id

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

    def setReturnDocument(self, document):
        self.return_document = document

    def getReturnDocument(self):
        try:
            return self.return_document
        except:
            return None

    def setSession(self, session_byte_array_stream, session_path):
        self.session_byte_array_stream = session_byte_array_stream
        self.session_path = DMFSERV_PATH_PREFIX + session_path

    def setByteArrayStream(self, byte_array_stream):
        self.byte_array_stream = byte_array_stream

    def setSimByteArrayStreamList(self, sim_byte_array_stream_list):
        self.sim_byte_array_stream_list = sim_byte_array_stream_list

    def setProgressDialogByteArrayStream(self, byte_array_stream):
        self.pd_byte_array_stream = byte_array_stream

    def getProgressDialogByteArrayStream(self):
        try:
            return self.pd_byte_array_stream
        except:
            return None

    def getSimByteArrayStreamList(self):
        if self.verbose:
            print "Getting sim byte array stream list..."
        try:
            return self.sim_byte_array_stream_list
        except:
            return None

    def getByteArrayStream(self):
        if self.verbose:
            print "Getting byte array stream..."
        try:
            return self.byte_array_stream
        except:
            return None

    def getSession(self):
        if self.verbose:
            print "Getting session byte array stream and path..."
        try:
            return (self.session_byte_array_stream, self.session_path)
        except:
            return (None, ) * 2

    def getByteArrayStreamById(self, dmf_id):
        if self.verbose:
            print "Get byte array stream by id..."
        try:
            if id is None:
                StatusDialog.displayStatus("ID argument is None.")
                return None
            if self.session is None:
                StatusDialog.displayStatus("No active session recorded")
                return None
            if not isinstance(dmf_id, str):
                StatusDialog.displayStatus("ID is not of str instance")
                return None
            doc = self.data_op.cmisObject2Document(
                self.session.getObject(dmf_id))
            self.download_pool.append(ProgressDialog(self, doc, False))
            return self.getProgressDialogByteArrayStream()
        except Py4JNetworkError, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, traceback.format_exc()
            StatusDialog.displayStatus(
                e.__class__.__name__ + PRINT_COLON + self.JVM_CONN_MSG)
        except Exception, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, traceback.format_exc()
            StatusDialog.displayStatus(str(e))

    def getSimFileByteArrayStreamByName(self, name):
        if self.verbose:
            print "Getting sim file byte array stream by name..."
        try:
            if name is None:
                StatusDialog.displayStatus("Name argument is None.")
                return None
            if self.session is None:
                StatusDialog.displayStatus("No active session recorded")
                return None
            if not isinstance(name, str):
                StatusDialog.displayStatus("Name is not of str instance")
                return None

            doc = self.data_op.cmisObject2Document(
                self.session.getObjectByPath(
                    self.sim_folder.getPath() + UNIX_PATH_SEPARATOR + name))
            self.download_pool.append(ProgressDialog(self, doc, False))
            return self.getProgressDialogByteArrayStream()
        except Py4JNetworkError, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, traceback.format_exc()
            StatusDialog.displayStatus(
                e.__class__.__name__ + PRINT_COLON + self.JVM_CONN_MSG)
        except Exception, e:
            if self.verbose:
                print e.__class__.__name__, PRINT_COLON, traceback.format_exc()
            StatusDialog.displayStatus(str(e))

    def setParents(self, parents):
        # Hack for demo
        new_parents = []
        for parent in parents:
            if parent.startswith(FIND_SINTER_INDICATOR):
                try:
                    sim = self.data_op.cmisObject2Document(
                        self.session.getObject(
                            NODE_PREFIX + parent.replace(
                                FIND_SINTER_INDICATOR, '')))
                    sinter_config_path = sim.getPaths().get(
                        0) + SINTER_CONFIG_EXT
                    sinter_config_id = self.session.getObjectByPath(
                        sinter_config_path).getId().replace(NODE_PREFIX, '')
                    new_parents.append(sinter_config_id)
                except Exception, e:
                    if self.verbose:
                        print e.__class__.__name__, PRINT_COLON, \
                            traceback.format_exc()
            else:
                new_parents.append(parent)
        self.parents = new_parents

    def getParents(self):
        try:
            return self.parents
        except:
            return None

    def setUpdateComment(self, update_comment):
        self.update_comment = update_comment

    def getUpdateComment(self):
        try:
            return self.update_comment
        except:
            return None

    def setSavedMetadata(self, id):
        self.return_dmf_id = id

    def getSavedMetadata(self):
        try:
            return self.return_dmf_id
        except:
            return None

    def addSimParentsByteStream(self, id, sim_ids, sim_byte_array_stream_list):
        if self.verbose:
            print "Adding sim parents byte stream..."
        if id not in sim_ids:
            doc = self.data_op.cmisObject2Document(
                self.session.getObject(NODE_PREFIX + id))
            parents = doc.getProperty(
                self.data_model_vars.CCSI_PARENTS).getValues()
            self.download_pool.append(ProgressDialog(self, doc, False))
            sim_byte_array_stream_list.append(
                self.getProgressDialogByteArrayStream())
            sim_ids.append(id)
            if len(parents) > 0:
                for p_id in parents:
                    self.addSimParentsByteStream(
                        p_id,
                        sim_ids,
                        sim_byte_array_stream_list)

    def isLatestVersion(self, dmf_id):
        if self.verbose:
            print "Checking if dmf_id is latest version..."
        id, ver = self.common.splitDMFID(dmf_id)
        if id is None and ver is None:
            return None
        latest_dmf_id = self.session.getObject(id).getId()
        latest_id, latest_ver = self.common.splitDMFID(latest_dmf_id)
        if latest_id is None and latest_ver is None:
            return None
        if self.common.isVersion1OlderThanVersion2(ver, latest_ver):
            return False
        else:
            return True

    def isOpenOrBrowserMode(self):
        return (AlfrescoFileSystem.IS_OPEN_MODE or
                AlfrescoFileSystem.IS_BROWSER_MODE)

    def uploadAllFolderObjects(
            self,
            parent_folder,
            path,
            description,
            initial=False,
            fixed_form=False):
        res_list = []
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
                        folder_name +
                        " ...",
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
            create_folder_status = self.data_op.createFolder(
                parent_folder, folder_name, description, fixed_form)
            if create_folder_status.isOperationSuccessful():
                cmis_object = self.session.getObject(
                    create_folder_status.getDataObjectID())
                parent_folder = cmis_object
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
                    folder_name + " folder")

            for f in os.listdir(path):
                f_path = path + UNIX_PATH_SEPARATOR + f
                if os.path.isdir(f_path):
                    res_list.append(self.uploadAllFolderObjects(
                        parent_folder, f_path, description))
                else:
                    with open(str(f_path), "rb") as opened_file:
                        try:
                            original_name = os.path.basename(f_path)
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
                            isSuccess, display_name, status_msg \
                                = self.saveFile(
                                    bytearray(opened_file.read()),
                                    parent_folder,
                                    original_name,
                                    original_name,
                                    description,
                                    'Unknown',
                                    '',
                                    'experimental',
                                    '',
                                    None,
                                    suppress_dialog=True,
                                    display_status=False)
                            dialog.close()
                            dialog.deleteLater()
                            res_list.append(isSuccess)
                        except Exception, e:
                            if self.verbose:
                                print self.__class__.__name__, PRINT_COLON, e
                            StatusDialog.displayStatus(str(e))
                            res_list.append(False)
        except Exception, e:
            try:
                dialog.close()
                dialog.deleteLater()
            except:
                pass
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, e
            res_list.append(False)
            raise
        return all(res_list)

    def getSimulationList(self, path=None):
        sim_names = []
        sim_ids = []
        sc_ids = []

        if not path:
            path = self.sim_folder.getPath()
            print path
        cmis_obj = self.session.getObjectByPath(path)
        obj_type = str(cmis_obj.getType().getBaseTypeId())
        if obj_type == self.CMIS_DOCUMENT:
            self.appendSimAttr(sim_names, sim_ids, sc_ids,
                               *self.getSimAttr(path))
        elif obj_type == self.CMIS_FOLDER:
            children = cmis_obj.getChildren()
            children_iterator = children.iterator()

            while children_iterator.hasNext():
                child = children_iterator.next()
                child_name = child.getName()
                child_path = cmis_obj.getPath() + UNIX_PATH_SEPARATOR + \
                    child_name
                child_obj_type = str(child.getType().getBaseTypeId())
                if child_obj_type == self.CMIS_FOLDER:
                    tmp_names, tmp_ids, tmp_sc_ids = self.getSimulationList(
                        child_path)
                    sim_ids += tmp_ids
                    sim_names += tmp_names
                    sc_ids += tmp_sc_ids
                else:
                    self.appendSimAttr(sim_names, sim_ids, sc_ids,
                                       *self.getSimAttr(child_path))
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
            doc = self.data_op.cmisObject2Document(
                self.session.getObjectByPath(f_path))
            self.download_pool.append(
                ProgressDialog(self, doc, False))
            contents = self.getProgressDialogByteArrayStream()
            f_json = json.loads(contents.decode(UTF8))
            if f_json[SC_TYPE] == SC_TYPENAME:
                sc_ccsi_meta = f_json.get(CCSI_EMBEDDED_METADATA)
                sim_id = sc_ccsi_meta.get(CCSI_SIM_ID_KEY)
                sim_name = f_json.get(SC_TITLE)
                sc_id = doc.getId().replace(NODE_PREFIX, '')
        return sim_name, sim_id, sc_id

    # ------------------------------------------------------------------- #
    # Tree operations                                                     #
    # ------------------------------------------------------------------- #
    def setupTree(self):
        if AlfrescoFileSystem.IS_BROWSER_MODE:
            self.root.updateSplash("Setting up user filesystem structure...")
        if self.verbose:
            t_start_millis = int(round(time.time() * 1000))
        self.last_clicked_index = None
        # Only display user space and shared space contents
        self.addDisplayNodeProperties(self.root_folder, self.model)
        self.addDisplayNodeProperties(self.shared_folder, self.model)
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
