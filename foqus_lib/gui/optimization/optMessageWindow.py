#
# John Eslick, 2013
# Copyright Carnegie Mellon University
#
from PySide import QtCore, QtGui
from optMessageWindow_UI import *

class optMessageWindow(QtGui.QWidget, Ui_optMessageWindow):
	def __init__(self, parent=None):
		'''
			Constructor for optimization message window
		'''
		QtGui.QWidget.__init__(self, parent)
		self.setupUi(self) # Create the widgets
	
	def closeEvent(self, e):
		e.ignore()
		
	def clearMessages(self):
		self.msgTextBrowser.clear()
		