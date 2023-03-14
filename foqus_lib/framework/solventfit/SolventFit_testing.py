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

import sys

# print(sys.path)
# sys.path.append('/Users/a241211/Documents/CCSI/Solvents/RCode/SolventFit/');
# sys.path.append('/Users/a241211/Documents/CCSI/Solvents/RCode/SolventFit/foqus_lib/framework/uq/');
import shutil

# from Distribution import *
# from Common import *
# from RSInference import *
# from Plotter import *

from foqus_lib.framework.uq.Distribution import *
from foqus_lib.framework.uq.Common import *

# from foqus_lib.framework.uq.RSInference import RSInferencer
# from foqus_lib.framework.uq.Plotter import Plotter


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
    ):  # last three parameters are not available in this version, but are needed in R code

        if emul_params is None:
            emul_params = {"bte": "[0,1000,1]", "nterms": "20", "order": "2"}

        if calib_params is None:
            calib_params = {"bte": "[0,2000,1]"}

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
            # shutil.copyfile(src, f)

        # create string for input to command window

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

        # p = subprocess.Popen([rpath, 'solvfit_calibfit.R',
        #                       str(nx_design), str(nx_var), xdatfile, ydatfile, modelfile,
        #                       expfile, priorsfile, disc, writepost, writedisc,
        #                       emul_params['bte'], emul_params['nterms'], emul_params['order'],
        #                       calib_params['bte'], disc_params['nterms'], disc_params['order']],
        #                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #    Common.runCommandInWindow([rpath, 'solvfit_calibfit.R',
        #                           str(nx_design), str(nx_var), str(nx_out), xdatfile, ydatfile, modelfile,
        #                           expfile, priorsfile, initsfile, disc, writepost, writedisc,
        #                           emul_params['bte'], emul_params['nterms'], emul_params['order'],
        #                           calib_params['bte'], disc_params['nterms'], disc_params['order'],
        #                          pt_mass,incl_em,model_func,restartfile],
        #                          'solventfit_log')

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


rdsfile = SolventFit.calibfit(
    "Rscript",
    1,
    3,
    3,
    "example2/xdat.csv",
    "example2/ydatmult.csv",
    "example2/solvfit_calibrator5_test.rds",
    "example2/expdatmult.csv",
    priorsfile="example2/morrispriorsmultfile.txt",
    disc=True,
)

#  rdsfile = fit('1','3','3','example/xdat.csv','example/ydatmult.csv','example/solvfit_calibrator4mult_em.rds','example/expdatmult.csv',priorsfile='example/morrispriorsmultfile.txt',disc=True,incl_em=True)

print(rdsfile)
