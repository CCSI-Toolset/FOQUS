#################################################################################
# FOQUS Copyright (c) 2012 - 2024, by the software owners: Oak Ridge Institute
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
import os

import dask.config as dconf
import numpy as np
import pandas as pd

from foqus_lib.framework.sdoe import df_utils, usf, usf_dask


def test_criterion():
    dconf.set({"dataframe.convert-string": False})

    cand = pd.DataFrame([(1, 1), (2, 2), (3, 3), (4, 4)])
    args = {
        "icol": "",
        "xcols": [0, 1],
        "scale_factors": pd.Series(1.0, index=range(len(cand))),
    }
    nr = 3
    nd = 2
    mode = "maximin"
    hist = None

    result = usf_dask.criterion(
        cand=cand, args=args, nr=nr, nd=nd, mode=mode, hist=hist
    )

    assert result.get("best_cand") is not None


def test_same_result_as_usf():
    dconf.set({"dataframe.convert-string": False})
    index = "__id"
    inputs = ["w", "G", "lldg", "L"]
    min_vals = [0.0, 0.12, 1000.0, 0.1, 3020.0]
    max_vals = [241.0, 0.18, 2700.0, 0.3, 11392.0]
    nr = 1000
    nd = 2
    mode = "maximin"
    hist = None

    dir_path = os.path.dirname(os.path.realpath(__file__))
    csv_file_path = os.path.join(dir_path, "candidates_usf.csv")
    cand = df_utils.load(fname=csv_file_path, index=index)
    include = inputs.copy()
    include.append(index)
    scl = np.array([ub - lb for ub, lb in zip(max_vals, min_vals)])
    args = {
        "icol": index,
        "xcols": inputs,
        "scale_factors": pd.Series(scl, index=include),
    }
    rand_seed = 23112209280756322351382740501499295435

    rand_gen = np.random.default_rng(rand_seed)
    rand_gen_dask = np.random.default_rng(rand_seed)

    results = usf.criterion(cand, args, nr, nd, mode=mode, hist=hist, rand_gen=rand_gen)
    dask_results = usf_dask.criterion(
        cand, args, nr, nd, mode=mode, hist=hist, rand_gen=rand_gen_dask
    )
    assert results["best_cand"].equals(dask_results["best_cand"])

    mode = "minimax"
    rand_gen = np.random.default_rng(rand_seed)
    rand_gen_dask = np.random.default_rng(rand_seed)
    results = usf.criterion(cand, args, nr, nd, mode=mode, hist=hist, rand_gen=rand_gen)
    dask_results = usf_dask.criterion(
        cand, args, nr, nd, mode=mode, hist=hist, rand_gen=rand_gen_dask
    )
    assert results["best_cand"].equals(dask_results["best_cand"])
