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
from PyQt5 import QtCore
import matplotlib.pyplot as plt
from foqus_lib.framework.uq.Common import Common

global TIME_STEP, HAVE_TEXT
MAX_RUN_TIME = 5000000  # Maximum time to let script run in ms.
TIME_STEP = 1
HAVE_TEXT = 1
testOutFile = "ui_test_out.txt"
with open(testOutFile, "w") as f:
    f.write("")
timers = {}

if HAVE_TEXT == 1:
    global dialog, textedit
    dialog = Common.textDialog(MainWin)
    textedit = dialog.textedit

global go


def go(MainWin=MainWin):
    """
    Process gui events so that gui can still function(ish) while
    script is running also add delay between calls to GUI stuff to
    make the execution fun to watch.  Also checks the stop flag and
    returns True keep going or False to stop.
    """
    MainWin.app.processEvents()
    time.sleep(0.25)
    return not MainWin.helpDock.stop


def getButton(w, label):
    blist = w.buttons()
    # print [b.text() for b in blist]
    for b in blist:
        if b.text().replace("&", "") == label:
            return b
    return None


def addEnsembelCancel(self=self, MainWin=MainWin, getButton=getButton):
    w = MainWin.app.activeWindow()
    if "updateUQModelDialog" in str(type(w)):
        b = getButton(w.buttonBox, "Cancel")
        b.click()


def addEnsembelOkay(self=self, MainWin=MainWin, getButton=getButton):
    w = MainWin.app.activeWindow()
    if "updateUQModelDialog" in str(type(w)):
        b = getButton(w.buttonBox, "OK")
        b.click()


def uqSamplingScheme(self=self, MainWin=MainWin, getButton=getButton, timers=timers):
    TIME_STEP = 1
    w = MainWin.app.activeWindow()
    if "SimSetup" in str(type(w)):
        timers["uq_sampling_scheme"].stop()
        w.samplingTabs.setCurrentIndex(1)
        items = w.schemesList.findItems("Quasi Monte Carlo", QtCore.Qt.MatchExactly)
        w.schemesList.setCurrentItem(items[0])
        w.numSamplesBox.setValue(1000)
        w.generateSamplesButton.click()
        time.sleep(TIME_STEP)  # need to wait long enough for samples to generate
        w.doneButton.click()


def rsAnalyze(self=self, MainWin=MainWin, getButton=getButton, timers=timers):
    w = MainWin.app.activeWindow()
    if "AnalysisDialog" in str(type(w)):
        timers["rs_analyze"].stop()
        ### set response surface mode
        # w.setWizardRSAnalysisMode(True)
        ### need to check the response surface button
        # w.wizardRS_radio.setChecked(True)
        if HAVE_TEXT == 1:
            textedit.insertPlainText("      Performing response surface validation\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                w.close()
                return
            time.sleep(TIME_STEP)
        ### set response surface mode
        w.wizardRS_radio.setChecked(True)
        ### use RBF
        w.wizardRS_combo1.setCurrentIndex(5)
        ### validate rs
        w.wizardRSValidate_button.click()
        time.sleep(TIME_STEP)

        ### RS Viz
        if HAVE_TEXT == 1:
            textedit.insertPlainText("      Generating plots for response surfaces\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                w.close()
                return
            time.sleep(TIME_STEP)
        ### visualization (2D, inputs 1 and 3)
        w.wizardViz_combo1.setCurrentIndex(1)
        w.wizardViz_combo2.setCurrentIndex(3)
        w.wizardViz_button.click()
        time.sleep(TIME_STEP)
        ### visualization (1D, input 2)
        w.wizardViz_combo1.setCurrentIndex(2)
        w.wizardViz_combo2.setCurrentIndex(0)
        w.wizardViz_button.click()
        time.sleep(TIME_STEP)

        ### UA
        if HAVE_TEXT == 1:
            textedit.insertPlainText("      Performing uncertainty analysis\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                w.close()
                return
            time.sleep(TIME_STEP)
        w.wizardAnalyze_button.click()
        time.sleep(TIME_STEP)

        ### SA
        if HAVE_TEXT == 1:
            textedit.insertPlainText("      Performing sensitivity analysis\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                w.close()
                return
            time.sleep(TIME_STEP)
        ### sensitivity analysis (first order)
        w.wizardAnalyze_combo1.setCurrentIndex(1)
        w.wizardAnalyze_button.click()
        time.sleep(TIME_STEP)
        ### sensitivity analysis (second order)
        w.wizardAnalyze_combo2.setCurrentIndex(1)
        w.wizardAnalyze_button.click()
        time.sleep(TIME_STEP)
        ### sensitivity analysis (total order)
        w.wizardAnalyze_combo2.setCurrentIndex(2)
        w.wizardAnalyze_button.click()
        time.sleep(TIME_STEP)

        w.close()


def addTimer(name, cb, MainWin=MainWin, timers=timers):
    """
    Using timers to push buttons on popups and modal dialogs and
    other things were I need an easy way to make things happen from
    a separate thread.  Usually where something is blocking the main
    GUI loop.

    name: string name of timer
    cd is the timer call back function
    """
    timers[name] = QtCore.QTimer(MainWin)
    timers[name].timeout.connect(cb)


def timersStop(timers=timers):
    """
    Call stop for all timers to make sure they all stop
    """
    for key, t in timers.items():
        t.stop()


# make the timers that will be needed just start and stop as needed
# need to make sure that when this script exits all timers are stopped
# or some crazy stuff may happen until you exit FOQUS.
addTimer("time_out", MainWin.helpDock.setStopTrue)  # stop script for taking too long
addTimer("msg_okay", MainWin.helpDock.msgBoxOK)  # click okay on a pop up message box
addTimer("msg_no", MainWin.helpDock.msgBoxNo)  # Click no on a popup message box
addTimer("addUQ_cancel", addEnsembelCancel)  # click cancel on add uq ensemble dialog
addTimer("addUQ_okay", addEnsembelOkay)  # click cancel on add uq ensemble dialog
addTimer("uq_sampling_scheme", uqSamplingScheme)
addTimer("rs_analyze", rsAnalyze)
# Start timer to stop script for running too long
# This won't work it execution of the script is blocked.
timers["time_out"].start(MAX_RUN_TIME)

try:
    # raise(Exception("Test exception handling"))
    while 1:

        ### This is the dialog I created for this type of stuff
        if HAVE_TEXT == 1:
            dialog = Common.textDialog(MainWin)
            dialog.show()
            textedit = dialog.textedit
            textedit.insertPlainText(
                "First move this screen to your upper right hand corner\n"
            )
            textedit.ensureCursorVisible()  # Scroll the window to the bottom

        ### Go to main window home
        if HAVE_TEXT == 1:
            textedit.insertPlainText("Entering the home screen\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.homeAction.trigger()
        if not go():
            break
        time.sleep(TIME_STEP)

        ### Enter session name
        if HAVE_TEXT == 1:
            textedit.insertPlainText("Typing in the session name = UQ GUI test\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.dashFrame.sessionNameEdit.setText("UQ GUI test - use flowsheet")
        if not go():
            break
        time.sleep(TIME_STEP)

        ###===========================================
        ### Make a flowsheet
        ###===========================================
        ### Click flowsheet icon
        if HAVE_TEXT == 1:
            textedit.insertPlainText("Clicking the Flowsheet icon (at the top)\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.fsEditAction.trigger()
        time.sleep(TIME_STEP)
        if not go():
            break

        ### Click add node button
        if HAVE_TEXT == 1:
            textedit.insertPlainText(
                "   Clicking the Add Node button (the plus sign on the left panel)\n"
            )
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.addNodeAction.trigger()
        time.sleep(TIME_STEP)
        if not go():
            break

        ### Click at the open space which prompts a name, enter 'Test'
        ### Click add node button
        if HAVE_TEXT == 1:
            textedit.insertPlainText("      Entering the name of the node = Test\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.flowsheetEditor.sc.mousePressEvent(
            None, dbg_x=10, dbg_y=10, dbg_name="Test"
        )
        time.sleep(TIME_STEP)
        if not go():
            break

        ### toggle the editor button
        if HAVE_TEXT == 1:
            textedit.insertPlainText(
                "   Toggling the node edit button (the pencil on left panel)\n"
            )
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.toggleNodeEditorAction.trigger()
        if not go():
            break
        time.sleep(TIME_STEP)

        ### click add input (the green + symbol) and enter x1
        if HAVE_TEXT == 1:
            textedit.insertPlainText("      Clicking the Input Variables section\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.nodeDock.toolBox.setCurrentIndex(0)
        if not go():
            break
        time.sleep(TIME_STEP)

        if HAVE_TEXT == 1:
            textedit.insertPlainText(
                "         Adding 3 input variables: x1, x2 and x3\n"
            )
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.nodeDock.addInput("x1")
        time.sleep(TIME_STEP)
        if not go():
            break

        ### click add input (the green + symbol) and enter x2
        MainWin.nodeDock.addInput("x2")
        time.sleep(TIME_STEP)
        if not go():
            break

        ### click add input (the green + symbol) and enter x3
        MainWin.nodeDock.addInput("x3")
        time.sleep(TIME_STEP)
        if not go():
            break

        ### set X1 min to be -pi/2
        if HAVE_TEXT == 1:
            textedit.insertPlainText("         Changing the input bounds\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
        if not go():
            break
        time.sleep(TIME_STEP)

        # MainWin.nodeDock.inputVarTable.item(0, 4).setText("-1.5708")
        MainWin.nodeDock.inputVarTable.item(0, 5).setText("-2")
        if not go():
            break
        time.sleep(TIME_STEP)
        ### set X1 max to be pi/2
        # MainWin.nodeDock.inputVarTable.item(0, 5).setText("1.5708")
        MainWin.nodeDock.inputVarTable.item(0, 6).setText("2")
        if not go():
            break
        time.sleep(TIME_STEP)
        ### set X2 min to be -pi/2
        # MainWin.nodeDock.inputVarTable.item(1, 5).setText("-1.5708")
        MainWin.nodeDock.inputVarTable.item(1, 5).setText("-2")
        if not go():
            break
        time.sleep(TIME_STEP)
        ### set X2 max to be pi/2
        # MainWin.nodeDock.inputVarTable.item(1, 6).setText("1.5708")
        MainWin.nodeDock.inputVarTable.item(1, 6).setText("2")
        if not go():
            break
        time.sleep(TIME_STEP)
        ### set X3 min to be -pi/2
        # MainWin.nodeDock.inputVarTable.item(2, 5).setText("-1.5708")
        MainWin.nodeDock.inputVarTable.item(2, 5).setText("-2")
        if not go():
            break
        time.sleep(TIME_STEP)
        ### set X3 max to be pi/2
        # MainWin.nodeDock.inputVarTable.item(2, 6).setText("1.5708")
        MainWin.nodeDock.inputVarTable.item(2, 6).setText("2")
        if not go():
            break
        time.sleep(TIME_STEP)
        ### select 'Output Variables'
        if HAVE_TEXT == 1:
            textedit.insertPlainText("      Clicking the Output Variable section\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.nodeDock.toolBox.setCurrentIndex(1)
        if not go():
            break
        time.sleep(TIME_STEP)

        ### setting 'Output Variable' name
        if HAVE_TEXT == 1:
            textedit.insertPlainText("         Adding the model output = y\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.nodeDock.addOutput("y")
        if not go():
            break
        time.sleep(TIME_STEP)

        ### select 'Node Script'
        if HAVE_TEXT == 1:
            textedit.insertPlainText("   Clicking the node script tab\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.nodeDock.tabWidget.setCurrentIndex(2)
        if not go():
            break
        time.sleep(TIME_STEP)

        ### enter the function
        if HAVE_TEXT == 1:
            textedit.insertPlainText("      Adding the simulation model function\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.nodeDock.pyCode.setPlainText(
            "f['y'] = math.sin(x['x1']) + 7 * math.sin(x['x2']) * math.sin(x['x2']) + 0.1 * x['x3'] * x['x3'] * x['x3'] * x['x3'] * math.sin(x['x1'])\ntime.sleep(0.02)"
        )
        if not go():
            break
        time.sleep(TIME_STEP)

        ### Go to UQ module (click the top icon)
        if HAVE_TEXT == 1:
            textedit.insertPlainText("Clicking the Uncertainty icon (at the top)\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.uqSetupAction.trigger()
        if not go():
            break
        time.sleep(TIME_STEP)

        ### get ready to respond with a 'ok' for uqSetupFrame add simulation
        timers["addUQ_okay"].start(1000)
        ### get ready to respond with selecting MC and sample size 10
        ### the sampling window will be activated after ok to 'Add New'
        timers["uq_sampling_scheme"].start(1000)

        ### add simulation in UQ module ('Add New')
        ### again, this trigger selection of flowsheet and sampling scheme/size
        ##  and finally click 'generate samples'
        if HAVE_TEXT == 1:
            textedit.insertPlainText(
                "   Clicking the Add New button, then select sampling and size\n"
            )
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.uqSetupFrame.addSimulationButton.click()
        if not go():
            break
        time.sleep(TIME_STEP)

        ### launch jobs in UQ module
        if HAVE_TEXT == 1:
            textedit.insertPlainText("   Launching jobs\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        timers["addUQ_okay"].stop()
        w = MainWin.uqSetupFrame.simulationTable.cellWidget(0, 3)
        w.click()
        if not go():
            break
        time.sleep(TIME_STEP)

        ### press 'OK' on msg box that appears when ensemble has been run
        timers["msg_okay"].start(1000)
        while MainWin.uqSetupFrame.gThread.isAlive():
            if not go():
                MainWin.uqSetupFrame.gThread.terminate()
                break
        for i in range(4):  # wait a bit
            if not go():
                break
            time.sleep(1)
        if not go():
            break
        timers["msg_okay"].stop()
        if not go():
            break
        time.sleep(TIME_STEP)

        ### go to analyze screen
        if HAVE_TEXT == 1:
            textedit.insertPlainText("   Clicking the Analysis button for ensemble 1\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        timers["rs_analyze"].start(1000)
        timers["msg_okay"].start(1000)
        w = MainWin.uqSetupFrame.simulationTable.cellWidget(0, 4)
        w.click()
        timers["rs_analyze"].stop()
        timers["msg_okay"].stop()
        if not go():
            break
        time.sleep(TIME_STEP)

        ### Wait
        if HAVE_TEXT == 1:
            textedit.insertPlainText("This test will terminate in 30 seconds\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
        for ii in range(5000):
            if not go():
                break
            time.sleep(1)

        ### Close FOQUS
        timers["msg_no"].start(1000)
        if HAVE_TEXT == 1:
            dialog.close()
        MainWin.close()
        timers["msg_no"].stop()
        break

except Exception as e:
    # if there is any exception make sure the timers are stopped
    # before reraising it
    print("Exception stopping script")
    timersStop()
    with open(testOutFile, "a") as f:
        f.write("Exception: {0}\n".format(e))
    raise (e)
timersStop()  # make sure all timers are stopped
