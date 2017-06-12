# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tagSelectDialog_UI.ui'
#
# Created: Mon Apr 14 15:52:42 2014
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_tagSelectDialog(object):
    def setupUi(self, tagSelectDialog):
        tagSelectDialog.setObjectName("tagSelectDialog")
        tagSelectDialog.resize(470, 471)
        tagSelectDialog.setModal(False)
        self.verticalLayout_3 = QtGui.QVBoxLayout(tagSelectDialog)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.groupBox_2 = QtGui.QGroupBox(tagSelectDialog)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout = QtGui.QVBoxLayout(self.groupBox_2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtGui.QLabel(self.groupBox_2)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.newTagEdit = QtGui.QLineEdit(self.groupBox_2)
        self.newTagEdit.setObjectName("newTagEdit")
        self.horizontalLayout.addWidget(self.newTagEdit)
        self.createTagButton = QtGui.QPushButton(self.groupBox_2)
        self.createTagButton.setObjectName("createTagButton")
        self.horizontalLayout.addWidget(self.createTagButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.mainTagList = QtGui.QTreeWidget(self.groupBox_2)
        self.mainTagList.setBaseSize(QtCore.QSize(0, 0))
        self.mainTagList.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.mainTagList.setObjectName("mainTagList")
        self.verticalLayout.addWidget(self.mainTagList)
        self.verticalLayout_3.addWidget(self.groupBox_2)
        self.horizontalLayout_6 = QtGui.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.addTagToListButton = QtGui.QPushButton(tagSelectDialog)
        self.addTagToListButton.setObjectName("addTagToListButton")
        self.horizontalLayout_6.addWidget(self.addTagToListButton)
        self.doneButton = QtGui.QPushButton(tagSelectDialog)
        self.doneButton.setObjectName("doneButton")
        self.horizontalLayout_6.addWidget(self.doneButton)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem)
        self.verticalLayout_3.addLayout(self.horizontalLayout_6)

        self.retranslateUi(tagSelectDialog)
        QtCore.QMetaObject.connectSlotsByName(tagSelectDialog)

    def retranslateUi(self, tagSelectDialog):
        tagSelectDialog.setWindowTitle(QtGui.QApplication.translate("tagSelectDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("tagSelectDialog", "Available Tags", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("tagSelectDialog", "New Tag", None, QtGui.QApplication.UnicodeUTF8))
        self.createTagButton.setText(QtGui.QApplication.translate("tagSelectDialog", "Create Tag", None, QtGui.QApplication.UnicodeUTF8))
        self.mainTagList.headerItem().setText(0, QtGui.QApplication.translate("tagSelectDialog", "Tags", None, QtGui.QApplication.UnicodeUTF8))
        self.addTagToListButton.setText(QtGui.QApplication.translate("tagSelectDialog", "Insert", None, QtGui.QApplication.UnicodeUTF8))
        self.doneButton.setText(QtGui.QApplication.translate("tagSelectDialog", "Done", None, QtGui.QApplication.UnicodeUTF8))

