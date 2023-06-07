#################################################################################
# FOQUS Copyright (c) 2012 - 2023, by the software owners: Oak Ridge Institute
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
#################################################################################
import re
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cmx
from matplotlib.figure import Figure

try:
    from PyQt5 import QtCore, QtWidgets

    usePyQt = True
except:
    usePyQt = False

plt.rcParams["figure.figsize"] = 10, 10
useFrameAlpha = False
mplVersion = mpl.__version__.split(".")
if int(mplVersion[0]) > 1 or (int(mplVersion[0]) == 1 and int(mplVersion[1]) >= 3):
    useFrameAlpha = True

if usePyQt:

    class PlotDialog(QtWidgets.QDialog):
        def __init__(self, parent=None):
            super(PlotDialog, self).__init__(parent)
            self.figure = Figure(
                figsize=(600, 400),
                dpi=72,
                facecolor=(1, 1, 1),
                edgecolor=(0, 0, 0),
                tight_layout=True,
            )
            self.gridLayout = QtWidgets.QGridLayout(self)

            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            Plotter.currentDialogs.append(
                self
            )  # Set a pointer to this dialog so it is not garbage collected
            print("INFO START HERE: ", Plotter.currentDialogs)

        def closeEvent(self, event):
            Plotter.currentDialogs.remove(self)
            # WHY the missing `can_exit` variable looks like a legitimate cause of runtime error
            # which suggests that this function is not being run
            if can_exit:  # TODO pylint: disable=undefined-variable
                event.accept()  # let the window close
            else:
                event.ignore()


class Plotter:

    currentDialogs = []

    @staticmethod
    def getdata(fname, datvar, grabline=False):

        # read output file
        f = open(fname)
        lines = f.read()
        f.close()

        # delete \r
        lines = lines.replace("\r", "")

        # grab data
        pat = "%s = \[\n(.*?)[\s\n]\]'*;\s*\n" % datvar
        if grabline:
            pat = "%s = (.*?);" % datvar
        regex = re.findall(pat, lines, re.DOTALL)

        # process only the first match
        i = 0
        nlines = len(regex[i].split("\n"))
        tokens = regex[i].split()
        ntokens = len(tokens)
        dat = [float(s) for s in tokens]
        if (ntokens > nlines) & (nlines > 1):  # reshape data if it's a matrix
            ncols = ntokens / nlines
            dat = np.reshape(dat, [int(nlines), int(ncols)])

        return dat

    @staticmethod
    def gencolors(ncolors, cmap):

        cm = plt.get_cmap(cmap)
        vv = list(range(ncolors))
        cNorm = colors.Normalize(vmin=0, vmax=vv[-1])
        scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)
        colorVals = [scalarMap.to_rgba(i) for i in range(ncolors)]

        return colorVals

    @staticmethod
    def emptypatch():

        from matplotlib.patches import Rectangle

        return Rectangle(
            (0, 0), 0.01, 0.01, fc="w", fill=False, edgecolor="none", linewidth=0
        )

    @staticmethod
    def plotline(xdat, ydat, figtitle, title, xlabel, ylabel):

        fig = plt.figure()
        fig.canvas.manager.set_window_title(figtitle)
        _ax = fig.add_subplot(111)
        plt.plot(xdat, ydat, color="b", linewidth=2)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        plt.autoscale(enable=True, axis="both")
        plt.grid()
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plotscatter(xdat, ydat, figtitle, title, xlabel, ylabel, ylim, star=None):

        nseries, _npts = xdat.shape  # number of data series

        # check if there are multiple plots to generate
        if nseries > 1:

            colorVals = Plotter.gencolors(nseries, "jet")

            # generate subplots
            if nseries < 4:
                ncols = 1
                nrows = nseries
            else:
                p = np.sqrt(nseries)
                ncols = int(np.floor(p))
                nrows = int(np.ceil(float(nseries) / ncols))

            fig, axes = plt.subplots(nrows=nrows, ncols=ncols)
            i = 0
            for ax in axes.flat:
                if i < nseries:
                    c = colorVals[i]
                    if star is not None:
                        k = [e for e in range(len(xdat[i])) if e not in star]
                        l = [e for e in range(len(xdat[i])) if e in star]
                        ax.scatter(xdat[i][k], ydat[i][k], color="k", s=40)
                        ax.scatter(xdat[i][l], ydat[i][l], color=c, marker="*", s=80)
                    else:
                        ax.scatter(xdat[i], ydat[i], color=c, s=80)
                    ax.set_xlabel(xlabel[i])
                    ax.set_ylabel(ylabel[i])
                    ax.xaxis.grid(True)
                    ax.yaxis.grid(True)
                    if ylim is not None:  # force same y-axis limits across subplots
                        ax.set_ylim(ylim)
                    ax.autoscale(enable=True, axis="x", tight=True)
                    ax.set_title(title[i])

                else:
                    fig.delaxes(ax)

                i = i + 1  # increment plot count

            # add subplot zooming
            fig.canvas.mpl_connect("button_press_event", Plotter.on_click)

        else:

            # generate single plot
            fig = plt.figure()

            ax = fig.add_subplot(111)
            c = "m"
            if star is not None:
                k = [e for e in range(len(xdat[0])) if e not in star]
                l = [e for e in range(len(xdat[0])) if e in star]
                ax.scatter(xdat[0][k], ydat[0][k], color="k", s=40)
                ax.scatter(xdat[0][l], ydat[0][l], color=c, marker="*", s=80)
            else:
                ax.scatter(xdat[0], ydat[0], color=c, s=80)
            ax.set_xlabel(xlabel[0])
            ax.set_ylabel(ylabel[0])
            ax.xaxis.grid(True)
            ax.yaxis.grid(True)
            ax.autoscale(enable=True, axis="both", tight=True)
            ax.set_title(title[0])

        fig.canvas.manager.set_window_title(figtitle)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plotscatter3d(xdat, ydat, zdat, figtitle, title, xlabel, ylabel, zlabel):

        fig = plt.figure()
        fig.canvas.manager.set_window_title(figtitle)
        ax = fig.add_subplot(111, projection="3d")
        ax.scatter(xdat, ydat, zdat, c="m", marker="o")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_zlabel(zlabel)
        plt.title(title)
        plt.autoscale(enable=True, axis="both")
        plt.grid()
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plothist(
        dat, moments, figtitle, title, xlabel, ylabel, plotcdf=True, lastplot=True
    ):

        fig = plt.figure()
        fig.canvas.manager.set_window_title(figtitle)

        # plot PDF
        if plotcdf:
            ax1 = fig.add_subplot(211)
        else:
            ax1 = fig.add_subplot(111)
        opacity = 1
        nbins = 15
        bheights, bedges = np.histogram(dat, nbins)
        w = np.diff(bedges)
        w = w[0]
        norm_area = False
        if norm_area:  # areas of histogram bars sum to 1
            bareas = [h * w for h in bheights]
            bheights_normed = bheights / float(sum(bareas))
        else:  # heights of histogram bars sum to 1
            bheights_normed = bheights / float(sum(bheights))
        xdat = bedges[:-1]
        ydat = bheights_normed
        ax1.bar(
            xdat, ydat, color="g", width=w, align="center", alpha=opacity, edgecolor="k"
        )
        ax1.set_xlabel(xlabel)
        ax1.set_ylabel(ylabel)
        ax1.set_title(title)

        dummy = Plotter.emptypatch()
        s = "    "
        numValidStats = 0
        validStats = []
        for stat, desc in zip(
            ["mean", "std", "skew", "kurt"], ["mean", "std dev", "skewness", "kurtosis"]
        ):
            if moments[stat] != "":
                numValidStats += 1
                validStats.append("Sample %s: " % desc + moments[stat] + s)

        if useFrameAlpha:
            ax1.legend(
                [dummy] * numValidStats,
                validStats,
                loc=0,
                prop={"size": 10},
                framealpha=0.8,
            )
        else:
            ax1.legend([dummy] * numValidStats, validStats, loc=0, prop={"size": 10})

        xmin = min(xdat)
        xmax = max(xdat)
        ax1.set_xlim(xmin, xmax)
        ax1.xaxis.grid(True)
        ax1.yaxis.grid(True)

        if plotcdf:

            # plot CDF
            ax2 = fig.add_subplot(212)
            ax2.plot(xdat, np.cumsum(ydat), linewidth=3, color="k")
            ax2.set_xlabel(xlabel)
            ax2.set_ylabel(ylabel)
            m = re.findall(".* for (.*)", title)
            if m:
                title = "Cumulative Distribution for " + m[0]
            else:
                title = "Corresponding Cumulative Distribution"
            ax2.set_title(title)
            ax2.set_xlim(xmin, xmax)
            ax2.xaxis.grid(True)
            ax2.yaxis.grid(True)

        plt.tight_layout()

        if lastplot:
            plt.show()

    @staticmethod
    def plotpdf(xdat, ydat, moments, pdfs, figtitle, title, xlabel, ylabel):

        fig = plt.figure()
        fig.canvas.manager.set_window_title(figtitle)

        # plot PDF
        ax1 = fig.add_subplot(211)
        opacity = [0.5, 0.25]
        w = xdat[1] - xdat[0]  # assume uniform distance between xdat elements
        pdf1 = ax1.bar(
            xdat,
            ydat[0],
            color="y",
            width=w,
            yerr=None,
            error_kw={"ecolor": "b", "elinewidth": 6, "capsize": 10},
            align="center",
            alpha=opacity[0],
            edgecolor="k",
        )
        legend_handles = [pdf1]
        legend_labels = ["PDF"]
        if pdfs is not None:
            pdf2 = ax1.bar(
                xdat,
                ydat[1],
                color="g",
                width=w,
                yerr=None,
                error_kw={"ecolor": "b", "elinewidth": 6, "capsize": 10},
                align="center",
                alpha=opacity[1],
                edgecolor="k",
            )
            legend_handles = [pdf1, pdf2]
            legend_labels = ["Ensemble PDF", "Mean PDF"]
        if useFrameAlpha:
            pdflegend = plt.legend(legend_handles, legend_labels, loc=1, framealpha=0.8)
        else:
            pdflegend = plt.legend(legend_handles, legend_labels, loc=1)
        ax1.set_xlabel(xlabel)
        ax1.set_ylabel(ylabel)
        ax1.set_title(title)

        dummy = Plotter.emptypatch()
        s = "    "
        if useFrameAlpha:
            ax1.legend(
                [dummy, dummy, dummy, dummy, dummy],
                [
                    "STATISTICS FOR MEAN PDF",
                    "Sample mean: " + moments["mean"] + s,
                    "Sample std dev: " + moments["std"] + s,
                    "Sample skewness: " + moments["skew"] + s,
                    "Sample kurtosis: " + moments["kurt"] + s,
                ],
                loc=2,
                prop={"size": 10},
                framealpha=0.8,
            )
        else:
            ax1.legend(
                [dummy, dummy, dummy, dummy, dummy],
                [
                    "STATISTICS FOR MEAN PDF",
                    "Sample mean: " + moments["mean"] + s,
                    "Sample std dev: " + moments["std"] + s,
                    "Sample skewness: " + moments["skew"] + s,
                    "Sample kurtosis: " + moments["kurt"] + s,
                ],
                loc=2,
                prop={"size": 10},
            )

        ax1.add_artist(pdflegend)

        xmin = min(xdat)
        xmax = max(xdat)
        ax1.set_xlim(xmin, xmax)
        ax1.xaxis.grid(True)
        ax1.yaxis.grid(True)

        # plot CDF
        ax2 = fig.add_subplot(212)
        if pdfs is None:
            ax2.plot(xdat, np.cumsum(ydat[0]), linewidth=3, color="k", label="CDF")
        else:  # handle multiple PDFs as a result of RS uncertainty
            P = len(pdfs)
            colorVals = Plotter.gencolors(P, "jet")
            for i in range(P):
                cdf = np.cumsum(pdfs[i])
                if i == 3:
                    ax2.plot(xdat, cdf, linewidth=3, color="k", label="Mean CDF")
                else:
                    ax2.plot(xdat, cdf, color=colorVals[i])
        if useFrameAlpha:
            ax2.legend(loc=0, framealpha=0.8)
        else:
            ax2.legend(loc=0)
        ax2.set_xlabel(xlabel)
        ax2.set_ylabel(ylabel)
        m = re.findall(".* for (.*)", title)
        if m:
            title = "Cumulative Distribution for " + m[0]
        else:
            title = "Corresponding Cumulative Distribution"
        ax2.set_title(title)
        ax2.set_xlim(xmin, xmax)
        ax2.set_ylim(0, 1)
        ax2.xaxis.grid(True)
        ax2.yaxis.grid(True)

        plt.tight_layout()
        plt.show()

    @staticmethod
    def plotcdf(cdfs, figtitle, title, xlabel, ylabel):
        # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
        # Discrete slider code adapted from
        # http://stackoverflow.com/questions/13656387/can-i-make-matplotlib-sliders-more-discrete
        # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

        from matplotlib.widgets import Slider

        class ChangingPlot(object):
            def __init__(self):

                # process data
                self.cdfs = np.array(cdfs)
                xx = self.cdfs.flatten()

                self.xmin = np.min(xx)
                self.xmax = np.max(xx)
                P = len(cdfs)
                self.cdfU = cdfs[P - 1]
                self.cdfL = cdfs[P - 2]
                self.xlabel = xlabel
                self.ylen = len(cdfs[0])
                self.ydat = [float(i) / self.ylen for i in range(1, self.ylen + 1)]

                # set up slider steps
                N = len(self.cdfU)
                self.steps = np.linspace(self.xmin, self.xmax, num=N)
                self.inc = self.steps[1] - self.steps[0]

                # set up figure and slider
                left = 0.15
                bottom = 0.15
                width = 0.75
                height = 0.03
                self.fig = plt.figure()
                self.fig.canvas.manager.set_window_title(figtitle)
                self.ax = self.fig.add_subplot(111)
                plt.subplots_adjust(left=left, bottom=2 * bottom)
                self.sliderax = self.fig.add_axes(
                    [left, bottom, width, height], facecolor="lightgoldenrodyellow"
                )
                value = self.steps[1]
                self.slider = Slider(
                    self.sliderax,
                    xlabel,
                    self.xmin,
                    self.xmax,
                    valstep=self.steps,
                    facecolor="k",
                    valinit=value,
                    valfmt="%f",
                )
                self.slider.valtext.set_text("")

                (k1,) = np.where(self.cdfL < value)
                (k2,) = np.where(self.cdfU < value)
                y1 = self.ydat[min(len(k1), self.ylen - 1)]
                y2 = self.ydat[min(len(k2), self.ylen - 1)]
                slabel = (
                    "Move slider to select input to get corresponding probability range.\n\nProb(%s=%f) -> [%f,%f]"
                    % (self.xlabel, value, y1, y2)
                )
                self.sliderax.set_title(slabel)
                self.slider.on_changed(self.update)

                # assume particular order of CDFs
                for i in range(P - 2):
                    self.ax.plot(self.cdfs[i], self.ydat, color="k")
                (_yu,) = self.ax.plot(
                    self.cdfU, self.ydat, linewidth=3, color="r", label="Upper CDF"
                )
                (_yl,) = self.ax.plot(
                    self.cdfL, self.ydat, linewidth=3, color="b", label="Lower CDF"
                )

                # draw new line
                (self.yrange,) = self.ax.plot(
                    [value, value],
                    [y1, y2],
                    linewidth=6,
                    color="g",
                    label="Prob(%s=%f) -> [%.4f,%.4f]" % (self.xlabel, value, y1, y2),
                )
                if useFrameAlpha:
                    self.ax.legend(loc=0, framealpha=0.8)
                else:
                    self.ax.legend(loc=0)

                # label plot
                self.ax.set_xlabel(self.xlabel)
                self.ax.set_ylabel(ylabel)
                self.ax.xaxis.grid(True)
                self.ax.yaxis.grid(True)
                self.ax.set_xlim([self.xmin, self.xmax])
                self.ax.set_ylim([0, 1])
                self.ax.set_title(title)

                self.update(value)
                self.slider.set_val(self.xmin)

            def update(self, value):
                # remove last line
                self.ax.lines.remove(self.yrange)

                # draw new line
                (k1,) = np.where(self.cdfL < value)
                (k2,) = np.where(self.cdfU < value)
                y1 = self.ydat[min(len(k1), self.ylen - 1)]
                y2 = self.ydat[min(len(k2), self.ylen - 1)]
                (self.yrange,) = self.ax.plot(
                    [value, value],
                    [y1, y2],
                    linewidth=6,
                    color="g",
                    label="Prob(%s=%f) -> [%.4f,%.4f]" % (self.xlabel, value, y1, y2),
                )
                if useFrameAlpha:
                    self.ax.legend(loc=0, framealpha=0.8)
                else:
                    self.ax.legend(loc=0)
                slabel = (
                    "Move slider to select input to get corresponding probability range.\n\nProb(%s=%f) -> [%f,%f]"
                    % (self.xlabel, value, y1, y2)
                )
                self.sliderax.set_title(slabel)
                self.fig.canvas.draw()

            def show(self):
                plt.show()

        p = ChangingPlot()
        p.show()

    @staticmethod
    def autolabel(ax, rects):
        for rect in rects:
            height = rect.get_height()
            ax.text(
                rect.get_x() + rect.get_width() / 2.0,
                1.05 * height,
                "%.3f" % height,
                ha="center",
                va="bottom",
            )

    @staticmethod
    def plotbar(
        dat, std, figtitle, title, xlabel, ylabel, xticklabels, barlabels=False
    ):

        opacity = 1
        w = 1

        # check if dat is a multi-dim array
        if isinstance(dat[0], list):

            # generate subplots
            nplots = len(dat)
            colorVals = Plotter.gencolors(nplots, "summer_r")
            fig, ax = plt.subplots(nrows=nplots, ncols=1, sharex=True)
            for i in range(nplots):
                dat_i = dat[i]
                std_i = std[i]
                index = np.arange(len(dat_i))
                rects = ax[i].bar(
                    index,
                    dat_i,
                    color=colorVals[i],
                    width=w,
                    yerr=std_i,
                    error_kw={"ecolor": "b", "elinewidth": 6, "capsize": 10},
                    align="center",
                    alpha=opacity,
                    edgecolor="k",
                )
                ax[i].set_ylabel(ylabel[i])
                ax[i].xaxis.grid(True)
                ax[i].yaxis.grid(True)
                ax[i].autoscale(enable=True, axis="x", tight=True)
                if std_i is not None:
                    topVals = [d + s for d, s in zip(dat_i, std_i)]
                    ax[i].set_ylim(0, max(topVals))  # cap error bars at 0
                if barlabels:
                    Plotter.autolabel(ax[i], rects)
            ax[0].set_title(title)

        else:

            # generate single plot
            fig = plt.figure()
            ax = fig.add_subplot(111)
            index = np.arange(len(dat))
            rects = ax.bar(
                index,
                dat,
                color="y",
                width=w,
                yerr=std,
                error_kw={"ecolor": "b", "elinewidth": 6, "capsize": 10},
                align="center",
                alpha=opacity,
                edgecolor="k",
            )
            ax.set_ylabel(ylabel)
            ax.xaxis.grid(True)
            ax.yaxis.grid(True)
            ax.autoscale(enable=True, axis="x", tight=True)
            if std is not None:
                topVals = [d + s for d, s in zip(dat, std)]
                ax.set_ylim(0, max(topVals))  # cap error bars at 0
            ax.set_title(title)
            if barlabels:
                Plotter.autolabel(ax, rects)

        fig.canvas.manager.set_window_title(figtitle)
        plt.xlabel(xlabel)
        if xticklabels:
            plt.xticks(index, xticklabels, rotation=90)

        plt.tight_layout()
        plt.show()

    @staticmethod
    def plotbar3d(
        dat,
        std,
        figtitle,
        title,
        xlabel,
        ylabel,
        xticklabels,
        yticklabels,
        barlabels=False,
    ):

        _xlabel = xlabel
        _ylabel = ylabel
        _barlabels = barlabels

        lx = len(dat[0])
        ly = len(dat[:, 0])
        n = lx * ly

        # generate plot data
        xpos = np.arange(0, lx, 1)
        ypos = np.arange(0, ly, 1)
        xpos, ypos = np.meshgrid(xpos + 0.25, ypos + 0.25)
        xpos = xpos.flatten()
        ypos = ypos.flatten()
        zpos = np.zeros(n)
        dx = 0.5 * np.ones_like(zpos)
        dy = dx.copy()
        dz = dat.flatten()
        dz[np.argwhere(dz < np.spacing(1))] = 0  # zero out small elements
        cc = np.tile(list(range(lx)), (ly, 1))
        cc = cc.T.flatten()

        # generate colors
        ncolors = len(dat)
        colorVals = Plotter.gencolors(ncolors, "jet")

        # generate plot
        fig = plt.figure()
        fig.canvas.manager.set_window_title(figtitle)
        ax = fig.add_subplot(111, projection="3d")
        opacity = 0.25

        # plot 3d bars
        for i in range(n):
            ax.bar3d(
                xpos[i],
                ypos[i],
                zpos[i],
                dx[i],
                dy[i],
                dz[i],
                color=colorVals[cc[i]],
                alpha=opacity,
                zsort="average",
                edgecolor="k",
            )
            ax.text(xpos[i], ypos[i], zpos[i], "%.3f" % dz[i], ha="center", va="bottom")

        # plot errorbars
        if std is not None:
            thresh = 0.0001  # plot error bars only for non-negligible errors > 1%
            epsilon = np.finfo(np.double).eps
            std = std.flatten()
            for i in range(n):
                e = std[i]
                if e / (dz[i] + epsilon) < thresh:
                    continue
                xi = xpos[i] + 0.25
                yi = ypos[i] + 0.25
                ax.plot(
                    [xi, xi],
                    [yi, yi],
                    [max(0, dz[i] - e), dz[i] + e],
                    color=colorVals[cc[i]],
                    alpha=1,
                    linewidth=8,
                    marker="o",
                    markersize=12,
                    markeredgecolor="k",
                    markerfacecolor="k",
                )

        plt.title(title)

        if xticklabels:
            ticksx = np.arange(0.5, lx, 1)
            plt.xticks(ticksx, xticklabels)

        if yticklabels:
            ticksy = np.arange(0.5, lx, 1)
            plt.yticks(ticksy, yticklabels)

        plt.autoscale(enable=True, axis="both")
        plt.grid()
        plt.show()

    @staticmethod
    def plotisoline(xdat, ydat, zdatm, figtitle, title, xlabel, ylabel, zlabel):

        # process data
        # ... plot_surface does not support masked arrays
        zdat = zdatm.data
        zdat[np.where(np.ma.getmask(zdatm) == True)] = np.nan
        zdat_notnan = zdat[np.where(np.ma.getmask(zdatm) == False)]

        # plot
        fig = plt.figure(figsize=(12, 10))  # adjust figure size
        fig.canvas.manager.set_window_title(figtitle)

        # ... generate 3D surface plot
        step = 1
        opacity = 1
        ax1 = fig.add_subplot(121, projection="3d")
        norm = colors.Normalize(vmin=np.min(zdat_notnan), vmax=np.max(zdat_notnan))
        cs1 = ax1.plot_surface(
            xdat,
            ydat,
            zdat,
            rstride=step,
            cstride=step,
            linewidth=0,
            cmap=cmx.get_cmap("jet"),
            norm=norm,
            alpha=opacity,
            antialiased=True,
        )
        fig.colorbar(cs1, ax=ax1)
        ax1.set_xlabel(xlabel)
        ax1.set_ylabel(ylabel)
        ax1.set_zlabel(zlabel)
        ax1.xaxis.grid(True)
        ax1.yaxis.grid(True)
        ax1.zaxis.grid(True)
        ax1.autoscale(enable=True, axis="both", tight=True)
        dummy = Plotter.emptypatch()
        if useFrameAlpha:
            ax1.legend([dummy], ["Surface plot"], loc=0, framealpha=0.8)
        else:
            ax1.legend([dummy], ["Surface plot"], loc=0)

        # ... generate 2D contour plot
        nc = 10  # number of contour lines
        ax2 = fig.add_subplot(122)
        _cs2 = ax2.contour(xdat, ydat, zdatm, nc, colors="k", linewidths=1)
        cs2f = ax2.contourf(xdat, ydat, zdatm, nc, cmap=cmx.get_cmap("jet"))
        fig.colorbar(cs2f, ax=ax2)
        labels = ax2.get_xticklabels()
        for label in labels:  # rotate the xtick labels to avoid bunching
            label.set_rotation(90)
        ax2.set_xlabel(xlabel)
        ax2.set_ylabel(ylabel)
        ax2.xaxis.grid(True)
        ax2.yaxis.grid(True)
        ax2.autoscale(enable=True, axis="both", tight=True)
        if useFrameAlpha:
            ax2.legend([dummy], ["Contour plot"], loc=0, framealpha=0.8)
        else:
            ax2.legend([dummy], ["Contour plot"], loc=0)

        fig.suptitle(title)
        plt.subplots_adjust(wspace=0.5)  # add space to for super title and subplots

        plt.show()

    @staticmethod
    def plotisosurface(
        xdat, ydat, zdat, vdat, figtitle, title, xlabel, ylabel, zlabel, vlabel
    ):
        # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
        # Discrete slider code adapted from
        # http://stackoverflow.com/questions/13656387/can-i-make-matplotlib-sliders-more-discrete
        # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

        from matplotlib.widgets import Slider

        class ChangingPlot(object):
            def __init__(self):

                # process data
                # ... since we are displaying the isosurface as a scatterplot, flattened arrays are all we need
                self.Xf = xdat.flatten()
                self.Yf = ydat.flatten()
                self.Zf = zdat.flatten()
                self.Vf = vdat.flatten()
                self.xmin = np.min(self.Xf)
                self.xmax = np.max(self.Xf)
                self.ymin = np.min(self.Yf)
                self.ymax = np.max(self.Yf)
                self.zmin = np.min(self.Zf)
                self.zmax = np.max(self.Zf)
                self.vmin = np.min(self.Vf)
                self.vmax = np.max(self.Vf)

                # set up slider steps
                N = 20
                self.steps = np.linspace(self.vmin, self.vmax, num=N)
                self.inc = self.steps[1] - self.steps[0]

                # set up colors
                self.norm = colors.Normalize(vmin=self.vmin, vmax=self.vmax)
                self.cmap = "jet"
                self.scalarMap = cmx.ScalarMappable(norm=self.norm, cmap=self.cmap)

                # set up figure and slider
                left = 0.15
                bottom = 0.15
                width = 0.65
                height = 0.03
                self.fig = plt.figure(figsize=(12, 12))  # adjust figure size
                self.fig.canvas.manager.set_window_title(figtitle)
                self.ax = self.fig.add_subplot(111, projection="3d")
                plt.subplots_adjust(left=left, bottom=2 * bottom)
                self.sliderax = self.fig.add_axes(
                    [left, bottom, width, height], facecolor="lightgoldenrodyellow"
                )
                self.slider = Slider(
                    self.sliderax,
                    vlabel,
                    self.vmin,
                    self.vmax,
                    valstep=self.steps,
                    facecolor="k",
                    valinit=self.steps[1],
                    valfmt="",
                )
                self.slider.valtext.set_text(
                    "Min: %.4f\nMax: %.4f" % (self.steps[0], self.steps[1])
                )  # display slider range
                slabel = (
                    "Move BLACK slider to select output range.\n"
                    "Points shown represent the inputs responsible for the output response.\n"
                )
                self.sliderax.set_title(slabel)
                self.slider.on_changed(self.update)

                # set up colorbar
                self.cbax = self.fig.add_axes([left, bottom - height, width, height])
                self.fig.colorbar = mpl.colorbar.ColorbarBase(
                    self.cbax,
                    cmap=cmx.get_cmap(self.cmap),
                    norm=self.norm,
                    ticks=self.steps,  # optional
                    spacing="proportional",  # discrete levels
                    orientation="horizontal",
                )
                for label in self.fig.colorbar.ax.get_xticklabels():
                    label.set_rotation(90)

                # plot 3D scatter plot of points satisfying f(X,Y,Z) \in [val-dv, val]
                # ... mask points that do NOT satisfy f(X,Y,Z) \in [val-dv, val]
                lb = self.steps[0]
                ub = self.steps[1]
                Vm = np.ma.array(self.Vf)
                Vm = np.ma.masked_where(Vm < lb, Vm)
                Vm = np.ma.masked_where(Vm > ub, Vm)
                cval = self.scalarMap.to_rgba(ub)
                ii = np.where(np.ma.getmask(Vm) == False)
                # ... generate scatterplot of points that DO satisfy f(X,Y,Z) \in [val-dv, val]
                if ii:
                    self.sc = self.ax.scatter3D(
                        self.Xf[ii], self.Yf[ii], self.Zf[ii], color=cval
                    )
                    self.ax.set_xlim3d(self.xmin, self.xmax)
                    self.ax.set_ylim3d(self.ymin, self.ymax)
                    self.ax.set_zlim3d(self.zmin, self.zmax)

                # label plot
                self.ax.set_xlabel(xlabel)
                self.ax.set_ylabel(ylabel)
                self.ax.set_zlabel(zlabel)
                self.fig.suptitle(title)

            def update(self, value):

                # remove old scatterplot
                self.ax.collections.remove(self.sc)

                # draw new scatterplot
                lb = value - self.inc
                ub = value
                Vm = np.ma.array(self.Vf)
                Vm = np.ma.masked_where(Vm < lb, Vm)
                Vm = np.ma.masked_where(Vm > ub, Vm)
                cval = ub
                ii = np.where(np.ma.getmask(Vm) == False)
                cval = self.scalarMap.to_rgba(ub)
                if ii:
                    self.sc = self.ax.scatter3D(
                        self.Xf[ii], self.Yf[ii], self.Zf[ii], color=cval
                    )
                    self.ax.set_xlim3d(self.xmin, self.xmax)
                    self.ax.set_ylim3d(self.ymin, self.ymax)
                    self.ax.set_zlim3d(self.zmin, self.zmax)

            def show(self):
                plt.show()

        p = ChangingPlot()
        p.show()

    @staticmethod
    def plotRSvalidate(dat, figtitle, title, xlabel, ylabel, error_tol_percent=10):

        # show +/- 10% around true values on the predicted vs. actual plot
        show_envelope = True

        # process data
        err = dat[:, 0]
        truth = dat[:, 1]
        est = dat[:, 2]
        std = dat[:, 3]

        # plot
        fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)
        fig.canvas.manager.set_window_title(figtitle)

        # ... plot CV error histogram
        nbins = 10
        bheights, bedges = np.histogram(err, nbins)
        w = np.diff(bedges)
        ax1.bar(bedges[:-1], bheights, width=w, color="c", alpha=1, edgecolor="k")
        ax1.set_xlabel(xlabel[0])
        ax1.xaxis.grid(True)
        ax1.set_ylabel(ylabel[0])
        ax1.yaxis.grid(True)
        ax1.set_title(title[0])
        ax1.autoscale(enable=True, axis="x", tight=True)
        err_mu = np.mean(err)
        err_sigma = np.std(err)
        dummy = Plotter.emptypatch()
        if useFrameAlpha:
            ax1.legend(
                [dummy, dummy],
                ["Error mean: %f" % err_mu, "Error std dev: %f" % err_sigma],
                loc=0,
                framealpha=0.8,
            )
        else:
            ax1.legend(
                [dummy, dummy],
                ["Error mean: %f" % err_mu, "Error std dev: %f" % err_sigma],
                loc=0,
            )

        # ... plot actual vs. estimate
        minval = min(truth)
        maxval = max(truth)
        diag_label = "Estimate = Actual"
        (diag_plot,) = ax2.plot(
            [minval, maxval], [minval, maxval], color="k", label=diag_label
        )

        if show_envelope:
            error_tol = error_tol_percent * 0.01
            env_label = "Actual +/- " + str(error_tol_percent) + "%"
            minTruth = min(truth)
            maxTruth = max(truth)
            numPoints = 10
            sparseTruth = [
                minTruth + r / numPoints * (maxTruth - minTruth)
                for r in range(numPoints + 1)
            ]
            under = [(1 - error_tol) * t for t in sparseTruth]
            over = [(1 + error_tol) * t for t in sparseTruth]
            (under_plot,) = ax2.plot(
                sparseTruth, under, color="g", linestyle=":", label=env_label
            )
            (_over_plot,) = ax2.plot(
                sparseTruth, over, color="g", linestyle=":", label=env_label
            )
        errbar_label = "Estimate +/- 1 std dev"
        errbar_plot = ax2.errorbar(
            truth,
            est,
            yerr=std,
            color="b",
            fmt="o",
            ecolor="r",
            capthick=2,
            label=errbar_label,
        )
        ax2.set_xlabel(xlabel[1])
        ax2.xaxis.grid(True)
        ax2.set_ylabel(ylabel[1])
        ax2.yaxis.grid(True)
        ax2.set_title(title[1])
        ax2.autoscale(enable=True, axis="x", tight=True)
        if useFrameAlpha:
            ax2.legend(
                [diag_plot, errbar_plot, under_plot],
                [diag_label, errbar_label, env_label],
                numpoints=1,
                loc=0,
                framealpha=0.8,
            )
        else:
            ax2.legend(
                [diag_plot, errbar_plot, under_plot],
                [diag_label, errbar_label, env_label],
                numpoints=1,
                loc=0,
            )

        plt.tight_layout()
        plt.show()

    @staticmethod
    def plotinf(
        xdat,
        ydat,
        zdat,
        figtitle,
        title,
        xlabel,
        ylabel,
        subplot_indices,
        xlim,
        ylim,
        zlim,
        lastplot=True,
    ):

        from scipy import interpolate

        N = len(subplot_indices)
        opacity = 1  # opacity of bars (1 being completely opaque)
        p = 0  # subplot index

        # check if there are multiple plots to generate
        if N > 1:

            # customize
            show_cbar = False  # impose global colormap and show colorbar
            same_yscale = False  # impose same y-scaling for diagonal subplots

            # set up colors
            cmap = "jet"
            if show_cbar:
                zmin, zmax = zlim
                norm_global = colors.Normalize(vmin=zmin, vmax=zmax)

            # generate subplots
            sbi = subplot_indices[
                subplot_indices > 0
            ]  # the upper-triangular elements are positive
            fig, axes = plt.subplots(nrows=N, ncols=N)
            # This is the source of slow plots. Not sure if this can be sped up
            A = axes.flat

            for i in range(1, N + 1):
                k = sbi[p]
                ax = A[k - 1]
                # ... plot histogram for diagonal subplot
                x = xdat[p]
                z = zdat[p]
                w = x[1] - x[0]
                ax.bar(
                    x,
                    z,
                    color="g",
                    width=w,
                    align="center",
                    alpha=opacity,
                    edgecolor="k",
                )
                xmin = x[0]
                xmax = x[-1]
                ax.set_xlim(xlim[p])
                if same_yscale:
                    ax.set_ylim(ylim[p])
                ax.set_xlabel(xlabel[p])
                ax.set_ylabel(ylabel[p])
                ax.xaxis.grid(True)
                ax.yaxis.grid(True)
                labels = ax.get_xticklabels()
                for label in labels:  # rotate the xtick labels to avoid bunching
                    label.set_rotation(90)
                p = p + 1

                for j in range(1, i):
                    # ... delete the unused (lower-triangular) axes
                    k = (i - 1) * N + j
                    ax = A[k - 1]
                    fig.delaxes(ax)

                for j in range(i + 1, N + 1):
                    k = sbi[p]
                    ax = A[k - 1]
                    # ... plot 2D heatmap for upper-triangular subplot
                    y = ydat[p]
                    z = zdat[p]
                    ymin = y[0]
                    ymax = y[-1]
                    xx, yy = np.meshgrid(x, y)
                    xnew, ynew = np.mgrid[xmin:xmax:101j, ymin:ymax:101j]
                    tck = interpolate.bisplrep(xx, yy, z)  # spline parameters
                    znew = interpolate.bisplev(xnew[:, 0], ynew[0, :], tck)
                    # ...... display heatmap such that x variable is on y-axis
                    if show_cbar:  # use global colormap for each off-diagonal subplots
                        ax.pcolormesh(ynew, xnew, znew, cmap=cmap, norm=norm_global)
                    else:  # use local colormap for each off-diagonal subplots
                        znewf = znew.flatten()
                        norm_local = colors.Normalize(vmin=min(znewf), vmax=max(znewf))
                        ax.pcolormesh(ynew, xnew, znew, cmap=cmap, norm=norm_local)

                    ax.set_xlim(xlim[p])
                    ax.set_ylim(ylim[p])
                    ax.set_xlabel(xlabel[p])
                    ax.set_ylabel(ylabel[p])
                    labels = ax.get_xticklabels()
                    for label in labels:  # rotate the xtick labels to avoid bunching
                        label.set_rotation(90)
                    p = p + 1

            # ... set up colorbar
            if show_cbar:
                left = 0.925
                bottom = 0.1
                width = 0.03
                height = 0.8
                cbax = fig.add_axes([left, bottom, width, height])
                fig.colorbar = mpl.colorbar.ColorbarBase(
                    cbax, cmap=cmap, norm=norm_global
                )
                plt.subplots_adjust(
                    wspace=0.6,
                    hspace=0.6,
                    bottom=0.1,
                    top=0.9,
                    left=0.1,
                    right=left - 0.02,
                )

            # ... add subplot zooming
            fig.canvas.mpl_connect("button_press_event", Plotter.on_click)

        else:

            # generate single plot
            fig = plt.figure()
            ax = fig.add_subplot(111)
            # ... plot histogram for diagonal subplot
            x = xdat[p]
            z = zdat[p]
            w = x[1] - x[0]
            ax.bar(
                x, z, color="g", width=w, align="center", alpha=opacity, edgecolor="k"
            )
            xmin = x[0]
            xmax = x[-1]
            ax.set_xlim(xlim[p])
            ax.set_xlabel(xlabel[p])
            ax.set_ylabel(ylabel[p])
            ax.xaxis.grid(True)
            ax.yaxis.grid(True)
            labels = ax.get_xticklabels()
            for label in labels:  # rotate the xtick labels to avoid bunching
                label.set_rotation(90)

        fig.suptitle(title)
        fig.canvas.manager.set_window_title(figtitle)
        #       plt.tight_layout()

        if lastplot:
            plt.show()

    @staticmethod
    def on_click(event):
        # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
        # Subplot zoom code adapted from
        # http://stackoverflow.com/questions/9012081/matplotlib-grab-single-subplot-from-multiple-subplots
        # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
        ax = event.inaxes

        try:
            ax.get_geometry()
        except AttributeError:
            return  # the selected axis (e.g., colorbar) does not have geometry attribute

        if event.button == 1:
            # On left click, zoom in
            axlist = event.canvas.figure.axes
            # if any one of the subplots are already zoomed in, ignore
            for axis in axlist:
                try:
                    if axis.get_geometry() == (1, 1, 1):
                        return
                except AttributeError:
                    pass  # ignore axes without geometry attribute

            # otherwise, zoom the selected axes
            if ax.get_geometry() != (1, 1, 1):
                ax._geometry = ax.get_geometry()
                ax.change_geometry(1, 1, 1)
                for axis in event.canvas.figure.axes:
                    # hide all the other axes...
                    if axis is not ax:
                        axis.set_visible(False)

        elif event.button == 3:
            # On right click, restore the axes
            if ax.get_geometry() == (1, 1, 1):
                nrows, ncols, num = ax._geometry
                ax.change_geometry(nrows, ncols, num)
                for axis in event.canvas.figure.axes:
                    axis.set_visible(True)
            else:
                return  # no subplots to unzoom, so return
        else:
            # no need to re-draw the canvas if it's not a left or right click
            return

        event.canvas.draw()
