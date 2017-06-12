from PySide.QtGui import *
from PySide.QtCore import *
from dmf_lib.common.common import *

class GraphPopupDialog(QDialog):
    def __init__(self, parent = None):
        super(GraphPopupDialog, self).__init__(parent)

        self.dock = parent.root
        self.verbose = self.dock.verbose

        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.grid_layout = QGridLayout()

        self.dock_button = QPushButton("Dock dependency graph", self)
        self.dock_button.setMaximumWidth(180)
        self.dock_button.clicked.connect(self.close)

        self.view_label = QLabel(self)
        self.view_label.setText("Dependency Graph")
        self.view_label.setStyleSheet("color: #767676;")

        self.layout.addLayout(self.grid_layout)
        self.grid_layout.addWidget(self.view_label, 0, 0)
        self.grid_layout.addWidget(self.dock_button, 0, 1)
#        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

    def addView(self, view):
        self.view = view
        self.layout.addWidget(self.view)
        self.dock.layout.removeWidget(self.view)
        self.view.reload()

    def closeEvent(self, event):
        if self.verbose:
            print self.__class__.__name__,PRINT_COLON,"Close event invoked."
        if self.isVisible():
            if self.verbose:
                print self.__class__.__name__,PRINT_COLON,"Docking graph."
            self.layout.removeWidget(self.view)
            self.dock.view.undock_button.show()
            self.dock.view.view_label.show()
            self.dock.view.layout.addWidget(self.view)
            self.view.reload()
        super(GraphPopupDialog, self).closeEvent(event)

    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key_Escape:
            if self.verbose:
                print self.__class__.__name__,PRINT_COLON,"Escape button clicked."
            self.close()

    def resizeEvent(self, event):
        if self.verbose:
            print self.__class__.__name__,PRINT_COLON,"Resize event."
        self.view.reload()
