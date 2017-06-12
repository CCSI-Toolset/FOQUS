import os
import platform
from PySide.QtCore import Qt
from PySide.QtCore import QIODevice
from PySide.QtCore import QFile
from PySide.QtCore import QDataStream

from dmf_lib.dialogs.status_dialog import StatusDialog
from dmf_lib.common.common import NAME_COLUMN
from dmf_lib.common.common import SIZE_COLUMN
from dmf_lib.common.common import KIND_COLUMN
from dmf_lib.common.common import DATE_MOD_COLUMN
from dmf_lib.common.common import NODE_ID_COLUMN
from dmf_lib.common.common import DEFAULT_NAME_COLUMN_WIDTH
from dmf_lib.common.common import NUM_COLUMN
from dmf_lib.common.common import PRINT_COLON
from dmf_lib.common.common import WINDOWS
from dmf_lib.common.common import WIN_PATH_SEPARATOR
from dmf_lib.common.common import UNIX_PATH_SEPARATOR
from dmf_lib.common.common import FOLDER_DISPLAY_STRING
from dmf_lib.common.common import DOCUMENT_DISPLAY_STRING
from dmf_lib.common.common import CACHE_EXT
from dmf_lib.common.common import REPO_PROPERTIES_WIN_PATH
from dmf_lib.common.common import REPO_PROPERTIES_UNIX_PATH


class TreeOps():
    def __init__(self, parent=None):
        if parent:
            self.verbose = parent.verbose
            self.root = parent

    def setupTreeViewWithModel(self, tree_view, model):
        tree_view.setModel(model)
        tree_view.hideColumn(NODE_ID_COLUMN)
        tree_view.setSortingEnabled(True)
        tree_view.setColumnWidth(0, DEFAULT_NAME_COLUMN_WIDTH)

    def setModelHeaders(self, model):
        model.setHeaderData(NAME_COLUMN, Qt.Horizontal, "Name")
        model.setHeaderData(SIZE_COLUMN, Qt.Horizontal, "Size")
        model.setHeaderData(KIND_COLUMN, Qt.Horizontal, "Kind")
        model.setHeaderData(DATE_MOD_COLUMN, Qt.Horizontal, "Date Modified")
        model.setHeaderData(NODE_ID_COLUMN, Qt.Horizontal, "Id")

    def refreshTree(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, \
                "Refresh Tree."
        dialog = StatusDialog(
            status="Refreshing...", use_padding=True, parent=self.root)
        dialog.show()
        self.exportTree()
        self.root.model.clear()
        self.root.model.setColumnCount(NUM_COLUMN)
        self.setModelHeaders(self.root.model)
        self.root.setupTree()
        dialog.close()
        dialog.deleteLater()

    def deleteCachedTree(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, \
                "Delete cached tree."
        if platform.system().startswith(WINDOWS):  # We are on Windows
            file_location = os.environ[REPO_PROPERTIES_WIN_PATH] + \
                WIN_PATH_SEPARATOR
        else:
            file_location = os.environ[REPO_PROPERTIES_UNIX_PATH] + \
                UNIX_PATH_SEPARATOR
        try:
            os.remove(
                file_location +
                '.' + self.root.repo_fname +
                '_' + self.root.user +
                CACHE_EXT)
            if self.verbose:
                print file_location + \
                    '.' + self.root.repo_fname + \
                    '_' + self.root.user + CACHE_EXT
        except Exception, e:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, e

    def exportTree(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON,\
                "Exporting tree..."

        def exportTreeTraveller(self, item, out):
            index = item.index()
            kind = index.model().itemFromIndex(
                index.sibling(index.row(), KIND_COLUMN)).text()
            node_id = index.model().itemFromIndex(
                index.sibling(index.row(), NODE_ID_COLUMN)).text()

            if kind == FOLDER_DISPLAY_STRING:
                if self.root.tree_view.isExpanded(item.index()):
                    if index in self.root.tree_view.selectedIndexes():
                        output = node_id + '---11'
                        out.writeQString(output)
                    else:
                        output = node_id + '---01'
                        out.writeQString(output)

                    if item.hasChildren():
                        for r in xrange(item.rowCount()):
                            exportTreeTraveller(self, item.child(r, 0), out)
                else:
                    if index in self.root.tree_view.selectedIndexes():
                        output = node_id + '---10'
                        out.writeQString(output)

            elif kind == DOCUMENT_DISPLAY_STRING:
                if index in self.root.tree_view.selectedIndexes():
                    output = node_id + '---1'
                    out.writeQString(output)

        if platform.system().startswith(WINDOWS):  # We are on Windows
            PROP_LOC = os.environ[REPO_PROPERTIES_WIN_PATH] + \
                WIN_PATH_SEPARATOR
        else:
            PROP_LOC = os.environ[REPO_PROPERTIES_UNIX_PATH] + \
                UNIX_PATH_SEPARATOR

        f = QFile(PROP_LOC +
                  '.' + self.root.repo_fname +
                  '_' + self.root.user +
                  CACHE_EXT)
        if f.exists():
            # Do something maybe?
            pass
        if not f.open(QIODevice.WriteOnly or QIODevice.Text):
            return
        out = QDataStream(f)
        for i in xrange(self.root.model.rowCount()):
            exportTreeTraveller(self, self.root.model.item(i, 0), out)
        f.flush()
        f.close()

    def importTree(self, tree_view):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON,\
                "Importing tree..."

        def importTreeTraveller(self, item):
            index = item.index()
            kind = index.model().itemFromIndex(
                index.sibling(index.row(), KIND_COLUMN)).text()
            object_id = index.model().itemFromIndex(
                index.sibling(index.row(), NODE_ID_COLUMN)).text()
            value = tree_dict.get(object_id)

            if value is None:
                return
            if value or value[0]:
                try:
                    if value[0]:
                        self.root.tree_view.setCurrentIndex(index)
                        self.root.last_clicked_index = index.sibling(
                            index.row(), NAME_COLUMN)
                except:
                    self.root.tree_view.setCurrentIndex(index)
                    self.root.last_clicked_index = index.sibling(
                        index.row(), NAME_COLUMN)

            if kind == FOLDER_DISPLAY_STRING and item.hasChildren():
                if value[1]:
                    tree_view.expand(index)
                for r in xrange(item.rowCount()):
                    importTreeTraveller(self, item.child(r, 0))

        if platform.system().startswith(WINDOWS):  # We are on Windows
            f = QFile(
                os.environ[REPO_PROPERTIES_WIN_PATH] +
                WIN_PATH_SEPARATOR +
                '.' + self.root.repo_fname +
                '_' + self.root.user +
                CACHE_EXT)
        else:
            f = QFile(os.environ[REPO_PROPERTIES_UNIX_PATH] +
                      UNIX_PATH_SEPARATOR +
                      '.' + self.root.repo_fname +
                      '_' + self.root.user +
                      CACHE_EXT)

        if not f.exists():
            return
        if not f.open(QIODevice.ReadOnly | QIODevice.Text):
            return
        if self.root.IS_BROWSER_MODE:
            self.root.root.updateSplash(
                "Importing last user session filesystem structure...")
        input = QDataStream(f)
        tree_dict = {}
        while not input.atEnd():
            line = input.readQString()
            line_split = line.split('---')
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON,\
                    "Import:", line_split[0], line_split[1]
            if line_split[1] == '1':
                tree_dict.update({line_split[0]: True})
            else:
                if line_split[1] == '11':
                    tree_dict.update({line_split[0]: [True, True]})
                elif line_split[1] == '10':
                    tree_dict.update({line_split[0]: [True, False]})
                else:
                    tree_dict.update({line_split[0]: [False, True]})
        for i in xrange(tree_view.model().rowCount()):
            importTreeTraveller(self, self.root.model.item(i, 0))
        f.close()

    def isNodeNeedsFilter(self, data_type, ext_filter, obj_name):
        return True if (data_type == DOCUMENT_DISPLAY_STRING and
                        ext_filter is not None and
                        not obj_name.endswith(ext_filter)) else False

    def filterDocuments(self, tree_view, item, model, ext_filter):
        index = item.index()
        object_kind = index.model().itemFromIndex(
            index.sibling(index.row(), KIND_COLUMN)).text()

        if object_kind == DOCUMENT_DISPLAY_STRING:
            if ext_filter is None:
                tree_view.setRowHidden(index.row(), index.parent(), False)
                for n in xrange(NUM_COLUMN):
                    row_item = index.model().itemFromIndex(
                        index.sibling(index.row(), n))
                    row_item.setEnabled(True)
                    row_item.setSelectable(True)
            elif not str(item.text()).endswith(ext_filter):
                # Select first element of tree view
                if tree_view.selectedIndexes()[0] == index:
                    tree_view.setCurrentIndex(index.parent())
                    self.root.last_clicked_index = tree_view.currentIndex().\
                        sibling(index.row(), NAME_COLUMN)
                tree_view.setRowHidden(index.row(), index.parent(), True)
                for n in xrange(NUM_COLUMN):
                    row_item = index.model().itemFromIndex(
                        index.sibling(index.row(), n))
                    row_item.setEnabled(False)
                    row_item.setSelectable(False)

        elif object_kind == FOLDER_DISPLAY_STRING and item.hasChildren():
            if tree_view.selectedIndexes()[0] == index:
                self.root.last_clicked_index = tree_view.currentIndex().\
                    sibling(index.row(), NAME_COLUMN)
            for i in xrange(item.rowCount()):
                child = item.child(i, 0)
                self.filterDocuments(tree_view, child, model, ext_filter)
