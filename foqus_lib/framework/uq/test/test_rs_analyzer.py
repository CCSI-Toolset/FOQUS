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
import numpy as np
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from foqus_lib.framework.uq.Distribution import Distribution
from foqus_lib.framework.uq.RSAnalyzer import RSAnalyzer


class TestRSAnalyzer(unittest.TestCase):
    """Test cases for RSAnalyzer class"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        RSAnalyzer.dname = self.test_dir

    def test_write_rs_sample_basic(self):
        """Test writing RS sample files"""
        x = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".dat", delete=False) as f:
            temp_file = f.name

        try:
            RSAnalyzer.writeRSsample(temp_file, x)

            # Verify file was created and has correct content
            with open(temp_file, "r") as f:
                lines = f.readlines()

            # Check header: 3 samples, 2 inputs
            self.assertIn("3 2", lines[0])

            # Check data format
            self.assertEqual(len(lines), 4)  # header + 3 data lines

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_write_rs_sample_with_outputs(self):
        """Test writing RS sample with outputs"""
        x = np.array([[1.0, 2.0], [3.0, 4.0]])
        y = np.array([[10.0], [20.0]])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".dat", delete=False) as f:
            temp_file = f.name

        try:
            RSAnalyzer.writeRSsample(temp_file, x, y=y)

            with open(temp_file, "r") as f:
                content = f.read()

            # Should include outputs in header: 2 samples, 2 inputs, 1 output
            self.assertIn("2 2 1", content)

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_read_rs_sample(self):
        """Test reading RS sample files"""
        # Create test data file
        test_content = """2 2 1
1.0 2.0 10.0
3.0 4.0 20.0"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".dat", delete=False) as f:
            f.write(test_content)
            temp_file = f.name

        try:
            inputArray, outputArray = RSAnalyzer.readRSsample(temp_file)

            # Check shapes and values
            self.assertEqual(inputArray.shape, (2, 2))
            self.assertEqual(outputArray.shape, (2, 1))
            np.testing.assert_array_equal(inputArray[0], [1.0, 2.0])
            np.testing.assert_array_equal(outputArray[0], [10.0])

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_check_sample_size_polynomial(self):
        """Test sample size validation for polynomial RS"""
        from foqus_lib.framework.uq.ResponseSurfaces import ResponseSurfaces

        # Test linear (should need at least nInputs + 1)
        result = RSAnalyzer.checkSampleSize(10, 3, ResponseSurfaces.LINEAR)
        self.assertTrue(result)  # 10 >= 4 (3 + 1)

        result = RSAnalyzer.checkSampleSize(3, 3, ResponseSurfaces.LINEAR)
        self.assertFalse(result)  # 3 < 4

        # Test quadratic
        result = RSAnalyzer.checkSampleSize(20, 3, ResponseSurfaces.QUADRATIC)
        self.assertTrue(result)  # Should have enough samples

        result = RSAnalyzer.checkSampleSize(5, 3, ResponseSurfaces.QUADRATIC)
        self.assertFalse(result)  # Not enough samples

    def test_check_sample_size_other_methods(self):
        """Test sample size validation for other RS methods"""
        from foqus_lib.framework.uq.ResponseSurfaces import ResponseSurfaces

        # MARS needs 50+
        result = RSAnalyzer.checkSampleSize(60, 5, ResponseSurfaces.MARS)
        self.assertTrue(result)

        result = RSAnalyzer.checkSampleSize(40, 5, ResponseSurfaces.MARS)
        self.assertFalse(result)

        # Kriging needs 10+
        result = RSAnalyzer.checkSampleSize(15, 5, ResponseSurfaces.KRIGING)
        self.assertTrue(result)

        result = RSAnalyzer.checkSampleSize(5, 5, ResponseSurfaces.KRIGING)
        self.assertFalse(result)

    def test_check_mars(self):
        """Test MARS validation"""
        mock_data = Mock()

        rs_options = {"marsBases": 30, "marsInteractions": 3}

        # Patch the SampleData static methods
        with patch(
            "foqus_lib.framework.uq.RSAnalyzer.SampleData.getNumSamples"
        ) as mock_num_samples, patch(
            "foqus_lib.framework.uq.RSAnalyzer.SampleData.getInputTypes"
        ) as mock_input_types:
            mock_num_samples.return_value = 50
            mock_input_types.return_value = [1, 1, 1, 1, 1]  # 5 variable inputs

            result = RSAnalyzer.checkMARS(mock_data, rs_options)
            self.assertIsNotNone(result)

            marsBases, marsInteractions, marsNormOutputs = result
            self.assertEqual(marsBases, 30)
            self.assertEqual(marsInteractions, 3)
            self.assertEqual(marsNormOutputs, "n")

    def test_check_mars_invalid_options(self):
        """Test MARS validation with invalid options"""
        mock_data = Mock()

        # Test with out-of-range marsBases
        rs_options = {"marsBases": 5, "marsInteractions": 2}  # Too small (< 10)

        with patch(
            "foqus_lib.framework.uq.RSAnalyzer.SampleData.getNumSamples"
        ) as mock_num_samples, patch(
            "foqus_lib.framework.uq.RSAnalyzer.SampleData.getInputTypes"
        ) as mock_input_types, patch(
            "foqus_lib.framework.uq.RSAnalyzer.Common.showError"
        ) as mock_error:
            mock_num_samples.return_value = 20
            mock_input_types.return_value = [1, 1, 1]  # 3 variable inputs

            result = RSAnalyzer.checkMARS(mock_data, rs_options)
            self.assertIsNotNone(result)
            mock_error.assert_called()  # Should show warning

    def test_parse_prior_valid(self):
        """Test parsing valid prior information"""
        mock_data = Mock()

        xprior = [
            {
                "type": "Variable",
                "pdf": Distribution.UNIFORM,
                "min": 1,
                "max": 8,
                "param1": None,
                "param2": None,
            },
            {
                "type": "Variable",
                "pdf": Distribution.NORMAL,
                "min": -3,
                "max": 3,
                "param1": 0,
                "param2": 1,
            },
        ]

        # Patch all the SampleData static methods
        with patch(
            "foqus_lib.framework.uq.RSAnalyzer.SampleData.getNumInputs"
        ) as mock_num_inputs, patch(
            "foqus_lib.framework.uq.RSAnalyzer.SampleData.getInputNames"
        ) as mock_names, patch(
            "foqus_lib.framework.uq.RSAnalyzer.SampleData.getInputTypes"
        ) as mock_types, patch(
            "foqus_lib.framework.uq.RSAnalyzer.SampleData.getInputMins"
        ) as mock_mins, patch(
            "foqus_lib.framework.uq.RSAnalyzer.SampleData.getInputMaxs"
        ) as mock_maxs, patch(
            "foqus_lib.framework.uq.RSAnalyzer.SampleData.getInputDistributions"
        ) as mock_dists:
            mock_num_inputs.return_value = 2
            mock_names.return_value = ["x", "y"]
            mock_types.return_value = [1, 1]  # 2 variable inputs
            mock_mins.return_value = [0, -5]
            mock_maxs.return_value = [10, 5]
            mock_dists.return_value = [Mock(), Mock()]

            result = RSAnalyzer.parsePrior(mock_data, xprior)

            self.assertIsNotNone(result)
            self.assertIn("inputLB", result)
            self.assertIn("inputUB", result)
            self.assertIn("dist", result)

    def test_parse_prior_wrong_length(self):
        """Test parsing prior with wrong number of variables"""
        mock_data = Mock()
        xprior = [{"type": "Variable"}]  # Only 1 element, but need 2

        with patch(
            "foqus_lib.framework.uq.RSAnalyzer.SampleData.getNumInputs"
        ) as mock_num_inputs, patch(
            "foqus_lib.framework.uq.RSAnalyzer.SampleData.getInputNames"
        ) as mock_names, patch(
            "foqus_lib.framework.uq.RSAnalyzer.SampleData.getInputTypes"
        ) as mock_types, patch(
            "foqus_lib.framework.uq.RSAnalyzer.Common.showError"
        ) as mock_error:
            mock_num_inputs.return_value = 2
            mock_names.return_value = ["x", "y"]
            mock_types.return_value = [1, 1]  # 2 variable inputs

            result = RSAnalyzer.parsePrior(mock_data, xprior)
            self.assertIsNone(result)
            mock_error.assert_called()

    def test_ystats(self, mock_getdata=None):
        """Test output statistics calculation"""
        # Mock output data
        output_data = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])

        mock_data = Mock()

        with patch(
            "foqus_lib.framework.uq.RSAnalyzer.LocalExecutionModule.readSampleFromPsuadeFile"
        ) as mock_read, patch(
            "foqus_lib.framework.uq.RSAnalyzer.SampleData.getOutputData"
        ) as mock_output_data, patch(
            "foqus_lib.framework.uq.RSAnalyzer.SampleData.getNumOutputs"
        ) as mock_num_outputs:
            mock_read.return_value = mock_data
            mock_output_data.return_value = output_data
            mock_num_outputs.return_value = 2

            result = RSAnalyzer.ystats("test.dat")

            self.assertEqual(len(result), 2)  # Two outputs
            for stats in result:
                self.assertIn("mean", stats)
                self.assertIn("std", stats)
                self.assertIn("skew", stats)
                self.assertIn("kurt", stats)

    def test_pdfrange_normal(self):
        """Test PDF range calculation for normal distribution"""
        result = RSAnalyzer.pdfrange(Distribution.NORMAL, 0.0, 1.0)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)  # (lower, upper)
        self.assertLess(result[0], result[1])  # lower < upper

    def test_pdfrange_uniform(self):
        """Test PDF range for unsupported distribution (should return None)"""
        result = RSAnalyzer.pdfrange(Distribution.UNIFORM, 0.0, 1.0)
        self.assertIsNone(result)

    def test_pdfrange_exponential(self):
        """Test PDF range calculation for exponential distribution"""
        result = RSAnalyzer.pdfrange(Distribution.EXPONENTIAL, 1.0)  # lambda = 1.0
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertGreaterEqual(result[0], 0)  # Should be non-negative
