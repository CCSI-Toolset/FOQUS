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

from foqus_lib.framework.uq.SamplingMethods import SamplingMethods


class TestSamplingMethods(unittest.TestCase):
    """Test cases for SamplingMethods class"""

    def test_static_methods(self):
        """Test all static methods"""
        # Test getFullName
        self.assertEqual(SamplingMethods.getFullName(SamplingMethods.MC), "Monte Carlo")
        self.assertEqual(
            SamplingMethods.getFullName(SamplingMethods.LH), "Latin Hypercube"
        )
        self.assertEqual(
            SamplingMethods.getFullName(SamplingMethods.MOAT), "Morris Design"
        )

        # Test getPsuadeName
        self.assertEqual(SamplingMethods.getPsuadeName(SamplingMethods.MC), "MC")
        self.assertEqual(SamplingMethods.getPsuadeName(SamplingMethods.LPTAU), "LPTAU")
        self.assertEqual(SamplingMethods.getPsuadeName(SamplingMethods.OA), "OA")

        # Test getInfo
        info = SamplingMethods.getInfo(SamplingMethods.METIS)
        self.assertEqual(info, ("METIS", "METIS"))

        # Test getEnumValue
        self.assertEqual(
            SamplingMethods.getEnumValue("Monte Carlo"), SamplingMethods.MC
        )
        self.assertEqual(SamplingMethods.getEnumValue("LH"), SamplingMethods.LH)
        self.assertEqual(SamplingMethods.getEnumValue("FACT"), SamplingMethods.FACT)

    def test_validate_sample_size_lsa(self):
        """Test sample size validation for LSA"""
        nInputs = 5
        nSamples = 10

        result = SamplingMethods.validateSampleSize(
            SamplingMethods.LSA, nInputs, nSamples
        )
        self.assertEqual(result, nInputs + 1)  # LSA always returns nInputs + 1

    def test_validate_sample_size_moat_exact(self):
        """Test sample size validation for MOAT with exact multiple"""
        nInputs = 3
        nSamples = 12  # Exactly divisible by (nInputs + 1) = 4

        result = SamplingMethods.validateSampleSize(
            SamplingMethods.MOAT, nInputs, nSamples
        )
        self.assertEqual(result, nSamples)  # Should return the same value

    def test_validate_sample_size_moat_range(self):
        """Test sample size validation for MOAT with inexact multiple"""
        nInputs = 3
        nSamples = 10  # Not exactly divisible by (nInputs + 1) = 4

        result = SamplingMethods.validateSampleSize(
            SamplingMethods.MOAT, nInputs, nSamples
        )
        self.assertEqual(result, (8, 12))  # Should return (floor*M, ceil*M)

    def test_validate_sample_size_gmoat(self):
        """Test sample size validation for GMOAT"""
        nInputs = 2
        nSamples = 5  # Not exactly divisible by (nInputs + 1) = 3

        result = SamplingMethods.validateSampleSize(
            SamplingMethods.GMOAT, nInputs, nSamples
        )
        self.assertEqual(result, (3, 6))  # Should return (floor*M, ceil*M)

    def test_validate_sample_size_other_methods(self):
        """Test sample size validation for other methods"""
        nInputs = 4
        nSamples = 100

        for method in [
            SamplingMethods.MC,
            SamplingMethods.LH,
            SamplingMethods.OA,
            SamplingMethods.METIS,
            SamplingMethods.GMETIS,
            SamplingMethods.FACT,
        ]:
            result = SamplingMethods.validateSampleSize(method, nInputs, nSamples)
            self.assertEqual(result, nSamples)  # Should return unchanged

    def test_enum_consistency(self):
        """Test that enum values are consistent with array indices"""
        # Test that all enum values correspond to valid array indices
        for i, (full_name, psuade_name) in enumerate(
            zip(SamplingMethods.fullNames, SamplingMethods.psuadeNames)
        ):
            self.assertEqual(SamplingMethods.getFullName(i), full_name)
            self.assertEqual(SamplingMethods.getPsuadeName(i), psuade_name)
            # self.assertEqual(SamplingMethods.getEnumValue(full_name), i)
            self.assertEqual(SamplingMethods.getEnumValue(psuade_name), i)
