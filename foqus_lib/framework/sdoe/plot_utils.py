import matplotlib.pyplot as plt
import numpy as np
from .df_utils import load
from .nusf import scale_y

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
    width = bins[1] - bins[0]
    center = (bins[1:] + bins[:-1]) / 2
    if hbars:
        ax.barh(center, ns, align='center', height=width, facecolor=fc['cand'], linewidth=linewidth, edgecolor='k')
        ax.set_ylabel(xname)
    else:
        ax.bar(center, ns, align='center', width=width, facecolor=fc['cand'], linewidth=linewidth, edgecolor='k')
        ax.set_xlabel(xname)

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
        

def remove_xticklabels(ax):
    labels = [item.get_text() for item in ax.get_xticklabels()]
    no_labels = ['']*len(labels)
    ax.set_xticklabels(no_labels)
    return ax

def remove_yticklabels(ax):    
    labels = [item.get_text() for item in ax.get_yticklabels()]
    no_labels = ['']*len(labels)
    ax.set_yticklabels(no_labels)
    return ax

def plot_candidates(df, hf, show, title, scatter_label):

    # process inputs to be shown
    if show is None:
        show = list(df)
    nshow = len(show)

    # handle case for one input
    if nshow == 1:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        xname = show[0]
        ax = plot_hist(ax, df[xname], xname, show_grids=True, linewidth=0, hbars=True)

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
            ax = plot_hist(ax, df[xname], xname, show_grids=True, linewidth=0, hbars=True)

            for j in range(i + 1, nshow):
                k = sb_indices[i][j]
                ax = A[k]
                yname = show[j]
                # ... plot scatter for off-diagonal subplot
                # ... area/alpha can be customized to visualize weighted points (future feature)
                ax.scatter(df[yname], df[xname], s=area['cand'], facecolor=fc['cand'], color='b')
                if hf is not None:
                    ax.scatter(hf[yname], hf[xname], s=area['hist'], facecolor=fc['hist'], color='r', marker="*")
                ax.grid(True, axis='both')
                ax = remove_yticklabels(ax)
                if i == 0:
                    ax.xaxis.set_ticks_position('top')
                    ax.xaxis.set_label_position('top')
                else:
                    ax = remove_xticklabels(ax)

    labels = ['Frequency', scatter_label]
    if hf is not None:
        labels.append('History points')
    fig.legend(labels=labels, loc='lower left', fontsize='xx-large')

    fig.canvas.set_window_title(title)
    
    return fig


def plot_weights(xs, wt, wts, title):
    # Inputs:
    #    xs - numpy array of shape (nd, nx) containing inputs from best designs
    #    wt - numpy array of shape (nd, 1) containing weights from best designs
    #    wts - numpy array of shape (N,) containing weights from all candidates
    
    # generate subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)

    # the top subplot shows the min distance for only best designs
    from .distance import compute_dist
    dmat = compute_dist(xs)
    dist = np.sqrt(np.min(dmat, axis=1))   # Euclidean distance
    nd = dist.shape[0]
    for w, d in zip(wt, dist):
        ax1.plot([w,w],[0,d], color='b')
    ax1.set_title('Distance to closest neighbor within the design set (N={})'.format(nd))
    ax1.set_ylabel('Min distance')
    
    # the bottom subplot shows a histogram of ALL the weights from the candidate set
    ax2 = plot_hist(ax2, wts, 'Weight', show_grids=False, linewidth=1)
    N = wts.shape[0]
    ax2.set_title('Histogram of weights from the candidate set (N={})'.format(N))
    ax2.set_xlabel('Candidate weight')

    fig.canvas.set_window_title(title)
        
    return fig


def plot(fname, scatter_label, hname=None, show=None, nusf=None):
    df, hf = load_data(fname, hname)
    title = 'SDOE Candidates Visualization'
    _fig1 = plot_candidates(df, hf, show, title, scatter_label)
    if nusf:
        des = nusf['results']['best_cand_scaled'].values
        xs = des[:,:-1]    # scaled coordinates from best candidate
        wt = des[:,-1]     # scaled weights from best candidate
        scale_method = nusf['scale_method']
        cand = nusf['cand']
        wcol = nusf['wcol']
        mwr = nusf['results']['mwr']
        cand_ = scale_y(scale_method, mwr, cand, wcol)
        wts = cand_[wcol]  # scaled weights from all candidates
        title = 'SDOE (NUSF) Weight Visualization for MWR={}'.format(mwr)
        _fig2 = plot_weights(xs, wt, wts, title)
        
    plt.show()
