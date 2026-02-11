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
import numpy as np
import os
import tempfile
import unittest

from foqus_lib.framework.uq.Distribution import Distribution
from foqus_lib.framework.uq.Model import Model


class TestModel(unittest.TestCase):
    """Test cases for the Model class"""

    def setUp(self):
        """Set up test model"""
        self.model = Model()

    def test_initialization(self):
        """Test model initialization"""
        self.assertIsNone(self.model.name)
        self.assertEqual(self.model.numInputs, 0)
        self.assertEqual(self.model.numOutputs, 0)
        self.assertIsNone(self.model.inputNames)

    def test_name_operations(self):
        """Test setting and getting model name"""
        self.model.setName("TestModel")
        self.assertEqual(self.model.getName(), "TestModel")

    def test_driver_operations(self):
        """Test driver name operations"""
        self.model.setDriverName("test_driver.py")
        self.assertEqual(self.model.getDriverName(), "test_driver.py")

        self.model.setOptDriverName("opt_driver.py")
        self.assertEqual(self.model.getOptDriverName(), "opt_driver.py")

        self.model.setAuxDriverName("aux_driver.py")
        self.assertEqual(self.model.getAuxDriverName(), "aux_driver.py")

    def test_input_names(self):
        """Test input name operations"""
        # Single string
        self.model.setInputNames("input1")
        self.assertEqual(self.model.getInputNames(), ("input1",))
        self.assertEqual(self.model.numInputs, 1)

        # List of names
        self.model.setInputNames(["input1", "input2", "input3"])
        self.assertEqual(self.model.getInputNames(), ("input1", "input2", "input3"))
        self.assertEqual(self.model.numInputs, 3)

        # Multiple arguments
        self.model.setInputNames("x", "y", "z")
        self.assertEqual(self.model.getInputNames(), ("x", "y", "z"))

    def test_input_names_error(self):
        """Test input names with invalid types"""
        with self.assertRaises(TypeError):
            self.model.setInputNames([1, 2, 3])  # Numbers instead of strings

    def test_output_names(self):
        """Test output name operations"""
        self.model.setOutputNames(["output1", "output2"])
        self.assertEqual(self.model.getOutputNames(), ("output1", "output2"))
        self.assertEqual(self.model.numOutputs, 2)

    def test_input_types(self):
        """Test input types"""
        self.model.setInputNames(["x", "y", "z"])
        self.model.setInputTypes([Model.VARIABLE, Model.FIXED, Model.VARIABLE])
        self.assertEqual(
            self.model.getInputTypes(), (Model.VARIABLE, Model.FIXED, Model.VARIABLE)
        )

        with self.assertRaises(ValueError):
            self.model.setInputTypes([Model.VARIABLE])  # Wrong number of types

    def test_input_bounds(self):
        """Test input min/max operations"""
        self.model.setInputNames(["x", "y"])

        self.model.setInputMins([0.0, -10.0])
        np.testing.assert_array_equal(self.model.getInputMins(), [0.0, -10.0])

        self.model.setInputMaxs([100.0, 10.0])
        np.testing.assert_array_equal(self.model.getInputMaxs(), [100.0, 10.0])

        with self.assertRaises(ValueError):
            self.model.setInputMins([0.0])  # Wrong number of mins

    def test_input_defaults(self):
        """Test input default values"""
        self.model.setInputNames(["x", "y"])
        self.model.setInputDefaults([5.0, 0.0])
        np.testing.assert_array_equal(self.model.getInputDefaults(), [5.0, 0.0])

    def test_input_distributions(self):
        """Test input distribution operations"""
        self.model.setInputNames(["x", "y"])

        # Test with Distribution objects
        dist1 = Distribution(Distribution.NORMAL)
        dist1.setParameterValues(0, 1)
        dist2 = Distribution(Distribution.UNIFORM)

        self.model.setInputDistributions([dist1, dist2])
        dists = self.model.getInputDistributions()
        self.assertEqual(len(dists), 2)
        self.assertEqual(dists[0].getDistributionType(), Distribution.NORMAL)

        # Test with string types and parameters
        self.model.setInputDistributions(["N", "U"], [0, None], [1, None])
        dists = self.model.getInputDistributions()
        self.assertEqual(dists[0].getDistributionType(), Distribution.NORMAL)
        self.assertEqual(dists[0].getParameterValues(), (0, 1))

    def test_variable_inputs_count(self):
        """Test counting variable inputs"""
        self.model.setInputNames(["x", "y", "z"])
        self.model.setInputTypes([Model.VARIABLE, Model.FIXED, Model.VARIABLE])
        self.assertEqual(self.model.getNumVarInputs(), 2)

    def test_emulator_operations(self):
        """Test emulator-related operations"""
        self.model.setOutputNames(["out1", "out2", "out3"])

        # Test setting single output status
        self.model.setEmulatorOutputStatus(0, Model.CALCULATED)
        status = self.model.getEmulatorOutputStatus()
        self.assertEqual(status[0], Model.CALCULATED)
        self.assertEqual(status[1], Model.NOT_CALCULATED)

        # Test setting multiple output status
        self.model.setEmulatorOutputStatus([1, 2], Model.NEED_TO_CALCULATE)
        status = self.model.getEmulatorOutputStatus()
        self.assertEqual(status[1], Model.NEED_TO_CALCULATE)
        self.assertEqual(status[2], Model.NEED_TO_CALCULATE)

        # Test training file
        self.model.setEmulatorTrainingFile("training.dat")
        self.assertEqual(self.model.getEmulatorTrainingFile(), "training.dat")

    def test_flowsheet_fixed(self):
        """Test flowsheet fixed operations"""
        self.model.setInputNames(["x", "y", "z"])

        # Test setting individual input as fixed
        self.model.setInputFlowsheetFixed(1)
        self.assertTrue(self.model.getInputFlowsheetFixed(1))
        self.assertFalse(self.model.getInputFlowsheetFixed(0))

        # Test setting all at once
        self.model.setInputFlowsheetFixed([True, False, True])
        fixed = self.model.getInputFlowsheetFixed()
        self.assertEqual(fixed, [True, False, True])

    def test_save_load_operations(self):
        """Test saving and loading model"""
        # Set up a complex model
        self.model.setName("TestModel")
        self.model.setInputNames(["x", "y"])
        self.model.setOutputNames(["out1"])
        self.model.setInputTypes([Model.VARIABLE, Model.FIXED])
        self.model.setInputMins([0, -5])
        self.model.setInputMaxs([10, 5])
        self.model.setInputDefaults([5, 0])
        self.model.setSelectedOutputs([0])

        # Test saveDict
        saved = self.model.saveDict()
        self.assertEqual(saved["name"], "TestModel")
        self.assertEqual(saved["inputNames"], ("x", "y"))
        self.assertEqual(saved["outputNames"], ("out1",))

        # Test loadDict
        new_model = Model()
        new_model.loadDict(saved)
        self.assertEqual(new_model.getName(), "TestModel")
        self.assertEqual(new_model.getInputNames(), ("x", "y"))
        np.testing.assert_array_equal(new_model.getInputMins(), [0, -5])

    def test_save_load_file(self):
        """Test saving and loading to/from file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            self.model.setName("FileTestModel")
            self.model.setInputNames(["param1", "param2"])
            self.model.setInputTypes([Model.VARIABLE, Model.FIXED])
            self.model.setInputMins([0, 0])
            self.model.setInputMaxs([2, 2])
            self.model.setInputDefaults([1, 1])
            self.model.setOutputNames(["output1", "output2"])

            # Save to file
            self.model.saveFile(temp_file)

            # Load from file
            new_model = Model()
            new_model.loadFile(temp_file)

            self.assertEqual(new_model.getName(), "FileTestModel")
            self.assertEqual(new_model.getInputNames(), ("param1", "param2"))
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
