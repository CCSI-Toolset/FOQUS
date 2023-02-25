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
from operator import lt, gt
import numpy as np
from .distance import compute_dist
import time


def compute_min_dist(mat, scl, hist_xs=None):
    dmat = compute_dist(mat, scl=scl, hist_xs=hist_xs)
    min_dist = np.min(dmat, axis=0)
    return dmat, min_dist


def criterion(
    cand,  # candidates
    args,  # scaling factors for included columns
    nr,  # number of restarts (each restart uses a random set of <nd> points)
    nd,  # design size <= len(candidates)
    mode="maximin",
    hist=None,
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
    _id_ = args["icol"]  # Index
    idx = args["xcols"]  # Input

    # scaling factors
    scl = args["scale_factors"]
    scl = scl[idx].values

    # history, if provided
    if hist is not None:
        hist_xs = hist[idx].values
    else:
        hist_xs = None

    best_cand = []
    _best_rand_sample = []

    t0 = time.time()
    for i in range(nr):

        print("Random start {}".format(i))

        # sample without replacement <nd> indices
        rand_index = np.random.choice(cand.index, nd, replace=False)
        # extract the <nd> rows
        rand_cand = cand.loc[rand_index]
        # extract the relevant columns (of type 'Input' only) for dist computations
        dmat, min_dist = compute_min_dist(rand_cand[idx].values, scl, hist_xs=hist_xs)
        dist = fcn(min_dist)

        if cond(dist, best_val):
            best_cand = rand_cand
            best_index = rand_index  # for debugging
            best_val = dist  # for debugging
            best_dmat = dmat  # used for ranking candidates

        elapsed_time = time.time() - t0
    # best_cand.insert(loc=0, column=id_, value=best_cand.index)

    results = {
        "best_cand": best_cand,
        "best_index": best_index,
        "best_val": best_val,
        "best_dmat": best_dmat,
        "dmat_cols": idx,
        "mode": mode,
        "design_size": nd,
        "num_restarts": nr,
        "elapsed_time": elapsed_time,
    }

    return results
