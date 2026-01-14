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
import os
import tempfile
import unittest

from foqus_lib.framework.uq.Distribution import Distribution
from foqus_lib.framework.uq.Model import Model


class TestExperimentalDesign(unittest.TestCase):
    """Test cases for ExperimentalDesign functionality"""

    def setUp(self):
        """Set up test model and data"""
        from foqus_lib.framework.uq.ExperimentalDesign import ExperimentalDesign
        from foqus_lib.framework.uq.SampleData import SampleData

        self.ExperimentalDesign = ExperimentalDesign

        # Create a test model
        model = Model()
        model.setInputNames(["x", "y"])
        model.setOutputNames(["z"])
        model.setInputTypes([Model.VARIABLE, Model.VARIABLE])
        model.setInputMins([0, -1])
        model.setInputMaxs([10, 1])

        # Create distributions
        dist1 = Distribution(Distribution.UNIFORM)
        dist2 = Distribution(Distribution.NORMAL)
        dist2.setParameterValues(0, 0.5)
        model.setInputDistributions([dist1, dist2])

        self.test_data = SampleData(model)
        self.test_data.setNumSamples(50)
        self.test_data.setSampleMethod("MC")

    def test_create_psuade_in_file(self):
        """Test creating PSUADE input file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".in", delete=False) as f:
            temp_file = f.name

        try:
            self.ExperimentalDesign.createPsuadeInFile(self.test_data, temp_file)

            # Verify file was created and has expected content
            with open(temp_file, "r") as f:
                content = f.read()
                self.assertIn("PSUADE", content)
                self.assertIn("INPUT", content)
                self.assertIn("OUTPUT", content)
                self.assertIn("dimension = 2", content)  # 2 inputs
                self.assertIn("variable 1 x", content)
                self.assertIn("variable 2 y", content)
                self.assertIn("PDF 2 N", content)  # Normal distribution for y
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_create_psuade_in_file_no_pdf(self):
        """Test creating PSUADE input file without PDF info"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".in", delete=False) as f:
            temp_file = f.name

        try:
            self.ExperimentalDesign.createPsuadeInFile(
                self.test_data, temp_file, includePDF=False
            )

            with open(temp_file, "r") as f:
                content = f.read()
                self.assertNotIn("PDF 2 N", content)  # Should not include PDF info
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
