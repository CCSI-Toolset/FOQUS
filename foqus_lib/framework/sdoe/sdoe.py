from .df_utils import load, write
import configparser, time, os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

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
    min_size = int(config['METHOD']['min_design_size'])
    max_size = int(config['METHOD']['max_design_size'])
    nr = int(config['METHOD']['number_random_starts'])

    hfile = config['INPUT']['history_file']
    cfile = config['INPUT']['candidate_file']
    include = [s.strip() for s in config['INPUT']['include'].split(',')]
    max_vals = [float(s) for s in config['INPUT']['max_vals'].split(',')]
    min_vals = [float(s) for s in config['INPUT']['min_vals'].split(',')]
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
            from .nusf import scale_cand
            sc, xmin, xmax = scale_cand(cand.values)
            cand = pd.DataFrame(sc, columns=cand.columns)
            args['xmin'] = xmin
            args['xmax'] = xmax
            
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
        for mwr in mwr_values:
            suffix = 'd{}_n{}_m{}_{}'.format(nd, nr, mwr, '+'.join(include))
            fnames = {'cand': os.path.join(outdir, 'nusf_{}.csv'.format(suffix)),
                      'dmat': os.path.join(outdir, 'nusf_dmat_{}.npy'.format(suffix))}
            save(fnames, results[mwr], elapsed_time)
    else:
        suffix = 'd{}_n{}_{}'.format(nd, nr, '+'.join(include))
        fnames = {'cand': os.path.join(outdir, 'usf_{}.csv'.format(suffix)),
                  'dmat': os.path.join(outdir, 'usf_dmat_{}.npy'.format(suffix))}
        save(fnames, results, elapsed_time)
        
    return fnames, results, elapsed_time


### TO DO: modify plots for NUSF
def plot(fname, hname=None, show=None, nbins=20, area=10, hbars=False):

    alpha = {'hist': 1.0, 'cand': 0.25}
    area = {'hist': 40, 'cand': 25}

    def plot_hist(ax, xs, xname):
        ns, bins = np.histogram(xs, nbins)
        xmin = bins[0]
        xmax = bins[-1]
        width = bins[1] - bins[0]
        center = (bins[1:] + bins[:-1]) / 2
        if hbars:
            ax.barh(center, ns, align='center', height=width, alpha=alpha['cand'])
            ax.set_ylabel(xname)
            ax.set_xlabel('Frequency')
        else:
            ax.bar(center, ns, align='center', width=width, alpha=alpha['cand'])
            ax.set_xlabel(xname)
            ax.set_ylabel('Frequency')

        ax.grid(True, axis='both')
        return ax

    # load results
    df = load(fname)
    names = list(df)
    # load history
    if hname:
        hf = load(hname)
        # make sure headers match
        assert (names == list(hf))

    # process inputs to be shown
    if show is None:
        show = list(df)
    nshow = len(show)

    # handle case for one input
    if nshow == 1:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        xname = show[0]
        ax = plot_hist(ax, df[xname], xname)

    else:  # multiple inputs

        # subplot indices
        sb_indices = np.reshape(range(nshow ** 2), [nshow, nshow])

        # generate subplots
        fig, axes = plt.subplots(nrows=nshow, ncols=nshow)
        A = axes.flat

        for i in range(nshow):
            for j in range(i):
                # ... delete the unused (lower-triangular) axes
                k = sb_indices[i][j]
                fig.delaxes(A[k])

            k = sb_indices[i][i]
            ax = A[k]
            xname = show[i]
            # ... plot histogram for diagonal subplot
            ax = plot_hist(ax, df[xname], xname)

            for j in range(i + 1, nshow):
                k = sb_indices[i][j]
                ax = A[k]
                yname = show[j]
                # ... plot scatter for off-diagonal subplot
                # ... area/alpha can be customized to visualize weighted points (future feature)
                ax.scatter(df[yname], df[xname], s=area['cand'], alpha=alpha['cand'], color='b')
                if hname:
                    ax.scatter(hf[yname], hf[xname], s=area['hist'], alpha=alpha['hist'], color='red', marker="*")
                ax.set_ylabel(xname)
                ax.set_xlabel(yname)
                ax.grid(True, axis='both')

    title = 'SDOE candidates from {}'.format(fname)
    fig.canvas.set_window_title(title)
    plt.tight_layout()
    if hname:
        fig.legend(labels=['cand', 'cand', 'hist'], loc='lower left', fontsize='xx-large')
    else:
        fig.legend(labels=['cand', 'cand'], loc='lower left', fontsize='xx-large')

    plt.show()
