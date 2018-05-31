__author__ = 'ou3'

from foqus_lib.gui.common.InputPriorTable import InputPriorTable

class InferenceInputsTable(InputPriorTable):
    def __init__(self, parent = None):
        super(InferenceInputsTable, self).__init__(parent)
        self.typeItems = ['Variable', 'Fixed', 'Design', 'Uncertain']
