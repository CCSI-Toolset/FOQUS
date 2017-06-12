# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'basicDataFrame_UI.ui'
#
# Created: Thu Feb  4 11:51:48 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_basicDataFrame(object):
    def setupUi(self, basicDataFrame):
        basicDataFrame.setObjectName("basicDataFrame")
        basicDataFrame.resize(995, 835)
        basicDataFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        basicDataFrame.setFrameShadow(QtGui.QFrame.Raised)
        self.vboxlayout_0 = QtGui.QVBoxLayout(basicDataFrame)
        self.vboxlayout_0.setObjectName("vboxlayout_0")
        self.groupBox = QtGui.QGroupBox(basicDataFrame)
        self.groupBox.setObjectName("groupBox")
        self.gridlayout_1 = QtGui.QGridLayout(self.groupBox)
        self.gridlayout_1.setObjectName("gridlayout_1")
        self.selector_label = QtGui.QLabel(self.groupBox)
        self.selector_label.setObjectName("selector_label")
        self.gridlayout_1.addWidget(self.selector_label, 0, 0, 1, 1)
        self.selected_folder = QtGui.QLineEdit(self.groupBox)
        self.selected_folder.setReadOnly(True)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(False)
        self.selected_folder.setFont(font)
        self.selected_folder.setObjectName("selected_folder")
        self.gridlayout_1.addWidget(self.selected_folder, 0, 1, 1, 1)
        self.folderBrowse_button = QtGui.QPushButton(self.groupBox)
        self.folderBrowse_button.setFixedWidth(100)
        self.folderBrowse_button.setObjectName("folderBrowse_button")
        self.gridlayout_1.addWidget(self.folderBrowse_button, 0, 2, 1, 1)
        self.vboxlayout_0.addWidget(self.groupBox)
        self.ingest_button = QtGui.QPushButton(basicDataFrame)
        self.ingest_button.setFixedWidth(150)
        self.ingest_button.setObjectName("ingest_button")
        self.vboxlayout_0.addWidget(self.ingest_button)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout_0.addItem(spacerItem)

        self.retranslateUi(basicDataFrame)
        QtCore.QMetaObject.connectSlotsByName(basicDataFrame)

    def retranslateUi(self, basicDataFrame):
        basicDataFrame.setWindowTitle(QtGui.QApplication.translate("basicDataFrame", "Frame", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("basicDataFrame", "Ingest Basic Data Models", None, QtGui.QApplication.UnicodeUTF8))
        self.selector_label.setText(QtGui.QApplication.translate("basicDataFrame", " Basic Data Directory", None, QtGui.QApplication.UnicodeUTF8))
        self.folderBrowse_button.setText(QtGui.QApplication.translate("basicDataFrame", "Browse...", None, QtGui.QApplication.UnicodeUTF8))
        self.ingest_button.setText(QtGui.QApplication.translate("basicDataFrame", "Ingest", None, QtGui.QApplication.UnicodeUTF8))

