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
from PyQt5 import QtCore, QtWidgets

MAX_RUN_TIME = 50000  # Maximum time to let script run in ms.
testOutFile = "ui_test_out.txt"
with open(testOutFile, "w") as f:  # file to write test results to
    f.write("Test Results\n")
timers = {}  # mainly put all timers in a dic so I can easily stop them all


def go(sleep=0.25, MainWin=MainWin):
    """Process gui events
    Since this script is running holds up the GUI main loop, this function
    processes GUI events and checks if the stop button has been pressed. It also
    pauses for sleep seconds to let things happen.
    """
    MainWin.app.processEvents()
    time.sleep(sleep)
    return not MainWin.helpDock.stop  # Return true is stop flag is set


def getButton(w, label):
    """Get a button in window w labeled label"""
    blist = w.buttons()
    for b in blist:
        if b.text().replace("&", "") == label:
            return b
    return None


def msg_okay(MainWin=MainWin, getButton=getButton, timers=timers):
    """Click OK when a msgbox pops up, stops timer once a msgbox pops up"""
    w = MainWin.app.activeWindow()
    if isinstance(w, QtWidgets.QMessageBox):
        getButton(w, "OK").click()
        timers["msg_okay"].stop()


def msg_no(MainWin=MainWin, getButton=getButton, timers=timers):
    """Click No when a msgbox pops up, stops timer once a msgbox pops up"""
    w = MainWin.app.activeWindow()
    if isinstance(w, QtWidgets.QMessageBox):
        getButton(w, "No").click()
        timers["msg_no"].stop()


def add_UQ_cancel(MainWin=MainWin, getButton=getButton, timers=timers):
    """Cancel adding a UQ ensemble, stops timer once the window comes up"""
    w = MainWin.app.activeWindow()
    if "updateUQModelDialog" in str(type(w)):
        getButton(w.buttonBox, "Cancel").click()
        timers["add_UQ_cancel"].stop()


def add_UQ_okay(MainWin=MainWin, getButton=getButton, timers=timers):
    """Press OK in adding a UQ ensemble, stops timer once the window comes up"""
    w = MainWin.app.activeWindow()
    if "updateUQModelDialog" in str(type(w)):
        getButton(w.buttonBox, "OK").click()
        timers["add_UQ_okay"].stop()


def uq_sampling_scheme(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup up an enseble sampling scheme, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    if "SimSetup" in str(type(w)):
        timers["uq_sampling_scheme"].stop()
        w.distTable.cellWidget(2, 1).setCurrentIndex(1)
        w.samplingTabs.setCurrentIndex(1)
        items = w.schemesList.findItems("Latin Hypercube", QtCore.Qt.MatchExactly)
        w.schemesList.setCurrentItem(items[0])
        w.numSamplesBox.setValue(100)
        w.generateSamplesButton.click()
        if not go(sleep=2):
            return  # wait long enough for samples to generate
        w.doneButton.click()


def uq_analyze_scheme(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup a UQ analysis from the sampling scheme, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    if "AnalysisDialog" in str(type(w)):
        timers["uq_analyze_scheme"].stop()
        ## Change to Expert Mode
        if w.modeButton.text() == w.wizardModeButtonText:
            w.modeButton.click()
        ## Select the Output to Analyze
        output_index = w.output_combo.findText("Rosenbrock.f")
        w.output_combo.setCurrentIndex(output_index)
        ## Begin Input Importance Calculation
        w.screen_button.click()
        param_selection = w.screen_combo.findText("Sum of Trees")
        w.screen_combo.setCurrentIndex(param_selection)
        w.screen_button.click()
        #        param_selection = w.screen_combo.findText('Delta Test')
        #        w.screen_combo.setCurrentIndex(param_selection)
        #        w.screen_button.click()
        #        param_selection = w.screen_combo.findText('Gaussian Process')
        #        w.screen_combo.setCurrentIndex(param_selection)
        #        w.screen_button.click()
        #        ## Begin Data Analysis
        #        w.dataAnalyze_button.click()
        #        w.dataAnalyze_combo1.setCurrentIndex(1)
        #        w.dataAnalyze_button.click()
        ##        ### This Part is Only for the Sensitivity Analysis Which Requires  \
        ##        ### at Least 1,000 Points to Work and 10,000 Points for Total Order
        ##        #### Just Sensitivity
        ##        w.dataAnalyze_combo1.setCurrentIndex(2)
        ##        w.dataAnalyze_button.click()
        ##        #### Second Order Sensitivity
        ##        w.dataAnalyze_combo2.setCurrentIndex(1)
        ##        w.dataAnalyze_button.click()
        ##        #### Total Order Sensitivity (10,000 runs needed)
        ##        w.dataAnalyze_combo2.setCurrentIndex(2)
        ##        w.dataAnalyze_button.click()
        #        ### Begin Data Visualization
        #        w.dataViz_combo1.setCurrentIndex(3)
        #        w.dataViz_button.click()
        #        w.dataViz_combo1.setCurrentIndex(0)
        #        w.dataViz_combo2.setCurrentIndex(2)
        #        w.dataViz_button.click()
        #        w.dataViz_combo1.setCurrentIndex(1)
        #        w.dataViz_combo2.setCurrentIndex(4)
        #        w.dataViz_button.click()
        #        ## Begin Response Surface Validation
        #        w.RSValidate_button.click()
        #        response_sub_select = w.RS_combo2.findText('Quadratic Regression')
        #        w.RS_combo2.setCurrentIndex(response_sub_select)
        #        w.RSValidate_button.click()
        #        response_sub_select = w.RS_combo2.findText('Cubic Regression')
        #        w.RS_combo2.setCurrentIndex(response_sub_select)
        #        w.RSValidate_button.click()
        #        response_sub_select = w.RS_combo2.findText('Legendre Polynomial Regression')
        #        w.RS_combo2.setCurrentIndex(response_sub_select)
        #        w.RSValidate_button.click()
        #        response_select = w.RS_combo1.findText('MARS ->')
        #        w.RS_combo1.setCurrentIndex(response_select)
        #        w.RSValidate_button.click()
        #        response_sub_select = w.RS_combo2.findText('MARS with Bagging')
        #        w.RS_combo2.setCurrentIndex(response_sub_select)
        #        w.RSValidate_button.click()
        #        response_select = w.RS_combo1.findText('Gaussian Process')
        #        w.RS_combo1.setCurrentIndex(response_select)
        #        w.RSValidate_button.click()
        #        response_select = w.RS_combo1.findText('Kriging')
        #        w.RS_combo1.setCurrentIndex(response_select)
        #        w.RSValidate_button.click()
        #        response_select = w.RS_combo1.findText('Sum of Trees')
        #        w.RS_combo1.setCurrentIndex(response_select)
        #        w.RSValidate_button.click()
        #        response_select = w.RS_combo1.findText('K Nearest Neighbors')
        #        w.RS_combo1.setCurrentIndex(response_select)
        #        w.RSValidate_button.click()
        #        response_select = w.RS_combo1.findText('Radial Basis Function')
        #        w.RS_combo1.setCurrentIndex(response_select)
        #        w.RSValidate_button.click()
        #        ## Begin Response Surface Visualization
        #        w.RSViz_combo1.setCurrentIndex(1) #Should this be changed to use the
        #        w.RSViz_button.click()
        #        w.RSViz_combo1.setCurrentIndex(0)
        #        w.RSViz_combo2.setCurrentIndex(2)
        #        w.RSViz_button.click()
        #        w.RSViz_combo2.setCurrentIndex(0)
        #        w.RSViz_combo3.setCurrentIndex(3)
        #        w.RSViz_button.click()
        #        w.RSViz_combo1.setCurrentIndex(4)
        #        w.RSViz_combo2.setCurrentIndex(5)
        #        w.RSViz_combo3.setCurrentIndex(0)
        #        w.RSViz_button.click()
        #        w.RSViz_combo1.setCurrentIndex(2)
        #        w.RSViz_combo2.setCurrentIndex(0)
        #        w.RSViz_combo3.setCurrentIndex(1)
        #        w.RSViz_button.click()
        #        w.RSViz_combo1.setCurrentIndex(0)
        #        w.RSViz_combo2.setCurrentIndex(3)
        #        w.RSViz_combo3.setCurrentIndex(5)
        #        w.RSViz_button.click()
        #        w.RSViz_combo1.setCurrentIndex(3)
        #        w.RSViz_combo2.setCurrentIndex(4)
        #        w.RSViz_combo3.setCurrentIndex(2)
        #        w.RSViz_button.click()
        #        ## Begin Response Surface UQ Analysis
        #        w.RSAnalyze_button.click()
        #        w.RSAnalyze_combo2.setCurrentIndex(1) # Change analysis to Epistemic-Aleatory
        #        w.inputPrior_table.cellWidget(1,1).setCurrentIndex(1) # Change one cell to Epistemic
        #        w.RSAnalyze_button.click()
        #        ### Change to Sensitivity Analysis
        #        w.RSAnalyze_combo1.setCurrentIndex(1)
        ##        ####------------------------------- Trying to Get a Different Distribution to Work for this --------------------------------------------
        ##        w.inputPrior_table.cellWidget(2,3).setCurrentIndex(1) # Need to specify the fourth column here since the table just hides the columns not needed
        ##        w.inputPrior_table.setItem(2,4,QtWidgets.QTableWidgetItem(str(4)))
        ##        w.inputPrior_table.cellWidget(2,5).setItem("3")
        ##        ####-------------------------------------------------------------------------------------------------------------------------------------
        #        w.RSAnalyze_button.click()
        #        w.RSAnalyze_combo2.setCurrentIndex(1)
        #        w.RSAnalyze_button.click()
        #        w.RSAnalyze_combo2.setCurrentIndex(2)
        #        w.RSAnalyze_button.click()
        #        ### Change to Point Evaluation
        #        w.RSAnalyze_combo1.setCurrentIndex(2)
        #        w.RSAnalyze_button.click()
        ## Begin Inference
        #        w.expertInfer_button.click()
        #        ## Close Window
        w.close()


def uq_infer_scheme(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup a UQ analysis from the sampling scheme, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    if "InferenceDialog" in str(type(w)):
        timers["uq_infer_scheme"].stop()
        w.output_table.cellWidget(1, 0).toggle()
        ## Test Different Response Surfaces
        # w.inf_button.click()
        response_sub_select = w.output_table.cellWidget(1, 3).findText("Quadratic")
        w.output_table.cellWidget(1, 3).setCurrentIndex(response_sub_select)
        w.inf_button.click()
        #        w.close_button.click()
        #        response_sub_select = w.output_table.cellWidget(1,3).findText('Cubic')
        #        w.output_table.cellWidget(1,3).setCurrentIndex(response_sub_select)
        #        w.inf_button.click()
        #        response_sub_select = w.output_table.cellWidget(1,3).findText('Legendre')
        #        w.output_table.cellWidget(1,3).setCurrentIndex(response_sub_select)
        #        w.inf_button.click()
        #        response_select = w.output_table.cellWidget(1,2).findText('MARS ->')
        #        w.output_table.cellWidget(1,2).setCurrentIndex(response_select)
        #        w.inf_button.click()
        #        response_sub_select = w.output_table.cellWidget(1,3).findText('With Bagging')
        #        w.output_table.cellWidget(1,3).setCurrentIndex(response_sub_select)
        #        w.inf_button.click()
        #        response_select = w.output_table.cellWidget(1,2).findText('Gaussian Process')
        #        w.output_table.cellWidget(1,2).setCurrentIndex(response_select)
        #        w.inf_button.click()
        #        response_select = w.output_table.cellWidget(1,2).findText('Kriging')
        #        w.output_table.cellWidget(1,2).setCurrentIndex(response_select)
        #        w.inf_button.click()
        #        response_select = w.output_table.cellWidget(1,2).findText('Sum of Trees')
        #        w.output_table.cellWidget(1,2).setCurrentIndex(response_select)
        #        w.inf_button.click()
        #        response_select = w.output_table.cellWidget(1,2).findText('K Nearest Neighbors')
        #        w.output_table.cellWidget(1,2).setCurrentIndex(response_select)
        #        w.inf_button.click()
        #        response_select = w.output_table.cellWidget(1,2).findText('Radial Basis Function')
        #        w.output_table.cellWidget(1,2).setCurrentIndex(response_select)
        #        w.inf_button.click()
        #        ## Enable Discrepancy
        #        w.discrepancy_chkbox.toggle()
        #        response_select = w.output_table.cellWidget(1,2).findText('Polynomial ->')
        #        w.output_table.cellWidget(1,2).setCurrentIndex(response_select)
        #        w.inf_button.click()
        w.close()


def uq_analyze_close(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup a UQ analysis from the sampling scheme, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    if "AnalysisDialog" in str(type(w)):
        timers["uq_analyze_close"].stop()
        w.close()


def uq_infer_close(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup a UQ analysis from the sampling scheme, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    if "InferenceDialog" in str(type(w)):
        timers["uq_infer_close"].stop()
        w.close_button.click()


def addTimer(name, cb, MainWin=MainWin, timers=timers):
    """Add a timer to do something.  Timers are needed because some things like
    a modal dialog box will hold up executaion on the main UI thread, so a timer
    can be used to do something while execution of this script is held up.

    Args:
        name: string name of timer
        cb: timer call back function (timer should stop itself once it's done)
    """
    timers[name] = QtCore.QTimer(MainWin)
    timers[name].timeout.connect(cb)


def timersStop(timers=timers):
    """Stop all timers"""
    for key, t in iter(timers.items()):
        t.stop()


def timerWait(timer, sleep=0.25, n=40, go=go, timers=timers, tf=testOutFile):
    """Wait sleep*n seconds for timer to finish its job."""
    for i in range(n):
        if not go(sleep=sleep):
            return False
        if not timers[timer].isActive():
            return True
    timers[timer].stop()  # Timer never did it's thing so just shut it down
    with open(tf, "a") as f:  # file to write test results to
        f.write("ERROR: timer {} didn't stop in allotted time\n".format(timer))
    return False  # return False to stop script.  Something is wrong


# make the timers that will be needed just start and stop as needed
# need to make sure that when this script exits all timers are stopped
# or some crazy stuff may happen until you exit FOQUS.
addTimer("time_out", MainWin.helpDock.setStopTrue)  # stop script if too long
addTimer("msg_okay", msg_okay)  # click OK on mgsbox
addTimer("msg_no", msg_no)  # click No on msgbox
addTimer("add_UQ_cancel", add_UQ_cancel)  # click cancel on uq ensemble dialog
addTimer("add_UQ_okay", add_UQ_okay)  # click okay on uq ensemble dialog
addTimer("uq_sampling_scheme", uq_sampling_scheme)  # do sampling scheme dialog
addTimer("uq_analyze_scheme", uq_analyze_scheme)  # do analysis scheme dialog
addTimer("uq_infer_scheme", uq_infer_scheme)  # do inference scheme dialog

addTimer("uq_analyze_close", uq_analyze_close)  # do analysis scheme dialog
addTimer("uq_infer_close", uq_infer_close)  # do inference scheme dialog

timers["time_out"].start(MAX_RUN_TIME)  # start max script time timer

try:  # Catch any exception and stop all timers before finishing up
    while 1:  # Loop and break and break as convenient way to jump to end
        # Rosenbrock Test for UQ
        MainWin.homeAction.trigger()
        if not go():
            break
        # Enter some information
        MainWin.dashFrame.sessionNameEdit.setText("Rosenbrock Test")
        if not go():
            break
        MainWin.dashFrame.tabWidget.setCurrentIndex(1)
        if not go():
            break
        MainWin.dashFrame.setSessionDescription("Rosenbrock Description Text")
        if not go():
            break
        # Make a flowsheet
        MainWin.fsEditAction.trigger()
        if not go():
            break
        MainWin.addNodeAction.trigger()
        if not go():
            break
        MainWin.flowsheetEditor.sc.mousePressEvent(
            None, dbg_x=10, dbg_y=10, dbg_name="Rosenbrock"
        )
        if not go():
            break
        MainWin.toggleNodeEditorAction.trigger()
        if not go():
            break
        MainWin.nodeDock.addInput("x1")
        MainWin.nodeDock.addInput("x2")
        MainWin.nodeDock.addInput("x3")
        MainWin.nodeDock.addInput("x4")
        MainWin.nodeDock.addInput("x5")
        MainWin.nodeDock.addInput("x6")
        MainWin.nodeDock.inputVarTable.item(0, 5).setText("-10")
        MainWin.nodeDock.inputVarTable.item(0, 6).setText("10")
        MainWin.nodeDock.inputVarTable.item(1, 5).setText("-10")
        MainWin.nodeDock.inputVarTable.item(1, 6).setText("10")
        MainWin.nodeDock.inputVarTable.item(2, 5).setText("-10")
        MainWin.nodeDock.inputVarTable.item(2, 6).setText("10")
        MainWin.nodeDock.inputVarTable.item(3, 5).setText("-10")
        MainWin.nodeDock.inputVarTable.item(3, 6).setText("10")
        MainWin.nodeDock.inputVarTable.item(4, 5).setText("-10")
        MainWin.nodeDock.inputVarTable.item(4, 6).setText("10")
        MainWin.nodeDock.inputVarTable.item(5, 5).setText("-10")
        MainWin.nodeDock.inputVarTable.item(5, 6).setText("10")
        MainWin.nodeDock.inputVarTable.item(0, 4).setText("4")
        MainWin.nodeDock.inputVarTable.item(1, 4).setText("5")
        MainWin.nodeDock.inputVarTable.item(2, 4).setText("4")
        MainWin.nodeDock.inputVarTable.item(3, 4).setText("5")
        MainWin.nodeDock.inputVarTable.item(4, 4).setText("4")
        MainWin.nodeDock.inputVarTable.item(5, 4).setText("4")
        MainWin.nodeDock.inputVarTable.item(0, 1).setText("4")
        MainWin.nodeDock.inputVarTable.item(1, 1).setText("5")
        MainWin.nodeDock.inputVarTable.item(2, 1).setText("4")
        MainWin.nodeDock.inputVarTable.item(3, 1).setText("5")
        MainWin.nodeDock.inputVarTable.item(4, 1).setText("4")
        MainWin.nodeDock.inputVarTable.item(5, 1).setText("4")
        MainWin.nodeDock.toolBox.setCurrentIndex(1)
        MainWin.nodeDock.addOutput("f")
        MainWin.nodeDock.tabWidget.setCurrentIndex(2)
        MainWin.nodeDock.pyCode.setPlainText(
            "f['f'] = 0 \
                                             \nf['f'] += (1-x['x1'])**2 + 100.0*(x['x2']-x['x1']**2)**2 \
                                             \nf['f'] += (1-x['x2'])**2 + 100.0*(x['x3']-x['x2']**2)**2 \
                                             \nf['f'] += (1-x['x3'])**2 + 100.0*(x['x4']-x['x3']**2)**2 \
                                             \nf['f'] += (1-x['x4'])**2 + 100.0*(x['x5']-x['x4']**2)**2 \
                                             \nf['f'] += (1-x['x5'])**2 + 100.0*(x['x6']-x['x5']**2)**2"
        )
        MainWin.nodeDock.tabWidget.setCurrentIndex(0)
        if not go():
            break
        # Before running start up a timer to close completed run msgbox
        timers["msg_okay"].start(500)  # timer to push ok on a msgbox if up
        MainWin.runAction.trigger()  # run flowsheet
        while MainWin.singleRun.is_alive():
            if not go():
                MainWin.singleRun.terminate()
                break
        if not timerWait("msg_okay"):
            break
        # assert abs(self.flowsheet.output["Rosenbrock"]["f"] - 126859) < 1e-8
        # assert self.flowsheet.errorStat==0
        ## Try out controlling UQ ensemble add
        MainWin.uqSetupAction.trigger()
        if not go():
            break
        ## Start add then cancel
        # timers['add_UQ_cancel'].start(500)
        # MainWin.uqSetupFrame.addSimulationButton.click()
        # if not timerWait('add_UQ_cancel'): break
        # This time add for real
        timers["add_UQ_okay"].start(1000)
        timers["uq_sampling_scheme"].start(500)
        MainWin.uqSetupFrame.addSimulationButton.click()
        if not timerWait("add_UQ_okay"):
            break
        if not timerWait("uq_sampling_scheme"):
            break
        # Run UQ ensemble
        MainWin.uqSetupFrame.simulationTable.cellWidget(0, 3).click()
        timers["msg_okay"].start(500)  # press okay on ensemble done msgbox
        while MainWin.uqSetupFrame.gThread.isAlive():  # while is running
            if not go():
                MainWin.uqSetupFrame.gThread.terminate()
                break
        if not timerWait("msg_okay"):
            break
        #        timers['uq_infer_scheme'].start(500)
        timers["uq_analyze_scheme"].start(500)
        MainWin.uqSetupFrame.simulationTable.cellWidget(0, 4).click()
        if not timerWait("uq_analyze_scheme"):
            break
        #        if not timerWait('uq_infer_scheme'): break

        ### Test for second run
        timers["add_UQ_okay"].start(1000)
        timers["uq_sampling_scheme"].start(500)
        MainWin.uqSetupFrame.addSimulationButton.click()
        if not timerWait("add_UQ_okay"):
            break
        if not timerWait("uq_sampling_scheme"):
            break
        # Run UQ ensemble
        MainWin.uqSetupFrame.simulationTable.cellWidget(1, 3).click()
        timers["msg_okay"].start(500)  # press okay on ensemble done msgbox
        while MainWin.uqSetupFrame.gThread.isAlive():  # while is running
            if not go():
                MainWin.uqSetupFrame.gThread.terminate()
                break
        if not timerWait("msg_okay"):
            break
        timers["uq_infer_scheme"].start(500)
        timers["uq_analyze_scheme"].start(500)
        MainWin.uqSetupFrame.simulationTable.cellWidget(1, 4).click()
        if not timerWait("uq_analyze_scheme"):
            break
        if not timerWait("uq_infer_scheme"):
            break
        #        timers['uq_infer_close'].start(500)
        #        timers['uq_analyze_close'].start(500)
        #        if not timerWait('uq_infer_close'): break
        #        if not timerWait('uq_analyze_close'): break
        break
except Exception as e:
    # if there is any exception make sure the timers are stopped
    # before reraising it
    print("Exception stopping script")
    timersStop()
    with open(testOutFile, "a") as f:
        f.write("ERROR: Exception: {0}\n".format(e))
timersStop()  # make sure all timers are stopped

# Try to close FOQUS
timers["msg_no"].start(1000)
MainWin.close()
timerWait("msg_no")
print("Exited Code: UQ Polynomial")
