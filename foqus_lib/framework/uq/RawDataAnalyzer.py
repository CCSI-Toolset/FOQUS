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
import platform
from .Model import Model
from .SampleData import SampleData
from .Common import Common
from .LocalExecutionModule import LocalExecutionModule
from .Plotter import Plotter


class RawDataAnalyzer:

    dname = os.getcwd() + os.path.sep + "RawDataAnalyzer_files"

    @staticmethod
    def screenInputs(fname, y, cmd):

        # read data
        data = LocalExecutionModule.readSampleFromPsuadeFile(fname)

        # write script
        f = tempfile.SpooledTemporaryFile(mode="wt")
        if platform.system() == "Windows":
            import win32api

            fname = win32api.GetShortPathName(fname)
        f.write("load %s\n" % fname)
        f.write("%s\n" % cmd)
        f.write("%d\n" % y)  # select output
        if cmd == "gp_sa":
            f.write(
                "3\n"
            )  # 1 for MacKay's Tpros, 2 for Rasmussen's gp-mc, 3 for kriging
        elif cmd == "moat":
            f.write("n\n")  # select no to generate screening diagram
            f.write("n\n")  # select no to generate scatter plot
            f.write("y\n")  # select yes to generate bootstrap mean plot
        elif cmd == "mars_sa":
            f.write("0\n")  # 0 for MARS or 1 for MARS with bagging
        f.write("quit\n")
        f.seek(0)

        # invoke psuade
        out, error = Common.invokePsuade(f)
        f.close()

        # process error
        if error:
            return None

        # check output file
        outfile = {
            "moat": "matlabmoatbs.m",
            "delta_test": "matlabdelta.m",
            "sot_sa": "matlabsot.m",
            "mars_sa": "matlabmarsa.m",
            "gp_sa": "matlabkrisa.m",
            "lsa": "matlablsa.m",
        }
        mfile = outfile[cmd]
        if os.path.exists(mfile):
            mfile_ = RawDataAnalyzer.dname + os.path.sep + mfile
            os.rename(mfile, mfile_)
            mfile = mfile_
        else:
            error = "RawDataAnalyzer: %s does not exist." % mfile
            Common.showError(error, out)
            return None

        RawDataAnalyzer.plotScreenInputs(data, cmd, y, mfile)
        return mfile

    @staticmethod
    def plotScreenInputs(data, cmd, y, mfile):
        # plot
        datvar = {
            "moat": ["Means", "Stds"],
            "delta_test": "A",
            "sot_sa": "A",
            "mars_sa": "Y",
            "gp_sa": "Y",
            "lsa": "Y",
        }
        figtitle = {
            "moat": "MORRIS",
            "delta_test": "DELTA",
            "sot_sa": "SUM-OF-TREES",
            "mars_sa": "MARS",
            "gp_sa": "KRIGING",
            "lsa": "LOCAL SUM-OF-TREES",
        }
        title = {
            "moat": "Modified Means Plot (Bootstrap)",
            "delta_test": "Delta Test Rankings",
            "sot_sa": "Sum-of-trees Rankings",
            "mars_sa": "MARS Rankings",
            "gp_sa": "Kriging Rankings",
            "lsa": "Local Sensitivity Rankings",
        }
        ylabel = {
            "moat": "Modified Means (of gradients)",
            "delta_test": "Delta Metric (normalized)",
            "sot_sa": "Sum-of-trees Metric (normalized)",
            "mars_sa": "MARS Measure",
            "gp_sa": "Kriging Measure",
            "lsa": "Sensitivity Measure",
        }
        xlabel = "Input Parameters"
        xticklabels = []
        inputNames = data.getInputNames()
        inputTypes = data.getInputTypes()
        for name, inType in zip(inputNames, inputTypes):
            if inType == Model.VARIABLE:
                xticklabels.append(name)
        if cmd == "moat":
            dat = Plotter.getdata(mfile, datvar[cmd][0])
            std = Plotter.getdata(mfile, datvar[cmd][1])
        else:
            dat = Plotter.getdata(mfile, datvar[cmd])
            std = None
        outVarNames = data.getOutputNames()
        outVarName = outVarNames[y - 1]
        ftitle = "%s Parameter Screening Rankings" % figtitle[cmd]
        ptitle = "%s for %s" % (title[cmd], outVarName)
        Plotter.plotbar(
            dat, std, ftitle, ptitle, xlabel, ylabel[cmd], xticklabels, barlabels=True
        )

    @staticmethod
    def performUA(fname, y, **kwargs):

        import re

        # process keyworded arguments
        rs = None
        for key in kwargs:
            k = key.lower()
            if k == "rsmethod":
                rs = kwargs[key]

        # read data
        data = LocalExecutionModule.readSampleFromPsuadeFile(fname)

        # write script
        cmd = "ua"
        f = tempfile.SpooledTemporaryFile(mode="wt")
        if platform.system() == "Windows":
            import win32api

            fname = win32api.GetShortPathName(fname)
        f.write("load %s\n" % fname)
        f.write("%s\n" % cmd)
        f.write("%d\n" % y)  # select output
        f.write("quit\n")
        f.seek(0)

        # invoke psuade
        out, error = Common.invokePsuade(f)
        f.close()

        # process error
        if error:
            return None

        # parse output for moment info
        mres = []
        mstr = [
            r"Sample mean\s*=\s*(\S*)",
            r"Sample std dev\s*=\s*(\S*)",
            r"Sample skewness\s*=\s*(\S*)",
            r"Sample kurtosis\s*=\s*(\S*)",
        ]
        for m in mstr:
            regex = re.findall(m, out)
            if regex:
                mres.append(regex[0])
            else:
                mres.append("")
        moments = None
        if len(mres) == 4:
            moments = {
                "mean": mres[0],
                "std": mres[1],
                "skew": mres[2],
                "kurt": mres[3],
            }

        # check output file
        mfile = "matlab" + cmd + ".m"
        if os.path.exists(mfile):
            mfile_ = RawDataAnalyzer.dname + os.path.sep + mfile
            os.rename(mfile, mfile_)
            mfile = mfile_
        else:
            error = "RawDataAnalyzer: %s does not exist." % mfile
            Common.showError(error, out)
            return None

        RawDataAnalyzer.plotUA(data, y, mfile, moments)

        return (mfile, moments)

    @staticmethod
    def plotUA(data, y, mfile, moments):
        # plot
        outVarNames = SampleData.getOutputNames(data)
        outVarName = outVarNames[y - 1]
        datvar = "Y"
        dat = Plotter.getdata(mfile, datvar)
        ftitle = "Uncertainty Analysis on Ensemble Data"
        ptitle = "Probability Distribution for %s" % outVarName
        xlabel = outVarName
        ylabel = "Probabilities"
        ystd = None
        rsPDF = None
        Plotter.plothist(dat, moments, ftitle, ptitle, xlabel, ylabel)

    @staticmethod
    def performCA(fname, y):

        # read data
        data = LocalExecutionModule.readSampleFromPsuadeFile(fname)

        # write script
        cmd = "ca"
        f = tempfile.SpooledTemporaryFile(mode="wt")
        if platform.system() == "Windows":
            import win32api

            fname = win32api.GetShortPathName(fname)
        f.write("load %s\n" % fname)
        f.write("%s\n" % cmd)
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
        mfile = "matlab" + cmd + ".m"
        if os.path.exists(mfile):
            mfile_ = RawDataAnalyzer.dname + os.path.sep + mfile
            os.rename(mfile, mfile_)
            mfile = mfile_
        else:
            error = "RawDataAnalyzer: %s does not exist." % mfile
            Common.showError(error, out)
            return None
        if os.stat(mfile).st_size == 0:  # matlabca.m can be empty if segfault occurs
            error = "RawDataAnalyzer: %s is an empty file." % mfile
            Common.showError(error, out)
            return None

        RawDataAnalyzer.plotCA(data, y, mfile)
        return mfile

    @staticmethod
    def plotCA(data, y, mfile):
        # plot
        outVarNames = SampleData.getOutputNames(data)
        outVarName = outVarNames[y - 1]
        ftitle = "Correlation Analysis on Ensemble Data"
        ptitle = "Correlation Analysis for %s" % outVarName
        xlabel = "Input Parameters"
        xticklabels = []
        inputNames = data.getInputNames()
        inputTypes = data.getInputTypes()
        for name, inType in zip(inputNames, inputTypes):
            if inType == Model.VARIABLE:
                xticklabels.append(name)
        ylabel = "Correlation Coefficients"
        ylabel = ["Pearson " + ylabel, "Spearman " + ylabel]
        dat_pcc = Plotter.getdata(mfile, "PCC")
        dat_scc = Plotter.getdata(mfile, "SPEA")
        dat = [dat_pcc, dat_scc]
        std = [None] * len(dat)
        Plotter.plotbar(
            dat, std, ftitle, ptitle, xlabel, ylabel, xticklabels, barlabels=True
        )

    @staticmethod
    def performSA(fname, y, cmd):

        # read data
        data = LocalExecutionModule.readSampleFromPsuadeFile(fname)

        # check sample size
        nSamples = SampleData.getNumSamples(data)
        nSamplesLB = {
            "me": 1000,  # lower bound on number of samples
            "ie": 1000,
            "tsi": 10000,
        }
        N = nSamplesLB[cmd]
        if nSamples < N:
            error = (
                "RawDataAnalyzer: In function performSA(), %s requires at least %d samples."
                % (cmd.upper(), N)
            )
            Common.showError(error)
            return None

        # check number of inputs (for tsi only)
        nInputs = SampleData.getNumInputs(data)
        if cmd == "tsi":
            D = 10
            if nInputs > D:
                error = (
                    "RawDataAnalyzer: In function performSA(), %s requires at most %d inputs for total sensitivity analysis."
                    % (cmd.upper(), D)
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
        outfile = {"me": "matlabme.m", "ie": "matlabaie.m", "tsi": "matlabtsi.m"}

        mfile = outfile[cmd]
        if os.path.exists(mfile):
            mfile_ = RawDataAnalyzer.dname + os.path.sep + mfile
            os.rename(mfile, mfile_)
            mfile = mfile_
        else:
            error = "RawDataAnalyzer: %s does not exist." % mfile
            Common.showError(error, out)
            return None

        RawDataAnalyzer.plotSA(data, cmd, y, mfile)
        return mfile

    @staticmethod
    def plotSA(data, cmd, y, mfile):
        # plot
        datvar = "Mids"
        figtitle = {"me": "First-order", "ie": "Second-order", "tsi": "Total-order"}
        title = {
            "me": "Sobol First Order Indices",
            "ie": "Sobol First and Second Order Indices",
            "tsi": "Sobol Total Order Indices",
        }
        ylabel = "Sobol Indices"
        xlabel = "Input Parameters"
        xticklabels = []
        inputNames = data.getInputNames()
        inputTypes = data.getInputTypes()
        for name, inType in zip(inputNames, inputTypes):
            if inType == Model.VARIABLE:
                xticklabels.append(name)
        dat = Plotter.getdata(mfile, datvar)
        std = None
        outVarNames = SampleData.getOutputNames(data)
        outVarName = outVarNames[y - 1]
        ftitle = "%s Sensitivity Analysis on Ensemble Data" % figtitle[cmd]
        ptitle = "%s for %s" % (title[cmd], outVarName)
        if cmd == "ie":
            import numpy as np  # numpy used here only
            import math  # math used here only

            L = len(dat)
            M = int(math.sqrt(L))
            dat = np.reshape(dat, [M, M], order="F")
            yticklabels = xticklabels
            Plotter.plotbar3d(
                dat,
                std,
                ftitle,
                ptitle,
                xlabel,
                ylabel,
                xticklabels,
                yticklabels,
                barlabels=True,
            )
        else:
            Plotter.plotbar(
                dat, std, ftitle, ptitle, xlabel, ylabel, xticklabels, barlabels=True
            )

        return mfile
