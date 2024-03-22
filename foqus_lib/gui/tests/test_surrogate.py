#################################################################################
# FOQUS Copyright (c) 2012 - 2024, by the software owners: Oak Ridge Institute
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

import pytest

from foqus_lib.gui.main.mainWindow import mainWindow
from foqus_lib.gui.surrogate.surrogateFrame import surrogateFrame

pytestmark = pytest.mark.gui


@pytest.fixture(
    scope="class", params=["tutorial_files/Flowsheets/Tutorial_4/Simple_flow.foqus"]
)
def flowsheet_session_file(foqus_examples_dir, request):
    return str(foqus_examples_dir / request.param)


@pytest.fixture(scope="class")
def frame(main_window, flowsheet_session_file, qtbot, request) -> surrogateFrame:
    qtbot.wait_for_window_shown(main_window)
    main_window.loadSessionFile(flowsheet_session_file, saveCurrent=False)
    main_window.surrogateAction.trigger()
    frame: surrogateFrame = main_window.surFrame
    request.cls.frame = frame
    return frame


# @pytest.mark.usefixtures("setup_frame_blank")
class TestFrame:
    frame: surrogateFrame

    # FIXME currently getting errors at the end of the test run
    # QBasicTimer::start: QBasicTimer can only be used with threads started with QThread
    # fish: Job 1, 'pytest --pyargs foqus_lib -m gu…' terminated by signal SIGSEGV (Address boundary error)
    # initially thought it was related with pytest.mark.parametrize being used,
    # but it's happening even after commenting it out
    @pytest.mark.parametrize(
        "name,required_import",
        [
            ("keras_nn", "tensorflow.keras"),
            ("pytorch_nn", "torch.nn"),
            ("scikit_nn", "sklearn.neural_network"),
            # "ACOSSO",
        ],
    )
    def test_run_surrogate(
        self,
        qtbot,
        frame,
        main_window: mainWindow,
        name: str,
        required_import: str,
    ):
        qtbot.focused = frame
        pytest.importorskip(required_import, reason=f"{required_import} not available")

        qtbot.using(combo_box="Tool:").set_option(name)

        for tab in [
            "Data",
            "Method Settings",
            "Variables",
            "Execution",
        ]:
            qtbot.select_tab(tab)
        qtbot.select_tab("Variables")
        with qtbot.focusing_on(group_box="Input Variables"):
            qtbot.click(button="Select All")
        with qtbot.focusing_on(group_box="Output Variables"):
            qtbot.click(button="Select All")
        qtbot.select_tab("Execution")
        run_button, stop_button = qtbot.locate(button=any, index=[0, 1])
        run_button.click()

        def is_completed():
            return (
                "surrogate finished" in main_window.statusBar().currentMessage().lower()
            )

        qtbot.wait_until(is_completed, timeout=30_000)
        qtbot.wait(1_000)
