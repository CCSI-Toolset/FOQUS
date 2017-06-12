# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'basicDataParentFrame_UI.ui'
#
# Created: Thu Jan 28 17:18:21 2016
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Frame(object):
    def setupUi(self, Frame):
        Frame.setObjectName("Frame")
        Frame.resize(932, 831)
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setWeight(75)
        font.setBold(True)
        Frame.setFont(font)
        Frame.setFrameShape(QtGui.QFrame.StyledPanel)
        Frame.setFrameShadow(QtGui.QFrame.Raised)
        self.gridLayout_3 = QtGui.QGridLayout(Frame)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.dmfGroup = QtGui.QGroupBox(Frame)
        self.dmfGroup.setObjectName("dmfGroup")
        self.gridLayout = QtGui.QGridLayout(self.dmfGroup)
        self.gridLayout.setObjectName("gridLayout")
        self.dmfFrame = basicDataFrame(self.dmfGroup)
        font = QtGui.QFont()
        font.setWeight(50)
        font.setBold(False)
        self.dmfFrame.setFont(font)
        self.dmfFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.dmfFrame.setFrameShadow(QtGui.QFrame.Raised)
        self.dmfFrame.setObjectName("dmfFrame")
        self.gridLayout.addWidget(self.dmfFrame, 0, 0, 1, 1)
        self.gridLayout_3.addWidget(self.dmfGroup, 0, 0, 1, 1)
        self.solventFitGroup = QtGui.QGroupBox(Frame)
        self.solventFitGroup.setObjectName("solventFitGroup")
        self.gridLayout_2 = QtGui.QGridLayout(self.solventFitGroup)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.solventFitFrame = solventFitSetupFrame(self.solventFitGroup)
        font = QtGui.QFont()
        font.setWeight(50)
        font.setBold(False)
        self.solventFitFrame.setFont(font)
        self.solventFitFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.solventFitFrame.setFrameShadow(QtGui.QFrame.Raised)
        self.solventFitFrame.setObjectName("solventFitFrame")
        self.gridLayout_2.addWidget(self.solventFitFrame, 0, 0, 1, 1)
        self.gridLayout_3.addWidget(self.solventFitGroup, 1, 0, 1, 1)

        self.retranslateUi(Frame)
        QtCore.QMetaObject.connectSlotsByName(Frame)

    def retranslateUi(self, Frame):
        Frame.setWindowTitle(QtGui.QApplication.translate("Frame", "Frame", None, QtGui.QApplication.UnicodeUTF8))
        self.dmfGroup.setTitle(QtGui.QApplication.translate("Frame", "DMF", None, QtGui.QApplication.UnicodeUTF8))
        self.solventFitGroup.setTitle(QtGui.QApplication.translate("Frame", "SolventFit", None, QtGui.QApplication.UnicodeUTF8))

from foqus_lib.gui.basic_data.basicDataFrame import basicDataFrame
from foqus_lib.gui.solventfit.solventFitSetupFrame import solventFitSetupFrame
