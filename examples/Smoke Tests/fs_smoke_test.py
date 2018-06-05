from PyQt5 import QtCore, QtWidgets

MAX_RUN_TIME = 50000 # Maximum time to let script run in ms.
testOutFile = 'ui_test_out.txt'
with open(testOutFile, 'w') as f: # file to write test results to
    f.write('Test Results\n')
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

def add_UQ_cancel(MainWin=MainWin, getButton=getButton, timers=timers):
    """Cancel adding a UQ ensemble, stops timer once the window comes up"""
    w = MainWin.app.activeWindow()
    if 'updateUQModelDialog' in str(type(w)):
        getButton(w.buttonBox, 'Cancel').click()
        timers['add_UQ_cancel'].stop()

def add_UQ_okay(MainWin=MainWin, getButton=getButton, timers=timers):
    """Press OK in adding a UQ ensemble, stops timer once the window comes up"""
    w = MainWin.app.activeWindow()
    if 'updateUQModelDialog' in str(type(w)):
        getButton(w.buttonBox, 'OK').click()
        timers['add_UQ_okay'].stop()

def uq_sampling_scheme_MC(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup up an enseble sampling scheme, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    if 'SimSetup' in str(type(w)):
        timers['uq_sampling_scheme'].stop()
        w.distTable.cellWidget(1,1).setCurrentIndex(1)
        w.samplingTabs.setCurrentIndex(1)
        items = w.schemesList.findItems('Monte Carlo', QtCore.Qt.MatchExactly)
        w.schemesList.setCurrentItem(items[0])
        w.numSamplesBox.setValue(100)
        w.generateSamplesButton.click()
        if not go(sleep=2): return #wait long enough for samples to generate
        w.doneButton.click()
        
def uq_sampling_scheme_QMC(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup up an enseble sampling scheme, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    if 'SimSetup' in str(type(w)):
        timers['uq_sampling_scheme'].stop()
        w.distTable.cellWidget(1,1).setCurrentIndex(1)
        w.samplingTabs.setCurrentIndex(1)
        items = w.schemesList.findItems('Quasi Monte Carlo', QtCore.Qt.MatchExactly)
        w.schemesList.setCurrentItem(items[0])
        w.numSamplesBox.setValue(100)
        w.generateSamplesButton.click()
        if not go(sleep=2): return #wait long enough for samples to generate
        w.doneButton.click()
        
def uq_sampling_scheme_LH(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup up an enseble sampling scheme, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    if 'SimSetup' in str(type(w)):
        timers['uq_sampling_scheme'].stop()
        w.distTable.cellWidget(1,1).setCurrentIndex(1)
        w.samplingTabs.setCurrentIndex(1)
        items = w.schemesList.findItems('Latin Hypercube', QtCore.Qt.MatchExactly)
        w.schemesList.setCurrentItem(items[0])
        w.numSamplesBox.setValue(100)
        w.generateSamplesButton.click()
        if not go(sleep=2): return #wait long enough for samples to generate
        w.doneButton.click()
        
def uq_sampling_scheme_OA(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup up an enseble sampling scheme, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    if 'SimSetup' in str(type(w)):
        timers['uq_sampling_scheme'].stop()
        w.distTable.cellWidget(1,1).setCurrentIndex(1)
        w.samplingTabs.setCurrentIndex(1)
        items = w.schemesList.findItems('Orthogonal Array', QtCore.Qt.MatchExactly)
        w.schemesList.setCurrentItem(items[0])
        w.numSamplesBox.setValue(100)
        w.generateSamplesButton.click()
        if not go(sleep=2): return #wait long enough for samples to generate
        w.doneButton.click()
        
def uq_sampling_scheme_MD(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup up an enseble sampling scheme, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    if 'SimSetup' in str(type(w)):
        timers['uq_sampling_scheme'].stop()
        w.distTable.cellWidget(1,1).setCurrentIndex(1)
        w.samplingTabs.setCurrentIndex(1)
        items = w.schemesList.findItems('Morris Design', QtCore.Qt.MatchExactly)
        w.schemesList.setCurrentItem(items[0])
        w.numSamplesBox.setValue(100)
        w.generateSamplesButton.click()
        if not go(sleep=2): return #wait long enough for samples to generate
        w.doneButton.click()
        
def uq_sampling_scheme_GMD(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup up an enseble sampling scheme, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    if 'SimSetup' in str(type(w)):
        timers['uq_sampling_scheme'].stop()
        w.distTable.cellWidget(1,1).setCurrentIndex(1)
        w.samplingTabs.setCurrentIndex(1)
        items = w.schemesList.findItems('Generalized Morris Design', QtCore.Qt.MatchExactly)
        w.schemesList.setCurrentItem(items[0])
        w.numSamplesBox.setValue(100)
        w.generateSamplesButton.click()
        if not go(sleep=2): return #wait long enough for samples to generate
        w.doneButton.click()
        
def uq_sampling_scheme_GS(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup up an enseble sampling scheme, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    if 'SimSetup' in str(type(w)):
        timers['uq_sampling_scheme'].stop()
        w.distTable.cellWidget(1,1).setCurrentIndex(1)
        w.samplingTabs.setCurrentIndex(1)
        items = w.schemesList.findItems('Gradient Sample', QtCore.Qt.MatchExactly)
        w.schemesList.setCurrentItem(items[0])
        w.numSamplesBox.setValue(100)
        w.generateSamplesButton.click()
        if not go(sleep=2): return #wait long enough for samples to generate
        w.doneButton.click()
        
def uq_sampling_scheme_METIS(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup up an enseble sampling scheme, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    if 'SimSetup' in str(type(w)):
        timers['uq_sampling_scheme'].stop()
        w.distTable.cellWidget(1,1).setCurrentIndex(1)
        w.samplingTabs.setCurrentIndex(1)
        items = w.schemesList.findItems('METIS', QtCore.Qt.MatchExactly)
        w.schemesList.setCurrentItem(items[0])
        w.numSamplesBox.setValue(100)
        w.generateSamplesButton.click()
        if not go(sleep=2): return #wait long enough for samples to generate
        w.doneButton.click()
        
def fs_scheme(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup a flowsheet, run once, run several series, and then apply sort filters, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    if 'AnalysisDialog' in str(type(w)):
        timers['fs_scheme'].stop()

        ## Close Window
        w.close()

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
    for key, t in timers.iteritems():
        t.stop()

def timerWait(timer, sleep=0.25, n=40, go=go, timers=timers, tf=testOutFile):
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
addTimer('add_UQ_cancel', add_UQ_cancel) # click cancel on uq ensemble dialog
addTimer('add_UQ_okay', add_UQ_okay) # click okay on uq ensemble dialog
addTimer('uq_sampling_scheme_MC', uq_sampling_scheme_MC) # do sampling scheme dialog
addTimer('uq_sampling_scheme_QMC', uq_sampling_scheme_QMC) # do sampling scheme dialog
addTimer('uq_sampling_scheme_LH', uq_sampling_scheme_LH) # do sampling scheme dialog
addTimer('uq_sampling_scheme_OA', uq_sampling_scheme_OA) # do sampling scheme dialog
addTimer('uq_sampling_scheme_MD', uq_sampling_scheme_MD) # do sampling scheme dialog
addTimer('uq_sampling_scheme_GMC', uq_sampling_scheme_GMD) # do sampling scheme dialog
addTimer('uq_sampling_scheme_GS', uq_sampling_scheme_GS) # do sampling scheme dialog
addTimer('uq_sampling_scheme_METIS', uq_sampling_scheme_METIS) # do sampling scheme dialog
addTimer('fs_scheme', fs_scheme) # do analysis scheme dialog

timers['time_out'].start(MAX_RUN_TIME) # start max script time timer

try: # Catch any exception and stop all timers before finishing up
    while(1): # Loop and break and break as convenient way to jump to end
        # Rosenbrock Test for UQ
        MainWin.homeAction.trigger()
        if not go(): break
        # Enter some information
        MainWin.dashFrame.sessionNameEdit.setText("Simple Flowsheet")
        if not go(): break
        MainWin.dashFrame.tabWidget.setCurrentIndex(1)
        if not go(): break
        MainWin.dashFrame.setSessionDescription("Simple Flowsheet Description Text")
        if not go(): break
        # Make a flowsheet
        MainWin.fsEditAction.trigger()
        if not go(): break
        MainWin.addNodeAction.trigger()
        if not go(): break
        MainWin.flowsheetEditor.sc.mousePressEvent(
            None, dbg_x=10, dbg_y=10, dbg_name="calc")
        if not go(): break
        MainWin.toggleNodeEditorAction.trigger()
        if not go(): break
        MainWin.nodeDock.addInput("x1")
        MainWin.nodeDock.addInput("x2")
        MainWin.nodeDock.addInput("x3")
        MainWin.nodeDock.inputVarTable.item(0, 5).setText("-2")
        MainWin.nodeDock.inputVarTable.item(0, 6).setText("2")
        MainWin.nodeDock.inputVarTable.item(1, 5).setText("-1")
        MainWin.nodeDock.inputVarTable.item(1, 6).setText("4")
        MainWin.nodeDock.inputVarTable.item(2, 5).setText("-3")
        MainWin.nodeDock.inputVarTable.item(2, 6).setText("6")
        MainWin.nodeDock.inputVarTable.item(0, 4).setText("1")
        MainWin.nodeDock.inputVarTable.item(1, 4).setText("3")
        MainWin.nodeDock.inputVarTable.item(2, 4).setText("-2")
        MainWin.nodeDock.inputVarTable.item(0, 1).setText("1")
        MainWin.nodeDock.inputVarTable.item(1, 1).setText("3")
        MainWin.nodeDock.inputVarTable.item(2, 1).setText("-2")
        MainWin.nodeDock.toolBox.setCurrentIndex(1)
        MainWin.nodeDock.addOutput("z")
        MainWin.nodeDock.tabWidget.setCurrentIndex(2)
        MainWin.nodeDock.pyCode.setPlainText("f.z = x.x1*math.sqrt(x.x2)/x.x3")
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
        MainWin.uqSetupAction.trigger()
        if not go(): break
        # Add the sampling scheme
        timers['add_UQ_okay'].start(1000)
        timers['uq_sampling_scheme'].start(500)
        MainWin.uqSetupFrame.addSimulationButton.click()
        if not timerWait('add_UQ_okay'): break
        if not timerWait('uq_sampling_scheme'): break
        # Run UQ ensemble
        MainWin.uqSetupFrame.simulationTable.cellWidget(0,3).click()
        timers['msg_okay'].start(500) # press okay on ensemble done msgbox
        while MainWin.uqSetupFrame.gThread.isAlive(): # while is running
            if not go():
                MainWin.uqSetupFrame.gThread.terminate()
                break
        if not timerWait('msg_okay'): break
        timers['fs_scheme'].start(500)
        MainWin.uqSetupFrame.simulationTable.cellWidget(0,4).click()
        if not timerWait('fs_scheme'): break
        ### Test for second run
        timers['add_UQ_okay'].start(1000)
        timers['uq_sampling_scheme'].start(500)
        MainWin.uqSetupFrame.addSimulationButton.click()
        if not timerWait('add_UQ_okay'): break
        if not timerWait('uq_sampling_scheme'): break
        # Run UQ ensemble
        MainWin.uqSetupFrame.simulationTable.cellWidget(1,3).click()
        timers['msg_okay'].start(500) # press okay on ensemble done msgbox
        while MainWin.uqSetupFrame.gThread.isAlive(): # while is running
            if not go():
                MainWin.uqSetupFrame.gThread.terminate()
                break
        if not timerWait('msg_okay'): break
        timers['uq_infer_scheme'].start(500)
        timers['uq_analyze_scheme'].start(500)
        MainWin.uqSetupFrame.simulationTable.cellWidget(1,4).click()
        if not timerWait('uq_analyze_scheme'): break
        if not timerWait('uq_infer_scheme'): break
#        timers['uq_infer_close'].start(500)
#        timers['uq_analyze_close'].start(500)
#        if not timerWait('uq_infer_close'): break
#        if not timerWait('uq_analyze_close'): break
        break
except Exception as e:
    # if there is any exception make sure the timers are stopped
    # before reraising it
    print "Exception stopping script"
    timersStop()
    with open(testOutFile, 'a') as f:
        f.write('ERROR: Exception: {0}\n'.format(e))
timersStop() #make sure all timers are stopped

##Try to close FOQUS
#timers['msg_no'].start(1000)
#MainWin.close()
#timerWait('msg_no')
#print("Exited Code")