import matplotlib.pyplot as plt
import numpy as np
from .df_utils import load


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
