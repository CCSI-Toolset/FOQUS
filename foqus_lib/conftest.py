import os
from pathlib import Path
import shutil


import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--slowdown-wait",
        action="store",
        default=100,
    )
    parser.addoption(
        "--artifacts-path",
        action="store",
        default=".pytest-artifacts",
    )
    parser.addoption(
        "--main-window-size",
        action="store",
        default="800x600",
        help="Size of the main window specified as a <width>x<height> string",
    )
    parser.addoption("--main-window-title", action="store", default="FOQUS")


@pytest.fixture(scope="session")
def _repo_root():
    this_file = Path(__file__).resolve()  # FOQUS/foqus_lib/conftest.py
    repo_root = this_file.parent.parent
    assert (repo_root / ".git").is_dir()
    return repo_root


@pytest.fixture(scope="session")
def examples_dir(_repo_root):
    _examples_dir = _repo_root / "examples"
    assert _examples_dir.exists()
    return _examples_dir


@pytest.fixture(scope="session")
def psuade_path():
    _psuade_path = shutil.which("psuade")
    assert _psuade_path is not None
    return Path(_psuade_path).resolve()


@pytest.fixture(scope="session", params=["UQ/Rosenbrock.foqus"])
def flowsheet_session_file(examples_dir, request):
    return str(examples_dir / "test_files" / request.param)


@pytest.fixture(
    scope="session",
)
def foqus_working_dir(qtbot_params):
    # FIXME use CLI params
    return Path("/tmp") / "foqus_working_dir"


@pytest.fixture(scope="session")
def foqus_session(foqus_working_dir, psuade_path):
    from foqus_lib.service.flowsheet import _set_working_dir
    from foqus_lib.framework.session import session

    _set_working_dir(foqus_working_dir)
    # foqus_working_dir.mkdir(exist_ok=True, parents=True)
    # reproducing what happens in foqus_lib.focus.main()
    # os.chdir(foqus_working_dir)
    session.makeWorkingDirStruct()
    session.makeWorkingDirFiles()

    dat = session.session(useCurrentWorkingDir=True)
    dat.foqusSettings.psuade_path = str(psuade_path)
    return dat
