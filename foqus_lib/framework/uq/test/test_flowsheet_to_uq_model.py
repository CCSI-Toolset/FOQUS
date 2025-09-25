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

from foqus_lib.framework.uq.Model import Model
from foqus_lib.framework.uq.flowsheetToUQModel import flowsheetToUQModel


class TestFlowsheetConversion(unittest.TestCase):
    """Test cases for flowsheet to UQ model conversion."""

    def test_flowsheet_to_uq_model(self):
        """Test converting flowsheet to UQ model."""
        # Create mock flowsheet graph
        mock_gr = Mock()

        # Mock input variables
        mock_input1 = Mock()
        mock_input1.con = False  # Not connected
        mock_input1.value = 0.5
        mock_input1.min = 0.0
        mock_input1.max = 1.0
        mock_input1.default = 0.5
        mock_input1.dist = None

        mock_input2 = Mock()
        mock_input2.con = True  # Connected (should be skipped)

        # Mock input collection
        mock_gr.input = Mock()
        mock_gr.input.compoundNames.return_value = ["input1", "input2"]
        mock_gr.input.get.side_effect = lambda x: (
            mock_input1 if x == "input1" else mock_input2
        )

        # Mock output collection
        mock_gr.output = Mock()
        mock_gr.output.compoundNames.return_value = ["output1", "output2"]

        # Mock generateGlobalVariables method
        mock_gr.generateGlobalVariables = Mock()

        uq_model = flowsheetToUQModel(mock_gr)

        self.assertIsInstance(uq_model, Model)
        self.assertEqual(uq_model.getName(), "Flowsheet")
        self.assertEqual(uq_model.getRunType(), Model.GATEWAY)

        # Check input names - expect tuple from Model class
        input_names = uq_model.getInputNames()
        # Convert both to lists for comparison to handle tuple vs list differences
        expected_inputs = ["input1"]  # Only non-connected input
        self.assertEqual(list(input_names), expected_inputs)

        # Check output names
        output_names = uq_model.getOutputNames()
        expected_outputs = ["output1", "output2"]
        self.assertEqual(list(output_names), expected_outputs)

        # Verify that non-connected inputs are properly identified
        self.assertEqual(len(input_names), 1)  # Only one non-connected input
        self.assertIn("input1", input_names)
        self.assertNotIn(
            "input2", input_names
        )  # input2 was connected, should be filtered out
