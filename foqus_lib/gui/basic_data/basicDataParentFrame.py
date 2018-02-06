import sys
import os

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow
mypath = os.path.dirname(__file__)
_basicDataParentFrameUI, _basicDataParentFrame = \
        uic.loadUiType(os.path.join(mypath, "basicDataParentFrame_UI.ui"))

class basicDataParentFrame(_basicDataParentFrame, _basicDataParentFrameUI):
    format = '%.5f'  # numeric format for table entries in UQ Toolbox

    def __init__(self, parent=None):
        super(basicDataParentFrame, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)
        self.dmfGroup.hide()
        self.solventFitFrame.init(parent=self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    MainWindow = QMainWindow(parent=None)

    MainFrame = basicDataParentFrame()
    MainWindow.setCentralWidget(MainFrame)

    MainWindow.show()
    sys.exit(app.exec_())
