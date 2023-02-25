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
import math
import os
import subprocess
import tempfile
import platform
import copy
import re
import numpy as np
from scipy import stats
from .Model import Model
from .SampleData import SampleData
from .SamplingMethods import SamplingMethods
from .Distribution import Distribution
from .Common import Common
from .LocalExecutionModule import LocalExecutionModule
from .ResponseSurfaces import ResponseSurfaces
from .RawDataAnalyzer import RawDataAnalyzer
from .Plotter import Plotter


class RSAnalyzer:

    dname = os.getcwd() + os.path.sep + "RSAnalyzer_files"
    Common.initFolder(dname)

    @staticmethod
    def writeRSdata(outfile, y, data, **kwargs):

        nInputs = SampleData.getNumInputs(data)
        nOutputs = SampleData.getNumOutputs(data)
        nSamples = SampleData.getNumSamples(data)

        # defaults
        rsIndex = 0
        rsPsuadeName = "MARS"
        order = SampleData.getLegendreOrder(data)
        if order is None:
            order = -1  # set to psuade default
        omitData = False
        nDataPts = nSamples  # number of data points from which RS will be constructed
        driver = SampleData.getDriverName(data)
        if driver is None:
            driver = "NONE"
        savefreq = 0
        inputLB = None
        inputUB = None
        distributions = None
        indexfile = None
        rseed = None

        # process keyworded arguments
        for key in kwargs:
            k = key.lower()
            if k == "randseed":
                rseed = kwargs[key]
            elif k == "rsmethod":
                rs = kwargs[key]
                rsIndex = ResponseSurfaces.getEnumValue(rs)
                rsPsuadeName = ResponseSurfaces.getPsuadeName(rsIndex)
            elif k == "legendreorder":
                legendreOrder = kwargs[key]
                if type(legendreOrder) == int:
                    order = legendreOrder
            elif k == "omitdata":
                if kwargs[key]:
                    omitData = True
            elif k == "nsamples":
                nSamples = kwargs[key]
            elif k == "driver":  # for RS emulation, set to name of training data file
                driver = kwargs[key]
                trainData = LocalExecutionModule.readSampleFromPsuadeFile(driver)
                nDataPts = max(nDataPts, trainData.getNumSamples())
            elif k == "savefreq":
                savefreq = kwargs[key]
            elif k == "inputlowerbounds":
                inputLB = kwargs[key]
            elif k == "inputupperbounds":
                inputUB = kwargs[key]
            elif k == "inputpdf":
                distributions = kwargs[key]
            elif k == "indexfile":
                indexfile = kwargs[key]

        ### modified version of SampleData.writeToPsuade() ###
        f = open(outfile, "w")

        inputNames = SampleData.getInputNames(data)
        inputTypes = data.getInputTypes()
        nVariableInputs = inputTypes.count(Model.VARIABLE)

        # write out data
        if not omitData:
            S = SampleData.getRunState(data)
            X = SampleData.getInputData(data)
            Y = SampleData.getOutputData(data)

            hasOutputData = False
            if Y is not None:
                if isinstance(Y, np.ndarray):
                    if Y.size > 0:
                        hasOutputData = True
                elif Y:
                    hasOutputData = True
            if not hasOutputData:
                nan = 9.9999999999999997e34
                Y = [[nan] * nOutputs] * nSamples

            f.write("PSUADE_IO (Note : inputs not true inputs if pdf ~=U)\n")
            f.write("%d %d %d\n" % (nVariableInputs, nOutputs, nSamples))
            for i in range(nSamples):
                f.write("%d %d\n" % (i + 1, S[i]))
                for j in range(nInputs):
                    if inputTypes[j] == Model.VARIABLE:
                        f.write(" % .16e\n" % X[i][j])
                for j in range(nOutputs):
                    if np.isnan(Y[i][j]):
                        f.write(" 9.9999999999999997e+34\n")
                    else:
                        f.write(" % .16e\n" % Y[i][j])
            f.write("PSUADE_IO\n")

        # write out meta info
        f.write("PSUADE\n")
        # ... inputs ...
        f.write("INPUT\n")
        numFixed = nInputs - nVariableInputs
        if numFixed > 0:
            f.write("   num_fixed %d\n" % numFixed)
        f.write("   dimension = %d\n" % nVariableInputs)
        if inputLB is None:
            inputLB = SampleData.getInputMins(data)
        if inputUB is None:
            inputUB = SampleData.getInputMaxs(data)
        indices = list(range(nInputs))
        variableIndex = 1
        fixedIndex = 1
        for i, name, inType, lb, ub in zip(
            indices, inputNames, inputTypes, inputLB, inputUB
        ):
            if inType == Model.VARIABLE:
                f.write(
                    "   variable %d %s  =  % .16e  % .16e\n"
                    % (variableIndex, name, lb, ub)
                )
                variableIndex = variableIndex + 1
            else:
                f.write("   fixed %d %s = % .16e\n" % (fixedIndex, name, lb))
                fixedIndex = fixedIndex + 1
        if distributions is None:
            distributions = SampleData.getInputDistributions(data)
        for i, inType, dist in zip(indices, inputTypes, distributions):
            if inType == Model.VARIABLE:
                distType = dist.getDistributionType()
                distParams = dist.getParameterValues()
                if distType != Distribution.UNIFORM:
                    f.write(
                        "   PDF %d %c" % (i + 1, Distribution.getPsuadeName(distType))
                    )
                    if distType == Distribution.SAMPLE:
                        sfile = distParams[0]
                        xindex = distParams[1]
                        if sfile is not None and xindex is not None:
                            if platform.system() == "Windows":
                                import win32api

                                sfile = win32api.GetShortPathName(sfile)
                            f.write(" %s %d" % (sfile, xindex))
                        else:
                            error = 'RSAnalyzer: In function writeRSdata(), "sfile" and "xindex" is required of SAMPLE distribution.'
                            Common.showError(error)
                            return None
                    else:
                        if distParams[0] is not None:
                            f.write(" % .16e" % distParams[0])
                        if distParams[1] is not None:
                            f.write(" % .16e" % distParams[1])
                    f.write("\n")
        f.write("END\n")

        # ... outputs ...
        f.write("OUTPUT\n")
        f.write("   dimension = %d\n" % nOutputs)
        outputNames = SampleData.getOutputNames(data)
        indices = list(range(nOutputs))
        for i, name in zip(indices, outputNames):
            f.write("   variable %d %s\n" % (i + 1, name))
        f.write("END\n")

        # ... method ...
        f.write("METHOD\n")
        method = SamplingMethods.getPsuadeName(SampleData.getSampleMethod(data))
        f.write("   sampling = %s\n" % method)
        f.write("   num_samples = %d\n" % nSamples)
        f.write("   num_replications = 1\n")
        f.write("   num_refinements = 0\n")
        f.write("   refinement_size = 10000000\n")
        f.write("   reference_num_refinements = 0\n")
        if rseed is not None:
            f.write("random_seed = %d\n" % rseed)  # random seed
        f.write("END\n")

        # ... application ...
        f.write("APPLICATION\n")
        if driver != "NONE" and platform.system() == "Windows":
            import win32api

            driver = win32api.GetShortPathName(driver)
        f.write("   driver = %s\n" % driver)
        f.write("   opt_driver = NONE\n")
        f.write("   aux_opt_driver = NONE\n")
        f.write("   max_job_wait_time = 1000000\n")
        if savefreq > 0:
            f.write("   save_frequency = %d\n" % savefreq)
        f.write("END\n")

        # ... analysis ...
        f.write("ANALYSIS\n")
        f.write("   analyzer output_id  = %d\n" % y)
        f.write("   analyzer rstype = %s\n" % rsPsuadeName)
        f.write("   use_input_pdfs\n")
        if rsIndex == ResponseSurfaces.LEGENDRE:
            if order == -1:
                error = 'RSAnalyzer: In function writeRSdata(), "legendreOrder" is required for LEGENDRE response surface.'
                Common.showError(error)
                return None
            f.write("   analyzer rs_legendre_order = %d\n" % order)
        f.write("   analyzer threshold = 1.000000e+00\n")
        if nDataPts > 5000:
            f.write("   rs_max_pts = %d\n" % nDataPts)
        if indexfile is not None:
            f.write("   analyzer rs_index_file = %s\n" % indexfile)
        f.write("   printlevel 1\n")
        f.write("END\n")

        f.write("END\n")
        f.close()

        return outfile

    @staticmethod
    def checkSampleSize(nSamples, nInputs, rsIndex, legendreOrder=None):

        # apply this function to activate response surfaces in the GUI
        if rsIndex in ResponseSurfaces.polynomialEnums:
            if rsIndex == ResponseSurfaces.LINEAR:
                p = 1
            elif rsIndex == ResponseSurfaces.QUADRATIC:
                p = 2
            elif rsIndex == ResponseSurfaces.CUBIC:
                p = 3
            elif rsIndex == ResponseSurfaces.QUARTIC:
                p = 4
            elif rsIndex == ResponseSurfaces.LEGENDRE:
                if legendreOrder is not None:
                    p = legendreOrder  # Legendre order is a required input argument
                else:
                    error = 'RSAnalyzer: In function checkSampleSize(), "legendreOrder" is required for LEGENDRE response surface.'
                    Common.showError(error)
                    return False
            N = ResponseSurfaces.getPolynomialMinSampleSize(nInputs, p)
        elif rsIndex == ResponseSurfaces.MARS:
            N = 50
        elif rsIndex == ResponseSurfaces.KRIGING:
            N = 10
        else:
            N = 100  # minimum sample size for all other response surfaces

        return nSamples >= N

    @staticmethod
    def parsePrior(data, xprior):
        nInputs = SampleData.getNumInputs(data)
        inVarNames = SampleData.getInputNames(data)
        inVarTypes = SampleData.getInputTypes(data)
        nVariableInputs = inVarTypes.count(Model.VARIABLE)
        nXpriorVariable = len(
            [1 for prior in xprior if prior is None or prior["type"] != "Fixed"]
        )
        if nXpriorVariable != nVariableInputs:
            error = (
                'RSAnalyzer: In function parsePrior(), "xprior" is expected to be a list of length %d.'
                % nVariableInputs
            )
            Common.showError(error)
            return None
        else:
            inputLB = SampleData.getInputMins(data)
            inputUB = SampleData.getInputMaxs(data)
            dist = list(SampleData.getInputDistributions(data))
            priorIndex = 0
            for i in range(nInputs):
                if inVarTypes[i] == Model.VARIABLE:
                    prior = xprior[priorIndex]
                    if prior is not None and prior["type"] != "Fixed":
                        pdf = prior["pdf"]
                        # ... assume prior specification has already been validated
                        if pdf == Distribution.UNIFORM:
                            vmin = prior["min"]
                            vmax = prior["max"]
                            if vmin < inputLB[i]:
                                error = (
                                    "RSAnalyzer WARNING: In function parsePrior(), minimum value for %s needs to equal or greater than %f (%f)."
                                    % (inVarNames[i], inputLB[i], vmin)
                                )
                                # Charles Tong (Feb 2017)
                                # disable for now because the prior[''] function
                                # only takes limited number of digits so it may
                                # send out erroneous results ==> no checking
                                # Common.showError(error)
                                # return None
                            if vmax > inputUB[i]:
                                error = (
                                    "RSAnalyzer WARNING: In function parsePrior(), maximum value for %s needs to equal or less than %f (%f)."
                                    % (inVarNames[i], inputUB[i], vmax)
                                )
                                # Common.showError(error)
                                # return None
                            # ... set new bounds for uniform random variables only
                            inputLB[i] = vmin
                            inputUB[i] = vmax
                            prior["param1"] = None
                            prior["param2"] = None
                        d = Distribution(pdf)
                        d.setParameterValues(prior["param1"], prior["param2"])
                        dist[i] = d
                    priorIndex = priorIndex + 1

        return {"inputLB": inputLB, "inputUB": inputUB, "dist": dist}

    @staticmethod
    def checkMARS(data, rsOptions):
        if rsOptions is not None:
            nSamples = SampleData.getNumSamples(data)
            if nSamples < 12:
                error = 'RSAnalyzer ERROR: In function checkMARS(), "nSamples" needs to be > 11 to work.'
                Common.showError(error)
                return None
            inVarTypes = SampleData.getInputTypes(data)
            nVariableInputs = inVarTypes.count(Model.VARIABLE)
            marsBases = rsOptions["marsBases"]
            if marsBases < 10 or marsBases > nSamples:
                error = 'RSAnalyzer WARNING: In function checkMARS(), "marsBases" is out of range for MARS response surface (will reset).'
                Common.showError(error)
                marsBases = nSamples
                # return None
            marsInteractions = rsOptions["marsInteractions"]
            if marsInteractions < 2 or marsInteractions > nVariableInputs:
                error = 'RSAnalyzer WARNING: In function checkMARS(), "marsInteractions" is out of range for MARS response surface.'
                Common.showError(error)
                # return None
                marsInteractions = nVariableInputs
            marsNormOutputs = "n"
            return (marsBases, marsInteractions, marsNormOutputs)
        return None

    @staticmethod
    def validateRS(
        fname,
        y,
        rsMethodName,
        rsOptions=None,
        genCodeFile=False,
        nCV=None,
        userRegressionFile=None,
        testfile=None,
        error_tol_percent=10,
    ):

        # read data
        data = LocalExecutionModule.readSampleFromPsuadeFile(
            fname
        )  # does not assume rstype/order written to data
        rsIndex = ResponseSurfaces.getEnumValue(rsMethodName)

        userMethod = False
        setMARS = False
        if rsIndex == ResponseSurfaces.LEGENDRE:  # require order for LEGENDRE RS
            if rsOptions is not None:
                if isinstance(rsOptions, dict):
                    legendreOrder = rsOptions["legendreOrder"]
                else:
                    legendreOrder = rsOptions
            else:
                error = 'RSAnalyzer: In function validateRS(), "legendreOrder" is required for LEGENDRE response surface.'
                Common.showError(error)
                return None
        elif (
            rsIndex == ResponseSurfaces.USER
        ):  # require user regression file for USER REGRESSION RS
            if userRegressionFile is not None:
                userMethod = True
            else:
                error = 'RSAnalyzer: In function validateRS(), "userRegressionFile" is required for USER REGRESSION response surface.'
                Common.showError(error)
                return None
        elif rsIndex in [
            ResponseSurfaces.MARS,
            ResponseSurfaces.MARSBAG,
        ]:  # check for MARS options
            if rsOptions is not None:
                marsOptions = RSAnalyzer.checkMARS(data, rsOptions)
                if marsOptions is not None:
                    marsBases, marsInteractions, marsNormOutputs = marsOptions
                    setMARS = True

        # write script
        f = tempfile.SpooledTemporaryFile(mode="wt")
        if platform.system() == "Windows":
            import win32api

            fname = win32api.GetShortPathName(fname)

        f.write("load %s\n" % fname)
        if genCodeFile:
            f.write("rs_codegen\n")

        if userMethod:  # ... user regression ...
            if testfile is None:
                dname = RSAnalyzer.dname
                if platform.system() == "Windows":
                    dname = win32api.GetShortPathName(dname)
                fnameTest = Common.getLocalFileName(dname, fname, ".testdat")
            else:
                fnameTest = testfile
                if platform.system() == "Windows":
                    fnameTest = win32api.GetShortPathName(fnameTest)
            # if no test data is given, use training data
            if testfile is None:
                f.write("write %s\n" % fnameTest)  # write 1-output test data file
                nOutputs = SampleData.getNumOutputs(data)
                if nOutputs > 1:
                    f.write("y\n")  # write one output
                    f.write("%d\n" % y)  # select output
                f.write("load %s\n" % fname)  # reload file
            cmd = "rstest"
            f.write("%s\n" % cmd)
            f.write("%s\n" % fnameTest)  # test data file
            f.write("%d\n" % y)  # select output
            f.write("%d\n" % rsIndex)  # select response surface
            f.write("n\n")  # no discrepancy file
            f.write("1\n")  # number of basis functions
            if platform.system() == "Windows":
                userRegressionFile = win32api.GetShortPathName(userRegressionFile)
            f.write("%s\n" % userRegressionFile)  # driver file
            f.write("y\n")  # apply auxillary arg (output name)
            outVarNames = data.getOutputNames()
            outName = outVarNames[y - 1]
            outName = Common.getUserRegressionOutputName(
                outName, userRegressionFile, data
            )
            f.write("%s\n" % outName)  # output name
            mfile = "RSTest_hs.m"

        else:  # ... standard ...
            if setMARS:
                f.write("rs_expert\n")
            cmd = "rscheck"
            f.write("%s\n" % cmd)
            f.write("%d\n" % rsIndex)  # select response surface
            f.write("%d\n" % y)  # select output
            if rsIndex == ResponseSurfaces.LEGENDRE:
                f.write("%d\n" % legendreOrder)
            elif setMARS:
                f.write("0\n")  # no transformations on input/output
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
            f.write("y\n")  # select yes for cross-validation (CV)
            nSamples = SampleData.getNumSamples(data)
            if (nCV is None) or (math.floor(nCV) > nSamples):
                nCV = min(nSamples, 10)  # default number of cross-validation groups
            f.write("%d\n" % nCV)  # number of groups to validate
            if setMARS:
                if rsIndex == ResponseSurfaces.MARSBAG:
                    f.write("0\n")  # mean (0) or median (1) mode
                    f.write(
                        "100\n"
                    )  # number of MARS instantiations [range:10-5000, default=100]
                    ### TO DO: revert back to 100 for deployment
                nSamplesCV = math.floor(
                    nSamples / nCV
                )  # number of samples in each CV group
                marsBasesCV = min(marsBases, nSamples - nSamplesCV)
                f.write("%d\n" % marsBasesCV)
                f.write("%d\n" % marsInteractions)
            f.write("y\n")  # select yes for random selection of leave-out groups
            if rsIndex == ResponseSurfaces.LEGENDRE:
                f.write("%d\n" % legendreOrder)
            mfile = "RSFA_CV_err.m"
        f.write("quit\n")
        f.seek(0)

        # for line in f:
        #    print line
        # f.seek(0)

        # invoke psuade
        out, error = Common.invokePsuade(f)
        f.close()
        if error:
            return None

        testErrors = None
        trainErrors = None
        cvErrors = None
        if userMethod:  # ... user regression ...
            # parse output for prediction errors on test set
            mres = re.findall(r"Prediction errors\s*=\s*(\S*)", out)
            if len(mres) == 6:
                testErrors = {
                    "max_unscaled": mres[0],
                    "max_scaled": mres[1],
                    "rms_unscaled": mres[2],
                    "rms_scaled": mres[3],
                    "avg_unscaled": mres[4],
                    "avg_scaled": mres[5],
                }

        else:  # ... standard ...
            # parse output for interpolation errors on training set
            mres = re.findall(r"avg error\s*=\s*(\S*)", out)
            mres.extend(re.findall(r"rms error\s*=\s*(\S*)", out))
            mres.extend(re.findall(r"max error\s*=\s*(\S*)", out))
            mres.extend(re.findall(r"R-square    =\s*(\S*)", out))
            if len(mres) == 7:
                trainErrors = {
                    "avg_unscaled": mres[0],
                    "avg_scaled": mres[1],
                    "rms_unscaled": mres[2],
                    "rms_scaled": mres[3],
                    "max_unscaled": mres[4],
                    "max_scaled": mres[5],
                    "R-square": mres[6],
                }
            # parse output for cross validation errors
            mres = re.findall(r"final CV error\s*=\s*(\S*)", out)
            if len(mres) == 6:
                cvErrors = {
                    "avg_unscaled": mres[0],
                    "avg_scaled": mres[1],
                    "rms_unscaled": mres[2],
                    "rms_scaled": mres[3],
                    "max_unscaled": mres[4],
                    "max_scaled": mres[5],
                }

        # check output file
        if os.path.exists(mfile):
            mfile_ = RSAnalyzer.dname + os.path.sep + mfile
            if os.path.exists(mfile_):
                os.remove(mfile_)
            os.rename(mfile, mfile_)
            mfile = mfile_
        else:
            error = "RSAnalyzer: %s does not exist." % mfile
            Common.showError(error, out)
            return None

        RSAnalyzer.plotValidate(
            data, y, rsMethodName, userMethod, mfile, error_tol_percent
        )

        return (mfile, trainErrors, cvErrors, testErrors)

    @staticmethod
    def plotValidate(data, y, rsMethodName, userMethod, mfile, error_tol_percent=10):
        outVarNames = data.getOutputNames()
        outVarName = outVarNames[y - 1]
        if userMethod:  # ... user regression ...
            datvar = "E"
            dat_ = Plotter.getdata(mfile, datvar)
            indices = [2, 1, 0, 4]  # reshuffle E's columns to be consistent with A's
            dat = dat_[:, indices]
        else:  # ... standard ...
            datvar = "A"
            dat = Plotter.getdata(mfile, datvar)
        ftitle = "Model Validation of %s Response Surface for %s" % (
            rsMethodName.upper(),
            outVarName.upper(),
        )
        ptitle = ["Model Error Histogram", "Actual vs. Predicted Data"]
        xlabel = ["Model Errors", "Actual Data for %s" % outVarName]
        ylabel = ["Probabilities", "Predicted Data for %s" % outVarName]
        Plotter.plotRSvalidate(
            dat, ftitle, ptitle, xlabel, ylabel, error_tol_percent=error_tol_percent
        )

        return None

    @staticmethod
    def writeRSsample(fname, x, y=None, row=False, sdoe=False):

        d = " "
        nSamples, nInputs = x.shape
        if sdoe:
            header = "PSUADE_BEGIN\n%d %d" % (nSamples, nInputs)
            footer = "PSUADE_END"
        else:
            header = "%d %d" % (nSamples, nInputs)
            footer = ""
        z = x
        if row:
            z = np.concatenate((np.arange(1, nSamples + 1)[:, np.newaxis], x), axis=1)
            format = "%i"
            for i in range(nInputs):
                format += " %1.18e"
        if y is not None:
            nOutputs = y.shape[1]
            header = "%d %d %d" % (nSamples, nInputs, nOutputs)
            z = np.concatenate((x, y), axis=1)
        if row:
            np.savetxt(
                fname,
                z,
                header=header,
                comments="",
                delimiter=d,
                fmt=format,
                footer=footer,
            )
        else:
            np.savetxt(fname, z, header=header, comments="", delimiter=d, footer=footer)

        return None

    @staticmethod
    def readRSsample(fname):

        f = open(fname, "r")
        lines = f.readlines()
        f.close()

        # ignore text preceded by '%'
        c = "%"
        lines = [line.strip().split(c)[0] for line in lines if not line.startswith(c)]
        nlines = len(lines)

        # process header
        k = 0
        header = lines[k]
        nums = header.split()
        numSamples = int(nums[0])
        numInputs = int(nums[1])
        numOutputs = 0
        if len(nums) == 3:
            numOutputs = int(nums[2])

        # process samples
        data = [None] * numSamples
        for i in range(nlines - k - 1):
            line = lines[i + k + 1]
            nums = line.split()
            data[i] = [float(x) for x in nums]

        # split samples
        data = np.array(data)
        inputData = data[:, 0:numInputs]
        inputArray = np.array(inputData, dtype=float, ndmin=2)
        outputArray = None
        if numOutputs:
            outputData = data[:, numInputs:]
            outputArray = np.array(outputData, dtype=float, ndmin=2)

        return (inputArray, outputArray)

    @staticmethod
    def processRSdata(
        fnameRS, y, data, rsMethodName, rsOptions=None, xprior=None, indexfile=None
    ):

        # process input prior
        inputLB = None
        inputUB = None
        dist = None
        if xprior is not None:
            p = RSAnalyzer.parsePrior(data, xprior)
            if p is not None:
                inputLB = p["inputLB"]
                inputUB = p["inputUB"]
                dist = p["dist"]

        # process index file
        ifile = None
        if indexfile is not None:
            ifile = indexfile

        # write rstype (and order if applicable) to data file (required for UA and SA analyses)
        rsIndex = ResponseSurfaces.getEnumValue(rsMethodName)
        if rsIndex == ResponseSurfaces.LEGENDRE and rsOptions is not None:
            if isinstance(rsOptions, dict):
                legendreOrder = rsOptions["legendreOrder"]
            else:
                legendreOrder = rsOptions
            outfile = RSAnalyzer.writeRSdata(
                fnameRS,
                y,
                data,
                rsMethod=rsMethodName,
                legendreOrder=legendreOrder,
                inputLowerBounds=inputLB,
                inputUpperBounds=inputUB,
                inputPDF=dist,
                indexfile=ifile,
            )
        else:
            outfile = RSAnalyzer.writeRSdata(
                fnameRS,
                y,
                data,
                rsMethod=rsMethodName,
                inputLowerBounds=inputLB,
                inputUpperBounds=inputUB,
                inputPDF=dist,
                indexfile=ifile,
            )
        if outfile is None:
            error = (
                "RSAnalyzer: In function processRSdata(), %s is not written." % fnameRS
            )
            Common.showError(error)
            return None

        # operate on the new data file
        rsdata = LocalExecutionModule.readSampleFromPsuadeFile(fnameRS)

        return rsdata

    @staticmethod
    def pointEval(
        fname, xtest, y, rsMethodName, rsOptions=None, userRegressionFile=None
    ):
        ### xtest should be an array of length N, where N is the number of variable inputs.
        ### xtest[i] should be a single-key dictionary: {'value':%f}

        # read data
        data = LocalExecutionModule.readSampleFromPsuadeFile(
            fname
        )  # does not assume rstype/order written to data
        rsIndex = ResponseSurfaces.getEnumValue(rsMethodName)

        userMethod = False
        setMARS = False
        if rsIndex == ResponseSurfaces.LEGENDRE:  # require order for LEGENDRE RS
            if rsOptions is not None:
                if isinstance(rsOptions, dict):
                    legendreOrder = rsOptions["legendreOrder"]
                else:
                    legendreOrder = rsOptions
            else:
                error = 'RSAnalyzer: In function pointEval(), "legendreOrder" is required for LEGENDRE response surface.'
                Common.showError(error)
                return None
        elif (
            rsIndex == ResponseSurfaces.USER
        ):  # require user regression file for USER REGRESSION RS
            if userRegressionFile is not None:
                userMethod = True
            else:
                error = 'RSAnalyzer: In function pointEval(), "userRegressionFile" is required for USER REGRESSION response surface.'
                Common.showError(error)
                return None
        elif rsIndex in [
            ResponseSurfaces.MARS,
            ResponseSurfaces.MARSBAG,
        ]:  # check for MARS options
            if rsOptions is not None:
                marsOptions = RSAnalyzer.checkMARS(data, rsOptions)
                if marsOptions is not None:
                    marsBases, marsInteractions, marsNormOutputs = marsOptions
                    setMARS = True

        # write script
        f = tempfile.SpooledTemporaryFile(mode="wt")
        if platform.system() == "Windows":
            import win32api

            fname = win32api.GetShortPathName(fname)

        f.write("load %s\n" % fname)  # load data
        if setMARS:
            f.write("rs_expert\n")
        cmd = "rscreate"
        f.write("%s\n" % cmd)
        nOutputs = data.getNumOutputs()
        if nOutputs > 1:
            f.write("%d\n" % y)  # select output
        f.write("%d\n" % rsIndex)  # select response surface
        if userMethod:  # ... user regression ...
            f.write("1\n")  # number of basis functions
            if platform.system() == "Windows":
                userRegressionFile = win32api.GetShortPathName(userRegressionFile)
            f.write("%s\n" % userRegressionFile)  # driver file
            f.write("y\n")  # apply auxillary arg (output name)
            outVarNames = data.getOutputNames()
            outName = outVarNames[y - 1]
            if data.getNamesIncludeNodes():
                index = outName.index(".")
                outName = outName[index + 1 :]
            f.write("%s\n" % outName)  # output name
        else:  # ... standard ...
            if rsIndex == ResponseSurfaces.LEGENDRE:
                f.write("%d\n" % legendreOrder)
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
        cmd = "ivec_create"  # create input vector
        f.write("%s\n" % cmd)
        cmd = "ivec_modify"  # instantiate input vector
        for i in range(len(xtest)):
            f.write("%s\n" % cmd)
            f.write("%d\n" % (i + 1))
            f.write("%f\n" % xtest[i]["value"])
        cmd = "ivec_show"
        f.write("%s\n" % cmd)  # show input vector
        cmd = "rseval"
        f.write("%s\n" % cmd)
        f.write("n\n")  # data taken from register
        f.write("y\n")  # do fuzzy evaluation
        f.write("n\n")  # do not write data to file
        f.write("quit\n")
        f.seek(0)

        # invoke psuade
        out, error = Common.invokePsuade(f)
        f.close()
        if error:
            return None

        # parse output for prediction
        ytest = []
        mres = re.findall(r"Interpolated Point\s*\d*:\s*output\s*\d*\s*=\s*(\S*)", out)
        if mres:
            ytest.append(mres[0])
        mres = re.findall(r"stdev\s*=\s*(\S*)", out)
        if mres:
            ytest.append(mres[0][:-1])  # skip last character, which is a parenthesis

        return ytest

    @staticmethod
    def performUA(
        fname, y, rsMethodName, rsOptions=None, userRegressionFile=None, xprior=None
    ):

        ### xprior should be an array of length N, where N is the number of variable inputs.
        ### xprior[i] should contain the following fields: {'min':%f, 'max':%f, 'pdf':%d, 'param1':%f, 'param2':%f}

        # read data
        data = LocalExecutionModule.readSampleFromPsuadeFile(
            fname
        )  # does not assume rstype/order written to data

        # process RS data
        dname = RSAnalyzer.dname
        if platform.system() == "Windows":
            import win32api

            dname = win32api.GetShortPathName(dname)
        fnameRS = Common.getLocalFileName(dname, fname, ".rsdat")
        data = RSAnalyzer.processRSdata(
            fnameRS, y, data, rsMethodName, rsOptions=rsOptions, xprior=xprior
        )
        rsIndex = data.getSampleRSType()

        # check for MARS options
        setMARS = False
        if rsIndex in [ResponseSurfaces.MARS, ResponseSurfaces.MARSBAG]:
            marsOptions = RSAnalyzer.checkMARS(data, rsOptions)
            if marsOptions is not None:
                marsBases, marsInteractions, marsNormOutputs = marsOptions
                setMARS = True

        # write script
        cmd = "rs_ua"
        f = tempfile.SpooledTemporaryFile(mode="wt")
        if platform.system() == "Windows":
            fnameRS = win32api.GetShortPathName(fnameRS)
        f.write("load %s\n" % fnameRS)
        if setMARS:
            f.write("rs_expert\n")
        f.write("%s\n" % cmd)
        f.write("%d\n" % y)  # select output
        f.write(
            "10000\n"
        )  # sample size for generating distribution [range: 10000-100000]
        f.write("y\n")  # save generated sample in a file

        if rsIndex == ResponseSurfaces.LEGENDRE:
            legendreOrder = data.getLegendreOrder()
            f.write("%d\n" % legendreOrder)  # Legendre order
        elif rsIndex == ResponseSurfaces.USER and userRegressionFile is not None:
            f.write("1\n")  # number of basis functions
            if platform.system() == "Windows":
                userRegressionFile = win32api.GetShortPathName(userRegressionFile)
            f.write("%s\n" % userRegressionFile)  # driver file
            f.write("y\n")  # apply auxillary arg (output name)
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
        f.write("quit\n")
        f.seek(0)
        #       for line in f.readlines():
        #           print line
        #       f.seek(0)

        # invoke psuade
        out, error = Common.invokePsuade(f)
        f.close()
        if error:
            return None

        # check output files
        mfile = "matlabrsua.m"
        if os.path.exists(mfile):
            mfile_ = RSAnalyzer.dname + os.path.sep + mfile
            if os.path.exists(mfile_):
                os.remove(mfile_)
            os.rename(mfile, mfile_)
            mfile = mfile_
        else:
            error = "RSAnalyzer: %s does not exist." % mfile
            Common.showError(error, out)
            return None
        sfile = "rsua_sample"
        if os.path.exists(sfile):
            sfile_ = RSAnalyzer.dname + os.path.sep + sfile
            if os.path.exists(sfile_):
                os.remove(sfile_)
            os.rename(sfile, sfile_)
            sfile = sfile_
        else:
            error = "RSAnalyzer: %s does not exist." % sfile
            Common.showError(error, out)
            return None

        RSAnalyzer.plotUA(data, y, rsMethodName, sfile, mfile)

        return (sfile, mfile)

    @staticmethod
    def plotUA(data, y, rsMethodName, sfile, mfile):

        outVarNames = data.getOutputNames()

        # read sample file
        indat, outdat = RSAnalyzer.readRSsample(sfile)
        rsdat0 = outdat[:, 0]  # output
        rserr = (outdat[:, 0] - outdat[:, 1]) / 3  # sigma
        nSamples = len(rsdat0)

        # generate an ensemble of outputs based on RS uncertainty
        rsdat = []
        rsdat.append(outdat[:, 1])  # output-3*sigma
        rsdat.append(rsdat0 - 2 * rserr)  # output-2*sigma
        rsdat.append(rsdat0 - rserr)  # output-sigma
        rsdat.append(rsdat0)  # output
        rsdat.append(rsdat0 + rserr)  # output+sigma
        rsdat.append(rsdat0 + 2 * rserr)  # output+2*sigma
        rsdat.append(outdat[:, 2])  # output+3*sigma

        # compute moments from outputs generated from mean PDF
        fmt = "%1.4e"
        moments = {
            "mean": fmt % np.mean(rsdat0),
            "std": fmt % np.std(rsdat0),
            "skew": fmt % stats.skew(rsdat0),
            "kurt": fmt % (stats.kurtosis(rsdat0, bias=False) + 3),
        }

        # generate samples from each output
        ns = 50  # number of samples to be drawn from each output
        ysamples = []
        for i in range(nSamples):
            m = rsdat0[i]
            if rserr[i] > 0:
                ys = np.random.normal(loc=m, scale=rserr[i], size=ns)
            else:
                ys = [m] * ns
            ysamples.append(ys)
        ysamples = np.array(ysamples)
        ysamples = ysamples.flatten()

        # transform ensemble outputs into PDF (this should have wider spread than that of mean outputs)
        ydat = []
        nbins = 100
        bheights, bedges = np.histogram(ysamples, bins=nbins)
        bheights_normed = bheights / float(len(ysamples))
        ydat.append(bheights_normed)
        xdat = bedges[:-1]

        # transform mean outputs into PDF
        bheights, bedges = np.histogram(
            rsdat0, bins=bedges
        )  # use the same bin edges as before
        bheights_normed = bheights / float(nSamples)
        ydat.append(bheights_normed)
        ydat = np.array(ydat)

        # transform ensemble outputs into PDFs
        pdfs = []
        for d in rsdat:
            bheights, bedges = np.histogram(
                d, bins=bedges
            )  # use the same bin edges as before
            bheights_normed = bheights / float(nSamples)
            pdfs.append(bheights_normed)

        # plot
        outVarName = outVarNames[y - 1]
        ftitle = "Uncertainty Analysis"
        ftitle = "%s based on %s Response Surface" % (ftitle, rsMethodName.upper())
        ptitle = "Probability Distribution for %s" % outVarName
        xlabel = outVarName
        ylabel = "Probabilities"
        Plotter.plotpdf(xdat, ydat, moments, pdfs, ftitle, ptitle, xlabel, ylabel)

        return None

    @staticmethod
    def performAEUA(
        fname, y, rsMethodName, rsOptions=None, userRegressionFile=None, xtable=None
    ):

        ### xtable should be an array of length N, where N is the number of variable inputs.
        ### xtable[i] should contain the following fields: {'type':%s, 'value':%s, 'min':%f, 'max':%f, 'pdf':%d, 'param1':%f, 'param2':%f}

        # if table is not provided, then epistemic variables cannot be identified, so revert to standard UA
        if xtable is None:
            warn = "RSAnalyzer: In function performAEUA(), no epistemic variables are designated... reverting to performUA().\n"
            Common.showError(warn)
            return RSAnalyzer.performUA(
                fname,
                y,
                rsMethodName,
                rsOptions=rsOptions,
                userRegressionFile=userRegressionFile,
            )

        # read data
        data = LocalExecutionModule.readSampleFromPsuadeFile(
            fname
        )  # does not assume rstype/order written to data

        # process input prior info
        inputTypes = data.getInputTypes()
        nVariableInputs = inputTypes.count(Model.VARIABLE)
        # ... get epistemic inputs
        epistemicInVars = [
            i + 1 for i, e in enumerate(xtable) if e["type"] == "Epistemic"
        ]
        nEpistemic = len(epistemicInVars)
        if nEpistemic == 0:
            warn = "RSAnalyzer: In function performAEUA(), no epistemic variables are designated... reverting to performUA().\n"
            Common.showError(warn)
            return RSAnalyzer.performUA(
                fname,
                y,
                rsMethodName,
                rsOptions=rsOptions,
                userRegressionFile=userRegressionFile,
            )
        # ... get aleatory inputs
        aleatoryInVars = [
            i + 1 for i, e in enumerate(xtable) if e["type"] == "Aleatory"
        ]
        nAleatory = len(aleatoryInVars)
        if nAleatory == 0:
            error = "RSAnalyzer: In function performAEUA(), no aleatory variables are designated.\n"
            Common.showError(error)
            return None
        # ... get fixed inputs
        fixedInVars = [i + 1 for i, e in enumerate(xtable) if e["type"] == "Fixed"]
        indexfile = None
        if fixedInVars:
            # ... write index file based on fixed inputs
            indexfile = RSAnalyzer.dname + os.path.sep + "indexfile"
            f = open(indexfile, "w")
            f.write("%d\n" % nVariableInputs)
            for i in range(nVariableInputs):
                k = i + 1
                e = xtable[i]
                if e["type"] == "Fixed":
                    f.write("%d %d %f\n" % (k, 0, e["value"]))
            f.close()
        # ... nullify xtable's entries corresponding to fixed inputs
        for i in range(nVariableInputs):
            e = xtable[i]
            if e["type"] == "Fixed":
                xtable[i] = None
        # ... write out RS data file with only variable inputs' prior info
        fnameRS = Common.getLocalFileName(RSAnalyzer.dname, fname, ".rsdat")
        data = RSAnalyzer.processRSdata(
            fnameRS,
            y,
            data,
            rsMethodName,
            rsOptions=rsOptions,
            xprior=xtable,
            indexfile=indexfile,
        )
        rsIndex = data.getSampleRSType()

        # check for MARS options
        setMARS = False
        if rsIndex in [ResponseSurfaces.MARS, ResponseSurfaces.MARSBAG]:
            marsOptions = RSAnalyzer.checkMARS(data, rsOptions)
            if marsOptions is not None:
                marsBases, marsInteractions, marsNormOutputs = marsOptions
                setMARS = True

        # write script
        cmd = "aeua"
        f = tempfile.SpooledTemporaryFile(mode="wt")
        if platform.system() == "Windows":
            import win32api

            fnameRS = win32api.GetShortPathName(fnameRS)
        f.write("load %s\n" % fnameRS)
        if setMARS:
            f.write("rs_expert\n")
        f.write("%s\n" % cmd)
        f.write("%d\n" % y)  # select output
        if rsIndex == ResponseSurfaces.LEGENDRE:
            legendreOrder = data.getLegendreOrder()
            f.write("%d\n" % legendreOrder)  # Legendre order
        elif rsIndex == ResponseSurfaces.USER and userRegressionFile is not None:
            f.write("1\n")  # number of basis functions
            if platform.system() == "Windows":
                userRegressionFile = win32api.GetShortPathName(userRegressionFile)
            f.write("%s\n" % userRegressionFile)  # driver file
            f.write("y\n")  # apply auxillary arg (output name)
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
        for e in epistemicInVars:
            f.write("%d\n" % e)  # select epistemic inputs
        f.write("0\n")  # done with epistemic inputs
        f.write("quit\n")
        f.seek(0)

        # invoke psuade
        out, error = Common.invokePsuade(f)
        f.close()
        if error:
            return None

        # check output files
        mfile = "matlabaeua.m"
        if os.path.exists(mfile):
            mfile_ = RSAnalyzer.dname + os.path.sep + mfile
            if os.path.exists(mfile_):
                os.remove(mfile_)
            os.rename(mfile, mfile_)
            mfile = mfile_
        else:
            error = "RSAnalyzer: %s does not exist." % mfile
            Common.showError(error, out)
            return None

        RSAnalyzer.plotAEUA(data, y, rsMethodName, mfile)

        return mfile

    @staticmethod
    def plotAEUA(data, y, rsMethodName, mfile):
        outVarNames = data.getOutputNames()

        P = 50  # number of cdfs
        datvars = ["Y%d" % i for i in range(1, P + 1)]
        datvars.extend(["YU", "YL"])
        cdfs = []
        for d in datvars:
            cdf = np.sort(Plotter.getdata(mfile, d))
            cdfs.append(cdf)

        # plot
        outVarName = outVarNames[y - 1]
        ftitle = "Mixed Aleatory-Epistemic Uncertainty Analysis"
        ftitle = "%s based on %s Response Surface" % (ftitle, rsMethodName.upper())
        ptitle = "Cumulative Distributions for %s" % outVarName
        xlabel = outVarName
        ylabel = "Probabilities"
        Plotter.plotcdf(cdfs, ftitle, ptitle, xlabel, ylabel)

        return None

    @staticmethod
    def performSA(
        fname,
        y,
        cmd,
        showErrorBars,
        rsMethodName,
        rsOptions=None,
        userRegressionFile=None,
        xprior=None,
    ):

        ### xprior should be an array of length N, where N is the number of variable inputs.
        ### xprior[i] should contain the following fields: {'min':%f, 'max':%f, 'pdf':%d, 'param1':%f, 'param2':%f}

        # change to MARS if bootstrapped SA method is selected for bagged MARS sample
        if showErrorBars and rsMethodName == "MARSBAG":
            rsMethodName = "MARS"
            warn = (
                "RSAnalyzer: In function performSA(), MARSBAG ensemble treated as MARS ensemble for %s analysis."
                % cmd.upper()
            )
            Common.showError(warn)

        # read data
        data = LocalExecutionModule.readSampleFromPsuadeFile(
            fname
        )  # does not assume rstype/order written to data

        # process RS data
        dname = RSAnalyzer.dname
        if platform.system() == "Windows":
            import win32api

            dname = win32api.GetShortPathName(dname)
        fnameRS = Common.getLocalFileName(dname, fname, ".rsdat")
        data = RSAnalyzer.processRSdata(
            fnameRS, y, data, rsMethodName, rsOptions=rsOptions, xprior=xprior
        )
        rsIndex = data.getSampleRSType()

        # for bootstrapped SA method, aappend 'b' to cmd
        cmd_ = cmd
        if showErrorBars:
            cmd = cmd + "b"

        # check for MARS options
        setMARS = False
        if rsIndex in [ResponseSurfaces.MARS, ResponseSurfaces.MARSBAG]:
            marsOptions = RSAnalyzer.checkMARS(data, rsOptions)
            if marsOptions is not None:
                marsBases, marsInteractions, marsNormOutputs = marsOptions
                setMARS = True

        # write script
        f = tempfile.SpooledTemporaryFile(mode="wt")
        if platform.system() == "Windows":
            fnameRS = win32api.GetShortPathName(fnameRS)
        f.write("load %s\n" % fnameRS)
        if setMARS:
            f.write("rs_expert\n")
        f.write("%s\n" % cmd)
        f.write("%d\n" % y)  # select output
        nBootstrap = 1
        if showErrorBars:
            nBootstrap = 50
            f.write("%d\n" % nBootstrap)  # number of bootstrapped samples
            ### TO DO: revert to 50 at deployment
        if setMARS:
            if showErrorBars:
                # for bootstrap SA: MARSBAG -> MARS
                for i in range(nBootstrap):
                    nSamples = data.getNumSamples()
                    nSamplesBS = math.floor(
                        0.5 * nSamples
                    )  # number of samples in each bootstrap group
                    # This is the number of unique samples drawn with replacement
                    # which should statistically be 60% of sample size.
                    marsBasesBS = min(marsBases, nSamplesBS)
                    f.write("%d\n" % marsBasesBS)
                    f.write("%d\n" % marsInteractions)
                    f.write("%s\n" % marsNormOutputs)
            else:
                if rsIndex == ResponseSurfaces.MARSBAG:
                    f.write("0\n")  # mean (0) or median (1) mode
                    f.write(
                        "100\n"
                    )  # number of MARS instantiations [range:10-5000, default=100]
                    ### TO DO: revert to 100 at deployment
                f.write("%d\n" % marsBases)
                f.write("%d\n" % marsInteractions)
                if rsIndex == ResponseSurfaces.MARS:
                    f.write("%s\n" % marsNormOutputs)

        if rsIndex == ResponseSurfaces.USER and userRegressionFile is not None:
            outVarNames = data.getOutputNames()
            for i in range(nBootstrap):
                f.write("1\n")  # number of basis functions
                if platform.system() == "Windows":
                    userRegressionFile = win32api.GetShortPathName(userRegressionFile)
                f.write("%s\n" % userRegressionFile)  # driver file
                f.write("y\n")  # apply auxillary arg (output name)
                outName = outVarNames[y - 1]
                outName = Common.getUserRegressionOutputName(
                    outName, userRegressionFile, data
                )
                f.write("%s\n" % outName)  # output name

        f.write("quit\n")
        f.seek(0)

        # invoke psuade
        out, error = Common.invokePsuade(f)
        f.close()
        if error:
            return None

        # check output file
        mfile = "matlab" + cmd + ".m"
        if os.path.exists(mfile):
            mfile_ = RSAnalyzer.dname + os.path.sep + mfile
            if os.path.exists(mfile_):
                os.remove(mfile_)
            os.rename(mfile, mfile_)
            mfile = mfile_
            mfile0 = "matlab" + cmd_ + ".m"  # extra file generated by psuade
            if showErrorBars and os.path.exists(mfile0):
                mfile0_ = RSAnalyzer.dname + os.path.sep + mfile0
                if os.path.exists(mfile0_):
                    os.remove(mfile0_)
                os.rename(mfile0, mfile0_)
        else:
            error = "RSAnalyzer: %s does not exist." % mfile
            Common.showError(error, out)
            return None

        RSAnalyzer.plotSA(data, y, rsMethodName, cmd_, showErrorBars, mfile)

        return mfile

    @staticmethod
    def plotSA(data, y, rsMethodName, cmd_, showErrorBars, mfile):
        outVarNames = SampleData.getOutputNames(data)

        if showErrorBars:
            datvar = ["Means", "Stds"]
            dat = Plotter.getdata(mfile, datvar[0])
            std = Plotter.getdata(mfile, datvar[1])
        else:
            datvar = "Mids"
            dat = Plotter.getdata(mfile, datvar)
            std = None
        figtitle = {
            "rssobol1": "First-order",
            "rssobol2": "Second-order",
            "rssoboltsi": "Total-order",
        }
        title = {
            "rssobol1": "Sobol First Order Indices",
            "rssobol2": "Sobol First and Second Order Indices",
            "rssoboltsi": "Sobol Total Order Indices",
        }
        ylabel = "Sobol Indices"
        xlabel = "Input Parameters"
        xticklabels = []
        inputNames = data.getInputNames()
        inputTypes = data.getInputTypes()
        for name, inType in zip(inputNames, inputTypes):
            if inType == Model.VARIABLE:
                xticklabels.append(name)

        outVarName = outVarNames[y - 1]
        ftitle = "%s Sensitivity Analysis based on %s Response Surface" % (
            figtitle[cmd_],
            rsMethodName.upper(),
        )
        ptitle = "%s for %s" % (title[cmd_], outVarName)
        if cmd_ == "rssobol2":
            L = len(dat)
            M = int(math.sqrt(L))
            dat = np.reshape(dat, [M, M], order="F")
            if std is not None:
                std = np.reshape(std, [M, M], order="F")
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

        return None

    @staticmethod
    def emulate(
        fnameRS,
        fnameInputSamples,
        y,
        textDialog=None,
        dialogShowSignal=None,
        dialogCloseSignal=None,
        textInsertSignal=None,
        ensureVisibleSignal=None,
    ):

        ### TO DO: implement rsOptions for emulate() to allow RS customization

        # delete all outputs except for 'y' in training data
        dname = RSAnalyzer.dname
        if platform.system() == "Windows":
            import win32api

            dname = win32api.GetShortPathName(dname)
        fnameTrain = Common.getLocalFileName(dname, fnameRS, ".traindat")
        # ... write script
        f = tempfile.SpooledTemporaryFile(mode="wt")
        if platform.system() == "Windows":
            fnameRS = win32api.GetShortPathName(fnameRS)
        f.write("load %s\n" % fnameRS)
        f.write("write %s\n" % fnameTrain)
        f.write("y\n")  # save one output
        f.write("%d\n" % y)  # select output
        f.write("quit\n")
        f.seek(0)
        # ... invoke psuade
        out, error = Common.invokePsuade(
            f,
            textDialog=textDialog,
            dialogShowSignal=dialogShowSignal,
            dialogCloseSignal=dialogCloseSignal,
            textInsertSignal=textInsertSignal,
            ensureVisibleSignal=ensureVisibleSignal,
        )
        f.close()

        # process error
        if error:
            return None

        if not os.path.exists(fnameTrain):
            error = "RSAnalyzer: %s does not exist." % fnameTrain
            Common.showError(error, out)
            return None

        # read traindata
        dataTrain = LocalExecutionModule.readSampleFromPsuadeFile(
            fnameTrain
        )  # rstype/order written to data
        rsIndex = SampleData.getSampleRSType(dataTrain)
        rs = ResponseSurfaces.getPsuadeName(rsIndex).lower()
        legendreOrder = None
        if rsIndex == ResponseSurfaces.LEGENDRE:
            legendreOrder = SampleData.getLegendreOrder(dataTrain)
            rs = rs + "%d" % legendreOrder
        # prepare testdata
        # !!! assumes testdata contains the same inputs and outputs as traindata !!!
        dataTest = copy.deepcopy(dataTrain)
        try:
            data = LocalExecutionModule.readDataFromSimpleFile(fnameInputSamples)
            inArray = data[0]
            sampleType = "MC"
        except:
            fullData = LocalExecutionModule.readSampleFromPsuadeFile(fnameInputSamples)
            inArray = fullData.getInputData()
            sampleType = fullData.getSampleMethod()
        dataTest.setSampleMethod(sampleType)
        nSamples, nInputs = inArray.shape
        dataTest.setNumSamples(nSamples)
        dataTest.setInputData(inArray)
        dataTest.setOutputData([])
        dataTest.setRunState([False] * nSamples)
        # ... write psuade input file
        fnameIn = RSAnalyzer.dname + os.path.sep + rs + ".in"
        y = 1
        outfile = RSAnalyzer.writeRSdata(fnameIn, y, dataTest, driver=fnameTrain)
        if outfile is None:
            error = "RSAnalyzer: In function emulate(), %s is not written.\n" % fnameIn
            Common.showError(error, out)
            return None
        # ... invoke psuade
        psfile = "psuadeData"
        if os.path.exists(psfile):
            os.remove(psfile)
        if platform.system() == "Windows":
            import win32api

            fnameIn = win32api.GetShortPathName(fnameIn)
        out, error = Common.invokePsuade(
            fnameIn,
            textDialog=textDialog,
            dialogShowSignal=dialogShowSignal,
            dialogCloseSignal=dialogCloseSignal,
            textInsertSignal=textInsertSignal,
            ensureVisibleSignal=ensureVisibleSignal,
        )

        # process error
        if error:
            return None

        # check output file
        if os.path.exists(psfile):
            psfile_ = Common.getLocalFileName(
                RSAnalyzer.dname, fnameInputSamples, ".testdat"
            )
            if os.path.exists(psfile_):
                os.remove(psfile_)
            import shutil

            shutil.copyfile(psfile, psfile_)
            psfile = psfile_
        else:
            error = "RSAnalyzer: %s does not exist." % psfile
            Common.showError(error, out)
            return None

        return psfile, rsIndex, legendreOrder

    @staticmethod
    def ystats(fname):
        # apply this function for initializing observations with reasonable means and stds

        # read data
        data = LocalExecutionModule.readSampleFromPsuadeFile(
            fname
        )  # does not assume rstype/order written to data

        # extract ensemble statistics for each output
        ys = []
        ydat = SampleData.getOutputData(data)
        fmt = "%1.4e"
        nOutputs = SampleData.getNumOutputs(data)
        for i in range(nOutputs):
            y = ydat[:, i]
            moments = {
                "mean": fmt % np.mean(y),
                "std": fmt % np.std(y),
                "skew": fmt % stats.skew(y),
                "kurt": fmt % (stats.kurtosis(y, bias=False) + 3),
            }
            ys.append(moments)

        return ys

    @staticmethod
    def pdfrange(pdf, param1, param2=None):
        # apply this function for initializing the prior bounds
        # make sure parameters are passed in as floats

        from scipy.stats import norm, lognorm, triang, gamma, beta, expon, weibull_min

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
