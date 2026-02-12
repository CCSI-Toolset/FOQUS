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

from foqus_lib.framework.uq.ParameterScreening import ParameterScreening


class TestParameterScreening(unittest.TestCase):
    """Test cases for ParameterScreening class"""

    def setUp(self):
        """Set up test parameter screening"""
        self.mock_ensemble = Mock()
        self.mock_output = "test_output"

    def test_static_methods(self):
        """Test static utility methods"""
        # Test getSubTypeFullName
        self.assertEqual(
            ParameterScreening.getSubTypeFullName(ParameterScreening.MOAT), "MOAT"
        )
        self.assertEqual(
            ParameterScreening.getSubTypeFullName(ParameterScreening.LSA),
            "Local Sensitivity Analysis",
        )

        # Test getSubTypePsuadeName
        self.assertEqual(
            ParameterScreening.getSubTypePsuadeName(ParameterScreening.MOAT), "moat"
        )
        self.assertEqual(
            ParameterScreening.getSubTypePsuadeName(ParameterScreening.MARSRANK),
            "mars_sa",
        )

        # Test getInfo
        info = ParameterScreening.getInfo(ParameterScreening.SOT)
        self.assertEqual(info, ("Sum of Trees", "sot_sa"))

        # Test getEnumValue
        self.assertEqual(
            ParameterScreening.getEnumValue("MOAT"), ParameterScreening.MOAT
        )
        self.assertEqual(
            ParameterScreening.getEnumValue("delta_test"), ParameterScreening.DELTA
        )

    def test_initialization(self):
        """Test ParameterScreening initialization"""
        ps = ParameterScreening(
            self.mock_ensemble, self.mock_output, ParameterScreening.MOAT
        )

        self.assertEqual(ps.ensemble, self.mock_ensemble)
        self.assertEqual(ps.outputs, ["test_output"])
        self.assertEqual(ps.subType, ParameterScreening.MOAT)

    @patch("foqus_lib.framework.uq.ParameterScreening.RawDataAnalyzer.screenInputs")
    @patch("foqus_lib.framework.uq.ParameterScreening.Common.initFolder")
    def test_analyze(self, mock_init_folder, mock_screen):
        """Test parameter screening analysis"""
        # Set up mocks
        mock_data = Mock()
        mock_data.getModelName.return_value = "test_model"
        mock_data.writeToPsuade = Mock()
        self.mock_ensemble.getValidSamples.return_value = mock_data

        mock_screen.return_value = "screening_results.m"

        ps = ParameterScreening(
            self.mock_ensemble, self.mock_output, ParameterScreening.LSA
        )
        ps.archiveFile = Mock()  # Mock inherited method

        result = ps.analyze()

        mock_init_folder.assert_called_once()
        mock_screen.assert_called_once()
        ps.archiveFile.assert_called_once_with("screening_results.m")
        self.assertEqual(result, "screening_results.m")

    @patch("foqus_lib.framework.uq.ParameterScreening.RawDataAnalyzer.plotScreenInputs")
    def test_show_results(self, mock_plot):
        """Test showing parameter screening results"""
        ps = ParameterScreening(
            self.mock_ensemble, self.mock_output, ParameterScreening.DELTA
        )
        ps.restoreFromArchive = Mock()  # Mock inherited method

        ps.showResults()

        expected_filename = ParameterScreening.outFileNames[ParameterScreening.DELTA]
        ps.restoreFromArchive.assert_called_once_with(expected_filename)
        mock_plot.assert_called_once()
