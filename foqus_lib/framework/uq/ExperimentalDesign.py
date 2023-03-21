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
import copy
import numpy
import platform
import tempfile

from foqus_lib.framework.uq.Model import Model
from foqus_lib.framework.uq.SampleData import SampleData
from foqus_lib.framework.uq.Distribution import Distribution
from foqus_lib.framework.uq.SamplingMethods import SamplingMethods
from .LocalExecutionModule import LocalExecutionModule
from .RSAnalyzer import RSAnalyzer
from .Common import Common


class ExperimentalDesign:
    @staticmethod
    def createPsuadeInFile(data, filename, includePDF=True):
        outf = open(filename, "w")
        outf.write("PSUADE\n")

        # Write inputs
        outf.write("INPUT\n")
        outf.write("   dimension = %d\n" % data.getNumInputs())
        names = data.getInputNames()
        mins = data.getInputMins()
        maxs = data.getInputMaxs()
        indices = list(range(data.getNumInputs()))
        for i, name, minimum, maximum in zip(indices, names, mins, maxs):
            outf.write("   variable %d %s = %e %e\n" % (i + 1, name, minimum, maximum))
        distributions = data.getInputDistributions()
        for i, dist in zip(indices, distributions):
            distType = dist.getDistributionType()
            distParams = dist.getParameterValues()
            if distType == Distribution.SAMPLE:
                outf.write(
                    "   PDF %d %c" % (i + 1, Distribution.getPsuadeName(distType))
                )
                if distParams[0] is not None:
                    filename = distParams[0]
                    if platform.system() == "Windows":
                        import win32api

                        filename = win32api.GetShortPathName(filename)
                    outf.write(" %s" % filename)
                if distParams[1] is not None:
                    outf.write(" %d" % distParams[1])
                outf.write("\n")
            elif includePDF:  # write out PDF info for all non-uniform PDF types
                if distType != Distribution.UNIFORM:
                    outf.write(
                        "   PDF %d %c" % (i + 1, Distribution.getPsuadeName(distType))
                    )
                    if distParams[0] is not None:
                        outf.write(" %e" % distParams[0])
                    if distParams[1] is not None:
                        outf.write(" %e" % distParams[1])
                    outf.write("\n")
        outf.write("END\n")

        # Write outputs
        outf.write("OUTPUT\n")
        if data.getNumOutputs() == 0:
            outf.write("   dimension = 1\n")
            names = ["ghostOuput"]
            indices = list(range(1))
            for i, name in zip(indices, names):
                outf.write("   variable %d %s\n" % (i + 1, name))
        else:
            outf.write("   dimension = %d\n" % data.getNumOutputs())
            names = data.getOutputNames()
            indices = list(range(data.getNumOutputs()))
            for i, name in zip(indices, names):
                outf.write("   variable %d %s\n" % (i + 1, name))

        outf.write("END\n")

        # Write Method
        outf.write("METHOD\n")
        outf.write(
            "   sampling = %s\n" % SamplingMethods.getPsuadeName(data.getSampleMethod())
        )
        outf.write("   num_samples = %d\n" % data.getNumSamples())
        if data.getSampleMethod() != SamplingMethods.GMOAT:
            outf.write("   randomize\n")
        outf.write("END\n")

        # Write Application
        outf.write("APPLICATION\n")
        driverString = data.getDriverName()
        if driverString is None:
            driverString = "NONE"
        elif platform.system() == "Windows":
            if os.path.exists(driverString):
                import win32api

                driverString = win32api.GetShortPathName(driverString)
            else:
                driverString = "NONE"
        driverString = "NONE"

        outf.write("   driver = %s\n" % driverString)
        outf.write("   save_frequency = 1\n")
        outf.write("END\n")

        # Write Analysis
        outf.write("ANALYSIS\n")
        outf.write("   diagnostics 2\n")
        outf.write("END\n")

        outf.write("END\n")
        outf.close()

    @staticmethod
    def generateSamples(
        data, selectedInputs, selectedOutputs, numSamples=None, sampleMethod=-1
    ):
        psuadeDataFile = os.getcwd() + os.path.sep + "psuadeData"
        if os.path.exists(psuadeDataFile):
            os.remove(psuadeDataFile)

        # Create new SampleData object with only selected inputs and outputs
        newModel = Model()
        inputNames = numpy.array(data.getInputNames())
        newModel.setInputNames(inputNames[selectedInputs])
        outputNames = numpy.array(data.getOutputNames())
        newModel.setOutputNames(outputNames[selectedOutputs])
        newModel.setInputMins(data.getInputMins()[selectedInputs])
        newModel.setInputMaxs(data.getInputMaxs()[selectedInputs])
        newModel.setDriverName(data.getDriverName())
        if data.getInputDefaults() is not None:
            newModel.setInputDefaults(data.getInputDefaults()[selectedInputs])
        returnData = SampleData(newModel)

        if numSamples:
            returnData.setNumSamples(numSamples)
        else:
            returnData.setNumSamples(data.getNumSamples())

        if sampleMethod >= 0:
            returnData.setSampleMethod(sampleMethod)
        else:
            returnData.setSampleMethod(data.getSampleMethod())
        if returnData.getSampleMethod() == SamplingMethods.METIS and os.path.exists(
            "psuadeMetisInfo"
        ):
            os.remove("psuadeMetisInfo")

        distributions = data.getInputDistributions()
        pdfconvert = False
        for dist in distributions:
            distType = dist.getDistributionType()
            if returnData.getSampleMethod() != SamplingMethods.MC and distType not in [
                Distribution.SAMPLE,
                Distribution.UNIFORM,
            ]:
                pdfconvert = True
        returnData.setInputDistributions(distributions)

        curDir = os.getcwd()
        if platform.system() == "Windows":
            import win32api

            curDir = win32api.GetShortPathName(curDir)
        psuadeInFile = curDir + os.sep + "psuade.in"

        if pdfconvert:
            # omit non-uniform and non-sample PDF info from input file
            ExperimentalDesign.createPsuadeInFile(
                returnData, psuadeInFile, includePDF=False
            )
        else:
            ExperimentalDesign.createPsuadeInFile(
                returnData, psuadeInFile, includePDF=True
            )

        out, error = Common.invokePsuade(psuadeInFile)

        if os.path.exists(psuadeDataFile):
            showerr = True
            data = LocalExecutionModule.readSampleFromPsuadeFile(psuadeDataFile)
            if pdfconvert:
                os.remove(psuadeDataFile)
                tmpfile = os.getcwd() + os.path.sep + "tmp"
                y = 1
                # add back in the full PDF info
                RSAnalyzer.writeRSdata(tmpfile, y, data, inputPDF=distributions)
                # write script to PDF conversion
                f = tempfile.SpooledTemporaryFile()
                if platform.system() == "Windows":
                    import win32api

                    tmpfile = win32api.GetShortPathName(tmpfile)
                f.write(("load %s\n" % tmpfile).encode())
                f.write(b"pdfconvert\n")
                f.write(("write %s\n" % psuadeDataFile).encode())
                nOutputs = returnData.getNumOutputs()
                if nOutputs > 1:
                    f.write(b"n\n")  # write all outputs
                f.write(b"quit\n")
                f.seek(0)
                out, error = Common.invokePsuade(f)
                f.close()
                if os.path.exists(psuadeDataFile):
                    data = LocalExecutionModule.readSampleFromPsuadeFile(psuadeDataFile)
                    showerr = False
            else:
                showerr = False

            if showerr:
                error = "ExperimentalDesign: %s does not exist." % psuadeDataFile
                Common.showError(error, out)
                return None
            else:
                return data
