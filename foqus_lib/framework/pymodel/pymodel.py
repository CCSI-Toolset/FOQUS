###############################################################################
# FOQUS Copyright (c) 2012 - 2021, by the software owners: Oak Ridge Institute
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
#
###############################################################################
import numpy
from foqus_lib.framework.graph.nodeVars import *
from collections import OrderedDict


class pymodel:
    def __init__(self):
        self.inputs = OrderedDict()
        self.outputs = OrderedDict()
        self.status = -1  # Caclulation status code
        self.description = "A Python model plugin"
        self.node = None

    def setNode(self, node=None):
        self.node = node

    def run(self):
        """
        Override this function with python model
        """
        pass
