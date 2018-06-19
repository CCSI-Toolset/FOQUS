__author__ = 'ou3'

from foqus_lib.gui.common.InputPriorTable import InputPriorTable

class AnalysisInputsTable(InputPriorTable):
    def __init__(self, parent = None):
        super(AnalysisInputsTable, self).__init__(parent)
        self.typeItems = ['Aleatory', 'Epistemic', 'Fixed']