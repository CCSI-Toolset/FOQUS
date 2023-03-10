#################################################################################
# FOQUS Copyright (c) 2012 - 2023, by the software owners: Oak Ridge Institute
# for Science and Education (ORISE), TRIAD National Security, LLC., Lawrence
# Livermore National Security, LLC., The Regents of the University of
# California, through Lawrence Berkeley National Laboratory, Battelle Memorial
# Institute, Pacific Northwest Division through Pacific Northwest National
# Laboratory, Carnegie Mellon University, West Virginia University, Boston
# University, the Trustees of Princeton University, The University of Texas at
# Austin, URS Energy & Construction, Inc., et al.  All rights reserved.
#
# Please see the file LICENSE.md for full copyright and license information,
# respectively. This file is also available online at the URL
# "https://github.com/CCSI-Toolset/FOQUS".
#################################################################################
"""Dash.py
* This FOQUS home screen, it doesn't do much but show the screen
  and emit signals that are handeled by the main window

    John Eslick, Carnegie Mellon University, 2014
"""
import os

from PyQt5 import QtCore, QtGui, QtWidgets, uic

mypath = os.path.dirname(__file__)
_dashFrameUI, _dashFrame = uic.loadUiType(os.path.join(mypath, "Dash_UI.ui"))


class dashFrame(_dashFrame, _dashFrameUI):
    """
    This is the main FOQUS screen, it contains some FOQUS settings
    and a session description.  Very little happens here all the
    buttons emit signals that are handled by the main window
    """

    def __init__(self, parent=None):
        """
        Initialize dash frame
        """
        super(dashFrame, self).__init__(parent=parent)
        self.setupUi(self)
        self.underlineButton.clicked.connect(self.underline)
        self.overlineButton.clicked.connect(self.overline)
        self.boldButton.clicked.connect(self.bold)
        self.superscriptButton.clicked.connect(self.superscript)
        self.subscriptButton.clicked.connect(self.subscript)
        self.fontButton.clicked.connect(self.font)
        self.colorButton.clicked.connect(self.color)
        self.textEdit.currentCharFormatChanged.connect(self.getFormat)
        self.getFormat()

    def setSessionDescription(self, text):
        """
        Set the session description
        """
        self.textEdit.setHtml(text)

    def sessionDescription(self):
        """
        Get the session description
        """
        return self.textEdit.toHtml()

    def getFormat(self):
        self.format = self.textEdit.currentCharFormat()
        self.underlineButton.setChecked(self.format.fontUnderline())
        self.overlineButton.setChecked(self.format.fontOverline())
        if self.format.fontWeight() == QtGui.QFont.Bold:
            self.boldButton.setChecked(True)
        else:
            self.boldButton.setChecked(False)
        if self.format.verticalAlignment() == QtGui.QTextCharFormat.AlignSuperScript:
            self.superscriptButton.setChecked(True)
            self.subscriptButton.setChecked(False)
        elif self.format.verticalAlignment() == QtGui.QTextCharFormat.AlignSubScript:
            self.superscriptButton.setChecked(False)
            self.subscriptButton.setChecked(True)
        else:
            self.superscriptButton.setChecked(False)
            self.subscriptButton.setChecked(False)

    def color(self):
        color = QtWidgets.QColorDialog.getColor(self.textEdit.textColor(), self)
        self.textEdit.setTextColor(color)
        self.textEdit.setFocus()

    def font(self):
        font, ok = QtWidgets.QFontDialog.getFont(self.format.font(), self)
        if ok:
            self.format.setFont(font)
            self.textEdit.setCurrentCharFormat(self.format)
            self.textEdit.setFocus()

    def superscript(self):
        if self.superscriptButton.isChecked():
            self.subscriptButton.setChecked(False)
            self.format.setVerticalAlignment(QtGui.QTextCharFormat.AlignSuperScript)
        else:
            self.format.setVerticalAlignment(QtGui.QTextCharFormat.AlignNormal)
        self.textEdit.setCurrentCharFormat(self.format)
        self.textEdit.setFocus()

    def subscript(self):
        if self.subscriptButton.isChecked():
            self.superscriptButton.setChecked(False)
            self.format.setVerticalAlignment(QtGui.QTextCharFormat.AlignSubScript)
        else:
            self.format.setVerticalAlignment(QtGui.QTextCharFormat.AlignNormal)
        self.textEdit.setCurrentCharFormat(self.format)
        self.textEdit.setFocus()

    def bold(self):
        if self.boldButton.isChecked():
            self.format.setFontWeight(QtGui.QFont.Bold)
        else:
            self.format.setFontWeight(QtGui.QFont.Normal)
        self.textEdit.setCurrentCharFormat(self.format)
        self.textEdit.setFocus()

    def underline(self):
        self.format.setFontUnderline(self.underlineButton.isChecked())
        self.textEdit.setCurrentCharFormat(self.format)
        self.textEdit.setFocus()

    def overline(self):
        self.format.setFontOverline(self.overlineButton.isChecked())
        self.textEdit.setCurrentCharFormat(self.format)
        self.textEdit.setFocus()

    def reject(self):
        self.done(QtWidgets.QDialog.Rejected)

    def accept(self):
        self.done(QtWidgets.QDialog.Accepted)

    def html(self):
        return self.textEdit.toHtml()
