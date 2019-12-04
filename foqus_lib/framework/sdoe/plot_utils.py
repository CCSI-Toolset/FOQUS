import matplotlib.pyplot as plt
import numpy as np
from .df_utils import load

# plot parameters
fc = {'hist': (1, 0, 0, 0.5), 'cand': (0, 0, 1, 0.5)}
area = {'hist': 40, 'cand': 25}


def plot_hist(ax, xs, xname,
              nbins=20,
              show_grids=True,  # set to True to show grid lines
              linewidth=0,      # set to nonzero to show border around bars 
              hbars=False       # set to True for horizontal bars 
):
    ns, bins = np.histogram(xs, nbins)
    xmin = bins[0]
    xmax = bins[-1]
    width = bins[1] - bins[0]
    center = (bins[1:] + bins[:-1]) / 2
    if hbars:
        ax.barh(center, ns, align='center', height=width, fc=fc['cand'], linewidth=linewidth, edgecolor='k')
        ax.set_ylabel(xname)
        ax.set_xlabel('Frequency')
    else:
        ax.bar(center, ns, align='center', width=width, fc=fc['cand'], linewidth=linewidth, edgecolor='k')
        ax.set_xlabel(xname)
        ax.set_ylabel('Frequency')

    ax.grid(show_grids, axis='both')
    return ax


def load_data(fname, hname):
    # load results
    df = load(fname)
    names = list(df)
    # load history
    hf = None
    if hname:
        hf = load(hname)
        # make sure headers match
        assert (names == list(hf))
    return df, hf
        

def plot_candidates(df, hf, show):

    # process inputs to be shown
    if show is None:
        show = list(df)
    nshow = len(show)

    # handle case for one input
    if nshow == 1:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        xname = show[0]
        ax = plot_hist(ax, df[xname], xname, show_grids=True, linewidth=0)

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
            ax = plot_hist(ax, df[xname], xname, show_grids=True, linewidth=0)

            for j in range(i + 1, nshow):
                k = sb_indices[i][j]
                ax = A[k]
                yname = show[j]
                # ... plot scatter for off-diagonal subplot
                # ... area/alpha can be customized to visualize weighted points (future feature)
                ax.scatter(df[yname], df[xname], s=area['cand'], fc=fc['cand'], color='b')
                if hf:
                    ax.scatter(hf[yname], hf[xname], s=area['hist'], fc=fc['hist'], color='r', marker="*")
                ax.set_ylabel(xname)
                ax.set_xlabel(yname)
                ax.grid(True, axis='both')

    if hf:
        fig.legend(labels=['cand', 'cand', 'hist'], loc='lower left', fontsize='xx-large')
    else:
        fig.legend(labels=['cand', 'cand'], loc='lower left', fontsize='xx-large')

    return fig


def plot_weights(wts, dmat, fname):
    
    # generate subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)

    # plot histogram of weights
    ax2 = plot_hist(ax2, wts, 'Weight', show_grids=False, linewidth=1) 
    
    # plot min distances
    for w, d in zip(wts, np.min(dmat, axis=0)):
        ax1.plot([w,w],[0,d], color='b')
        ax1.set_ylabel('Min distance')

    title = 'SDOE (NUSF) Weights from {}'.format(fname)
    fig.canvas.set_window_title(title)
        
    return fig


def plot(fname, hname=None, show=None, nusf=None):
    df, hf = load_data(fname, hname)
    fig1 = plot_candidates(df, hf, show)
    title = 'SDOE candidates from {}'.format(fname)
    fig1.canvas.set_window_title(title)
    if nusf:
        wts = df.iloc[:,-1]
        dmat = np.load(nusf['dmat'])
        fig2 = plot_weights(wts, dmat, fname)
        title = 'SDOE (NUSF) weights from {}'.format(fname)
        fig2.canvas.set_window_title(title)
        
    plt.show()


# ------------
'''
Example:

fname = '/Users/ng30/Downloads/nusf_results/nusf_d20_n50_m5_Label+X1+X2+Values.csv'
dname = '/Users/ng30/Downloads/nusf_results/nusf_dmat_d20_n50_m5_Label+X1+X2+Values.npy'
plot(fname, nusf={'dmat': dname, 'wt': 'Values'})
'''
