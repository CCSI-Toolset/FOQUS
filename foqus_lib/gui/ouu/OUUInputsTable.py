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


class OUUInputsTable(InputPriorTable):
    def __init__(self, parent=None):
        super(OUUInputsTable, self).__init__(parent)
        self.typeItems = [
            "Fixed",
            "Opt: Primary Continuous (Z1)",
            "Opt: Recourse (Z2)",
            "UQ: Discrete (Z3)",
            "UQ: Continuous (Z4)",
        ]
