# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main\saveMetadataDialog_UI.ui'
#
# Created: Thu Aug 07 09:19:29 2014
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_saveMetadataDialog(object):
    def setupUi(self, saveMetadataDialog):
        saveMetadataDialog.setObjectName("saveMetadataDialog")
        saveMetadataDialog.resize(626, 294)
        self.verticalLayout = QtGui.QVBoxLayout(saveMetadataDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_2 = QtGui.QLabel(saveMetadataDialog)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.changeLogEntryText = QtGui.QTextEdit(saveMetadataDialog)
        self.changeLogEntryText.setObjectName("changeLogEntryText")
        self.verticalLayout.addWidget(self.changeLogEntryText)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.cancelButton = QtGui.QPushButton(saveMetadataDialog)
        self.cancelButton.setObjectName("cancelButton")
        self.horizontalLayout_3.addWidget(self.cancelButton)
        self.continueButton = QtGui.QPushButton(saveMetadataDialog)
        self.continueButton.setObjectName("continueButton")
        self.horizontalLayout_3.addWidget(self.continueButton)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.label_2.setBuddy(self.changeLogEntryText)

        self.retranslateUi(saveMetadataDialog)
        QtCore.QMetaObject.connectSlotsByName(saveMetadataDialog)

    def retranslateUi(self, saveMetadataDialog):
        saveMetadataDialog.setWindowTitle(QtGui.QApplication.translate("saveMetadataDialog", "Saving Session -- Metadata Entry", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("saveMetadataDialog", "Change Log Entry:", None, QtGui.QApplication.UnicodeUTF8))
        self.cancelButton.setText(QtGui.QApplication.translate("saveMetadataDialog", "Cancel Save", None, QtGui.QApplication.UnicodeUTF8))
        self.continueButton.setText(QtGui.QApplication.translate("saveMetadataDialog", "Continue", None, QtGui.QApplication.UnicodeUTF8))

