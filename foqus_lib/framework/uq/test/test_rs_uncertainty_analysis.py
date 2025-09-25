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

from foqus_lib.framework.uq.ResponseSurfaces import ResponseSurfaces
from foqus_lib.framework.uq.RSUncertaintyAnalysis import RSUncertaintyAnalysis
from foqus_lib.framework.uq.RSValidation import RSValidation
from foqus_lib.framework.uq.RSVisualization import RSVisualization


class TestRSAnalyses(unittest.TestCase):
    """Test cases for Response Surface analysis classes."""

    def setUp(self):
        # Create mock ensemble
        self.mock_ensemble = Mock()
        self.mock_ensemble.getOutputNames.return_value = ["output1"]
        self.mock_ensemble.getInputNames.return_value = ["input1", "input2"]
        self.mock_ensemble.getValidSamples.return_value = Mock()

    def test_rs_uncertainty_analysis(self):
        """Test RSUncertaintyAnalysis initialization."""
        rs_ua = RSUncertaintyAnalysis(
            ensemble=self.mock_ensemble,
            output=[1],
            subType=RSUncertaintyAnalysis.ALEATORY_ONLY,
            responseSurface=ResponseSurfaces.MARS,
        )

        self.assertIsInstance(rs_ua, RSUncertaintyAnalysis)
        self.assertEqual(rs_ua.getResponseSurface(), ResponseSurfaces.MARS)
        self.assertEqual(rs_ua.subType, RSUncertaintyAnalysis.ALEATORY_ONLY)

    def test_rs_validation(self):
        """Test RSValidation initialization."""
        rs_val = RSValidation(
            ensemble=self.mock_ensemble,
            output=[1],
            responseSurface=ResponseSurfaces.LINEAR,
            nCV=5,
        )

        self.assertIsInstance(rs_val, RSValidation)
        self.assertEqual(rs_val.nCV, 5)
        self.assertEqual(rs_val.getResponseSurface(), ResponseSurfaces.LINEAR)

    def test_rs_visualization(self):
        """Test RSVisualization initialization."""
        rs_viz = RSVisualization(
            ensemble=self.mock_ensemble,
            output=[1],
            inputs=[1, 2],
            responseSurface=ResponseSurfaces.QUADRATIC,
            minVal=0.0,
            maxVal=1.0,
        )

        self.assertIsInstance(rs_viz, RSVisualization)
        self.assertEqual(rs_viz.minVal, 0.0)
        self.assertEqual(rs_viz.maxVal, 1.0)
        self.assertEqual(rs_viz.getInputs(), [1, 2])

    def test_rs_options(self):
        """Test response surface options handling."""
        rs_options = {"legendreOrder": 3}

        rs_ua = RSUncertaintyAnalysis(
            ensemble=self.mock_ensemble,
            output=[1],
            subType=RSUncertaintyAnalysis.ALEATORY_ONLY,
            responseSurface=ResponseSurfaces.LEGENDRE,
            rsOptions=rs_options,
        )

        self.assertEqual(rs_ua.getRSOptions(), rs_options)

    def test_save_load_dict_rs(self):
        """Test saving and loading RS analysis state."""
        rs_ua = RSUncertaintyAnalysis(
            ensemble=self.mock_ensemble,
            output=[1],
            subType=RSUncertaintyAnalysis.ALEATORY_ONLY,
            responseSurface=ResponseSurfaces.MARS,
        )

        saved_dict = rs_ua.saveDict()
        self.assertIn("rs", saved_dict)
        self.assertIn("rsOptions", saved_dict)
        self.assertEqual(saved_dict["rs"], ResponseSurfaces.MARS)
