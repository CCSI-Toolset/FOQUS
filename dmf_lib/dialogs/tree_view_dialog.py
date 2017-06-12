import traceback

from PySide.QtGui import QDesktopWidget
from PySide.QtGui import QDialog
from PySide.QtGui import QIcon
from PySide.QtGui import QStandardItem
from PySide.QtGui import QStandardItemModel
from PySide.QtGui import QTreeView
from PySide.QtGui import QVBoxLayout

from PySide.QtCore import Qt
from PySide.QtCore import QModelIndex
from PySide.QtCore import Slot
from dmf_lib.common.common import DOCUMENT_DISPLAY_STRING
from dmf_lib.common.common import FOLDER_DISPLAY_STRING
from dmf_lib.common.common import NAME_COLUMN
from dmf_lib.common.common import KIND_COLUMN \
    as ROOT_KIND_COLUMN
from dmf_lib.common.common import NODE_ID_COLUMN \
    as ROOT_NODE_ID_COLUMN
from dmf_lib.common.common import PRINT_COLON
from dmf_lib.common.common import PWC
from dmf_lib.dialogs.status_dialog import StatusDialog
from dmf_lib.gui.path import FILETYPE_IMAGE_PATH
from dmf_lib.gui.path import FOLDER_CLOSED
from dmf_lib.gui.path import FOLDER_OPENED
from dmf_lib.gui.path import TEXT_FILE

from py4j.java_gateway import Py4JNetworkError


class TreeViewDialog(QDialog):
    FOQUS_SESSION_TYPE = "FOQUS_Session"
    KIND_COLUMN = 1
    NODE_ID_COLUMN = 2
    NUM_COLUMN = 3
    JVM_CONN_MSG = "Unable to connect to JVM!"

    def __init__(self, tree_model=None, parent=None):
        super(TreeViewDialog, self).__init__(parent)

        # Inherit from parent
        self.root = parent
        self.verbose = self.root.verbose
        self.session = self.root.session
        self.data_operator = self.root.data_operator
        self.data_folder_map = self.root.data_folder_map
        self.data_model_vars = self.root.data_model_vars
        self.basetype_id = self.root.basetype_id
        self.username = self.root.username
        self.DMF_HOME = self.root.DMF_HOME

        self.CMIS_FOLDER = str(self.basetype_id.CMIS_FOLDER)
        self.CMIS_DOCUMENT = str(self.basetype_id.CMIS_DOCUMENT)

        self.folder_opened_icon = QIcon(
            self.DMF_HOME + FILETYPE_IMAGE_PATH + FOLDER_OPENED)
        self.folder_closed_icon = QIcon(
            self.DMF_HOME + FILETYPE_IMAGE_PATH + FOLDER_CLOSED)
        self.document_icon_url = (
            self.DMF_HOME + FILETYPE_IMAGE_PATH + TEXT_FILE)
        self.document_icon = QIcon(self.document_icon_url)

        self.model = QStandardItemModel(self)
        self.model.setColumnCount(TreeViewDialog.NUM_COLUMN)
        self.model.setHeaderData(NAME_COLUMN, Qt.Horizontal, "Name")
        self.initTreeViewModel(tree_model, self.model)

        self.tree_view = QTreeView(self)
        self.tree_view_selected = self.tree_view.selectionModel()
        self.tree_view.setModel(self.model)
        self.tree_view.clicked.connect(self.onTreeViewClicked)
        self.tree_view.expanded.connect(self.expanded)
        self.tree_view.collapsed.connect(self.collapsed)
        self.tree_view.hideColumn(TreeViewDialog.KIND_COLUMN)
        self.tree_view.hideColumn(TreeViewDialog.NODE_ID_COLUMN)
        self.tree_view_selected = self.tree_view.selectionModel()
        self.tree_view_selected.selectionChanged.connect(
            self.handleSelectionChanged)

        self.tree_view.sortByColumn(0, Qt.AscendingOrder)
        self.tree_view.setCurrentIndex(
            self.model.index(0, 0))  # Select first element of tree view
        self.tree_view.setSortingEnabled(True)
        self.tree_view.setColumnWidth(0, 150)

        layout = QVBoxLayout(self)
        self.setLayout(layout)
        layout.addWidget(self.tree_view)
        screen_geometry = QDesktopWidget().screenGeometry()
        self.setMinimumSize(
            screen_geometry.width()/4, screen_geometry.height()/3)

    @Slot(QModelIndex)
    def expanded(self, index):
        self.model.itemFromIndex(
            index.sibling(index.row(), NAME_COLUMN)).setIcon(
                self.folder_opened_icon)
        self.createChildNode(index)
        self.tree_view.resizeColumnToContents(0)

    @Slot(QModelIndex)
    def collapsed(self, index):
        self.model.itemFromIndex(
            index.sibling(index.row(), NAME_COLUMN)).setIcon(
                self.folder_closed_icon)
        self.tree_view.resizeColumnToContents(0)

    @Slot(QModelIndex)
    def onTreeViewClicked(self, index):
        cmis_object = index.model().itemFromIndex(
            index.sibling(index.row(), NAME_COLUMN))
        cmis_object_id = index.model().itemFromIndex(
            index.sibling(index.row(), self.NODE_ID_COLUMN)).text()
        type = index.model().itemFromIndex(
            index.sibling(index.row(), self.KIND_COLUMN)).text()
        if type == DOCUMENT_DISPLAY_STRING:
            can_add_parent = True
        else:
            can_add_parent = False
        self.root.add_parent_button.setEnabled(can_add_parent)
        self.target_name = cmis_object.text()
        self.target_id = cmis_object_id

    @Slot(QModelIndex)
    def handleSelectionChanged(self, selected, deselected):
        try:
            index = selected.indexes()[0]
            self.onTreeViewClicked(index)
        except Py4JNetworkError, e:
            print e.__class__.__name__, PRINT_COLON, traceback.format_exc()
            StatusDialog.displayStatus(
                TreeViewDialog.JVM_CONN_MSG + " " + traceback.format_exc())
        except Exception, e:
            pass

    def initTreeViewModel(self, origin_model, target_model):
        for i in xrange(origin_model.rowCount()):
            target_model.appendRow(
                self.createTreeViewModelRow(origin_model, i))
            if origin_model.item(i).hasChildren():
                for c in xrange(origin_model.item(i).rowCount()):
                    target_model.item(i).appendRow(self.createTreeViewModelRow(
                        origin_model.item(i), c, True))

    def createTreeViewModelRow(self, origin_item, i, is_child=False):
        # Ugly stuff referenced from AlfrescoFileSystem
        if is_child:
            name = origin_item.child(i).text()
            type = origin_item.child(i, ROOT_KIND_COLUMN).text()
            id = origin_item.child(i, ROOT_NODE_ID_COLUMN).text()
        else:
            name = origin_item.item(i).text()
            type = origin_item.item(i, ROOT_KIND_COLUMN).text()
            id = origin_item.item(i, ROOT_NODE_ID_COLUMN).text()
        name = QStandardItem(name)
        if type == DOCUMENT_DISPLAY_STRING:
            name.setIcon(self.document_icon)
            # Get ID with version for documents
            id = self.session.getObject(str(id)).getId()
        else:
            name.setIcon(self.folder_closed_icon)
        type = QStandardItem(type)
        id = QStandardItem(id)
        row = [name, type, id]
        for r in row:
            r.setEditable(False)
        return row

    def createChildNode(self, index):
        try:
            # This is a dummy test to check if connection is alive
            id = index.model().itemFromIndex(index.sibling(
                index.row(), TreeViewDialog.NODE_ID_COLUMN)).text()
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
        except Py4JNetworkError:
            StatusDialog.displayStatus(
                TreeViewDialog.JVM_CONN_MSG + " " + traceback.format_exc())

    def addChildNode(self, index):
        id = index.model().itemFromIndex(
            index.sibling(index.row(), TreeViewDialog.NODE_ID_COLUMN)).text()
        if id is not None:
            try:
                cmis_object = self.session.getObject(str(id))
                if self.CMIS_FOLDER == str(
                        cmis_object.getType().getBaseTypeId()):
                    children = cmis_object.getChildren()
                    children_iterator = children.iterator()

                    while children_iterator.hasNext():
                        current_child = children_iterator.next()
                        self.addDisplayNodeProperties(
                            current_child, index.model(), index)

            except Exception, e:
                print e.__class__.__name__, PRINT_COLON, e

    def addDisplayNodeProperties(self, cmis_object, model, index=None):
        id = cmis_object.getId()
        if PWC in str(id):
            return
        name = cmis_object.getName()
        type = str(cmis_object.getType().getBaseTypeId())
        name = QStandardItem(name)
        id = QStandardItem(id)
        if type == self.CMIS_DOCUMENT:
            type = DOCUMENT_DISPLAY_STRING
            name.setIcon(self.document_icon)
        else:
            type = FOLDER_DISPLAY_STRING
            name.setIcon(self.folder_closed_icon)
        type = QStandardItem(type)
        new_row = [name, type, id]
        for r in new_row:
            r.setEditable(False)

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

            else:
                model.item(index.row(), 0).appendRow(new_row)
        else:
            model.appendRow(new_row)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Enter or key == Qt.Key_Return:
            self.tree_view.expand(self.tree_view.currentIndex())
        elif key == Qt.Key_Escape:
            self.root.close()

    def closeEvent(self, event):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Close event invoked."
        super(TreeViewDialog, self).closeEvent(event)

        self.model.clear()
        self.model.deleteLater()
        self.tree_view.deleteLater()

        self.tree_view = None
        self.model = None
