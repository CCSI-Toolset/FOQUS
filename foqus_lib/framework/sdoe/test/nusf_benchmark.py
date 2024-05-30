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

import numpy as np
import pandas as pd
from dask.distributed import Client

from foqus_lib.framework.sdoe import df_utils, nusf, nusf_dask


def main():
    client = Client()

    ## NUSF set up
    index = "__id"
    inputs = ["L", "G", "w", "lldg"]
    weight = "CI Width Prior"
    nr = 10
    nd = 10
    mode = "maximin"
    hist = None
    scale_method = "direct_mwr"  # "ranked_mwr"
    mwr_values = [5, 10, 20, 40, 60]

    cand = df_utils.load(fname="candidates_nusf.csv", index=index)

    rand_seed = 23112209280756322351382740501499295435

    MAX = 4
    iteration_sample_sizes = [10**x for x in range(1, MAX)]
    random_starts_sample_sizes = [10 * x for x in range(1, MAX)]
    df = pd.DataFrame(
        {
            "Random Starts": random_starts_sample_sizes * len(iteration_sample_sizes),
            "Max Iterations": [
                element
                for element in iteration_sample_sizes
                for _ in range(len(random_starts_sample_sizes))
            ],
            "Original Time": [None]
            * len(iteration_sample_sizes)
            * len(random_starts_sample_sizes),
            "Using Dask Time": [None]
            * len(iteration_sample_sizes)
            * len(random_starts_sample_sizes),
        }
    )
    print(f"iteration sample sizes: {iteration_sample_sizes}")
    print(f"random starts sample sizes: {random_starts_sample_sizes}")

    for i in random_starts_sample_sizes:
        for j in iteration_sample_sizes:
            args = {
                "icol": index,
                "xcols": inputs,
                "wcol": weight,
                "max_iterations": j,
                "mwr_values": mwr_values,
                "scale_method": scale_method,
            }
            t0 = time.time()
            results = nusf.criterion(
                cand, args, i, nd, mode=mode, hist=hist, rand_seed=rand_seed
            )
            df.loc[
                (df["Random Starts"] == i) & (df["Max Iterations"] == j),
                "Original Time",
            ] = (
                time.time() - t0
            )
            # was occasionally having issues with Dask shutting down but referencing the client here stopped that
            print(client)
            t0 = time.time()
            dask_results = nusf_dask.criterion(
                cand, args, i, nd, mode=mode, hist=hist, rand_seed=rand_seed
            )
            df.loc[
                (df["Random Starts"] == i) & (df["Max Iterations"] == j),
                "Using Dask Time",
            ] = (
                time.time() - t0
            )
            print(
                f"Random start num = {i}\n{df.loc[(df['Random Starts'] == i) & (df['Max Iterations'] == j)]}"
            )
            for mwr in mwr_values:
                assert results[mwr]["best_cand"].equals(dask_results[mwr]["best_cand"])
                assert results[mwr]["best_cand_scaled"].equals(
                    dask_results[mwr]["best_cand_scaled"]
                )
                assert results[mwr]["best_val"] == dask_results[mwr]["best_val"]
                assert results[mwr]["best_mties"] == dask_results[mwr]["best_mties"]

    df.to_csv("nusf_test_times.csv", index=False)
    print(df)


if __name__ == "__main__":
    main()
