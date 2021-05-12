###############################################################################
# FOQUS Copyright (c) 2012 - 2021, by the software owners: Oak Ridge Institute
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
#
###############################################################################
from operator import itemgetter
import random
import numpy as np
import pandas as pd
import time


def criterion(cand, args, nr, nd, mode='maximin', hist=None, test=False):
    _hist = hist
    inp_x = cand[args['idx']]
    xcols = list(inp_x.columns)
    norm_x = unitscale_cand(inp_x)
    inp_y = cand[args['idy']]
    ycols = list(inp_y.columns)
    norm_y = unitscale_cand(inp_y)

    # if testing, T1 is for X only search, and T2 for PF search with 0.5 weight
    if test:
        t0 = time.time()
        design_X, best_X, mdpts_X, mties_X, dist_mat_X = criterion_X(norm_x, args['max_iterations'], nd, nr, mode)
        print("X space Best value in Normalized Scale: ", best_X)
        t1 = time.time() - t0
        design_Y, best_Y, mdpts_Y, mties_Y, dist_mat_Y = criterion_X(norm_y, args['max_iterations'], nd, nr, mode)
        print("Y space Best value in Normalized Scale: ", best_Y)

        # We are initializing the following dictionaries here
        best_xdes, best_ydes, bestcrit, bestpoints, best_mdties, best_wdmat, \
        best_wdxmat, best_wdymat, PFxdes, PFydes, PFmdvals = {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}

        args['ws'] = [0.5]
        for i in range(len(args['ws'])):
            t0 = time.time()
            print("Weight: ", round(args['ws'][i], 1))
            best_xdes[i], best_ydes[i], bestcrit[i], bestpoints[i], best_mdties[i], best_wdmat[i], \
            best_wdxmat[i], best_wdymat[i], PFxdes[i], PFydes[i], PFmdvals[i] = criterion_irsf(norm_x,
                                                                                               norm_y,
                                                                                               nd,
                                                                                               best_X,
                                                                                               best_Y,
                                                                                               args['ws'][i],
                                                                                               args['max_iterations'],
                                                                                               nr,
                                                                                               mode)
            t2 = time.time() - t0

        results = {'t1': t1,
                   't2': t2}

        return results

    # Otherwise IRSF for real
    # Input only and output only optimization are here Using the same function call 'criterion_X'. These are essentially
    # the boundary points for the Pareto Front.
    # Possible to parallelize: search for X and Y at the same time
    design_X, best_X, mdpts_X, mties_X, dist_mat_X = criterion_X(norm_x, args['max_iterations'], nd, nr, mode)
    print("X space Best value in Normalized Scale: ", best_X)

    design_Y, best_Y, mdpts_Y, mties_Y, dist_mat_Y = criterion_X(norm_y, args['max_iterations'], nd, nr, mode)
    print("Y space Best value in Normalized Scale: ", best_Y)

    # We are initializing the following dictionaries here
    best_xdes, best_ydes, bestcrit, bestpoints, best_mdties, best_wdmat, \
    best_wdxmat, best_wdymat, PFxdes, PFydes, PFmdvals = {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}

    # This is the most important function call of IRSF. For each weight value, its calling 'criterion_irsf' function
    # and returning
    # Possible to parallelize: one call to criterion_irsf for each weight (5 different values)
    for i in range(len(args['ws'])):
        print("Weight: ", round(args['ws'][i], 1))
        best_xdes[i], best_ydes[i], bestcrit[i], bestpoints[i], best_mdties[i], best_wdmat[i], \
        best_wdxmat[i], best_wdymat[i], PFxdes[i], PFydes[i], PFmdvals[i] = criterion_irsf(norm_x,
                                                                                           norm_y,
                                                                                           nd,
                                                                                           best_X,
                                                                                           best_Y,
                                                                                           args['ws'][i],
                                                                                           args['max_iterations'],
                                                                                           nr,
                                                                                           mode)

    # Pareto Front for each weight i is created here. For example if 3 Pareto solutions were found for ith weight, and
    # the design size is 10, then PFxdes will contain all 3 designs (10 each) in an order, so the number of rows in
    # PFxdes is 30.

    # The following 4 lines are basically constructing a combined Pareto Front for all weight values
    # (Here 0.1, 0.3, 0.5, 0.7 and 0.9) all together.

    PFcomb = [PFxdes[0], PFydes[0], PFmdvals[0]]
    for i in range(1, len(args['ws'])):
        temp_new = [PFxdes[i], PFydes[i], PFmdvals[i]]
        PFcomb = CombPF(temp_new, PFcomb, nd)

    ParetoVal, ParetoX, ParetoY, PV, PX, PY = {}, {}, {}, {}, {}, {}
    N1 = len(PFcomb[2])
    for i in range(N1):
        ParetoVal[i] = PFcomb[2][i, :]
        ParetoX[i] = []
        ParetoY[i] = []
        for j in range(nd):
            ParetoX[i].append(np.array(PFcomb[0][(i*nd)+j, :]).flatten())
            ParetoY[i].append(np.array(PFcomb[1][(i*nd)+j, :]).flatten())

    indx1 = np.argsort(PFcomb[2], axis=0)[:, 0]

    for i in range(len(indx1)):
        j = int(indx1[i])
        PV[i] = np.array(ParetoVal[j])
        PX[i] = ParetoX[j]
        PY[i] = ParetoY[j]

    PV_tuple = ()
    for key in PV:
        if len(PV[key].shape) == 1:
            PV[key] = np.expand_dims(PV[key], axis=0)
        PV_tuple += (PV[key],)
    PV_arr = np.concatenate(PV_tuple, axis=0)
    PV_df = pd.DataFrame(data=PV_arr, columns=['Best Input', 'Best Response'])
    PV_df.insert(0, 'Design', PV_df.index + 1)

    design_dict = {}

    xcols.extend(ycols)
    for key in PX:
        temp = np.concatenate((PX[key], PY[key]), axis=1)
        df = pd.DataFrame(data=temp, columns=xcols)
        design_dict[key+1] = df

    results = {}
    for design in design_dict:
        results[design] = {'pareto_front': PV_df,
                           'design': design,
                           'des': design_dict[design],
                           'mode': mode,
                           'design_size': nd,
                           'num_restarts': nr,
                           'num_designs': len(PV_df)}

    return results


def unitscale_cand(cand):
    cand_arr = np.asarray(cand)
    norm_cand = np.zeros((cand_arr.shape[0], cand_arr.shape[1]))
    for i in range(cand.shape[1]):
        norm_cand[:, i] = (1 / (max(cand_arr[:, i]) - min(cand_arr[:, i]))) * (cand_arr[:, i] - min(cand_arr[:, i])) - 0
    return norm_cand


def Inv_scale_cand(cand, xmin, xmax):
    cand_arr = np.asarray(cand)
    inv_norm_cand = np.zeros((len(cand_arr), len(cand_arr.T)))
    for i in range(cand_arr.shape[1] - 1):
        inv_norm_cand[:, i] = ((cand_arr[:, i] + 1) / 2) * (xmax[i] - xmin[i]) + xmin[i]
    inv_norm_cand[:, -1] = cand_arr[:, -1]
    return inv_norm_cand


# BN: take a look at this function
def checkon2xy(newdesX, newdesY, newpt, curpfdesX, curpfdesY, curpf):
    # This is the main routine that constructs the ParetoFront
    curpf = np.matrix(curpf)
    g1 = newpt[0, 0] > curpf[:, 0]
    g2 = newpt[0, 1] > curpf[:, 1]

    ge1 = newpt[0, 0] >= curpf[:, 0]
    ge2 = newpt[0, 1] >= curpf[:, 1]

    l1 = newpt[0, 0] < curpf[:, 0]
    l2 = newpt[0, 1] < curpf[:, 1]

    le1 = newpt[0, 0] <= curpf[:, 0]
    le2 = newpt[0, 1] <= curpf[:, 1]

    eq1 = newpt[0, 0] == curpf[:, 0]
    eq2 = newpt[0, 1] == curpf[:, 1]

    cond1 = (np.multiply(g1, ge2) + np.multiply(g2, ge1)) == 0
    cond1 = np.asarray(cond1).flatten()
    cond2 = np.sum(np.multiply(l1, le2) + np.multiply(l2, le1) + np.multiply(eq1, eq2))
    cond3 = np.asarray(range(len(curpf))).flatten()[cond1]

    if len(cond3) > 0:

        cond4 = []

        for i in range(len(cond3)):
            dd = np.shape(newdesX)[0]
            temp99 = cond3[i] * dd + np.array(range(dd))
            cond4 = np.append(cond4, temp99)
            cond4 = cond4.astype(int)

    if len(cond3) == 0:
        newpf = np.empty((0, np.shape(newpt)[1]))
        newpfdesX = np.empty((0, np.shape(newdesX)[1]))
        newpfdesY = np.empty((0, np.shape(newdesY)[1]))

    else:
        newpf = np.asarray(curpf)[np.asarray(cond3).flatten()]
        curpfdesX = np.matrix(curpfdesX)
        newpfdesX = itemgetter(cond4)(curpfdesX)
        newpfdesY = itemgetter(cond4)(curpfdesY)

    if cond2 == 0:
        newpf = np.append(newpf, newpt, axis=0)
        newpfdesX = np.append(newpfdesX, newdesX, axis=0)
        newpfdesY = np.append(newpfdesY, newdesY, axis=0)

    return newpfdesX, newpfdesY, newpf


# BN: take a look at this function
def update_min_xydist(Dx, Dy, wt, md_xy, mdpoints, mties_xy, dist_xymat, dist_xmat,
                      dist_ymat, xmat, ymat, mpdx, mpdy, PFxdes, PFydes, PFmat):
    Nxx = int(np.shape(Dx)[0])
    ncolsxx = int(np.shape(Dx)[1])
    Nyy = int(np.shape(Dy)[0])
    ncolsyy = int(np.shape(Dy)[1])
    nxcand = int(np.shape(xmat)[0])
    cur_xdes = np.matrix(Dx)
    cur_ydes = np.matrix(Dy)
    cur_md = md_xy
    cur_mdpts = mdpoints
    cur_mties = mties_xy
    cur_dist_xymat = dist_xymat
    cur_dist_xmat = dist_xmat
    cur_dist_ymat = dist_ymat

    _cur_xmat = xmat
    _cur_ymat = np.matrix(ymat)
    PFdesX = PFxdes

    PFdesY = PFydes
    PFvals = PFmat
    ymat = np.matrix(ymat)

    d0 = np.zeros((len(cur_mdpts), nxcand))
    mt0 = np.zeros((len(cur_mdpts), nxcand))

    for i in range(len(cur_mdpts)):
        for j in range(nxcand):
            new_dist_xmat = np.matrix(cur_dist_xmat)
            new_dist_ymat = np.matrix(cur_dist_ymat)
            new_dist_xymat = np.matrix(cur_dist_xymat)
            new_xdes = np.matrix(cur_xdes)
            new_ydes = np.matrix(cur_ydes)
            new_xdes[cur_mdpts[i], :] = xmat[j, :]
            new_ydes[cur_mdpts[i], :] = ymat[j, :]
            x = (np.repeat(np.reshape(xmat[j, :], (ncolsxx, 1)), Nxx, axis=1).T - new_xdes[:, :])
            new_dist_xmat[cur_mdpts[i], :] = np.sum(np.square(x), axis=1).T / mpdx
            new_dist_xmat[:, cur_mdpts[i]] = new_dist_xmat[cur_mdpts[i], :].T
            y = (np.repeat(np.reshape(ymat[j, :], (ncolsyy, 1)), Nyy, axis=1).T - new_ydes[:, :])
            new_dist_ymat[cur_mdpts[i], :] = np.sum(np.square(y), axis=1).T / mpdy
            new_dist_ymat[:, cur_mdpts[i]] = new_dist_ymat[cur_mdpts[i], :].T
            new_dist_xymat[:, cur_mdpts[i]] = wt * new_dist_xmat[:, cur_mdpts[i]] + (1 - wt) * \
                                              new_dist_ymat[:, cur_mdpts[i]]
            new_dist_xymat[cur_mdpts[i], :] = new_dist_xymat[:, cur_mdpts[i]].T

            np.fill_diagonal(new_dist_xmat, 9999)
            np.fill_diagonal(new_dist_ymat, 9999)
            np.fill_diagonal(new_dist_xymat, 9999)
            newvals = np.matrix([np.min(new_dist_xmat), np.min(new_dist_ymat)])
            d0[i, j] = np.min(new_dist_xymat)
            mt0[i, j] = ((new_dist_xymat == d0[i, j]).sum()) / 2
            temppf1, temppf2, temppf3 = checkon2xy(new_xdes, new_ydes, newvals.flatten(), PFdesX, PFdesY, PFvals)
            PFvals = temppf3
            PFdesX = temppf1
            PFdesY = temppf2
    update = False
    if np.max(d0) > cur_md:
        cur_md = np.max(d0)
        nr = np.nonzero(d0.T == np.max(d0))[1]
        nc = np.nonzero(d0.T == np.max(d0))[0]
        nselect = np.random.randint(len(nr), size=1)
        ni = nr[nselect]
        nj = nc[nselect]
        cur_xdes[cur_mdpts[ni], :] = xmat[nj, :]
        cur_ydes[cur_mdpts[ni], :] = ymat[nj, :]
        x = np.repeat(np.reshape(xmat[nj, :], (ncolsxx, 1)), Nxx, axis=1).T - cur_xdes[:, :]
        cur_dist_xmat[cur_mdpts[ni], :] = np.sum(np.square(x), axis=1).T / mpdx
        cur_dist_xmat[:, cur_mdpts[ni]] = cur_dist_xmat[cur_mdpts[ni], :].T

        y = np.repeat(np.reshape(ymat[nj, :], (ncolsyy, 1)), Nyy, axis=1).T - cur_ydes[:, :]
        cur_dist_ymat[cur_mdpts[ni], :] = np.sum(np.square(y), axis=1).T / mpdy
        cur_dist_ymat[:, cur_mdpts[ni]] = cur_dist_ymat[cur_mdpts[ni], :].T

        cur_dist_xymat[:, cur_mdpts[ni]] = wt * cur_dist_xmat[:, cur_mdpts[ni]] + (1 - wt) * \
                                           cur_dist_ymat[:, cur_mdpts[ni]]
        cur_dist_xymat[cur_mdpts[ni], :] = cur_dist_xymat[:, cur_mdpts[ni]].T
        np.fill_diagonal(cur_dist_xmat, 9999)
        np.fill_diagonal(cur_dist_ymat, 9999)
        cur_dist_xymat2 = cur_dist_xymat
        np.fill_diagonal(cur_dist_xymat2, 9999)
        cur_mdpts = np.sort(np.nonzero(cur_dist_xymat == np.min(cur_dist_xymat2))[0])
        cur_mties = mt0[ni, nj]
        update = True

    elif np.max(d0) == cur_md:

        nr = np.nonzero(d0 == np.max(d0))[0]
        nc = np.nonzero(d0 == np.max(d0))[1]
        nselect = []
        for j in range(len(nr)):
            if mt0[nr[j], nc[j]] < cur_mties:
                nselect = np.append(nselect, j)

        if len(nselect) > 0:
            ns = int(np.random.choice(nselect, size=1))
            ni = nr[ns]
            nj = nc[ns]
            cur_xdes[cur_mdpts[ni], :] = xmat[nj, :]
            cur_ydes[cur_mdpts[ni], :] = ymat[nj, :]
            x = np.repeat(np.reshape(xmat[nj, :], (ncolsxx, 1)), Nxx, axis=1).T - cur_xdes[:, :]
            cur_dist_xmat[cur_mdpts[ni], :] = np.sum(np.square(x), axis=1).T / mpdx

            y = np.repeat(np.reshape(ymat[nj, :], (ncolsyy, 1)), Nyy, axis=1).T - cur_ydes[:, :]
            cur_dist_ymat[cur_mdpts[ni], :] = np.sum(np.square(y), axis=1).T / mpdy
            cur_dist_xymat[:, cur_mdpts[ni]] = wt * cur_dist_xmat[:, cur_mdpts[ni]] + (1 - wt) * \
                                               cur_dist_ymat[:, cur_mdpts[ni]]

            np.fill_diagonal(cur_dist_xmat, 9999)
            np.fill_diagonal(cur_dist_ymat, 9999)
            cur_dist_xymat2 = cur_dist_xymat
            np.fill_diagonal(cur_dist_xymat2, 9999)
            cur_mdpts = np.sort(np.nonzero(cur_dist_xymat == np.min(cur_dist_xymat2))[0])
            cur_mties = mt0[ni, nj]
            update = True

    return cur_xdes, cur_ydes, cur_md, cur_mdpts, cur_mties, cur_dist_xymat, \
           cur_dist_xmat, cur_dist_ymat, PFdesX, PFdesY, PFvals, update


# BN: take a look at this function
def XY_min_dist(Dx, Dy, wt, mpdx, mpdy):  # numpy array of shape (N, ncols) and type 'float'

    Nx, ncolsx = Dx.shape
    Ny, ncolsy = Dy.shape
    dist_xmat = np.full((Nx, Nx), np.nan)
    dist_ymat = np.full((Ny, Ny), np.nan)

    for i in range(Nx):
        x = np.repeat(np.reshape(Dx[i, :], (ncolsx, 1)), Nx, axis=1).T - Dx[:, :]
        y = np.repeat(np.reshape(Dy[i, :], (ncolsy, 1)), Ny, axis=1).T - Dy[:, :]
        dist_xmat[:, i] = np.sum(np.square(x), axis=1)
        dist_ymat[:, i] = np.sum(np.square(y), axis=1)

    np.fill_diagonal(dist_xmat, 9999)
    np.fill_diagonal(dist_ymat, 9999)
    dist_xymat = (wt / mpdx) * dist_xmat + ((1 - wt) / mpdy) * dist_ymat
    md_xy = np.min(dist_xymat)

    nr = np.nonzero(dist_xymat == np.min(dist_xymat))[0]
    nc = np.nonzero(dist_xymat == np.min(dist_xymat))[1]
    mdpts = np.unique(np.sort(np.append(nr, nc)))
    mties = len(nr) / 2
    np.fill_diagonal(dist_xymat, 0)

    return dist_xymat, dist_xmat, dist_ymat, md_xy, mdpts, mties


# BN: take a look at this function
def irsf_tex(cand,   # input space candidate
             resp,   # response space candidate
             numpt,  # number of points (design size N)
             mpdx,
             mpdy,
             wt,
             maxit):

    xmat = np.asarray(cand)
    npp = np.shape(xmat)[1]
    ymat = np.asarray(resp)
    heav = np.heaviside((wt - 0.5), 1)
    cmat = np.c_[xmat, ymat]

    rand_index = random.sample(range(len(cand)), numpt)

    if heav == 1.0:
        cmat_new = cmat[np.lexsort(np.transpose(cmat[:, npp:])[::-1])]
        xmat_new = cmat_new[:, 0:npp]
        ymat_new = cmat_new[:, npp:]
        des_x = np.asarray(itemgetter(*rand_index)(xmat_new))
        des_y = np.asarray(itemgetter(*rand_index)(ymat_new))

    if heav == 0.0:
        cmat_new = cmat[np.lexsort(np.transpose(cmat[:, :-1])[::-1])]
        xmat_new = cmat_new[:, 0:npp]
        ymat_new = cmat_new[:, npp:]
        des_x = np.asarray(itemgetter(*rand_index)(xmat_new))
        des_y = np.asarray(itemgetter(*rand_index)(ymat_new))

    dist_xymat, dist_xmat, dist_ymat, md_xy, mdpoints, mties_xy = XY_min_dist(des_x, des_y, wt, mpdx, mpdy)
    PFdesx = des_x
    PFdesy = des_y
    PFmat = np.matrix([np.min(dist_xmat), np.min(dist_ymat)])
    update = True
    nit = 0
    while update & (nit < maxit):

        update = False
        temp1, temp2, temp3, temp4, temp5, temp6, \
        temp7, temp8, temp9, temp10, temp11, temp12 = update_min_xydist(des_x,
                                                                        des_y,
                                                                        wt,
                                                                        md_xy,
                                                                        mdpoints,
                                                                        mties_xy,
                                                                        dist_xymat,
                                                                        dist_xmat,
                                                                        dist_ymat,
                                                                        xmat,
                                                                        ymat,
                                                                        mpdx,
                                                                        mpdy,
                                                                        PFdesx,
                                                                        PFdesy,
                                                                        PFmat)
        PFdesx = temp9
        PFdesy = temp10
        PFmat = np.matrix(temp11)
        nit = nit + 1
        if temp12:
            des_x = temp1
            des_y = temp2
            md_xy = temp3
            mdpoints = temp4
            mties_xy = temp5
            dist_xymat = temp6
            dist_xmat = temp7
            dist_ymat = temp8
            update = True

    return des_x, des_y, md_xy, mdpoints, mties_xy, dist_xymat, dist_xmat, dist_ymat, PFdesx, PFdesy, PFmat


def criterion_irsf(cand,    # input space candidate
                   resp,    # response space candidate
                   numpt,   # number of points (design size N)
                   mpdx,
                   mpdy,
                   wt,
                   maxit,   # maximum iteration
                   numdes,  # number of random start (startnum)
                   mode):

    temp1, temp2, temp3, temp4, temp5, temp6, temp7, temp8, temp9, temp10, temp11 = irsf_tex(cand,
                                                                                             resp,
                                                                                             numpt,
                                                                                             mpdx,
                                                                                             mpdy,
                                                                                             wt,
                                                                                             maxit)
    des_x = temp1
    des_y = temp2
    md_xy = temp3
    mdpoints = temp4
    mties_xy = temp5
    dist_xymat = temp6
    dist_xmat = temp7
    dist_ymat = temp8
    PFxdes = temp9
    PFydes = temp10
    PFmdvals = np.matrix(temp11)

    for i in range(1, numdes):
        temp1, temp2, temp3, temp4, temp5, temp6, temp7, temp8, temp9, temp10, temp11 = irsf_tex(cand,
                                                                                                 resp,
                                                                                                 numpt,
                                                                                                 mpdx,
                                                                                                 mpdy,
                                                                                                 wt,
                                                                                                 maxit)
        if (temp3 > md_xy) or (temp3 == md_xy) and (temp5 < mties_xy):
            des_x = temp1
            des_y = temp2
            md_xy = temp3
            mdpoints = temp4
            mties_xy = temp5
            dist_xymat = temp6
            dist_xmat = temp7
            dist_ymat = temp8
        for s in range(temp11.shape[0]):
            PFxdes, PFydes, PFmdvals = checkon2xy(temp9[s * numpt:(s + 1) * numpt, :],
                                                  temp10[s * numpt:(s + 1) * numpt, :],
                                                  temp11[s, :].flatten(),
                                                  PFxdes,
                                                  PFydes,
                                                  PFmdvals)

    _mode = mode
    return des_x, des_y, md_xy, mdpoints, mties_xy, dist_xymat, dist_xmat, dist_ymat, PFxdes, PFydes, PFmdvals


def CombPF(PFnew, PFcur, N):

    PFcomb = PFcur
    dnew = len(PFnew[2])
    if dnew == 1:
        PFcomb[0], PFcomb[1], PFcomb[2] = checkon2xy(PFnew[0],
                                                     PFnew[1],
                                                     np.matrix(PFnew[2]),
                                                     PFcomb[0],
                                                     PFcomb[1],
                                                     PFcomb[2])
    else:
        for s in range(dnew):
            PFcomb[0], PFcomb[1], PFcomb[2] = checkon2xy(PFnew[0][s * N:(s + 1) * N, :],
                                                         PFnew[1][s * N:(s + 1) * N, :],
                                                         np.matrix(PFnew[2][s, :]),
                                                         PFcomb[0],
                                                         PFcomb[1],
                                                         PFcomb[2])

    return PFcomb


def X_min_dist(dmat):   # numpy array of shape (N, ncols) and type 'float'

    N, ncols = dmat.shape
    dist_mat = np.full((N, N), np.nan)

    for i in range(N):
        x = np.repeat(np.reshape(dmat[i, :], (ncols, 1)), N, axis=1).T - dmat[:, :]
        dist_mat[:, i] = np.sum(np.square(x), axis=1)

    np.fill_diagonal(dist_mat, 9999)
    min_dist = np.asarray(np.min(dist_mat, axis=0))
    md = np.min(dist_mat)
    nr = np.nonzero(dist_mat == np.min(dist_mat))[0]
    nc = np.nonzero(dist_mat == np.min(dist_mat))[1]
    mdpts = np.unique(np.sort(np.append(nr, nc)))
    mties = len(nr) / 2

    return dist_mat, min_dist, md, mdpts, mties


def update_min_dist(cand_rand, md, mdpts1, mties, Xdist_mat, cand):
    ndes = int(np.shape(cand_rand)[0])
    npt = int(np.shape(cand_rand)[1])
    ncand = int(np.shape(cand)[0])
    cur_des = np.matrix(cand_rand)
    cur_md = md
    cur_mdpts = mdpts1
    cur_mties = mties
    cur_w_mat = Xdist_mat   # type 'object'
    d0 = np.zeros((len(cur_mdpts), ncand))
    mt0 = np.zeros((len(cur_mdpts), ncand))

    for i in range(len(cur_mdpts)):
        for j in range(ncand):
            new_w_mat = np.matrix(Xdist_mat)
            new_des = np.matrix(cur_des)
            new_des[cur_mdpts[i], :] = cand[j, :]
            x = np.repeat(np.reshape(cand[j, :], (npt, 1)), ndes, axis=1).T - new_des[:, :]
            new_w_mat[cur_mdpts[i], :] = (np.sum(np.square(x), axis=1)).T
            new_w_mat[:, cur_mdpts[i]] = new_w_mat[cur_mdpts[i], :].T
            np.fill_diagonal(new_w_mat, 9999)
            d0[i, j] = np.min(new_w_mat)
            mt0[i, j] = ((new_w_mat == d0[i, j]).sum()) / 2
    update = False
    if np.max(d0) > cur_md:
        cur_md = np.max(d0)
        nr = np.nonzero(d0.T == np.max(d0))[1]
        nc = np.nonzero(d0.T == np.max(d0))[0]
        nselect = np.random.randint(len(nr), size=1)
        ni = nr[nselect]
        nj = nc[nselect]
        cur_des[cur_mdpts[ni], :] = cand[nj, :]
        x = np.repeat(np.reshape(cand[nj, :], (npt, 1)), ndes, axis=1).T - cur_des[:, :]
        cur_w_mat[cur_mdpts[ni], :] = (np.sum(np.square(x), axis=1)).T
        cur_w_mat[:, cur_mdpts[ni]] = cur_w_mat[cur_mdpts[ni], :].T
        cur_w_mat2 = np.matrix(cur_w_mat)
        np.fill_diagonal(cur_w_mat2, 9999)
        cur_mdpts = np.sort(np.nonzero(cur_w_mat == np.min(cur_w_mat2))[0])
        cur_mties = mt0[ni, nj]
        update = True

    elif np.max(d0) == cur_md:
        nr = np.nonzero(d0.T == np.max(d0))[1]
        nc = np.nonzero(d0.T == np.max(d0))[0]
        nselect = []
        for j in range(len(nr)):
            if mt0[nr[j], nc[j]] < cur_mties:
                nselect = np.append(nselect, j)
        if len(nselect) > 0:
            ns = int(np.random.choice(nselect, size=1))
            ni = nr[ns]
            nj = nc[ns]
            cur_des[cur_mdpts[ni], :] = cand[nj, :]
            x = np.repeat(np.reshape(cand[nj, :], (npt, 1)), ndes, axis=1).T - cur_des[:, :]
            cur_w_mat[cur_mdpts[ni], :] = (np.sum(np.square(x), axis=1)).T
            cur_w_mat[:, cur_mdpts[ni]] = cur_w_mat[cur_mdpts[ni], :].T
            cur_w_mat2 = np.matrix(cur_w_mat)
            np.fill_diagonal(cur_w_mat2, 9999)
            cur_mdpts = np.sort(np.nonzero(cur_w_mat == np.min(cur_w_mat2))[0])
            cur_mties = mt0[ni, nj]
            update = True

    return cur_des, cur_md, cur_mdpts, cur_mties, cur_w_mat, update


def criterion_X(cand,    # candidates
                maxit,   # maximum iteration
                numpt,   # number of points (design size N)
                numdes,  # number of random start (startnum)
                mode):

    _mode = mode.lower()
    candid = np.asarray(cand)

    best_md = 0.0
    best_mties = 0.0
    for i in range(numdes):
        rand_index = random.sample(range(len(candid)), numpt)
        cand_rand = np.asarray(itemgetter(*rand_index)(candid))
        Xdist_mat, min_dist, md, mdpts, mties = X_min_dist(cand_rand)
        update = True
        nit = 0

        while update & (nit < maxit):
            update = False
            up_cand_rand, up_md, up_mdpts, up_mties, up_Xdist_mat, new_update = update_min_dist(cand_rand,
                                                                                                md,
                                                                                                mdpts,
                                                                                                mties,
                                                                                                Xdist_mat,
                                                                                                cand)
            nit = nit+1
            if new_update:
                cand_rand = up_cand_rand
                md = up_md
                mdpts = up_mdpts
                mties = up_mties
                Xdist_mat = up_Xdist_mat
                update = True

        if (md > best_md) or ((md == best_md) and (mties < best_mties)):
            best_cand_rand = cand_rand
            best_md = md
            best_mdpts = mdpts
            best_mties = mties
            best_w_dist_mat = Xdist_mat

    return best_cand_rand, best_md, best_mdpts, best_mties, best_w_dist_mat
