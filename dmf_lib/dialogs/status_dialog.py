from PySide.QtGui import QDialog
from PySide.QtGui import QDialogButtonBox
from PySide.QtGui import QLabel
from PySide.QtGui import QLayout
from PySide.QtGui import QPalette
from PySide.QtGui import QVBoxLayout
from PySide.QtCore import Qt


class StatusDialog(QDialog):
    def __init__(
            self,
            status,
            button_mode=False,
            use_padding=False,
            parent=None):
        super(StatusDialog, self).__init__(parent)

        layout = QVBoxLayout(self)
        padding = '     '

        label = QLabel(self)
        if use_padding:
            label.setText(padding + status + padding)
        else:
            label.setText(status)

        layout.addWidget(label)
        label.setStyleSheet("background-color: transparent;")
        label.setStyleSheet("color: #FFFFFF;")

        if button_mode:
            buttons = QDialogButtonBox(QDialogButtonBox.Ok)
            buttons.accepted.connect(self.accept)
            layout.addWidget(buttons)

        layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint | Qt.Dialog)

        pal = QPalette()
        pal.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(pal)
        self.setWindowOpacity(0.85)
        self.setAttribute(Qt.WA_DeleteOnClose)  # Delete Dialog on close

    @staticmethod
    def displayStatus(status, parent=None):
        dialog = StatusDialog(status, True, False, parent)
        dialog.exec_()
