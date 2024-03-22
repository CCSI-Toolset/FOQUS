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
import pandas as pd

from foqus_lib.framework.sdoe import df_utils, nusf, nusf_dask


def test_criterion():
    dconf.set({"dataframe.convert-string": False})

    cand = pd.DataFrame([(1, 1, 1), (2, 2, 1), (3, 3, 1), (4, 4, 1)])
    args = {
        "icol": "",
        "xcols": [0, 1],
        "scale_factors": pd.Series(1.0, index=range(len(cand))),
        "wcol": 2,
        "max_iterations": 100,
        "mwr_values": [1, 2, 4, 8, 16],
        "scale_method": "direct_mwr",
    }
    nr = 3
    nd = 2
    mode = "maximin"
    hist = None

    result = nusf_dask.criterion(
        cand=cand, args=args, nr=nr, nd=nd, mode=mode, hist=hist
    )

    for mwr in args["mwr_values"]:
        assert result[mwr].get("best_cand") is not None


def test_same_results_as_nusf():
    dconf.set({"dataframe.convert-string": False})

    index = "__id"
    inputs = ["L", "G", "w", "lldg"]
    weight = "CI Width Prior"
    nr = 5
    nd = 10
    mode = "maximin"
    hist = None
    scale_method = "direct_mwr"
    mwr_values = [5, 10, 20, 40, 60]

    dir_path = os.path.dirname(os.path.realpath(__file__))
    csv_file_path = os.path.join(dir_path, "candidates_nusf.csv")
    cand = df_utils.load(fname=csv_file_path, index=index)
    args = {
        "icol": index,
        "xcols": inputs,
        "wcol": weight,
        "max_iterations": 5,
        "mwr_values": mwr_values,
        "scale_method": scale_method,
    }

    rand_seed = 23112209280756322351382740501499295435

    results = nusf.criterion(
        cand, args, nr, nd, mode=mode, hist=hist, rand_seed=rand_seed
    )
    dask_results = nusf_dask.criterion(
        cand, args, nr, nd, mode=mode, hist=hist, rand_seed=rand_seed
    )
    for mwr in mwr_values:
        assert results[mwr]["best_cand"].equals(dask_results[mwr]["best_cand"])
        assert results[mwr]["best_cand_scaled"].equals(
            dask_results[mwr]["best_cand_scaled"]
        )
        assert results[mwr]["best_val"] == dask_results[mwr]["best_val"]
        assert results[mwr]["best_mties"] == dask_results[mwr]["best_mties"]

    scale_method = "ranked_mwr"
    args = {
        "icol": index,
        "xcols": inputs,
        "wcol": weight,
        "max_iterations": 5,
        "mwr_values": mwr_values,
        "scale_method": scale_method,
    }

    results = nusf.criterion(
        cand, args, nr, nd, mode=mode, hist=hist, rand_seed=rand_seed
    )
    dask_results = nusf_dask.criterion(
        cand, args, nr, nd, mode=mode, hist=hist, rand_seed=rand_seed
    )
    for mwr in mwr_values:
        assert results[mwr]["best_cand"].equals(dask_results[mwr]["best_cand"])
        assert results[mwr]["best_cand_scaled"].equals(
            dask_results[mwr]["best_cand_scaled"]
        )
        assert results[mwr]["best_val"] == dask_results[mwr]["best_val"]
        assert results[mwr]["best_mties"] == dask_results[mwr]["best_mties"]
