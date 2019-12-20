import pandas as pd
import numpy as np
from scipy.stats import rankdata
from .distance import compute_dist
import time

# -----------------------------------
def compute_dmat(mat, hist=[]):
    # Inputs:
    #    mat - numpy array of shape (nd, nx+1) 
    #   hist - numpy array of shape (nh, nx+1) 
    # Output:
    #   dmat - numpy array of shape (nd+nh, nd+nh)
    
    # Assumes last column contains weights
    xs = mat[:,:-1]
    wt = mat[:,-1]
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

def update_min_dist(des, md, mdpts, mties, dmat, mat):
    # Inputs:
    #     des - numpy array of shape (nd, nx+1)
    #      md - scalar representing min(dmat)
    #   mdpts - numpy array of shape (K, 2) representing indices where 'md' occurs
    #   mties - scalar representing number of 'mdpts'
    #    dmat - numpy array of shape (M, M) where M = nx+nh
    #     mat - numpy array of shape (N, nx+1) containing the candidates
    # Output:
    #     des - numpy array of shape (nd, nx+1)
    #      md - scalar representing min(dmat)
    #   mdpts - numpy array of shape (K, 2) representing indices where 'md' occurs
    #   mties - scalar representing number of 'mdpts'
    #    dmat - numpy array of shape (M, M) where M = nx+nh
    #  update - boolean representing whether an update should occur

    # <ncand> is the number of candidates from which you will choose
    # <nd> designs as the best ones for your experiment
    nd, nx = des.shape
    nx = nx-1
    ncand = mat.shape[0]
    assert (nd <= ncand)
    
    def update_dmat(row, des, dmat_, k, val=9999):
        x = np.repeat(np.reshape(row[:-1], (nx, 1)), nd, axis=1).T - des[:,:-1]
        row = np.multiply(np.sum(np.square(x), axis=1)*row[-1], des[:,-1])
        dmat = np.copy(dmat_)
        dmat[k,:] = row
        dmat[:,k] = row.T
        np.fill_diagonal(dmat, val)
        return dmat

    def step(pt, cand, mdpts, des_, dmat_, mt0=None):
        i, j = pt
        des = np.copy(des_)
        dmat = np.copy(dmat_)
        row = cand[j]
        k = mdpts[i]
        des[k, :] = row
        dmat = update_dmat(row, des, dmat, k)
        md, mdpts, mties = compute_min_params(dmat)
        if mt0 is not None:
            mties = mt0[i,j]
        return des, dmat, md, mdpts, mties

    # initialize d0 and mt0
    d0 = np.empty((int(2*mties), ncand))
    mt0 = np.empty((int(2*mties), ncand))
    tuples = [(i,j) for i in range(len(mdpts)) for j in range(ncand)]
    for t in tuples:
        i,j = t
        _, _, d0[i,j], _, mt0[i,j] = step(t, mat, mdpts, des, dmat)

    d0_max = np.max(d0)
    pts = np.argwhere(d0 == d0_max)
    update = True
    if d0_max > md:
        md = d0_max
        k = np.random.randint(pts.shape[0])
        pt = pts[k]
        des, dmat, md, mdpts, mties = step(pt, mat, mdpts, des, dmat, mt0=mt0)
    elif d0_max == md:
        nselect = []
        for k, pt in enumerate(pts):
            i, j = pt
            if (mt0[i,j] < mties):
                nselect.append(k)
        if nselect:
            pt = pts[np.random.choice(nselect)]
            des, dmat, md, mdpts, mties = step(pt, mat, mdpts, des, dmat, mt0=mt0)
    else:
        update = False
            
    return des, md, mdpts, mties, dmat, update

# -----------------------------------
def scale_xs(df_, xcols):
    # Inputs:
    #      df - pandas dataframe of size (nd, nx+1) containing original inputs
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
    #            df - pandas dataframe of size (nd, nx+1) containing original weights
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
              include, # columns to include in distance computation
              args,    # maximum number of iterations & mwr values
              nr,      # number of restarts (each restart uses a random set of <nd> points)
              nd,      # design size <= len(candidates)
              mode='maximin', hist=[]):

    assert(nd <= len(cand))  # this should have been checked in GUI

    T = args['max_iterations']
    mwr_vals = args['mwr_values']
    scale_method = args['scale_method']
    xmin = args['xmin']
    xmax = args['xmax']
    wcol = args['wcol']
    xcols = args['xcols']
    mode = mode.lower()
    assert mode == 'maximin', 'MODE {} not recognized for NUSF. Only MAXIMIN is currently supported.'.format(mode)

    N = cand.shape[0]
    cols = list(cand)
    
    if hist:
        hist = hist[include].values

    def step(mwr, cand):

        cand = scale_y(scale_method, mwr, cand, wcol)
        best_cand = []
        best_md = 0
        best_mties = 0
        best_index = []
        
        t0 = time.time()
        for i in range(nr):
        
            print('Random start {}'.format(i))
            rand_index = np.random.choice(N, nd, replace=False)
            rand_cand = cand.iloc[rand_index]
            des = rand_cand[include].values
            mat = cand[include].values
            dmat = compute_dmat(des, hist=hist)
            md, mdpts, mties = compute_min_params(dmat)

            update = True
            t = 0
            while update and (t<T):
                update = False
                des_, md_, mdpts_, mties_, dmat_, update_ = update_min_dist(des, md, mdpts, mties, dmat, mat)
                t = t+1

                if update_:
                    des = des_
                    md = md_
                    mdpts = mdpts_
                    mties = mties_
                    dmat = dmat_
                    update = update_

            if (md > best_md) or ((md == best_md) and (mties < best_mties)):
                best_index = rand_index
                best_cand = des
                best_md = md
                best_mdpts = mdpts
                best_mties = mties
                best_dmat = dmat

            elapsed_time = time.time() - t0
            print('Best minimum distance for this random start: {}'.format(best_md))
        
        df_best_cand_scaled = pd.DataFrame(best_cand, columns=cols)

        # inverse-scale the inputs and replace with original weights
        df_best_cand = inv_scale_xs(df_best_cand_scaled, xmin, xmax, xcols)
        wts = cand[wcol].values               # array of (N,)
        df_best_cand[wcol] = wts[best_index]  # array of (nd,) 
        
        results = {'best_cand_scaled': df_best_cand_scaled,
                   'best_cand': df_best_cand,  # both inputs & wt are in original scales
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
        print('Best value in Normalized Scale:', res['best_val'])
        print('Best NUSF Design in Scaled Coordinates:', res['best_cand_scaled'])
        print('Best NUSF Design in Original Coordinates:', res['best_cand'])
        print('Elapsed time:', res['elapsed_time'])
        results[mwr] = res


    return results
