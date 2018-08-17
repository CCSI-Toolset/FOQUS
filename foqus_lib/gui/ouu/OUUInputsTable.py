__author__ = 'ou3'

from foqus_lib.gui.common.InputPriorTable import InputPriorTable

class OUUInputsTable(InputPriorTable):
    def __init__(self, parent = None):
        super(OUUInputsTable, self).__init__(parent)
        self.typeItems = ['Fixed', 'Opt: Primary Continuous (Z1)', 'Opt: Primary Discrete (Z1d)', 'Opt: Recourse (Z2)', 'UQ: Discrete (Z3)', 'UQ: Continuous (Z4)']