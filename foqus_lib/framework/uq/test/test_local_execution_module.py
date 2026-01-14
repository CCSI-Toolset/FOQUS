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

from foqus_lib.framework.uq.LocalExecutionModule import LocalExecutionModule


class TestLocalExecutionModule(unittest.TestCase):
    """Test cases for LocalExecutionModule class"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()

    def test_read_data_from_csv_file_with_headers(self):
        """Test reading CSV file with headers"""
        csv_content = "x,y,output1,output2\n1.0,2.0,3.0,4.0\n5.0,6.0,7.0,8.0\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_file = f.name

        try:
            with patch("builtins.input", return_value="2"):  # 2 inputs
                result = LocalExecutionModule.readDataFromCsvFile(
                    temp_file, askForNumInputs=True
                )

                inputArray, outputArray, inputNames, outputNames, runState = result

                # Test shapes and content
                self.assertEqual(inputArray.shape, (2, 2))
                self.assertEqual(outputArray.shape, (2, 2))
                self.assertEqual(inputNames, ["x", "y"])
                self.assertEqual(outputNames, ["output1", "output2"])
                np.testing.assert_array_equal(inputArray[0], [1.0, 2.0])
                np.testing.assert_array_equal(outputArray[0], [3.0, 4.0])

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_read_data_from_csv_file_no_ask(self):
        """Test reading CSV file without asking for number of inputs"""
        csv_content = "1.0,2.0,3.0\n4.0,5.0,6.0\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_file = f.name

        try:
            result = LocalExecutionModule.readDataFromCsvFile(
                temp_file, askForNumInputs=False
            )
            inputArray, outputArray, inputNames, outputNames, runState = result

            # Should treat all columns as inputs when askForNumInputs=False
            self.assertEqual(inputArray.shape, (2, 3))
            self.assertEqual(outputArray.shape, (2, 0))

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_write_simple_file(self):
        """Test writing simple file format"""
        inputData = [[1.0, 2.0], [3.0, 4.0]]
        outputData = [[5.0], [6.0]]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".dat", delete=False) as f:
            temp_file = f.name

        try:
            LocalExecutionModule.writeSimpleFile(temp_file, inputData, outputData)

            # Read back and verify
            with open(temp_file, "r") as f:
                lines = f.readlines()

            # Check header
            self.assertEqual(lines[0].strip(), "2 2 1")  # 2 samples, 2 inputs, 1 output

            # Check data lines
            self.assertEqual(lines[1].strip(), "1 1.0 2.0 5.0")
            self.assertEqual(lines[2].strip(), "2 3.0 4.0 6.0")

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_write_simple_file_no_outputs(self):
        """Test writing simple file with no outputs"""
        inputData = [[1.0, 2.0], [3.0, 4.0]]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".dat", delete=False) as f:
            temp_file = f.name

        try:
            LocalExecutionModule.writeSimpleFile(temp_file, inputData)

            with open(temp_file, "r") as f:
                content = f.read()

            self.assertIn("2 2 0", content)  # 2 samples, 2 inputs, 0 outputs

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_save_load_mcmc_file(self):
        """Test saving and loading MCMC file"""
        data = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        designIDs = [1, 2]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".mcmc", delete=False) as f:
            temp_file = f.name

        try:
            # Save MCMC file
            LocalExecutionModule.saveMCMCFile(temp_file, 1, 2, designIDs, data)

            # Load MCMC file
            designVars, designArray, outputArray = LocalExecutionModule.readMCMCFile(
                temp_file
            )

            self.assertEqual(designVars, [1, 2])
            self.assertEqual(designArray.shape, (2, 2))
            self.assertEqual(outputArray.shape, (2, 1))

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    @patch(
        "foqus_lib.framework.uq.LocalExecutionModule.LocalExecutionModule.getPsuadePath"
    )
    def test_gen_config_file(self, mock_get_path):
        """Test generating config file"""
        mock_get_path.return_value = "/path/to/psuade"

        # Create mock data
        mock_data = Mock()
        mock_data.getInputNames.return_value = ["x", "y"]
        mock_data.getNumInputs.return_value = 2
        mock_data.getOutputNames.return_value = ["z"]
        mock_data.getNumOutputs.return_value = 1

        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg", delete=False) as f:
            temp_file = f.name

        try:
            LocalExecutionModule.genConfigFile(mock_data, temp_file)

            with open(temp_file, "r") as f:
                content = f.read()

            self.assertIn("[PSUADE]", content)
            self.assertIn("PSUADE=/path/to/psuade", content)
            self.assertIn("x=0", content)
            self.assertIn("y=1", content)

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_write_psuade_path(self):
        """Test writing PSUADE path to file"""
        path = "/test/path/to/psuade"

        # Use a real temporary directory instead of mocking
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("os.getcwd", return_value=temp_dir):
                result_file = LocalExecutionModule.writePsuadePath(path)
                expected_file = temp_dir + os.path.sep + "PSUADEPATH"
                self.assertEqual(result_file, expected_file)

                # Verify the file was actually created and contains the correct path
                self.assertTrue(os.path.exists(result_file))
                with open(result_file, "r") as f:
                    written_path = f.read()
                self.assertEqual(written_path, path)
