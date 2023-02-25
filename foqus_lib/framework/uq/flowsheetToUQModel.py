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
from foqus_lib.framework.graph.graph import *
from foqus_lib.framework.uq.Model import *
from foqus_lib.framework.uq.Distribution import *


def flowsheetToUQModel(gr):
    """
    This function converts a node model to a UQ model for UQ analysis.  This is temporary solution.
    The extra python calculations that are include in a node are not converted, just the simulation.
    """
    uqModel = Model()
    uqModel.setName("Flowsheet")
    uqModel.setRunType(Model.GATEWAY)  # Basically run through John's stuff
    uqModel.setNamesIncludeNodes(True)
    keys = gr.input.compoundNames()
    names = []
    typ = []  # Type for each input (Fixed or Variable)
    val = []  # Current value of inputs in the node
    mins = []  # minimums for inputs
    maxs = []  # maximums for inputs
    dists = []
    default = []  # defaults for inputs
    flowsheetFixed = []
    gr.generateGlobalVariables()
    for key in keys:  # key is input variable name, make lists
        if not gr.input.get(key).con:
            names.append(key)
            typ.append(Model.VARIABLE)
            val.append(gr.input.get(key).value)
            mins.append(gr.input.get(key).min)
            maxs.append(gr.input.get(key).max)
            default.append(gr.input.get(key).default)
            dists.append(gr.input.get(key).dist)
            flowsheetFixed.append(False)
    # Set input values
    uqModel.setInputNames(names)
    uqModel.setInputTypes(typ)
    uqModel.setInputMins(mins)
    uqModel.setInputMaxs(maxs)
    uqModel.setInputDistributions(dists)
    uqModel.setInputDefaults(default)
    uqModel.setInputFlowsheetFixed(flowsheetFixed)
    # Set output names and set all outputs as selected
    keys = gr.output.compoundNames()
    uqModel.setOutputNames(keys)
    uqModel.setSelectedOutputs(list(range(len(keys))))
    return uqModel


def printUQModel(self):
    """
    Print the UQ model, to make sure things are working as expected.
    """
    print("Model Name:")
    print(self.getName())
    print("\nRun File:")
    print(self.getDriverName())
    print("\nRun Type (0 = Gateway, 1 = Local):")
    print(self.getRunType())
    print("\nInput Names:")
    print(self.getInputNames())
    print("\nInput Types (0 = Fixed, 1 = Variable):")
    print(self.getInputTypes())
    print("\nInput Minimums:")
    print(self.getInputMins())
    print("\nInput Maximums:")
    print(self.getInputMaxs())
    print("\nInput Defaults:")
    print(self.getInputDefaults())
    print("\nOutput Names:")
    print(self.getOutputNames())
    print("\nSelected Outputs:")
    print(self.getSelectedOutputs())
    print("\n\n")
