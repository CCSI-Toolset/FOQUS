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

from unittest.mock import Mock

from foqus_lib.framework.uq.UQAnalysis import UQAnalysis
from foqus_lib.framework.uq.SensitivityAnalysis import SensitivityAnalysis
from foqus_lib.framework.uq.UncertaintyAnalysis import UncertaintyAnalysis


class TestUQAnalysis(unittest.TestCase):
    """Test cases for the UQAnalysis base class."""

    def setUp(self):
        # Create a mock ensemble for testing
        self.mock_ensemble = Mock()
        self.mock_ensemble.getOutputNames.return_value = ["output1", "output2"]

    def test_type_operations(self):
        """Test UQAnalysis type operations."""
        self.assertEqual(
            UQAnalysis.getTypeFullName(UQAnalysis.UNCERTAINTY), "Uncertainty Analysis"
        )
        self.assertEqual(
            UQAnalysis.getTypeEnumValue("Uncertainty Analysis"), UQAnalysis.UNCERTAINTY
        )

    def test_analysis_creation(self):
        """Test creating analysis instances."""
        # Test SensitivityAnalysis
        sa = SensitivityAnalysis(
            self.mock_ensemble, [1], SensitivityAnalysis.FIRST_ORDER
        )
        self.assertIsInstance(sa, SensitivityAnalysis)
        self.assertEqual(
            sa.getType(), (UQAnalysis.SENSITIVITY, SensitivityAnalysis.FIRST_ORDER)
        )

        # Test UncertaintyAnalysis
        ua = UncertaintyAnalysis(self.mock_ensemble, [1])
        self.assertIsInstance(ua, UncertaintyAnalysis)
        self.assertEqual(ua.getType(), (UQAnalysis.UNCERTAINTY, None))

    def test_output_operations(self):
        """Test output operations in UQAnalysis."""
        ua = UncertaintyAnalysis(self.mock_ensemble, [1])
        self.assertEqual(ua.getOutputs(), [1])

        ua.setOutputs([1, 2])
        self.assertEqual(ua.getOutputs(), [1, 2])

        # Test single output conversion to list
        ua.setOutputs(3)
        self.assertEqual(ua.getOutputs(), [3])
