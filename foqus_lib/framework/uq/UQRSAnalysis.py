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
import abc  # abstract base class
from collections import OrderedDict
from .ResponseSurfaces import ResponseSurfaces
from .UQAnalysis import UQAnalysis


class UQRSAnalysis(UQAnalysis, metaclass=abc.ABCMeta):
    def __init__(
        self,
        ensemble,
        output,
        analysisType,
        responseSurface,
        subType=None,
        rsOptions=None,
        userRegressionFile=None,
        xprior=None,
    ):
        super(UQRSAnalysis, self).__init__(ensemble, output, analysisType, subType)
        self.responseSurface = responseSurface
        self.rsOptions = rsOptions
        self.userRegressionFile = userRegressionFile
        self.xprior = xprior

    def saveDict(self):
        sd = super(UQRSAnalysis, self).saveDict()
        sd["rs"] = self.responseSurface
        sd["rsOptions"] = self.rsOptions
        if self.userRegressionFile is not None and len(self.userRegressionFile) > 0:
            self.archiveFile(self.userRegressionFile)
            sd["userRegressionFile"] = os.path.basename(self.userRegressionFile)
        sd["xprior"] = self.xprior
        return sd

    def loadDict(self, sd):
        super(UQRSAnalysis, self).loadDict(sd)
        self.responseSurface = sd.get("rs", None)
        self.rsOptions = sd.get("rsOptions", None)
        self.userRegressionFile = sd.get("userRegressionFile", None)
        if self.userRegressionFile is not None:
            self.userRegressionFile = self.restoreFromArchive(self.userRegressionFile)
        self.xprior = sd.get("xprior", None)

    def getResponseSurface(self):
        return self.responseSurface

    # MARS and Legendre Response surface info
    def setRSOptions(self, options):
        self.rsOptions = options

    def getRSOptions(self):
        return self.rsOptions

    #### Add RS coefficient code file?

    # Thresholds for RS Vis plot
    def setThresholds(self, lower, upper):
        self.lowerThreshold = lower
        self.upperThreshold = upper

    def getThresholds(self):
        return (self.lowerThreshold, self.upperThreshold)

    def getAdditionalInfo(self):
        info = OrderedDict()
        if not isinstance(self.responseSurface, (tuple, list)):
            rs = ResponseSurfaces.getEnumValue(self.responseSurface)
            if rs == ResponseSurfaces.LEGENDRE:
                if self.rsOptions is not None:
                    if isinstance(self.rsOptions, dict):
                        info["Legendre Polynomial Order"] = self.rsOptions[
                            "legendreOrder"
                        ]
                    else:
                        info["Legendre Poynomial Order"] = self.rsOptions
            elif rs in [ResponseSurfaces.MARS, ResponseSurfaces.MARSBAG]:  # MARS
                if self.rsOptions is not None:
                    info["Number of MARS basis functions"] = self.rsOptions["marsBases"]
                    info["MARS degree of interaction"] = self.rsOptions[
                        "marsInteractions"
                    ]
            elif rs == ResponseSurfaces.USER:
                if self.userRegressionFile is not None:
                    info["User Regression File"] = os.path.basename(
                        self.userRegressionFile
                    )

        # xprior info
        if self.xprior is not None:
            info["xprior"] = self.xprior

        return info
