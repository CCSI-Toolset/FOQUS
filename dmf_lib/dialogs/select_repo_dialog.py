from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLayout
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QRadioButton
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from dmf_lib.gui.path import FILETYPE_IMAGE_PATH
from dmf_lib.gui.path import GREEN
from dmf_lib.gui.path import RED
from dmf_lib.common.common import DMF_LITE_REPO_NAME


class SelectRepoDialog(QDialog):
    def __init__(self, parent=None):
        super(SelectRepoDialog, self).__init__(parent)
        self.setWindowTitle("Select Repository")

        layout = QVBoxLayout(self)
        self.grid_layout = QGridLayout()

        self.label = QLabel(self)
        self.label.setText("Data Management servers found. Please select one:")

        # OK and Cancel buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.grid_layout.addWidget(self.label, 0, 0)
        layout.addLayout(self.grid_layout)
        layout.addWidget(self.buttons)
        layout.setSizeConstraint(QLayout.SetFixedSize)

    @staticmethod
    def getDialog(
            repo_name_list,
            status_list,
            dmf_home,
            show_dmf_lite=False,
            parent=None):
        dialog = SelectRepoDialog(parent)
        radio_list = []

        green_status_url = dmf_home + FILETYPE_IMAGE_PATH + GREEN
        red_status_url = dmf_home + FILETYPE_IMAGE_PATH + RED

        for i in xrange(len(repo_name_list)):
            radio = QRadioButton(dialog)
            radio.setText(repo_name_list[i])

            indicator = QLabel()
            indicator.setGeometry(5, 5, 5, 5)
            if status_list[i] != 200:
                indicator.setPixmap(QPixmap(red_status_url))
            else:
                indicator.setPixmap(QPixmap(green_status_url))
            dialog.grid_layout.addWidget(radio, i+1, 0)
            dialog.grid_layout.addWidget(indicator, i+1, 1)
            radio_list.append(radio)
            if i == 0:
                radio.setChecked(True)

        # Local filesystem
        if show_dmf_lite:
            radio = QRadioButton(dialog)
            radio.setText(DMF_LITE_REPO_NAME)

            indicator = QLabel()
            indicator.setGeometry(5, 5, 5, 5)
            indicator.setPixmap(QPixmap(green_status_url))

            dialog.grid_layout.addWidget(radio, len(repo_name_list)+1, 0)
            dialog.grid_layout.addWidget(indicator, len(repo_name_list)+1, 1)
            radio_list.append(radio)
            if not repo_name_list:
                radio.setChecked(True)

        # Helper function to overwrite toggle action
        def overwriteToggle():
            radio_list[0].setChecked(True)

        if len(radio_list) == 1:
            dialog.label.setText(
                "Data Management server found. Please select:")
            radio_list[0].clicked.connect(overwriteToggle)

        result = dialog.exec_()

        index = 0
        for r in radio_list:
            if r.isChecked():
                if index < len(repo_name_list):
                    repo_name = repo_name_list[index]
                else:
                    repo_name = r.text()
                break
            else:
                index += 1

        #  Delete Dialog on close
        dialog.setAttribute(Qt.WA_DeleteOnClose)
        dialog.close()
        return (result == QDialog.Accepted, index, repo_name)
