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
import time
from operator import gt, lt

import numpy as np
import dask.bag as db

from .usf import compute_min_dist


def criterion(
    cand,  # candidates
    args,  # scaling factors for included columns
    nr,  # number of restarts (each restart uses a random set of <nd> points)
    nd,  # design size <= len(candidates)
    mode="maximin",
    hist=None,
    rand_gen=np.random.default_rng(),
):

    mode = mode.lower()
    assert mode in ["maximin", "minimax"], "MODE {} not recognized.".format(mode)
    if mode == "maximin":
        best_val = -1
        fcn = np.mean
        cond = gt
    elif mode == "minimax":
        best_val = 99999
        fcn = np.max
        cond = lt

    # indices of type ...
    idx = args["xcols"]  # Input

    # scaling factors
    scl = args["scale_factors"]
    scl = scl[idx].values

    # history, if provided
    if hist is not None:
        hist_xs = hist[idx].values
    else:
        hist_xs = None

    t0 = time.time()
    choices = []
    for i in range(nr):  # create all the choices upfront
        choices.append(rand_gen.choice(cand.index, nd, replace=False))
    nrs = db.from_sequence(choices, npartitions=(nr // 1000) + 1)
    part_choices = nrs.map_partitions(
        choose_from_partition, best_val, cand, idx, scl, hist_xs, fcn, cond
    ).to_dataframe()
    if mode == "maximin":
        best_val = part_choices["val"].max()
    else:
        best_val = part_choices["val"].min()

    best = part_choices[part_choices.val == best_val].compute()

    elapsed_time = time.time() - t0

    results = {
        "best_cand": best["cand"].iloc[0],
        "best_index": best["index"].iloc[0],
        "best_val": best["val"].iloc[0],
        "best_dmat": best["dmat"].iloc[0],
        "dmat_cols": idx,
        "mode": mode,
        "design_size": nd,
        "num_restarts": nr,
        "elapsed_time": elapsed_time,
    }

    return results


def choose_from_partition(nums, starting_val, cand, idx, scl, hist_xs, fcn, cond):
    best_cand, best_val = None, starting_val
    for i in nums:
        rand_cand = choose(i, cand, idx, scl, hist_xs, fcn)
        if cond(rand_cand["val"], best_val):
            best_cand = rand_cand
            best_val = rand_cand["val"]
    return [best_cand]


def choose(choice, cand, idx, scl, hist_xs, fcn):
    rand_cand = cand.loc[choice]
    # extract the relevant columns (of type 'Input' only) for dist computations
    dmat, min_dist = compute_min_dist(rand_cand[idx].values, scl, hist_xs=hist_xs)
    dist = fcn(min_dist)
    return {
        "cand": rand_cand,
        "index": choice,
        "val": dist,
        "dmat": dmat,
    }