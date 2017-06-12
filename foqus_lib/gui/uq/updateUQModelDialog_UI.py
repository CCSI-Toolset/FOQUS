# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'updateUQModelDialog_UI.ui'
#
# Created: Tue Jun 09 16:59:37 2015
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_updateUQModelDialog(object):
    def setupUi(self, updateUQModelDialog):
        updateUQModelDialog.setObjectName("updateUQModelDialog")
        updateUQModelDialog.resize(534, 360)
        updateUQModelDialog.setModal(True)
        self.verticalLayout = QtGui.QVBoxLayout(updateUQModelDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.nodeRadioButton = QtGui.QRadioButton(updateUQModelDialog)
        self.nodeRadioButton.setObjectName("nodeRadioButton")
        self.verticalLayout.addWidget(self.nodeRadioButton)
        self.line = QtGui.QFrame(updateUQModelDialog)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName("line")
        self.verticalLayout.addWidget(self.line)
        self.emulatorRadioButton = QtGui.QRadioButton(updateUQModelDialog)
        self.emulatorRadioButton.setObjectName("emulatorRadioButton")
        self.verticalLayout.addWidget(self.emulatorRadioButton)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        spacerItem = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.dataFileLabel = QtGui.QLabel(updateUQModelDialog)
        self.dataFileLabel.setObjectName("dataFileLabel")
        self.horizontalLayout_2.addWidget(self.dataFileLabel)
        self.dataFileEdit = QtGui.QLineEdit(updateUQModelDialog)
        self.dataFileEdit.setReadOnly(True)
        self.dataFileEdit.setObjectName("dataFileEdit")
        self.horizontalLayout_2.addWidget(self.dataFileEdit)
        self.browseButton = QtGui.QPushButton(updateUQModelDialog)
        self.browseButton.setObjectName("browseButton")
        self.horizontalLayout_2.addWidget(self.browseButton)
        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 1, 1, 1)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.outputLabel = QtGui.QLabel(updateUQModelDialog)
        self.outputLabel.setObjectName("outputLabel")
        self.horizontalLayout_3.addWidget(self.outputLabel)
        self.outputList = QtGui.QListWidget(updateUQModelDialog)
        self.outputList.setObjectName("outputList")
        self.horizontalLayout_3.addWidget(self.outputList)
        self.gridLayout.addLayout(self.horizontalLayout_3, 1, 1, 1, 1)
        self.fileStatsLabel = QtGui.QLabel(updateUQModelDialog)
        self.fileStatsLabel.setObjectName("fileStatsLabel")
        self.gridLayout.addWidget(self.fileStatsLabel, 2, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.buttonBox = QtGui.QDialogButtonBox(updateUQModelDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(updateUQModelDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), updateUQModelDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), updateUQModelDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(updateUQModelDialog)

    def retranslateUi(self, updateUQModelDialog):
        updateUQModelDialog.setWindowTitle(QtGui.QApplication.translate("updateUQModelDialog", "Add New Ensemble - Model Selection", None, QtGui.QApplication.UnicodeUTF8))
        self.nodeRadioButton.setToolTip(QtGui.QApplication.translate("updateUQModelDialog", "Choose this option if your simulation model\n"
"is a node in the flowsheet.", None, QtGui.QApplication.UnicodeUTF8))
        self.nodeRadioButton.setText(QtGui.QApplication.translate("updateUQModelDialog", "Use flowsheet", None, QtGui.QApplication.UnicodeUTF8))
        self.emulatorRadioButton.setToolTip(QtGui.QApplication.translate("updateUQModelDialog", "Choose this option if you want to train a response\n"
"surface that emulates your actual simulation model.\n"
"You will need training data saved as a PSUADE file.\n"
"If you\'d like to change the response surface type and/or\n"
"Legendre order, edit these options directly in the file.", None, QtGui.QApplication.UnicodeUTF8))
        self.emulatorRadioButton.setText(QtGui.QApplication.translate("updateUQModelDialog", "Use emulator (Response Surface)", None, QtGui.QApplication.UnicodeUTF8))
        self.dataFileLabel.setText(QtGui.QApplication.translate("updateUQModelDialog", "Data File:", None, QtGui.QApplication.UnicodeUTF8))
        self.browseButton.setText(QtGui.QApplication.translate("updateUQModelDialog", "Browse...", None, QtGui.QApplication.UnicodeUTF8))
        self.outputLabel.setText(QtGui.QApplication.translate("updateUQModelDialog", "Select Output(s) of Interest:", None, QtGui.QApplication.UnicodeUTF8))
        self.fileStatsLabel.setText(QtGui.QApplication.translate("updateUQModelDialog", "Response Surface Type:\n"
"Legendre Order:", None, QtGui.QApplication.UnicodeUTF8))

