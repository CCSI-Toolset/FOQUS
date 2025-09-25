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
from PyQt5 import QtCore
import tempfile
import unittest
from unittest.mock import Mock, patch

from foqus_lib.framework.uq.Distribution import Distribution
from foqus_lib.framework.uq.Model import Model
from foqus_lib.framework.uq.RSInference import RSInference, RSInferencer


class TestRSInference(unittest.TestCase):
    """Test cases for RSInference and RSInferencer classes"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        RSInferencer.dname = self.test_dir

        # Create mock tables for testing
        self.ytable = [
            {"rsIndex": 1, "legendreOrder": 3},
            None,  # Unobserved output
        ]

        self.xtable = [
            {
                "name": "x1",
                "type": "Variable",
                "min": 0,
                "max": 10,
                "pdf": 0,
                "param1": None,
                "param2": None,
            },
            {"name": "x2", "type": "Fixed", "value": 5.0},
            {
                "name": "x3",
                "type": "Design",
                "min": -1,
                "max": 1,
                "pdf": 0,
                "param1": None,
                "param2": None,
            },
        ]

        self.obsTable = [
            [1, 5.0, 12.5, 0.5]  # [expIndex, designValue, outputMean, outputStd]
        ]

        self.mock_ensemble = Mock()
        self.mock_ensemble.getModelName.return_value = "test_model"
        self.mock_ensemble.writeToPsuade = Mock()

    def test_rs_inference_initialization(self):
        """Test RSInference initialization"""
        rs_inf = RSInference(
            self.mock_ensemble, self.ytable, self.xtable, self.obsTable
        )

        self.assertEqual(rs_inf.ensemble, self.mock_ensemble)
        self.assertEqual(rs_inf.outputs, [1])  # Only first output is observed
        self.assertEqual(rs_inf.ytable, self.ytable)
        self.assertEqual(rs_inf.xtable, self.xtable)
        self.assertEqual(rs_inf.obsTable, self.obsTable)
        self.assertFalse(rs_inf.genPostSample)
        self.assertFalse(rs_inf.addDisc)

    def test_rs_inference_save_load_dict(self):
        """Test saving and loading RSInference state"""
        rs_inf = RSInference(
            self.mock_ensemble,
            self.ytable,
            self.xtable,
            self.obsTable,
            genPostSample=True,
            addDisc=True,
            showList=[0, 1],
        )

        # Save state
        saved = rs_inf.saveDict()
        self.assertEqual(saved["ytable"], self.ytable)
        self.assertEqual(saved["genPostSample"], True)
        self.assertEqual(saved["addDisc"], True)

        # Load state
        new_rs_inf = RSInference(Mock(), [], [], [])
        new_rs_inf.loadDict(saved)
        self.assertEqual(new_rs_inf.ytable, self.ytable)
        self.assertTrue(new_rs_inf.genPostSample)
        self.assertTrue(new_rs_inf.addDisc)

    def test_rs_inferencer_initialization(self):
        """Test RSInferencer initialization"""
        inferencer = RSInferencer()
        self.assertIsNone(inferencer.mfile)
        self.assertIsInstance(inferencer, QtCore.QObject)

    def test_rs_inferencer_pdfrange_normal(self):
        """Test RSInferencer PDF range calculation"""
        result = RSInferencer.pdfrange(Distribution.NORMAL, 0.0, 1.0)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertLess(result[0], result[1])

    def test_rs_inferencer_pdfrange_beta(self):
        """Test RSInferencer PDF range for beta distribution"""
        result = RSInferencer.pdfrange(Distribution.BETA, 2.0, 5.0)
        self.assertIsNotNone(result)
        lower, upper = result
        self.assertGreaterEqual(lower, 0.0)
        self.assertLessEqual(upper, 1.0)

    def test_rs_inferencer_pdfrange_invalid(self):
        """Test RSInferencer PDF range for invalid distribution"""
        result = RSInferencer.pdfrange(999, 1.0, 2.0)  # Invalid distribution
        self.assertIsNone(result)

    @patch(
        "foqus_lib.framework.uq.RSInference.LocalExecutionModule.readSampleFromPsuadeFile"
    )
    def test_xvarinfo(self, mock_read):
        """Test extracting variable information"""
        mock_data = Mock()
        mock_data.getInputNames.return_value = ["x1", "x2", "x3"]
        mock_data.getInputTypes.return_value = [
            Model.VARIABLE,
            Model.FIXED,
            Model.VARIABLE,
        ]
        mock_data.getInputMins.return_value = [0, 5, -1]
        mock_data.getInputMaxs.return_value = [10, 5, 1]
        mock_read.return_value = mock_data

        # Patch the SampleData methods that are called directly
        with patch(
            "foqus_lib.framework.uq.RSInference.SampleData.getInputNames"
        ) as mock_names, patch(
            "foqus_lib.framework.uq.RSInference.SampleData.getInputTypes"
        ) as mock_types, patch(
            "foqus_lib.framework.uq.RSInference.SampleData.getInputMins"
        ) as mock_mins, patch(
            "foqus_lib.framework.uq.RSInference.SampleData.getInputMaxs"
        ) as mock_maxs:
            mock_names.return_value = ["x1", "x2", "x3"]
            mock_types.return_value = [Model.VARIABLE, Model.FIXED, Model.VARIABLE]
            mock_mins.return_value = [0, 5, -1]
            mock_maxs.return_value = [10, 5, 1]

            xnames, xmin, xmax = RSInferencer.xvarinfo("test.dat")

            # Should only return variable inputs (not fixed)
            self.assertEqual(xnames, ["x1", "x3"])
            self.assertEqual(xmin, [0, -1])
            self.assertEqual(xmax, [10, 1])

    @patch("foqus_lib.framework.uq.RSInference.Plotter.getdata")
    def test_getplotdat(self, mock_getdata):
        """Test getting plot data from MATLAB files"""
        # Mock data extraction - need more calls for the complex nested loops
        mock_data_calls = [
            np.array([1, 2, 3]),  # X(1,:) - first input X data
            np.array([0.1, 0.3, 0.2]),  # D(1,:) - first input histogram data
            np.array([4, 5, 6]),  # X(2,:) - second input X data for pair plot
            np.array([[0.1, 0.2], [0.3, 0.1]]),  # NC(2,1,:,:) - heatmap data
            np.array([7, 8, 9]),  # X(2,:) - second input X data
            np.array([0.2, 0.4, 0.3]),  # D(2,:) - second input histogram data
            # Add some extra calls in case the function makes more calls than expected
            np.array([0.5]),  # fallback
            np.array([0.6]),  # fallback
        ]
        mock_getdata.side_effect = mock_data_calls

        variableInputNames = ["x1", "x2"]
        xmin = [0, -1]
        xmax = [10, 1]
        plotvars = {"hist": "D", "heatmap": "NC"}

        # Mock the optional loglik extraction that might fail
        with patch(
            "foqus_lib.framework.uq.RSInference.Plotter.getdata"
        ) as mock_getdata_inner:
            # Set up the side effect to handle both regular calls and the loglik call
            def side_effect_func(*args, **kwargs):
                if len(args) >= 2 and args[1] == "negll":
                    # This is the loglik call that might raise IndexError
                    raise IndexError("No loglik data")
                else:
                    # Return data from our prepared list
                    return mock_data_calls.pop(0) if mock_data_calls else np.array([1])

            mock_getdata_inner.side_effect = side_effect_func

            result = RSInferencer.getplotdat(
                "test.m", variableInputNames, xmin, xmax, plotvars, show=[0, 1]
            )

            xdat, ydat, zdat, xlabel, ylabel, xlim, ylim, zlim, sb_indices, loglik = (
                result
            )

            # Test basic structure - should have data for 2 diagonal + 1 off-diagonal = 3 elements
            self.assertIsInstance(xdat, list)
            self.assertIsInstance(ydat, list)
            self.assertIsInstance(zdat, list)
            self.assertIsInstance(xlabel, list)

            # Should have extracted variable names
            self.assertIn("x1", xlabel)
            self.assertIn("x2", xlabel)

            # Limits should be set
            self.assertEqual(len(xlim), 3)  # 2 diagonals + 1 off-diagonal
            self.assertEqual(xlim[0], [0, 10])  # x1 limits
            self.assertEqual(xlim[1], [-1, 1])  # x2 limits

    @patch("foqus_lib.framework.uq.RSInference.Common.invokePsuade")
    @patch("os.path.exists")
    @patch("os.rename")
    def test_genheatmap(self, mock_rename, mock_exists, mock_invoke):
        """Test generating heatmap files"""
        mock_invoke.return_value = ("success", None)
        mock_exists.return_value = True

        result = RSInferencer.genheatmap("test.dat", move=False)

        mock_invoke.assert_called_once()
        self.assertEqual(result, "matlabiplt2pdf.m")
        mock_rename.assert_not_called()  # move=False

    @patch("foqus_lib.framework.uq.RSInference.Plotter.plotinf")
    @patch("foqus_lib.framework.uq.RSInference.RSInferencer.getplotdat")
    @patch("foqus_lib.framework.uq.RSInference.RSInferencer.xvarinfo")
    def test_infplot(self, mock_xvarinfo, mock_getplotdat, mock_plotinf):
        """Test inference plotting"""
        # Mock data
        mock_xvarinfo.return_value = (["x1", "x2"], [0, -1], [10, 1])
        mock_getplotdat.return_value = (
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            np.array([[1, 2], [-1, 3]]),
            None,
        )

        RSInferencer.infplot("test.m", "test.dat", show=[0, 1])

        mock_xvarinfo.assert_called_once()
        self.assertEqual(mock_getplotdat.call_count, 2)  # Prior and posterior
        self.assertEqual(mock_plotinf.call_count, 2)  # Prior and posterior plots


class TestRSInferenceIntegration(unittest.TestCase):
    """Integration tests for RSInference workflow"""

    def setUp(self):
        """Set up integration test environment"""
        self.test_dir = tempfile.mkdtemp()

        # Create a minimal ensemble mock
        self.mock_ensemble = Mock()
        self.mock_ensemble.getModelName.return_value = "integration_test_model"
        self.mock_ensemble.writeToPsuade = Mock()

    def test_analyze_workflow(self):
        """Test the complete analyze workflow"""
        ytable = [{"rsIndex": 1}]  # Simple RS
        xtable = [
            {
                "name": "x1",
                "type": "Variable",
                "min": 0,
                "max": 1,
                "pdf": 0,
                "param1": None,
                "param2": None,
            }
        ]
        obsTable = [[1, 5.0, 0.5]]

        rs_inf = RSInference(self.mock_ensemble, ytable, xtable, obsTable)

        # Mock the inferencer's infer method
        rs_inf.inferencer.infer = Mock()

        rs_inf.analyze()

        # Verify that the ensemble was written to file
        self.mock_ensemble.writeToPsuade.assert_called_once()

        # Verify that infer was called with correct parameters
        rs_inf.inferencer.infer.assert_called_once()

    def test_end_function_callback(self):
        """Test end function callback mechanism"""
        ytable = [{"rsIndex": 1}]
        xtable = [{"name": "x1", "type": "Variable"}]
        obsTable = []

        end_function_called = False

        def mock_end_function():
            nonlocal end_function_called
            end_function_called = True

        rs_inf = RSInference(
            self.mock_ensemble, ytable, xtable, obsTable, endFunction=mock_end_function
        )

        # Simulate the end of inference
        rs_inf.inferencer.mfile = "test.m"
        rs_inf.archiveFile = Mock()  # Mock inherited method
        rs_inf.newEndFunction()

        self.assertTrue(end_function_called)
        rs_inf.archiveFile.assert_called_once_with("test.m")

    def test_additional_info(self):
        """Test getting additional information"""
        ytable = [{"rsIndex": 1}]
        xtable = [{"name": "x1", "type": "Variable"}]
        obsTable = []

        rs_inf = RSInference(self.mock_ensemble, ytable, xtable, obsTable, addDisc=True)

        # Mock parent method
        with patch(
            "foqus_lib.framework.uq.RSInference.UQRSAnalysis.getAdditionalInfo"
        ) as mock_parent:
            mock_parent.return_value = {"base": "info"}

            info = rs_inf.getAdditionalInfo()

            self.assertIn("xtable", info)
            self.assertIn("ytable", info)
            self.assertIn("obsTable", info)
            self.assertIn("Use Discrepancy", info)
            self.assertTrue(info["Use Discrepancy"])
