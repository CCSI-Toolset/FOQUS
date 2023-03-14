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
from .UQAnalysis import UQAnalysis
from .RawDataAnalyzer import RawDataAnalyzer
from .Common import Common


class UncertaintyAnalysis(UQAnalysis):
    def __init__(self, ensemble, output):
        self.moments = None
        super(UncertaintyAnalysis, self).__init__(
            ensemble, output, UQAnalysis.UNCERTAINTY
        )

    def saveDict(self):
        sd = super(UncertaintyAnalysis, self).saveDict()
        sd["moments"] = self.moments
        return sd

    def loadDict(self, sd):
        super(UncertaintyAnalysis, self).loadDict(sd)
        self.moments = sd.get("moments", None)

    def analyze(self):
        data = self.ensemble.getValidSamples()
        Common.initFolder(RawDataAnalyzer.dname)
        fname = Common.getLocalFileName(
            RawDataAnalyzer.dname, data.getModelName().split()[0], ".dat"
        )
        data.writeToPsuade(fname, fixedAsVariables=True)

        # perform UA
        mfile, self.moments = RawDataAnalyzer.performUA(fname, self.outputs[0])

        # archive file
        if mfile is not None:
            self.archiveFile(mfile)

        return mfile

    def showResults(self):
        # restore .m file from archive
        fileName = "matlabua.m"
        self.restoreFromArchive(fileName)

        RawDataAnalyzer.plotUA(self.ensemble, self.outputs[0], fileName, self.moments)
