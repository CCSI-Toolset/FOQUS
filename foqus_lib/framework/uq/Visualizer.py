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
import os
import subprocess
import tempfile
import re
import platform
import numpy as np
from .Model import Model
from .SampleData import SampleData
from .LocalExecutionModule import LocalExecutionModule
from .Common import Common
from .Plotter import Plotter


class Visualizer:

    dname = os.getcwd() + os.path.sep + "Visualizer_files"

    @staticmethod
    def xScatter(fname, x, cmd, star=None):

        # star is 0-indexed and refers to the indices of x that will use the * marker

        # read data
        data = LocalExecutionModule.readSampleFromPsuadeFile(fname)

        # check if selected inputs are valid
        nInputs = data.getNumInputs()
        validInputs = set(x).issubset(range(1, nInputs + 1))
        if not validInputs:
            error = "Visualizer: In function xScatter(), x is out of range for valid inputs."
            Common.showError(error)
            return None

        # get input names
        inVarNames = data.getInputNames()

        types = data.getInputTypes()
        variableIndices = []
        for i in range(len(types)):
            if types[i] == Model.VARIABLE:
                variableIndices.append(i + 1)

        mfiles = []
        datvar = "X"

        if cmd == "iplot1":
            xdat = []
            ydat = []
            ptitle = []
            ylabel = []

            mfileRoot = "matlabiplt1"
            mfile = mfileRoot + ".m"
            for i in x:
                # write script
                f = tempfile.SpooledTemporaryFile(mode="wt")
                if platform.system() == "Windows":
                    import win32api

                    fname = win32api.GetShortPathName(fname)
                f.write("load %s\n" % fname)
                f.write("%s\n" % cmd)
                f.write("%d\n" % (variableIndices.index(i) + 1))  # select input
                f.write("quit\n")
                f.seek(0)

                # invoke psuade
                out, error = Common.invokePsuade(f)
                f.close()

                # process error
                if error:
                    return None

                # check output file
                if os.path.exists(mfile):
                    suffix = "_x%d.m" % i
                    mfile_ = Visualizer.dname + os.path.sep + mfileRoot + suffix
                    os.rename(mfile, mfile_)
                    mfiles.append(mfile_)
                else:
                    error = "Visualizer: %s does not exist." % mfile
                    Common.showError(error, out)
                    return None

                # plot
                inVarName = inVarNames[i - 1]
                y = Plotter.getdata(mfile_, datvar)
                y = y[:, 0]
                ydat.append(y)
                sampleIndices = list(range(1, len(y) + 1))
                xdat.append(sampleIndices)
                ptitle.append("Scatter Plot of %s" % inVarName)
                ylabel.append(inVarName)

            nx = len(x)
            xlabel = ["Sample Number"] * nx
            ylim = None
            ftitle = "1-Input Scatter Plot"

        elif cmd == "iplot2":
            if len(x) == 2:
                x1 = x[0]
                x2 = x[1]
                if x1 == x2:
                    error = (
                        "Visualizer: In function xScatter(), %s requires unique elements in x."
                        % cmd.upper()
                    )
                    Common.showError(error)
                    return None
            else:
                error = (
                    "Visualizer: In function xScatter(), %s expects x to be a list of length 2."
                    % cmd.upper()
                )
                Common.showError(error)
                return None

            # write script
            f = tempfile.SpooledTemporaryFile(mode="wt")
            if platform.system() == "Windows":
                import win32api

                fname = win32api.GetShortPathName(fname)
            f.write("load %s\n" % fname)
            f.write("%s\n" % cmd)
            f.write("%d\n" % (variableIndices.index(x1) + 1))  # select input
            f.write("%d\n" % (variableIndices.index(x2) + 1))  # select input
            f.write("quit\n")
            f.seek(0)

            # invoke psuade
            out, error = Common.invokePsuade(f)
            f.close()

            # process error
            if error:
                return None

            # check output file
            mfileRoot = "matlabiplt2"
            mfile = mfileRoot + ".m"
            if os.path.exists(mfile):
                suffix = "_x%d_x%d.m" % (x1, x2)
                mfile_ = Visualizer.dname + os.path.sep + mfileRoot + suffix
                os.rename(mfile, mfile_)
                mfiles.append(mfile_)
            else:
                error = "Visualizer: %s does not exist." % mfile
                Common.showError(error, out)
                return None

            # plot
            dat = Plotter.getdata(mfile_, datvar)
            xdat = [dat[:, 0]]
            ydat = [dat[:, 1]]
            xlabel = inVarNames[x1 - 1]
            ylabel = inVarNames[x2 - 1]
            ptitle = ["Scatter Plot of %s vs. %s" % (ylabel, xlabel)]
            xlabel = [xlabel]
            ylabel = [ylabel]
            ftitle = "2-Input Scatter Plot"

        ylim = None
        xdat = np.array(xdat)
        ydat = np.array(ydat)
        Plotter.plotscatter(xdat, ydat, ftitle, ptitle, xlabel, ylabel, ylim, star)

        return mfiles

    @staticmethod
    def yScatter(fname, y, x, cmd):
        # x is 1-indexed

        # read data
        data = LocalExecutionModule.readSampleFromPsuadeFile(fname)
        nInputs = SampleData.getNumInputs(data)

        types = data.getInputTypes()
        variableIndices = []
        for i in range(len(types)):
            if types[i] == Model.VARIABLE:
                variableIndices.append(i + 1)

        # process user arguments
        if cmd == "splot":
            validInputs = set(x).issubset(range(1, nInputs + 1))
            if not validInputs:
                error = "Visualizer: In function yScatter(), x is out of range for valid inputs."
                Common.showError(error)
                return None
        elif cmd == "splot2":
            if len(x) == 2:
                x1 = x[0]
                x2 = x[1]
                if x1 == x2:
                    error = (
                        "Visualizer: In function yScatter(), %s requires unique elements in x."
                        % cmd.upper()
                    )
                    Common.showError(error)
                    return None
            else:
                error = (
                    "Visualizer: In function yScatter(), %s expects x to be a list of length 2."
                    % cmd.upper()
                )
                Common.showError(error)
                return None

        # write script
        f = tempfile.SpooledTemporaryFile(mode="wt")
        if platform.system() == "Windows":
            import win32api

            fname = win32api.GetShortPathName(fname)
        f.write("load %s\n" % fname)
        f.write("%s\n" % cmd)
        if cmd == "splot2":
            f.write("%d\n" % (variableIndices.index(x1) + 1))  # select input
            f.write("%d\n" % (variableIndices.index(x2) + 1))  # select input
        f.write("%d\n" % y)  # select output
        f.write("quit\n")
        f.seek(0)

        # invoke psuade
        out, error = Common.invokePsuade(f)
        f.close()

        # process error
        if error:
            return None

        # check output file
        outfile = {"splot": "matlabsp.m", "splot2": "matlabsp2.m"}
        mfile = outfile[cmd]
        if os.path.exists(mfile):
            mfile_ = Visualizer.dname + os.path.sep + mfile
            os.rename(mfile, mfile_)
            mfile = mfile_
        else:
            error = "Visualizer: %s does not exist." % mfile
            Common.showError(error, out)
            return None

        Visualizer.yScatterPlot(data, y, x, cmd, mfile)

        return mfile

    @staticmethod
    def yScatterPlot(data, y, x, cmd, mfile):
        types = data.getInputTypes()
        variableIndices = []
        for i in range(len(types)):
            if types[i] == Model.VARIABLE:
                variableIndices.append(i + 1)

        # plot
        inVarNames = SampleData.getInputNames(data)
        outVarNames = SampleData.getOutputNames(data)
        outVarName = outVarNames[y - 1]
        if cmd == "splot":
            ftitle = '"1-Input to 1-Output" Scatter Plot of %s' % outVarName
            xdat = []
            xlabel = []
            ptitle = []
            for i in x:
                datvar = "X%d" % (variableIndices.index(i) + 1)
                xdat.append(Plotter.getdata(mfile, datvar))
                inVarName = inVarNames[i - 1]
                xlabel.append(inVarName)
                ptitle.append("%s vs. %s" % (outVarName, inVarName))
            nx = len(x)
            xdat = np.array(xdat)
            datvar = "Y"
            y = Plotter.getdata(mfile, datvar)
            ylim = [min(y), max(y)]
            ydat = [y] * nx
            ydat = np.array(ydat)
            ylabel = [outVarName] * nx
            Plotter.plotscatter(xdat, ydat, ftitle, ptitle, xlabel, ylabel, ylim)
        elif cmd == "splot2":
            datvar = "X"
            dat = Plotter.getdata(mfile, datvar)
            xdat = dat[:, 0]
            ydat = dat[:, 1]
            zdat = dat[:, 2]
            ftitle = '"2-Input to 1-Output" Scatter Plot of %s' % outVarName
            x1 = x[0]
            x2 = x[1]
            xlabel = inVarNames[x1 - 1]
            ylabel = inVarNames[x2 - 1]
            zlabel = outVarName
            ptitle = "%s vs. (%s, %s)" % (zlabel, xlabel, ylabel)
            Plotter.plotscatter3d(
                xdat, ydat, zdat, ftitle, ptitle, xlabel, ylabel, zlabel
            )

    @staticmethod
    def maskdata(v, vmin, vmax):

        vm = np.ma.array(v)
        vm = np.ma.masked_where(vm < vmin, vm)  # mask data below min value
        vm = np.ma.masked_where(vm > vmax, vm)  # mask data above max value

        if vm.mask.all():  # if all values are masked (i.e., no valid data)
            error = (
                "Visualizer: Data lies within [%f, %f] (outside of specified range [%f, %f])."
                % (min(v), max(v), vmin, vmax)
            )
            Common.showError(error)
            vm = None

        return vm

    @staticmethod
    def showRS(fnameRS, y, x, rsdim, rsMethodName, **kwargs):

        from .ResponseSurfaces import ResponseSurfaces

        # read data
        data = LocalExecutionModule.readSampleFromPsuadeFile(
            fnameRS
        )  # rstype/order written to data
        nSamples = SampleData.getNumSamples(data)
        order = SampleData.getLegendreOrder(data)

        types = data.getInputTypes()
        inputNames = data.getInputNames()
        variableIndices = []
        variableNames = []
        for i in range(len(types)):
            if types[i] == Model.VARIABLE:
                variableIndices.append(i + 1)
                variableNames.append(inputNames[i])

        rsIndex = ResponseSurfaces.getEnumValue(rsMethodName)

        # process keyworded arguments
        vmax = np.inf
        vmin = -vmax
        userRegressionFile = None
        setMARS = False
        for key in kwargs:
            k = key.lower()
            if k == "rsoptions":
                rsOptions = kwargs[key]
                if rsIndex == ResponseSurfaces.LEGENDRE:
                    if rsOptions is None:
                        error = 'Visualizer: In function showRS(), "legendreOrder" is required for LEGENDRE response surface.'
                        Common.showError(error)
                        return None
                    else:
                        if isinstance(rsOptions, dict):
                            legendreOrder = rsOptions["legendreOrder"]
                        else:
                            legendreOrder = rsOptions
                        if type(legendreOrder) == int:
                            order = legendreOrder
                        else:
                            error = 'Visualizer: In function showRS(), "legendreOrder" is required for LEGENDRE response surface.'
                            Common.showError(error)
                            return None
                elif rsIndex in [
                    ResponseSurfaces.MARS,
                    ResponseSurfaces.MARSBAG,
                ]:  # check for MARS options
                    if rsOptions is not None:
                        from .RSAnalyzer import RSAnalyzer

                        marsOptions = RSAnalyzer.checkMARS(data, rsOptions)
                        if marsOptions is not None:
                            marsBases, marsInteractions, marsNormOutputs = marsOptions
                            setMARS = True
            elif k == "vmin":
                vmin = kwargs[key]
            elif k == "vmax":
                vmax = kwargs[key]
            elif k == "userregressionfile":
                userRegressionFile = kwargs[key]

        # check user arguments
        if rsdim < 1 or rsdim > 3:
            error = "Visualizer: showRS() supports only rs1, rs2 and rs3."
            Common.showError(error)
            return None
        nx = len(x)
        if nx != rsdim:
            error = "Visualizer: showRS() expects x to be a list of length %d." % rsdim
            Common.showError(error)
            return None
        uniqx = list(set(x))
        if nx != len(uniqx):
            error = "Visualizer: showRS() expects unique elements in x."
            Common.showError(error)
            return None
        if vmin >= vmax:
            error = "Visualizer: showRS() requires vmin to be less than vmax."
            Common.showError(error)
            return None

        # write script
        cmd = "rs%d" % rsdim
        f = tempfile.SpooledTemporaryFile(mode="wt")
        if setMARS:
            f.write("rs_expert\n")
        if platform.system() == "Windows":
            import win32api

            fnameRS = win32api.GetShortPathName(fnameRS)
        f.write("load %s\n" % fnameRS)
        if nSamples > 4000:
            f.write("rsmax %d\n" % nSamples)
        f.write("%s\n" % cmd)
        ngrid = 0
        if rsdim == 2:
            ngrid = 256  # select grid resolution (32-256)
            f.write("%d\n" % ngrid)
        elif rsdim == 3:
            ngrid = 32  # select grid resolution (16-32)
            f.write("%d\n" % ngrid)
        f.write("%d\n" % rsIndex)  # select response surface
        if rsIndex == ResponseSurfaces.USER and userRegressionFile is not None:
            f.write("1\n")  # number of basis functions
            f.write("%s\n" % userRegressionFile)  # surrogate file
            f.write("y\n")  # apply auxillary arg (output index)
            outVarNames = data.getOutputNames()
            outName = outVarNames[y - 1]
            outName = Common.getUserRegressionOutputName(
                outName, userRegressionFile, data
            )
            f.write("%s\n" % outName)  # output name
        elif setMARS:
            if rsIndex == ResponseSurfaces.MARSBAG:
                f.write("0\n")  # mean (0) or median (1) mode
                f.write(
                    "100\n"
                )  # number of MARS instantiations [range:10-5000, default=100]
                ### TO DO: revert back to 100 for deployment
            f.write("%d\n" % marsBases)
            f.write("%d\n" % marsInteractions)
            if rsIndex == ResponseSurfaces.MARS:
                f.write("%s\n" % marsNormOutputs)
        nInputs = SampleData.getNumInputs(data)
        if nInputs > rsdim:
            for d in range(0, rsdim):
                # f.write('%d\n' % (variableIndices.index(x[d]) + 1))   # select input
                f.write("%d\n" % (variableNames.index(x[d]) + 1))  # select input
            f.write("y\n")  # set nominal values for other inputs
        elif nInputs == rsdim:
            for d in range(0, rsdim - 1):  # psuade can infer last remaining input
                # f.write('%d\n' % (variableIndices.index(x[d]) + 1))   # select input
                f.write("%d\n" % (variableNames.index(x[d]) + 1))  # select input
        elif nInputs < rsdim:
            error = (
                "Visualizer: In showRS(), %s cannot be performed on a %d-input system."
                % (cmd.upper(), nInputs)
            )
            Common.showError(error)
            return None
        f.write("%d\n" % y)  # select output
        if rsIndex == ResponseSurfaces.LEGENDRE:
            f.write("%d\n" % order)
        f.write("n\n")  # select no for selecting lower threshold
        f.write("n\n")  # select no for selecting upper threshold
        f.write("quit\n")
        f.seek(0)

        # print the psuade script to screen
        # for line in f:
        #    print line.strip()
        # f.seek(0)

        # invoke psuade
        out, error = Common.invokePsuade(f)
        f.close()

        # process error
        if error:
            return None

        # check output file
        mfile = "matlab" + cmd + ".m"
        if os.path.exists(mfile):
            mfile_ = Visualizer.dname + os.path.sep + mfile
            os.rename(mfile, mfile_)
            mfile = mfile_
        else:
            error = "Visualizer: %s does not exist." % mfile
            Common.showError(error, out)
            return None

        Visualizer.showRSPlot(data, y, x, rsdim, ngrid, rsMethodName, vmin, vmax, mfile)
        return mfile

    @staticmethod
    def showRSPlot(data, y, x, rsdim, ngrid, rsMethodName, vmin, vmax, mfile):
        import math

        inVarNames = data.getInputNames()
        outVarNames = data.getOutputNames()
        outVarName = outVarNames[y - 1]
        if rsdim == 1:
            xdat = Plotter.getdata(mfile, "X")
            ydat = Plotter.getdata(mfile, "A")
            ydatm = Visualizer.maskdata(ydat, vmin, vmax)
            if ydatm is None:
                error = (
                    'Visualizer: In function showRS(), the output "%s" has no points within [%f, %f].'
                    % (outVarName, vmin, vmax)
                )
                Common.showError(error)
                return None
            # xlabel = inVarNames[x[0] - 1]
            xlabel = x[0]
            ylabel = outVarName
            ftitle = (
                '"1-Input to 1-Output" Visualization of %s Response Surface'
                % rsMethodName.upper()
            )
            ptitle = 'Line Plot of "%s = %s(%s)"' % (
                ylabel,
                rsMethodName.upper(),
                xlabel,
            )
            Plotter.plotline(xdat, ydatm, ftitle, ptitle, xlabel, ylabel)
        elif rsdim == 2:
            xdat = Plotter.getdata(mfile, "x")
            ydat = Plotter.getdata(mfile, "y")
            xmesh, ymesh = np.meshgrid(xdat, ydat)
            zdat = Plotter.getdata(mfile, "A")
            zdatm = Visualizer.maskdata(zdat, vmin, vmax)
            if zdatm is None:
                error = (
                    'Visualizer: In function showRS(), the output "%s" has no points within [%f, %f].'
                    % (outVarName, vmin, vmax)
                )
                Common.showError(error)
                return None
            L = len(zdat)
            M = int(math.sqrt(L))
            zdatm = np.reshape(zdatm, [M, M], order="F")
            # xlabel = inVarNames[x[0] - 1]
            # ylabel = inVarNames[x[1] - 1]
            xlabel = x[0]
            ylabel = x[1]
            zlabel = outVarName
            ftitle = (
                '"2-Input to 1-Output" Visualization of %s Response Surface'
                % rsMethodName.upper()
            )
            ptitle = 'Surface/Contour Plots of "%s = %s(%s, %s)"' % (
                zlabel,
                rsMethodName.upper(),
                xlabel,
                ylabel,
            )
            Plotter.plotisoline(
                xmesh, ymesh, zdatm, ftitle, ptitle, xlabel, ylabel, zlabel
            )
        elif rsdim == 3:
            xdat = []
            ydat = []
            zdat = []
            vdat = []
            for g in range(1, ngrid + 1):
                xdat.append(Plotter.getdata(mfile, "X\(:,:,%d\)" % g))
                ydat.append(Plotter.getdata(mfile, "Y\(:,:,%d\)" % g))
                zdat.append(Plotter.getdata(mfile, "Z\(:,:,%d\)" % g))
                vdat.append(Plotter.getdata(mfile, "V\(:,:,%d\)" % g))
            vdatm = Visualizer.maskdata(vdat, vmin, vmax)
            if vdatm is None:
                error = (
                    'Visualizer: In function showRS(), the output "%s" has no points within [%f, %f].'
                    % (outVarName, vmin, vmax)
                )
                Common.showError(error)
                return None
            # xlabel = inVarNames[x[0] - 1]
            # ylabel = inVarNames[x[1] - 1]
            # zlabel = inVarNames[x[2] - 1]
            xlabel = x[0]
            ylabel = x[1]
            zlabel = x[2]
            vlabel = outVarName
            ftitle = (
                '"3-Input to 1-Output" Visualization of %s Response Surface'
                % rsMethodName.upper()
            )
            ptitle = 'Isosurface Plot of "%s = %s(%s, %s, %s)"' % (
                vlabel,
                rsMethodName.upper(),
                xlabel,
                ylabel,
                zlabel,
            )
            # Chares (Feb/2017): This call seems to confusion between X and Y
            #                   axis label, so it is switched here (the bug
            #                   must be in Plotter.
            # Plotter.plotisosurface(np.array(xdat),np.array(ydat),np.array(zdat),                        vdatm,ftitle,ptitle,xlabel,ylabel,zlabel,vlabel)
            Plotter.plotisosurface(
                np.array(xdat),
                np.array(ydat),
                np.array(zdat),
                vdatm,
                ftitle,
                ptitle,
                ylabel,
                xlabel,
                zlabel,
                vlabel,
            )
