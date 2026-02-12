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

from foqus_lib.framework.uq.ResponseSurfaces import ResponseSurfaces


class TestResponseSurfaces(unittest.TestCase):
    """Test cases for the ResponseSurfaces class."""

    def test_enum_values(self):
        """Test response surface enumeration values."""
        self.assertEqual(ResponseSurfaces.MARS, 0)
        self.assertEqual(ResponseSurfaces.LINEAR, 1)
        self.assertEqual(ResponseSurfaces.QUADRATIC, 2)

    def test_full_names(self):
        """Test getting full names."""
        self.assertEqual(ResponseSurfaces.getFullName(ResponseSurfaces.MARS), "MARS")
        self.assertEqual(
            ResponseSurfaces.getFullName(ResponseSurfaces.LINEAR), "Linear Regression"
        )

    def test_psuade_names(self):
        """Test getting PSUADE names."""
        self.assertEqual(ResponseSurfaces.getPsuadeName(ResponseSurfaces.MARS), "MARS")
        self.assertEqual(
            ResponseSurfaces.getPsuadeName(ResponseSurfaces.LINEAR), "linear"
        )

    def test_enum_value_conversion(self):
        """Test converting names to enum values."""
        self.assertEqual(ResponseSurfaces.getEnumValue("MARS"), ResponseSurfaces.MARS)
        self.assertEqual(
            ResponseSurfaces.getEnumValue("Linear Regression"), ResponseSurfaces.LINEAR
        )

    def test_legendre_operations(self):
        """Test Legendre polynomial operations."""
        # Test max order calculation
        max_order = ResponseSurfaces.getLegendreMaxOrder(2, 10)
        self.assertIsInstance(max_order, int)
        self.assertGreaterEqual(max_order, 0)

        # Test minimum sample size calculation
        min_samples = ResponseSurfaces.getPolynomialMinSampleSize(2, 3)
        self.assertIsInstance(min_samples, (int, float))
        self.assertGreater(min_samples, 0)
