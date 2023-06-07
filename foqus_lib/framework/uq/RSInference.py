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
import copy
import subprocess
import tempfile
import platform
import abc
import numpy as np
from scipy.stats import norm, lognorm, triang, gamma, beta, expon, weibull_min

# from PySide import QtCore, QtGui
from PyQt5 import QtCore, QtGui
from .Model import Model
from .SampleData import SampleData
from .Distribution import Distribution
from .Common import Common
from .LocalExecutionModule import LocalExecutionModule
from .ResponseSurfaces import ResponseSurfaces
from .RSAnalyzer import RSAnalyzer
from .Plotter import Plotter
from .UQAnalysis import UQAnalysis
from .UQRSAnalysis import UQRSAnalysis


class RSInference(UQRSAnalysis):
    def __init__(
        self,
        ensemble,
        ytable,
        xtable,
        obsTable,
        genPostSample=False,
        addDisc=False,
        showList=None,
        endFunction=None,
        disableWhilePlotting=None,
        userRegressionFile=None,
    ):
        outputs = [i + 1 for i in range(len(ytable)) if ytable[i] is not None]
        super(RSInference, self).__init__(
            ensemble,
            outputs,
            UQAnalysis.INFERENCE,
            [y["rsIndex"] for y in ytable if y is not None],
        )
        self.inputs = [
            i + 1
            for i in range(len(xtable))
            if xtable[i] is None or xtable[i]["type"] != "Fixed"
        ]
        self.ytable = ytable
        self.xtable = xtable
        self.obsTable = obsTable
        self.genPostSample = genPostSample
        self.addDisc = addDisc
        self.showList = showList
        self.endFunction = endFunction
        self.disableWhilePlotting = disableWhilePlotting
        self.userRegressionFile = userRegressionFile
        self.inferencer = RSInferencer()
        self.mfile = None

    def saveDict(self):
        sd = super(RSInference, self).saveDict()
        sd["ytable"] = self.ytable
        sd["xtable"] = self.xtable
        sd["obsTable"] = self.obsTable
        sd["genPostSample"] = self.genPostSample
        sd["addDisc"] = self.addDisc
        sd["showList"] = self.showList
        return sd

    def loadDict(self, sd):
        super(RSInference, self).loadDict(sd)
        self.ytable = sd.get("ytable", None)
        self.xtable = sd.get("xtable", None)
        self.obsTable = sd.get("obsTable", None)
        self.genPostSample = sd.get("genPostSample", False)
        self.addDisc = sd.get("addDisc", False)
        self.showList = sd.get("showList", None)

    def newEndFunction(self):
        self.mfile = self.inferencer.mfile
        if self.mfile is not None:
            self.archiveFile(self.mfile)
        if self.endFunction is not None:
            self.endFunction()

    def getResultsFile(self):
        return self.mfile

    def analyze(self):
        fname = Common.getLocalFileName(
            RSInferencer.dname, self.ensemble.getModelName().split()[0], ".dat"
        )
        fixedAsVariables = ResponseSurfaces.USER in [
            ResponseSurfaces.getEnumValue(rs) for rs in self.responseSurface
        ]
        self.ensemble.writeToPsuade(fname, fixedAsVariables=fixedAsVariables)
        self.inferencer.infer(
            fname,
            self.ytable,
            self.xtable,
            self.obsTable,
            genPostSample=self.genPostSample,
            addDisc=self.addDisc,
            show=self.showList,
            endFunction=self.newEndFunction,
            disableWhilePlotting=self.disableWhilePlotting,
            userRegressionFile=self.userRegressionFile,
        )

    def showResults(self, showList=None):
        if showList == None:
            showList = self.showList
        self.mfile_post = "matlabmcmc2.m"
        self.restoreFromArchive(self.mfile)
        fname = Common.getLocalFileName(
            RSInferencer.dname, self.ensemble.getModelName().split()[0], ".dat"
        )
        self.inferencer.infplot(self.mfile, fname, showList)

    def getAdditionalInfo(self):
        info = super(RSInference, self).getAdditionalInfo()
        info["xtable"] = self.xtable
        info["ytable"] = self.ytable
        info["obsTable"] = self.obsTable
        info["Use Discrepancy"] = self.addDisc
        return info


class RSInferencer(
    QtCore.QObject
):  # Must inherit from QObject for plotting to stay in main thread

    dname = os.getcwd() + os.path.sep + "RSInference_files"

    def __init__(self):
        super(RSInferencer, self).__init__()
        self.mfile = None

    @staticmethod
    def pdfrange(pdf, param1, param2=None):
        # apply this function for initializing the prior bounds
        # parameters need to be passed in as floats

        if pdf == Distribution.NORMAL:
            # norm.pdf(x) = exp(-x**2/2)/sqrt(2*pi)
            mu = param1
            sigma = param2
            rv = norm(loc=mu, scale=sigma)
        elif pdf == Distribution.LOGNORMAL:
            # lognorm.pdf(x, s) = 1 / (s*x*sqrt(2*pi)) * exp(-1/2*(log(x)/s)**2)
            mu = param1  # scale parameter "exp(mu)"
            sigma = param2  # shape parameter "s"
            rv = lognorm(sigma, loc=0, scale=np.exp(mu))
        elif pdf == Distribution.TRIANGLE:
            # triangular dist represented as upsloping line from loc to (loc+c*scale)
            # and then downsloping line from (loc+c*scale) to (loc+scale)
            c = param1  # shape parameter "mode"
            scale = param2  # scale parameter "width"
            loc = c - scale / 2  # location parameter "start"
            rv = triang(c, loc=loc, scale=scale)
        elif pdf == Distribution.GAMMA:
            # gamma.pdf(x, a) = b**a * x**(a-1) * exp(-b*x) / gamma(a)
            a = param1  # shape parameter "alpha" > 0
            b = param2  # rate parameter "beta" > 0
            rv = gamma(a, loc=0, scale=1.0 / b)
        elif pdf == Distribution.BETA:
            # beta.pdf(x, a, b) = gamma(a+b)/(gamma(a)*gamma(b)) * x**(a-1) * (1-x)**(b-1)
            a = param1  # shape parameter "alpha" > 0
            b = param2  # shape parameter "beta" > 0
            rv = beta(a, b, loc=0, scale=1)
        elif pdf == Distribution.EXPONENTIAL:
            # expon.pdf(x) = b * exp(- b*x)
            b = param1  # rate parameter "lambda" > 0
            rv = expon(loc=0, scale=1.0 / b)
        elif pdf == Distribution.WEIBULL:
            # weibull_min.pdf(x, c) = c * x**(c-1) * exp(-x**c)
            scale = param1  # scale parameter "lambda" > 0
            c = param2  # shape parameter "k" > 0
            rv = weibull_min(c, loc=0, scale=scale)
        else:
            return None

        return rv.interval(0.99)

    def infer(
        self,
        fname,
        ytable,
        xtable,
        exptable,
        genPostSample=False,
        addDisc=None,
        show=None,
        endFunction=None,
        disableWhilePlotting=None,
        userRegressionFile=None,
    ):

        xtable = copy.deepcopy(xtable)
        self.stopInfer = False

        # Function to execute after inference has finished.
        # Function would enable button again and such things.
        self.endFunction = endFunction

        # Widget to disable while plotting
        # If widget is not disabled, if clicked while plotting,
        # it would cause inference to start again.
        self.disableWhilePlotting = disableWhilePlotting

        # read data
        data = LocalExecutionModule.readSampleFromPsuadeFile(
            fname
        )  # does not assume rstype/order written to data

        # process output RS info
        nOutputs = SampleData.getNumOutputs(data)
        if len(ytable) != nOutputs:
            error = 'RSInference: In function infer(), "ytable" is expected to be a list of length "nOutputs".'
            Common.showError(error)
            return None
        indices = (
            []
        )  # indices[i] stores the output index for the i-th observed output variable
        rsIndices = (
            []
        )  # rsIndices[i] stores the RS index for the i-th observed output variable
        legendreOrders = (
            []
        )  # legendreOrders[i] stores the Legendre order for the i-th observed output variable
        userRegressionFiles = (
            []
        )  # userRegressionFiles[i] stores the user driver file for the i-th observed output variable
        userRegressionArgs = (
            []
        )  # userRegressionArgs[i] stores the output index, an optional argument to the driver file,
        # ... for the i-th observed output variable
        marsOptions = [
            None
        ] * nOutputs  # marsOptions[i] stores customized settings for MARS and MARSBag
        setMARS = []
        ### ytable should be an array of length N, where N is the number of outputs, observed and unobserved.
        ### if output is unobserved, ytable[i] = None
        ### if output is observed, ytable[i] should contain the following fields:
        ###     {'rsIndex':%d, 'legendreOrder':%d, 'userRegressionFile':%s, 'userRegressionArg':%d}
        ### if MARS options are set, then ytable[i] should contain additional fields:
        ###     {'rsIndex':%d, 'legendreOrder':%d, 'userRegressionFile':%s, 'userRegressionArg':%d, 'marsBases':%d, 'marsInteractions':%d}
        for i in range(nOutputs):
            obs = ytable[i]
            if obs is not None:
                if "rsIndex" not in obs:
                    error = "RSInference: In function infer(), each observed output must have rsIndex key"
                    Common.showError(error)
                    return None
                rsIndex = obs["rsIndex"]
                if rsIndex == ResponseSurfaces.LEGENDRE:
                    order = None
                    if "legendreOrder" in obs:
                        order = obs["legendreOrder"]
                    userRegressionFiles.append(None)
                    userRegressionArgs.append(None)
                    if order is not None:
                        legendreOrders.append(order)
                    else:
                        error = 'RSInference: In function infer(), "legendreOrder" is required for LEGENDRE response surface.'
                        Common.showError(error)
                        return None
                elif rsIndex == ResponseSurfaces.USER:
                    userFile = None
                    if "userRegressionFile" in obs:
                        userFile = obs["userRegressionFile"]
                    userArg = None
                    if "userRegressionArg" in obs:
                        userArg = obs["userRegressionArg"]
                    legendreOrders.append(None)
                    if userFile is not None and os.path.exists(userFile):
                        userRegressionFiles.append(userFile)
                    else:
                        error = 'RSInference: In function infer(), "userRegressionFile" is required for USER REGRESSION response surface.'
                        Common.showError(error)
                        return None
                    if userArg is not None and isinstance(userArg, (int, str)):
                        userRegressionArgs.append(userArg)
                    else:
                        userRegressionArgs.append(
                            1
                        )  # if no output index or name is given, use 1 as default
                elif rsIndex in [
                    ResponseSurfaces.MARS,
                    ResponseSurfaces.MARSBAG,
                ]:  # check for MARS options
                    if "marsBases" in obs and "marsInteractions" in obs:
                        mopts = RSAnalyzer.checkMARS(data, obs)
                        if mopts is not None:
                            setMARS.append(i)
                            marsOptions[i] = mopts
                #                            marsBases, marsInteractions, marsNormOutputs = marsOptions

                rsIndices.append(rsIndex)
                indices.append(i)

        # delete unobserved outputs from data
        odelete = [
            i + 1 for i in range(nOutputs) if i not in indices
        ]  # stores the (1-indexed) output variable indices that are unobserved
        if odelete:
            # ... write script
            nOutputs = SampleData.getNumOutputs(data) - len(odelete)
            outfile = Common.getLocalFileName(RSInferencer.dname, fname, ".infdat")
            f = tempfile.SpooledTemporaryFile(mode="wt")
            if platform.system() == "Windows":
                import win32api

                fname = win32api.GetShortPathName(fname)
            f.write("load %s\n" % fname)
            odelete_reverse = odelete[::-1]  # reverse output indices to be deleted
            for (
                y
            ) in (
                odelete_reverse
            ):  # at each odelete, the highest-indexed output needs to be deleted first
                f.write("odelete\n")
                f.write("%d\n" % y)
            if platform.system() == "Windows":
                head, tail = os.path.split(outfile)
                head = win32api.GetShortPathName(head)
                outfile = os.path.join(head, tail)
            f.write("write %s\n" % outfile)
            f.write("n\n")  # write all outputs
            f.write("quit\n")
            f.seek(0)
            out, error = Common.invokePsuade(f)
            f.close()
            if out is None:
                return
            # ... operate on the new data file
            fname = outfile
            data = LocalExecutionModule.readSampleFromPsuadeFile(fname)
            marsOptions = [m for i, m in enumerate(marsOptions) if i in indices]

        # process input prior info
        ### xtable should be an array of length N, where N is the number of inputs.
        ### xtable[i] should contain the following fields:
        ###     {'name':%s, 'type':%s, 'value':%s, 'min':%f, 'max':%f, 'pdf':%d, 'param1':%f, 'param2':%f}
        inputTypes = data.getInputTypes()
        nVariableInputs = inputTypes.count(Model.VARIABLE)
        # ... get design inputs
        designInVars = [i + 1 for i, e in enumerate(xtable) if e["type"] == "Design"]
        # ... get fixed inputs
        fixedInVars = [i + 1 for i, e in enumerate(xtable) if e["type"] == "Fixed"]
        indexfile = None
        if fixedInVars:
            # ... write index file based on fixed inputs
            indexfile = RSInferencer.dname + os.path.sep + "indexfile"
            f = open(indexfile, "w")
            f.write("%d\n" % nVariableInputs)
            for i in range(nVariableInputs):
                k = i + 1
                e = xtable[i]
                if e["type"] == "Fixed":
                    f.write("%d %d %f\n" % (k, 0, e["value"]))
                else:
                    f.write("%d %d %d\n" % (k, k, 0))
            f.close()
        # Expand xtable and show in cases of user regression where all inputs are used in data, not just the variable ones
        j = 0
        newTable = [None] * nVariableInputs
        inputNames = data.getInputNames()
        variableInputNames = [
            inputName
            for i, inputName in enumerate(inputNames)
            if inputTypes[i] == Model.VARIABLE
        ]
        newShow = []
        for i in range(nVariableInputs):
            e = xtable[j]
            if e["name"] == variableInputNames[i]:
                # ... nullify xtable's entries corresponding to design/fixed inputs
                if e["type"] not in ["Design", "Fixed"]:
                    newTable[i] = e
                if j in show:
                    newShow.append(i)
                j += 1
                if j == len(xtable):
                    break
        xtable = newTable
        show = newShow
        # ... write out RS data file with only variable inputs' prior info
        p = RSAnalyzer.parsePrior(data, xtable)
        if p is not None:
            outfile = Common.getLocalFileName(RSInferencer.dname, fname, ".infdat")
            y = 1
            RSAnalyzer.writeRSdata(
                outfile,
                y,
                data,
                indexfile=indexfile,
                randseed=1211319841,  ### TO DO: remove rand seed?
                inputLowerBounds=p["inputLB"],
                inputUpperBounds=p["inputUB"],
                inputPDF=p["dist"],
            )
            # ... operate on the new data file
            fname = outfile
            data = LocalExecutionModule.readSampleFromPsuadeFile(fname)

        # write MCMC data file
        ### *** THE FORMAT OF THIS DATA FILE IS: (O1 means output 1,
        ### m - no. of design parameters, p - no. of experiments):
        ### PSUADE_BEGIN
        ### <p> <nOutputs> <m> <design parameter identifiers>
        ### 1 <design values...> <O1 mean> <O1 std dev> ... <On std dev>
        ### 2 <design values...> <O1 mean> <O1 std dev> ... <On std dev>
        ### ...
        ### p <design values...> <O1 mean> <O1 std dev> ... <On std dev>
        ### PSUADE_END
        ###
        ### exptable should be an array of length p.
        ### exptable[i] should be a numeric array:
        ###        [expIndex, designVal_1, ..., designVal_m, outputMean_1, outputStd_1, ..., outputMean_n, outputStd_n]
        mcmcfile = RSInferencer.dname + os.path.sep + "mcmcFile"
        f = open(mcmcfile, "w")
        f.write("PSUADE_BEGIN\n")
        nOutputs = SampleData.getNumOutputs(data)  # number of (observed) outputs
        nExp = len(exptable)  # number of experiments
        nDesignInVars = len(designInVars)  # number of design parameters
        delim = " "
        # ... write header
        dstr = ""
        if designInVars:
            dstr = [str(s) for s in designInVars]
            dstr = delim.join(dstr)
        f.write("%d %d %d %s\n" % (nExp, nOutputs, nDesignInVars, dstr))
        # ... write data
        nterms = nDesignInVars + 2 * nOutputs + 1
        for i in range(nExp):
            e = exptable[i]
            if len(e) == nterms:
                estr = [str(s) for s in e]
                estr = delim.join(estr)
                f.write("%s\n" % estr)
            else:
                error = (
                    "RSInference: In function infer(), the %d-th row of exptable expects %d terms."
                    % (i + 1, nterms)
                )
                Common.showError(error, out)
                return None
        f.write("PSUADE_END\n")
        f.close()

        # write script
        cmd = "rsmcmc"
        f = tempfile.SpooledTemporaryFile(mode="wt")
        if platform.system() == "Windows":
            import win32api

            fname = win32api.GetShortPathName(fname)
        f.write("load %s\n" % fname)
        if len(setMARS) > 0:
            f.write("rs_expert\n")
        f.write(
            "ana_expert\n"
        )  # turn on analysis expert mode, required for non-uniform input priors
        f.write("%s\n" % cmd)
        if platform.system() == "Windows":
            import win32api

            mcmcfile = win32api.GetShortPathName(mcmcfile)
        f.write("%s\n" % mcmcfile)  # spec file for building the likelihood function
        f.write("y\n")  # do include response surface uncertainties
        for i in range(
            nOutputs
        ):  # for each output, set RS; all outputs are observed in this data file
            rsIndex = rsIndices[i]
            f.write("%d\n" % rsIndex)
            if rsIndex == ResponseSurfaces.LEGENDRE:
                f.write("%d\n" % legendreOrders[i])
            elif rsIndex == ResponseSurfaces.USER:
                f.write("1\n")  # number of basis functions
                driverFile = userRegressionFiles[i]
                if platform.system() == "Windows":
                    driverFile = win32api.GetShortPathName(driverFile)
                f.write("%s\n" % driverFile)  # driver file
                f.write("y\n")  # apply auxillary arg (output index)
                arg = userRegressionArgs[i]
                if isinstance(arg, int):
                    formatString = "%d\n"
                else:
                    formatString = "%s\n"
                f.write(formatString % arg)  # output name
            elif indices[i] in setMARS:
                if rsIndex == ResponseSurfaces.MARSBAG:
                    f.write("0\n")  # mean (0) or median (1) mode
                    f.write(
                        "100\n"
                    )  # number of MARS instantiations [range:10-5000, default=100]
                    ### TO DO: revert back to 100 for deployment
                marsBases, marsInteractions, marsNormOutputs = marsOptions[i]
                f.write("%d\n" % marsBases)
                f.write("%d\n" % marsInteractions)
                if rsIndex == ResponseSurfaces.MARS:
                    f.write("%s\n" % marsNormOutputs)
        f.write(
            "5000\n"
        )  # MCMC sample increment [range: 5000 - 50000]; default = 10000
        f.write("20\n")  # number of bins in histogram [range: 10 - 25]; default = 20
        f.write("-1\n")  # generate posterior plots for all inputs
        disc = "n"
        if addDisc:
            disc = "y"
        f.write("%s\n" % disc)  # add discrepancy function
        saveSample = "n"
        if genPostSample:
            saveSample = "y"
        f.write("%s\n" % saveSample)  # generate a sample from posterior distributions
        f.write(
            "60\n"
        )  # sample size to construct MCMC proposal distribution; default = 100
        if addDisc:
            f.write("18\n")  # set RS for discrepancy function; default = kriging
            ### TO DO: allow user to customize RS for discrepancy function
            f.write("n\n")  # set nominal values for other inputs
            if len(setMARS) > 0:
                f.write("3\n")  # Kriging slow mode
                f.write("1e-4\n")  # Kriging tolerance
        f.write("3\n")  # number of MCMC chains; default = 3
        f.write(
            "1.05\n"
        )  # PSRF (convergence metric for MCMC) thershold; default = 1.05
        f.write("quit\n")
        f.seek(0)

        # invoke psuade
        self.fname = fname
        self.genPostSample = genPostSample
        self.addDisc = addDisc
        self.data = data
        self.show = show
        self.textDialog = Common.textDialog()
        self.thread = psuadeThread(self, f, self.finishInfer, self.textDialog)
        self.thread.start()

    def stopInference(self):
        self.stopInfer = True

    def finishInfer(self, out, error):
        # if self.stopInfer:
        #    return

        if self.disableWhilePlotting is not None:
            self.disableWhilePlotting.setEnabled(False)
            # Force immediate draw to prevent clicking of button before done, causing inference to go again
            self.disableWhilePlotting.repaint()

        errfile = "psTrack.m"  # diagnostics file generated by psuade if it fails during "rsmcmc"
        if os.path.exists(errfile):
            os.remove(errfile)
            s = "................................."
            ss = "Recommendations"
            error = (
                "RSInference: In function infer(), psuade has terminated.\n%s%s%s\n1. Increase the standard deviation of the observed outputs.\n2. Try different parameters for the input prior distributions.\n%s%s%s"
                % (s, ss, s, s, "".join(["."] * len(ss)), s)
            )
            Common.showError(error, out)
            return None

        # check output file
        mfile = "matlabmcmc2.m"
        self.mfile = None
        if os.path.exists(mfile):
            mfile_ = RSInferencer.dname + os.path.sep + mfile
            if os.path.exists(mfile_):
                os.remove(mfile_)
            os.rename(mfile, mfile_)
            mfile = mfile_
            mfile0 = "matlabmcmc.m"  # extra file generated by psuade
            if os.path.exists(mfile0):
                mfile0_ = RSInferencer.dname + os.path.sep + mfile0
                if os.path.exists(mfile0_):
                    os.remove(mfile0_)
                os.rename(mfile0, mfile0_)
        elif self.stopInfer:
            if self.endFunction is not None:
                self.endFunction()
            return None
        else:
            error = "RSInference: %s does not exist." % mfile
            Common.showError(error, out)
            if self.endFunction is not None:
                self.endFunction()
            return None
        self.mfile = mfile

        # check posterior sample file
        sfile = None
        if self.genPostSample:
            sfile = "MCMCPostSample"
            if os.path.exists(sfile):
                sfile_ = RSInferencer.dname + os.path.sep + sfile
                if os.path.exists(sfile_):
                    os.remove(sfile_)
                os.rename(sfile, sfile_)
                sfile = sfile_
            else:
                error = "RSInference: %s does not exist." % sfile
                Common.showError(error, out)
                return None
        self.sampleFile = sfile

        # check discrepancy sample file
        dfile = None
        if self.addDisc:
            dfile = "psDiscrepancyModel"
            if not os.path.exists(dfile):
                error = "RSInference: %s does not exist." % dfile
                Common.showError(error, out)
                return None

        # plot
        self.infplot(self.mfile, self.fname, self.show)

        if self.endFunction is not None:
            self.endFunction()

    @staticmethod
    def getplotdat(mfile, variableInputNames, xmin, xmax, plotvars, show=None):

        xdat = []
        ydat = []
        zdat = []
        hdat = []  # data for diagonal subplots (histograms)
        zmin = np.inf
        zmax = -zmin
        xlabel = []
        ylabel = []
        nVariableInputs = len(variableInputNames)

        if show is None:  # default: show all inputs
            showInputs = range(nVariableInputs)
        else:
            showInputs = show
        nshow = len(showInputs)

        # extract log likelihood, if available, from mfile
        datvar = "negll"
        try:
            loglik = Plotter.getdata(mfile, datvar, grabline=True)
            loglik = loglik[0]
        except IndexError:
            loglik = None

        # extract data from mfile
        xlim = []
        ylim = []
        for r in range(nshow):
            i_ = showInputs[r]
            i = i_ + 1  # psuade is 1-indexed
            datvar = "X\(%d,:\)" % i
            xd = Plotter.getdata(mfile, datvar)
            xdat.append(xd)
            ydat.append("None")
            datvar = "%s\(%d,:\)" % (plotvars["hist"], i)
            zd = Plotter.getdata(mfile, datvar)
            zdat.append(zd)
            hdat.extend(zd)
            inVarName = variableInputNames[i_]
            xlabel.append(inVarName)
            ylabel.append("Probabilities")
            xlim.append([xmin[i_], xmax[i_]])
            ylim.append(None)  # placeholder, actual limits will get set later
            for c in range(r + 1, nshow):
                j_ = showInputs[c]
                j = j_ + 1  # psuade is 1-indexed
                xdat.append(xd)
                datvar = "X\(%d,:\)" % j
                ydat.append(Plotter.getdata(mfile, datvar))
                datvar = "%s\(%d,%d,:,:\)" % (plotvars["heatmap"], j, i)
                zd = Plotter.getdata(mfile, datvar)
                zdat.append(zd)
                zdf = zd.flatten()
                zmin = min(zmin, min(zdf))
                zmax = max(zmax, max(zdf))
                ylabel.append(inVarName)  # input parameter above goes on y-axis
                ylim.append([xmin[i_], xmax[i_]])
                xlabel.append(variableInputNames[j_])
                xlim.append([xmin[j_], xmax[j_]])
            hmin = max(0, min(hdat))
            hmax = min(1, max(hdat))
        for e in range(len(ylim)):
            if ylim[e] is None:
                ylim[e] = [hmin, hmax]
        zlim = [zmin, zmax]
        ylabel = ["Probabilities"] * len(xlabel)
        sb_indices = np.reshape(np.arange(1, nshow**2 + 1), [nshow, nshow])
        sb_indices[
            np.tril(sb_indices, -1) > 0
        ] = -1  # set lower triangular elements to -1

        return (xdat, ydat, zdat, xlabel, ylabel, xlim, ylim, zlim, sb_indices, loglik)

    @staticmethod
    def genheatmap(fname, filetype=None, move=True):

        Common.initFolder(RSInferencer.dname)
        loadcmd = {None: "load", "std": "read_std"}

        # write script
        cmd = "iplot2_pdf"
        f = tempfile.SpooledTemporaryFile(mode="wt")
        if platform.system() == "Windows":
            import win32api

            fname = win32api.GetShortPathName(fname)
        f.write("%s %s\n" % (loadcmd[filetype], fname))
        f.write("%s\n" % cmd)
        f.write("quit\n")
        f.seek(0)

        # invoke psuade
        out, error = Common.invokePsuade(f)
        f.close()

        # process error
        if error:
            return None

        # check output file
        mfile = "matlabiplt2pdf.m"
        if os.path.exists(mfile):
            if move:
                mfile_ = RSInferencer.dname + os.path.sep + mfile
                os.rename(mfile, mfile_)
                mfile = mfile_
        else:
            error = "RSInference: %s does not exist." % mfile
            Common.showError(error, out)
            return None

        return mfile

    @staticmethod
    def xvarinfo(fname):
        # read data to get variable names and ranges
        data = LocalExecutionModule.readSampleFromPsuadeFile(fname)
        inVarNames = SampleData.getInputNames(data)
        inVarTypes = SampleData.getInputTypes(data)
        inVarLB = SampleData.getInputMins(data)
        inVarUB = SampleData.getInputMaxs(data)
        xnames = []
        xmin = []
        xmax = []
        for name, vartype, lower, upper in zip(
            inVarNames, inVarTypes, inVarLB, inVarUB
        ):
            if vartype == Model.VARIABLE:
                xnames.append(name)
                xmin.append(lower)
                xmax.append(upper)
        return (xnames, xmin, xmax)

    @staticmethod
    def infplot_prior(mfile, fname, show=None):

        # !!! This function generates the plot from matlabiplt2pdf.m !!!
        xnames, xmin, xmax = RSInferencer.xvarinfo(fname)

        # plot prior
        plotvars = {"hist": "D", "heatmap": "NC"}
        (
            xdat,
            ydat,
            zdat,
            xlabel,
            ylabel,
            xlim,
            ylim,
            zlim,
            sb_indices,
            loglik,
        ) = RSInferencer.getplotdat(mfile, xnames, xmin, xmax, plotvars, show=show)
        ptitle = "Input PRIOR Probabilities"
        ftitle = "Input Distribution Plots"
        Plotter.plotinf(
            xdat,
            ydat,
            zdat,
            ftitle,
            ptitle,
            xlabel,
            ylabel,
            sb_indices,
            xlim,
            ylim,
            zlim,
            lastplot=True,
        )

    @staticmethod
    def infplot(mfile, fname, show=None):

        # !!! This function generates the plot from matlabmcmc2.m !!!
        xnames, xmin, xmax = RSInferencer.xvarinfo(fname)

        # plot prior
        plotvars = {"hist": "DP", "heatmap": "NCP"}
        (
            xdat,
            ydat,
            zdat,
            xlabel,
            ylabel,
            xlim,
            ylim,
            zlim,
            sb_indices,
            loglik,
        ) = RSInferencer.getplotdat(mfile, xnames, xmin, xmax, plotvars, show=show)
        ptitle = "Input PRIOR Probabilities"
        ftitle = "Input Distribution Plots *before* Bayesian Inference"
        Plotter.plotinf(
            xdat,
            ydat,
            zdat,
            ftitle,
            ptitle,
            xlabel,
            ylabel,
            sb_indices,
            xlim,
            ylim,
            zlim,
            lastplot=False,
        )

        # plot posterior
        plotvars = {"hist": "D", "heatmap": "NC"}
        (
            xdat,
            ydat,
            zdat,
            xlabel,
            ylabel,
            xlim,
            ylim,
            zlim,
            sb_indices,
            loglik,
        ) = RSInferencer.getplotdat(mfile, xnames, xmin, xmax, plotvars, show=show)
        ptitle = "Input POSTERIOR Probabilities"
        if loglik != None:
            ptitle = ptitle + " (loglikelihood=" + str(loglik) + ")"
        ftitle = "Input Distribution Plots *after* Bayesian Inference"
        Plotter.plotinf(
            xdat,
            ydat,
            zdat,
            ftitle,
            ptitle,
            xlabel,
            ylabel,
            sb_indices,
            xlim,
            ylim,
            zlim,
            lastplot=True,
        )


class psuadeThread(QtCore.QThread):
    def __init__(self, parent, fileHandle, onFinishedFunctionHandle, textDialog):
        QtCore.QThread.__init__(self)
        self.worker = psuadeWorker(
            self, fileHandle, onFinishedFunctionHandle, textDialog
        )
        self.worker.moveToThread(self)
        self.started.connect(self.worker.run)
        self.worker.finishedSignal.connect(self.quit)
        self.worker.finishedSignal.connect(self.worker.deleteLater)
        self.finished.connect(self.deleteLater)


class psuadeWorker(QtCore.QObject):
    finishedSignal = QtCore.pyqtSignal()
    functionSignal = QtCore.pyqtSignal(str, str)
    textDialogShowSignal = QtCore.pyqtSignal()
    textDialogCloseSignal = QtCore.pyqtSignal()
    textDialogInsertSignal = QtCore.pyqtSignal(str)
    textDialogEnsureVisibleSignal = QtCore.pyqtSignal()
    showErrorSignal = QtCore.pyqtSignal(str, str)

    def __init__(self, parent, fileHandle, onFinishedFunctionHandle, textDialog):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.fileHandle = fileHandle
        self.functionHandle = onFinishedFunctionHandle
        self.textDialog = textDialog

    def run(self):
        self.functionSignal.connect(self.functionHandle)
        self.textDialogShowSignal.connect(self.textDialog.show)
        self.textDialogCloseSignal.connect(self.textDialog.close)
        self.textDialogInsertSignal.connect(self.textDialog.textedit.insertPlainText)
        self.textDialogEnsureVisibleSignal.connect(
            self.textDialog.textedit.ensureCursorVisible
        )
        self.showErrorSignal.connect(self.textDialog.showError)
        out, error = Common.invokePsuade(
            self.fileHandle,
            textDialog=self.textDialog,
            dialogShowSignal=self.textDialogShowSignal,
            dialogCloseSignal=self.textDialogCloseSignal,
            textInsertSignal=self.textDialogInsertSignal,
            ensureVisibleSignal=self.textDialogEnsureVisibleSignal,
            showErrorSignal=self.showErrorSignal,
            printOutputToScreen=True,
        )
        if out is None:
            return
        self.fileHandle.close()
        self.functionSignal.emit(out, error)
        self.finishedSignal.emit()
