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
from .LocalExecutionModule import LocalExecutionModule
from .Common import Common


class DataProcessor:

    dname = os.getcwd() + os.path.sep + "DataProcessor_files"

    @staticmethod
    def filterdata(fname, **kwargs):

        # read data
        data = LocalExecutionModule.readSampleFromPsuadeFile(fname)

        # process keyworded arguments
        filterVar = None
        vmin = None
        vmax = None
        for key in kwargs:
            k = key.lower()
            if k == "input":
                filterVar = kwargs[key]
                cmd = "ifilter"

                # Get only input variables that are variable
                types = data.getInputTypes()
                inVarNames = SampleData.getInputNames(data)
                varNames = []
                for i in range(len(types)):
                    if types[i] == Model.VARIABLE:
                        varNames.append(inVarNames[i])

            elif k == "output":
                filterVar = kwargs[key]
                cmd = "ofilter"
                varNames = SampleData.getOutputNames(data)
            elif k == "vmin":
                vmin = kwargs[key]
            elif k == "vmax":
                vmax = kwargs[key]

        if filterVar is None:
            error = "DataProcessor: In function filterData(), the filter variable is not specified."
            Common.showError(error)
            return None
        if (vmin is None) | (vmax is None) | (vmin >= vmax):
            error = (
                'DataProcessor: filterData() requires a valid [min, max] range to filter the variable "%s".'
                % filterVar
            )
            Common.showError(error)
            return None

        # check if the filter variable exists
        if filterVar not in varNames:
            error = (
                'DataProcessor: In function filterData(), %s does not contain the filter variable "%s".'
                % (fname, filterVar)
            )
            Common.showError(error)
            outfile = fname
            return outfile

        # get the output index to filter variable
        filterIndex = varNames.index(filterVar) + 1  # psuade is 1-indexed

        # write script
        outfile = Common.getLocalFileName(DataProcessor.dname, fname, ".filtered")
        f = tempfile.SpooledTemporaryFile(mode="wt")
        if platform.system() == "Windows":
            import win32api

            fname = win32api.GetShortPathName(fname)
        f.write("load %s\n" % fname)
        f.write("%s\n" % cmd)  # invoke ifilter or ofilter
        if (cmd == "ifilter" and data.getNumInputs() > 1) or (
            cmd == "ofilter" and data.getNumOutputs() > 1
        ):
            f.write("%d\n" % filterIndex)  # select the filter variable
        f.write("%f\n" % vmin)  # extract points within range [vmin, vmax]
        f.write("%f\n" % vmax)
        if platform.system() == "Windows":
            head, tail = os.path.split(outfile)
            head = win32api.GetShortPathName(head)
            outfile = os.path.join(head, tail)
        f.write("write %s\n" % outfile)
        f.write("n\n")  # write all outputs
        f.write("quit\n")
        f.seek(0)

        # invoke psuade
        out, error = Common.invokePsuade(f)
        f.close()

        # Process error
        if error:
            return None

        if not os.path.exists(outfile):
            error = "DataProcessor: %s does not exist." % outfile
            Common.showError(error, out)
            return None

        return outfile

    @staticmethod
    def delete(fname, nInputs, nOutputs, nSamples, inVars, outVars, samples):

        di = nInputs - len(inVars)
        do = nOutputs - len(outVars)
        ds = nSamples - len(samples)

        if (di == 0) or (do == 0) or (ds == 0):
            error = "DataProcessor: In function delete(), one cannot delete all sample points or all input or output parameters."
            Common.showError(error)
            return None

        # write script
        outfile = Common.getLocalFileName(DataProcessor.dname, fname, ".deleted")
        f = tempfile.SpooledTemporaryFile(mode="wt")
        if platform.system() == "Windows":
            import win32api

            fname = win32api.GetShortPathName(fname)

        f.write("load %s\n" % fname)
        if (di > 0) and inVars:
            f.write("idelete\n")  # invoke idelete
            f.write("%d\n" % len(inVars))  # number of inputs to be deleted
            for i in inVars:
                f.write("%d\n" % i)  # select the input variable to delete
        if (do > 0) and outVars:
            outVars_reverse = outVars[::-1]
            for i in outVars_reverse:
                f.write("odelete\n")  # invoke odelete
                f.write("%d\n" % i)  # select the output variable to delete
            nOutputs = nOutputs - len(outVars)
        if (ds > 0) and samples:
            samples_reverse = samples[::-1]
            for i in samples_reverse:
                f.write("sdelete\n")  # invoke sdelete
                f.write("%d\n" % i)  # select the sample point to delete
        if platform.system() == "Windows":
            head, tail = os.path.split(outfile)
            head = win32api.GetShortPathName(head)
            outfile = os.path.join(head, tail)
        f.write("write %s\n" % outfile)

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

        if not os.path.exists(outfile):
            error = "DataProcessor: %s does not exist." % outfile
            Common.showError(error, out)
            return None

        return outfile
