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
import numpy
from .UQRSAnalysis import UQRSAnalysis
from .ResponseSurfaces import ResponseSurfaces
from .UQAnalysis import UQAnalysis
from .Visualizer import Visualizer
from .Common import Common


class RSVisualization(UQRSAnalysis):

    psuadeNames = ["rssobol1", "rssobol2", "rssoboltsi"]

    def __init__(
        self,
        ensemble,
        output,
        inputs,
        responseSurface,
        minVal,
        maxVal,
        rsOptions=None,
        userRegressionFile=None,
    ):
        super(RSVisualization, self).__init__(
            ensemble,
            output,
            UQAnalysis.RS_VISUALIZATION,
            responseSurface,
            None,
            rsOptions,
            userRegressionFile,
            None,
        )
        self.minVal = minVal
        self.maxVal = maxVal

        if not isinstance(inputs, (tuple, list)):
            inputs = [inputs]
        self.setInputs(inputs)
        # xlist = numpy.array(inputs)
        # k = numpy.where(xlist > 0)
        # self.x = xlist[k]
        # rsdim = len(self.x)
        rsdim = len(inputs)
        self.cmd = "rs%d" % rsdim

    def saveDict(self):
        sd = super(RSVisualization, self).saveDict()
        sd["minVal"] = self.minVal
        sd["maxVal"] = self.maxVal
        return sd

    def loadDict(self, sd):
        super(RSVisualization, self).loadDict(sd)
        self.minVal = sd.get("minVal", None)
        self.maxVal = sd.get("maxVal", None)

    def analyze(self):
        Common.initFolder(Visualizer.dname)

        data = self.ensemble
        data = data.getValidSamples()  # filter out samples that have no output results

        fname = Common.getLocalFileName(
            Visualizer.dname, data.getModelName().split()[0], ".dat"
        )
        index = ResponseSurfaces.getEnumValue(self.responseSurface)
        fixedAsVariables = index == ResponseSurfaces.USER
        data.writeToPsuade(fname, fixedAsVariables=fixedAsVariables)
        rsdim = len(self.inputs)

        inNames = data.getInputNames()
        plotInNames = [inNames[i - 1] for i in self.inputs]
        if self.legendreOrder is not None:
            mfile = Visualizer.showRS(
                fname,
                self.outputs[0],
                plotInNames,
                rsdim,
                self.responseSurface,
                vmin=self.minVal,
                vmax=self.maxVal,
                rsOptions=self.rsOptions,
                userRegressionFile=self.userRegressionFile,
            )
        else:
            mfile = Visualizer.showRS(
                fname,
                self.outputs[0],
                plotInNames,
                rsdim,
                self.responseSurface,
                vmin=self.minVal,
                vmax=self.maxVal,
                userRegressionFile=self.userRegressionFile,
            )
        if mfile is not None:
            self.archiveFile(mfile)
        return mfile

    def showResults(self):
        cmd = "rs%d" % len(self.inputs)
        mfile = "matlab" + cmd + ".m"
        self.restoreFromArchive(mfile)

        ngrid = 0
        if len(self.inputs) == 2:
            ngrid = 256  # select grid resolution (32-256)
        elif len(self.inputs) == 3:
            ngrid = 32  # select grid resolution (16-32)

        inNames = self.ensemble.getInputNames()
        x = [index + 1 for index in self.inputs]

        Visualizer.showRSPlot(
            self.ensemble,
            self.outputs[0],
            x,
            len(self.inputs),
            ngrid,
            self.responseSurface,
            self.minVal,
            self.maxVal,
            mfile,
        )

    def getAdditionalInfo(self):
        info = super(RSVisualization, self).getAdditionalInfo()
        info["Upper Threshold"] = self.maxVal
        info["Lower Threshold"] = self.minVal
        return info
