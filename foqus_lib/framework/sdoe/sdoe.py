from .df_utils import load, write
import configparser, time, os
import numpy as np

def save(fnames, results, elapsed_time):
    write(fnames['cand'], results['best_cand'])
    print('Candidates saved to {}'.format(fnames['cand']))
    np.save(fnames['dmat'], results['best_dmat'])
    print(('d={}, n={}: best_val={}, elapsed_time={}s'.format(results['design_size'], results['num_restarts'],
                                                              results['best_val'], elapsed_time)))
    print('Candidate distances saved to {}'.format(fnames['dmat']))

def run(config_file, nd, test=False):

    # parse config file
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_file)
    mode = config['METHOD']['mode']
    nr = int(config['METHOD']['number_random_starts'])

    hfile = config['INPUT']['history_file']
    cfile = config['INPUT']['candidate_file']
    include = [s.strip() for s in config['INPUT']['include'].split(',')]
    max_vals = [float(s) for s in config['INPUT']['max_vals'].split(',')]
    min_vals = [float(s) for s in config['INPUT']['min_vals'].split(',')]
    types = [s.strip() for s in config['INPUT']['type'].split(',')]
    outdir = config['OUTPUT']['results_dir']

    nusf = 'SF' in config.sections()
    if nusf:
        weight_mode = config['WEIGHT']['weight_mode']
        assert weight_mode == 'by_user', 'WEIGHT_MODE {} not recognized for NUSF. Only BY_USER is currently supported.'.format(weight_mode)
            
        scale_method = config['SF']['scale_method']
        assert(scale_method in ['direct_mwr', 'ranked_mwr'])
        mwr_values = [int(s) for s in config['SF']['mwr_values'].split(',')]

        args = {'max_iterations': 100,
                'mwr_values': mwr_values,
                'scale_method': scale_method}
        from .nusf import criterion
        
    else:
        scl = np.array([ub-lb for ub,lb in zip(max_vals, min_vals)])
        args = {'scale_factors': scl}
        from .usf import criterion
        
    # create outdir as needed
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # load candidates
    if cfile:
        cand = load(cfile)
        if len(include) == 1 and include[0] == 'all':
            include = list(cand)
        if nusf and weight_mode == 'by_user':

            # move the weight column to the last column
            # if nusf, one of the columns is expected to be the weight vector
            i = types.index('Weight')  
            wcol = include[i]   # weight column name
            wts = cand[wcol]    
            cand = cand.drop(columns=[wcol])
            xcols = list(cand)  # input column names
            cand[wcol] = wts
            
            from .nusf import scale_xs
            cand, xmin, xmax = scale_xs(cand, xcols)
            args['xmin'] = xmin
            args['xmax'] = xmax
            args['wcol'] = wcol
            args['xcols'] = xcols
            
    # load history
    hist = None
    if hist is None:
        pass
    else:
        hist = load(hfile)
        
    # do a quick test to get an idea of runtime
    if test:
        t0 = time.time()
        results = criterion(cand, include, args, nr, nd, mode=mode, hist=hist)
        elapsed_time = time.time() - t0
        return elapsed_time

    # otherwise, run sdoe for real
    t0 = time.time()
    results = criterion(cand, include, args, nr, nd, mode=mode, hist=hist)
    elapsed_time = time.time() - t0

    # save the output
    if nusf:
        fnames = {}
        for mwr in mwr_values:
            suffix = 'd{}_n{}_m{}_{}'.format(nd, nr, mwr, '+'.join(include))
            fnames[mwr] = {'cand': os.path.join(outdir, 'nusf_{}.csv'.format(suffix)),
                           'dmat': os.path.join(outdir, 'nusf_dmat_{}.npy'.format(suffix))}
            save(fnames[mwr], results[mwr], elapsed_time)
    else:
        suffix = 'd{}_n{}_{}'.format(nd, nr, '+'.join(include))
        fnames = {'cand': os.path.join(outdir, 'usf_{}.csv'.format(suffix)),
                  'dmat': os.path.join(outdir, 'usf_dmat_{}.npy'.format(suffix))}
        save(fnames, results, elapsed_time)
        
    return fnames, results, elapsed_time
