# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'uq\stopEnsembleDialog_UI.ui'
#
# Created: Mon Jul 27 11:42:54 2015
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_stopEnsembleDialog(object):
    def setupUi(self, stopEnsembleDialog):
        stopEnsembleDialog.setObjectName("stopEnsembleDialog")
        stopEnsembleDialog.resize(416, 161)
        self.verticalLayout = QtGui.QVBoxLayout(stopEnsembleDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtGui.QLabel(stopEnsembleDialog)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.terminateButton = QtGui.QPushButton(stopEnsembleDialog)
        self.terminateButton.setMinimumSize(QtCore.QSize(250, 0))
        self.terminateButton.setObjectName("terminateButton")
        self.horizontalLayout.addWidget(self.terminateButton)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem3 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem3)
        self.disconnectButton = QtGui.QPushButton(stopEnsembleDialog)
        self.disconnectButton.setMinimumSize(QtCore.QSize(250, 0))
        self.disconnectButton.setObjectName("disconnectButton")
        self.horizontalLayout_2.addWidget(self.disconnectButton)
        spacerItem4 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem4)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem5 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem5)
        self.continueButton = QtGui.QPushButton(stopEnsembleDialog)
        self.continueButton.setMinimumSize(QtCore.QSize(250, 0))
        self.continueButton.setObjectName("continueButton")
        self.horizontalLayout_3.addWidget(self.continueButton)
        spacerItem6 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem6)
        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.retranslateUi(stopEnsembleDialog)
        QtCore.QMetaObject.connectSlotsByName(stopEnsembleDialog)

    def retranslateUi(self, stopEnsembleDialog):
        stopEnsembleDialog.setWindowTitle(QtGui.QApplication.translate("stopEnsembleDialog", "Stop Ensemble", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("stopEnsembleDialog", "Stop ensemble?", None, QtGui.QApplication.UnicodeUTF8))
        self.terminateButton.setText(QtGui.QApplication.translate("stopEnsembleDialog", "Terminate Jobs", None, QtGui.QApplication.UnicodeUTF8))
        self.disconnectButton.setText(QtGui.QApplication.translate("stopEnsembleDialog", "Disconnect From Turbine", None, QtGui.QApplication.UnicodeUTF8))
        self.continueButton.setText(QtGui.QApplication.translate("stopEnsembleDialog", "Continue Running", None, QtGui.QApplication.UnicodeUTF8))

