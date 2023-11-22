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
from foqus_lib.gui.uq.InputPriorTable import InputPriorTable

MAX_RUN_TIME = 5000000  # Maximum time to let script run in ms.
TIME_STEP = 2
HAVE_TEXT = 0
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
# Start timer to stop script for running too long
# This won't work it execution of the script is blocked.
timers["time_out"].start(MAX_RUN_TIME)

try:
    # raise(Exception("Test exception handling"))
    while 1:

        ### This is the dialog I created for this type of stuff
        if HAVE_TEXT == 1:
            dialog = Common.textDialog()
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
            textedit.insertPlainText("Typing in the session name = OUU GUI test\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.dashFrame.sessionNameEdit.setText("OUU GUI test")
        if not go():
            break
        time.sleep(TIME_STEP)

        ###===========================================
        ### Go to OUU module (click the top icon)
        ###===========================================
        if HAVE_TEXT == 1:
            textedit.insertPlainText("Clicking the OUU icon (at the top)\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.ouuSetupAction.trigger()
        if not go():
            break
        time.sleep(TIME_STEP)

        ### Enter model file name
        if HAVE_TEXT == 1:
            textedit.insertPlainText(
                "   Clicking the load model button, enter file name\n"
            )
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.ouuSetupFrame.modelFile_radio.setChecked(True)
        ###fname = '/g/g0/chtong/FOQUS/FOQUS/examples/OUU/test_suite/ouu_optdriver.in'
        fname = "../examples/OUU/test_suite/ouu_optdriver.in"
        MainWin.ouuSetupFrame.modelFile_edit.setText(fname)
        MainWin.ouuSetupFrame.model = LocalExecutionModule.readSampleFromPsuadeFile(
            fname
        )
        MainWin.ouuSetupFrame.model = MainWin.ouuSetupFrame.model.model
        if not go():
            break
        time.sleep(TIME_STEP)

        ### Load File
        if HAVE_TEXT == 1:
            textedit.insertPlainText("   Reading input file and load input table\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.ouuSetupFrame.input_table.init(
            MainWin.ouuSetupFrame.model, InputPriorTable.OUU
        )
        MainWin.ouuSetupFrame.setFixed_button.setEnabled(True)
        MainWin.ouuSetupFrame.setX1_button.setEnabled(True)
        MainWin.ouuSetupFrame.setX2_button.setEnabled(True)
        MainWin.ouuSetupFrame.setX3_button.setEnabled(True)
        MainWin.ouuSetupFrame.setX4_button.setEnabled(True)
        MainWin.ouuSetupFrame.initTabs()
        MainWin.ouuSetupFrame.setCounts()
        if not go():
            break
        time.sleep(TIME_STEP)

        ### Set Z1 inputs
        if HAVE_TEXT == 1:
            textedit.insertPlainText("   Configuring Z1 inputs\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        for ii in range(4):
            c = MainWin.ouuSetupFrame.input_table.cellWidget(ii, 0)
            c.setChecked(True)
        MainWin.ouuSetupFrame.setX1()
        for ii in range(4):
            c = MainWin.ouuSetupFrame.input_table.cellWidget(ii, 0)
            c.setChecked(False)
        if not go():
            break
        time.sleep(TIME_STEP)

        ### Set Z2 inputs
        if HAVE_TEXT == 1:
            textedit.insertPlainText("   Configuring Z2 inputs\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        for ii in range(4):
            MainWin.ouuSetupFrame.input_table.verticalScrollBar().setValue(ii + 2)
            MainWin.app.processEvents()
            c = MainWin.ouuSetupFrame.input_table.cellWidget(ii + 4, 0)
            c.setChecked(True)
        MainWin.ouuSetupFrame.setX2()
        for ii in range(4):
            c = MainWin.ouuSetupFrame.input_table.cellWidget(ii + 4, 0)
            c.setChecked(False)
        if not go():
            break
        time.sleep(TIME_STEP)

        ### Set Z4 inputs
        if HAVE_TEXT == 1:
            textedit.insertPlainText("   Configuring Z4 inputs\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        for ii in range(4):
            MainWin.ouuSetupFrame.input_table.verticalScrollBar().setValue(ii + 6)
            MainWin.app.processEvents()
            c = MainWin.ouuSetupFrame.input_table.cellWidget(ii + 8, 0)
            c.setChecked(True)
        MainWin.ouuSetupFrame.setX4()
        if not go():
            break
        time.sleep(TIME_STEP)

        ### Set second level solver
        if HAVE_TEXT == 1:
            textedit.insertPlainText("   Setting second level solver\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.ouuSetupFrame.secondarySolver_combo.setCurrentIndex(1)
        if not go():
            break
        time.sleep(TIME_STEP)

        ### Go to UQ setup tab
        if HAVE_TEXT == 1:
            textedit.insertPlainText("   Going into UQ setup tab\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.ouuSetupFrame.tabs.setCurrentIndex(1)
        if not go():
            break
        time.sleep(TIME_STEP)

        ### Set up Z4 sample
        if HAVE_TEXT == 1:
            textedit.insertPlainText("   Setting Z4 sample\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        # MainWin.ouuSetupFrame.x4SampleScheme_label.setEnabled(False)
        # MainWin.ouuSetupFrame.x4SampleScheme_combo.setEnabled(False)
        # MainWin.ouuSetupFrame.x4SampleSize_label.setEnabled(False)
        # MainWin.ouuSetupFrame.x4SampleSize_spin.setEnabled(False)
        MainWin.ouuSetupFrame.z4NewSample_radio.setChecked(False)
        # MainWin.ouuSetupFrame.x4File_edit.setEnabled(True)
        MainWin.ouuSetupFrame.z4LoadSample_radio.setChecked(True)
        MainWin.ouuSetupFrame.x4FileBrowse_button.setEnabled(True)
        # MainWin.ouuSetupFrame.x4FileBrowse_button.setChecked(True)
        # fname = '/g/g0/chtong/FOQUS/FOQUS/examples/OUU/test_suite/x4sample.txt'
        fname = "../examples/OUU/test_suite/x4sample.smp"
        MainWin.ouuSetupFrame.x4File_edit.setText(fname)
        if not go():
            break
        time.sleep(TIME_STEP)

        ### Go to Run tab
        if HAVE_TEXT == 1:
            textedit.insertPlainText("   Going into launch tab\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        MainWin.ouuSetupFrame.tabs.setCurrentIndex(2)
        if not go():
            break
        time.sleep(TIME_STEP)

        ### optimize
        if HAVE_TEXT == 1:
            textedit.insertPlainText("   Optimizing\n")
            textedit.ensureCursorVisible()  # Scroll the window to the bottom
            if not go():
                break
            time.sleep(TIME_STEP)
        timers["msg_okay"].start(1000)
        MainWin.ouuSetupFrame.run_button.click()
        timers["msg_okay"].stop()

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
