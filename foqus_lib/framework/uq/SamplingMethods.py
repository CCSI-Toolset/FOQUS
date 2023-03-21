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
import numpy as np


class SamplingMethods:
    MC, LPTAU, LH, OA, MOAT, GMOAT, LSA, METIS, GMETIS, FACT = list(range(10))
    fullNames = (
        "Monte Carlo",
        "Quasi Monte Carlo",
        "Latin Hypercube",
        "Orthogonal Array",
        "Morris Design",
        "Generalized Morris Design",
        "Gradient Sample",
        "METIS",
        "Monte Carlo",
        "Full Factorial Design",
    )
    psuadeNames = (
        "MC",
        "LPTAU",
        "LH",
        "OA",
        "MOAT",
        "GMOAT",
        "LSA",
        "METIS",
        "GMETIS",
        "FACT",
    )

    @staticmethod
    def getFullName(num):
        return SamplingMethods.fullNames[num]

    @staticmethod
    def getPsuadeName(num):
        return SamplingMethods.psuadeNames[num]

    @staticmethod
    def getInfo(num):
        return (SamplingMethods.fullNames[num], SamplingMethods.psuadeNames[num])

    @staticmethod
    def getEnumValue(name):
        try:
            index = SamplingMethods.fullNames.index(name)
            return index
        except ValueError:
            index = SamplingMethods.psuadeNames.index(name)
            return index

    @staticmethod
    def validateSampleSize(num, nInputs, nSamples):
        if num == SamplingMethods.LSA:
            return nInputs + 1
        elif num == SamplingMethods.MOAT or num == SamplingMethods.GMOAT:
            M = float(nInputs + 1)
            a = np.floor(float(nSamples) / M) * M
            b = np.ceil(float(nSamples) / M) * M
            if a == b:
                return nSamples
            else:
                return (a, b)
        else:
            return nSamples
