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
#
# FOQUS_PYMODEL_PLUGIN

import numpy
from foqus_lib.framework.pymodel.pymodel import *
from foqus_lib.framework.graph.nodeVars import *


def checkAvailable():
    """
    Plugins should have this function to check availability of any
    additional required software.  If requirements are not available
    plugin will not be available.
    """
    return True


class pymodel_pg(pymodel):
    def __init__(self):
        pymodel.__init__(self)
        self.inputs["x1"] = NodeVars(
            value=1.0,
            vmin=0.0,
            vmax=10.0,
            vdflt=1.0,
            unit="",
            vst="pymodel",
            vdesc="Test 1",
            tags=[],
            dtype=float,
        )
        self.inputs["x2"] = NodeVars(
            value=1.0,
            vmin=0.0,
            vmax=10.0,
            vdflt=1.0,
            unit="",
            vst="pymodel",
            vdesc="Test 2",
            tags=[],
            dtype=float,
        )
        self.outputs["y"] = NodeVars(vdesc="test out", dtype=float)

    def run(self):
        y = self.inputs["x1"].value + self.inputs["x2"].value
        self.outputs["y"].value = y
