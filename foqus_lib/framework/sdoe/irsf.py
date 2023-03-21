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
from .distance import compute_dist, compute_min_params
import numpy as np
import pandas as pd
import time
import itertools


def unit_scale(xs):
    xmin = np.min(xs, axis=0)
    xmax = np.max(xs, axis=0)
    scaled = (xs - xmin) / (xmax - xmin)

    return scaled, xmin, xmax


def inv_unit_scale(scaled, xmin, xmax):
    return scaled * (xmax - xmin) + xmin


# Pedro: this is almost identical to NUSF's compute_dmat; something to consider if code needs to be refactored
def compute_dmat(cand, hist=None, val=np.inf):
    # Inputs:
    #  cand - numpy array of size (N, nx)
    #  hist - numpy array of shape (nh, nx)
    # Output:
    #  dmat - numpy array of shape (N+nh, N+nh)

    if hist is None:
        dmat = compute_dist(cand, val=val, return_sqrt=True)
    else:
        dmat = compute_dist(cand, hist_xs=hist, val=val, return_sqrt=True)
        # if history exists, set history-history distances to some large value
        nhist = len(hist)
        dmat[-nhist:, -nhist:] = np.max(dmat)

    np.fill_diagonal(dmat, val)

    return dmat


# Pedro: this is almost identical to NUSF's update_min_dist; something to consider if code needs to be refactored
def update_min_dist(rcand, cand, md, mdpts, mties, dmat, hist=None, val=np.inf):
    def update_dmat(row, rcand, dmat, k, val=np.inf):
        xs = rcand if hist is None else np.concatenate((rcand, hist))

        m = np.sqrt(np.sum(np.square(row - xs), axis=1))
        m[k] = val

        dmat_ = np.copy(dmat)
        dmat_[k, :] = dmat_[:, k] = m

        return dmat_

    def step(pt, rcand, cand, mdpts, dmat):
        i, j = pt  # i=mdpts index to remove from rcand; j=cand index to add to rcand
        rcand_ = np.copy(rcand)
        row = cand[j]
        k = mdpts[i]
        rcand_[k] = row
        dmat_ = update_dmat(row, rcand_, dmat, k, val)
        md_, mdpts_, mties_ = compute_min_params(dmat_)

        return rcand_, md_, mdpts_, mties_, dmat_, j, k

    # exclude mdpts indices corresponding to history
    mdpts_cand = mdpts[mdpts < len(rcand)]
    n_mdpts = len(mdpts_cand)

    # 02/28: removed ncand as input param; calculated below now
    n_cand = len(cand)
    # initialize d0 and mt0
    d0 = np.zeros((n_mdpts, n_cand))
    # min dist when the ith point to remove is replaced with the jth candidate to add
    mt0 = np.zeros((n_mdpts, n_cand))
    # number of ties when the ith point to remove is replaced with the jth candidate to add

    for pt in np.ndindex(n_mdpts, n_cand):
        i, j = pt
        _, d0[i, j], _, mt0[i, j], _, _, _ = step(pt, rcand, cand, mdpts_cand, dmat)

    d0_max = np.max(d0)
    pts = np.argwhere(d0 == d0_max)
    update_ = True
    added_ = None
    removed_ = None

    if d0_max > md:  # if maximin increased
        k = np.random.randint(pts.shape[0])
        pt = pts[k]
        rcand_, md_, mdpts_, mties_, dmat_, added_, removed_ = step(
            pt, rcand, cand, mdpts_cand, dmat
        )
    elif d0_max == md:
        nselect = np.argwhere(mt0[pts[:, 0], pts[:, 1]] < mties).flatten()
        if nselect.size > 0:
            pt = pts[
                np.random.choice(nselect)
            ]  # take the subset of pts where the corresponding ties is less than mties
            rcand_, md_, mdpts_, mties_, dmat_, added_, removed_ = step(
                pt, rcand, cand, mdpts_cand, dmat
            )
        else:
            return rcand, md, mdpts, mties, dmat, None, None, False
    else:
        update_ = False
        added_ = None
        removed_ = None
        return rcand, md, mdpts, mties, dmat, None, None, False

    return rcand_, md_, mdpts_, mties_, dmat_, added_, removed_, update_


def update_pareto_front(newdesX, newdesY, newpt, curpfdesX, curpfdesY, curpf):
    g1 = newpt[0] > curpf[:, 0]
    g2 = newpt[1] > curpf[:, 1]

    ge1 = newpt[0] >= curpf[:, 0]
    ge2 = newpt[1] >= curpf[:, 1]

    l1 = np.logical_not(ge1)
    l2 = np.logical_not(ge2)

    le1 = np.logical_not(g1)
    le2 = np.logical_not(g2)

    eq1 = newpt[0] == curpf[:, 0]
    eq2 = newpt[1] == curpf[:, 1]

    cond1 = (
        np.multiply(g1, ge2) + np.multiply(g2, ge1)
    ) == 0  # PN: should be able to simplify this
    cond1 = cond1.flatten()
    cond2 = np.sum(
        np.multiply(l1, le2) + np.multiply(l2, le1) + np.multiply(eq1, eq2)
    )  # PN: and this

    if np.any(cond1):
        n_desX = len(newdesX)
        idxs = np.where(cond1)[0]
        idxs_des = np.array([i * n_desX + np.arange(n_desX) for i in idxs]).flatten()

        newpf = curpf[idxs]
        newpfdesX = curpfdesX[idxs_des]
        newpfdesY = curpfdesY[idxs_des]
    else:
        newpf = np.empty((0, len(newpt)))
        newpfdesX = np.empty((0, np.shape(newdesX)[1]))
        newpfdesY = np.empty((0, np.shape(newdesY)[1]))

    if cond2 == 0:
        newpf = np.append(newpf, [newpt], axis=0)
        newpfdesX = np.append(newpfdesX, newdesX, axis=0)
        newpfdesY = np.append(newpfdesY, newdesY, axis=0)
    return newpfdesX, newpfdesY, newpf


def CombPF(PFnew, PFcur=None):

    if PFcur is None:
        return PFnew

    combined_pf = PFcur
    dnew = len(PFnew[2])
    N = int(len(PFnew[0]) / dnew)

    for s in range(dnew):
        combined_pf = update_pareto_front(
            PFnew[0][s * N : (s + 1) * N, :],
            PFnew[1][s * N : (s + 1) * N, :],
            PFnew[2][s, :],
            combined_pf[0],
            combined_pf[1],
            combined_pf[2],
        )

    return combined_pf


# Pedro: this is almost identical to NUSF's criterion; something to consider if code needs to be refactored
def criterion_X(
    cand,  # candidates
    maxit,  # maximum iterations
    nr,  # number of restarts (each restart uses a random set of <nd> points)
    nd,  # design size <= len(candidates)
    mode="maximin",
    hist=None,
):

    _mode = mode.lower()

    ncand = len(cand)

    best_md = 0
    best_mties = 0

    for i in range(nr):

        print("Random start {}".format(i))

        # sample without replacement <nd> indices
        rand_index = np.random.choice(ncand, nd, replace=False)
        rcand = cand[rand_index]
        dmat = compute_dmat(rcand, hist)
        md, mdpts, mties = compute_min_params(dmat)

        update_ = True
        it = 0

        while update_ and (it < maxit):

            (
                rcand_,
                md_,
                mdpts_,
                mties_,
                dmat_,
                added_,
                removed_,
                update_,
            ) = update_min_dist(rcand, cand, md, mdpts, mties, dmat, hist=hist)

            if update_:
                rcand = rcand_
                md = md_
                mdpts = mdpts_
                mties = mties_
                dmat = dmat_
                if added_:
                    rand_index[removed_] = added_

            it += 1

        if (md > best_md) or ((md == best_md) and (mties < best_mties)):
            best_md = md
            best_mties = mties

    return best_md


def XY_min_dist(cand_x, cand_y, mpdx, mpdy, wt, hist_x=None, hist_y=None, val=np.inf):

    # to do: add checks on hist_x, hist_y (both [don't] exist, same number of points)
    dmat_x = compute_dmat(cand_x, hist_x, val)
    dmat_y = compute_dmat(cand_y, hist_y, val)

    # for compatibility with compute_min_params,
    # if history exists, set history-history distances to some large value
    if hist_x is not None and hist_y is not None:
        nhist = len(hist_x)
        dmat_x[-nhist:, -nhist:] = np.max(dmat_x)
        dmat_y[-nhist:, -nhist:] = np.max(dmat_y)

    dmat_xy = (wt / mpdx) * dmat_x + ((1 - wt) / mpdy) * dmat_y

    if hist_x is not None and hist_y is not None:
        dmat_xy[-nhist:, -nhist:] = np.max(dmat_xy)

    # np.fill_diagonal(dmat_xy, val) #Pedro: check that this is not necessary

    md, mdpts, mties = compute_min_params(dmat_xy)

    return dmat_xy, dmat_x, dmat_y, md, mdpts, mties


def update_min_xydist(
    des_x,
    des_y,
    cand_x,
    cand_y,
    md,
    mdpts,
    mties,
    dmat_xy,
    dmat_x,
    dmat_y,
    mpdx,
    mpdy,
    wt,
    PF_des_x,
    PF_des_y,
    PF_mat,
    hist_x=None,
    hist_y=None,
    val=np.inf,
):

    # to do: check that hist_x and hist_y both (don't) exist

    def update_dmat_xy(
        row_x, row_y, des_x, des_y, dmat_xy, dmat_x, dmat_y, k, val=np.inf
    ):

        xs = des_x if hist_x is None else np.concatenate((des_x, hist_x))
        m_x = np.sqrt(np.sum(np.square(row_x - xs), axis=1))
        m_x[k] = val
        dmat_x_ = np.copy(dmat_x)
        dmat_x_[k, :] = dmat_x_[:, k] = m_x

        ys = des_y if hist_y is None else np.concatenate((des_y, hist_y))
        m_y = np.sqrt(np.sum(np.square(row_y - ys), axis=1))
        m_y[k] = val
        dmat_y_ = np.copy(dmat_y)
        dmat_y_[k, :] = dmat_y_[:, k] = m_y

        dmat_xy_ = np.copy(dmat_xy)
        dmat_xy_[k, :] = dmat_xy_[:, k] = wt / mpdx * m_x + (1 - wt) / mpdy * m_y

        return dmat_xy_, dmat_x_, dmat_y_

    def step(
        pt, des_x, des_y, cand_x, cand_y, mdpts, dmat_xy, dmat_x, dmat_y, val=np.inf
    ):

        i, j = pt  # i=mdpts index to remove from rcand; j=cand index to add to rcand

        des_x_ = np.copy(des_x)
        des_y_ = np.copy(des_y)
        row_x = cand_x[j]
        row_y = cand_y[j]
        k = mdpts[i]
        des_x_[k] = row_x
        des_y_[k] = row_y
        dmat_xy_, dmat_x_, dmat_y_ = update_dmat_xy(
            row_x, row_y, des_x_, des_y_, dmat_xy, dmat_x, dmat_y, k, val
        )

        md_, mdpts_, mties_ = compute_min_params(dmat_xy_)

        # j: added; k: removed
        return des_x_, des_y_, md_, mdpts_, mties_, dmat_xy_, dmat_x_, dmat_y_, j, k

    ncand = np.shape(cand_x)[0]

    # exclude mdpts indices corresponding to history
    mdpts_cand = mdpts[mdpts < len(des_x)]
    n_mdpts = len(mdpts_cand)

    d0 = np.zeros((n_mdpts, ncand))
    mt0 = np.zeros((n_mdpts, ncand))

    # before:
    for pt in itertools.product(range(n_mdpts), range(ncand)):
        # with Monte Carlo sampling:
        # for pt in itertools.product(
        #     range(n_mdpts), np.random.choice(ncand, ncand_samples, False)
        # ):
        i, j = pt
        des_x_, des_y_, d0[i, j], _, mt0[i, j], _, dmat_x_, dmat_y_, _, _ = step(
            pt, des_x, des_y, cand_x, cand_y, mdpts_cand, dmat_xy, dmat_x, dmat_y
        )

        new_pt = np.array([np.min(dmat_x_), np.min(dmat_y_)])
        PF_des_x, PF_des_y, PF_mat = update_pareto_front(
            des_x_, des_y_, new_pt, PF_des_x, PF_des_y, PF_mat
        )

    d0_max = np.max(d0)
    pts = np.argwhere(d0 == d0_max)
    update_ = True
    added_ = None
    removed_ = None

    if d0_max > md:
        k = np.random.randint(pts.shape[0])
        pt = pts[k]
        (
            des_x_,
            des_y_,
            md_,
            mdpts_cand_,
            mties_,
            dmat_xy_,
            dmat_x_,
            dmat_y_,
            added_,
            removed_,
        ) = step(pt, des_x, des_y, cand_x, cand_y, mdpts_cand, dmat_xy, dmat_x, dmat_y)
    elif d0_max == md:
        nselect = np.argwhere(mt0[pts[:, 0], pts[:, 1]] < mties).flatten()
        if nselect.size > 0:
            pt = pts[np.random.choice(nselect)]
            (
                des_x_,
                des_y_,
                md_,
                mdpts_cand_,
                mties_,
                dmat_xy_,
                dmat_x_,
                dmat_y_,
                added_,
                removed_,
            ) = step(
                pt, des_x, des_y, cand_x, cand_y, mdpts_cand, dmat_xy, dmat_x, dmat_y
            )
        else:
            return (
                des_x,
                des_y,
                md,
                mdpts_cand,
                mties,
                dmat_xy,
                dmat_x,
                dmat_y,
                PF_des_x,
                PF_des_y,
                PF_mat,
                None,
                None,
                False,
            )
            # Pedro: if Monte Carlo sampling is used, then return True in the last index instead
            # to allow for a longer search
    else:
        return (
            des_x,
            des_y,
            md,
            mdpts_cand,
            mties,
            dmat_xy,
            dmat_x,
            dmat_y,
            PF_des_x,
            PF_des_y,
            PF_mat,
            None,
            None,
            False,
        )
        # Pedro: if Monte Carlo sampling is used, then return True in the last index instead
        # to allow for a longer search

    return (
        des_x_,
        des_y_,
        md_,
        mdpts_cand_,
        mties_,
        dmat_xy_,
        dmat_x_,
        dmat_y_,
        PF_des_x,
        PF_des_y,
        PF_mat,
        added_,
        removed_,
        update_,
    )


def irsf_tex(
    cand_x,  # input space candidate
    cand_y,  # response space candidate
    mpdx,
    mpdy,
    wt,
    maxit,
    nd,  # number of points (design size N)
    hist_x=None,
    hist_y=None,
):

    rand_index = np.random.choice(len(cand_x), nd)

    des_x = cand_x[rand_index]
    des_y = cand_y[rand_index]

    dmat_xy, dmat_x, dmat_y, md, mdpts, mties = XY_min_dist(
        des_x, des_y, mpdx, mpdy, wt, hist_x, hist_y
    )
    PF_des_x = des_x
    PF_des_y = des_y
    PF_mat = np.array([[np.min(dmat_x), np.min(dmat_y)]])
    update_ = True
    nit = 0
    while update_ & (nit < maxit):

        (
            des_x_,
            des_y_,
            md_,
            mdpts_,
            mties_,
            dmat_xy_,
            dmat_x_,
            dmat_y_,
            PF_des_x,
            PF_des_y,
            PF_mat,
            added_,
            removed_,
            update_,
        ) = update_min_xydist(  # Assume that this function takes care of history
            des_x,
            des_y,
            cand_x,
            cand_y,
            md,
            mdpts,
            mties,
            dmat_xy,
            dmat_x,
            dmat_y,
            mpdx,
            mpdy,
            wt,
            PF_des_x,
            PF_des_y,
            PF_mat,
            hist_x,
            hist_y,
        )

        nit = nit + 1
        if update_:
            des_x = des_x_
            des_y = des_y_
            md = md_
            mdpts = mdpts_
            mties = mties_
            dmat_xy = dmat_xy_
            dmat_x = dmat_x_
            dmat_y = dmat_y_

    return (
        des_x,
        des_y,
        md,
        mdpts,
        mties,
        dmat_xy,
        dmat_x,
        dmat_y,
        PF_des_x,
        PF_des_y,
        PF_mat,
    )


def criterion_irsf(
    cand_x,  # input space candidate
    cand_y,  # response space candidate
    mpdx,
    mpdy,
    wt,
    maxit,  # maximum iteration
    nr,  # number of random start (startnum)
    nd,  # number of points (design size N)
    mode,
    hist_x,
    hist_y,
):

    (
        _,
        _,
        md,
        _,
        mties,
        _,
        _,
        _,
        PF_des_x,
        PF_des_y,
        PF_mat,
    ) = irsf_tex(cand_x, cand_y, mpdx, mpdy, wt, maxit, nd, hist_x, hist_y)

    md = None

    for i in range(nr - 1):
        (
            _,
            _,
            md_,
            _,
            mties_,
            _,
            _,
            _,
            PF_des_x_,
            PF_des_y_,
            PF_mat_,
        ) = irsf_tex(cand_x, cand_y, mpdx, mpdy, wt, maxit, nd, hist_x, hist_y)
        if (md is None) or ((md_ > md) or (md_ == md) and (mties_ < mties)):
            md = md_
            mties = mties_

        for s in range(PF_mat_.shape[0]):
            PF_des_x, PF_des_y, PF_mat = update_pareto_front(
                PF_des_x_[s * nd : (s + 1) * nd, :],
                PF_des_y_[s * nd : (s + 1) * nd, :],
                PF_mat_[s, :],
                PF_des_x,
                PF_des_y,
                PF_mat,
            )

    _mode = mode

    return PF_des_x, PF_des_y, PF_mat


def criterion(cand, args, nr, nd, mode="maximin", hist=None, test=False):
    cand_x = cand[args["idx"]]
    xcols = list(cand_x.columns)
    cand_x = cand_x.to_numpy()

    cand_y = cand[args["idy"]]
    ycols = list(cand_y.columns)
    cand_y = cand_y.to_numpy()

    if hist is not None:
        ncand = len(cand_x)
        hist_x = hist[args["idx"]].to_numpy()
        hist_y = hist[args["idy"]].to_numpy()

        scaled_x, xmin, xmax = unit_scale(np.concatenate((cand_x, hist_x)))
        scaled_y, ymin, ymax = unit_scale(np.concatenate((cand_y, hist_y)))

        cand_x_norm = scaled_x[:ncand]
        hist_x_norm = scaled_x[ncand:]
        cand_y_norm = scaled_y[:ncand]
        hist_y_norm = scaled_y[ncand:]

    else:
        cand_x_norm, xmin, xmax = unit_scale(cand_x)
        cand_y_norm, ymin, ymax = unit_scale(cand_y)
        hist_x_norm = None
        hist_y_norm = None

    t0 = time.time()
    best_X = criterion_X(cand_x_norm, args["max_iterations"], nr, nd, mode, hist_x_norm)
    print("X space Best value in Normalized Scale: ", best_X)
    t1 = time.time() - t0
    best_Y = criterion_X(cand_y_norm, args["max_iterations"], nr, nd, mode, hist_y_norm)
    print("Y space Best value in Normalized Scale: ", best_Y)

    # if testing, T1 is for X only search, and T2 for PF search with 0.5 weight
    if test:
        t0 = time.time()
        print("Weight: ", round(0.5, 1))
        _ = criterion_irsf(
            cand_x_norm,
            cand_y_norm,
            best_X,
            best_Y,
            0.5,
            args["max_iterations"],
            nr,
            nd,
            mode,
            hist_x_norm,
            hist_y_norm,
        )
        t2 = time.time() - t0

        return {"t1": t1, "t2": t2}

    # Otherwise IRSF for real
    # This is the most important function call of IRSF. For each weight value, its calling 'criterion_irsf' function
    # Possible to parallelize: one call to criterion_irsf for each weight (5 different values)
    PFxdes, PFydes, PFmdvals = {}, {}, {}

    for i in range(len(args["ws"])):
        print("Weight: ", round(args["ws"][i], 1))
        PFxdes[i], PFydes[i], PFmdvals[i] = criterion_irsf(
            cand_x_norm,
            cand_y_norm,
            best_X,
            best_Y,
            args["ws"][i],
            args["max_iterations"],
            nr,
            nd,
            mode,
            hist_x_norm,
            hist_y_norm,
        )
        # Reverse scaling
        PFxdes[i] = inv_unit_scale(PFxdes[i], xmin, xmax)
        PFydes[i] = inv_unit_scale(PFydes[i], ymin, ymax)

    combined_pf = None
    for i in range(len(args["ws"])):
        combined_pf = CombPF([PFxdes[i], PFydes[i], PFmdvals[i]], combined_pf)

    sort_idx = np.argsort(combined_pf[2], axis=0)[:, 0]

    ParetoVal = combined_pf[2][sort_idx]

    PV_df = pd.DataFrame(data=ParetoVal, columns=["Best Input", "Best Response"])
    PV_df.insert(0, "Design", PV_df.index + 1)

    results = {
        "pareto_front": PV_df,
        "design_id": {},
        "des": {},
        "mode": mode,
        "design_size": nd,
        "num_restarts": nr,
        "num_designs": len(PV_df),
    }

    for i, idx in enumerate(sort_idx):
        pareto_x = combined_pf[0][(idx * nd) + np.arange(nd), :]
        pareto_y = combined_pf[1][(idx * nd) + np.arange(nd), :]
        design_df = pd.DataFrame(
            data=np.concatenate((pareto_x, pareto_y), axis=1), columns=xcols + ycols
        )

        results["design_id"][i + 1] = i + 1
        results["des"][i + 1] = design_df

    return results
