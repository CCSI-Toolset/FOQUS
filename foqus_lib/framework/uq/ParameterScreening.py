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


class ParameterScreening(UQAnalysis):
    MOAT, LSA, MARSRANK, SOT, DELTA, GP = list(range(6))

    fullNames = (
        "MOAT",
        "Local Sensitivity Analysis",
        "MARS Ranking",
        "Sum of Trees",
        "Delta Test",
        "Gaussian Process",
    )
    psuadeNames = ("moat", "lsa", "mars_sa", "sot_sa", "delta_test", "gp_sa")

    outFileNames = (
        "matlabmoatbs.m",
        "matlablsa.m",
        "matlabmarsa.m",
        "matlabsot.m",
        "matlabdelta.m",
        "matlabkrisa.m",
    )

    @staticmethod
    def getSubTypeFullName(num):
        return ParameterScreening.fullNames[num]

    @staticmethod
    def getSubTypePsuadeName(num):
        return ParameterScreening.psuadeNames[num]

    @staticmethod
    def getInfo(num):
        return (ParameterScreening.fullNames[num], ParameterScreening.psuadeNames[num])

    @staticmethod
    def getEnumValue(name):
        try:
            index = ParameterScreening.fullNames.index(name)
            return index
        except ValueError:
            index = ParameterScreening.psuadeNames.index(name)
            return index

    def __init__(self, ensemble, output, subType):
        super(ParameterScreening, self).__init__(
            ensemble, output, UQAnalysis.PARAM_SCREEN, subType
        )

    def analyze(self):
        data = self.ensemble.getValidSamples()
        Common.initFolder(RawDataAnalyzer.dname)
        fname = Common.getLocalFileName(
            RawDataAnalyzer.dname, data.getModelName().split()[0], ".dat"
        )
        data.writeToPsuade(fname)

        # perform screening
        cmd = ParameterScreening.getSubTypePsuadeName(self.subType)
        mfile = RawDataAnalyzer.screenInputs(fname, self.outputs[0], cmd)

        if mfile is not None:
            # archive file
            self.archiveFile(mfile)

        return mfile

    def showResults(self):
        # restore .m file from archive
        fileName = ParameterScreening.outFileNames[self.subType]
        self.restoreFromArchive(fileName)

        cmd = ParameterScreening.getSubTypePsuadeName(self.subType)
        RawDataAnalyzer.plotScreenInputs(self.ensemble, cmd, self.outputs[0], fileName)
