from PySide.QtGui import QLabel
from PySide.QtGui import QDialog
from PySide.QtGui import QDialogButtonBox
from PySide.QtGui import QComboBox
from PySide.QtGui import QLayout
from PySide.QtGui import QVBoxLayout
from PySide.QtGui import QGridLayout
from PySide.QtCore import Qt
from dmf_lib.common.common import PWC


class SelectVersionDialog(QDialog):
    def __init__(self, parent=None):
        super(SelectVersionDialog, self).__init__(parent)

        layout = QVBoxLayout(self)
        grid_layout = QGridLayout()

        self.root = parent
        self.verbose = self.root.verbose
        self.version_label = QLabel(self)

        self.version_list = []
        self.versions = QComboBox(self)
        self.version_label.setText("Please select a version to retrieve:")

        # OK and Cancel buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        grid_layout.addWidget(self.version_label, 0, 0)
        grid_layout.addWidget(self.versions, 1, 0)

        layout.addLayout(grid_layout)
        layout.addWidget(self.buttons)
        layout.setSizeConstraint(QLayout.SetFixedSize)

    def setVersions(self, ver_list):
        for v in ver_list:
            if v != PWC:
                self.versions.addItem(v, v)
        self.versions.setCurrentIndex(0)
        self.version_list = ver_list

    def getSelectedVersion(self):
        return str(self.version_list[self.versions.currentIndex()])

    @staticmethod
    def getVersion(ver_list, parent=None):
        dialog = SelectVersionDialog(parent)
        dialog.setWindowTitle("Select Retrieve Version")

        if ver_list is None or len(ver_list) == 0:
            if dialog.verbose:
                print "Error case: Version list does not exist or is empty."
            return None, False
        elif len(ver_list) == 1:
            return ver_list[0], QDialog.Accepted
        else:
            if len(ver_list) == 2 and ver_list[0] == PWC:
                return ver_list[1], QDialog.Accepted
            dialog.setVersions(ver_list)
            result = dialog.exec_()
            return dialog.getSelectedVersion(), result
