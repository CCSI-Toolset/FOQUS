import os
from pathlib import Path

import pytest

from foqus_lib import foqus


@pytest.fixture
def examples_dir_path():
    return Path(__file__).parent.parent.parent / 'examples'


@pytest.fixture
def input_file(examples_dir_path):
    return str(examples_dir_path / 'test_files/Optimization/Opt_Test_01.foqus')


@pytest.fixture
def nonexisting_input_file():
    return 'SHOULD_NOT_EXIST.foqus'


@pytest.fixture
def output_file():
    return 'test_opt.foqus'


def test_run_optimization_with_existing_input_file_succeeds(input_file, output_file):
    assert Path(input_file).exists()

    cli_args = [
        '--load', input_file,
        '--run', 'opt',
        '--out', output_file,
    ]

    with pytest.raises(SystemExit, match='0'):
        foqus.main(cli_args)

    assert Path(output_file).exists()


def test_run_optimization_with_nonexisting_input_file_fails(nonexisting_input_file, output_file):
    assert not Path(nonexisting_input_file).exists()

    cli_args = [
        '--load', nonexisting_input_file,
        '--run', 'opt',
        '--out', output_file,
    ]

    with pytest.raises(SystemExit, match='10'):
        foqus.main(cli_args)


@pytest.mark.requires_human("Close the GUI window manually to complete the test")
def test_start_gui():
    cli_args = []
    with pytest.raises(SystemExit, match="0"):
        foqus.main(cli_args)


def test_gui_imports():
    if foqus.PyQt5 is None:
        foqus.guiImport()
    assert foqus.PyQt5 is not None, "After running guiImport(), foqus.PyQt5 points to the actual module instead of the placeholder value None"
