from operator import lt, gt
import numpy as np
from .distance import compute_dist

def compute_min_dist(mat, scl, hist=[]):
    dmat = compute_dist(mat, scl=scl, hist=hist)
    min_dist = np.min(dmat, axis=0)
    return dmat, min_dist


def criterion(cand,    # candidates
              include, # columns to include in distance computation
              types,   # column types: {Index, Input}
              args,    # scaling factors for included columns
              nr,      # number of restarts (each restart uses a random set of <nd> points)
              nd,      # design size <= len(candidates)
              mode='maximin', hist=[]):

    mode = mode.lower()
    assert mode in ['maximin', 'minimax'], 'MODE {} not recognized.'.format(mode)
    if mode == 'maximin':
        best_val = -1
        fcn = np.mean
        cond = gt
    elif mode == 'minimax':
        best_val = 99999
        fcn = np.max
        cond = lt

    # indices of type 'Input'
    idx = [x for x, t in zip(include, types) if t == 'Input']
    
    # scaling factors
    scl = args['scale_factors']
    scl = scl[idx].values

    # history, if provided
    if hist:
        hist = hist[idx].values

    best_cand = []
    best_rand_sample = []
 
    for i in range(nr):

        # sample without replacement <nd> indices
        rand_index = np.random.choice(len(cand), nd, replace=False)
        # extract the <nd> rows
        rand_cand = cand.iloc[rand_index]
        # extract the relevant columns (of type 'Input' only) for dist computations
        dmat, min_dist = compute_min_dist(rand_cand[idx].values, scl, hist=hist)
        dist = fcn(min_dist)

        if cond(dist, best_val):
            best_cand = rand_cand    
            best_index = rand_index  # for debugging
            best_val = dist          # for debugging
            best_dmat = dmat         # used for ranking candidates

    results = {'best_cand': best_cand,
               'best_index': best_index,
               'best_val': best_val,
               'best_dmat': best_dmat,
               'dmat_cols': idx,      
               'mode': mode,
               'design_size': nd,
               'num_restarts': nr}
         
    return results
