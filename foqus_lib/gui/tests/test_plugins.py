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
from pathlib import Path
from typing import List, Tuple
import os

import pytest
from pytest_qt_extras import QtBot
from PyQt5 import QtWidgets

from foqus_lib.gui.main.mainWindow import mainWindow
from foqus_lib.framework.session import session as FoqusSession
from foqus_lib.gui.flowsheet.drawFlowsheet import drawFlowsheet
from foqus_lib.framework.plugins.pluginSearch import plugins


pytestmark = pytest.mark.gui


@pytest.fixture(scope="session")
def model_files(
    foqus_plugin_models_dir: Path,
    install_plugin_model_files,
    suffixes: Tuple[str] = (".py",),
) -> List[Path]:
    paths = []
    for path in sorted(foqus_plugin_models_dir.glob("*")):
        if all(
            [
                ((path.is_file() and path.suffix in suffixes) or path.is_dir()),
                path.stat().st_size > 0,
                path.name != "__init__.py",
            ]
        ):
            paths.append(path)
    return paths


@pytest.fixture(scope="session")
def expected_plugin_keys() -> List[str]:
    return [
        "heat_integration",
        "pymodel_test",
        "steam_cycle",
    ]


def test_model_files_are_present(model_files: List[Path]):
    assert model_files


# ----------------------------------------------------------------------------
# parent class to run flowsheet, starting from main FOQUS session

# use the ML_AI session since it already exists, will load and run plugins here
@pytest.fixture(
    scope="class", params=["other_files/ML_AI_Plugin/mea_column_model.foqus"]
)
def flowsheet_session_file(foqus_examples_dir: Path, request) -> Path:
    return foqus_examples_dir / request.param


class TestPluginFlowsheetRun:
    @pytest.fixture(scope="class")
    def focus_flowsheet_tab(
        self,
        qtbot: QtBot,
        main_window,
    ) -> None:
        qtbot.focused = main_window
        with qtbot.wait_signal(main_window.fsEditAction.triggered):
            qtbot.click(button="Flowsheet")

    def test_flowsheet_tab_is_active(
        self, qtbot: QtBot, main_window, focus_flowsheet_tab: drawFlowsheet
    ):
        assert main_window.mainWidget.currentIndex() == main_window.screenIndex["flow"]

    @pytest.fixture(scope="class")
    def active_session(
        self,
        main_window: mainWindow,
        flowsheet_session_file: Path,
    ) -> FoqusSession:
        main_window.loadSessionFile(str(flowsheet_session_file), saveCurrent=False)
        return main_window.dat

    def test_model_flowsheet_is_loaded(
        self, qtbot: QtBot, focus_flowsheet_tab, active_session: FoqusSession
    ):
        assert active_session.flowsheet is not None

    @pytest.fixture(scope="class")
    def pymodels(
        self,
        active_session: FoqusSession,
        model_files: List[Path],
        foqus_plugin_models_dir: Path,
    ) -> plugins:
        if not model_files:
            pytest.skip(f"No model files found in directory: {foqus_plugin_models_dir}")
        return active_session.pymodels

    def test_plugin_models_loaded(self, pymodels: plugins, expected_plugin_keys):
        assert len(pymodels.plugins) > 0
        # sort both lists before comparing to ensure order matches
        assert sorted(pymodels.plugins.keys()) == sorted(expected_plugin_keys)


# it would be nice to have a GUI test for this too, leaving the commented code here for future reference

# @pytest.fixture(scope="class")
# def trigger_flowsheet_run_action(
#     self,
#     qtbot: QtBot,
#     active_session,
#     main_window: mainWindow,
#     pymodels,
# ):
#     run_action = main_window.runAction
#     with qtbot.replacing_with_signal(
#         (QtWidgets.QMessageBox, "information"),
#         (QtWidgets.QMessageBox, "critical"),
#     ) as signal:
#         with qtbot.wait_signal(signal, timeout=2_000):
#             run_action.trigger()
#     return run_action

# @pytest.fixture(scope="class")
# def statusbar_message(self, main_window: mainWindow) -> str:
#     return main_window.statusBar().currentMessage()

# # specific methods to test running each example (main example using the
# # 'Linear' normalization flag, simple example without a custom layer, and
# # a modified example with a custom normalization function form)

# @pytest.fixture(scope="class")
# def simnode(self, active_session):
#     simnode = active_session.mainWin.nodeDock
#     return simnode

# def test_sim_and_modeltype(self, active_session, simnode):
#     # set simulation node node and confirm the updates are correct
#     simnode.setNodeName("test")
#     assert simnode.nodeNameBox.currentText() == "test"
#     assert simnode.nodeName == "test"

#     # set model type to 2 and confirm it's Plugin
#     simnode.modelTypeBox.setCurrentIndex(2)
#     assert simnode.modelTypeBox.currentText() == "Plugin"

# def test_load_and_run_heatintegration(self, active_session, simnode):
#     # set sim name and confirm it's the correct model
#     simnode.simNameBox.setCurrentIndex(0)
#     assert simnode.simNameBox.currentText() == "heat_integration"

#     def test_flowsheet_run_successful(
#         self,
#         trigger_flowsheet_run_action,
#         statusbar_message: str,
#         text_when_success: str = "Finished Single Simulation... Success",
#     ):
#         assert text_when_success in statusbar_message

# def test_load_and_run_pymodeltest(self, active_session, simnode):
#     # set sim name and confirm it's the correct model
#     simnode.simNameBox.setCurrentIndex(1)
#     assert simnode.simNameBox.currentText() == "pymodel_test"

#     def test_flowsheet_run_successful(
#         self,
#         trigger_flowsheet_run_action,
#         statusbar_message: str,
#         text_when_success: str = "Finished Single Simulation... Success",
#     ):
#         assert text_when_success in statusbar_message

# def test_load_and_run_steamcycle(self, active_session, simnode):
#     # set sim name and confirm it's the correct model
#     simnode.simNameBox.setCurrentIndex(2)
#     assert simnode.simNameBox.currentText() == "steam_cycle"

#     def test_flowsheet_run_successful(
#         self,
#         trigger_flowsheet_run_action,
#         statusbar_message: str,
#         text_when_success: str = "Finished Single Simulation... Success",
#     ):
#         assert text_when_success in statusbar_message
