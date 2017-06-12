from PySide.QtGui import QDialog
from PySide.QtGui import QLabel
from PySide.QtGui import QGridLayout
from PySide.QtGui import QVBoxLayout
from PySide.QtGui import QLineEdit
from PySide.QtGui import QTextEdit
from PySide.QtGui import QComboBox
from PySide.QtGui import QDialogButtonBox
from PySide.QtGui import QRadioButton
from PySide.QtGui import QPushButton

from PySide.QtCore import Qt
from dmf_lib.dialogs.status_dialog import StatusDialog
from dmf_lib.dialogs.edit_parents_dialog import EditParentsDialog
from dmf_lib.common.common import PRINT_COLON


class SaveFileDialog(QDialog):
    def __init__(self, parent=None):
        super(SaveFileDialog, self).__init__(parent)
        if parent:
            # Inherit from parent
            self.root = parent
            self.DMF_HOME = self.root.DMF_HOME
            self.verbose = self.root.verbose
            try:
                self.username = self.root.user
                self.session = self.root.session
                self.data_operator = self.root.data_op
                self.data_folder_map = self.root.data_folder_map
                self.data_model_vars = self.root.data_model_vars
                self.basetype_id = self.root.basetype_id
                self.id = None
            except:
                # Ignore if fail
                pass

        layout = QVBoxLayout(self)
        grid_layout = QGridLayout()

        self.display_label = QLabel(self)
        self.display_label.setText("Display Name:*")
        self.display_name = QLineEdit(self)

        self.original_name_label = QLabel(self)
        self.original_name_label.setText("Original File Name:")
        self.original_name = QLineEdit(self)

        self.description_label = QLabel(self)
        self.description_label.setText("Description:")
        self.description = QTextEdit(self)

        self.mimetype_label = QLabel(self)
        self.mimetype_label.setText("Mimetype:*")

        try:
            self.mimetype_dict = parent.mimetype_dict
            self.mimetype = QComboBox(self)
            for k in self.mimetype_dict:
                self.mimetype.addItem(k, self.mimetype_dict[k])
        except:
            self.mimetype = QLineEdit(self)

        self.external_label = QLabel(self)
        self.external_label.setText("External URL:")
        self.external = QLineEdit(self)

        self.version_req_label = QLabel(self)
        self.version_req_label.setText("Version Requirements:")
        self.version_req = QLineEdit(self)

        self.confidence_label = QLabel(self)
        self.confidence_label.setText("Confidence:")
        self.confidence = QComboBox(self)
        self.confidence_values = ['experimental', 'testing', 'production']
        for v in self.confidence_values:
            self.confidence.addItem(v, v)

        self.parents_edit_button = QPushButton("Edit Parents")
        self.parents_edit_button.clicked.connect(self.editParentsClicked)

        grid_layout.addWidget(self.display_label, 0, 0)
        grid_layout.addWidget(self.display_name, 1, 0)
        grid_layout.addWidget(self.original_name_label, 2, 0)
        grid_layout.addWidget(self.original_name, 3, 0)
        grid_layout.addWidget(self.description_label, 4, 0)
        grid_layout.addWidget(self.description, 5, 0)
        grid_layout.addWidget(self.mimetype_label, 6, 0)
        grid_layout.addWidget(self.mimetype, 7, 0)
        grid_layout.addWidget(self.external_label, 8, 0)
        grid_layout.addWidget(self.external, 9, 0)
        grid_layout.addWidget(self.version_req_label, 10, 0)
        grid_layout.addWidget(self.version_req, 11, 0)
        grid_layout.addWidget(self.confidence_label, 12, 0)
        grid_layout.addWidget(self.confidence, 13, 0)
        grid_layout.addWidget(self.parents_edit_button, 14, 0)

        # OK and Cancel buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout.addLayout(grid_layout)
        layout.addWidget(self.buttons)

    def editParentsClicked(self):
        if self.verbose:
            print self.__class__.__name__, \
                PRINT_COLON, "Edit parents clicked."
        self.setEnabled(False)
        result, parent_ids = EditParentsDialog.displayParents(
            id=self.id,
            parent_ids=self.parent_ids,
            tree_model=self.root.default_model,
            parent=self)
        if result:
            self.parent_ids = parent_ids
        self.setEnabled(True)

    def getDisplayName(self):
        return str(self.display_name.text())

    def getOriginalName(self):
        return str(self.original_name.text())

    def getDescription(self):
        return str(self.description.toPlainText())

    def getExternalUrl(self):
        return str(self.external.text())

    def getMimeType(self):
        try:
            return str(
                self.mimetype_dict.values()[self.mimetype.currentIndex()])
        except:
            return str(self.mimetype.text())

    def getVersionRequirements(self):
        return str(self.version_req.text())

    def getConfidence(self):
        return str(self.confidence_values[self.confidence.currentIndex()])

    def getParentsID(self):
        return self.parent_ids

    def setDisplayName(self, display_name):
        self.display_name.setText(display_name)

    def setOriginalName(self, original_name):
        self.original_name.setText(original_name)

    def setDescription(self, description):
        self.description.setPlainText(description)

    def setExternalUrl(self, external):
        self.external.setText(external)

    def setMimeType(self, mimetype):
        try:
            if mimetype in self.mimetype_dict.values():
                self.mimetype.setCurrentIndex(
                    self.mimetype_dict.values().index(mimetype))
            else:
                StatusDialog.displayStatus(
                    "File has unknown mimetype: " + str(mimetype))
        except:
            self.mimetype.setText(mimetype)

    def setVersionRequirements(self, version_req):
        self.version_req.setText(version_req)

    def setConfidence(self, confidence):
        if confidence in self.confidence_values:
            self.confidence.setCurrentIndex(
                self.confidence_values.index(confidence))
        else:
            # Should never come here, but if so, default to experimental
            StatusDialog.displayStatus(
                "File has unknown confidence type: " + str(confidence))
            self.confidence.setCurrentIndex(0)

    def setParents(self, parents):
        self.parent_ids = parents
        if parents is None:
            self.parents_edit_button.setEnabled(False)

    def setID(self, id):
        self.id = id

    # static method to create the dialog and return (folder_name, accepted)
    @staticmethod
    def getSaveFileProperties(
            dialog_title,
            display_name,
            original_name,
            description,
            mimetype,
            external,
            confidence,
            version_requirements,
            parent_ids=None,
            id=None,
            parent=None):
        dialog = SaveFileDialog(parent)
        dialog.setWindowTitle(dialog_title)

        if type(display_name) is tuple:
            dialog.setDisplayName(display_name[0])
            dialog.display_name.setDisabled(display_name[1])
            dialog.display_name.setStyleSheet("background-color: lightgray;")
        else:
            if display_name != '':
                dialog.setDisplayName(display_name)
        if original_name != '':
            dialog.setOriginalName(original_name)
        if description != '':
            dialog.setDescription(description)
        if mimetype != '':
            dialog.setMimeType(mimetype)
        if external != '':
            dialog.setExternalUrl(external)
        if confidence != '':
            dialog.setConfidence(confidence)
        if version_requirements != '':
            dialog.setVersionRequirements(version_requirements)
        if parent_ids != '':
            dialog.setParents(parent_ids)
        if id != '':
            dialog.setID(id)

        result = dialog.exec_()

        display_name = dialog.getDisplayName()
        original_name = dialog.getOriginalName()
        description = dialog.getDescription()
        external = dialog.getExternalUrl()
        mimetype = dialog.getMimeType()
        version_req = dialog.getVersionRequirements()
        confidence = dialog.getConfidence()
        parent_ids = dialog.getParentsID()
        dialog.setAttribute(Qt.WA_DeleteOnClose)  # Delete Dialog on close
        dialog.close()

        return (display_name,
                original_name,
                description,
                external,
                mimetype,
                version_req,
                confidence,
                parent_ids,
                result == QDialog.Accepted)


class SaveOverwriteFileDialog(QDialog):

    def __init__(self, parent=None):
        super(SaveOverwriteFileDialog, self).__init__(parent)

        layout = QVBoxLayout(self)
        grid_layout = QGridLayout()

        self.label = QLabel(self)
        self.label.setText(
            "File exists! Please choose one of the following actions:")

        self.radio1 = QRadioButton(self)
        self.radio2 = QRadioButton(self)
        self.radio3 = QRadioButton(self)

        self.radio1.setText("New major version")
        self.radio2.setText("New minor version")
        self.radio3.setText("Overwrite current version")
        self.radio3.hide()
        self.radio1.setChecked(True)

        # OK and Cancel buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        grid_layout.addWidget(self.label, 0, 0)
        grid_layout.addWidget(self.radio1, 1, 0)
        grid_layout.addWidget(self.radio2, 2, 0)
        grid_layout.addWidget(self.radio3, 3, 0)

        layout.addLayout(grid_layout)
        layout.addWidget(self.buttons)

    @staticmethod
    def getSaveFileProperties(dialog_title, parent=None):
        dialog = SaveOverwriteFileDialog(parent)
        dialog.setWindowTitle(dialog_title)
        result = dialog.exec_()

        isMajorVersion = False
        overwrite = None

        if dialog.radio1.isChecked():
            isMajorVersion = True
        elif dialog.radio2.isChecked():
            isMajorVersion = False
        else:
            overwrite = True
        dialog.setAttribute(Qt.WA_DeleteOnClose)  # Delete Dialog on close
        dialog.close()
        return (result == QDialog.Accepted, isMajorVersion, overwrite)


class SaveLocalOverwriteFileDialog(QDialog):
    def __init__(self, parent=None):
        super(SaveLocalOverwriteFileDialog, self).__init__(parent)

        layout = QVBoxLayout(self)
        grid_layout = QGridLayout()

        self.label = QLabel(self)
        self.label.setText("File exists! Do you want to overwrite?")

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        grid_layout.addWidget(self.label, 0, 0)
        layout.addLayout(grid_layout)
        layout.addWidget(self.buttons)

    @staticmethod
    def getSaveFileProperties(parent=None):
        dialog = SaveLocalOverwriteFileDialog(parent)
        result = dialog.exec_()
        return (result == QDialog.Accepted)
