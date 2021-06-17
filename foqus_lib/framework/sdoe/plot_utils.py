###############################################################################
# FOQUS Copyright (c) 2012 - 2021, by the software owners: Oak Ridge Institute
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
#
###############################################################################
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm
import mplcursors
from .df_utils import load
from .nusf import scale_y

# plot parameters
fc = {'hist': (0.5, 0.5, 0.5, 0.5), 'cand': (0, 0, 1, 0.5), 'imp': (1, 0, 0, 0.5)}
area = {'hist': 40, 'cand': 25}


def plot_hist(ax, xs, xname,
              nbins=20,
              show_grids=True,  # set to True to show grid lines
              linewidth=0,      # set to nonzero to show border around bars 
              hbars=False,       # set to True for horizontal bars
              cand_rgba=None,
              ):

    if cand_rgba is not None:
        fc['cand'] = cand_rgba
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
        hf = load(hname, index='__id')
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


def plot_candidates(df, hf, show, title, scatter_label, cand, cand_rgba=None, wcol=None, nImpPts=0):

    if cand_rgba is not None:
        fc['cand'] = cand_rgba

    if wcol is not None:
        cand_vals = cand[wcol].values
        vals = df[wcol].values
        area['cand'] = 30 * abs((vals - np.mean(cand_vals)) / np.std(cand_vals)) + 10
        if hf is not None:
            vals_h = hf[wcol].values
            area['hist'] = 30 * abs((vals_h - np.mean(vals_h)) / np.std(vals_h)) + 10

    # process inputs to be shown
    if show is None:
        show = list(df)
    nshow = len(show)

    # handle case for one input
    if nshow == 1:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        xname = show[0]
        _ax = plot_hist(ax, df[xname], xname, show_grids=True, linewidth=0, hbars=True, cand_rgba=cand_rgba)

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
            _ax = plot_hist(ax, df[xname], xname, show_grids=True, linewidth=0, hbars=True, cand_rgba=cand_rgba)

            for j in range(i + 1, nshow):
                k = sb_indices[i][j]
                ax = A[k]
                yname = show[j]
                # ... plot scatter for off-diagonal subplot
                # ... area/alpha can be customized to visualize weighted points (future feature)
                if nImpPts == 0:
                    ax.scatter(df[yname], df[xname], s=area['cand'], facecolor=fc['cand'])
                else:
                    ax.scatter(df[yname][0:-nImpPts], df[xname][0:-nImpPts], s=area['cand'], facecolor=fc['cand'])
                    ax.scatter(df[yname][-nImpPts:], df[xname][-nImpPts:], s=area['cand'], facecolor=fc['imp'])

                if hf is not None:
                    ax.scatter(hf[yname], hf[xname], s=area['hist'], facecolor=fc['hist'])

                # Setting axis limits to min and max values of the candidate set plus some padding
                if cand is not None:
                    xdelta = (max(cand[yname]) - min(cand[yname])) / 20
                    ydelta = (max(cand[xname]) - min(cand[xname])) / 20
                    ax.set_xlim((min(cand[yname]) - xdelta, max(cand[yname]) + xdelta))
                    ax.set_ylim((min(cand[xname]) - ydelta, max(cand[xname]) + ydelta))
                else:
                    xdelta = (max(df[yname]) - min(df[yname])) / 20
                    ydelta = (max(df[xname]) - min(df[xname])) / 20
                    ax.set_xlim((min(df[yname]) - xdelta, max(df[yname]) + xdelta))
                    ax.set_ylim((min(df[xname]) - ydelta, max(df[xname]) + ydelta))

                ax.grid(True, axis='both')
                ax = remove_yticklabels(ax)
                if i == 0:
                    ax.xaxis.set_ticks_position('top')
                    ax.xaxis.set_label_position('top')
                else:
                    _ax = remove_xticklabels(ax)

    labels = ['Frequency', scatter_label]
    if nImpPts > 0:
        labels.append('Imputed')
    if hf is not None:
        labels.append('Previous data points')
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
        ax1.plot([w, w], [0, d], color='b')
    ax1.set_title('Distance to closest neighbor within the design set (N={})'.format(nd))
    ax1.set_ylabel('Min distance')
    
    # the bottom subplot shows a histogram of ALL the weights from the candidate set
    ax2 = plot_hist(ax2, wts, 'Weight', show_grids=False, linewidth=1)
    N = wts.shape[0]
    ax2.set_title('Histogram of weights from the candidate set (N={})'.format(N))
    ax2.set_xlabel('Candidate weight')

    fig.canvas.set_window_title(title)
        
    return fig


def plot(fname, scatter_label, hname=None, show=None, usf=None, nusf=None, irsf=None, nImpPts=0):
    df, hf = load_data(fname, hname)
    title = 'SDOE Candidates Visualization'
    if usf:
        cand = usf['cand']
        wcol = None
    elif nusf:
        cand = nusf['cand']
        wcol = nusf['wcol']
    elif irsf:
        cand = irsf['cand']
        wcol = None
    else:
        cand = None
        wcol = None
    _fig1 = plot_candidates(df, hf, show, title, scatter_label, cand, wcol=wcol, nImpPts=nImpPts)
    if nusf:
        des = nusf['results']['best_cand_scaled'].values
        xs = des[:, :-1]    # scaled coordinates from best candidate
        wt = des[:, -1]     # scaled weights from best candidate
        scale_method = nusf['scale_method']
        cand = nusf['cand']
        idw = nusf['wcol']
        idw_np = cand.columns.get_loc(idw)
        cand_np = cand.to_numpy()
        mwr = nusf['results']['mwr']
        cand_ = scale_y(scale_method, mwr, cand_np, idw_np)
        wts = cand_[:, idw_np]  # scaled weights from all candidates
        title = 'SDOE (NUSF) Weight Visualization for MWR={}'.format(mwr)
        _fig2 = plot_weights(xs, wt, wts, title)
        
    plt.show()


def plot_pareto(pf, results, cand):  # Plot Pareto front with hovering labels

    def onpick(event):  # Define nested function onpick
        if event.artist != points:
            return True

        N = len(event.ind)
        if not N:
            return True

        for _subplotnum, dataind in enumerate(event.ind):
            df = results[dataind+1]['des']
            hf = None
            show = None
            title = 'Design %s, Input Distance: %s, ' \
                    'Response Distance: %s' % (dataind + 1,
                                               str(round(pf['Best Input'][dataind], 4)),
                                               str(round(pf['Best Response'][dataind], 4)))
            scatter_label = 'Design Points'
            figi = plot_candidates(df, hf, show, title, scatter_label, cand, cand_rgba=colors[dataind])
            
        figi.show()
        return True

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_xlabel('Maximin Input Distance')
    ax.set_ylabel('Maximin Response Distance')
    colors = cm.rainbow(np.linspace(0, 1, len(pf)))
    for i, c in enumerate(colors):
        x = pf['Best Input'][i]
        y = pf['Best Response'][i]
        lab = pf['Design'][i]

        ax.scatter(x, y, label=lab, c=c, marker='D', zorder=2)

    ax.legend(title='Designs', ncol=4)

    points = ax.scatter(pf['Best Input'], pf['Best Response'], marker='D', color=colors, zorder=2, picker=len(pf))
    _line = ax.plot(pf['Best Input'], pf['Best Response'], zorder=1, color='black', linewidth=1)
    cursor = mplcursors.cursor(points, hover=True)
    _mpl = cursor.connect("add", lambda sel: sel.annotation.set_text(
        "Input Distance: %s\n Response Distance: %s" % (str(round(sel.target[0], 4)), str(round(sel.target[1], 4)))))

    fig.canvas.set_window_title('Pareto Front')
    fig.canvas.mpl_connect('pick_event', onpick)

    plt.show()
