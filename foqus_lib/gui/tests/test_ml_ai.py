from pathlib import Path
import shutil
from typing import List, Tuple

import pytest
from pytest_qt_extras import QtBot, instrument
from PyQt5 import QtWidgets

from foqus_lib.gui.main.mainWindow import mainWindow
from foqus_lib.framework.session import session as FoqusSession
from foqus_lib.gui.flowsheet.drawFlowsheet import drawFlowsheet
from foqus_lib.framework.ml_ai_models.mlaiSearch import ml_ai_models


_ = pytest.importorskip("tensorflow", reason="tensorflow not installed")


@pytest.fixture(
    scope="module", params=["other_files/ML_AI_Plugin/mea_column_model.foqus"]
)
def flowsheet_session_file(examples_dir: Path, request) -> Path:
    return examples_dir / request.param


@pytest.fixture(scope="module", autouse=True)
def models_dir(
    foqus_working_dir: Path,
) -> Path:

    return foqus_working_dir / "user_ml_ai_models"


@pytest.fixture(
    scope="module",
    autouse=True,
)
def install_ml_ai_model_files(examples_dir: Path, models_dir: Path) -> Path:
    """
    This is a module-level fixture with autouse b/c it needs to be created before the main window is instantiated.
    """

    base_path = examples_dir / "other_files" / "ML_AI_Plugin"
    ts_models_base_path = base_path / "TensorFlow_2-7_Models"

    models_dir.mkdir(exist_ok=True, parents=False)

    for path in [
        base_path / "mea_column_model.py",
        ts_models_base_path / "mea_column_model.h5",
    ]:
        shutil.copy2(path, models_dir)
    yield models_dir


@pytest.fixture(scope="module")
def model_files(
    models_dir: Path,
    suffixes: Tuple[str] = (".py", ".h5"),
) -> List[Path]:
    paths = []
    for path in sorted(models_dir.glob("*")):
        if all(
            [
                path.is_file(),
                path.stat().st_size > 0,
                path.suffix in suffixes,
                path.name != "__init__.py",
            ]
        ):
            paths.append(path)
    return paths


def test_model_files_are_present(model_files: List[Path]):
    assert model_files


class TestMLAIPluginFlowsheetRun:
    @pytest.fixture
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

    @pytest.fixture
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

    @pytest.fixture
    def pymodels_ml_ai(
        self,
        active_session: FoqusSession,
        model_files: List[Path],
        models_dir: Path,
    ) -> ml_ai_models:
        if not model_files:
            pytest.skip(f"No model files found in directory: {models_dir}")
        return active_session.pymodels_ml_ai

    def test_ml_ai_models_loaded(self, pymodels_ml_ai: ml_ai_models):
        assert len(pymodels_ml_ai.ml_ai_models) > 0

    @pytest.fixture
    def trigger_flowsheet_run_action(
        self,
        qtbot: QtBot,
        active_session,
        main_window: mainWindow,
        pymodels_ml_ai,
    ):
        run_action = main_window.runAction
        with qtbot.replacing_with_signal(
            (QtWidgets.QMessageBox, "information"),
            (QtWidgets.QMessageBox, "critical"),
        ) as signal:
            with qtbot.wait_signal(signal, timeout=2_000):
                run_action.trigger()
        return run_action

    @pytest.fixture(scope="function")
    def statusbar_message(self, main_window: mainWindow) -> str:
        return main_window.statusBar().currentMessage()

    def test_flowsheet_run_successful(
        self,
        trigger_flowsheet_run_action,
        statusbar_message: str,
        text_when_success: str = "Finished Single Simulation... Success",
    ):
        assert text_when_success in statusbar_message
