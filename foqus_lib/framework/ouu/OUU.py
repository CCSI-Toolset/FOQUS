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
import re
import numpy as np
from PyQt5 import QtCore, QtGui
from foqus_lib.framework.uq.Model import Model
from foqus_lib.framework.uq.Distribution import Distribution
from foqus_lib.framework.uq.SampleData import SampleData
from foqus_lib.framework.uq.Common import Common
from foqus_lib.framework.uq.LocalExecutionModule import LocalExecutionModule
from foqus_lib.framework.uq.RSAnalyzer import RSAnalyzer
from foqus_lib.framework.uq.SamplingMethods import SamplingMethods


class OUU(
    QtCore.QObject
):  # Must inherit from QObject for plotting to stay in main thread)

    dname = os.getcwd() + os.path.sep + "OUU_files"
    hfile = "psuade_ouu_history"
    stopFile = "psuade_ouu_stop"

    def __init__(self):
        super(OUU, self).__init__()
        self.hadError = False
        self.ignoreResults = False

    @staticmethod
    def writeOUUdata(
        outfile, outputs, constraints, derivatives, data, xtable, **kwargs
    ):

        # Charles TODO: Handle y is now a list of inputs
        # Charles TODO: Handle derivatives

        # defaults
        rseed = None
        driver = data.getDriverName()
        if driver is None:
            driver = "NONE"
        optdriver = data.getOptDriverName()
        if optdriver is None:
            optdriver = "NONE"
        ensoptdriver = data.getEnsembleOptDriverName()
        if ensoptdriver is None:
            ensoptdriver = "NONE"
        auxdriver = data.getAuxDriverName()
        if auxdriver is None:
            auxdriver = "NONE"
        inputLB = None
        inputUB = None
        inputDefaults = None
        distributions = None
        init_input = None

        # process keyworded arguments
        for key in kwargs:
            k = key.lower()
            if k == "randseed":
                rseed = kwargs[key]
            elif k == "driver":
                driver = kwargs[key]
            elif k == "optdriver":
                optdriver = kwargs[key]
            elif k == "ensoptdriver":
                ensoptdriver = kwargs[key]
            elif k == "auxdriver":
                auxdriver = kwargs[key]
            elif k == "inputlowerbounds":
                inputLB = kwargs[key]
            elif k == "inputupperbounds":
                inputUB = kwargs[key]
            elif k == "inputpdf":
                distributions = kwargs[key]
            elif k == "init_input":
                init_input = kwargs[key]

        inputTypes = data.getInputTypes()
        nInputs = data.getNumInputs()
        inputNames = data.getInputNames()
        variableInputIndices = []
        for e in xtable:
            if e["type"] != "Fixed":
                variableInputIndices.append(inputNames.index(e["name"]))
        nVariableInputs = len(variableInputIndices)
        nOutputs = len(outputs)
        nSamples = num_fmin = 1  # number of random restarts
        nConstraints = constraints.count(True)
        nDerivatives = derivatives.count(True)
        totalOutputs = nOutputs + nConstraints + nDerivatives

        f = open(outfile, "w")
        if init_input:
            f.write("PSUADE_IO\n")
            f.write("%d %d %d\n" % (nVariableInputs, totalOutputs, nSamples))
            f.write("1 0\n")  # assume initial point has not been run
            for x in init_input:
                f.write(" % .16e\n" % x)
            for i in range(totalOutputs):
                f.write(" 9.9999999999999997e+34\n")
            f.write("PSUADE_IO\n")

        # TO DO: merge with RSAnalyzer.writeRSdata()
        f.write("PSUADE\n")

        # ... input ...
        numFixed = nInputs - nVariableInputs
        f.write("INPUT\n")
        if numFixed > 0:
            f.write("   num_fixed %d\n" % numFixed)
        f.write("   dimension = %d\n" % nVariableInputs)
        if inputLB is None:
            inputLB = data.getInputMins()
        if inputUB is None:
            inputUB = data.getInputMaxs()
        if inputDefaults is None:
            inputDefaults = data.getInputDefaults()
        indices = list(range(nInputs))
        variableIndex = 1
        fixedIndex = 1
        for i, name, inType, lb, ub, default in zip(
            indices, inputNames, inputTypes, inputLB, inputUB, inputDefaults
        ):
            if i in variableInputIndices:  # inType == Model.VARIABLE:
                f.write(
                    "   variable %d %s  =  % .16e  % .16e\n"
                    % (variableIndex, name, lb, ub)
                )
                variableIndex = variableIndex + 1
            else:
                f.write("   fixed %d %s = % .16e\n" % (fixedIndex, name, default))
                fixedIndex = fixedIndex + 1

        # inject discrete variables in psuade
        opttypes = []
        cnt = 0
        for e in xtable:
            cnt = cnt + 1
            t = e["type"]
            if t == "Opt: Primary Discrete (Z1d)":
                opttypes.append(cnt)

        nn = len(opttypes)
        for ii in range(nn):
            jj = opttypes[ii]
            f.write("   discrete %d\n" % (jj))

        if distributions is None:
            distributions = SampleData.getInputDistributions(data)
        for i, inType, dist in zip(indices, inputTypes, distributions):
            if i in variableInputIndices:  # inType == Model.VARIABLE:
                distType = dist.getDistributionType()
                distParams = dist.getParameterValues()
                if distType != Distribution.UNIFORM:
                    f.write(
                        "   PDF %d %c" % (i + 1, Distribution.getPsuadeName(distType))
                    )
                    if distType == Distribution.SAMPLE:
                        error = "OUU: In function writeOUUdata(), "
                        error = error + "SAMPLE distribution is not supported."
                        Common.showError(error)
                        return None
                    else:
                        if distParams[0] is not None:
                            f.write(" % .16e" % distParams[0])
                        if distParams[1] is not None:
                            f.write(" % .16e" % distParams[1])
                    f.write("\n")
        f.write("END\n")

        # ... output ...
        outActive = nOutputs
        nConstrs = 0
        nDerivs = 0
        for ii in range(len(constraints)):
            if constraints[ii]:
                outActive = outActive + 1
                nConstrs = nConstrs + 1
        for ii in range(len(derivatives)):
            if derivatives[ii]:
                outActive = outActive + 1
                nDerivs = nDerivs + 1
        if nOutputs != 1:
            error = "OUU: In function writeOUUdata(), "
            error = error + "multi-objective optimization not supported."
            Common.showError(error)
            return None
        else:
            if (nConstrs > 0) and (nDerivs > 0):
                error = "OUU: In function writeOUUdata(), "
                error = error + "LBFGS does not support inequality constraints."
                Common.showError(error)
                return None
            elif (nDerivs > 0) and (nDerivs != nVariableInputs):
                error = "OUU: In function writeOUUdata(), "
                error = error + "Number of derivatives not correct"
                Common.showError(error)
                return None

        f.write("OUTPUT\n")
        f.write("   dimension = %d\n" % (outActive))
        outputNames = SampleData.getOutputNames(data)
        for ii in range(nOutputs):
            ind = outputs[ii]
            f.write("   variable %d %s\n" % (ii + 1, outputNames[ind - 1]))
            print(("   variable %d %s\n" % (ii + 1, outputNames[ind - 1])))
        outActive = nOutputs + 1
        for ii in range(len(constraints)):
            if constraints[ii]:
                f.write("   variable %d %s\n" % (outActive, outputNames[ii]))
                print(("   variable %d %s\n" % (outActive, outputNames[ii])))
                outActive = outActive + 1
        for ii in range(len(derivatives)):
            if derivatives[ii]:
                f.write("   variable %d %s\n" % (outActive, outputNames[ii]))
                print(("   variable %d %s\n" % (outActive, outputNames[ii])))
                outActive = outActive + 1
        f.write("END\n")

        # ... method ...
        f.write("METHOD\n")
        f.write("   sampling = MC\n")  # OUU uses this to create
        f.write("   num_samples = 1\n")  # initial guess
        if rseed is not None:
            f.write("random_seed = %d\n" % rseed)  # random seed
        f.write("END\n")

        # ... application ...
        f.write("APPLICATION\n")
        if platform.system() == "Windows":
            import win32api

            if driver != "NONE" and driver != "PSUADE_LOCAL":
                driver = win32api.GetShortPathName(driver)
            if optdriver != "NONE" and optdriver != "PSUADE_LOCAL":
                optdriver = win32api.GetShortPathName(optdriver)
            if ensoptdriver != "NONE" and ensoptdriver != "PSUADE_LOCAL":
                ensoptdriver = win32api.GetShortPathName(ensoptdriver)
            if auxdriver != "NONE" and auxdriver != "PSUADE_LOCAL":
                auxdriver = win32api.GetShortPathName(auxdriver)
        f.write("   driver = %s\n" % driver)
        f.write("   opt_driver = %s\n" % optdriver)
        f.write("   ensemble_opt_driver = %s\n" % ensoptdriver)
        f.write("   aux_opt_driver = %s\n" % auxdriver)
        f.write("   launch_interval = 0\n")
        f.write("END\n")

        # ... analysis ...
        f.write("ANALYSIS\n")
        if nDerivs > 0:
            f.write("   optimization method = ouu_lbfgs\n")
        else:
            f.write("   optimization method = ouu\n")
        f.write("   optimization num_local_minima = 1\n")
        f.write("   optimization max_feval = 1000000\n")
        f.write("   optimization fmin = 0.0\n")
        f.write("   optimization tolerance = 1.000000e-06\n")
        f.write("   optimization num_fmin = %d\n" % num_fmin)
        f.write("   optimization print_level = 3\n")
        # f.write('   analyzer output_id = %d\n' % y)
        f.write("   analyzer output_id = 1\n")
        f.write("   opt_expert\n")
        f.write("   printlevel 0\n")
        f.write("END\n")

        f.write("END\n")
        f.close()

        return outfile

    @staticmethod
    def compress(fname):

        N = 0  # number of samples in x3sample['file']
        with open(fname) as f:  ### TO DO for Jeremy: check sample size in GUI
            header = f.readline()
            header = header.split()
            N = int(header[0])
            nInputs = int(header[1])

        Nmin = 100  # psuade minimum for genhistogram
        if N < Nmin:
            warn = 'OUU: In function compress(), "x3sample file" requires '
            warn = warn + "at least %d samples." % Nmin
            Common.showError(warn)
            return {N: fname}  # return original sample file

        outfiles = {}
        nbins_max = 20
        nscenarios_max = 1501
        for nbins in range(2, nbins_max):

            # write script to invoke scenario compression
            f = tempfile.SpooledTemporaryFile(mode="wt")
            if platform.system() == "Windows":
                import win32api

                fname = win32api.GetShortPathName(fname)
            f.write("read_std %s\n" % fname)
            f.write("genhistogram\n")
            for x in range(nInputs):
                f.write("%d\n" % nbins)
            f.write("quit\n")
            f.seek(0)

            # invoke psuade
            out, error = Common.invokePsuade(f)
            f.close()
            if error:
                return None

            # check output file
            sfile = "psuade_pdfhist_sample"
            if os.path.exists(sfile):
                Ns = 0  # number of samples in psuade_pdfhist_sample
                with open(sfile) as f:
                    header = f.readline()
                    header = header.split()
                    Ns = int(header[0])
                sfile_ = Common.getLocalFileName(
                    OUU.dname, fname, ".compressed" + str(Ns)
                )
                if os.path.exists(sfile_):
                    os.remove(sfile_)
                os.rename(sfile, sfile_)
                sfile = sfile_
            else:
                error = "OUU: %s does not exist." % sfile
                Common.showError(error, out)
                return None

            # append scenario file to data structure
            if len(outfiles) > 1 and Ns > min(N, nscenarios_max):
                return outfiles
            else:
                outfiles[Ns] = (sfile, nbins)

        return outfiles

    def ouu(
        self,
        fname,
        y,
        outputsAsConstraint,
        outputsAsDerivative,
        xtable,
        phi,
        x3sample=None,
        x4sample=None,
        useRS=False,
        useBobyqa=True,
        driver=None,
        optDriver=None,
        auxDriver=None,
        ensOptDriver=None,
        plotSignal=None,
        endFunction=None,
    ):

        # Function to execute after inference has finished.
        # Function would enable button again and such things.
        self.endFunction = endFunction

        # read data, assumes data already have fixed variables written to file
        data = LocalExecutionModule.readSampleFromPsuadeFile(fname)
        if (
            optDriver == None
            and ensOptDriver == None
            and data.getOptDriverName() == None
            and data.getEnsembleOptDriverName() == None
        ):
            Common.showError(
                "Model file does not have any drivers set!",
                showDeveloperHelpMessage=False,
            )
            self.hadError = True
            if endFunction is not None:
                endFunction()
            return
        if driver != None:
            data.setDriverName(driver)
        if optDriver != None:
            data.setOptDriverName(optDriver)
        if auxDriver != None:
            data.setAuxDriverName(auxDriver)
        if ensOptDriver != None:
            data.setEnsembleOptDriverName(ensOptDriver)
        else:
            ensOptDriver = data.getEnsembleOptDriverName()

        # Remove file that tells OUU to stop
        if os.path.exists(OUU.stopFile):
            os.remove(OUU.stopFile)

        # process input table
        dname = OUU.dname
        deleteFiles = True
        if x3sample is not None:
            deleteFiles = not x3sample["file"].startswith(dname)
        # Common.initFolder(dname, deleteFiles = deleteFiles)
        if platform.system() == "Windows":
            import win32api

            dname = win32api.GetShortPathName(dname)
        fnameOUU = Common.getLocalFileName(dname, fname, ".ouudat")
        p = RSAnalyzer.parsePrior(data, xtable)
        if p is not None:
            inputLB = p["inputLB"]
            inputUB = p["inputUB"]
            dist = p["dist"]

        init_input = []
        vartypes = []
        for e in xtable:
            t = e["type"]
            if t == "Opt: Primary Continuous (Z1)":
                vartypes.append(1)
            elif t == "Opt: Primary Continuous (Z1c)":
                vartypes.append(1)
            elif t == "Opt: Primary Discrete (Z1d)":
                vartypes.append(1)
            elif t == "Opt: Recourse (Z2)":
                vartypes.append(2)
            elif t == "UQ: Discrete (Z3)":
                vartypes.append(3)
            elif t == "UQ: Continuous (Z4)":
                vartypes.append(4)
            if t != "Fixed":
                init_input.append(e["value"])
        M1 = vartypes.count(1)
        M2 = vartypes.count(2)
        M3 = vartypes.count(3)
        M4 = vartypes.count(4)

        # check arguments
        if M1 < 1:
            error = "OUU: In function ouu(), number of Z1 (design opt) "
            error = error + "must be at least 1."
        if M3 > 0:
            if x3sample == None:
                error = 'OUU: In function ouu(), "x3sample" is undefined.'
                Common.showError(error)
                return None

        if M4 > 0:
            if x4sample == None:
                error = 'OUU: In function ouu(), "x4sample" is undefined.'
                Common.showError(error)
                return None
            loadcs = "file" in x4sample
            if loadcs:
                N = 0  # number of samples in x4sample['file']

                ### TO DO for Jeremy: check sample size in GUI
                with open(x4sample["file"]) as f:
                    header = f.readline()
                    header = header.split()
                    N = int(header[0])

                Nmin = M4 + 1  # minimum number of samples
                if N < Nmin:
                    error = 'OUU: In function ouu(), "x4sample file" requires '
                    error = error + "at least %d samples." % Nmin
                    Common.showError(error)
                    return None
                if useRS:
                    Nrs = "nsamplesRS" in x4sample
                    if not Nrs:
                        error = 'OUU: In function ouu(), "x4sample nsamplesRS" is '
                        error = error + "required for setting up response surface."
                        Common.showError(error)
                        return None
                    Nrs = x4sample["nsamplesRS"]
                    Nrs = min(max(Nrs, Nmin), N)  ### TO DO for Jeremy: check in GUI

        # TO DO: remove randSeed
        ouuFile = OUU.writeOUUdata(
            fnameOUU,
            y,
            outputsAsConstraint,
            outputsAsDerivative,
            data,
            xtable,
            randSeed=41491431,
            inputLowerBounds=inputLB,
            inputUpperBounds=inputUB,
            inputPDF=dist,
            useEnsOptDriver=(ensOptDriver != None),
            init_input=init_input,
        )
        if ouuFile == None:
            return None

        # write script
        f = OUU.writescript(
            vartypes,
            fnameOUU,
            outputsAsConstraint,
            phi,
            x3sample,
            x4sample,
            useRS,
            useBobyqa,
            useEnsOptDriver=(ensOptDriver != None),
        )

        # delete previous history file
        if os.path.exists(OUU.hfile):
            os.remove(OUU.hfile)

        self.textDialog = Common.textDialog()
        self.thread = psuadeThread(self, f, self.finishOUU, self.textDialog, plotSignal)
        self.thread.start()

    def stopOUU(self):
        f = open(OUU.stopFile, "w")
        f.close()
        self.ignoreResults = True

    def finishOUU(self, out, error):

        if error:
            return None

        # clean up
        if os.path.exists(OUU.hfile):
            hfile_ = OUU.dname + os.path.sep + OUU.hfile
            os.rename(OUU.hfile, hfile_)
            hfile = hfile_
        for f in os.listdir("."):
            if "psuadeOpt" in f:
                os.remove(f)

        # save output for debugging
        f = open("ouu.out", "w")
        f.write(out)
        f.close()

        # grab optimization results
        if self.ignoreResults:
            self.ignoreResults = False
        else:
            self.results = OUU.getPsuadeResults(out)
            if self.results == None:
                error = "OUU: Optimization error."
                Common.showError(error, out)
                return None

        if self.endFunction is not None:
            self.endFunction()

    def getHadError(self):
        return self.hadError

    def getResults(self):
        return self.results

    @staticmethod
    def writescript(
        vartypes,
        fnameOUU,
        outputsAsConstraint,
        phi=None,
        x3sample=None,
        x4sample=None,
        useRS=False,
        useBobyqa=False,
        useEnsOptDriver=None,
    ):

        M1 = vartypes.count(1)
        M2 = vartypes.count(2)
        M3 = vartypes.count(3)
        M4 = vartypes.count(4)
        nInputs = M1 + M2 + M3 + M4

        # write script
        # f = open('ouu.in','w+b')
        f = tempfile.SpooledTemporaryFile(mode="w+b")
        if platform.system() == "Windows":
            import win32api

            fnameOUU = win32api.GetShortPathName(fnameOUU)
        f.write(("run %s\n" % fnameOUU).encode())
        f.write(b"y\n")  # ready to proceed
        # ... partition variables
        f.write(("%d\n" % M1).encode())  # number of design opt variables
        if M1 == nInputs:
            f.write(b"quit\n")
            f.seek(0)
            return f

        # ________ M1 < nInputs ________
        f.write(("%d\n" % M2).encode())  # number of operating opt variables
        if M1 + M2 == nInputs:
            for i in range(nInputs):
                f.write(("%d\n" % vartypes[i]).encode())
            if useBobyqa:
                f.write(b"n\n")  # use BOBYQA means 'no' to use own driver
            else:
                f.write(b"y\n")  # use own driver as optimizer
            f.write("quit\n")
            f.seek(0)
            return f

        # ________ M1+M2 < nInputs ________
        f.write(("%d\n" % M3).encode())  # number of discrete UQ variables
        for i in range(nInputs):
            f.write(("%d\n" % vartypes[i]).encode())

        # ... set objective function w.r.t. to uncertainty
        ftype = phi["type"]
        f.write(("%d\n" % ftype).encode())  # optimization objective w.r.t. UQ variables
        if ftype == 2:
            beta = max(0, phi["beta"])  # beta >= 0
            f.write(("%f\n" % beta).encode())
        elif ftype == 3:
            alpha = phi["alpha"]
            alpha = min(max(alpha, 0.5), 1.0)  # 0.05 <= alpha <= 1.0
            f.write(("%f\n" % alpha).encode())

        if outputsAsConstraint.count(True) > 0:
            f.write(b"1\n")

        # ... get sample for discrete UQ variables
        # The file format should be:
        # line 1: <nSamples> <nInputs>
        # line 2: <sample 1 input 1> <input 2> ... <probability>
        # line 3: <sample 2 input 1> <input 2> ... <probability>
        if M3 > 0:
            if platform.system() == "Windows":
                import win32api

                x3sample["file"] = win32api.GetShortPathName(x3sample["file"])

            f.write(
                ("%s\n" % x3sample["file"]).encode()
            )  # sample file for discrete UQ variables

        # ... get sample for continuous UQ variables
        # The file format should be:
        # line 1: <nSamples> <nInputs>
        # line 2: <sample 1 input 1> <input 2> ...
        # line 3: <sample 2 input 1> <input 2> ...
        #                .....
        # line N: <sample N input 1> <input 2> ...
        if M4 > 0:
            loadcs = "file" in x4sample
            if loadcs:
                if platform.system() == "Windows":
                    import win32api

                    x4sample["file"] = win32api.GetShortPathName(x4sample["file"])
                f.write(b"1\n")  # load samples for continuous UQ vars
                f.write(
                    ("%s\n" % x4sample["file"]).encode()
                )  # sample file for continuous UQ vars
            else:
                f.write(b"2\n")  # generate samples for continuous UQ variables
            # ... apply response surface
            if useRS:
                f.write(b"y\n")  # use response surface
                if loadcs:
                    Nrs = x4sample["nsamplesRS"]
                    f.write(
                        ("%d\n" % Nrs).encode()
                    )  # number of points to build RS (range: [M4+1,N] where N=samplesize)
                    randsample = True  # set to False to pass in subsample based on convex hull analysis
                    # set to True to use psuade's built-in random sampler
                    if randsample:
                        f.write(b"2\n")  # 2 to generate random sample
                    else:
                        f.write(b"1\n")  # 1 to upload subsample file
                        x, y = RSAnalyzer.readRSsample(x4sample["file"])
                        xsub = OUU.subsample(x, Nrs)
                        dname = OUU.dname
                        if platform.system() == "Windows":
                            import win32api

                            dname = win32api.GetShortPathName(dname)
                        x4subsample = Common.getLocalFileName(
                            dname, x4sample["file"], ".subsample"
                        )
                        RSAnalyzer.writeRSsample(x4subsample, xsub)
                        f.write(
                            ("%s\n" % x4subsample).encode()
                        )  # subsample file containing subset of original points
            else:
                f.write(b"n\n")  # do not use response surface
            # ... # create samples for continuous UQ variables
            if not loadcs:
                Nmin = M4 + 1
                if x4sample["method"] == SamplingMethods.LH:
                    f.write(b"1\n")  # sampling scheme: Latin Hypercube
                    nSamples = x4sample["nsamples"]
                    nSamples = min(max(nSamples, Nmin), 1000)
                    f.write(
                        ("%d\n" % nSamples).encode()
                    )  # number of samples (range: [M4+1,1000])
                elif x4sample["method"] == SamplingMethods.FACT:
                    f.write(b"2\n")  # sampling scheme: Factorial
                    nlevels = x4sample["nlevels"]
                    nlevels = min(max(nlevels, 3), 100)
                    f.write(
                        ("%d\n" % nlevels).encode()
                    )  # number of levels per variable (range: [3,100])
                elif x4sample["method"] == SamplingMethods.LPTAU:
                    f.write(b"3\n")  # sampling scheme: Quasi Monte Carlo
                    nSamples = x4sample["nsamples"]
                    nSamples = min(max(nSamples, Nmin), 1000)
                    f.write(
                        ("%d\n" % nSamples).encode()
                    )  # number of samples (range: [M4+1,1000])

        # ... choose optimizer
        if M2 > 0:
            # if useBobyqa:
            #    f.write('n\n')    # use BOBYQA
            # else:
            #    f.write('y\n')    # use own driver as optimizer
            f.write(b"y\n")  # use own driver as optimizer

        # ... choose ensemble optimization driver
        if M3 + M4 > 0:  # and not useBobyqa:
            if useEnsOptDriver:
                f.write(b"y\n")  # use ensemble driver
            else:
                f.write(b"n\n")

        # ... choose mode to run simulations for computing statistics
        if M3 + M4 > 0:
            f.write(b"n\n")  # do not use asynchronous mode (not tested)

        f.write(b"quit\n")
        f.seek(0)

        # for line in f:
        #    print line.strip()
        # f.seek(0)

        return f

    @staticmethod
    def inhull(p, hull):
        """
        Test if points in `p` are in `hull`

        `p` should be a `NxK` coordinates of `N` points in `K` dimensions
        `hull` is either a scipy.spatial.Delaunay object or the `MxK` array of the
        coordinates of `M` points in `K`dimensions for which Delaunay triangulation
        will be computed

        Source: http://stackoverflow.com/questions/16750618
        """
        from scipy.spatial import Delaunay

        if not isinstance(hull, Delaunay):
            hull = Delaunay(hull)

        return hull.find_simplex(p) >= 0

    @staticmethod
    def subsample(p, N):

        M = len(p)
        if N == M:
            return p

        import scipy

        if scipy.version.version == "0.11.0":  # version on aztec
            s = scipy.spatial.Delaunay(p).convex_hull
        else:
            s = scipy.spatial.ConvexHull(p).simplices  # works for 0.12.0+
        v = np.unique(s)  # indices to vertices
        nv = len(v)
        pv = p[v]

        if N == nv:
            return pv

        if N > nv:
            i = np.setdiff1d(list(range(len(p))), v)  # indices to interior points
            r = np.random.permutation(i)
            N = N - nv  # number of interior points
            r = r[0:N]  # randomized interior indices
            return np.concatenate(
                (pv, p[r])
            )  # return vertices with some interior points

        if N < nv:
            R = 10
            indices = []
            h = []
            for i in range(R):
                r = np.random.permutation(v)
                r = r[0:N]
                indices.append(r)  # randomized vertex indices
                b = OUU.inhull(
                    p, p[r]
                ).tolist()  # compute goodness of hull formed by random vertices
                h.append(b.count(True))
            s = indices[np.argmax(h)]
            return p[s]  # return subset of vertices that form the "best" hull

    @staticmethod
    def getPsuadeResults(lines):

        pat = "OUU total number of function evaluations = (.*)"
        r = re.findall(pat, lines)
        try:
            N = int(r[0])  # number of function evaluations
        except:
            return None

        i = lines.find("#")
        j = lines.rfind("#")
        results = lines[i:j]
        results = results.replace(
            "PSUADE OPTIMIZATION : CURRENT GLOBAL MINIMUM -",
            "OPTIMIZATION RESULTS (after %d function evaluations)" % N,
        )

        return results


class psuadeThread(QtCore.QThread):
    def __init__(
        self, parent, fileHandle, onFinishedFunctionHandle, textDialog, plotValuesSignal
    ):
        QtCore.QThread.__init__(self)
        self.worker = psuadeWorker(
            self, fileHandle, onFinishedFunctionHandle, textDialog, plotValuesSignal
        )
        self.worker.moveToThread(self)
        self.started.connect(self.worker.run)
        self.worker.finishedSignal.connect(self.quit)
        self.worker.finishedSignal.connect(self.worker.deleteLater)
        self.finished.connect(self.deleteLater)


class psuadeWorker(QtCore.QObject):
    finishedSignal = QtCore.Signal()
    functionSignal = QtCore.Signal(str, str)
    textDialogShowSignal = QtCore.Signal()
    textDialogCloseSignal = QtCore.Signal()
    textDialogInsertSignal = QtCore.Signal(str)
    textDialogEnsureVisibleSignal = QtCore.Signal()
    showErrorSignal = QtCore.Signal(str, str)

    def __init__(
        self, parent, fileHandle, onFinishedFunctionHandle, textDialog, plotValuesSignal
    ):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.fileHandle = fileHandle
        self.functionHandle = onFinishedFunctionHandle
        self.textDialog = textDialog
        self.plotValuesSignal = plotValuesSignal

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
            plotOuuValuesSignal=self.plotValuesSignal,
        )
        if out is None:
            return
        self.fileHandle.close()
        self.functionSignal.emit(out, error)
        self.finishedSignal.emit()
