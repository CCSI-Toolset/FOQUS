# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'optimization\optMessageWindow_UI.ui'
#
# Created: Mon Apr 14 15:52:43 2014
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_optMessageWindow(object):
    def setupUi(self, optMessageWindow):
        optMessageWindow.setObjectName("optMessageWindow")
        optMessageWindow.resize(400, 326)
        self.verticalLayout = QtGui.QVBoxLayout(optMessageWindow)
        self.verticalLayout.setObjectName("verticalLayout")
        self.msgTextBrowser = QtGui.QTextBrowser(optMessageWindow)
        self.msgTextBrowser.setMinimumSize(QtCore.QSize(100, 0))
        self.msgTextBrowser.setObjectName("msgTextBrowser")
        self.verticalLayout.addWidget(self.msgTextBrowser)
        self.statusLine = QtGui.QLineEdit(optMessageWindow)
        self.statusLine.setReadOnly(True)
        self.statusLine.setObjectName("statusLine")
        self.verticalLayout.addWidget(self.statusLine)
        self.clearMsgButton = QtGui.QPushButton(optMessageWindow)
        self.clearMsgButton.setObjectName("clearMsgButton")
        self.verticalLayout.addWidget(self.clearMsgButton)

        self.retranslateUi(optMessageWindow)
        QtCore.QMetaObject.connectSlotsByName(optMessageWindow)

    def retranslateUi(self, optMessageWindow):
        optMessageWindow.setWindowTitle(QtGui.QApplication.translate("optMessageWindow", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.clearMsgButton.setText(QtGui.QApplication.translate("optMessageWindow", "Clear", None, QtGui.QApplication.UnicodeUTF8))

