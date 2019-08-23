from operator import lt, gt
import numpy as np


def compute_dist(mat,   # numpy array of shape (N, ncols) and type 'float'
                 scl,   # numpy array of shape (ncols,) and type 'float'
                 hist=[]):
    if hist:
        mat = np.concatenate((mat, hist), axis=0)

    N, ncols = mat.shape
    dist_mat = np.full((N, N), np.nan)
    assert scl.shape[0] == ncols, 'SCL should be of dim %d.' % ncols

    norm_mat = mat / np.repeat(np.reshape(scl, (ncols, 1)), N, axis=1).T
    for i in range(N):
        x = np.repeat(np.reshape(norm_mat[i, :], (ncols, 1)), N, axis=1).T - norm_mat
        dist_mat[:, i] = np.sum(np.square(x), axis=1)
        dist_mat[i, i] = 10  ### TO DO: ask Towfiq

    return dist_mat

def criterion(cand,    # candidates
              include, # columns to include in distance computation
              scl,     # scaling factors for included columns
              nr,      # number of restarts (e.g., random combinations of <nd> points)
              nd,      # design size <= len(candidates)
              mode='maximin', hist=[]):

    best_cand = []
    best_rand_sample = []
    mode = mode.lower()
    assert mode in ['maximin', 'minimax'], 'MODE %s not recognized.' % mode
    if mode == 'maximin':
        best_val = -1
        fcn = np.mean
        cond = gt
    elif mode == 'minimax':
        best_val = 99999
        fcn = np.max
        cond = lt

    if hist:
        hist = hist[include].values

    assert(nd <= len(cand))  # this should have been checked in GUI

    for i in range(nr):

        rand_index = np.random.choice(len(cand), nd, replace=False)
        rand_cand = cand.iloc[rand_index]
        dist_mat = compute_dist(rand_cand[include].values, scl, hist=hist)
        min_dist = np.min(dist_mat, axis=0)
        dist = fcn(min_dist)

        if cond(dist, best_val):
            best_cand = rand_cand    
            best_index = rand_index  # for debugging
            best_val = dist          # for debugging
            best_dmat = dist_mat     # used for ranking candidates

    return best_cand, best_index, best_val, best_dmat
