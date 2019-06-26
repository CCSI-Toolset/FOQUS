from .distance import criterion
from .df_utils import load, write
import configparser, time, os
import numpy as np
import matplotlib.pyplot as plt

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
    type = [s.strip() for s in config['INPUT']['type'].split(',')]
    outdir = config['OUTPUT']['results_dir']

    # create outdir as needed
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # load candidates
    if cfile:
        cand = load(cfile)
        if len(include) == 1 and include[0] == 'all':
            include = list(cand)

    # load history
    hist = None
    if hist is None:
        pass
    else:
        hist= load(hfile)

    # scale factors
    ### TO DO: GUI should check bounds on cand and hist
    scl = np.array([ub-lb for ub,lb in zip(max_vals, min_vals)])

    t0 = time.time()

    # do a quick test to get an idea of runtime
    if test:
        nr = 200 # number of random starts for testing, set to a small number
        best_val, cand_rand, rand_index = criterion(cand, include, scl, nr, nd, mode=mode, hist=hist)
        elapsed_time = time.time() - t0
        return elapsed_time

    # if not testing, run sdoe for real...
    best_val, cand_rand, rand_index = criterion(cand, include, scl, nr, nd, mode=mode, hist=hist)
    elapsed_time = time.time() - t0

    # save the output
    fname = os.path.join(outdir, 'candidates_d{}_n{}_{}'.format(nd, nr, '+'.join(include)))
    write(fname, cand_rand)
    print(('d={}, n={}: best_val={}, elapsed_time={}s'.format(nd, nr, best_val, elapsed_time)))

    return mode, nd, nr, elapsed_time, fname, best_val


def plot(fname, hname=None, show=None, nbins=20, area=10, hbars=False):
    def plot_hist(ax, xs, xname):
        ns, bins = np.histogram(xs, nbins)
        xmin = bins[0]
        xmax = bins[-1]
        width = bins[1] - bins[0]
        center = (bins[1:] + bins[:-1]) / 2
        if hbars:
            ax.barh(center, ns, align='center', height=width)
            ax.set_ylabel(xname)
            ax.set_xlabel('Frequency')
        else:
            ax.bar(center, ns, align='center', width=width)
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
        xname = names[0]
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
            xname = names[i]
            # ... plot histogram for diagonal subplot
            ax = plot_hist(ax, df[xname], xname)

            for j in range(i + 1, nshow):
                k = sb_indices[i][j]
                ax = A[k]
                yname = names[j]
                # ... plot scatter for off-diagonal subplot
                # ... area/alpha can be customized to visualize weighted points (future feature)
                ax.scatter(df[yname], df[xname], s=area, alpha=0.5, color='b')
                if hname:
                    ax.scatter(hf[yname], hf[xname], s=area, alpha=0.5, color='orange')
                ax.set_ylabel(xname)
                ax.set_xlabel(yname)
                ax.grid(True, axis='both')

    title = 'SDOE candidates from {}'.format(fname)
    fig.canvas.set_window_title(title)
    plt.tight_layout()
    plt.show()