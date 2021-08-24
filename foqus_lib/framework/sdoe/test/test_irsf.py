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
"""
Tests for sdoe/irsf

See LICENSE.md for license and copyright details.
"""

import numpy as np
from foqus_lib.framework.sdoe import irsf


def test_inv_scale_cand():
    cand = np.array([[1, 1, 1], [2, 2, 2], [3, 3, 3]])
    norm_cand = irsf.unitscale_cand(cand)

    xmin = cand.min(axis=0)
    xmax = cand.max(axis=0)
    norm_cand_reversed = irsf.Inv_scale_cand(norm_cand, xmin, xmax)

    assert np.array_equal(cand, norm_cand_reversed), "Inv_scale_cand function not working properly."
