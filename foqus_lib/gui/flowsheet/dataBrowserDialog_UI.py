# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'flowsheet\dataBrowserDialog_UI.ui'
#
# Created: Mon May 19 09:39:06 2014
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_dataBrowserDialog(object):
    def setupUi(self, dataBrowserDialog):
        dataBrowserDialog.setObjectName("dataBrowserDialog")
        dataBrowserDialog.resize(773, 743)
        self.verticalLayout_2 = QtGui.QVBoxLayout(dataBrowserDialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")

        self.retranslateUi(dataBrowserDialog)
        QtCore.QMetaObject.connectSlotsByName(dataBrowserDialog)

    def retranslateUi(self, dataBrowserDialog):
        dataBrowserDialog.setWindowTitle(QtGui.QApplication.translate("dataBrowserDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))

import foqus_lib.gui.icons_rc as icons_rc
