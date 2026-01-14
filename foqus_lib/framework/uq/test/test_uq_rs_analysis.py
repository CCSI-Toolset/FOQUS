#################################################################################
# FOQUS Copyright (c) 2012 - 2025, by the software owners: Oak Ridge Institute
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
import unittest
from unittest.mock import Mock
from foqus_lib.framework.uq.UQRSAnalysis import UQRSAnalysis
from foqus_lib.framework.uq.ResponseSurfaces import ResponseSurfaces
from foqus_lib.framework.uq.UQAnalysis import UQAnalysis


class ConcreteUQRSAnalysis(UQRSAnalysis):
    def analyze(self):
        pass

    def showResults(self):
        pass


class TestUQRSAnalysis(unittest.TestCase):
    def test_initialization(self):
        mock_ensemble = Mock()
        analysis = ConcreteUQRSAnalysis(
            mock_ensemble, [1], UQAnalysis.RS_VALIDATION, ResponseSurfaces.MARS
        )
        self.assertEqual(analysis.responseSurface, ResponseSurfaces.MARS)

    def test_save_load_dict(self):
        mock_ensemble = Mock()
        analysis = ConcreteUQRSAnalysis(
            mock_ensemble,
            [1],
            UQAnalysis.RS_VALIDATION,
            ResponseSurfaces.LEGENDRE,
            rsOptions={"legendreOrder": 3},
        )
        saved = analysis.saveDict()
        self.assertEqual(saved["rs"], ResponseSurfaces.LEGENDRE)
        self.assertEqual(saved["rsOptions"]["legendreOrder"], 3)
