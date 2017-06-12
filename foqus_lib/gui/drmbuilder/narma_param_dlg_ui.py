# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'narma_param_dlg.ui'
#
# Created: Tue Dec 02 16:31:54 2014
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_narmaParamDlg(object):
    def setupUi(self, narmaParamDlg):
        narmaParamDlg.setObjectName("narmaParamDlg")
        narmaParamDlg.resize(377, 176)
        self.gridLayout = QtGui.QGridLayout(narmaParamDlg)
        self.gridLayout.setObjectName("gridLayout")
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label_NumberOfHistoryData = QtGui.QLabel(narmaParamDlg)
        self.label_NumberOfHistoryData.setObjectName("label_NumberOfHistoryData")
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label_NumberOfHistoryData)
        self.lineEdit_NumberOfHistoryData = QtGui.QLineEdit(narmaParamDlg)
        self.lineEdit_NumberOfHistoryData.setObjectName("lineEdit_NumberOfHistoryData")
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.lineEdit_NumberOfHistoryData)
        self.label_NumberOfNeurons = QtGui.QLabel(narmaParamDlg)
        self.label_NumberOfNeurons.setObjectName("label_NumberOfNeurons")
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_NumberOfNeurons)
        self.lineEdit_NumberOfNeurons = QtGui.QLineEdit(narmaParamDlg)
        self.lineEdit_NumberOfNeurons.setObjectName("lineEdit_NumberOfNeurons")
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.lineEdit_NumberOfNeurons)
        self.label_MaxNumberOfIterations = QtGui.QLabel(narmaParamDlg)
        self.label_MaxNumberOfIterations.setObjectName("label_MaxNumberOfIterations")
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label_MaxNumberOfIterations)
        self.lineEdit_MaxNumberOfIterations = QtGui.QLineEdit(narmaParamDlg)
        self.lineEdit_MaxNumberOfIterations.setObjectName("lineEdit_MaxNumberOfIterations")
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.lineEdit_MaxNumberOfIterations)
        self.gridLayout.addLayout(self.formLayout, 0, 0, 1, 1)
        self.pushButton_ResetToDefault = QtGui.QPushButton(narmaParamDlg)
        self.pushButton_ResetToDefault.setAutoDefault(False)
        self.pushButton_ResetToDefault.setObjectName("pushButton_ResetToDefault")
        self.gridLayout.addWidget(self.pushButton_ResetToDefault, 1, 0, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_Cancel = QtGui.QPushButton(narmaParamDlg)
        self.pushButton_Cancel.setAutoDefault(False)
        self.pushButton_Cancel.setObjectName("pushButton_Cancel")
        self.horizontalLayout.addWidget(self.pushButton_Cancel)
        self.pushButton_OK = QtGui.QPushButton(narmaParamDlg)
        self.pushButton_OK.setAutoDefault(False)
        self.pushButton_OK.setObjectName("pushButton_OK")
        self.horizontalLayout.addWidget(self.pushButton_OK)
        self.gridLayout.addLayout(self.horizontalLayout, 2, 0, 1, 1)

        self.retranslateUi(narmaParamDlg)
        QtCore.QMetaObject.connectSlotsByName(narmaParamDlg)
        narmaParamDlg.setTabOrder(self.lineEdit_NumberOfHistoryData, self.lineEdit_NumberOfNeurons)
        narmaParamDlg.setTabOrder(self.lineEdit_NumberOfNeurons, self.lineEdit_MaxNumberOfIterations)
        narmaParamDlg.setTabOrder(self.lineEdit_MaxNumberOfIterations, self.pushButton_ResetToDefault)

    def retranslateUi(self, narmaParamDlg):
        narmaParamDlg.setWindowTitle(QtGui.QApplication.translate("narmaParamDlg", "NARMA DRM Parameter Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label_NumberOfHistoryData.setText(QtGui.QApplication.translate("narmaParamDlg", "Number of Discrete History Data", None, QtGui.QApplication.UnicodeUTF8))
        self.label_NumberOfNeurons.setText(QtGui.QApplication.translate("narmaParamDlg", "Number of Neurons in Hidden Layer", None, QtGui.QApplication.UnicodeUTF8))
        self.label_MaxNumberOfIterations.setText(QtGui.QApplication.translate("narmaParamDlg", "Maximum Number of BP Iterations", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_ResetToDefault.setText(QtGui.QApplication.translate("narmaParamDlg", "Reset To Default Parameters", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_Cancel.setText(QtGui.QApplication.translate("narmaParamDlg", "Cancel", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_OK.setText(QtGui.QApplication.translate("narmaParamDlg", "OK", None, QtGui.QApplication.UnicodeUTF8))

