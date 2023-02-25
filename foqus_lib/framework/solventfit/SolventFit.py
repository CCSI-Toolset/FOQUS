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
import csv
import subprocess
import numpy as np
import platform

from foqus_lib.framework.uq.Distribution import *
from foqus_lib.framework.uq.Common import *
from foqus_lib.framework.uq.RSInference import RSInferencer
from foqus_lib.framework.uq.Plotter import Plotter


class SolventFit:

    dname = os.getcwd() + os.path.sep + "SolventFit_files"

    @staticmethod
    def getVarNames(datfile):
        f = open(datfile, "r")
        reader = csv.reader(f)
        varNames = next(reader)
        f.close()
        return varNames

    @staticmethod
    def calibfit(
        rpath,  # path to Rscript
        nx_design,  # number of design variables
        nx_var,  # number of random variables
        nx_out,  # number of output variables
        xdatfile,  # input train set: design vars followed by rand vars
        ydatfile,  # output train set:
        modelfile,  # RDS file where trained model will be saved
        expfile,  # experiment data
        priorsfile,  # file describing parametric form of input PDFs
        initsfile="NULL",  # file of initial values, not avaailable in this version.
        restartfile="NULL",  # restart file name to restart from output, not available in this version
        disc=True,  # include discrepancy
        writepost=True,  # write posterior sample
        writedisc=True,  # write discrepancy sample
        emul_params=None,
        calib_params=None,
        disc_params=None,
        pt_mass=False,
        incl_em=True,
        model_func="NULL",
    ):  # last four parameters are not available in this version, but are needed in R code

        if emul_params is None:
            emul_params = {"bte": "[0,10000,1]", "nterms": "20", "order": "3"}

        if calib_params is None:
            calib_params = {"bte": "[0,50000,1]"}

        booldict = {True: "1", False: "0"}
        disc = booldict[disc]
        writepost = booldict[writepost]
        writedisc = booldict[writedisc]
        pt_mass = booldict[pt_mass]  # capability not available
        incl_em = booldict[incl_em]  # capability not available

        if disc_params is None:
            disc_params = {"nterms": "20", "order": "2"}

        files = ["solvfit_calibfit.R", "solvfit_emulfit.R"]
        for f in files:
            mydir = os.path.dirname(__file__)
            src = os.path.join(mydir, f)
            shutil.copyfile(src, f)

        # p = subprocess.Popen([rpath, 'solvfit_calibfit.R',
        #                       str(nx_design), str(nx_var), xdatfile, ydatfile, modelfile,
        #                       expfile, priorsfile, disc, writepost, writedisc,
        #                       emul_params['bte'], emul_params['nterms'], emul_params['order'],
        #                       calib_params['bte'], disc_params['nterms'], disc_params['order']],
        #                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if platform.system() == "Windows":
            import win32api

            rpath = win32api.GetShortPathName(rpath)
            xdatfile = win32api.GetShortPathName(xdatfile)
            ydatfile = win32api.GetShortPathName(ydatfile)
            expfile = win32api.GetShortPathName(expfile)
            priorsfile = win32api.GetShortPathName(priorsfile)

        commandItems = [
            rpath,
            "solvfit_calibfit.R",
            str(nx_design),
            str(nx_var),
            str(nx_out),
            xdatfile,
            ydatfile,
            modelfile,
            expfile,
            priorsfile,
            initsfile,
            disc,
            writepost,
            writedisc,
            emul_params["bte"],
            emul_params["nterms"],
            emul_params["order"],
            calib_params["bte"],
            disc_params["nterms"],
            disc_params["order"],
            pt_mass,
            incl_em,
            model_func,
            restartfile,
        ]
        commandItems = list(map(str, commandItems))
        Common.runCommandInWindow(" ".join(commandItems), "solventfit_log")

        # out, error = p.communicate()
        # if error:
        #     print(out)
        #     print(error)
        #     outf = open('solventfit_log', 'w')
        #     outf.write(out)
        #     outf.write('\n\n\n')
        #     outf.write(error)
        #     outf.close()
        # Common.showError(error, out)
        # return None

        return modelfile

    @staticmethod
    def fit(
        xdatfile,
        ydatfile,
        ytable,
        xtable,
        exptable,
        genPostSample=True,  # posterior sample is ALWAYS generated, set to True to copy sample to user-specified file
        addDisc=None,
        show=None,
        rpath="Rscript",
        saveRdsFile=None,
        numEmulIter=10000,
        numCalibIter=50000,
        numEmulBurnIn=0,
        numCalibBurnIn=0,
    ):

        # get input variable names
        inVarNames = SolventFit.getVarNames(xdatfile)

        nx_out = sum(1 for y in ytable if y is not None)

        ### ytable should be an array of length N, where N is the number of outputs, observed and unobserved.
        ### if output is unobserved, ytable[i] = None
        ### if output is observed, ytable[i] should contain the following fields: {'outputName': varName}

        ### xtable should be an array of length N, where N is the number of inputs.
        ### xtable[i] should contain the following fields:
        ###     {'type':%s, 'value':%s, 'min':%f, 'max':%f, 'pdf':%d, 'param1':%f, 'param2':%f}
        ###      'type' can only be DESIGN or VARIABLE.
        # ... parse xtable
        xdesign = []
        xrand = []
        xfixed = []
        pdf_index = {
            Distribution.NORMAL: 1,
            Distribution.GAMMA: 2,
            Distribution.LOGNORMAL: 3,
            Distribution.UNIFORM: 4,
        }
        pdf_generator = {
            Distribution.NORMAL: np.random.normal,  # (mu,sigma,N)
            Distribution.GAMMA: np.random.gamma,  # (shape,scale,N)
            Distribution.LOGNORMAL: np.random.lognormal,  # (mu,sigma,N)
            Distribution.UNIFORM: np.random.uniform,  # (low,high,N)
        }
        dist = []
        param1 = []
        param2 = []
        minval = []
        maxval = []
        priorsample = []
        fixedVals = []
        N = 1000  # prior sample size
        for i, e in enumerate(xtable):
            if e["type"] == "Design":
                xdesign.append(i)
            elif e["type"] == "Variable":
                d = e["pdf"]
                dist.append(pdf_index[d])
                if d == Distribution.UNIFORM:
                    p1 = e["min"]
                    p2 = e["max"]
                else:
                    p1 = e["param1"]
                    p2 = e["param2"]
                param1.append(p1)
                param2.append(p2)
                minval.append(e["min"])
                maxval.append(e["max"])
                pdfgen = pdf_generator[d]
                priorsample.append(pdfgen(p1, p2, N))
                xrand.append(i)
            else:  ## TODO Sham: Account for fixed variable
                fixedVals.append(e["value"])
                xfixed.append(i)
        xnames = [inVarNames[x] for x in (xrand + xfixed)]  # names of variable inputs
        dist += [0] * len(xfixed)
        param1 += fixedVals
        param2 += fixedVals
        minval += fixedVals
        maxval += fixedVals
        fixedVals = list(map(str, fixedVals))

        # ... reorder the columns in xdatfile: design followed by random
        lines = []
        f = open(xdatfile, "r")
        reader = csv.reader(f)
        for row in reader:
            lines.append(row)
        f.close()
        cols = list(zip(*lines))
        newcols = []
        for i in xdesign:
            newcols.append(cols[i])
        for i in xrand:
            newcols.append(cols[i])
        xdat = list(zip(*newcols))  # list of tuples with data in correct order
        Common.initFolder(SolventFit.dname)
        xdatfile_ = Common.getLocalFileName(SolventFit.dname, xdatfile, ".ordered")
        f = open(xdatfile_, "w")
        xdat[0] = ['"%s"' % x for x in xdat[0]]
        for i, row in enumerate(xdat):
            if i == 0:
                row += ['"%s"' % inVarNames[x] for x in xfixed]
                f.write(",".join(row) + "\n")
            else:
                f.write(",".join(row + tuple(fixedVals)) + "\n")
        f.close()
        xdatfile = xdatfile_  # use ordered file for training

        # ... write priors file for variable inputs
        ### *** THE FORMAT OF THIS DATA FILE IS: (contains nx_var columns)
        ### Line 1: dist type: 0=fixed, 1=normal, 2=gamma, 3=lognormal, 4=uniform
        ### Line 2: first param
        ### Line 3: second param
        ### Line 4: min value
        ### Line 5: max value
        ### Line 6: boolean for point mass (set to 0 bc not currently supported)
        priorsfile = SolventFit.dname + os.path.sep + "priors.txt"
        f = open(priorsfile, "w")
        f.write(" ".join([str(e) for e in dist]) + "\n")
        f.write(" ".join([str(e) for e in param1]) + "\n")
        f.write(" ".join([str(e) for e in param2]) + "\n")
        f.write(" ".join([str(e) for e in minval]) + "\n")
        f.write(" ".join([str(e) for e in maxval]) + "\n")
        f.write(" ".join(["0"] * len(dist)) + "\n")
        f.close()

        # ... write priors sample
        priorsamplefile = SolventFit.dname + os.path.sep + "prior.samples.std"
        priorsample = list(zip(*priorsample))
        f = open(priorsamplefile, "w")
        f.write("%d %d 0\n" % (N, len(xrand)))  # header
        for row in priorsample:
            f.write(" ".join([str(e) for e in row]) + "\n")
        f.close()

        ### exptable should be an array of length p where p = number of experiments.
        ### exptable[i] should be a numeric array:
        ### TODO Sham: The format was changed to add Std Devs. Need to change writing of expfile to reflect change if different from below:
        ###        Old format: [expIndex, designVal_1, ..., designVal_m, outputMean_1, ..., outputMean_n]
        ###        New format: [expIndex, designVal_1, ..., designVal_m, outputMean_1, outputStd_1, ..., outputMean_n, outputStd_n]
        ###    Also make sure your test files use this format for exptable as well.
        # ... write experiment data file
        expfile = SolventFit.dname + os.path.sep + "expdata.csv"
        f = open(expfile, "w")
        numDesign = len(xdesign)
        for i, row in enumerate(exptable):
            if i == 0:
                f.write(
                    ",".join(row[1:] + ["%sStd" % r for r in row[numDesign + 1 :]])
                    + "\n"
                )
            else:
                # Reorder everything to conform to new format
                newRow = row[1 : numDesign + 1]  # Design variables
                newRow += row[numDesign + 1 : len(row) : 2]  # Means
                newRow += row[numDesign + 2 : len(row) : 2]  # Std Devs
                f.write(
                    ",".join([str(e) for e in newRow]) + "\n"
                )  # omit expIndex when writing
        f.close()

        ## TODO Sham: Do we want both emul_params and calib_params to be changed with burn in and iterations
        emul_params = {
            "bte": "[%d,%d,1]" % (numEmulBurnIn, numEmulIter),
            "nterms": "20",
            "order": "2",
        }
        calib_params = {"bte": "[%d,%d,1]" % (numCalibBurnIn, numCalibIter)}

        # invoke R to perform SolventFit calibration
        rdsFile = "solvfit_calib.rds"
        #        if not xdesign:  # account for dummy variable
        #            SolventFit.calibfit(rpath,1,len(xrand),xdatfile,ydatfile,
        #                                rdsFile,expfile,priorsfile,
        #                                disc=False,writepost=True,writedisc=False,
        #                                emul_params = emul_params, calib_params = calib_params)
        #        else:
        SolventFit.calibfit(
            rpath,
            len(xdesign),
            len(xrand),
            nx_out,
            xdatfile,
            ydatfile,
            rdsFile,
            expfile,
            priorsfile,
            disc=addDisc,
            writepost=True,
            writedisc=addDisc,
            emul_params=emul_params,
            calib_params=calib_params,
        )

        # check output files
        postsamplefile = "post.samples"
        if os.path.exists(postsamplefile):
            postsamplefile_ = SolventFit.dname + os.path.sep + postsamplefile
            if os.path.exists(postsamplefile_):
                os.remove(postsamplefile_)
            os.rename(postsamplefile, postsamplefile_)
            postsamplefile = postsamplefile_
        else:
            error = "SolventFit: %s does not exist." % postsamplefile
            Common.showError(error)
            return None
        if os.path.exists(rdsFile):
            if saveRdsFile is None:
                saveRdsFile = SolventFit.dname + os.path.sep + rdsFile
            if os.path.exists(saveRdsFile):
                os.remove(saveRdsFile)
            os.rename(rdsFile, saveRdsFile)
            rdsFile = saveRdsFile
        else:
            error = "SolventFit: %s does not exist." % rdsFile
            Common.showError(error)
            return None

        with open(postsamplefile) as f:
            postsample = [list(map(float, line.split())) for line in f.readlines()]

        # ----- plot histogram for 1 random input -----
        if len(xrand) == 1:
            return SolventFit.plotSingleRandomSample(priorsample, postsample, xnames[0])

        # ----- plot heatmaps for more than 1 random inputs -----
        # add header to posterior sample file
        nrows = len(postsample)
        postsamplefile = postsamplefile + ".std"
        f = open(postsamplefile, "w")
        f.write("%d %d 0\n" % (nrows - 1, len(xrand)))  # header
        for row in postsample:
            f.write(" ".join([str(e) for e in row]) + "\n")
        f.close()

        # generate prior heatmap
        prior_mfile = RSInferencer.genheatmap(
            priorsamplefile, filetype="std", move=False
        )
        prior_mfile_ = SolventFit.dname + os.path.sep + "prior_" + prior_mfile
        if not os.path.exists(prior_mfile):
            error = "SolventFit: %s does not exist." % prior_mfile
            Common.showError(error)
            return None
        if os.path.exists(prior_mfile_):
            os.remove(prior_mfile_)
        os.rename(prior_mfile, prior_mfile_)
        prior_mfile = prior_mfile_

        # generate posterior heatmap
        post_mfile = RSInferencer.genheatmap(postsamplefile, filetype="std", move=False)
        post_mfile_ = SolventFit.dname + os.path.sep + "post_" + post_mfile
        if not os.path.exists(post_mfile):
            error = "SolventFit: %s does not exist." % post_mfile
            Common.showError(error)
            return None
        if os.path.exists(post_mfile_):
            os.remove(post_mfile_)
        os.rename(post_mfile, post_mfile_)
        post_mfile = post_mfile_

        # plot prior and posterior
        SolventFit.plotsample(
            prior_mfile, post_mfile, xnames, minval, maxval, show=None
        )

        return (prior_mfile, post_mfile, xnames, minval, maxval)

    @staticmethod
    def plotsample(prior_mfile, post_mfile, xnames, xmin, xmax, show=None):

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
        ) = RSInferencer.getplotdat(
            prior_mfile, xnames, xmin, xmax, plotvars, show=show
        )
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
        ) = RSInferencer.getplotdat(post_mfile, xnames, xmin, xmax, plotvars, show=show)
        ptitle = "Input POSTERIOR Probabilities"
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

    @staticmethod
    def restart(
        rdsFile,
        genPostSample=True,  # posterior sample is ALWAYS generated, set to True to copy sample to user-specified file
        addDisc=None,
        show=None,
        rpath="Rscript",
        saveRdsFile=None,
        numIter=1000,
        numBurnIn=0,
    ):
        ## TODO Sham: Implement this
        pass

    @staticmethod
    def plotSingleRandomSample(priorsample, postsample, xlabel):
        from scipy import stats

        # compute moments
        fmt = "%1.4e"
        priormoments = {
            "mean": fmt % np.mean(priorsample),
            "std": fmt % np.std(priorsample),
            "skew": fmt % stats.skew(priorsample),
            "kurt": fmt % (stats.kurtosis(priorsample, bias=False) + 3),
        }
        postmoments = {
            "mean": fmt % np.mean(postsample),
            "std": fmt % np.std(postsample),
            "skew": fmt % stats.skew(postsample),
            "kurt": fmt % (stats.kurtosis(postsample, bias=False) + 3),
        }
        # plot
        ylabel = "Probabilities"
        ptitle = "Input PRIOR Probabilities"
        ftitle = "Input Distribution Plots *before* Bayesian Inference"
        Plotter.plothist(
            np.array(priorsample),
            priormoments,
            ftitle,
            ptitle,
            xlabel,
            ylabel,
            plotcdf=False,
            lastplot=False,
        )
        ptitle = "Input POSTERIOR Probabilities"
        ftitle = "Input Distribution Plots *after* Bayesian Inference"
        Plotter.plothist(
            np.array(postsample),
            postmoments,
            ftitle,
            ptitle,
            xlabel,
            ylabel,
            plotcdf=False,
            lastplot=True,
        )

        return (priorsample, postsample, xlabel)
