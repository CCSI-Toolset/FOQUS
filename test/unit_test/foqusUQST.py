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
from PySide import QtCore
from PySide.QtGui import *
from PySide.QtCore import *

import matplotlib.pyplot as plt
from foqus_lib.framework.uq.Common import Common

MAX_RUN_TIME = 5000000  # Maximum time to let script run in ms.
HAVE_TEXT = 0
TIME_STEP = 2
testOutFile = "ui_test_out.txt"
with open(testOutFile, "w") as f:
    f.write("")
timers = {}


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


def rsInference(self=self, MainWin=MainWin, getButton=getButton, timers=timers):
    TIME_STEP = 2
    w = MainWin.app.activeWindow()
    if "InferenceDialog" in str(type(w)):
        timers["rs_inference"].stop()
        time.sleep(TIME_STEP)
        ### check to select output 1
        c = w.output_table.cellWidget(0, 0)
        c.setChecked(True)
        ### select MARS as the response surface
        c = w.output_table.cellWidget(0, w.outputCol_index["rs1"])
        c.setCurrentIndex(1)
        MainWin.app.processEvents()
        time.sleep(TIME_STEP)
        ### select the first 3 inputs as design parameters
        c = w.inputPrior_table
        for ii in range(3):
            p = c.cellWidget(ii, c.col_index["type"])
            p.setCurrentIndex(2)
            MainWin.app.processEvents()
            time.sleep(TIME_STEP)
        ### load the experimental data file
        # fname = '/g/g0/chtong/FOQUS/FOQUS/examples/UQ/test_suite/'
        fname = "../examples/UQ/test_suite/"
        fname = fname + "Phoenix/SurfaceTension/expdataST"
        XN, XD, YD = LocalExecutionModule.readMCMCFile(fname)
        nExps = 72
        w.numExperiments_spin.setValue(nExps)
        data = np.hstack([XD, YD])
        for r in xrange(nExps):
            # w.numExperiments_spin.setValue(r+1)
            w.obs_table.verticalScrollBar().setValue(max([r - 2, 0]))
            for c in xrange(data.shape[1]):
                item = w.obs_table.item(r, c)
                if item is None:
                    item = QtGui.QTableWidgetItem()
                    w.obs_table.setItem(r, c, item)
                item.setText("%g" % data[r, c])
            MainWin.app.processEvents()
        time.sleep(TIME_STEP)

        ##w.discrepancy_chkbox.setChecked(True)
        MainWin.app.processEvents()
        time.sleep(TIME_STEP)
        ### check box for saving posterior
        w.infSave_chkbox.setChecked(True)
        MainWin.app.processEvents()
        time.sleep(TIME_STEP)
        # fname = '/g/g0/chtong/FOQUS/FOQUS/examples/UQ/test_suite/'
        fname = "../examples/UQ/test_suite/"
        fname = fname + "Phoenix/SurfaceTension/STPostSample"
        w.infSave_edit.setText(fname)
        MainWin.app.processEvents()
        time.sleep(TIME_STEP)
        w.inf_button.click()


def rsAnalyze(self=self, MainWin=MainWin, getButton=getButton, timers=timers):
    TIME_STEP = 2
    w = MainWin.app.activeWindow()
    if "AnalysisDialog" in str(type(w)):
        timers["rs_analyze"].stop()
        ### switch to expert mode
        w.modeButton.click()
        MainWin.app.processEvents()
        timers["rs_inference"].start(1000)
        w.expertInfer_button.click()
        timers["rs_inference"].stop()
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
addTimer("rs_analyze", rsAnalyze)
addTimer("rs_inference", rsInference)
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
                "Do not move your mouse or type anything until the end\n"
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
            textedit.insertPlainText("Typing in the session name = Surface Tension \n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.dashFrame.sessionNameEdit.setText("Surface Tension inference")
        if not go():
            break
        time.sleep(TIME_STEP)

        ###===========================================
        ### Go to UQ module (click the top icon)
        ###===========================================
        if HAVE_TEXT == 1:
            textedit.insertPlainText("Clicking the Uncertainty icon (at the top)\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.uqSetupAction.trigger()
        if not go():
            break
        time.sleep(1)

        ### add simulation in UQ module ('Load File')
        if HAVE_TEXT == 1:
            textedit.insertPlainText(
                "   Clicking the load file button, enter file name\n"
            )
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)

        ###MainWin.uqSetupFrame.loadSimulationButton.click()
        # fname = '/g/g0/chtong/FOQUS/FOQUS/examples/UQ/test_suite/'
        fname = "../examples/UQ/test_suite/"
        fname = fname + "Phoenix/SurfaceTension/STSample.psuade"
        data = LocalExecutionModule.readSampleFromPsuadeFile(fname)
        data.setSession(MainWin.uqSetupFrame.dat)
        MainWin.uqSetupFrame.dat.uqSimList.append(data)
        if not go():
            break
        MainWin.uqSetupFrame.updateSimTable()
        if not go():
            break
        MainWin.uqSetupFrame.dataTabs.setEnabled(True)
        if not go():
            break
        time.sleep(TIME_STEP)

        ### go to analyze screen
        if HAVE_TEXT == 1:
            textedit.insertPlainText("   Clicking the Analysis button for Ensemble 1\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            textedit.insertPlainText("      which will then perform inference\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        timers["rs_analyze"].start(1000)
        w = MainWin.uqSetupFrame.simulationTable.cellWidget(0, 4)
        w.click()
        timers["rs_analyze"].stop()
        if not go():
            break

        ### Wait
        if HAVE_TEXT == 1:
            textedit.insertPlainText("This test will terminate in 30 seconds\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
        for ii in range(30):
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
