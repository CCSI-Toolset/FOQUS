import contextlib
import logging
import os
from pathlib import Path
import shutil
import typing as t

from PyQt5 import QtWidgets, QtCore, QtGui

import pytest
from pytestqt.exceptions import capture_exceptions, format_captured_exceptions
from _pytest.monkeypatch import MonkeyPatch
import pytest_qt_extras


def pytest_addoption(parser):
    parser.addoption(
        '--slowdown-wait', action='store', default=100,
    )
    parser.addoption(
        '--artifacts-path', action='store', default='.pytest-artifacts',
    )
    parser.addoption(
        '--main-window-size', action='store', default='800x600', help="Size of the main window specified as a <width>x<height> string"
    )
    parser.addoption(
        '--main-window-title', action='store', default='FOQUS'
    )


@pytest.fixture(scope='session', autouse=True)
def configure_logging(request):
    logger = pytest_qt_extras._logger

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(logging.Formatter('%(relativeCreated)6d :: %(levelname)s :: %(filename)s:L%(lineno)d :: %(message)s'))
    logger.addHandler(console)


@pytest.fixture(scope='session')
def qtbot_params(request):
    cfg = request.config
    return {
        'slowdown_wait': int(cfg.getoption('--slowdown-wait')),
        'artifacts_path': Path(cfg.getoption('--artifacts-path')).absolute(),
    }


@pytest.fixture(scope='class')
def qtbot(request, qapp, qtbot_params) -> pytest_qt_extras.QtBot:
    _qtbot = pytest_qt_extras.QtBot(request, **qtbot_params)
    with capture_exceptions() as exceptions:
        yield _qtbot
    if exceptions:
        pytest.fail(format_captured_exceptions(exceptions))
    _qtbot.describe()


@pytest.fixture(scope='session')
def examples_dir():
    here = Path(__file__).resolve()  # FOQUS/test/conftest.py
    _examples_dir = here.parent.parent / 'examples'
    assert _examples_dir.exists()
    return _examples_dir


@pytest.fixture(scope='session')
def psuade_path():
    _psuade_path = shutil.which('psuade')
    assert _psuade_path is not None
    return Path(_psuade_path).resolve()


@pytest.fixture(
    scope='session',
    params=[
        'UQ/Rosenbrock.foqus'
    ]
)
def flowsheet_session_file(examples_dir, request):
    return str(examples_dir / 'test_files' / request.param)


@pytest.fixture(
    scope='session',
)
def foqus_working_dir(qtbot_params):
    return qtbot_params['artifacts_path'] / 'foqus_working_dir'


@pytest.fixture(scope="session")
def foqus_session(foqus_working_dir, psuade_path):
    from foqus_lib.framework.session import session
    foqus_working_dir.mkdir(exist_ok=True, parents=True)
    # reproducing what happens in foqus_lib.focus.main()
    os.chdir(foqus_working_dir)
    session.makeWorkingDirStruct()
    session.makeWorkingDirFiles()

    dat = session.session(useCurrentWorkingDir=True)
    dat.foqusSettings.psuade_path = str(psuade_path)
    return dat


@pytest.fixture(scope='session')
def main_window_params(request):
    cfg = request.config
    width, height = cfg.getoption('--main-window-size').split('x')
    return {
        'width': int(width),
        'height': int(height),
        'title': cfg.getoption('--main-window-title'),
    }


@pytest.yield_fixture(scope="class")
def main_window(foqus_session, qtbot, main_window_params):
    from foqus_lib import foqus
    foqus.guiImport(mpl_backend='AGG')

    from foqus_lib.gui.main.mainWindow import mainWindow

    main_win = mainWindow(
        main_window_params['title'],
        main_window_params['width'],
        main_window_params['height'],
        foqus_session, # FOQUS session data
        splash=None,
        showUQ=False,
        showOpt=False,
        showOuu=True,
        showBasicData=False,
        showSDOE=False,
        ts=False
    )
    main_win.closeEvent = lambda *args, **kwargs: None
    print(f'main_win={main_win}')
    main_win.app = QtWidgets.QApplication.instance()
    print(f'main_win.app={main_win.app}')
    # qtbot.addWidget(main_win)
    qtbot.waitForWindowShown(main_win)
    print(f'main_win.app.activeWindow()={main_win.app.activeWindow()}')
    yield main_win
    main_win.close()
