#!/usr/bin/env python3
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
import time

import dask.config as dconf
import numpy as np
import pandas as pd
from dask.distributed import Client

from foqus_lib.framework.sdoe import df_utils, usf, usf_dask


def main():
    dconf.set({"dataframe.convert-string": False})

    client = Client()

    ## USF set up
    index = "__id"
    inputs = ["w", "G", "lldg", "L"]
    min_vals = [0.0, 0.12, 1000.0, 0.1, 3020.0]
    max_vals = [241.0, 0.18, 2700.0, 0.3, 11392.0]
    nd = 2
    mode = "maximin"
    hist = None

    include = inputs.copy()
    include.append(index)
    scl = np.array([ub - lb for ub, lb in zip(max_vals, min_vals)])
    cand = df_utils.load(fname="candidates_usf.csv", index=index)
    args = {
        "icol": index,
        "xcols": inputs,
        "scale_factors": pd.Series(scl, index=include),
    }
    rand_seed = 23112209280756322351382740501499295435
    rand_gen = np.random.default_rng(rand_seed)
    rand_gen_dask = np.random.default_rng(rand_seed)

    # run across range of 10^1 to 10^6 for both types
    sample_sizes = [10**x for x in range(1, 7)]
    df = pd.DataFrame(
        {
            "Random Starts": sample_sizes,
            "Original Time": [None] * len(sample_sizes),
            "Using Dask Time": [None] * len(sample_sizes),
        }
    )
    print(f"sample sizes: {sample_sizes}")

    for i in sample_sizes:
        t0 = time.time()
        results = usf.criterion(
            cand, args, i, nd, mode=mode, hist=hist, rand_gen=rand_gen
        )
        df.loc[df["Random Starts"] == i, "Original Time"] = time.time() - t0
        print(client)
        t0 = time.time()
        dask_results = usf_dask.criterion(
            cand, args, i, nd, mode=mode, hist=hist, rand_gen=rand_gen_dask
        )
        assert results["best_cand"].equals(dask_results["best_cand"])
        df.loc[df["Random Starts"] == i, "Using Dask Time"] = time.time() - t0
        print(f"Random start num = {i}\n{df.loc[df['Random Starts'] == i]}")

    df.to_csv("usf_test_times.csv", index=False)
    print(df)


if __name__ == "__main__":
    main()
