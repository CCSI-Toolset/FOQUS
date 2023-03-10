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
def main_window_params(request):
    cfg = request.config
    width, height = cfg.getoption("--main-window-size").split("x")
    return {
        "width": int(width),
        "height": int(height),
        "title": cfg.getoption("--main-window-title"),
    }


@pytest.fixture(scope="session")
def main_window(foqus_session, main_window_params):
    "Main window object, initialized once per pytest session."
    from foqus_lib import foqus

    foqus.guiImport(mpl_backend="AGG")

    from foqus_lib.gui.main.mainWindow import mainWindow

    app = QtWidgets.QApplication([])

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
    main_win.app = app
    print(f"main_win.app={main_win.app}")
    print(f"main_win.app.activeWindow()={main_win.app.activeWindow()}")
    yield main_win

    def handle_closing_prompt(w: QtWidgets.QMessageBox):
        return QtWidgets.QMessageBox.No

    with pytest_qt_extras._ModalPatcher(QtWidgets.QMessageBox).patching(
        handle_closing_prompt
    ):
        main_win.close()


@pytest.fixture(scope="session")
def qtbot_params(request, tmp_path_factory):
    cfg = request.config
    artifacts = cfg.getoption("--qtbot-artifacts")

    if bool(artifacts):
        artifacts = Path(artifacts)
        if not artifacts.absolute():
            artifacts = tmp_path_factory.mktemp(artifacts, numbered=False)
    else:
        artifacts = False

    return {
        "slowdown_wait": int(cfg.getoption("--qtbot-slowdown-wait-ms")),
        "artifacts": artifacts,
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
    _qtbot.cleanup()
