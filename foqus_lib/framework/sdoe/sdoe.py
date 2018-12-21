from .distance import criterion
from .candidate import load_candidates
import configparser, time, os
import numpy as np

def test(config_file):
    # parse config file
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_file)
    mode = config['METHOD']['mode']
    min_size = int(config['METHOD']['min_design_size'])
    max_size = int(config['METHOD']['max_design_size'])
    hfile = config['INPUT']['history_file']

    cfile = config['INPUT']['candidate_file']
    max_vals = [float(s) for s in config['INPUT']['max_vals'].split(',')]
    min_vals = [float(s) for s in config['INPUT']['min_vals'].split(',')]
    outdir = config['OUTPUT']['results_dir']

    # load candidates
    if cfile:
        cand, header = load_candidates(cfile)

    # load history
    histmat = None
    if hfile:
        histmat, header_ = load_candidates(hfile)
        assert header == header_, 'Headers mismatch detected.'

    # scale factors
    scl = np.array([ub - lb for ub, lb in zip(max_vals, min_vals)])

    d = max_size
    n = 200
    t0 = time.time()
    best_val, cand_rand, rand_index = criterion(cand, scl, d, n, mode=mode, histmat=histmat)
    elapsed_time = time.time() - t0
    # fname = 'sdoe_candidates_%d_%d' % (d, n)
    # fname = os.path.join(outdir, fname)
    # header_str = ', '.join(header)
    # np.savetxt(fname, cand_rand, delimiter=', ', header=header_str)
    #print(('d=%d, n=%d: best_val=%f, elapsed_time=%fs' % (d, n, best_val, elapsed_time)))
    return elapsed_time


def run(config_file, d, test=False):

    # parse config file
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_file)
    mode = config['METHOD']['mode']
    min_size = int(config['METHOD']['min_design_size'])
    max_size = int(config['METHOD']['max_design_size'])
    hfile = config['INPUT']['history_file']

    cfile = config['INPUT']['candidate_file']
    max_vals = [float(s) for s in config['INPUT']['max_vals'].split(',')]
    min_vals = [float(s) for s in config['INPUT']['min_vals'].split(',')]
    outdir = config['OUTPUT']['results_dir']
    number_random_starts = int(config['TEST']['number_random_starts'])

    # load candidates
    if cfile:
        cand, header = load_candidates(cfile)

    # load history
    histmat = None
    if hfile:
        histmat, header_ = load_candidates(hfile)
        assert header == header_, 'Headers mismatch detected.'
    
    # scale factors
    scl = np.array([ub-lb for ub,lb in zip(max_vals, min_vals)])

    if test:
        t0 = time.time()
        best_val, cand_rand, rand_index = criterion(cand, scl, d, n, mode=mode, histmat=histmat)
        elapsed_time = time.time() - t0
    n = number_random_starts
    t0 = time.time()
    best_val, cand_rand, rand_index = criterion(cand, scl, d, n, mode=mode, histmat=histmat)
    elapsed_time = time.time() - t0
    fname = 'sdoe_candidates_%d_%d' % (d, n)
    fname = os.path.join(outdir, fname)
    header_str = ', '.join(header)
    np.savetxt(fname, cand_rand, delimiter=', ', header=header_str)
    print(('d=%d, n=%d: best_val=%f, elapsed_time=%fs' % (d, n, best_val, elapsed_time)))
    return (mode, d, n, elapsed_time)

# TO DO: plot, interpolate simulation time

#run('config.ini', debug=True)
