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
Tests for sdoe/usf

See LICENSE.md for license and copyright details.
"""

import numpy as np
from foqus_lib.framework.sdoe import usf


def test_compute_min_dist():
    mat = np.array([[1, 1], [2, 2], [3, 3]])
    scl = np.array([2.0, 2.0])
    results = usf.compute_min_dist(mat, scl, hist_xs=None)
    assert np.array_equal(np.array([[10.0, 0.5, 2.0], [ 0.5, 10.0, 0.5], [2.0, 0.5, 10.0]]), results[0])
    assert np.array_equal(np.array([0.5, 0.5, 0.5]), results[1])
