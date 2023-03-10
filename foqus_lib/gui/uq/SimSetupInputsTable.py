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
__author__ = "ou3"

from foqus_lib.gui.common.InputPriorTable import InputPriorTable


class SimSetupInputsTable(InputPriorTable):
    def __init__(self, parent=None):
        super(SimSetupInputsTable, self).__init__(parent)
        self.typeItems = ["Variable", "Fixed"]

    def setupLB(self):
        inVarTypes = self.data.getInputTypes()
        self.lb = self.data.getInputMins()
        self.lbVariable = [
            self.lb[i]
            for i in range(len(self.lb))
            if not self.data.getInputFlowsheetFixed(i)
        ]

    def setupUB(self):
        inVarTypes = self.data.getInputTypes()
        self.ub = self.data.getInputMaxs()
        self.ubVariable = [
            self.ub[i]
            for i in range(len(self.ub))
            if not self.data.getInputFlowsheetFixed(i)
        ]

    def setupDists(self):
        if self.dist == None:
            self.distVariable = None
        else:
            inVarTypes = self.data.getInputTypes()
            self.distVariable = [
                self.dist[i]
                for i in range(len(self.dist))
                if not self.data.getInputFlowsheetFixed(i)
            ]
