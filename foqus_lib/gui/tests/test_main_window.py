"Basic/smoke tests to ensure that the main window opens without errors."

import pytest


pytestmark = pytest.mark.gui


def test_main_window_opens(qtbot, main_window):
    qtbot.slow_down()
    main_window.close()


@pytest.fixture(scope='class')
def setup_main_window(qtbot, main_window):
    qtbot.focused = main_window


def _matches_current_index(mw, idx_or_key):
    if isinstance(idx_or_key, str):
        idx = mw.screenIndex[idx_or_key]
    else:
        idx = idx_or_key
    return mw.mainWidget.currentIndex() == idx


@pytest.mark.usefixtures('setup_main_window')
class TestNavigateMainWindow:

    def test_home_screen_visible_before_clicking(self, main_window):
        assert _matches_current_index(main_window, "home")

    def test_flowsheet_screen_visible_after_clicking(self, qtbot, main_window):
        with qtbot.wait_signal(main_window.fsEditAction.triggered):
            qtbot.click(button="Flowsheet")
        assert _matches_current_index(main_window, "flow")

    def test_uncertainty_screen_visible_after_clicking(self, qtbot, main_window):
        with qtbot.wait_signal(main_window.uqSetupAction.triggered):
            qtbot.click(button="Uncertainty")
        assert _matches_current_index(main_window, "uq")

    def test_optimization_screen_visible_after_clicking(self, qtbot, main_window):
        with qtbot.wait_signal(main_window.optSetupAction.triggered):
            qtbot.click(button="Optimization")
        assert _matches_current_index(main_window, "opt")

    def test_ouu_screen_visible_after_clicking(self, qtbot, main_window):
        with qtbot.wait_signal(main_window.ouuSetupAction.triggered):
            qtbot.click(button="OUU")
        assert _matches_current_index(main_window, "ouu")

    # TODO: Surrogates, Settings, Help
