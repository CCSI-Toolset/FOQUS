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
import shutil
import time
import typing

import pytest
from PyQt5 import QtCore, QtWidgets

from foqus_lib.framework.sampleResults.results import Results
from foqus_lib.framework.uq.LocalExecutionModule import *
from foqus_lib.gui.sdoe.sdoeAnalysisDialog import sdoeAnalysisDialog
from foqus_lib.gui.sdoe.sdoePreview import sdoePreview

pytestmark = pytest.mark.gui


@pytest.fixture(scope="class", params=["UQ/Rosenbrock.foqus"])
def flowsheet_session_file(foqus_examples_dir, request):
    return str(foqus_examples_dir / "test_files" / request.param)


@pytest.fixture(scope="class")
def setup_frame_blank(main_window, flowsheet_session_file, request):
    main_window.loadSessionFile(flowsheet_session_file, saveCurrent=False)
    main_window.sdoeSetupAction.trigger()
    setup_frame: sdoeSetupFrame = main_window.sdoeSetupFrame
    request.cls.frame = setup_frame
    return setup_frame


@pytest.mark.usefixtures("setup_frame_blank")
class TestSDOE:
    @property
    def analysis_dialog(self) -> typing.Union[None, sdoeAnalysisDialog]:
        return self.__class__.frame._analysis_dialog

    def test_run_sdoe(self, qtbot, start_analysis):
        assert self.analysis_dialog is not None
        qtbot.focused = self.analysis_dialog
        qtbot.click(button="Estimate Runtime")
        qtbot.wait(1000)
        qtbot.using(spin_box="Number of Random Starts: n = 10^").enter_value(2)
        qtbot.wait(1000)
        qtbot.click(button="Run SDoE")
        qtbot.wait(10_000)
        with qtbot.searching_within(self.analysis_dialog):
            with qtbot.searching_within(group_box="Created Designs"):
                with qtbot.focusing_on(table=any):
                    qtbot.select_row(0)
                    with qtbot.waiting_for_modal(timeout=10_000):
                        qtbot.using(column="Plot SDoE").click()
                        with qtbot.searching_within(sdoePreview):
                            with qtbot.searching_within(group_box="Plots"):
                                qtbot.click(button="Plot SDoE")
                                qtbot.wait(1000)
                            qtbot.click(button="OK")

    @pytest.fixture(scope="class")
    def start_analysis(self, qtbot, foqus_examples_dir):
        def has_dialog():
            return self.analysis_dialog is not None

        qtbot.focused = self.frame
        with qtbot.file_selection(
            foqus_examples_dir / "tutorial_files/SDOE/SDOE_Ex1_Candidates.csv"
        ):
            qtbot.click(button="Load Existing\n Set")
        with qtbot.focusing_on(self.frame.filesTable):
            qtbot.select_row(0)
            with qtbot.waiting_for_modal(timeout=10_000):
                qtbot.using(column="Visualize").click()
                with qtbot.searching_within(sdoePreview):
                    with qtbot.searching_within(group_box="Plots"):
                        qtbot.click(button="Plot SDoE")
                        qtbot.wait(1000)
                    qtbot.click(button="OK")
        qtbot.click(button="Continue")
        qtbot.wait(1000)
        with qtbot.focusing_on(self.frame.aggFilesTable):
            qtbot.select_row(0)
            with qtbot.waiting_for_modal(timeout=10_000):
                qtbot.using(column="Visualize").click()
                with qtbot.searching_within(sdoePreview):
                    with qtbot.searching_within(group_box="Plots"):
                        qtbot.click(button="Plot SDoE")
                        qtbot.wait(1000)
                    qtbot.click(button="OK")
        qtbot.click(button="Open SDoE Dialog")
        qtbot.wait_until(has_dialog, timeout=10_000)
