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
import numpy as np
from scipy.stats import rankdata
from .distance import compute_dist
import time
import pandas as pd  # only used for the final output of criterion


def compute_dmat(weight_mat, xcols, wcol, hist_xs=None, hist_wt=None):

    # Inputs:
    #  weight_mat - numpy array of size (nd, nx+1) containing scaled weights 
    #       xcols - list of integers corresponding to column indices for inputs 
    #        wcol - integer corresponding to the index of the weight column 
    #        hist - numpy array of shape (nh, nx+1) 
    # Output:
    #        dmat - numpy array of shape (nd+nh, nd+nh)

    xs = weight_mat[:, xcols]
    wt = weight_mat[:, wcol]

    dmat = compute_dist(xs, wt=wt, hist_xs=hist_xs, hist_wt=hist_wt)  # symmetric matrix
    return dmat  # symmetric distance matrix


def compute_min_params(dmat):
    # Input:
    #   dmat - numpy array of shape (M, M) where M = nx+nh
    # Output:
    #     md - scalar representing min(dmat)
    #  mdpts - numpy array of shape (K, 2) representing indices where 'md' occurs
    #  mties - scalar representing K, the number of 'mdpts'

    md = np.min(dmat)
    mdpts = np.argwhere(np.triu(dmat) == md)  # check upper triangular matrix
    mties = mdpts.shape[0]                    # number of points returned
    mdpts = np.unique(mdpts.flatten())
    return md, mdpts, mties


def update_min_dist(rcand, cand, ncand, xcols, wcol, md, mdpts, mties, dmat):
    # Inputs:
    #   rcand - numpy array of size (nd, nx+1) containing scaled weights 
    #    cand - numpy array of size (ncand, nx+1) containing scaled weights, nd < ncand 
    #   ncand - number of candidates to choose <nd> best design from, i.e., cand.shape[0]
    #   xcols - list of integers corresponding to column indices for inputs 
    #    wcol - integer corresponding to the index of the weight column 
    #      md - scalar representing min(dmat)
    #   mdpts - numpy array of shape (K, 2) representing indices where 'md' occurs
    #   mties - scalar representing number of 'mdpts'
    #    dmat - numpy array of shape (M, M) where M = nx+nh
    # Output:
    #   rcand - numpy array of size (nd, nx+1) containing scaled weights
    #      md - scalar representing min(dmat)
    #   mdpts - numpy array of shape (K, 2) representing indices where 'md' occurs
    #   mties - scalar representing number of 'mdpts'
    #    dmat - numpy array of shape (M, M) where M = nx+nh
    #  update - boolean representing whether an update should occur

    def update_dmat(row, rcand, xcols, wcol, dmat_, k, val=9999):
        rcand_norm = row[xcols] - rcand[:, xcols] 
        m = np.sum(rcand_norm**2, axis=1)     
        row = m*row[wcol]*rcand[:, wcol] 
        dmat = np.copy(dmat_)
        dmat[k, :] = row
        dmat[:, k] = row.T
        np.fill_diagonal(dmat, val)
        return dmat

    def step(pt, rcand_, cand, xcols, wcol, mdpts, dmat_, mt0=None):
        i, j = pt
        rcand = rcand_.copy() 
        dmat = np.copy(dmat_)
        row = cand[j]
        k = mdpts[i]                  # k = {0, ..., nd}
        rcand[k, xcols] = row[xcols]  
        dmat = update_dmat(row, rcand, xcols, wcol, dmat_, k)
        md, mdpts, mties = compute_min_params(dmat)
        if mt0 is not None:
            mties = mt0[i, j]
        return rcand, dmat, md, mdpts, mties

    # initialize d0 and mt0
    d0 = np.empty((int(2*mties), ncand))
    mt0 = np.empty((int(2*mties), ncand))

    for pt in np.ndindex(len(mdpts), ncand):
        i, j = pt
        _, _, d0[i, j], _, mt0[i, j] = step(pt, rcand, cand, xcols, wcol, mdpts, dmat)

    d0_max = np.max(d0)
    pts = np.argwhere(d0 == d0_max)
    update = True
    if d0_max > md:
        _md = d0_max
        k = np.random.randint(pts.shape[0])
        pt = pts[k]
        rcand, dmat, md, mdpts, mties = step(pt, rcand, cand, xcols, wcol, mdpts, dmat, mt0)
    elif d0_max == md:
        nselect = np.argwhere(mt0[pts[:, 0], pts[:, 1]] < mties).flatten()
        if nselect.size > 0:
            pt = pts[np.random.choice(nselect)]
            rcand, dmat, md, mdpts, mties = step(pt, rcand, cand, xcols, wcol, mdpts, dmat, mt0)
    else:
        update = False
            
    return rcand, md, mdpts, mties, dmat, update


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
    mat[:, xcols] = (xs - xmin) / (xmax - xmin) * 2 - 1

    return mat, xmin, xmax


def scale_y(scale_method, mwr, mat_, wcol):
    # Inputs:
    #  scale_method - string that denotes the scaling method
    #           mwr - scalar used in scaling
    #          mat_ - pandas dataframe of size (nd, nx+1) containing original weights
    #          wcol - integer corresponding to the index of the weight column
    # Output:
    #           mat - numpy array of size (nd, nx+1) containing the scaled weights

    mat = mat_.copy()

    def direct_mwr(mwr, mat, wcol):
        wts = mat[:, wcol]
        wmin = np.min(wts)
        wmax = np.max(wts)
        mat[:, wcol] = 1 + (mwr-1)*(wts-wmin)/(wmax-wmin)
        return mat

    def ranked_mwr(mwr, mat, wcol):
        mat[:, wcol] = rankdata(mat[:, wcol], method='dense')
        return direct_mwr(mwr, mat, wcol)

    # equivalent to if-else statements, but easier to maintain
    methods = {'direct_mwr': direct_mwr,
               'ranked_mwr': ranked_mwr}

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
    mat[:, xcols] = (xs + 1) / 2 * (xmax - xmin) + xmin
    return mat


def criterion(cand,    # candidates 
              args,    # maximum number of iterations & mwr values
              nr,      # number of restarts (each restart uses a random set of <nd> points)
              nd,      # design size <= len(candidates)
              mode='maximin', hist=None):

    ncand = len(cand)
    assert nd <= ncand, 'Number of designs exceeds number of available candidates.'  

    mode = mode.lower()
    assert mode == 'maximin', 'MODE {} not recognized for NUSF. Only MAXIMIN is currently supported.'.format(mode)

    T = args['max_iterations']
    mwr_vals = args['mwr_values']
    scale_method = args['scale_method']

    # indices of type ...
    idx = args['xcols']  # Input
    idw = args['wcol']   # Weight

    # np indices
    idx_np = [cand.columns.get_loc(i) for i in idx]
    idw_np = cand.columns.get_loc(idw)

    cand_np = cand.to_numpy()

    # scale inputs
    cand_np, _xmin, _xmax = scale_xs(cand_np, idx_np) 
    
    if hist is not None:
        hist_xs = hist[idx].values
        hist_wt = hist[idw].values
    else:
        hist_xs = None
        hist_wt = None

    def step(mwr, cand_np):

        cand_np_ = cand_np.copy()

        cand_np = scale_y(scale_method, mwr, cand_np, idw_np) 
        best_cand = []
        best_md = 0
        best_mties = 0
        best_index = []
        
        t0 = time.time()

        for i in range(nr):
        
            print('Random start {}'.format(i))
            
            # sample without replacement <nd> indices
            rand_index = np.random.choice(ncand, nd, replace=False)
            # extract the <nd> rows
            rcand = cand_np[rand_index]
            dmat = compute_dmat(rcand, idx_np, idw_np, hist_xs=hist_xs, hist_wt=hist_wt)
            md, mdpts, mties = compute_min_params(dmat)

            update = True
            t = 0

            while update and (t < T):
                update = False

                rcand_, md_, mdpts_, mties_, dmat_, update_ = update_min_dist(rcand, cand_np, ncand,
                                                                              idx_np, idw_np, md, mdpts,
                                                                              mties, dmat)  # bottleneck in old code
                                                     
                t = t+1

                if update_:
                    rcand = rcand_
                    md = md_
                    mdpts = mdpts_
                    mties = mties_
                    dmat = dmat_
                    update = update_

            if (md > best_md) or ((md == best_md) and (mties < best_mties)):
                best_index = rand_index
                best_cand = rcand
                best_md = md
                best_mdpts = mdpts
                best_mties = mties
                best_dmat = dmat

            elapsed_time = time.time() - t0
            print('Best minimum distance for this random start: {}'.format(best_md))

        # no need to inverse-scale; can just use the indices to look up original rows in cand_
        best_cand_unscaled = cand_np_[best_index]

        best_cand = pd.DataFrame(best_cand, index=best_index, columns=list(cand))
        best_cand_unscaled = pd.DataFrame(best_cand_unscaled, index=best_index, columns=list(cand))

        results = {'best_cand_scaled': best_cand, 
                   'best_cand': best_cand_unscaled,
                   'best_index': best_index,
                   'best_val': best_md,
                   'best_mdpts': best_mdpts,
                   'best_mties': best_mties,
                   'best_dmat': best_dmat,
                   'mode': mode,
                   'design_size': nd,
                   'num_restarts': nr,
                   'mwr': mwr,
                   'elapsed_time': elapsed_time}

        return results

    results = {}
    for mwr in mwr_vals:
        print('>>>>>> mwr={} <<<<<<'.format(mwr))
        res = step(mwr, cand_np)
        print('Best NUSF Design in Scaled Coordinates:\n', res['best_cand_scaled'])
        print('Best NUSF Design in Original Coordinates:\n', res['best_cand'])
        print('Best value in Normalized Scale:', res['best_val'])
        print('Elapsed time:', res['elapsed_time'])
        results[mwr] = res

    return results
