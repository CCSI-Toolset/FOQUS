from operator import lt, gt
import numpy as np


def compute_min_dist(dmat,  # numpy array of shape (N, ncols) and type 'float'
                     scl,  # numpy array of shape (ncols,) and type 'float'
                     hist=[]):
    if hist:
        dmat = np.concatenate((dmat, hist), axis=0)

    N, ncols = dmat.shape
    dist_mat = np.full((N, N), np.nan)
    assert scl.shape[0] == ncols, 'SCL should be of dim %d.' % ncols

    dmat_norm = dmat / np.repeat(np.reshape(scl, (ncols, 1)), N, axis=1).T
    for i in range(N):
        x = np.repeat(np.reshape(dmat_norm[i, :], (ncols, 1)), N, axis=1).T - dmat_norm
        dist_mat[:, i] = np.sum(np.square(x), axis=1)
        dist_mat[i, i] = 10

    min_dist = np.min(dist_mat, axis=0)
    return min_dist


def criterion(candid,  # candidates
              include,  # columns to include in distance computation
              scl,  # scaling factors for included columns
              nr,  # number of restarts (e.g., random combinations of <nd> points)
              nd,  # design size <= len(candidates)
              mode='maximin', hist=[]):
    best_cand = []
    best_rand_sample = []
    mode = mode.lower()
    assert mode in ['maximin', 'minimax'], 'MODE %s not recognized.' % mode
    if mode == 'maximin':
        best_val = -1
        dist_fcn = np.mean
        cond = gt
    elif mode == 'minimax':
        best_val = 99999
        dist_fcn = np.max
        cond = lt

    if hist:
        hist = hist[include].values

    assert (nd <= len(candid))  # this should have been checked in GUI

    for i in range(nr):

        rand_index = np.random.choice(len(candid), nd, replace=False)
        cand_rand = candid.iloc[rand_index]
        dist = dist_fcn(compute_min_dist(cand_rand[include].values, scl, hist=hist))

        if cond(dist, best_val):
            best_val = dist
            best_cand = cand_rand
            best_rand_sample = rand_index

    return best_val, best_cand, best_rand_sample