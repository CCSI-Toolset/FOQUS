# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Preview_UI.ui'
#
# Created: Wed Oct 14 15:37:39 2015
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(701, 499)
        font = QtGui.QFont()
        font.setPointSize(10)
        Dialog.setFont(font)
        self.gridLayout_3 = QtGui.QGridLayout(Dialog)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.table = QtGui.QTableWidget(Dialog)
        self.table.setMinimumSize(QtCore.QSize(371, 0))
        self.table.setObjectName("table")
        self.table.setColumnCount(1)
        self.table.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.table.setHorizontalHeaderItem(0, item)
        self.verticalLayout_2.addWidget(self.table)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtGui.QSpacerItem(208, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.fixedInputsCheck = QtGui.QCheckBox(Dialog)
        self.fixedInputsCheck.setObjectName("fixedInputsCheck")
        self.horizontalLayout_2.addWidget(self.fixedInputsCheck)
        spacerItem1 = QtGui.QSpacerItem(188, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.gridLayout_3.addLayout(self.verticalLayout_2, 0, 0, 2, 1)
        self.group1D = QtGui.QGroupBox(Dialog)
        self.group1D.setObjectName("group1D")
        self.gridLayout = QtGui.QGridLayout(self.group1D)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtGui.QLabel(self.group1D)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.inputList = QtGui.QListWidget(self.group1D)
        self.inputList.setObjectName("inputList")
        self.verticalLayout.addWidget(self.inputList)
        self.graph1DButton = QtGui.QPushButton(self.group1D)
        self.graph1DButton.setObjectName("graph1DButton")
        self.verticalLayout.addWidget(self.graph1DButton)
        self.graph2DScatterButton = QtGui.QPushButton(self.group1D)
        self.graph2DScatterButton.setObjectName("graph2DScatterButton")
        self.verticalLayout.addWidget(self.graph2DScatterButton)
        self.graph2DDistButton = QtGui.QPushButton(self.group1D)
        self.graph2DDistButton.setObjectName("graph2DDistButton")
        self.verticalLayout.addWidget(self.graph2DDistButton)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.gridLayout_3.addWidget(self.group1D, 0, 1, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem2 = QtGui.QSpacerItem(248, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.okButton = QtGui.QPushButton(Dialog)
        self.okButton.setObjectName("okButton")
        self.horizontalLayout.addWidget(self.okButton)
        spacerItem3 = QtGui.QSpacerItem(218, 27, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem3)
        self.gridLayout_3.addLayout(self.horizontalLayout, 2, 0, 1, 2)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.okButton, QtCore.SIGNAL("clicked()"), Dialog.close)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "CCSI UQ/Opt Framework - Preview Inputs", None, QtGui.QApplication.UnicodeUTF8))
        self.table.horizontalHeaderItem(0).setText(QtGui.QApplication.translate("Dialog", "Input 1", None, QtGui.QApplication.UnicodeUTF8))
        self.fixedInputsCheck.setText(QtGui.QApplication.translate("Dialog", "View Fixed Inputs", None, QtGui.QApplication.UnicodeUTF8))
        self.group1D.setTitle(QtGui.QApplication.translate("Dialog", "Plots", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Dialog", "Select Inputs to Graph\n"
" (Shift+Click or Ctrl+Click to select Multiple):", None, QtGui.QApplication.UnicodeUTF8))
        self.inputList.setToolTip(QtGui.QApplication.translate("Dialog", "Select single or multiple input parameter(s)\n"
"to view 1-D scatterplot(s) of the ensemble.", None, QtGui.QApplication.UnicodeUTF8))
        self.graph1DButton.setText(QtGui.QApplication.translate("Dialog", "Graph 1-D Scatter", None, QtGui.QApplication.UnicodeUTF8))
        self.graph2DScatterButton.setText(QtGui.QApplication.translate("Dialog", "Graph 2-D Scatter (2 Inputs Only)", None, QtGui.QApplication.UnicodeUTF8))
        self.graph2DDistButton.setText(QtGui.QApplication.translate("Dialog", "Graph Distribution", None, QtGui.QApplication.UnicodeUTF8))
        self.okButton.setText(QtGui.QApplication.translate("Dialog", "OK", None, QtGui.QApplication.UnicodeUTF8))

