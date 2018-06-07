__author__ = 'sotorrio1'

from PyQt5.QtCore import pyqtSignal
from foqus_lib.gui.flowsheet.dataBrowserFrame import dataBrowserFrame

class uqDataBrowserFrame(dataBrowserFrame):
    indicesSelectedSignal = pyqtSignal(list)

    def __init__(self, parent=None):
        self.parent = parent
        super(uqDataBrowserFrame, self).__init__(None, parent)
        self.saveEnsembleButton.show()
        self.saveEnsembleButton.clicked.connect(self.saveEnsemble)

    def init(self, dat):
        self.dat = dat

    def setResults(self, results):
        self.results = results

    def saveEnsemble(self):
        self.indicesSelectedSignal.emit(self.results.get_indexes(True))