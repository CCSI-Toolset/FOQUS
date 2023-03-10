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
"""
Tests for sdoe/order

See LICENSE.md for license and copyright details.
"""

import pathlib as pl
import sys

import numpy as np
import pandas as pd

from foqus_lib.framework.sdoe import order
from foqus_lib.framework.sdoe import df_utils


def test_mat2tuples():
    """Test mat2tuples"""
    arr = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    lte = order.mat2tuples(arr)
    assert lte == [(1, 0, 4), (2, 0, 7), (2, 1, 8)]


def test_rank():
    """Call to order.rank() using hard-coded data written to temp files"""

    # candidate dataframe to write to cand file
    cand_df = pd.DataFrame(
        {
            "w": [0.15, 0.15, 0.15, 0.175, 0.175, 0.15, 0.15, 0.15],
            "G": [2700, 2500, 2000, 2500, 2500, 1500, 1500, 2000],
            "lldg": [0.15, 0.15, 0.25, 0.25, 0.3, 0.15, 0.15, 0.3],
            "L": [10039, 9060, 7519, 7358, 6185, 3100, 3454, 8529],
        }
    )
    cand_fn = pl.Path(sys.path[0], "tmp_cand.csv")
    df_utils.write(cand_fn, cand_df)

    # dist matrix to be written to dmat.npy file
    dmat = np.array(
        [
            [
                1.00000000e01,
                2.75151884e-02,
                5.10153186e-01,
                5.40001829e-01,
                9.61868543e-01,
                1.18523604e00,
                1.11693144e00,
                7.64581026e-01,
            ],
            [
                2.75151884e-02,
                1.00000000e01,
                3.70385458e-01,
                4.64940661e-01,
                8.54039200e-01,
                8.52817813e-01,
                7.94402325e-01,
                6.53028010e-01,
            ],
            [
                5.10153186e-01,
                3.70385458e-01,
                1.00000000e01,
                2.60486124e-01,
                3.48005747e-01,
                6.15110612e-01,
                5.72261139e-01,
                7.70540649e-02,
            ],
            [
                5.40001829e-01,
                4.64940661e-01,
                2.60486124e-01,
                1.00000000e01,
                8.21307813e-02,
                1.02830593e00,
                9.87082757e-01,
                3.42180198e-01,
            ],
            [
                9.61868543e-01,
                8.54039200e-01,
                3.48005747e-01,
                8.21307813e-02,
                1.00000000e01,
                1.21791690e00,
                1.18854249e00,
                3.38505599e-01,
            ],
            [
                1.18523604e00,
                8.52817813e-01,
                6.15110612e-01,
                1.02830593e00,
                1.21791690e00,
                1.00000000e01,
                1.78792001e-03,
                1.06951995e00,
            ],
            [
                1.11693144e00,
                7.94402325e-01,
                5.72261139e-01,
                9.87082757e-01,
                1.18854249e00,
                1.78792001e-03,
                1.00000000e01,
                1.01646822e00,
            ],
            [
                7.64581026e-01,
                6.53028010e-01,
                7.70540649e-02,
                3.42180198e-01,
                3.38505599e-01,
                1.06951995e00,
                1.01646822e00,
                1.00000000e01,
            ],
        ]
    )
    dmat_fn = pl.Path(sys.path[0], "tmp_dmat.npy")
    np.save(dmat_fn, dmat)

    # file name dict to be passed to order.rank()
    fnames = {"cand": str(cand_fn), "dmat": str(dmat_fn)}

    # Make the actual call
    fname_ranked = order.rank(fnames, ga_max_attempts=5)

    # Ranked results as a dataframe
    ret_ranked_df = df_utils.load(fname_ranked)

    # Expected ranked results as dataframe
    ranked_df = pd.DataFrame(
        {
            "w": [0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.175, 0.175],
            "G": [2000, 2000, 1500, 1500, 2500, 2700, 2500, 2500],
            "lldg": [0.3, 0.25, 0.15, 0.15, 0.15, 0.15, 0.25, 0.3],
            "L": [8529, 7519, 3100, 3454, 9060, 10039, 7358, 6185],
        }
    )

    test_results = ret_ranked_df.equals(ranked_df)

    # Clean up tmp files
    cand_fn.unlink()
    dmat_fn.unlink()
    pl.Path(fname_ranked).unlink()

    assert test_results
