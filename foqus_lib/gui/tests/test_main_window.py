"Basic/smoke tests to ensure that the main window opens without errors."

import pytest


pytestmark = pytest.mark.gui


def test_main_window_opens(qtbot, main_window):
    qtbot.slow_down()
    assert main_window is not None
