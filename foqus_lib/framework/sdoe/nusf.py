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
import numpy as np
from scipy.stats import rankdata
from .distance import compute_dist, compute_min_params
import time
import pandas as pd  # only used for the final output of criterion


def compute_dmat(weight_mat, xcols, wcol, hist=None):
    # Inputs:
    #  weight_mat - numpy array of size (N, nx+1) containing scaled weights
    #       xcols - list of integers corresponding to column indices for inputs
    #        wcol - integer corresponding to the index of the weight column
    #        hist - numpy array of shape (nh, nx+1)
    # Output:
    #        dmat - numpy array of shape (N+nh, N+nh)

    xs = weight_mat[:, xcols]
    wt = weight_mat[:, wcol]

    if hist is None:
        dmat = compute_dist(xs, wt=wt)
    else:
        dmat = compute_dist(xs, wt=wt, hist_xs=hist[:, xcols], hist_wt=hist[:, wcol])
        # for compatibility with compute_min_params,
        # if history exists, set history-history distances to some large value
        nhist = len(hist)
        dmat[-nhist:, -nhist:] = np.max(dmat)

    return dmat


def update_min_dist(rcand, cand, ncand, xcols, wcol, md, mdpts, mties, dmat, hist):
    # Inputs:
    #   rcand - numpy array of size (nd, nx+1) containing currently subset of scaled weights
    #    cand - numpy array of size (ncand, nx+1) containing scaled weights, nd < ncand
    #   ncand - number of candidates to choose <nd> best design from, i.e., cand.shape[0]
    #   xcols - list of integers corresponding to column indices for inputs
    #    wcol - integer corresponding to the index of the weight column
    #      md - scalar representing min(dmat)
    #   mdpts - numpy array of shape (K, ) representing indices where 'md' occurs
    #   mties - scalar representing the number of index pairs (i, j) where i < j and dmat[i, j] == md
    #    dmat - numpy array of shape (M, M) where M = nd+nh
    #    hist - numpy array of shape (nh, nx+1) containing scaled weights
    # Output:
    #   rcand - numpy array of size (nd, nx+1) containing scaled weights
    #      md - scalar representing min(dmat)
    #   mdpts - numpy array of shape (K, 2) representing indices where 'md' occurs
    #   mties - scalar representing number of 'mdpts'
    #    dmat - numpy array of shape (M, M) where M = nx+nh
    #  update - boolean representing whether an update should occur

    def update_dmat(row, rcand, dmat, k, val=9999):
        xs = (
            rcand[:, xcols]
            if hist is None
            else np.concatenate((rcand[:, xcols], hist[:, xcols]))
        )
        weights = (
            rcand[:, wcol]
            if hist is None
            else np.concatenate((rcand[:, wcol], hist[:, wcol]))
        )

        m = np.sum(np.square(row[xcols] - xs), axis=1)
        m = m * row[wcol] * weights
        m[k] = val

        dmat_ = np.copy(dmat)
        dmat_[k, :] = dmat_[:, k] = m

        return dmat_

    def step(pt, rcand, cand, mdpts, dmat):
        i, j = pt  # i=mdpts index to remove from rcand; j=cand index to add to rcand
        rcand_ = rcand.copy()
        row = cand[j]
        k = mdpts[i]
        rcand_[k] = row
        dmat_ = update_dmat(row, rcand_, dmat, k)
        md_, mdpts_, mties_ = compute_min_params(dmat_)

        return rcand_, md_, mdpts_, mties_, dmat_, j, k

    # exclude mdpts indices corresponding to history
    mdpts_cand = mdpts[mdpts < len(rcand)]
    n_mdpts = len(mdpts_cand)

    # initialize d0 and mt0
    d0 = np.zeros(
        (n_mdpts, ncand)
    )  # min dist when the ith point to remove is replaced with the jth candidate to add
    mt0 = np.zeros(
        (n_mdpts, ncand)
    )  # number of ties when the ith point to remove is replaced with the jth candidate to add

    for pt in np.ndindex(n_mdpts, ncand):
        i, j = pt
        _, d0[i, j], _, mt0[i, j], _, _, _ = step(pt, rcand, cand, mdpts_cand, dmat)

    d0_max = np.max(d0)
    pts = np.argwhere(d0 == d0_max)
    update = True
    added = None
    removed = None

    if d0_max > md:  # if maximin increased
        _md = d0_max
        k = np.random.randint(pts.shape[0])
        pt = pts[k]
        rcand, md, mdpts, mties, dmat, added, removed = step(
            pt, rcand, cand, mdpts_cand, dmat
        )
    elif d0_max == md:
        nselect = np.argwhere(mt0[pts[:, 0], pts[:, 1]] < mties).flatten()
        if nselect.size > 0:
            pt = pts[
                np.random.choice(nselect)
            ]  # take the subset of pts where the corresponding ties is less than mties
            rcand, md, mdpts, mties, dmat, added, removed = step(
                pt, rcand, cand, mdpts_cand, dmat
            )
    else:
        update = False
        added = None
        removed = None

    return rcand, md, mdpts, mties, dmat, added, removed, update


def scale_xs(mat_, xcols):
    # Inputs:
    #   mat_ - numpy array of size (nd, nx+1) containing original inputs
    #  xcols - list of integers corresponding to column indices for inputs
    # Output:
    #    mat - numpy array of size (nd, nx+1) containing the scaled inputs
    #   xmin - numpy array of shape (1, nx)
    #   xmax - numpy array of shape (1, nx)

    mat = mat_.copy()
    xs = mat[:, xcols]

    # scale the inputs
    # save xmin, xmax for inverse scaling later
    xmin = np.min(xs, axis=0)
    xmax = np.max(xs, axis=0)
    # -1 to 1 scaling:
    # mat[:, xcols] = (xs - xmin) / (xmax - xmin) * 2 - 1
    # 0 to 1 scaling:
    mat[:, xcols] = (xs - xmin) / (xmax - xmin)

    return mat, xmin, xmax


def scale_y(scale_method, mwr, mat_, wcol):
    # Inputs:
    #  scale_method - string that denotes the scaling method
    #           mwr - scalar used in scaling
    #          mat_ - numpy array of size (nd, nx+1) containing original weights
    #          wcol - integer corresponding to the index of the weight column
    # Output:
    #           mat - numpy array of size (nd, nx+1) containing the scaled weights

    mat = mat_.copy()

    def direct_mwr(mwr, mat, wcol):
        wts = mat[:, wcol]
        wmin = np.min(wts)
        wmax = np.max(wts)

        # equal weights:
        if wmin != wmax:
            mat[:, wcol] = 1 + (mwr - 1) * (wts - wmin) / (wmax - wmin)
        return mat

    def ranked_mwr(mwr, mat, wcol):
        mat[:, wcol] = rankdata(mat[:, wcol], method="dense")
        return direct_mwr(mwr, mat, wcol)

    # equivalent to if-else statements, but easier to maintain
    methods = {"direct_mwr": direct_mwr, "ranked_mwr": ranked_mwr}

    return methods[scale_method](mwr, mat, wcol)


# Not needed because we are using the index to look up the original rows
def inv_scale_xs(mat_, xmin, xmax, xcols):
    # Inputs:
    #   mat_ - numpy array of size (nd, nx+1) containing scaled inputs
    #   xmin - numpy array of shape (1, nx) from before scaling
    #   xmax - numpy array of shape (1, nx) from before scaling
    #  xcols - list of integers corresponding to column indices for inputs
    # Output:
    #    mat - numpy array of size (nd, nx+1) containing the original inputs

    # inverse-scale the inputs
    mat = mat_.copy()
    xs = mat[:, xcols]
    # -1 to 1 scaling
    # mat[:, xcols] = (xs + 1) / 2 * (xmax - xmin) + xmin
    # 0 to 1 scaling
    mat[:, xcols] = xs * (xmax - xmin) + xmin

    return mat


def criterion(
    cand,  # candidates
    args,  # maximum number of iterations, mwr values, scale method, index types
    nr,  # number of restarts (each restart uses a random set of <nd> points)
    nd,  # design size <= len(candidates)
    mode="maximin",
    hist=None,
):

    ncand = len(cand)
    if hist is not None:
        nhist = len(hist)
    assert nd <= ncand, "Number of designs exceeds number of available candidates."

    mode = mode.lower()
    assert (
        mode == "maximin"
    ), "MODE {} not recognized for NUSF. Only MAXIMIN is currently supported.".format(
        mode
    )

    T = args["max_iterations"]
    mwr_vals = args["mwr_values"]
    scale_method = args["scale_method"]

    # index types
    idx_np = [cand.columns.get_loc(i) for i in args["xcols"]]
    idw_np = cand.columns.get_loc(args["wcol"])

    cand_np_ = cand.to_numpy()
    cand_np_unscaled = cand_np_.copy()

    # Combine candidates and history before scaling
    if hist is None:
        cand_np_, _xmin, _xmax = scale_xs(cand_np_, idx_np)
    else:
        cand_np_, _xmin, _xmax = scale_xs(
            np.concatenate((cand_np_, hist.to_numpy())), idx_np
        )

    def step(mwr):
        cand_np = scale_y(scale_method, mwr, cand_np_, idw_np)

        if hist is None:
            hist_np = None
        else:
            hist_np = cand_np[-nhist:]
            cand_np = cand_np[:ncand]

        best_cand = []
        best_md = 0
        best_mties = 0
        best_index = []

        t0 = time.time()

        for i in range(nr):

            print("Random start {}".format(i))

            # sample without replacement <nd> indices
            wts = cand_np[:, idw_np]
            wts_sum = np.sum(wts)
            prob = wts / wts_sum
            rand_index = np.random.choice(ncand, nd, replace=False, p=prob)

            # extract the <nd> rows
            rcand = cand_np[rand_index]
            dmat = compute_dmat(rcand, idx_np, idw_np, hist=hist_np)
            md, mdpts, mties = compute_min_params(dmat)

            update_ = True
            t = 0

            while update_ and (t < T):

                (
                    rcand_,
                    md_,
                    mdpts_,
                    mties_,
                    dmat_,
                    added_,
                    removed_,
                    update_,
                ) = update_min_dist(
                    rcand,
                    cand_np,
                    ncand,
                    idx_np,
                    idw_np,
                    md,
                    mdpts,
                    mties,
                    dmat,
                    hist=hist_np,
                )

                if update_:
                    rcand = rcand_
                    md = md_
                    mdpts = mdpts_
                    mties = mties_
                    dmat = dmat_
                    if added_:
                        rand_index[removed_] = added_

                t += 1

            if (md > best_md) or ((md == best_md) and (mties < best_mties)):
                best_index = rand_index  #
                best_cand = rcand
                best_md = md
                best_mdpts = mdpts
                best_mties = mties
                best_dmat = dmat

            elapsed_time = time.time() - t0
            print("Best minimum distance for this random start: {}".format(best_md))

        # no need to inverse-scale; can just use the indices to look up original rows in cand_
        best_cand_unscaled = cand_np_unscaled[best_index]

        best_cand = pd.DataFrame(best_cand, index=best_index, columns=list(cand))
        best_cand_unscaled = pd.DataFrame(
            best_cand_unscaled, index=best_index, columns=list(cand)
        )

        results = {
            "best_cand_scaled": best_cand,
            "best_cand": best_cand_unscaled,
            "best_index": best_index,
            "best_val": best_md,
            "best_mdpts": best_mdpts,
            "best_mties": best_mties,
            "best_dmat": best_dmat,
            "mode": mode,
            "design_size": nd,
            "num_restarts": nr,
            "mwr": mwr,
            "elapsed_time": elapsed_time,
        }

        return results

    results = {}
    for mwr in mwr_vals:
        print(">>>>>> mwr={} <<<<<<".format(mwr))
        res = step(mwr)
        print("Best NUSF Design in Scaled Coordinates:\n", res["best_cand_scaled"])
        print("Best NUSF Design in Original Coordinates:\n", res["best_cand"])
        print("Best value in Normalized Scale:", res["best_val"])
        print("Elapsed time:", res["elapsed_time"])
        results[mwr] = res

    return results
