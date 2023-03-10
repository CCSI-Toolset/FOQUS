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
__author__ = "sotorrio1"

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
