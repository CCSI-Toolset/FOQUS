#################################################################################
# FOQUS Copyright (c) 2012 - 2023, by the software owners: Oak Ridge Institute
# for Science and Education (ORISE), TRIAD National Security, LLC., Lawrence
# Livermore National Security, LLC., The Regents of the University of
# California, through Lawrence Berkeley National Laboratory, Battelle Memorial
# Institute, Pacific Northwest Division through Pacific Northwest National
# Laboratory, Carnegie Mellon University, West Virginia University, Boston
# University, the Trustees of Princeton University, The University of Texas at
# Austin, URS Energy & Construction, Inc., et al.  All rights reserved.
#
# Please see the file LICENSE.md for full copyright and license information,
# respectively. This file is also available online at the URL
# "https://github.com/CCSI-Toolset/FOQUS".
#################################################################################
import sys
from PyQt5 import QtGui, QtCore, QtWidgets


class Dialog(QtWidgets.QDialog):  # QtWidgets.QMainWindow):
    def __init__(self, title, parent=None, signal=None):
        super(Dialog, self).__init__(parent)
        self.button = QtWidgets.QPushButton("Push")
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.addWidget(self.button)
        self.button.clicked.connect(self.popup)
        self.setWindowTitle(title)
        self.resize(300, 200)
        self.closeSignal = signal

    def popup(self):
        self.d = Dialog("Dialog 2")
        self.d.show()

    def closeEvent(self, event):
        if self.closeSignal:
            self.closeSignal.emit(5)
        event.accept()


class MainWindow(QtWidgets.QMainWindow):
    valueSignal = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.button = QtWidgets.QPushButton("Push")
        self.setCentralWidget(self.button)
        self.button.clicked.connect(self.popup)
        self.valueSignal.connect(self.printValue)

    def popup(self):
        print("pushed")
        self.d = Dialog("Dialog 1", self, signal=self.valueSignal)
        # self.d.exec_()
        # self.d.setModal(True)
        self.d.show()

    def printValue(self, value):
        self.value = value
        print(self.value)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    w = MainWindow()
    w.resize(250, 150)
    w.move(300, 300)
    w.setWindowTitle("Simple")
    w.show()

    sys.exit(app.exec_())
