from .df_utils import load, write
import configparser, time, os
import numpy as np
import pandas as pd

def save(fnames, results, elapsed_time):
    write(fnames['cand'], results['best_cand'])
    print('Candidates saved to {}'.format(fnames['cand']))
    np.save(fnames['dmat'], results['best_dmat'])
    print(('d={}, n={}: best_val={}, elapsed_time={}s'.format(results['design_size'], results['num_restarts'],
                                                              results['best_val'], elapsed_time)))
    print('Candidate distances saved to {}'.format(fnames['dmat']))

def run(config_file, nd, test=False):

    # check config file
    config_file = config_file.strip()
    assert(os.path.isfile(config_file))
    
    # parse config file
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_file.strip())
    
    mode = config['METHOD']['mode']
    nr = int(config['METHOD']['number_random_starts'])

    hfile = config['INPUT']['history_file']
    cfile = config['INPUT']['candidate_file']
    include = [s.strip() for s in config['INPUT']['include'].split(',')]

    max_vals = [float(s) for s in config['INPUT']['max_vals'].split(',')]
    min_vals = [float(s) for s in config['INPUT']['min_vals'].split(',')]

    types = [s.strip() for s in config['INPUT']['types'].split(',')]
    # 'Input' columns
    idx = [x for x, t in zip(include, types) if t == 'Input']
    # 'Index' column (should only be one)
    id_ = [x for x, t in zip(include, types) if t == 'Index']
    if id_:
        assert len(id_) == 1, 'Multiple INDEX columns detected. There should only be one INDEX column.'
        id_ = id_[0]
    else:
        id_ = None
    outdir = config['OUTPUT']['results_dir']

    nusf = 'SF' in config.sections()
    
    if nusf:
        # 'Weight' column (should only be one)
        idw = [x for x, t in zip(include, types) if t == 'Weight']
        assert len(idw) == 1, 'Multiple WEIGHT columns detected. There should only be one WEIGHT column.'
        idw = idw[0]

        weight_mode = config['WEIGHT']['weight_mode']
        assert weight_mode == 'by_user', 'WEIGHT_MODE {} not recognized for NUSF. Only BY_USER is currently supported.'.format(weight_mode)
            
        scale_method = config['SF']['scale_method']
        assert(scale_method in ['direct_mwr', 'ranked_mwr'])
        mwr_values = [int(s) for s in config['SF']['mwr_values'].split(',')]

        args = {'icol': id_,
                'xcols': idx,
                'wcol': idw,
                'max_iterations': 100,
                'mwr_values': mwr_values,
                'scale_method': scale_method}
        from .nusf import criterion
        
    else:
        scl = np.array([ub-lb for ub,lb in zip(max_vals, min_vals)])
        args = {'icol': id_,
                'xcols': idx,
                'wcol': None,
                'scale_factors': pd.Series(scl, index=include)}
        from .usf import criterion
        
    # create outdir as needed
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # load candidates
    if cfile:
        cand = load(cfile, index=id_)
        if len(include) == 1 and include[0] == 'all':
            include = list(cand)

    # load history
    hist = None
    if hist is None:
        pass
    else:
        assert id_ in hfile, 'History file should have an INDEX column named "{}"'.format(id_)
        hist = load(hfile, index=id_)
        
    # do a quick test to get an idea of runtime
    if test:
        t0 = time.time()
        results = criterion(cand, args, nr, nd, mode=mode, hist=hist)
        elapsed_time = time.time() - t0
        return elapsed_time

    # otherwise, run sdoe for real
    t0 = time.time()
    results = criterion(cand, args, nr, nd, mode=mode, hist=hist)
    elapsed_time = time.time() - t0

    # save the output
    if nusf:
        fnames = {}
        for mwr in mwr_values:
            suffix = 'd{}_n{}_m{}_{}'.format(nd, nr, mwr, '+'.join(idx+[idw]))
            fnames[mwr] = {'cand': os.path.join(outdir, 'nusf_{}.csv'.format(suffix)),
                           'dmat': os.path.join(outdir, 'nusf_dmat_{}.npy'.format(suffix))}
            save(fnames[mwr], results[mwr], elapsed_time)
    else:
        suffix = 'd{}_n{}_{}'.format(nd, nr, '+'.join([id_]+idx))
        fnames = {'cand': os.path.join(outdir, 'usf_{}.csv'.format(suffix)),
                  'dmat': os.path.join(outdir, 'usf_dmat_{}.npy'.format(suffix))}
        save(fnames, results, elapsed_time)
        
    return fnames, results, elapsed_time
