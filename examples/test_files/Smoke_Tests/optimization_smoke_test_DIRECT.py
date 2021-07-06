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
"""
This test focuses on the input importance portion of the UQ
"""
MAX_RUN_TIME = 50000 # Maximum time to let script run in ms.
#testOutFile = 'AutoErrLog_optimization_smoke_test_COBYLA.txt'
#with open(testOutFile, 'w') as f: # file to write test results to
#    f.write('Test Results\n')
timers = {} # mainly put all timers in a dic so I can easily stop them all

def go(sleep=0.25, MainWin=MainWin):
    """Process gui events
    Since this script is running holds up the GUI main loop, this function
    processes GUI events and checks if the stop button has been pressed. It also
    pauses for sleep seconds to let things happen.
    """
    MainWin.app.processEvents()
    time.sleep(sleep)
    return not MainWin.helpDock.stop # Return true is stop flag is set

def getButton(w, label):
    """Get a buttom in window w labeled label"""
    blist = w.buttons()
    for b in blist:
        if b.text().replace("&", "") == label:
            return b
    return None

global errorCount
global errorTitle
global errorFile
errorFile = "AutoErrLog_optimization_smoke_test_DIRECT.txt"
errorCount = 0

def Error_okay(MainWin=MainWin, getButton=getButton, timers=timers):
    """Close the Error dialog if Error appears in the title, stops timer once the window comes up"""
    w = MainWin.app.activeWindow()
    try:
        if 'Error' in str(w.windowTitle()):
            w.close()
            global errorCount
            global errorTitle
            global errorFile
#            timers['Error_okay'].stop()
            if (errorCount == 0):
                errFile = open(errorFile,"w")
            else:
                errFile = open(errorFile,"a")
            errorCount += 1
            errFile.write("############################################################################\n")
            errFile.write("Error Number: " + str(errorCount) + "\n")
            errFile.write("Error Title: " + errorTitle + "\n")
            try:
                errFile.write("Error Text: " + w.text() + "\n")
            except:
                None
            try:
                errFile.write("Error Detailed Text: \n" + w.detailedText() + "\n")
            except:
                None
            try:
                errFile.write("Error Informative Text: \n" + w.informativeText() + "\n")
            except:
                None
            errFile.close()
    except:
        None

def Error_okay_text(MainWin=MainWin, getButton=getButton, timers=timers):
    """Close the Error dialog if a, stops timer once the window comes up"""
    w = MainWin.app.activeWindow()
    try:
        if 'FOQUS UQ developers' in str(w.text()):
            getButton(w, 'OK').click()
            global errorCount
            global errorTitle
            global errorFile
#            timers['Error_okay_text'].stop()
            if (errorCount == 0):
                errFile = open(errorFile,"w")
            else:
                errFile = open(errorFile,"a")
            errorCount += 1
            errFile.write("############################################################################\n")
            errFile.write("Error Number: " + str(errorCount) + "\n")
            errFile.write("Error Title: \n" + errorTitle + "\n")
            try:
                errFile.write("Error Text: \n" + w.text() + "\n")
            except:
                None
            try:
                errFile.write("Error Detailed Text: \n" + w.detailedText() + "\n")
            except:
                None
            try:
                errFile.write("Error Informative Text: \n" + w.informativeText() + "\n")
            except:
                None
            errFile.close()
    except AttributeError:
        None


def msg_okay(MainWin=MainWin, getButton=getButton, timers=timers):
    """Click OK when a msgbox pops up, stops timer once a msgbox pops up"""
    w = MainWin.app.activeWindow()
    if isinstance(w, QtWidgets.QMessageBox):
        getButton(w, 'OK').click()
        timers['msg_okay'].stop()

def msg_no(MainWin=MainWin, getButton=getButton, timers=timers):
    """Click No when a msgbox pops up, stops timer once a msgbox pops up"""
    w = MainWin.app.activeWindow()
    if isinstance(w, QtWidgets.QMessageBox):
        getButton(w, 'No').click()
        timers['msg_no'].stop()

def start_opt_scheme(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup up an enseble sampling scheme, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    if 'optMonitor' in str(type(w)):
        timers['start_opt_scheme'].stop()
        w.startButton.click()


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

def timerWait(timer, sleep=0.25, n=40, go=go, timers=timers, tf=errorFile):
    """Wait sleep*n seconds for timer to finish its job."""
    for i in range(n):
        if not go(sleep=sleep): return False
        if not timers[timer].isActive(): return True
    timers[timer].stop() #Timer never did it's thing so just shut it down
    with open(tf, 'a') as f: # file to write test results to
        f.write("ERROR: timer {} didn't stop in alloted time\n".format(timer))
    return False #return False to stop script.  Something is wrong

# make the timers that will be needed just start and stop as needed
# need to make sure that when this script exits all timers are stopped
# or some crazy stuff may happen untill you exit FOQUS.
addTimer('time_out', MainWin.helpDock.setStopTrue) #stop script if too long
addTimer('msg_okay', msg_okay) # click OK on mgsbox
addTimer('msg_no', msg_no) # click No on msgbox
addTimer('start_opt_scheme', start_opt_scheme) # do sampling scheme dialog

timers['time_out'].start(MAX_RUN_TIME) # start max script time timer

try: # Catch any exception and stop all timers before finishing up
    while(1): # Loop and break and break as convenient way to jump to end
        # Rosenbrock Test for UQ
        MainWin.homeAction.trigger()
        if not go(): break
        # Enter some information
        MainWin.dashFrame.sessionNameEdit.setText("Optimization Test")
        if not go(): break
        MainWin.dashFrame.tabWidget.setCurrentIndex(1)
        if not go(): break
        MainWin.dashFrame.setSessionDescription("Rosenbrock Optimization Description Text")
        if not go(): break
        # Make a flowsheet
        MainWin.fsEditAction.trigger()
        if not go(): break
        MainWin.addNodeAction.trigger()
        if not go(): break
        MainWin.flowsheetEditor.sc.mousePressEvent(
            None, dbg_x=10, dbg_y=10, dbg_name="Rosenbrock")
        if not go(): break
        MainWin.toggleNodeEditorAction.trigger()
        if not go(): break
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
        MainWin.nodeDock.pyCode.setPlainText("f['f'] = 0 \
                                             \nf['f'] += (1-x['x1'])**2 + 100.0*(x['x2']-x['x1']**2)**2 \
                                             \nf['f'] += (1-x['x2'])**2 + 100.0*(x['x3']-x['x2']**2)**2 \
                                             \nf['f'] += (1-x['x3'])**2 + 100.0*(x['x4']-x['x3']**2)**2 \
                                             \nf['f'] += (1-x['x4'])**2 + 100.0*(x['x5']-x['x4']**2)**2 \
                                             \nf['f'] += (1-x['x5'])**2 + 100.0*(x['x6']-x['x5']**2)**2")
        MainWin.nodeDock.tabWidget.setCurrentIndex(0)
        if not go(): break
        # Before running start up a timer to close completed run msgbox
        timers['msg_okay'].start(500) # timer to push ok on a msgbox if up
        MainWin.runAction.trigger() #run flowsheet
        while MainWin.singleRun.is_alive():
            if not go():
                MainWin.singleRun.terminate()
                break
        if not timerWait('msg_okay'): break
        # Switch to the Optimization window
        MainWin.optSetupAction.trigger()
        # Set up the variables
        MainWin.optSetupFrame.varForm.cellWidget(0,1).setCurrentIndex(1)
        MainWin.optSetupFrame.varForm.cellWidget(1,1).setCurrentIndex(1)
        MainWin.optSetupFrame.varForm.cellWidget(3,1).setCurrentIndex(1)
        MainWin.optSetupFrame.varForm.cellWidget(4,1).setCurrentIndex(1)
        MainWin.optSetupFrame.varForm.cellWidget(5,1).setCurrentIndex(1)
#        # Set the Scales
#        MainWin.optSetupFrame.varForm.cellWidget(0,2).setCurrentIndex(1)
#        MainWin.optSetupFrame.varForm.cellWidget(1,2).setCurrentIndex(2)
#        MainWin.optSetupFrame.varForm.cellWidget(3,2).setCurrentIndex(3)
#        MainWin.optSetupFrame.varForm.cellWidget(4,2).setCurrentIndex(4)
#        MainWin.optSetupFrame.varForm.cellWidget(5,2).setCurrentIndex(5)
        # Switch to the Objective tab and set the objective
        MainWin.optSetupFrame.tabWidget.setCurrentIndex(2)
        MainWin.optSetupFrame.fAddButton.click()
        MainWin.optSetupFrame.fTable.setItem(0,0, QtWidgets.QTableWidgetItem("f['Rosenbrock']['f']"))
        MainWin.optSetupFrame.fTable.setItem(0,1, QtWidgets.QTableWidgetItem("1"))
        MainWin.optSetupFrame.fTable.setItem(0,2, QtWidgets.QTableWidgetItem("10000"))
        ## Switch to the Solver tab and set the solver

        MainWin.optSetupFrame.tabWidget.setCurrentIndex(3)
        solverName = MainWin.optSetupFrame.solverBox.findText("NLopt")
        ### Select Sub-Solver for NLopt
        MainWin.optSetupFrame.solverBox.setCurrentIndex(solverName)
        solverOptionName = MainWin.optSetupFrame.solverOptionTable.cellWidget(0,1).findText('"DIRECT"')
        MainWin.optSetupFrame.solverOptionTable.cellWidget(0,1).setCurrentIndex(solverOptionName)

        MainWin.optSetupFrame.applyChanges()
        MainWin.optSetupFrame.setSolver(MainWin.optSetupFrame.solverBox.currentText())
        MainWin.optSetupFrame.lastSolver = MainWin.optSetupFrame.solverBox.currentText()

        MainWin.optSetupFrame.tabWidget.setCurrentIndex(4)

        MainWin.optSetupFrame.optMonitorFrame.startButton.click()
        while MainWin.optSetupFrame.optMonitorFrame.opt.isAlive(): # while is running
            None
#        print("Got here")
        time.sleep(5)

        if not go(): break

        break
except Exception as e:
    # if there is any exception make sure the timers are stopped
    # before reraising it
    print("Exception stopping script")
    timersStop()
    with open(errorFile, 'a') as f:
        f.write('ERROR: Exception: {0}\n'.format(e))
timersStop() #make sure all timers are stopped

#Try to close FOQUS
timers['msg_no'].start(1000)
MainWin.close()
timerWait('msg_no')
print("Exited Code")
