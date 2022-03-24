import time
import typing
import os

from PyQt5 import QtWidgets, QtCore
import pytest

from foqus_lib.gui.ouu.ouuSetupFrame import ouuSetupFrame
from foqus_lib.gui.ouu import foqusPSUADEClient
from foqus_lib.gui.ouu.OUUInputsTable import OUUInputsTable
from foqus_lib.gui.ouu import nodeToUQModel

from foqus_lib.framework.uq.LocalExecutionModule import LocalExecutionModule
from foqus_lib.gui.common.InputPriorTable import InputPriorTable


@pytest.fixture(scope="class")
def setup_frame_blank(main_window, request):
    main_window.ouuSetupAction.trigger()
    setup_frame: ouuSetupFrame = main_window.ouuSetupFrame
    request.cls.frame = setup_frame
    return setup_frame

@pytest.mark.usefixtures("setup_frame_blank")
class TestOUU():
    frame: ouuSetupFrame = ...
    ###############
    '''
    simple test to check the very basic test case
    '''
    @pytest.fixture(scope="class")
    def launchWindow(self, qtbot):
        qtbot.focused = self.frame
        
    @pytest.mark.usefixtures("launchWindow")
    def test_window(self):
        assert True

    ################
    '''
    Fixtures for comprehensive tests
    '''
    @pytest.fixture(scope="class")
    def selectModel(self, qtbot):
        ouu_frame = self.frame
        qtbot.focused = ouu_frame
        fname = os.path.join(
            os.path.dirname(__file__),
            "../../../examples/tutorial_files/OUU/ouu_optdriver.in",
        )
        fname = os.path.abspath(fname)
        ouu_frame.filesDir, _ = os.path.split(fname)
        ouu_frame.modelFile_edit.setText(fname)
        ouu_frame.model = LocalExecutionModule.readSampleFromPsuadeFile(fname).model
        ouu_frame.input_table.init(ouu_frame.model, InputPriorTable.OUU)
        ouu_frame.setFixed_button.setEnabled(True)
        ouu_frame.setX1_button.setEnabled(True)
        ouu_frame.setX2_button.setEnabled(True)
        ouu_frame.setX3_button.setEnabled(True)
        ouu_frame.setX4_button.setEnabled(True)
        ouu_frame.initTabs()
        ouu_frame.setCounts()
        

    @pytest.fixture(scope="class")
    def setVariables(self, qtbot):
        vars = ["Opt: Primary Continuous (Z1)", "Opt: Recourse (Z2)", "UQ: Discrete (Z3)"]
        # "Opt: Recourse (Z2)", "UQ: Discrete (Z3)", "UQ: Continuous (Z4)"
        with qtbot.focusing_on(table=any):
            rownum = 0
            for i in range(len(vars)):
                for _ in range(4):
                    qtbot.select_row(rownum)
                    qtbot.using(column="Type").set_option(vars[i])
                    rownum += 1

    @pytest.fixture(scope="class")
    def selectOptimizer(self, qtbot):
        qtbot.select_tab("Optimization Setup")
        # with qtbot.focusing_on(group_box="Optimization Solver"):
        #     combo = qtbot.locate(combo_box=any)
        #     # optimizer = "Use model as optimizer: min_Z2 G(Z1,Z2,Z3,Z4)"
        #     # qtbot.using(combo).set_option(vars[i])



    @pytest.fixture(scope="class")
    def selectDiscreteRandomVars(self, qtbot):
        ouu_frame = self.frame
        qtbot.select_tab("UQ Setup")

        fname = os.path.join(
            os.path.dirname(__file__),
            "../../../examples/tutorial_files/OUU/ex1_x3sample.smp",
        )

        ouu_frame.filesDir, _ = os.path.split(fname)

        data = LocalExecutionModule.readDataFromSimpleFile(
                    fname, hasColumnNumbers=False)
        data = data[0]

        numInputs = data.shape[1]
        M3 = len(ouu_frame.input_table.getUQDiscreteVariables()[0])
        print(data)

        # self.data, self.numInputs, self.M3 = data, numInputs, M3

        # ouu_frame.loadTable(ouu_frame.z3_table, data)

        if numInputs != M3:
            # have to be an assertion
            pass
        else:
            # ouu_frame.compressSamples_chk.setEnabled(True)
            with qtbot.focusing_on(group_box=" Discrete Random Variables (Z3)"):
                ouu_frame.loadTable(ouu_frame.z3_table, data)


    @pytest.fixture(scope="class")
    def loadRandomVariables(self):
        ouu_frame = self.frame
        with qtbot.focusing_on(table=ouu_frame.z3_table):
            ouu_frame.loadTable(ouu_frame.z3_table, self.data)


    @pytest.fixture(scope="class")
    def launchTest(self, qtbot):
        qtbot.select_tab("Launch/Progress")

        def run_and_wait():
                qtbot.click(button="Run OUU")
                qtbot.wait_until_called(self.frame.unfreeze)

        run_and_wait()
        # run_button = qtbot.locate(button="Run OUU")
        # qtbot.click(run_button)

        # with qtbot.focusing_on(
        #     group_box="Progress"
        # ), qtbot.taking_screenshots():
        #     # ouu_frame = self.frame
            
        # with qtbot.select_tab("Launch/Progress"), qtbot.taking_screenshots():
        #     qtbot.click(button="Run OUU")


    ###################
    '''
    Comprehensive tests for OUU tutorial 1
    '''
    def testModel(self, qtbot, selectModel, setVariables, selectOptimizer):
        assert True

    @pytest.mark.usefixtures("selectDiscreteRandomVars")
    def testRandomVarSetting(self):
        assert True

    # def testRandomVarSetting(self, qtbot, selectDiscreteRandomVars):
    #     assert self.numInputs == self.M3
    #     with qtbot.searching_within(group_box="Discrete Random Variables (Z3)"):
    #         var_table = qtbot.locate_widget(table=True)
    #         assert var_table.rowCount() > 0

    # @pytest.mark.usefixtures("loadRandomVariables")
    # def testRandomVarTable(self, qtbot):
    #     with qtbot.searching_within(group_box="Discrete Random Variables (Z3)"):
    #         var_table = qtbot.locate_widget(table=True)
    #         assert var_table.rowCount() > 0

    @pytest.mark.usefixtures("launchTest")
    def testRun(self):
        with qtbot.searching_within(group_box="Launch/Progress"):
            sol_table = qtbot.locate_widget(table=True)
            assert sol_table.rowCount() > 0