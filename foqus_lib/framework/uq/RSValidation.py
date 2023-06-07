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
from .UQRSAnalysis import UQRSAnalysis
from .UQAnalysis import UQAnalysis
from .RSAnalyzer import RSAnalyzer
from .ResponseSurfaces import ResponseSurfaces
from .Common import Common


class RSValidation(UQRSAnalysis):
    def __init__(
        self,
        ensemble,
        output,
        responseSurface,
        rsOptions=None,
        genCodeFile=False,
        nCV=10,
        userRegressionFile=None,
        testFile=None,
        error_tol_percent=10,
        odoe=False,
    ):
        super(RSValidation, self).__init__(
            ensemble,
            output,
            UQAnalysis.RS_VALIDATION,
            responseSurface,
            None,
            rsOptions,
            userRegressionFile,
            None,
        )
        self.genCodeFile = genCodeFile
        if nCV is None:
            nCV = 10
        self.nCV = nCV
        self.testFile = testFile
        self.error_tol_percent = error_tol_percent
        self.odoe = odoe

    def saveDict(self):
        sd = super(RSValidation, self).saveDict()
        sd["genCodeFile"] = self.genCodeFile
        sd["nCV"] = self.nCV
        if self.testFile is not None:
            self.archiveFile(self.testFile)
            sd["testFile"] = os.path.basename(self.testFile)
        return sd

    def loadDict(self, sd):
        super(RSValidation, self).loadDict(sd)
        self.genCodeFile = sd.get("genCodeFile", False)
        self.nCV = sd.get("nCV", 10)
        self.testFile = sd.get("testFile", None)
        if self.testFile is not None:
            self.testFile = self.restoreFromArchive(self.testFile)

    def analyze(self):
        data = self.ensemble
        fname = Common.getLocalFileName(
            RSAnalyzer.dname, data.getModelName().split()[0], ".dat"
        )
        index = ResponseSurfaces.getEnumValue(self.responseSurface)
        fixedAsVariables = index == ResponseSurfaces.USER
        data.writeToPsuade(fname, fixedAsVariables=fixedAsVariables)

        mfile = RSAnalyzer.validateRS(
            fname,
            self.outputs[0],
            self.responseSurface,
            self.rsOptions,
            self.genCodeFile,
            self.nCV,
            self.userRegressionFile,
            self.testFile,
            self.error_tol_percent,
        )

        if mfile is None:
            return None

        mfile = mfile[0]
        if not self.odoe:
            self.archiveFile(mfile)
        return mfile

    def showResults(self):
        rsIndex = ResponseSurfaces.getEnumValue(self.responseSurface)
        userMethod = rsIndex == ResponseSurfaces.USER
        if userMethod:
            mfile = "RSTest_hs.m"
        else:
            mfile = "RSFA_CV_err.m"
        self.restoreFromArchive(mfile)

        RSAnalyzer.plotValidate(
            self.ensemble,
            self.outputs[0],
            self.responseSurface,
            userMethod,
            mfile,
            error_tol_percent=self.error_tol_percent,
        )

    def getAdditionalInfo(self):
        info = super(RSValidation, self).getAdditionalInfo()
        info["Number of cross-validation groups"] = self.nCV
        if self.testFile is not None:
            info["Separate test file"] = os.path.basename(self.testFile)

        return info
