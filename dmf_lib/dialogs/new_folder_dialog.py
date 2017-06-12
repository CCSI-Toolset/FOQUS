import os
from PySide.QtGui import QDialog
from PySide.QtGui import QGridLayout
from PySide.QtGui import QVBoxLayout
from PySide.QtGui import QLabel
from PySide.QtGui import QTextEdit
from PySide.QtGui import QLineEdit
from PySide.QtGui import QComboBox
from PySide.QtGui import QDialogButtonBox
from PySide.QtGui import QIcon
from PySide.QtCore import Qt

# Import global variables
from dmf_lib.gui.path import CCSI
from dmf_lib.common.common import DMF_HOME


class FolderDialog(QDialog):
    def __init__(self, parent=None):
        super(FolderDialog, self).__init__(parent)

        layout = QVBoxLayout(self)
        grid_layout = QGridLayout()

        self.folder_label = QLabel(self)
        self.folder_label.setText("Name:*")
        self.folder_name = QLineEdit(self)

        self.description_label = QLabel(self)
        self.description_label.setText("Description:")
        self.description = QTextEdit(self)

        self.fixed_form_label = QLabel(self)
        self.fixed_form_label.setText("Fixed Form:")
        self.fixed_form = QComboBox(self)
        self.fixed_form_values = ['False', 'True']
        for v in self.fixed_form_values:
            self.fixed_form.addItem(v, v)

        grid_layout.addWidget(self.folder_label, 0, 0)
        grid_layout.addWidget(self.folder_name, 1, 0)
        grid_layout.addWidget(self.description_label, 2, 0)
        grid_layout.addWidget(self.description, 3, 0)
        grid_layout.addWidget(self.fixed_form_label, 4, 0)
        grid_layout.addWidget(self.fixed_form, 5, 0)

        # OK and Cancel buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout.addLayout(grid_layout)
        layout.addWidget(self.buttons)

    def getFolderName(self):
        return str(self.folder_name.text())

    def getDescription(self):
        return str(self.description.toPlainText())

    def getFixedForm(self):
        fixed_form = self.fixed_form_values[self.fixed_form.currentIndex()]
        return False if fixed_form == 'False' else True

    def setFolderName(self, name):
        if name:
            self.folder_name.setText(name)

    def setFolderDescription(self, description):
        if description:
            self.description.setText(description)

    def setFolderFixedForm(self, form):
        if form:
            self.fixed_form.setCurrentIndex(
                self.fixed_form_values.index(str(form)))
        else:
            self.fixed_form.setCurrentIndex(0)

    # static method to create the dialog and return (folder_name, accepted)
    @staticmethod
    def getNewFolderProperties(parent=None):
        dialog = FolderDialog(parent)
        dialog.setWindowTitle("New Folder Dialog")
        dialog.setWindowIcon(QIcon(os.environ[DMF_HOME] + CCSI))
        dialog.fixed_form_label.setVisible(False)
        dialog.fixed_form.setVisible(False)
        result = dialog.exec_()
        folder_name = dialog.getFolderName()
        description = dialog.getDescription()
        fixed_form = dialog.getFixedForm()
        dialog.setAttribute(Qt.WA_DeleteOnClose)  # Delete Dialog on close
        dialog.close()
        return (folder_name,
                description,
                fixed_form,
                result == QDialog.Accepted)

    # static method to create the dialog and return (folder_name, accepted)
    @staticmethod
    def setFolderProperties(folder_name, description, form, parent=None):
        dialog = FolderDialog(parent)
        dialog.setWindowTitle("Edit Folder Dialog")
        dialog.setWindowIcon(QIcon(os.environ[DMF_HOME] + CCSI))
        dialog.setFolderName(folder_name)
        dialog.setFolderDescription(description)
        dialog.setFolderFixedForm(form)
        result = dialog.exec_()
        folder_name = dialog.getFolderName()
        description = dialog.getDescription()
        fixed_form = dialog.getFixedForm()
        dialog.setAttribute(Qt.WA_DeleteOnClose)  # Delete Dialog on close
        dialog.close()
        return (folder_name,
                description,
                fixed_form,
                result == QDialog.Accepted)
