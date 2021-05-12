###############################################################################
# FOQUS Copyright (c) 2012 - 2021, by the software owners: Oak Ridge Institute
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
#
###############################################################################
from PyQt5 import QtCore, QtWidgets

test_name = "Basic UI"
exit_code = 2 # didn't finish tests, code will get set to 0 if tests finish
MAX_RUN_TIME = 50000 # Maximum time to let script run in ms.
timers = {} # mainly put all timers in a dic so I can easily stop them all

_log = logging.getLogger("foqus.testing")
_log.info("Running Test Script: {}".format(test_name))

##
## This part is test boilerplate, should consider creating a test module for
##   this stuff
##

def go(sleep=0.25, MainWin=MainWin, stopFlag=MainWin.helpDock.stop):
    """Process gui events
    Since this script is running holds up the GUI main loop, this function
    processes GUI events and checks if the stop button has been pressed. It also
    pauses for sleep seconds to let things happen.
    """
    MainWin.app.processEvents()
    time.sleep(sleep)
    return not stopFlag # Return true is stop flag is set

def getButton(w, label):
    """Get a buttom in window w labeled label, this could probably be better"""
    if isinstance(label, str):
        try:
            blist = w.buttons()
            for b in blist:
                if b.text().replace("&", "") == label:
                    return b
        except:
            pass
        try:
            blist = w.buttonBox.buttons()
            for b in blist:
                if b.text().replace("&", "") == label:
                    return b
        except:
            pass
    else:
        return label
    return None

def click_dialog(button_str, class_str, MainWin=MainWin):
    global getButton
    w = MainWin.app.activeWindow()
    if class_str in str(type(w)):
        try:
            getButton(w, button_str).click()
        except:
            _log.error("Didn't find expected button {} in dialog {}".format(
                button_str, class_str))
            return 6
    else:
        _log.error("Didn't find expected dialog {}".format(class_str))
        return 3
    return 0

def addTimer(name, cb, MainWin=MainWin):
    """Add a timer to do something.  Timers are needed because some things like
    a modal dialog box will hold up executaion on the main UI thread, so a timer
    can be used to do something while execution of this script is held up.

    Args:
        name: string name of timer
        cb: timer call back function (timer should stop itself once it's done)
    """
    global timers
    timers[name] = QtCore.QTimer(MainWin)
    timers[name].timeout.connect(cb)

def timersStop():
    """Stop all timers"""
    global timers
    for key, t in timers.items():
        t.stop()

def timerWait(timer, sleep=0.25, n=40):
    """Wait sleep*n seconds for timer to finish its job."""
    global exit_code, timers, go
    for i in range(n):
        if not go(sleep=sleep):
            timers[timer].stop()
            return False
        if not timers[timer].isActive():
            if exit_code == 3:
                return False
            else:
                return True
    timers[timer].stop() #Timer never did it's thing so just shut it down
    _log.error("timer {} didn't stop in alloted time\n".format(timer))
    return False #return False to stop script.  Something is wrong

##
## End of test boilerplate
##

##
## Timer callbacks, these are a way to handle dialog boxes that: 1) don't appear
## right away and 2) would hold up execution without the timer
##

def msg_okay(MainWin=MainWin):
    """Click OK when a msgbox pops up, stops timer once a msgbox pops up. """
    global timers, exit_code, click_dialog
    timers['msg_okay'].stop()
    exit_code = click_dialog("OK", "QMessageBox")

def msg_no(MainWin=MainWin):
    """Click No when a msgbox pops up, stops timer once a msgbox pops up"""
    global timers, exit_code, click_dialog
    timers['msg_no'].stop()
    exit_code = click_dialog("No", "QMessageBox")

def add_UQ_cancel(MainWin=MainWin):
    """Cancel adding a UQ ensemble, stops timer once the window comes up"""
    global timers, exit_code, click_dialog
    timers['add_UQ_cancel'].stop()
    exit_code = click_dialog("Cancel", "updateUQModelDialog")

def add_UQ_okay(MainWin=MainWin):
    """Press OK in adding a UQ ensemble, stops timer once the window comes up"""
    global timers, exit_code, click_dialog
    timers['add_UQ_okay'].stop()
    exit_code = click_dialog("OK", "updateUQModelDialog")

def uq_sampling_scheme(MainWin=MainWin):
    """Setup up an enseble sampling scheme, stops timer once window comes up"""
    global timers, exit_code, getButton, go
    w = MainWin.app.activeWindow()
    if 'SimSetup' in str(type(w)):
        timers['uq_sampling_scheme'].stop()
        w.samplingTabs.setCurrentIndex(1)
        items = w.schemesList.findItems('Monte Carlo', QtCore.Qt.MatchExactly)
        w.schemesList.setCurrentItem(items[0])
        w.numSamplesBox.setValue(10)
        w.generateSamplesButton.click()
        if not go(sleep=4): return #wait long enough for samples to generate
        w.doneButton.click()
    else: # Expected Window not there.
        timers['uq_sampling_scheme'].stop()
        exit_code = 3 # dialog box didn't appear

def time_out():
    global _log
    _log.error("Test script took to long exiting")
    _log.info("exit_code: {}".format(exit_code))
    sys.exit(5)

##
## End timer callbacks
##

# make the timers that will be needed just start and stop as needed
# need to make sure that when this script exits all timers are stopped
# or some crazy stuff may happen untill you exit FOQUS.
addTimer('time_out', time_out) #stop script if too long
addTimer('msg_okay', msg_okay) # click OK on mgsbox
addTimer('msg_no', msg_no) # click No on msgbox
addTimer('add_UQ_cancel', add_UQ_cancel) # click cancel on uq ensemble dialog
addTimer('add_UQ_okay', add_UQ_okay) # click okay on uq ensemble dialog
addTimer('uq_sampling_scheme', uq_sampling_scheme) # do sampling scheme dialog

# Set the max run time, after MAX_RUN_TIME the time_out timer will call
# sys.exit(), which hopefully will shut everything down if something went wrong
timers['time_out'].start(MAX_RUN_TIME)

try: # Catch any exception and stop all timers before finishing up
    while(1): # Loop and break as convenient way to jump to end

        # 1) Test flippling tabs
        MainWin.uqSetupAction.trigger()
        if not go(): break
        MainWin.fsEditAction.trigger()
        if not go(): break
        MainWin.ouuSetupAction.trigger()
        if not go(): break
        MainWin.homeAction.trigger()
        if not go(): break
        _log.info('SUCCESS: Test01: Flipping tabs test')

        # 2) Make a flowsheet
        MainWin.dashFrame.sessionNameEdit.setText("Example GUI test")
        if not go(): break
        MainWin.fsEditAction.trigger()
        if not go(): break
        MainWin.addNodeAction.trigger()
        if not go(): break
        MainWin.flowsheetEditor.sc.mousePressEvent(
            None, dbg_x=10, dbg_y=10, dbg_name="Test")
        if not go(): break
        MainWin.toggleNodeEditorAction.trigger()
        if not go(): break
        MainWin.nodeDock.addInput("x1")
        MainWin.nodeDock.addInput("x2")
        MainWin.nodeDock.inputVarTable.item(0, 5).setText("-10") # min x1
        MainWin.nodeDock.inputVarTable.item(0, 6).setText("10") # max x2
        MainWin.nodeDock.inputVarTable.item(1, 5).setText("-10") # min x2
        MainWin.nodeDock.inputVarTable.item(1, 6).setText("10") # max x2
        MainWin.nodeDock.inputVarTable.item(0, 4).setText("5") # deafult x1
        MainWin.nodeDock.inputVarTable.item(1, 4).setText("2") # default x2
        MainWin.nodeDock.inputVarTable.item(0, 1).setText("5") # value x1
        MainWin.nodeDock.inputVarTable.item(1, 1).setText("2") # value x2
        MainWin.nodeDock.toolBox.setCurrentIndex(1)
        MainWin.nodeDock.addOutput("z")
        MainWin.nodeDock.tabWidget.setCurrentIndex(2)
        MainWin.nodeDock.pyCode.setPlainText("f.z = x.x1 + x.x2**2")
        MainWin.nodeDock.tabWidget.setCurrentIndex(0)
        if not go(): break
        _log.info('SUCCESS: Test02: Create flowsheet')

        # 3) Run a flowsheet
        timers['msg_okay'].start(1500) # timer to push ok on a msgbox if up
        MainWin.runAction.trigger() #run flowsheet
        while MainWin.singleRun.is_alive():
            if not go():
                MainWin.singleRun.terminate()
                break
        if not timerWait('msg_okay'): break
        assert abs(self.flowsheet.output["Test"]["z"].value - 9.0) < 1e-8
        assert self.flowsheet.errorStat==0
        _log.info('SUCCESS: Test03: Flowsheet run')

        # 4) Start to add a UQ enseble, but cancel it.
        MainWin.uqSetupAction.trigger()
        if not go(): break
        # Start add then cancel
        timers['add_UQ_cancel'].start(500)
        MainWin.uqSetupFrame.addSimulationButton.click()
        if not timerWait('add_UQ_cancel'): break
        _log.info('SUCCESS: Test04: UQ Esemble add cancel')

        # 5) Add a UQ Ensemble
        # Comment out UQ ensemble test for now need to make sure we can get
        # it set up on the test platform.
        """
        # This time add for real
        timers['add_UQ_okay'].start(1000)
        timers['uq_sampling_scheme'].start(500)
        MainWin.uqSetupFrame.addSimulationButton.click()
        if not timerWait('add_UQ_okay'): break
        if not timerWait('uq_sampling_scheme'): break
        _log.info("SUCCESS: Test04: UQ Esemble add")
        # Run UQ ensemble
        MainWin.uqSetupFrame.simulationTable.cellWidget(0,3).click()
        timers['msg_okay'].start(500) # press okay on ensemble done msgbox
        while MainWin.uqSetupFrame.gThread.isAlive(): # while is running
            if not go():
                MainWin.uqSetupFrame.gThread.terminate()
                break
        if not timerWait('msg_okay'): break
        _log.info("SUCCESS: Test05: UQ Esemble run")
        """

        # All tests completed without error set exit_code 0 and end
        exit_code = 0
        break
except:
    exit_code = 1
    _log.exception("Exception stopping test script")

timersStop() #make sure all timers are stopped
_log.info("exit_code: {}".format(exit_code))
#Try to close FOQUS
sys.exit(exit_code)
