import os
import json
import shutil
import platform
from PySide.QtGui import QWidget
from PySide.QtGui import QGridLayout
from PySide.QtGui import QPushButton
from PySide.QtGui import QLabel
from PySide.QtGui import QVBoxLayout
from PySide.QtGui import QDesktopWidget
from PySide.QtCore import Qt
from PySide.QtCore import QUrl
from PySide.QtWebKit import QWebView

from dmf_lib.common.methods import Common
from dmf_lib.common.common import D3
from dmf_lib.common.common import GRAPH_DIR
from dmf_lib.common.common import GRAPH_FORCE_PATH
from dmf_lib.common.common import GRAPH_JSON_PATH
from dmf_lib.common.common import GRAPH_REINGOLD_PATH
from dmf_lib.common.common import GRAPH_TEMPLATES
from dmf_lib.common.common import FILE_PREFIX
from dmf_lib.common.common import NODE_PREFIX
from dmf_lib.common.common import WINDOWS
from dmf_lib.common.common import PRINT_COLON
from dmf_lib.common.common import REPO_PROPERTIES_UNIX_PATH
from dmf_lib.common.common import REPO_PROPERTIES_WIN_PATH
from dmf_lib.common.common import UNIX_PATH_SEPARATOR
from dmf_lib.common.common import WIN_PATH_SEPARATOR

from dmf_lib.gui.path import ASPEN_PLUS
from dmf_lib.gui.path import CCSI
from dmf_lib.gui.path import EXCEL_FILE
from dmf_lib.gui.path import FILETYPE_IMAGE_PATH
from dmf_lib.gui.path import TEXT_FILE

from dmf_lib.gui.icon_groups import aspen_mimetypes
from dmf_lib.gui.icon_groups import excel_mimetypes
from dmf_lib.gui.icon_groups import ccsi_mimetypes
from dmf_lib.dialogs.status_dialog import StatusDialog
from dmf_lib.dialogs.graph_popup_dialog import GraphPopupDialog
from dmf_lib.graph.dmf_webpage import DMFQWebPage

from dmf_lib.git.meta_dict import DISPLAY_NAME
from dmf_lib.git.meta_dict import MIMETYPE
from dmf_lib.git.meta_dict import MAJOR_VERSION
from dmf_lib.git.meta_dict import MINOR_VERSION
from dmf_lib.git.meta_dict import DEPENDENCIES

try:
    import networkx as nx
    from networkx.readwrite import json_graph
except:
    print 'No networkx module found'
try:
    import matplotlib
    matplotlib.use('Qt4Agg')
    matplotlib.rcParams['backend.qt4'] = 'PySide'
    # import matplotlib.pyplot as plt
except Exception, e:
    print e  # For debugging
    print 'No matplotlib module found'


class GraphViewer(QWidget):

    def __init__(self, parent=None):
        super(GraphViewer, self).__init__(parent)

        self.root = parent
        self.verbose = parent.verbose
        self.verbose = True
        self.DMF_HOME = parent.DMF_HOME
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.grid_layout = QGridLayout()

        self.g_pop = GraphPopupDialog(self)
        self.undock_button = QPushButton("Undock dependency graph", self)
        self.undock_button.setMaximumWidth(180)
        self.undock_button.clicked.connect(self.undock)

        self.view_label = QLabel(self)
        self.view_label.setText("Dependency Graph")
        self.view_label.setStyleSheet("color: #767676;")
        self.view = QWebView(self)

        # Setting page to customized QWebPage to interface with D3
        self.view.setPage(DMFQWebPage(self))

        self.setContentsMargins(0, 0, 0, 0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.view.page().mainFrame().setScrollBarPolicy(
            Qt.Horizontal, Qt.ScrollBarAlwaysOff)
        self.view.page().mainFrame().setScrollBarPolicy(
            Qt.Vertical, Qt.ScrollBarAlwaysOff)

        if platform.system().startswith(WINDOWS):
            # We are on Windows
            path = (os.environ[REPO_PROPERTIES_WIN_PATH] +
                    WIN_PATH_SEPARATOR +
                    os.path.join(GRAPH_DIR, GRAPH_REINGOLD_PATH))
        else:
            path = (os.environ[REPO_PROPERTIES_UNIX_PATH] +
                    UNIX_PATH_SEPARATOR +
                    os.path.join(
                    GRAPH_DIR, GRAPH_REINGOLD_PATH))

        self.view.load(QUrl(path))

        self.layout.addLayout(self.grid_layout)
        self.layout.addWidget(self.view)
        self.grid_layout.addWidget(self.view_label, 0, 0)
        self.grid_layout.addWidget(self.undock_button, 0, 1)
        self.setMaximumHeight((QDesktopWidget().screenGeometry().height() / 3))
        self.hide()

    def closeEvent(self, event):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Close event invoked."

        # Delete Graph popup dialog on close
        self.g_pop.setAttribute(Qt.WA_DeleteOnClose)
        self.g_pop.close()
        try:
            self.g_pop.dock_button.deleteLater()
            self.g_pop.view_label.deleteLater()
            self.g_pop.layout.deleteLater()
            self.g_pop.grid_layout.deleteLater()
            self.g_pop.deleteLater()
        except Exception, e:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, e
        try:
            self.view.close()
            self.view.deleteLater()
            self.view_label.deleteLater()
            self.undock_button.deleteLater()
            self.layout.deleteLater()
            self.grid_layout.deleteLater()
            self.close()
            self.root.close()
        except Exception, e:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, e

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, \
                    "Escape button clicked."
            self.close()

    def undock(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Undocking graph."
        self.undock_button.hide()
        self.view_label.hide()
        self.g_pop.addView(self.view)
        self.g_pop.show()


class Grapher():
    def __init__(
            self,
            session,
            property_ids,
            data_model_vars,
            gv,
            DMF_HOME,
            is_dmf_lite=False):

        self.session = session
        self.property_ids = property_ids
        self.data_model_vars = data_model_vars
        self.gv = gv
        self.DMF_HOME = DMF_HOME
        self.verbose = self.gv.verbose
        self.is_dmf_lite = is_dmf_lite
        self.common = Common()

        if platform.system().startswith(WINDOWS):
            # We are on Windows
            path = os.environ[REPO_PROPERTIES_WIN_PATH] + WIN_PATH_SEPARATOR
        else:
            path = os.environ[REPO_PROPERTIES_UNIX_PATH] + UNIX_PATH_SEPARATOR

        self.graph_folder = os.path.join(path, GRAPH_DIR)
        if not os.path.exists(self.graph_folder):
            try:
                os.makedirs(self.graph_folder)
                if self.verbose:
                    print self.__class__.__name__, PRINT_COLON, \
                        "Creating tmp graph folder:", PRINT_COLON, \
                        self.graph_folder
            except Exception, e:
                if self.verbose:
                    print self.__class__.__name__, PRINT_COLON, e

        has_write_access = os.access(self.graph_folder, os.W_OK)
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, \
                "Graph save path", PRINT_COLON, path
            print self.__class__.__name__, PRINT_COLON, \
                "Graph save path write access", PRINT_COLON, \
                has_write_access
        if not has_write_access:
            StatusDialog.displayStatus(
                "Warning:   DMF Browser does not have write access to " +
                self.graph_folder + ".\n\n" +
                "Display of dependency graphs will be disabled.\n" +
                "Full functionality may require administrator access.")
        else:
            # Copy over templates
            reingold_graph = (
                self.DMF_HOME + GRAPH_TEMPLATES + GRAPH_REINGOLD_PATH)
            force_directed_graph = (
                self.DMF_HOME + GRAPH_TEMPLATES + GRAPH_FORCE_PATH)
            d3 = self.DMF_HOME + GRAPH_TEMPLATES + D3
            shutil.copy(reingold_graph, os.path.join(
                self.graph_folder, os.path.basename(GRAPH_REINGOLD_PATH)))
            shutil.copy(force_directed_graph, os.path.join(
                self.graph_folder, os.path.basename(GRAPH_FORCE_PATH)))
            shutil.copy(d3, os.path.join(
                self.graph_folder, os.path.basename(D3)))
        self.is_enabled = True if has_write_access else False

    # Graph related functions
    def displayGraph(self, node_obj):
        if not self.is_enabled:
            return

        if platform.system().startswith(WINDOWS):
            # We are on Windows
            path = os.environ[REPO_PROPERTIES_WIN_PATH] + WIN_PATH_SEPARATOR
        else:
            path = os.environ[REPO_PROPERTIES_UNIX_PATH] + UNIX_PATH_SEPARATOR

        graph_dir = os.path.join(path, GRAPH_DIR)
        graph_json_path = os.path.join(graph_dir, GRAPH_JSON_PATH)
        try:
            os.remove(graph_json_path)
        except Exception, e:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, e

        graph = nx.DiGraph()
        if self.is_dmf_lite:
            meta = node_obj
            node_path = meta.get("path")
            maj_ver, min_ver = self.session.getLatestVersion(node_path)
            object_id = self.session.getDMFID(node_path)
            latest_meta = self.session.getLatestMeta(node_path)
            latest_maj_ver = latest_meta.get(MAJOR_VERSION)
            latest_min_ver = latest_meta.get(MINOR_VERSION)
            latest_ver = self.common.concatVersion(
                latest_maj_ver, latest_min_ver)
            name = meta.get(DISPLAY_NAME)
            parents = meta.get(DEPENDENCIES)
            maj_ver = meta.get(MAJOR_VERSION)
            min_ver = meta.get(MINOR_VERSION)
            current_ver = self.common.concatVersion(maj_ver, min_ver)
            mimetype = meta.get(MIMETYPE)
        else:
            cmis_object = node_obj
            object_id = cmis_object.getId().replace(NODE_PREFIX, "")
            name = cmis_object.getProperty(
                self.property_ids.NAME).getFirstValue()
            parents = cmis_object.getProperty(
                self.data_model_vars.CCSI_PARENTS).getValue()
            current_ver = cmis_object.getProperty(
                self.property_ids.VERSION_LABEL).getValue()
            newest_object = self.session.getObject(
                NODE_PREFIX + object_id.split(";")[0])
            latest_ver = newest_object.getProperty(
                self.property_ids.VERSION_LABEL).getValue()
            mimetype = cmis_object.getProperty(
                self.data_model_vars.CCSI_MIMETYPE).getValue()

        img_url = self.getMimeTypeImgUrl(mimetype)
        expired = True if float(latest_ver) > float(current_ver) else False
        graph.add_node(
            object_id,
            name=name,
            group="target",
            imgUrl=img_url,
            expired=expired,
            current_ver=current_ver,
            latest_ver=latest_ver)
        if len(parents) > 0:
            for p in parents:
                print p
                self.getParents(graph, p)
                graph.add_edge(object_id, p)

        if nx.is_tree(graph):
            d = json_graph.tree_data(graph, root=object_id)
        else:
            # This is for force directed layout
            d = json_graph.node_link_data(graph)

        f = open(graph_json_path, 'w')
        json.dump(d, f)
        f.close()
        self.gv.resize(
            self.gv.size().width(),
            (QDesktopWidget().screenGeometry().height() / 3))
        self.gv.view.settings().clearMemoryCaches()
        if nx.is_tree(graph):
            path = FILE_PREFIX + os.path.join(graph_dir, GRAPH_REINGOLD_PATH)
        else:
            path = FILE_PREFIX + os.path.join(graph_dir, GRAPH_FORCE_PATH)
        self.gv.view.load(QUrl(path))
        self.gv.show()  # self.gv.view.reload()

    def getParents(self, graph, node_id):
        if node_id in graph.nodes():
            return
        cmis_object = None
        try:
            if self.is_dmf_lite:
                dmf_id, ver = self.common.splitDMFID(node_id)
                maj_ver, min_ver = self.common.splitVersion(ver)
                meta = self.session.getMetaByDMFID(dmf_id, maj_ver, min_ver)
                parents = meta.get(DEPENDENCIES)
                latest_path = self.session.getLatestPath(dmf_id)
                latest_meta = self.session.getLatestMeta(latest_path)
                newest_name = latest_meta.get(DISPLAY_NAME)
                latest_maj_ver = latest_meta.get(MAJOR_VERSION)
                latest_min_ver = latest_meta.get(MINOR_VERSION)
                current_ver = self.common.concatVersion(maj_ver, min_ver)
                latest_ver = self.common.concatVersion(
                    latest_maj_ver, latest_min_ver)
                mimetype = meta.get(MIMETYPE)
            else:
                cmis_object = self.session.getObject(NODE_PREFIX + node_id)
                parents = cmis_object.getProperty(
                    self.data_model_vars.CCSI_PARENTS).getValues()
                current_ver = cmis_object.getProperty(
                    self.property_ids.VERSION_LABEL).getValue()
                newest_object = self.session.getObject(
                    NODE_PREFIX + node_id.split(";")[0])
                latest_ver = newest_object.getProperty(
                    self.property_ids.VERSION_LABEL).getValue()
                newest_name = newest_object.getProperty(
                    self.property_ids.NAME).getValue()
                mimetype = cmis_object.getProperty(
                    self.data_model_vars.CCSI_MIMETYPE).getValue()

        except Exception, e:
            print e
            cmis_object = None
            mimetype = None
            current_ver = "Unknown"
            latest_ver = "Unknown"
            newest_name = node_id
            expired = True

        img_url = self.getMimeTypeImgUrl(mimetype)
        expired = True if float(latest_ver) > float(current_ver) else False
        graph.add_node(
            node_id,
            name=newest_name,
            group="parent",
            imgUrl=img_url,
            expired=expired,
            current_ver=current_ver,
            latest_ver=latest_ver)

        if (cmis_object or self.is_dmf_lite) and len(parents) > 0:
            for p in parents:
                self.getParents(graph, p)
                graph.add_edge(node_id, p)

    def getMimeTypeImgUrl(self, mimetype):
        if self.verbose:
            print self.__class__.__name__, \
                PRINT_COLON, "Getting Mimetype Image URL for mimetype ", \
                "{m}".format(m=mimetype)
        self.document_icon_url = (
            FILE_PREFIX + self.DMF_HOME + FILETYPE_IMAGE_PATH + TEXT_FILE)

        if mimetype is None:
            return self.document_icon_url
        else:
            try:
                for aspen in aspen_mimetypes:
                    if aspen in mimetype:
                        return FILE_PREFIX + self.DMF_HOME + ASPEN_PLUS

                for excel in excel_mimetypes:
                    if excel in mimetype:
                        return FILE_PREFIX + self.DMF_HOME \
                            + FILETYPE_IMAGE_PATH + EXCEL_FILE

                for ccsi in ccsi_mimetypes:
                    if ccsi in mimetype:
                        return FILE_PREFIX + self.DMF_HOME + CCSI
                return self.document_icon_url
            except Exception, e:
                if self.verbose:
                    print self.__class__.__name__, PRINT_COLON, e
                return self.document_icon_url

    def cleanup(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Cleaning up."
        try:
            for root, dirs, files in os.walk(self.graph_folder, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.graph_folder)
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, \
                    "Removing tmp graph folder:", PRINT_COLON, \
                    self.graph_folder
        except Exception, e:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, e
