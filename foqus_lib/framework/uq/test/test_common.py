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
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from foqus_lib.framework.uq.Common import Common


class TestCommon(unittest.TestCase):
    """Test cases for the Common class"""

    def test_get_file_name_root(self):
        """Test extracting filename root"""
        self.assertEqual(Common.getFileNameRoot("test.dat"), "test")
        self.assertEqual(Common.getFileNameRoot("/path/to/file.psuade"), "file")
        self.assertEqual(Common.getFileNameRoot("complex.file.name.txt"), "complex")

    def test_get_local_filename(self):
        """Test generating local filename"""
        result = Common.getLocalFileName("/tmp", "test.dat", "_processed")
        expected = "/tmp" + os.path.sep + "test_processed"
        self.assertEqual(result, expected)

    @patch("os.path.exists")
    @patch("os.mkdir")
    @patch("os.listdir")
    @patch("os.unlink")
    def test_init_folder(self, mock_unlink, mock_listdir, mock_mkdir, mock_exists):
        """Test folder initialization"""
        # Test creating new folder
        mock_exists.return_value = False
        Common.initFolder("/test/path")
        mock_mkdir.assert_called_once_with("/test/path")

        # Test cleaning existing folder
        mock_exists.return_value = True
        mock_listdir.return_value = ["file1.txt", "file2.dat"]
        with patch("os.path.isfile", return_value=True):
            Common.initFolder("/test/path", deleteFiles=True)
            self.assertEqual(mock_unlink.call_count, 2)

    @patch("foqus_lib.framework.uq.Common.usePyside", False)
    @patch("builtins.print")
    def test_show_error_no_pyside(self, mock_print):
        """Test error display without PyQt"""
        Common.showError("Test error message")
        mock_print.assert_called_once_with("Test error message")

    def test_get_user_regression_output_name(self):
        """Test getting user regression output name"""
        # Create a mock data object
        mock_data = Mock()

        # Test case 1: When labels contain the modified name (with underscore)
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("# Test regression file\n")
            f.write("labels = ['node_output1', 'node_output2']\n")
            temp_file1 = f.name

        try:
            mock_data.getNamesIncludeNodes.return_value = False
            result = Common.getUserRegressionOutputName(
                "node.output1", temp_file1, mock_data
            )
            self.assertEqual(result, "node_output1")  # Should return the modified name

            # Even when getNamesIncludeNodes is True, if the modified name is found in labels,
            # it should still return the modified name
            mock_data.getNamesIncludeNodes.return_value = True
            result = Common.getUserRegressionOutputName(
                "node.output1", temp_file1, mock_data
            )
            self.assertEqual(
                result, "node_output1"
            )  # Should still return modified name because it's in labels
        finally:
            os.unlink(temp_file1)

        # Test case 2: When data has names that include nodes but labels don't match
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("# Test regression file\n")
            f.write(
                "labels = ['other_output1', 'other_output2']\n"
            )  # Different labels that don't match
            temp_file2 = f.name

        try:
            mock_data.getNamesIncludeNodes.return_value = True
            result = Common.getUserRegressionOutputName(
                "node.output1", temp_file2, mock_data
            )
            self.assertEqual(result, "output1")  # Should strip the node part

            # Test case 3: When data doesn't include nodes and no match in labels
            mock_data.getNamesIncludeNodes.return_value = False
            result = Common.getUserRegressionOutputName(
                "node.output1", temp_file2, mock_data
            )
            self.assertEqual(result, "node.output1")  # Should return original name
        finally:
            os.unlink(temp_file2)

    def test_get_user_regression_output_name_no_labels(self):
        """Test getting user regression output name when no labels line exists"""
        mock_data = Mock()
        mock_data.getNamesIncludeNodes.return_value = True

        # Create a temporary regression file without labels
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("# Test regression file\n")
            f.write("# No labels line here\n")
            temp_file = f.name

        try:
            result = Common.getUserRegressionOutputName(
                "node.output1", temp_file, mock_data
            )
            self.assertEqual(
                result, "output1"
            )  # Should strip node part when names include nodes
        finally:
            os.unlink(temp_file)
