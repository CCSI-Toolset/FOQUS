import contextlib
import logging
import os
from pathlib import Path
import shutil
import sys
import typing as t

from PyQt5 import QtWidgets, QtCore, QtGui

import pytest
from pytestqt.exceptions import capture_exceptions, format_captured_exceptions
from _pytest.monkeypatch import MonkeyPatch
import pytest_qt_extras


@pytest.fixture(scope="session", autouse=True)
def configure_logging(request):
    logger = pytest_qt_extras._logger

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(
        logging.Formatter(
            "%(relativeCreated)6d :: %(levelname)s :: %(filename)s:L%(lineno)d :: %(message)s"
        )
    )
    logger.addHandler(console)


@pytest.fixture(scope="session")
def qtbot_params(request):
    cfg = request.config
    return {
        "slowdown_wait": int(cfg.getoption("--slowdown-wait")),
        "artifacts_path": Path(cfg.getoption("--artifacts-path")).absolute(),
    }


@pytest.fixture(scope="class")
def qtbot(request, qapp, qtbot_params) -> pytest_qt_extras.QtBot:
    if sys.version_info < (3, 7):
        pytest.skip("GUI tests are not available for Python 3.6 or lower")
    _qtbot = pytest_qt_extras.QtBot(request, **qtbot_params)
    with capture_exceptions() as exceptions:
        yield _qtbot
    if exceptions:
        pytest.fail(format_captured_exceptions(exceptions))
    # _qtbot.cleanup()


@pytest.fixture(scope="session")
def main_window_params(request):
    cfg = request.config
    width, height = cfg.getoption("--main-window-size").split("x")
    return {
        "width": int(width),
        "height": int(height),
        "title": cfg.getoption("--main-window-title"),
    }


@pytest.yield_fixture(scope="class")
def main_window(foqus_session, qtbot, main_window_params):
    from foqus_lib import foqus

    foqus.guiImport(mpl_backend="AGG")

    from foqus_lib.gui.main.mainWindow import mainWindow

    main_win = mainWindow(
        main_window_params["title"],
        main_window_params["width"],
        main_window_params["height"],
        foqus_session,  # FOQUS session data
        splash=None,
        showUQ=False,
        showOpt=False,
        showOuu=True,
        showBasicData=False,
        showSDOE=False,
        ts=False,
    )
    print(f"main_win={main_win}")
    main_win.app = QtWidgets.QApplication.instance()
    print(f"main_win.app={main_win.app}")
    # qtbot.add_widget(main_win)
    qtbot.waitForWindowShown(main_win)
    print(f"main_win.app.activeWindow()={main_win.app.activeWindow()}")
    yield main_win

    def handle_closing_prompt(w: QtWidgets.QMessageBox):
        return QtWidgets.QMessageBox.No

    with pytest_qt_extras._ModalPatcher(QtWidgets.QMessageBox).patching(
        handle_closing_prompt
    ):
        main_win.close()
    qtbot.cleanup()


@pytest.fixture(scope="class")
def uq_setup_view(main_window, flowsheet_session_file, qtbot):
    main_window.loadSessionFile(flowsheet_session_file, saveCurrent=False)
    main_window.uqSetupAction.trigger()
    return main_window.uqSetupFrame
