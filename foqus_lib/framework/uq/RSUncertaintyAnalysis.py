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
from .UQRSAnalysis import UQRSAnalysis
from .UQAnalysis import UQAnalysis
from .ResponseSurfaces import ResponseSurfaces
from .RSAnalyzer import RSAnalyzer
from .Common import Common


class RSUncertaintyAnalysis(UQRSAnalysis):

    ALEATORY_ONLY, ALEATORY_EPISTEMIC = list(range(2))

    def __init__(
        self,
        ensemble,
        output,
        subType,
        responseSurface,
        rsOptions=None,
        userRegressionFile=None,
        xprior=None,
    ):
        super(RSUncertaintyAnalysis, self).__init__(
            ensemble,
            output,
            UQAnalysis.RS_UNCERTAINTY,
            responseSurface,
            subType,
            rsOptions,
            userRegressionFile,
            xprior,
        )

    def analyze(self):
        data = self.ensemble
        fnameRS = Common.getLocalFileName(
            RSAnalyzer.dname, data.getModelName().split()[0], ".rsdat"
        )
        index = ResponseSurfaces.getEnumValue(self.responseSurface)
        fixedAsVariables = index == ResponseSurfaces.USER
        data.writeToPsuade(fnameRS, fixedAsVariables=fixedAsVariables)
        if self.subType == RSUncertaintyAnalysis.ALEATORY_ONLY:
            (sfile, mfile) = RSAnalyzer.performUA(
                fnameRS,
                self.outputs[0],
                self.responseSurface,
                self.rsOptions,
                self.userRegressionFile,
                self.xprior,
            )
            self.archiveFile(sfile)
        else:
            mfile = RSAnalyzer.performAEUA(
                fnameRS,
                self.outputs[0],
                self.responseSurface,
                self.rsOptions,
                self.userRegressionFile,
                self.xprior,
            )
        if mfile is not None:
            self.archiveFile(mfile)
        return mfile

    def showResults(self):
        if self.subType == RSUncertaintyAnalysis.ALEATORY_ONLY:
            mfile = "matlabrsua.m"
            sfile = "rsua_sample"
            self.restoreFromArchive(mfile)
            self.restoreFromArchive(sfile)
            RSAnalyzer.plotUA(
                self.ensemble, self.outputs[0], self.responseSurface, sfile, mfile
            )
        else:
            mfile = "matlabaeua.m"
            self.restoreFromArchive(mfile)
            RSAnalyzer.plotAEUA(
                self.ensemble, self.outputs[0], self.responseSurface, mfile
            )
