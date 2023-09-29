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
"""
Candidate ordering by TSP Optimization using python-tsp
https://pypi.org/project/python-tsp/
"""
import logging
import os

import numpy as np
from python_tsp.exact import solve_tsp_dynamic_programming

from .df_utils import load, write

_log = logging.getLogger("foqus." + __name__)


def mat2tuples(mat):
    """assumes mat as dense matrix, extracts lower-triangular elements"""
    lte = []
    nrows, _ = mat.shape
    for i in range(nrows):
        for j in range(i):
            val = mat[i, j]
            if val:
                lte.append((i, j, val))
    return lte


def rank(fnames):
    """return fnames ranked"""
    dist_mat = np.load(fnames["dmat"])

    permutation, _distance = solve_tsp_dynamic_programming(dist_mat)

    # retrieve ranked list
    cand = load(fnames["cand"])
    ranked_cand = cand.loc[permutation]

    # save the output
    fname, ext = os.path.splitext(fnames["cand"])
    fname_ranked = fname + "_ranked" + ext
    write(fname_ranked, ranked_cand)
    _log.info("Ordered candidates saved to %s", fname_ranked)

    return fname_ranked
