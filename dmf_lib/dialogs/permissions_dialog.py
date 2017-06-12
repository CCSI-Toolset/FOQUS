from PySide.QtGui import *
from PySide.QtCore import *
from dmf_lib.gui.path import *
from dmf_lib.common.common import *
import json


class PermissionsDialog(QDialog):
    def __init__(self, parent):
        super(PermissionsDialog, self).__init__(parent)

        layout = QVBoxLayout(self)
        self.role_dict = {}
        self.indirect_role_dict = {}
        self.parent = parent
        self.inheritance = False
        self.roles = [parent.role.Editor.name(),
                      parent.role.Coordinator.name(),
                      parent.role.Collaborator.name(),
                      parent.role.Consumer.name(),
                      parent.role.Contributor.name()]
        self.delete = []

        # OK and Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        self.inherited_header = QWidget(self)
        self.inherited_header_layout = QGridLayout()
        self.inherited_header.setLayout(self.inherited_header_layout)

        self.inherited = QWidget(self)
        self.inherited_layout = QGridLayout()
        self.inherited.setLayout(self.inherited_layout)

        inherited_perm_label = QLabel(self)
        inherited_perm_label.setText("Inherited Permissions")
        inherited_perm_label.setStyleSheet("font-size: 18pt;")

        self.inherited_toggle = QPushButton("Inherit Permissions")
        self.inherited_toggle.setMaximumWidth(160)
        self.inherited_toggle.setMaximumHeight(40)
        self.inherited_toggle.clicked.connect(self.toggleInheritance)
        self.inherited_toggle.setEnabled(False)
        if self.inheritance:
            self.inherited_toggle.setIcon(QIcon(parent.DMF_HOME + ACTION_IMAGE_PATH + ENABLE_ON))
            self.inherited.show()
        else:
            self.inherited_toggle.setIcon(QIcon(parent.DMF_HOME + ACTION_IMAGE_PATH + ENABLE_OFF))
            self.inherited.hide()

        self.local_header = QWidget(self)
        self.local_header_layout = QGridLayout()
        self.local_header.setLayout(self.local_header_layout)

        self.local = QWidget(self)
        self.local_layout = QGridLayout()
        self.local.setLayout(self.local_layout)

        local_perm_label = QLabel(self)
        local_perm_label.setText("Locally Set Permissions")
        local_perm_label.setStyleSheet("font-size: 18pt;")

        add_local = QPushButton("Add User/Group")
        add_local.setIcon(QIcon(parent.DMF_HOME + ACTION_IMAGE_PATH + CREATE))
        add_local.setMaximumWidth(150)
        add_local.setMaximumHeight(40)
        add_local.clicked.connect(self.addRow)

        self.inherited_header_layout.addWidget(inherited_perm_label, 0, 0)
        self.inherited_header_layout.addWidget(self.inherited_toggle, 0, 1)

        self.local_header_layout.addWidget(local_perm_label, 0, 0)
        self.local_header_layout.addWidget(add_local, 0, 1)

        layout.addWidget(self.inherited_header)
        layout.addWidget(self.inherited)
        layout.addWidget(self.local_header)
        layout.addWidget(self.local)
        layout.addWidget(buttons)
        layout.setSizeConstraint(QLayout.SetFixedSize)

    def getDisplayID(self, id):
        if id.startswith("GROUP"):
            return id.split('_')[1].capitalize()
        else:
            return id

    def toggleInheritance(self):
        if self.inheritance:
            self.sender().setIcon(
                QIcon(self.parent.DMF_HOME + ACTION_IMAGE_PATH + ENABLE_OFF))
            self.inherited.hide()
        else:
            self.sender().setIcon(
                QIcon(self.parent.DMF_HOME + ACTION_IMAGE_PATH + ENABLE_ON))
            self.inherited.show()
        self.inheritance = False if self.inheritance else True

    def addRow(self):
        response, status_code = self.parent.service_adaptor.getAlfrescoUserList(
            self.parent.connURL, self.parent.username, self.parent.password)
        if status_code != HTTP_SUCCESS_CODE:
            print "Not successful in retrieving user list"
            return

        people = json.loads(response)
        username = []
        for p in people['people']:
            username.append(p['userName'])

        result, selected_user = UserSelectionDialog.\
            popupUserSelection(username, self.role_dict.keys(), self)
        if not result:
            return

        id_label = QLabel(self)
        id_label.setText(self.getDisplayID(selected_user))

        role = QComboBox(self)
        for r in self.roles:
            role.addItem(r, r)

        self.role_dict.update({selected_user: role})

        button = QPushButton()
        button.setIcon(
            QIcon(self.parent.DMF_HOME + ACTION_IMAGE_PATH + DELETE))
        button.setToolTip("Delete")
        button.setMaximumWidth(25)
        button.setMaximumHeight(25)
        button.setStyleSheet("background-color: transparent;")
        button.clicked.connect(self.deleteRow)
        row_count = self.local_layout.rowCount()
        self.local_layout.addWidget(id_label, row_count, 0)
        self.local_layout.addWidget(role, row_count, 1)
        self.local_layout.addWidget(button, row_count, 2)

    def deleteRow(self):
        # Get widgets
        cbox_pos=self.local_layout.getItemPosition(self.local_layout.indexOf(self.sender())-1)
        cbox=self.local_layout.itemAtPosition(cbox_pos[0], cbox_pos[1]).widget()
        label_pos=self.local_layout.getItemPosition(self.local_layout.indexOf(self.sender())-2)
        label=self.local_layout.itemAtPosition(label_pos[0], label_pos[1]).widget()

        # Hide removed
        self.local_layout.removeWidget(self.sender())
        self.local_layout.removeWidget(cbox)
        self.local_layout.removeWidget(label)
        self.sender().hide()
        cbox.hide()
        label.hide()
        self.delete.append(label.text())

        # Remove from dictionary
        del self.role_dict[label.text()]

    @staticmethod
    def displayPermissions(ace, inherited_ace, parent):
        padding = '                      '
        def getRoleDisplayName(r):
            r = str(r)
            if parent.role.Coordinator.name() in r:
                return parent.role.Coordinator.name()
            elif parent.role.Collaborator.name() in r:
                return parent.role.Collaborator.name()
            elif parent.role.Contributor.name() in r:
                return parent.role.Contributor.name()
            elif parent.role.Consumer.name() in r:
                return parent.role.Consumer.name()
            elif parent.role.Editor.name() in r:
                return parent.role.Editor.name()
            else:
                return None

        def addHeader(row_counter, layout):
            title_label = QLabel(dialog)
            title_label.setText("Users and Groups" + padding)
            role_label = QLabel(dialog)
            role_label.setText("Role")
            layout.addWidget(title_label, row_counter, 0)
            layout.addWidget(role_label, row_counter, 1)

        dialog = PermissionsDialog(parent)

        row_counter = 0
        addHeader(row_counter, dialog.inherited_layout)
        row_counter += 1

        for i in xrange(len(inherited_ace)):
            id_label = QLabel(dialog)
            id = inherited_ace[i].getPrincipalId()
            id_label.setText(dialog.getDisplayID(id))

            for p in inherited_ace[i].getPermissions():
                role = QLabel(dialog)
                role_display_name = getRoleDisplayName(p)
                if role_display_name:
                    role.setText(role_display_name)

            dialog.inherited_layout.addWidget(id_label, row_counter, 0)
            dialog.inherited_layout.addWidget(role, row_counter, 1)
            dialog.indirect_role_dict.update({id : role_display_name})

            row_counter += 1

        row_counter = 0
        addHeader(row_counter, dialog.local_layout)
        row_counter += 1

        for i in xrange(len(ace)):
            print ace[i]
            is_direct = ace[i].isDirect()
            if not is_direct:
                dialog.inheritance = True
                dialog.inherited_toggle.setIcon(QIcon(parent.DMF_HOME + ACTION_IMAGE_PATH + ENABLE_ON))
                dialog.inherited.show()
                continue

            id_label = QLabel(dialog)
            id = ace[i].getPrincipalId()
            id_label.setText(dialog.getDisplayID(id))

            role = QComboBox(dialog)
            for r in dialog.roles:
                role.addItem(r, r)
            for p in ace[i].getPermissions():
                role_display_name = getRoleDisplayName(p)
                if role_display_name:
                    role.setCurrentIndex(dialog.roles.index(role_display_name))

            button = QPushButton()
            button.setIcon(QIcon(parent.DMF_HOME + ACTION_IMAGE_PATH + DELETE))
            button.setToolTip("Delete")
            button.setMaximumWidth(25)
            button.setMaximumHeight(25)
            button.setStyleSheet("background-color: transparent;")
            button.clicked.connect(dialog.deleteRow)

            dialog.role_dict.update({id : role})
            dialog.delete.append(id)
            dialog.local_layout.addWidget(id_label, row_counter, 0)
            dialog.local_layout.addWidget(role, row_counter, 1)
            dialog.local_layout.addWidget(button, row_counter, 2)
            row_counter += 1

        result = dialog.exec_()
        for k in dialog.role_dict.keys():
            dialog.role_dict.update({k : str(dialog.roles[dialog.role_dict.get(k).currentIndex()])})

        return (result == QDialog.Accepted, dialog.role_dict, dialog.delete)
#        if not dialog.inheritance:
#            return (result == QDialog.Accepted, dialog.role_dict, False)
#        else:
#            return (result == QDialog.Accepted, dialog.role_dict, dialog.indirect_role_dict)

class UserSelectionDialog(QDialog):
    def __init__(self, users, disabled, parent=None):
        super(UserSelectionDialog, self).__init__(parent)

        self.radio_list = []
        layout = QVBoxLayout(self)
        label = QLabel(self)
        label.setText("Select User/Group:")
        label.setStyleSheet("color: #FFFFFF;")

        layout.addWidget(label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        for i in xrange(len(users)):
            radio = QRadioButton(self)
            radio.setText(users[i])
            radio.setStyleSheet("color: #FFFFFF;")
            self.radio_list.append(radio)
            layout.addWidget(radio)
            if i == 0:
                radio.setChecked(True)
            if users[i] in disabled:
                radio.setEnabled(False)

        layout.addWidget(buttons)
        layout.setSizeConstraint(QLayout.SetFixedSize)

        pal = QPalette()
        pal.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(pal)
        self.setWindowOpacity(0.85)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

    @staticmethod
    def popupUserSelection(users, disabled, parent=None):
        dialog = UserSelectionDialog(sorted(users), disabled, parent)

        result = dialog.exec_()
        index = 0
        for r in dialog.radio_list:
            if r.isChecked():
                break
            else:
                index += 1

        return (result == QDialog.Accepted, dialog.radio_list[index].text())
