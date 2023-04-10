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
class TestSDOE():
    def test_smoke(self, qtbot, load_data):
        qtbot.wait(10_000)

    @pytest.fixture(scope="class")
    def load_data(self, setup_frame_blank):
        frame = setup_frame_blank
        fileName =  "/Users/sfhome/Desktop/CCI_Spring_2023/foqus/CCSI-Toolset/FOQUS/examples/tutorial_files/SDOE/SDOE_Ex1_Candidates.csv"
        data = LocalExecutionModule.readSampleFromCsvFile(fileName, True)
        data.setSession(frame.dat)
        frame.dat.odoeEvalList.append(data)
        
        res = Results()
        res.eval_add_result(data)
        shutil.copy(fileName, frame.odoe_dname)

        # Update table
        frame.updateEvalTable()

