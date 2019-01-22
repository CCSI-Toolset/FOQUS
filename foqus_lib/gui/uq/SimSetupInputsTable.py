__author__ = 'ou3'

from foqus_lib.gui.common.InputPriorTable import InputPriorTable

class SimSetupInputsTable(InputPriorTable):
    def __init__(self, parent = None):
        super(SimSetupInputsTable, self).__init__(parent)
        self.typeItems = ['Variable', 'Fixed']

    def setupLB(self):
        inVarTypes = self.data.getInputTypes()
        self.lb = self.data.getInputMins()
        self.lbVariable = [self.lb[i] for i in range(len(self.lb)) if not self.data.getInputFlowsheetFixed(i)]

    def setupUB(self):
        inVarTypes = self.data.getInputTypes()
        self.ub = self.data.getInputMaxs()
        self.ubVariable = [self.ub[i] for i in range(len(self.ub)) if not self.data.getInputFlowsheetFixed(i)]

    def setupDists(self):
        if self.dist == None:
            self.distVariable = None
        else:
            inVarTypes = self.data.getInputTypes()
            self.distVariable = [self.dist[i] for i in range(len(self.dist)) if not self.data.getInputFlowsheetFixed(i)]
