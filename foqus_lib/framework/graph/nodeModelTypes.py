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
"""nodeModelTypes.py

* This contains the classes for node model types

John Eslick, Carnegie Mellon University, 2014
"""


class nodeModelTypes:
    MODEL_NONE = 0
    MODEL_PLUGIN = 1
    MODEL_TURBINE = 2
    MODEL_DMF_LITE = 3
    MODEL_DMF_SERV = 4
    MODEL_ML_AI = 5
