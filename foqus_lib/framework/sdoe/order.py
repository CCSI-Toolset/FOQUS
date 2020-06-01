'''
Candidate ordering by TSP Optimization

Code adopted from:
https://mlrose.readthedocs.io/en/stable/source/tutorial2.html

'''
import logging
import os
import numpy as np
import mlrose_hiive as mlrose
from .df_utils import load, write
_log = logging.getLogger("foqus." + __name__)

def mat2tuples(mat):
    ''' assumes mat as dense matrix, extracts lower-triangular elements '''
    lte = []
    nrows, _ = mat.shape
    for i in range(nrows):
        for j in range(i):
            val = mat[i, j]
            if val:
                lte.append((i, j, val))
    return lte

def rank(fnames, save=True, ga_max_attempts=100):
    ''' return fnames ranked '''
    dist_mat = np.load(fnames['dmat'])
    dist_list = mat2tuples(dist_mat)

    # define fitness function object
    fitness_dists = mlrose.TravellingSales(distances=dist_list)

    # define optimization problem object
    n_len = dist_mat.shape[0]
    problem_fit = mlrose.TSPOpt(length=n_len, fitness_fn=fitness_dists,
                                maximize=False)

    # solve problem using the genetic algorithm
    best_state, best_fitness, fitness_curve = mlrose.genetic_alg(problem_fit,
                                                                 mutation_prob=0.2,
                                                                 max_attempts=ga_max_attempts,
                                                                 random_state=2)

    # retrieve ranked list
    cand = load(fnames['cand'])
    ranked_cand = cand.loc[best_state]

    # save the output
    fname_ranked = None
    if save:
        fname, ext = os.path.splitext(fnames['cand'])
        fname_ranked = fname + '_ranked' + ext
        write(fname_ranked, ranked_cand)
        _log.info('Ordered candidates saved to {}'.format(fname_ranked))

    return fname_ranked
