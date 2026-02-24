#################################################################################
# FOQUS Copyright (c) 2012 - 2026, by the software owners: Oak Ridge Institute
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


class TestCorrelationAnalysis(unittest.TestCase):
    """Test cases for CorrelationAnalysis"""

    def setUp(self):
        """Set up test correlation analysis"""
        from foqus_lib.framework.uq.CorrelationAnalysis import CorrelationAnalysis

        # Mock ensemble and output
        self.mock_ensemble = Mock()
        self.mock_output = "test_output"

        self.ca = CorrelationAnalysis(self.mock_ensemble, self.mock_output)

    def test_initialization(self):
        """Test CorrelationAnalysis initialization"""
        # Test that the object was created successfully
        self.assertIsNotNone(self.ca)

        # Test that ensemble and outputs are set correctly
        self.assertEqual(self.ca.ensemble, self.mock_ensemble)
        self.assertEqual(self.ca.outputs, ["test_output"])

        # Test that moments is initialized to None
        self.assertIsNone(self.ca.moments)

        # If there's a way to check the analysis type, we can test it
        # For now, we'll just verify the object is properly instantiated

    @patch("foqus_lib.framework.uq.CorrelationAnalysis.RawDataAnalyzer.performCA")
    @patch("foqus_lib.framework.uq.CorrelationAnalysis.Common.initFolder")
    def test_analyze(self, mock_init_folder, mock_perform_ca):
        """Test correlation analysis"""
        # Mock valid samples
        mock_data = Mock()
        mock_data.getModelName.return_value = "test_model"
        mock_data.writeToPsuade = Mock()
        self.mock_ensemble.getValidSamples.return_value = mock_data

        mock_perform_ca.return_value = "results.m"

        result = self.ca.analyze()

        mock_init_folder.assert_called_once()
        mock_perform_ca.assert_called_once()
        self.assertEqual(result, "results.m")

    @patch("foqus_lib.framework.uq.CorrelationAnalysis.RawDataAnalyzer.plotCA")
    def test_show_results(self, mock_plot_ca):
        """Test showing correlation analysis results"""
        # Mock the archiveFile and restoreFromArchive methods
        self.ca.archiveFile = Mock()
        self.ca.restoreFromArchive = Mock()

        # Call showResults
        self.ca.showResults()

        # Verify that restoreFromArchive was called with the correct filename
        self.ca.restoreFromArchive.assert_called_once_with("matlabca.m")

        # Verify that plotCA was called with correct parameters
        mock_plot_ca.assert_called_once_with(
            self.mock_ensemble, "test_output", "matlabca.m"
        )
