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
from .SamplingMethods import SamplingMethods
from .SampleData import SampleData
from .Common import Common
from .LocalExecutionModule import LocalExecutionModule
from .Plotter import Plotter
from PyQt5 import QtWidgets


class SampleRefiner:

    dname = os.getcwd() + os.path.sep + "SampleRefiner_files"

    @staticmethod
    def adaptiveSample(fname, y, nSamples0, nSamplesNew):

        # read data
        data = LocalExecutionModule.readSampleFromPsuadeFile(fname)
        nSamples = SampleData.getNumSamples(data)

        # warn user of prohibitively long runtime if nSamples > 1000
        if nSamples > 1000:
            msg = "SampleRefiner: Adaptive sampling will take a long time with ensembles with greater than 1000 sample points. Proceed?"
            QtWidgets.QMessageBox.warning(
                None,
                "SampleRefiner: Warning of Long Runtime",
                msg,
                QtWidgets.QMessageBox.Ok,
                QtWidgets.QMessageBox.Ok,
            )

        # write script
        suffix = ".refine_%d" % (nSamples + nSamplesNew)
        fnameOut = Common.getLocalFileName(SampleRefiner.dname, fname, suffix)
        f = tempfile.SpooledTemporaryFile(mode="wt")
        if platform.system() == "Windows":
            import win32api

            fname = win32api.GetShortPathName(fname)
        f.write("load %s\n" % fname)
        cmd = "a_refine"
        f.write("%s\n" % cmd)
        f.write("%d\n" % y)  # output to use for sample refinement
        f.write("%d\n" % nSamples0)  # original size of sample
        f.write("%d\n" % nSamplesNew)  # number of samples to be added
        if platform.system() == "Windows":
            head, tail = os.path.split(fnameOut)
            head = win32api.GetShortPathName(head)
            fnameOut = os.path.join(head, tail)
        f.write("write %s\n" % fnameOut)
        nOutputs = SampleData.getNumOutputs(data)
        if nOutputs > 1:
            f.write("n\n")  # write all outputs
        f.write("quit\n")
        f.seek(0)

        # invoke psuade
        out, error = Common.invokePsuade(f)
        f.close()

        # process error
        if error:
            return None

        # check output file
        if not os.path.exists(fnameOut):
            error = "SampleRefiner: %s does not exist." % fnameOut
            Common.showError(error, out)
            return None

        return fnameOut
