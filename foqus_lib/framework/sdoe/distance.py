#################################################################################
# FOQUS Copyright (c) 2012 - 2023, by the software owners: Oak Ridge Institute
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
#################################################################################
import numpy as np


def compute_dist(
    mat,  # numpy array of shape (N, nx) and type 'float'
    scl=None,  # [usf] numpy array of shape (nx,) and type 'float'
    wt=None,  # [nusf] numpy array of shape (N,) and type 'float'
    hist_xs=None,  # numpy array of shape (M, nx) and type 'float'
    hist_wt=None,  # [nusf] numpy array of shape (M,) and type 'float'
    val=np.inf,
    return_sqrt=False,
):

    if hist_xs is not None:
        mat = np.concatenate((mat, hist_xs), axis=0)
    if mat.ndim != 2:
        raise ValueError("ndims must be 2")
    if mat.shape[0] < 2:
        raise ValueError("At least 2 points needed")
    if not np.all(np.isfinite(mat)):
        raise ValueError("All entries in the array must be finite")
    N, ncols = mat.shape
    dmat = np.full((N, N), np.nan)

    if scl is not None:
        assert scl.shape[0] == ncols, "SCL should be of dim %d." % ncols
        mat = mat / np.repeat(np.reshape(scl, (1, ncols)), N, axis=0)
        val = 10

    for i in range(N):
        x = np.repeat(np.reshape(mat[i, :], (1, ncols)), N, axis=0) - mat
        dmat[:, i] = np.sum(np.square(x), axis=1)

    if wt is not None:
        if hist_wt is not None:
            wt = np.concatenate((wt, hist_wt), axis=0)  # might not need axis = 0
        dmat = np.multiply(dmat, np.outer(wt, wt))
        val = 9999

    if return_sqrt:
        dmat = np.sqrt(dmat)

    np.fill_diagonal(dmat, val)

    return dmat


def compute_min_params(dmat):
    # Input:
    #   dmat - numpy array of shape (M, M) where M = N+nh
    # Output:
    #     md - scalar representing min(dmat)
    #  mdpts - numpy array of shape (K, ) representing indices where 'md' occurs
    #  mties - scalar representing the number of index pairs (i, j) where i < j and dmat[i, j] == md

    md = np.min(dmat)
    mdpts = np.argwhere(np.triu(dmat) == md)  # check upper triangular matrix
    mties = mdpts.shape[0]  # number of points returned
    mdpts = np.unique(mdpts.flatten())

    return md, mdpts, mties
