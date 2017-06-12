import os

from PySide.QtGui import QCheckBox
from PySide.QtGui import QDialog
from PySide.QtGui import QDialogButtonBox
from PySide.QtGui import QLabel
from PySide.QtGui import QLineEdit
from PySide.QtGui import QPixmap
from PySide.QtGui import QLayout
from PySide.QtGui import QGridLayout
from PySide.QtGui import QVBoxLayout
from PySide.QtCore import Qt

from dmf_lib.common.common import DMF_HOME
from dmf_lib.gui.path import HEADER_PATH


class LoginDialog(QDialog):
    def __init__(self, save_option, parent=None):
        super(LoginDialog, self).__init__(parent)
        self.setWindowTitle("Login Credentials")

        layout = QVBoxLayout(self)
        grid_layout = QGridLayout()

        self.user_label = QLabel(self)
        self.user_label.setText("Username:")
        self.user = QLineEdit()

        self.password_label = QLabel(self)
        self.password_label.setText("Password:")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)

        is_save_info_label = QLabel(self)
        is_save_info_label.setText("Save Credentials")
        self.is_save_info = QCheckBox()

        # OK and Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        grid_layout.addWidget(self.user_label, 0, 0)
        grid_layout.addWidget(self.user, 0, 1)
        grid_layout.addWidget(self.password_label, 1, 0)
        grid_layout.addWidget(self.password, 1, 1)
        grid_layout.addWidget(is_save_info_label, 2, 0)
        grid_layout.addWidget(self.is_save_info, 2, 1)
        if not save_option:
            is_save_info_label.hide()
            self.is_save_info.hide()

        image_label = QLabel(self)
        pixmap = QPixmap(os.environ[DMF_HOME] + HEADER_PATH)
        image_label.setPixmap(pixmap)
        layout.addWidget(image_label)
        layout.addLayout(grid_layout)
        layout.addWidget(buttons)
        layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

    def getUsername(self):
        return str(self.user.text())

    def getPassword(self):
        return str(self.password.text())

    def getIsSaveInfo(self):
        return self.is_save_info.isChecked()

    @staticmethod
    def getCredentials(
            user,
            password,
            user_label,
            password_label,
            save_option=True,
            parent=None):
        dialog = LoginDialog(save_option, parent)
        dialog.user.setText(user)
        dialog.password.setText(password)
        if user_label is not None:
            dialog.user_label.setText(user_label)
        if password_label is not None:
            dialog.password_label.setText(password_label)

        result = dialog.exec_()
        return (dialog.getUsername(),
                dialog.getPassword(),
                dialog.getIsSaveInfo(),
                result == QDialog.Accepted)
