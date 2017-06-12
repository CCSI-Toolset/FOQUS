from PySide.QtGui import QComboBox
from PySide.QtGui import QDialog
from PySide.QtGui import QDialogButtonBox
from PySide.QtGui import QGridLayout
from PySide.QtGui import QHBoxLayout
from PySide.QtGui import QIcon
from PySide.QtGui import QLabel
from PySide.QtGui import QLayout
from PySide.QtGui import QPushButton
from PySide.QtGui import QScrollArea
from PySide.QtGui import QSpacerItem
from PySide.QtGui import QVBoxLayout
from PySide.QtGui import QWidget
from PySide.QtCore import Qt

from dmf_lib.dialogs.status_dialog import StatusDialog
from dmf_lib.dialogs.tree_view_dialog import TreeViewDialog
from dmf_lib.common.common import NODE_PREFIX
from dmf_lib.common.common import SEMI_COLON
from dmf_lib.common.common import PRINT_COLON
from dmf_lib.common.common import PWC
from dmf_lib.common.methods import Common
from dmf_lib.gui.path import ACTION_IMAGE_PATH
from dmf_lib.gui.path import CREATE
from dmf_lib.gui.path import DELETE


class EditParentsDialog(QDialog):
    PARENT_LABEL_POS = 0
    PARENT_VER_POS = 1
    PARENT_REMOVE_BUTTON_POS = 2
    PARENT_ID_LABEL_POS = 3

    def __init__(self, id, parent_ids, tree_model, parent):
        super(EditParentsDialog, self).__init__(parent)

        StatusDialog.displayStatus(
            "\nWarning: Take caution when adding or removing dependencies.\n",
            parent=self)

        # Inherit from parent
        self.root = parent
        self.session = self.root.session
        self.data_operator = self.root.data_operator
        self.data_folder_map = self.root.data_folder_map
        self.data_model_vars = self.root.data_model_vars
        self.basetype_id = self.root.basetype_id
        self.username = self.root.username
        self.DMF_HOME = self.root.DMF_HOME
        self.verbose = self.root.verbose
        self.id = id

        self.parent_ids = dict()
        layout = QVBoxLayout(self)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        self.parents_label = QLabel(self)
        self.parents_label.setText("Current parents:")
        self.parents = QWidget(self)
        self.parents_layout = QGridLayout()
        self.parents_layout.setAlignment(Qt.AlignTop)
        self.parents.setLayout(self.parents_layout)

        self.parents_scroll = QScrollArea(self)
        self.parents_scroll.setWidgetResizable(True)
        self.parents_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.parents_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.parents_scroll.setWidget(self.parents)

        self.add_parent_button = QPushButton("Add parent", self)
        self.add_parent_button.setIcon(
            QIcon(parent.root.DMF_HOME + ACTION_IMAGE_PATH + CREATE))
        self.add_parent_button.setMaximumWidth(150)
        self.add_parent_button.setMaximumHeight(35)
        self.add_parent_button.clicked.connect(self.addParent)
        self.add_parent_button.setToolTip(
            "Click to add parent to current parents list "
            "(parents can only be files)")
        self.tree_view_dialog = TreeViewDialog(tree_model, self)

        self.central_layout = QHBoxLayout()
        self.central = QWidget(self)
        self.central.setLayout(self.central_layout)

        self.left_pane = QWidget(self)
        self.left_pane_layout = QVBoxLayout()
        self.left_pane.setLayout(self.left_pane_layout)
        self.central_layout.addWidget(self.left_pane)
        self.central_layout.addWidget(self.parents_scroll)

        self.parents_layout.addWidget(self.parents_label)
        self.spacer = QSpacerItem(self.tree_view_dialog.width()/1.2, 0)
        self.parents_layout.addItem(self.spacer)
        self.left_pane_layout.addWidget(self.tree_view_dialog)
        self.left_pane_layout.addWidget(self.add_parent_button)
        self.left_pane_layout.setSizeConstraint(QLayout.SetFixedSize)

        try:
            for id in parent_ids:
                label = QLabel(self)
                id_label = QLabel(self)
                id, ver = Common().splitDMFID(id)
                cmis_object = self.session.getObject(str(NODE_PREFIX + id))
                name = cmis_object.getName()
                ver_list = self.data_operator.getVersionHistoryLabels(
                    self.session, cmis_object)
                ver_select = QComboBox(self)
                initial_i = 0
                label.setText(name)
                id_label.setText(id)
                id_label.hide()
                if ver_list is not None or len(ver_list) > 0:
                    for v in ver_list:
                        if PWC in str(v):
                            continue
                        ver_select.addItem(v, v)
                        if v == ver:
                            initial_i = ver_select.count()-1
                ver_select.setCurrentIndex(initial_i)
                button = self.createRemoveButton()
                row_i = self.parents_layout.rowCount()
                self.parents_layout.addWidget(
                    label, row_i, EditParentsDialog.PARENT_LABEL_POS)
                self.parents_layout.addWidget(
                    ver_select, row_i, EditParentsDialog.PARENT_VER_POS)
                self.parents_layout.addWidget(
                    button, row_i, EditParentsDialog.PARENT_REMOVE_BUTTON_POS)
                self.parents_layout.addWidget(
                    id_label, row_i, EditParentsDialog.PARENT_ID_LABEL_POS)
                self.parent_ids.update({id: ver})
                ver_select.currentIndexChanged["QString"].connect(
                    self.handleComboBoxChange)
        except Exception, e:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, e

        layout.addWidget(self.central)
        layout.addWidget(buttons)
        layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(layout)

    def createRemoveButton(self):
        button = QPushButton()
        button.setIcon(QIcon(self.DMF_HOME + ACTION_IMAGE_PATH + DELETE))
        button.setToolTip("Remove parent")
        button.setMaximumWidth(25)
        button.setMaximumHeight(25)
        button.setStyleSheet("background-color: transparent;")
        button.clicked.connect(self.removeParent)
        return button

    def removeParent(self):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Remove parent..."
        id_label_pos = self.parents_layout.getItemPosition(
            self.parents_layout.indexOf(self.sender())+1)
        id_label = self.parents_layout.itemAtPosition(
            id_label_pos[0], id_label_pos[1]).widget()
        button_pos = self.parents_layout.getItemPosition(
            self.parents_layout.indexOf(self.sender()))
        button = self.parents_layout.itemAtPosition(
            button_pos[0], button_pos[1]).widget()
        ver_select_pos = self.parents_layout.getItemPosition(
            self.parents_layout.indexOf(self.sender())-1)
        ver_select = self.parents_layout.itemAtPosition(
            ver_select_pos[0], ver_select_pos[1]).widget()
        label_pos = self.parents_layout.getItemPosition(
            self.parents_layout.indexOf(self.sender())-2)
        label = self.parents_layout.itemAtPosition(
            label_pos[0], label_pos[1]).widget()
        self.parent_ids.pop(id_label.text())

        button.hide()
        ver_select.hide()
        label.hide()
        id_label.deleteLater()
        button.deleteLater()
        ver_select.deleteLater()
        label.deleteLater()
        button = None
        ver_select = None
        label = None
        self.adjustSize()

    def addParent(self):
        parent_id = self.tree_view_dialog.target_id
        parent_name = self.tree_view_dialog.target_name

        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, \
                "Adding parent..."
        id, ver = Common().splitDMFID(parent_id)
        if id == self.id:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, \
                    "Cannot create dependency to self"
            StatusDialog.displayStatus(
                "Error: Cannot create dependency to self.")
        else:
            id = str(id.replace(NODE_PREFIX, ''))
            if id in self.parent_ids:
                if self.verbose:
                    print self.__class__.__name__, PRINT_COLON, \
                        "Dependency already present"
                StatusDialog.displayStatus(
                    "Error: Multiple dependencies between "
                    "an object is disallowed.")
            else:
                label = QLabel(self)
                label.setText(parent_name)
                button = self.createRemoveButton()
                row_i = self.parents_layout.rowCount()
                cmis_object = self.session.getObject(str(NODE_PREFIX + id))
                ver_list = self.data_operator.getVersionHistoryLabels(
                    self.session, cmis_object)
                id_label = QLabel(self)
                id_label.setText(id)
                id_label.hide()
                ver_select = QComboBox()
                if ver_list is not None or len(ver_list) > 0:
                    for v in ver_list:
                        if PWC in str(v):
                            continue
                        ver_select.addItem(v, v)
                self.parents_layout.addWidget(
                    label, row_i, EditParentsDialog.PARENT_LABEL_POS)
                self.parents_layout.addWidget(
                    ver_select, row_i, EditParentsDialog.PARENT_VER_POS)
                self.parents_layout.addWidget(
                    button, row_i, EditParentsDialog.PARENT_REMOVE_BUTTON_POS)
                self.parents_layout.addWidget(
                    id_label, row_i, EditParentsDialog.PARENT_ID_LABEL_POS)
                self.parent_ids.update({id: ver})
                ver_select.currentIndexChanged["QString"].connect(
                    self.handleComboBoxChange)

    def handleComboBoxChange(self):
        try:
            ver_select_pos = self.parents_layout.getItemPosition(
                self.parents_layout.indexOf(self.sender()))
            ver_select = self.parents_layout.itemAtPosition(
                ver_select_pos[0], ver_select_pos[1]).widget()
            id_label_pos = self.parents_layout.getItemPosition(
                self.parents_layout.indexOf(self.sender())+2)
            id_label = self.parents_layout.itemAtPosition(
                id_label_pos[0], id_label_pos[1]).widget()
            ver = ver_select.itemData(ver_select.currentIndex())
            id = id_label.text()
            self.parent_ids.update({id: ver})
        except:
            # Known errors: It is known that at initialization
            # of each QComboBox, this function is called.
            pass

    def closeEvent(self, event):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Close event invoked."
        super(EditParentsDialog, self).closeEvent(event)
        try:
            self.parents_layout.deleteLater()
            self.central_layout.deleteLater()
            self.left_pane_layout.deleteLater()
            self.tree_view_dialog.close()
        except Exception, e:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, e

        self.parents_layout = None
        self.central_layout = None
        self.left_pane_layout = None

    @staticmethod
    def displayParents(id, parent_ids, tree_model, parent):
        dialog = EditParentsDialog(id, parent_ids, tree_model, parent)
        result = dialog.exec_()
        merged_parent_ids = []

        for k in dialog.parent_ids:
            merged_parent_ids.append(k + SEMI_COLON + dialog.parent_ids[k])
        dialog.setAttribute(Qt.WA_DeleteOnClose)  # Delete Dialog on close
        dialog.close()
        return (result == QDialog.Accepted, merged_parent_ids)
