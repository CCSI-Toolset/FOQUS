import pandas as pd
import numpy as np
from scipy.stats import rankdata
from .distance import compute_dist
import time

# -----------------------------------
def compute_dmat(mat,  # numpy array of shape (N, nx+1) and type 'float'
                 hist=[]):
    # Assumes last column contains weights
    xs = mat[:,:-1]
    wt = mat[:,-1]
    dmat = compute_dist(xs, wt=wt, hist=hist)  # symmetric matrix
    return dmat

def compute_min_params(dmat):
    md = np.min(dmat)
    mdpts = np.argwhere(np.triu(dmat) == md)   # check upper triangular matrix
    mties = mdpts.shape[0]                     # number of points returned
    return md, mdpts, mties

def update_min_dist(des,  # numpy array of shape (nd, nx+1) and type 'float'
                    md,
                    mdpts,
                    mties,
                    dmat,
                    mat # numpy array of shape (N, nx+1) and type 'float'
                    ):

    ncand = np.shape(mat)[0]

    nd, nx = des.shape 
    nx = nx-1
    assert (nd <= ncand)

    def replace_design(arr, mat, dmat, k, val=9999):
        x = np.repeat(np.reshape(arr[:-1], (1, nx)), nd, axis=0) - mat[:,:-1]
        row = np.multiply(np.sum(np.square(x), axis=1)*arr[-1], mat[:,-1])
        dmat[k,:] = row
        dmat[:,k] = row.T
        np.fill_diagonal(dmat, val)
        return dmat

    def step(pt, cand, mdpts, des, dmat, mt0=None):
        i, j = pt
        row = cand[j]
        s, t = mdpts[i]
        des[s, :] = row
        dmat = replace_design(row, des, dmat, s)
        md, mdpts, mties = compute_min_params(dmat)
        if mt0 is not None:
            mties = mt0[i,j]
        return des, dmat, md, mdpts, mties

    # initialize d0 and mt0
    d0 = np.zeros((mties, ncand), dtype=int)
    mt0 = np.zeros((mties, ncand), dtype=int)
    for i in range(len(mdpts)):
        for j in range(ncand):
            pt = (i,j)
            _, _, d0[i,j], _, mt0[i,j] = step(pt, mat, mdpts, des, dmat)

    d0_max = np.max(d0)
    pts = np.argwhere(d0 == d0_max)
    update = True
    if d0_max > md:
        md = d0_max
        pt = pts[np.random.randint(pts.shape[0])]
        des, dmat, _, mdpts, mties = step(pt, mat, mdpts, des, dmat, mt0=mt0)
    elif d0_max == md:
        nselect = []
        for k, pt in enumerate(pts):
            i, j = pt
            if (mt0[i,j] < mties):
                nselect.append(k)         
        if nselect:
            pt = pts[np.random.choice(nselect)]
            des, dmat, _, mdpts, mties = step(pt, mat, mdpts, des, dmat, mt0=mt0)
    else:
        update = False
            
    return des, md, mdpts, mties, dmat, update

# -----------------------------------
def scale_xs(df, xcols):
    # Takes pandas df as input

    xs = df[xcols]

    # scale the inputs
    # save xmin, xmax for inverse scaling later
    xmin = np.min(xs, axis=0)
    xmax = np.max(xs, axis=0)
    df[xcols] = (xs-xmin)/(xmax-xmin)*2-1

    return mat, xmin, xmax


def scale_y(scale_method, mwr, df, wcol):
    # Takes pandas df as input
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


def inv_scale_xs(df, xmin, xmax, xcols):
    # Takes pandas df as input
  
    # inverse-scale the inputs
    df[xcols] = (df[xcols]+1)/2*(xmax-xmin)+xmin
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
    
    if hist:
        hist = hist[include].values

    def step(mwr, cand):
        t0 = time.time()
        cand = scale_y(scale_method, mwr, cand, wcol)
                
        best_cand = []
        best_md = 0
        best_mties = 0
        for i in range(nr):
        
            print('Random start {}'.format(i))
            rand_index = np.random.choice(len(cand), nd, replace=False)
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
                best_cand = rand_cand
                best_md = md
                best_mdpts = mdpts
                best_mties = mties
                best_dmat = dmat

            elapsed_time = time.time() - t0
            print('Best minimum distance for this random start: {}'.format(best_md))

        results = {'best_cand_scaled': best_cand,
                   'best_cand': inv_scale_xs(best_cand, xmin, xmax, xcols),
                   'best_val': best_md,
                   'best_mdpts': best_mdpts,
                   'best_mties': best_mties,
                   'best_dmat': best_dmat,
                   'mode': mode,
                   'design_size': nd,
                   'num_restarts': nr,
                   'elapsed_time': elapsed_time}
        
        return results

    results = {}
    for mwr in mwr_vals:
        res = step(mwr, cand)
        print('Best value in Normalized Scale:', res['best_val'])
        print('Best NUSF Design in Scaled Coordinates:', res['best_cand_scaled'])
        print('Best NUSF Design in Original Coordinates:', res['best_cand'])
        results[mwr] = res
    return results
