from PySide import QtCore

MAX_RUN_TIME = 50000 #Maximum time to let script run in ms.
testOutFile = 'ui_test_out.txt'
with open(testOutFile, 'w') as f:
    f.write('')
timers = {}

def go(MainWin=MainWin):
    '''
        Process gui events so that gui can still function(ish) while 
        script is running also add delay between calls to GUI stuff to
        make the execution fun to watch.  Also checks the stop flag and 
        returns True keep going or False to stop.
    '''
    MainWin.app.processEvents()
    time.sleep(0.25) 
    return not MainWin.helpDock.stop

def getButton(w, label):
    blist = w.buttons()
    #print [b.text() for b in blist]
    for b in blist:
        if b.text().replace("&", "") == label:
            return b
    return None

def addEnsembelCancel(self=self, MainWin=MainWin, getButton=getButton):
    w = MainWin.app.activeWindow()
    if 'updateUQModelDialog' in str(type(w)):
        b = getButton(w.buttonBox, 'Cancel')
        b.click()
        
def addEnsembelOkay(self=self, MainWin=MainWin, getButton=getButton):
    w = MainWin.app.activeWindow()
    if 'updateUQModelDialog' in str(type(w)):
        b = getButton(w.buttonBox, 'OK')
        b.click()
        
def uqSamplingScheme(self=self, MainWin=MainWin, getButton=getButton, timers=timers):
    w = MainWin.app.activeWindow()
    print str(type(w))
    if 'SimSetup' in str(type(w)):
        timers['uq_sampling_scheme'].stop()
        time.sleep(0.5)
        w.samplingTabs.setCurrentIndex(1)
        time.sleep(0.5)
        items = w.schemesList.findItems('Monte Carlo', QtCore.Qt.MatchExactly)
        w.schemesList.setCurrentItem(items[0])
        time.sleep(0.5)
        w.numSamplesBox.setValue(10)
        time.sleep(0.5)
        w.generateSamplesButton.click()
        time.sleep(2) # need to wait long enough for samples to generate
        w.doneButton.click()
        
def addTimer(name, cb, MainWin=MainWin, timers=timers):
    '''
        Using timers to push buttons on popups and modal dialogs and 
        other things were I need an easy way to make things happen from
        a seperate thread.  Usually where something is blocking the main
        GUI loop.
        
        name: string name of timer
        cd is the timer call back function
    '''
    timers[name] =  QtCore.QTimer(MainWin)
    timers[name].timeout.connect(cb)
        
def timersStop(timers=timers):
    '''
        Call stop for all timers to make sure they all stop
    '''
    for key, t in timers.iteritems():
        t.stop()
        
# make the timers that will be needed just start and stop as needed
# need to make sure that when this script exits all timers are stopped
# or some crazy stuff may happen untill you exit FOQUS.
addTimer('time_out', MainWin.helpDock.setStopTrue) #stop script for taking too long
addTimer('msg_okay', MainWin.helpDock.msgBoxOK) #click okay on a pop up message box
addTimer('msg_no', MainWin.helpDock.msgBoxNo) #Click no on a popup message box
addTimer('addUQ_cancel', addEnsembelCancel) # click cancel on add uq ensemble dialog
addTimer('addUQ_okay', addEnsembelOkay) # click cancel on add uq ensemble dialog
addTimer('uq_sampling_scheme', uqSamplingScheme)
# Start timer to stop script for running too long
# This won't work it execution of the script is blocked.
timers['time_out'].start(MAX_RUN_TIME) 

try:
    #raise(Exception("Test excpetion handeling"))
    while(1):
        # Flipping tabs
        MainWin.uqSetupAction.trigger()
        if not go(): break
        MainWin.fsEditAction.trigger()
        if not go(): break
        MainWin.fsEditAction.trigger()
        if not go(): break
        MainWin.homeAction.trigger()
        if not go(): break
        # Enter some information
        MainWin.dashFrame.sessionNameEdit.setText("Example GUI test")
        if not go(): break
        # Make a flowsheet
        MainWin.fsEditAction.trigger()
        if not go(): break
        MainWin.addNodeAction.trigger()
        if not go(): break
        MainWin.flowsheetEditor.sc.mousePressEvent(None, dbg_x=10, dbg_y=10, dbg_name="Test")
        if not go(): break
        MainWin.toggleNodeEditorAction.trigger()
        if not go(): break
        MainWin.nodeDock.addInput("x1")
        if not go(): break
        MainWin.nodeDock.addInput("x2")
        if not go(): break
        MainWin.nodeDock.inputVarTable.item(0, 5).setText("-10")
        if not go(): break
        MainWin.nodeDock.inputVarTable.item(0, 6).setText("10")
        if not go(): break
        MainWin.nodeDock.inputVarTable.item(1, 5).setText("-10")
        if not go(): break
        MainWin.nodeDock.inputVarTable.item(1, 6).setText("10")
        if not go(): break
        MainWin.nodeDock.inputVarTable.item(0, 4).setText("5")
        if not go(): break
        MainWin.nodeDock.inputVarTable.item(1, 4).setText("2")
        if not go(): break
        MainWin.nodeDock.toolBox.setCurrentIndex(1)
        if not go(): break
        MainWin.nodeDock.addOutput("z")
        if not go(): break
        MainWin.nodeDock.tabWidget.setCurrentIndex(2)
        if not go(): break
        MainWin.nodeDock.pyCode.setPlainText("f['z'] = x['x1'] + x['x2']\ntime.sleep(2)")
        if not go(): break
        MainWin.nodeDock.tabWidget.setCurrentIndex(0)
        if not go(): break
        # Before running the flowsheet start up a timer to close the 
        # message box that appears when the run completes
        timers['msg_okay'].start(1000) # try push okay in meassege box every second
        MainWin.runAction.trigger() #run flowsheet
        while MainWin.singleRun.is_alive():
            if not go(): 
                MainWin.singleRun.terminate()
                break
        for i in range(4): # wait a bit to make sure msgbox appears before proceeding
            if not go(): break
            time.sleep(1)
        if not go(): break
        # stop the message box closing timer.  Should have closed if you
        # are here
        timers['msg_okay'].stop()
        with open(testOutFile, 'a') as f:
            f.write('Flowsheet_run: {0}\n'.format(self.flowsheet.errorStat))
        #
        # Try out controling UQ ensemble add
        MainWin.uqSetupAction.trigger()
        if not go(): break
        # Start add then cancle
        timers['addUQ_cancel'].start(1000)
        MainWin.uqSetupFrame.addSimulationButton.click()
        if not go(): break
        timers['addUQ_cancel'].stop()
        # This time add for real
        timers['addUQ_okay'].start(1000)
        timers['uq_sampling_scheme'].start(1000)
        MainWin.uqSetupFrame.addSimulationButton.click()
        if not go(): break
        timers['addUQ_okay'].stop()
        w = MainWin.uqSetupFrame.simulationTable.cellWidget(0,3)
        w.click()
        timers['msg_okay'].start(2000) #press okay on msg box that appears when ens. is done
        while MainWin.uqSetupFrame.gThread.isAlive():
            if not go():
                MainWin.uqSetupFrame.gThread.terminate()
                break
        for i in range(4): # wait a bit
            if not go(): break
            time.sleep(1)
        if not go(): break
        timers['msg_okay'].start(1000)
        #####
        #Close FOQUS
        timers['msg_no'].start(1000)
        MainWin.close()
        timers['msg_no'].stop()
        break
except Exception as e:
    # if there is any exception make sure the timers are stopped
    # before reraising it
    print "Exception stopping script"
    timersStop()
    with open(testOutFile, 'a') as f:
        f.write('Exception: {0}\n'.format(e))
    raise(e)
timersStop() #make sure all timers are stopped 
