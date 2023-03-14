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
from unittest import result
import numpy as np
from foqus_lib.framework.sdoe import distance


def test_compute_dist():
    # let N = 4, nx = 2, M = 3

    mat = np.array([[1.5, 2.5], [3.5, 4.5], [1.0, 2.0], [3.0, 4.0]])
    print(mat.shape)
    scl = np.array([2.2, 3.2])
    wt = np.array([1.6, 2.6, 3.6, 4.6])
    hist_xs = np.array([[1.7, 2.7], [3.7, 2.3], [3.3, 4.3]])
    hist_wt = np.array([10.0, 11.0, 12.0])

    mat_and_hist_xs = distance.compute_dist(
        mat, scl=None, wt=None, hist_xs=hist_xs, hist_wt=None
    )
    assert isinstance(mat_and_hist_xs, np.ndarray)
    assert mat_and_hist_xs.shape == (7, 7)
    # expect_mat_and_hist_xs = np.array([[1.5, 2.5],
    #                                 [3.5, 4.5],
    #                                 [1.0, 2.0],
    #                                 [3.0, 4.0],
    #                                 [1.7, 2.7],
    #                                 [3.7, 2.3],
    #                                 [3.3, 4.3]])

    # assert np.array_equal(mat_and_hist_xs, expect_mat_and_hist_xs)
