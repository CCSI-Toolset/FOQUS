from operator import lt, gt, itemgetter
import random
import numpy as np

# Replaces distance_noHist_Maximin, distance_Hist_Maximin
#          distance_noHist_Minimax, distance_Hist_Minimax
def compute_min_dist(dmat, # numpy array of shape (N, ncols) and type 'float'
                     scl,  # numpy array of shape (ncols,) and type 'float'
                     histmat=None):

    if histmat is not None:
        dmat = np.concatenate((dmat, histmat), axis=0)
    
    N, ncols = dmat.shape
    dist_mat = np.full((N, N), np.nan)
    assert scl.shape[0] ==  ncols, 'SCL should be of dim %d.' % ncols

    dmat_norm = dmat / np.repeat(np.reshape(scl, (ncols,1)), N, axis=1).T
    for i in range(N):
        x = np.repeat(np.reshape(dmat_norm[i,:], (ncols,1)), N, axis=1).T - dmat_norm
        dist_mat[:,i] = np.sum(np.square(x), axis=1) 
        dist_mat[i,i] = 10

    min_dist = np.min(dist_mat, axis=0)
    return min_dist
        
# Replaces Maximin_noHist, Maximin_Hist
#          Minimax_noHist, Minimax_Hist
def criterion(candid, # candidates
              scl,    # scaling factors
              numpt,  # number of points
              numdes, # number of designs
              mode='maximin', histmat=None):

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

    for i in range(numdes):
        # CONFIRM: this draws from [1, ..., len(candid)-1]
        rand_index = random.sample(range(1, len(candid)), numpt)
        # ASK: what happens if numpt > len(candid)?
        cand_rand = np.asarray(itemgetter(*rand_index)(candid))
        dist = dist_fcn(compute_min_dist(cand_rand, scl, histmat=histmat))

        if cond(dist, best_val):
            best_val = dist
            best_cand = cand_rand
            best_rand_sample = rand_index
           
    return (best_val, best_cand, best_rand_sample)
