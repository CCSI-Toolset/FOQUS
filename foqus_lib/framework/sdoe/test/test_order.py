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
    """ Test mat2tuples """
    arr = np.array([[1, 2, 3],
                    [4, 5, 6],
                    [7, 8, 9]])
    lte = order.mat2tuples(arr)
    assert lte == [(1, 0, 4), (2, 0, 7), (2, 1, 8)]

def test_rank():
    """ Call to order.rank() using hard-coded data written to temp files """

    # candidate dataframe to write to cand file
    cand_df = pd.DataFrame({
        'w':    [0.125, 0.125],
        'G':    [1500, 1500],
        'lldg': [0.2, 0.2],
        'L':    [4601, 5247]
    })
    cand_fn = pl.Path(sys.path[0], "tmp_cand.csv")
    df_utils.write(cand_fn, cand_df)

    # dist matrix to be written to dmat.npy file
    dmat = np.array([[1.00000000e+01, 5.95396938e-03],
                     [5.95396938e-03, 1.00000000e+01]])
    dmat_fn = pl.Path(sys.path[0], "tmp_dmat.npy")
    np.save(dmat_fn, dmat)

    # file name dict to be passed to order.rank()
    fnames = {
        "cand": str(cand_fn),
        "dmat": str(dmat_fn)
    }

    # Make the actual call
    fname_ranked = order.rank(fnames, ga_max_attempts=5)

    # Ranked results as a dataframe
    ret_ranked_df = df_utils.load(fname_ranked)

    # Expected ranked results as dataframe
    ranked_df = pd.DataFrame({
        'w':    [0.125, 0.125],
        'G':    [1500, 1500],
        'lldg': [0.2, 0.2],
        'L':    [5247, 4601]
    })

    test_results = ret_ranked_df.equals(ranked_df)

    # Clean up tmp files
    cand_fn.unlink()
    dmat_fn.unlink()
    pl.Path(fname_ranked).unlink()

    assert test_results
