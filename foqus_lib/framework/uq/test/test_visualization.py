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

from foqus_lib.framework.uq.Visualization import Visualization


class TestVisualization(unittest.TestCase):
    """Test cases for Visualization class."""

    def setUp(self):
        self.mock_ensemble = Mock()
        self.mock_ensemble.getValidSamples.return_value = Mock()

    def test_visualization_initialization(self):
        """Test Visualization initialization."""
        viz = Visualization(self.mock_ensemble, [1], [1, 2])

        self.assertIsInstance(viz, Visualization)
        self.assertEqual(viz.getOutputs(), [1])
        self.assertEqual(viz.getInputs(), [1, 2])
        self.assertEqual(viz.cmd, "splot2")  # 2 inputs

    def test_single_input_visualization(self):
        """Test visualization with single input."""
        viz = Visualization(self.mock_ensemble, [1], [1])
        self.assertEqual(viz.cmd, "splot")  # single input
