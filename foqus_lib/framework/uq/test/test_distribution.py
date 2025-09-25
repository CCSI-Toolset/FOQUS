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

from foqus_lib.framework.uq.Distribution import Distribution


class TestDistribution(unittest.TestCase):
    """Test cases for the Distribution class"""

    def test_static_methods(self):
        """Test all static methods"""
        # Test getFullName
        self.assertEqual(Distribution.getFullName(Distribution.UNIFORM), "Uniform")
        self.assertEqual(Distribution.getFullName(Distribution.NORMAL), "Normal")
        self.assertEqual(Distribution.getFullName(Distribution.LOGNORMAL), "Lognormal")

        # Test getPsuadeName
        self.assertEqual(Distribution.getPsuadeName(Distribution.UNIFORM), "U")
        self.assertEqual(Distribution.getPsuadeName(Distribution.NORMAL), "N")
        self.assertEqual(Distribution.getPsuadeName(Distribution.BETA), "B")

        # Test getInfo
        info = Distribution.getInfo(Distribution.GAMMA)
        self.assertEqual(info, ("Gamma", "G"))

        # Test getEnumValue
        self.assertEqual(Distribution.getEnumValue("Uniform"), Distribution.UNIFORM)
        self.assertEqual(Distribution.getEnumValue("N"), Distribution.NORMAL)
        self.assertEqual(Distribution.getEnumValue("T"), Distribution.TRIANGLE)

        # Test getParameterNames
        params = Distribution.getParameterNames(Distribution.NORMAL)
        self.assertEqual(params, ("Mean", "Std Dev"))

        params = Distribution.getParameterNames(Distribution.UNIFORM)
        self.assertEqual(params, (None, None))

        params = Distribution.getParameterNames(Distribution.EXPONENTIAL)
        self.assertEqual(params, ("Lambda", None))

    def test_distribution_creation_with_enum(self):
        """Test creating distribution with enum values"""
        dist = Distribution(Distribution.NORMAL)
        self.assertEqual(dist.getDistributionType(), Distribution.NORMAL)

    def test_distribution_creation_with_string(self):
        """Test creating distribution with string values"""
        dist = Distribution("Normal")
        self.assertEqual(dist.getDistributionType(), Distribution.NORMAL)

        dist = Distribution("L")  # Lognormal
        self.assertEqual(dist.getDistributionType(), Distribution.LOGNORMAL)

    def test_parameter_values(self):
        """Test setting and getting parameter values"""
        dist = Distribution(Distribution.NORMAL)

        # Initially None
        self.assertEqual(dist.getParameterValues(), (None, None))

        # Set both parameters
        dist.setParameterValues(10.0, 2.5)
        self.assertEqual(dist.getParameterValues(), (10.0, 2.5))

        # Set only first parameter
        dist.setParameterValues(15.0)
        self.assertEqual(dist.getParameterValues(), (15.0, None))

    def test_repr(self):
        """Test string representation"""
        dist = Distribution(Distribution.NORMAL)
        self.assertIn("N Distribution", repr(dist))

        dist.setParameterValues(10.0, 2.0)
        repr_str = repr(dist)
        self.assertIn("N Distribution", repr_str)
        self.assertIn("10.0", repr_str)
        self.assertIn("2.0", repr_str)

    def test_save_load_dict(self):
        """Test saving and loading distribution to/from dictionary"""
        dist = Distribution(Distribution.GAMMA)
        dist.setParameterValues(2.0, 1.5)

        # Save to dict
        saved = dist.saveDict()
        self.assertEqual(saved["type"], "G")
        self.assertEqual(saved["firstParamValue"], 2.0)
        self.assertEqual(saved["secondParamValue"], 1.5)

        # Load from dict
        new_dist = Distribution(Distribution.UNIFORM)  # Start with different type
        new_dist.loadDict(saved)
        self.assertEqual(new_dist.getDistributionType(), Distribution.GAMMA)
        self.assertEqual(new_dist.getParameterValues(), (2.0, 1.5))

    def test_distribution_type_changes(self):
        """Test changing distribution type"""
        dist = Distribution(Distribution.UNIFORM)
        self.assertEqual(dist.getDistributionType(), Distribution.UNIFORM)

        dist.setDistributionType(Distribution.WEIBULL)
        self.assertEqual(dist.getDistributionType(), Distribution.WEIBULL)

        dist.setDistributionType("Beta")
        self.assertEqual(dist.getDistributionType(), Distribution.BETA)
