import numpy as np

def compute_dist(mat,      # numpy array of shape (N, nx) and type 'float'
                 scl=None, # [usf] numpy array of shape (nx,) and type 'float'
                 wt=None,  # [nusf] numpy array of shape (N,) and type 'float'
                 hist=[]):
    if hist:
        mat = np.concatenate((mat, hist), axis=0)

    N, ncols = mat.shape
    dmat = np.full((N, N), np.nan)

    val = np.inf
    
    if scl is not None:
        assert scl.shape[0] == ncols, 'SCL should be of dim %d.' % ncols
        mat = mat / np.repeat(np.reshape(scl, (1, ncols)), N, axis=0)
        val = 10
        
    for i in range(N):
        x = np.repeat(np.reshape(mat[i,:], (1, ncols)), N, axis=0) - mat
        dmat[:,i] = np.sum(np.square(x), axis=1)

    if wt is not None:
        dmat = np.multiply(dmat, np.outer(wt, wt))
        val = 9999
        
    np.fill_diagonal(dmat, val)
            
    return dmat
