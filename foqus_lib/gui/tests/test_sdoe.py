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
import time
import typing
import shutil
from PyQt5 import QtWidgets, QtCore
from foqus_lib.framework.uq.LocalExecutionModule import *

from foqus_lib.gui.sdoe.sdoeSetupFrame import sdoeSetupFrame
from foqus_lib.framework.sampleResults.results import Results

import pytest

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
    def test_smoke(self, qtbot, load_simulation):
        qtbot.wait(10_000)

    @pytest.fixture(scope="class")
    def load_simulation(self, setup_frame_blank, foqus_examples_dir):
        "Reproduce sdoeSetupFrame.loadSimulation() bypassing the file picker dialog"

        frame = setup_frame_blank
        fileName = str(
            foqus_examples_dir / "tutorial_files/SDOE/SDOE_Ex1_Candidates.csv"
        )
        data = LocalExecutionModule.readSampleFromCsvFile(fileName, False)
        data_info = frame.dataInfo(data)
        data.setSession(frame.dat)
        frame.dat.sdoeSimList.append(data)

        res = Results()
        res.sdoe_add_result(data)
        frame.dat.sdoeFilterResultsList.append(res)
        shutil.copy(fileName, frame.dname)

        # Update table
        frame.updateSimTable()
        frame.dataTabs.setEnabled(True)
