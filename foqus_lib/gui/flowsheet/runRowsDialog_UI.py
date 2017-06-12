# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'flowsheet\runRowsDialog_UI.ui'
#
# Created: Wed Oct 26 08:35:31 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_runRowsDialog(object):
    def setupUi(self, runRowsDialog):
        runRowsDialog.setObjectName("runRowsDialog")
        runRowsDialog.resize(277, 179)
        self.verticalLayout = QtGui.QVBoxLayout(runRowsDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtGui.QLabel(runRowsDialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_2 = QtGui.QLabel(runRowsDialog)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.samplesLine = QtGui.QLineEdit(runRowsDialog)
        self.samplesLine.setReadOnly(True)
        self.samplesLine.setObjectName("samplesLine")
        self.gridLayout.addWidget(self.samplesLine, 0, 1, 1, 1)
        self.successLine = QtGui.QLineEdit(runRowsDialog)
        self.successLine.setReadOnly(True)
        self.successLine.setObjectName("successLine")
        self.gridLayout.addWidget(self.successLine, 1, 1, 1, 1)
        self.label_3 = QtGui.QLabel(runRowsDialog)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.errorLine = QtGui.QLineEdit(runRowsDialog)
        self.errorLine.setReadOnly(True)
        self.errorLine.setObjectName("errorLine")
        self.gridLayout.addWidget(self.errorLine, 2, 1, 1, 1)
        self.label_4 = QtGui.QLabel(runRowsDialog)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 3, 0, 1, 1)
        self.timeLine = QtGui.QLineEdit(runRowsDialog)
        self.timeLine.setReadOnly(True)
        self.timeLine.setObjectName("timeLine")
        self.gridLayout.addWidget(self.timeLine, 3, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        spacerItem = QtGui.QSpacerItem(20, 21, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem1)
        self.disButton = QtGui.QPushButton(runRowsDialog)
        self.disButton.setObjectName("disButton")
        self.horizontalLayout_4.addWidget(self.disButton)
        self.stopButton = QtGui.QPushButton(runRowsDialog)
        self.stopButton.setObjectName("stopButton")
        self.horizontalLayout_4.addWidget(self.stopButton)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.label.setBuddy(self.samplesLine)
        self.label_2.setBuddy(self.successLine)
        self.label_3.setBuddy(self.errorLine)
        self.label_4.setBuddy(self.timeLine)

        self.retranslateUi(runRowsDialog)
        QtCore.QMetaObject.connectSlotsByName(runRowsDialog)

    def retranslateUi(self, runRowsDialog):
        runRowsDialog.setWindowTitle(QtGui.QApplication.translate("runRowsDialog", "Running Table Rows...", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("runRowsDialog", "Samples:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("runRowsDialog", "Success:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("runRowsDialog", "Error:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("runRowsDialog", "Elapsed Time:", None, QtGui.QApplication.UnicodeUTF8))
        self.disButton.setText(QtGui.QApplication.translate("runRowsDialog", "Remote Disconnect", None, QtGui.QApplication.UnicodeUTF8))
        self.stopButton.setText(QtGui.QApplication.translate("runRowsDialog", "Stop", None, QtGui.QApplication.UnicodeUTF8))

