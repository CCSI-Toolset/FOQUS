import numpy as np
from scipy.stats import rankdata
from .distance import compute_dist
import time

# -----------------------------------
def compute_dmat(df, xcols, wcol, hist=None):
    # Inputs:
    #     df - pandas dataframe of size (nd, nx+1) containing scaled weights
    #  xcols - list of strings corresponding to column names for inputs
    #   wcol - string corresponding to the name of the weight column
    #   hist - numpy array of shape (nh, nx+1) 
    # Output:
    #   dmat - numpy array of shape (nd+nh, nd+nh)
    
    # Assumes last column contains weights
    xs = df[xcols].values
    wt = df[wcol].values
    dmat = compute_dist(xs, wt=wt, hist=hist)  # symmetric matrix
    return dmat  # symmetric distance matrix

def compute_min_params(dmat):
    # Input:
    #   dmat - numpy array of shape (M, M) where M = nx+nh
    # Output:
    #      md - scalar representing min(dmat)
    #   mdpts - numpy array of shape (K, 2) representing indices where 'md' occurs
    #   mties - scalar representing K, the number of 'mdpts'

    md = np.min(dmat)
    mdpts = np.argwhere(np.triu(dmat) == md)  # check upper triangular matrix
    mties = mdpts.shape[0]                    # number of points returned
    mdpts = np.unique(mdpts.flatten())
    return md, mdpts, mties

def update_min_dist(rcand, cand, ncand, xcols, wcol, md, mdpts, mties, dmat):
    # Inputs:
    #     rcand - pandas dataframe of size (nd, nx+1) containing scaled weights
    #      cand - pandas dataframe of size (ncand, nx+1) containing scaled weights, nd < ncand
    #     ncand - number of candidates to choose <nd> best design from, i.e., cand.shape[0]
    #   xcols - list of strings corresponding to column names for inputs
    #   wcol - string corresponding to the name of the weight column
    #      md - scalar representing min(dmat)
    #   mdpts - numpy array of shape (K, 2) representing indices where 'md' occurs
    #   mties - scalar representing number of 'mdpts'
    #    dmat - numpy array of shape (M, M) where M = nx+nh
    # Output:
    #     rcand - pandas dataframe of size (nd, nx+1) containing scaled weights
    #      md - scalar representing min(dmat)
    #   mdpts - numpy array of shape (K, 2) representing indices where 'md' occurs
    #   mties - scalar representing number of 'mdpts'
    #    dmat - numpy array of shape (M, M) where M = nx+nh
    #  update - boolean representing whether an update should occur

    def update_dmat(row, rcand, xcols, wcol, dmat_, k, val=9999):
        rcand_norm = rcand.apply(lambda r: row[xcols] - r[xcols], axis=1)
        m = rcand_norm.apply(lambda r: sum(r[xcols]**2), axis=1)
        row = m*row[wcol]*rcand[wcol]
        dmat = np.copy(dmat_)
        dmat[k,:] = row
        dmat[:,k] = row.T
        np.fill_diagonal(dmat, val)
        return dmat

    def step(pt, rcand_, cand, xcols, wcol, mdpts, dmat_, mt0=None):
        i, j = pt
        rcand = rcand_.copy()
        dmat = np.copy(dmat_)
        row = cand.iloc[j]            # series with all columns
        k = mdpts[i]                  # k = {0, ..., nd}
        index = list(rcand.index)[k]  # k-th row of rcand, which has its own df index
        rcand.loc[index, xcols] = row[xcols]  # set values at <xcols> columns
        dmat = update_dmat(row, rcand, xcols, wcol, dmat_, k)
        md, mdpts, mties = compute_min_params(dmat)
        if mt0 is not None:
            mties = mt0[i,j]
        return rcand, dmat, md, mdpts, mties

    # initialize d0 and mt0
    d0 = np.empty((int(2*mties), ncand))
    mt0 = np.empty((int(2*mties), ncand))
    tuples = [(i,j) for i in range(len(mdpts)) for j in range(ncand)]
    for pt in tuples:
        i,j = pt
        _, _, d0[i,j], _, mt0[i,j] = step(pt, rcand, cand, xcols, wcol, mdpts, dmat)

    d0_max = np.max(d0)
    pts = np.argwhere(d0 == d0_max)
    update = True
    if d0_max > md:
        md = d0_max
        k = np.random.randint(pts.shape[0])
        pt = pts[k]
        rcand, dmat, md, mdpts, mties = step(pt, rcand, cand, xcols, wcol, mdpts, dmat, mt0=mt0)
    elif d0_max == md:
        nselect = []
        for k, pt in enumerate(pts):
            i, j = pt
            if (mt0[i,j] < mties):
                nselect.append(k)
        if nselect:
            pt = pts[np.random.choice(nselect)]
            rcand, dmat, md, mdpts, mties = step(pt, rcand, cand, xcols, wcol, mdpts, dmat, mt0=mt0)
    else:
        update = False
            
    return rcand, md, mdpts, mties, dmat, update

# -----------------------------------
def scale_xs(df_, xcols):
    # Inputs:
    #     df_ - pandas dataframe of size (nd, nx+1) containing original inputs
    #   xcols - list of strings corresponding to column names for inputs
    # Output:
    #      df - pandas dataframe of size (nd, nx+1) containing the scaled inputs
    #    xmin - numpy array of shape (1, nx) 
    #    xmax - numpy array of shape (1, nx) 

    df = df_.copy()
    xs = df[xcols]

    # scale the inputs
    # save xmin, xmax for inverse scaling later
    xmin = np.min(xs, axis=0)
    xmax = np.max(xs, axis=0)
    df[xcols] = (xs-xmin)/(xmax-xmin)*2-1

    return df, xmin, xmax


def scale_y(scale_method, mwr, df_, wcol):
    # Inputs:
    #  scale_method - string that denotes the scaling method
    #           mwr - scalar used in scaling
    #           df_ - pandas dataframe of size (nd, nx+1) containing original weights
    #   wcol - string corresponding to the name of the weight column
    # Output:
    #      df - pandas dataframe of size (nd, nx+1) containing the scaled weights

    df = df_.copy()
    
    def direct_mwr(mwr, df, wcol):
        wts = df[wcol]
        wmin = np.min(wts)
        wmax = np.max(wts)
        df[wcol] = 1 + (mwr-1)*(wts-wmin)/(wmax-wmin)
        return df

    def ranked_mwr(mwr, df, wcol):
        df[wcol] = rankdata(df[wcol], method='dense')
        return direct_mwr(mwr, df, wcol)

    # equivalent to if-else statements, but easier to maintain
    methods = {'direct_mwr': direct_mwr,
               'ranked_mwr': ranked_mwr}

    return methods[scale_method](mwr, df, wcol)

# Not needed because we are using the index to look up the original rows
def inv_scale_xs(df_, xmin, xmax, xcols):
    # Inputs:
    #      df - pandas dataframe of size (nd, nx+1) containing scaled inputs
    #    xmin - numpy array of shape (1, nx) from before scaling
    #    xmax - numpy array of shape (1, nx) from before scaling
    #   xcols - list of strings corresponding to column names for inputs
    # Output:
    #      df - pandas dataframe of size (nd, nx+1) containing the original inputs

    # inverse-scale the inputs
    df = df_.copy()
    xs = df[xcols]
    df[xcols] = (xs+1)/2*(xmax-xmin)+xmin
    return df

# -----------------------------------
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
    
    # scale inputs
    cand, _xmin, _xmax = scale_xs(cand, idx)
    
    if hist is not None:
        hist = hist[idx].values

    def step(mwr, cand):
        
        cand_ = cand.copy()
        id_ = cand_.index
        
        cand = scale_y(scale_method, mwr, cand, idw)
        best_cand = []
        best_md = 0
        best_mties = 0
        best_index = []
        
        t0 = time.time()

        for i in range(nr):
        
            print('Random start {}'.format(i))
            
            # sample without replacement <nd> indices
            rand_index = np.random.choice(id_, nd, replace=False)
            # extract the <nd> rows
            rcand = cand.loc[rand_index]
            dmat = compute_dmat(rcand, idx, idw, hist=hist)
            md, mdpts, mties = compute_min_params(dmat)

            update = True
            t = 0

            while update and (t<T):
                update = False
                rcand_, md_, mdpts_, mties_, dmat_, update_ = update_min_dist(rcand, cand, ncand, idx, idw, md, mdpts, mties, dmat)
                                                                            
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

        # no need to inverse-scale; ccan just use the indices to look up original rows in cand_
        index = best_cand.index
        assert all(list(index) == best_index), 'Index mismatch in best candidates.'
        best_cand_unscaled = cand_.loc[index]
        
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
        res = step(mwr, cand)
        print('Best NUSF Design in Scaled Coordinates:\n', res['best_cand_scaled'])
        print('Best NUSF Design in Original Coordinates:\n', res['best_cand'])
        print('Best value in Normalized Scale:', res['best_val'])
        print('Elapsed time:', res['elapsed_time'])
        results[mwr] = res

    return results
