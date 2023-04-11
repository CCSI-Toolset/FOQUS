#################################################################################
# FOQUS Copyright (c) 2012 - 2023, by the software owners: Oak Ridge Institute
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
"""
Test module for FOQUS OUU Tutorial Example 1: `OUU with Discrete Uncertain Parameters Only`
URL: https://foqus.readthedocs.io/en/stable/chapt_ouu/tutorial.html#example-1-ouu-with-discrete-uncertain-parameters-only

To run the test:
pytest -k test_ouu [--qtbot-slowdown-wait-ms=<time_in_ms>]

Author: Devarshi Ghoshal <dghoshal@lbl.gov>
"""

import time
import typing
import os

from PyQt5 import QtWidgets, QtCore
import pytest

from foqus_lib.gui.ouu.ouuSetupFrame import ouuSetupFrame
from foqus_lib.gui.ouu import foqusPSUADEClient
from foqus_lib.gui.ouu.OUUInputsTable import OUUInputsTable
from foqus_lib.gui.ouu import nodeToUQModel

from foqus_lib.framework.uq.LocalExecutionModule import LocalExecutionModule
from foqus_lib.gui.common.InputPriorTable import InputPriorTable

from PyQt5.QtWidgets import QMessageBox


pytestmark = pytest.mark.gui


@pytest.fixture(scope="class")
def setup_frame_blank(main_window, request):
    """
    Sets up a blank OUU Frame.

    Args:
        main_window: FOQUS main GUI window. Instance of foqus_lib.gui.main.mainWindow.mainWindow.
        request: pytest request.

    Returns:
        ouuSetupFrame: FOQUS OUU UI.
    """
    main_window.ouuSetupAction.trigger()
    setup_frame: ouuSetupFrame = main_window.ouuSetupFrame
    request.cls.frame = setup_frame
    return setup_frame


def _accept_dialog(w):
    import time

    time.sleep(1)
    w.buttonBox.accepted.emit()


@pytest.mark.usefixtures("setup_frame_blank")
class TestOUU:
    frame: ouuSetupFrame = ...
    ###############
    """
    Simple test to check the very basic test- launching the FOQUS main window.
    """

    @pytest.fixture(scope="class")
    def launchWindow(self, qtbot):
        qtbot.focused = self.frame

    @pytest.mark.usefixtures("launchWindow")
    def test_window(self):
        assert True

    ################
    """
    Fixtures for comprehensive tests for OUU example 1.
    """

    @pytest.fixture(scope="class")
    def model_file(self):
        model_file_name = os.path.join(
            os.path.dirname(__file__),
            "../../../examples/tutorial_files/OUU/ouu_optdriver.in",
        )
        return model_file_name

    @pytest.fixture(scope="class")
    def model_file_button_label(self):
        label = "Load Model From File"
        return label

    @pytest.fixture(scope="class")
    def ouu_variables(self):
        ouu_vars = [
            "Opt: Primary Continuous (Z1)",
            "Opt: Recourse (Z2)",
            "UQ: Discrete (Z3)",
        ]
        # "Opt: Recourse (Z2)", "UQ: Discrete (Z3)", "UQ: Continuous (Z4)"
        return ouu_vars

    @pytest.fixture(scope="class")
    def sample_file(self):
        sample_file_name = os.path.join(
            os.path.dirname(__file__),
            "../../../examples/tutorial_files/OUU/ex1_x3sample.smp",
        )
        return sample_file_name

    @pytest.fixture(scope="class")
    def exec_timeout(self):
        timeout = 90_000
        return timeout

    @pytest.fixture(scope="class")
    def selectModel(self, qtbot, model_file, model_file_button_label):
        """
        [Step-1] Select the model from an example file.
        TODO: The code below needs to be called through a function in ouuSetupFrame.py.
              Currently, this is too tightly integrated and can not be reused correctly
              for the test. Hence, copied and used here directly.

        Args:
            qtbot: pytest_qt_extras QtBot to test/interact with FOQUS GUI.
            model_file: (from fixture) location of the example model file.
            model_file_button_label: (from fixture) label for the radio button for selecting model file.
        """
        ouu_frame = self.frame
        qtbot.focused = ouu_frame
        fname = os.path.abspath(model_file)
        ouu_frame.filesDir, _ = os.path.split(fname)
        ouu_frame.modelFile_edit.setText(fname)
        ouu_frame.model = LocalExecutionModule.readSampleFromPsuadeFile(fname).model
        ouu_frame.input_table.init(ouu_frame.model, InputPriorTable.OUU)
        ouu_frame.setFixed_button.setEnabled(True)
        ouu_frame.setX1_button.setEnabled(True)
        ouu_frame.setX2_button.setEnabled(True)
        ouu_frame.setX3_button.setEnabled(True)
        ouu_frame.setX4_button.setEnabled(True)
        ouu_frame.initTabs()
        ouu_frame.setCounts()

        qtbot.click(radio_button=model_file_button_label)

    @pytest.fixture(scope="class")
    def setVariables(self, qtbot, ouu_variables):
        """
        [Step-2] Set OUU variable types.

        Args:
            qtbot: pytest_qt_extras QtBot to test/interact with FOQUS GUI.
            ouu_variables: (from fixture) variable types from a dropdown list.
        """
        with qtbot.focusing_on(table=any):
            rownum = 0
            for i in range(len(ouu_variables)):
                for _ in range(4):
                    qtbot.select_row(rownum)
                    qtbot.using(column="Type").set_option(ouu_variables[i])
                    rownum += 1

    @pytest.fixture(scope="class")
    def selectOptimizer(self, qtbot):
        """
        [Step-3] Select the optimizer for the test. It should be the default
        optimizer BOBYQA for this test, will all the default settings.

        Args:
            qtbot: pytest_qt_extras QtBot to test/interact with FOQUS GUI.
        """
        qtbot.select_tab("Optimization Setup")
        with qtbot.focusing_on(
            group_box="Objective Function for Optimization Under Uncertainty (OUU)"
        ):
            qtbot.click(radio_button="Mean of G(Z1,Z2,Z3,Z4) with respect to Z3 and Z4")

    @pytest.fixture(scope="class")
    def discreteVars(self, qtbot, sample_file):
        """
        [Step-4] Set up the discrete variables from a simple example file.

        Args:
            qtbot: pytest_qt_extras QtBot to test/interact with FOQUS GUI.
            sample_file: simple input file from examples.

        Returns:
            [type]: Discrete random variables (Z3).
        """
        ouu_frame = self.frame
        qtbot.select_tab("UQ Setup")

        ouu_frame.filesDir, _ = os.path.split(sample_file)

        data = LocalExecutionModule.readDataFromSimpleFile(
            sample_file, hasColumnNumbers=False
        )

        data = data[0]

        with qtbot.focusing_on(group_box=" Discrete Random Variables (Z3)"):
            ouu_frame.compressSamples_chk.setEnabled(True)
            ouu_frame.loadTable(ouu_frame.z3_table, data)

        return data

    @pytest.fixture(scope="class")
    def runUntilConfirmationDialog(self, qtbot, exec_timeout):
        """
        [Step-5] Final step to run the optimizer and plot the graph.

        Args:
            qtbot: pytest_qt_extras QtBot to test/interact with FOQUS GUI.
            exec_timeout: timeout to run the optimizer and finish executing the workflow.
        """
        qtbot.select_tab("Launch/Progress")

        qtbot.click(button="Run OUU")
        with qtbot.waiting_for_dialog(
            dialog_cls=QtWidgets.QMessageBox, timeout=exec_timeout
        ) as dialog:
            yield dialog

    ###################
    """
    Comprehensive tests for OUU tutorial 1
    """

    @pytest.mark.usefixtures("selectModel")
    def testModelSelection(self):
        """
        [Test-1] Test that the correct model input file is selected and
                 the radio button is selected, else the test fails.
        """
        model_file = self.frame.modelFile_edit.text()
        assert os.path.basename(model_file) == "ouu_optdriver.in"
        assert self.frame.modelFile_radio.isChecked()

    @pytest.mark.usefixtures("setVariables")
    def testVariables(self):
        """
        [Test-2] Test that the correct variables - Z1, Z2, Z3 - are set.
        """
        fixed_text = self.frame.fixedCount_static.text()
        x1_text = self.frame.x1Count_static.text()
        x2_text = self.frame.x2Count_static.text()
        x3_text = self.frame.x3Count_static.text()
        x4_text = self.frame.x4Count_static.text()
        assert (
            fixed_text == "# Fixed: 0"
            and x1_text == "# Primary Opt Vars: 4"
            and x2_text == "# Recourse Opt Vars: 4"
            and x3_text == "# Discrete RVs: 4"
            and x4_text == "# Continuous RVs: 0"
        )

    @pytest.mark.usefixtures("selectOptimizer")
    def testOptimizer(self):
        """
        [Test-3] Test that BOBYQA is selected as the optimizer.
        """
        assert self.frame.mean_radio.isChecked()
        assert self.frame.primarySolver_combo.currentText() == "BOBYQA"
        assert (
            self.frame.secondarySolver_combo.currentText()
            == "Use model as optimizer: min_Z2 G(Z1,Z2,Z3,Z4)"
        )

    def testRandomVars(self, discreteVars):
        """
        [Test-4] Test that the discrete variables are selected appropriately.
        """
        n_inps = discreteVars.shape[1]
        n_vars = len(self.frame.input_table.getUQDiscreteVariables()[0])
        assert n_inps == n_vars

    def testRunOUU(self, runUntilConfirmationDialog):
        """
        [Test-5] Test that the optimizer launches and finishes.
        """
        dialog = runUntilConfirmationDialog
        assert "finished" in dialog.text
