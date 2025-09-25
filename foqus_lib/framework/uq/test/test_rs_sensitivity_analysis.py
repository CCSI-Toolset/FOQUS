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
from unittest.mock import Mock, patch

from foqus_lib.framework.uq.RSSensitivityAnalysis import RSSensitivityAnalysis


class TestRSSensitivityAnalysis(unittest.TestCase):
    """Test cases for RSSensitivityAnalysis class"""

    def setUp(self):
        """Set up test RS sensitivity analysis"""
        self.mock_ensemble = Mock()
        self.mock_output = "test_output"
        self.response_surface = "MARS"

    def test_static_methods(self):
        """Test static utility methods"""
        from foqus_lib.framework.uq.SensitivityAnalysis import SensitivityAnalysis

        # Test getSubTypeFullName (should delegate to SensitivityAnalysis)
        name = RSSensitivityAnalysis.getSubTypeFullName(0)
        # This will depend on SensitivityAnalysis implementation
        self.assertIsInstance(name, str)

    def test_initialization(self):
        """Test RSSensitivityAnalysis initialization"""
        rssa = RSSensitivityAnalysis(
            self.mock_ensemble, self.mock_output, 0, self.response_surface  # subType
        )

        self.assertEqual(rssa.ensemble, self.mock_ensemble)
        self.assertEqual(rssa.outputs, ["test_output"])
        self.assertEqual(rssa.responseSurface, self.response_surface)
        self.assertEqual(rssa.subType, 0)
        self.assertIsInstance(rssa.showErrorBars, bool)

    @patch("foqus_lib.framework.uq.RSSensitivityAnalysis.RSAnalyzer.performSA")
    @patch("foqus_lib.framework.uq.RSSensitivityAnalysis.ResponseSurfaces.getEnumValue")
    def test_analyze(self, mock_get_enum, mock_perform_sa):
        """Test RS sensitivity analysis"""
        mock_get_enum.return_value = 0
        mock_perform_sa.return_value = "sa_results.m"

        # Mock ensemble methods
        self.mock_ensemble.getModelName.return_value = "test_model"
        self.mock_ensemble.writeToPsuade = Mock()

        rssa = RSSensitivityAnalysis(
            self.mock_ensemble, self.mock_output, 0, self.response_surface
        )
        rssa.archiveFile = Mock()  # Mock inherited method

        result = rssa.analyze()

        mock_perform_sa.assert_called_once()
        rssa.archiveFile.assert_called_once_with("sa_results.m")
        self.assertEqual(result, "sa_results.m")

    @patch("foqus_lib.framework.uq.RSSensitivityAnalysis.RSAnalyzer.plotSA")
    def test_show_results(self, mock_plot_sa):
        """Test showing RS sensitivity analysis results"""
        rssa = RSSensitivityAnalysis(
            self.mock_ensemble, self.mock_output, 0, self.response_surface
        )
        rssa.restoreFromArchive = Mock()  # Mock inherited method

        rssa.showResults()

        expected_filename = "matlabrssobol1.m"
        rssa.restoreFromArchive.assert_called_once_with(expected_filename)
        mock_plot_sa.assert_called_once()
