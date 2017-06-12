# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'variableBrowser_UI.ui'
#
# Created: Mon Apr 14 15:52:42 2014
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_variableBrowser(object):
    def setupUi(self, variableBrowser):
        variableBrowser.setObjectName("variableBrowser")
        variableBrowser.resize(524, 356)
        self.verticalLayout = QtGui.QVBoxLayout(variableBrowser)
        self.verticalLayout.setObjectName("verticalLayout")
        self.treeWidget = QtGui.QTreeWidget(variableBrowser)
        self.treeWidget.setObjectName("treeWidget")
        self.verticalLayout.addWidget(self.treeWidget)
        self.varText = QtGui.QLineEdit(variableBrowser)
        self.varText.setReadOnly(True)
        self.varText.setObjectName("varText")
        self.verticalLayout.addWidget(self.varText)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.refreshButton = QtGui.QPushButton(variableBrowser)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(106, 104, 100))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, brush)
        self.refreshButton.setPalette(palette)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setUnderline(True)
        self.refreshButton.setFont(font)
        self.refreshButton.setCursor(QtCore.Qt.PointingHandCursor)
        self.refreshButton.setFlat(True)
        self.refreshButton.setObjectName("refreshButton")
        self.horizontalLayout.addWidget(self.refreshButton)
        self.closeButton = QtGui.QPushButton(variableBrowser)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(106, 104, 100))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, brush)
        self.closeButton.setPalette(palette)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setUnderline(True)
        self.closeButton.setFont(font)
        self.closeButton.setCursor(QtCore.Qt.PointingHandCursor)
        self.closeButton.setFlat(True)
        self.closeButton.setObjectName("closeButton")
        self.horizontalLayout.addWidget(self.closeButton)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(variableBrowser)
        QtCore.QMetaObject.connectSlotsByName(variableBrowser)

    def retranslateUi(self, variableBrowser):
        variableBrowser.setWindowTitle(QtGui.QApplication.translate("variableBrowser", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(0, QtGui.QApplication.translate("variableBrowser", "Node", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(1, QtGui.QApplication.translate("variableBrowser", "Mode", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(2, QtGui.QApplication.translate("variableBrowser", "Variable", None, QtGui.QApplication.UnicodeUTF8))
        self.refreshButton.setText(QtGui.QApplication.translate("variableBrowser", "Refresh", None, QtGui.QApplication.UnicodeUTF8))
        self.closeButton.setText(QtGui.QApplication.translate("variableBrowser", "Close", None, QtGui.QApplication.UnicodeUTF8))

