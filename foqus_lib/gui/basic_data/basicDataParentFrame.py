import sys
from PySide.QtGui import (
    QFrame,
    QMainWindow,
    QApplication)
from basicDataParentFrame_UI import Ui_Frame


class basicDataParentFrame(QFrame, Ui_Frame):
    format = '%.5f'  # numeric format for table entries in UQ Toolbox

    def __init__(self, showDMF, parent=None):
        super(basicDataParentFrame, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)
        if not showDMF:
            self.dmfGroup.hide()
        self.solventFitFrame.init(parent=self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    MainWindow = QMainWindow(parent=None)

    MainFrame = basicDataParentFrame()
    MainWindow.setCentralWidget(MainFrame)

    MainWindow.show()
    sys.exit(app.exec_())
