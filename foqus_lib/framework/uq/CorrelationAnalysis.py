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


class CorrelationAnalysis(UQAnalysis):
    def __init__(self, ensemble, output):
        self.moments = None
        super(CorrelationAnalysis, self).__init__(
            ensemble, output, UQAnalysis.CORRELATION
        )

    def analyze(self):
        data = self.ensemble.getValidSamples()
        Common.initFolder(RawDataAnalyzer.dname)
        fname = Common.getLocalFileName(
            RawDataAnalyzer.dname, data.getModelName().split()[0], ".dat"
        )
        data.writeToPsuade(fname)

        # perform UA
        mfile = RawDataAnalyzer.performCA(fname, self.outputs[0])

        # archive file
        if mfile is not None:
            self.archiveFile(mfile)
        return mfile

    def showResults(self):
        # restore .m file from archive
        fileName = "matlabca.m"
        self.restoreFromArchive(fileName)

        RawDataAnalyzer.plotCA(self.ensemble, self.outputs[0], fileName)
