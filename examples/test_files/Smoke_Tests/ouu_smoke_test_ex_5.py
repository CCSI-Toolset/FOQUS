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

from foqus_lib.gui.common.InputPriorTable import InputPriorTable
from foqus_lib.framework.ouu.OUU import OUU

MAX_RUN_TIME = 8000000 # Maximum time to let script run in ms.
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

global errorCount
global errorTitle
global errorFile
errorFile = "AutoErrLog_ouu_ex_5.txt"
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
addTimer('Error_okay', Error_okay) # click okay on uq ensemble dialog
addTimer('Error_okay_text', Error_okay_text) # click okay on uq ensemble dialog
timers['time_out'].start(MAX_RUN_TIME) # start max script time timer

try: # Catch any exception and stop all timers before finishing up
    while(1): # Loop and break and break as convenient way to jump to end
        # Go to home
        MainWin.homeAction.trigger()
        if not go(): break
        # Enter some information
        MainWin.dashFrame.sessionNameEdit.setText("OUU Test")
        if not go(): break
        MainWin.dashFrame.tabWidget.setCurrentIndex(1)
        if not go(): break
        MainWin.dashFrame.setSessionDescription("Optimization Under Uncertainty Description Text")
        if not go(): break
        
        ## -----------------Start Error Monitoring----------------------------
        timers['Error_okay'].start(1000)
        timers['Error_okay_text'].start(1000)
        ## -------------------------------------------------------------------
        
        global errorTitle
        errorTitle = "Set Window to OUU"
    
        #Set Window to OUU
        MainWin.ouuSetupAction.trigger()
        errorTitle = "Check Box for Model File"
        MainWin.ouuSetupFrame.modelFile_radio.setChecked(True)
        fname = "../GitHub/FOQUS/foqus/examples/OUU/test_suite/ouu_optdriver.in"
#        fname = 'C:/Users/318051/Documents/GitHub/FOQUS/foqus/examples/OUU/test_suite/ouu_optdriver.in'
        errorTitle = "Open optdriver.in File"
        MainWin.ouuSetupFrame.filesDir, name = os.path.split(fname)
        MainWin.ouuSetupFrame.modelFile_edit.setText(fname)
        MainWin.ouuSetupFrame.model = LocalExecutionModule.readSampleFromPsuadeFile(fname)
        MainWin.ouuSetupFrame.model = MainWin.ouuSetupFrame.model.model
        MainWin.ouuSetupFrame.input_table.init(MainWin.ouuSetupFrame.model,InputPriorTable.OUU)
        errorTitle = "Set All Selection Buttons to Enabled and Initialize Tabs/Etc"
        MainWin.ouuSetupFrame.setFixed_button.setEnabled(True)
        MainWin.ouuSetupFrame.setX1_button.setEnabled(True)
        MainWin.ouuSetupFrame.setX1d_button.setEnabled(True)
        MainWin.ouuSetupFrame.setX2_button.setEnabled(True)
        MainWin.ouuSetupFrame.setX3_button.setEnabled(True)
        MainWin.ouuSetupFrame.setX4_button.setEnabled(True)
        MainWin.ouuSetupFrame.initTabs()
        MainWin.ouuSetupFrame.setCounts()
        errorTitle = "Set All of the Variable Types to Match the Example"
        for ii in range(4):
            c = MainWin.ouuSetupFrame.input_table.cellWidget(ii,0)
            c.setChecked(True)
        MainWin.ouuSetupFrame.setX1()
        for ii in range(4):
            c = MainWin.ouuSetupFrame.input_table.cellWidget(ii,0)
            c.setChecked(False)
            
        for ii in range(4):
            MainWin.ouuSetupFrame.input_table.verticalScrollBar().setValue(ii+2)
            MainWin.app.processEvents()
            c = MainWin.ouuSetupFrame.input_table.cellWidget(ii+4,0)
            c.setChecked(True)
        MainWin.ouuSetupFrame.setX2()
        for ii in range(4):
            c = MainWin.ouuSetupFrame.input_table.cellWidget(ii+4,0)
            c.setChecked(False)
        
        MainWin.ouuSetupFrame.input_table.verticalScrollBar().setValue(6)
        MainWin.app.processEvents()
        c = MainWin.ouuSetupFrame.input_table.cellWidget(8,0)
        c.setChecked(True)
        MainWin.ouuSetupFrame.setX3()
        c = MainWin.ouuSetupFrame.input_table.cellWidget(8,0)
        c.setChecked(False)
        
        for ii in range(3):
           MainWin.ouuSetupFrame.input_table.verticalScrollBar().setValue(ii+7)
           MainWin.app.processEvents()
           c = MainWin.ouuSetupFrame.input_table.cellWidget(ii+9,0)
           c.setChecked(True)
           
        MainWin.ouuSetupFrame.setX4()
        
        errorTitle = "Set Inner Solver"
        
        MainWin.ouuSetupFrame.secondarySolver_combo.setCurrentIndex(0)
        MainWin.ouuSetupFrame.tabs.setCurrentIndex(2)
        
        errorTitle = "Load x3 samples"
        
        fname = '../GitHub/FOQUS/foqus/examples/OUU/test_suite/ex456_x3sample.smp'
#        MainWin.ouuSetupFrame.x4File_edit.setText(fname)
        data = LocalExecutionModule.readDataFromSimpleFile(fname, hasColumnNumbers = False)
        inData = data[0]
        numInputs = inData.shape[1]
        M3 = len(MainWin.ouuSetupFrame.input_table.getUQDiscreteVariables()[0])
        if numInputs != M3:
            QMessageBox.warning(MainWin.ouuSetupFrame, "Number of variables don't match",
                                      'The number of variables from the file (%d) does not match the number of Z3 discrete variables (%d).  You will not be able to perform analysis until this is corrected.' % (numInputs, M3))
        else:
            MainWin.ouuSetupFrame.compressSamples_chk.setEnabled(True)
            MainWin.ouuSetupFrame.loadTable(MainWin.ouuSetupFrame.z3_table, inData)
        
        errorTitle = "Change Settings for X4 Sampling"
        
#        #MainWin.ouuSetupFrame.x4SampleScheme_label.setEnabled(False)
#        #MainWin.ouuSetupFrame.x4SampleScheme_combo.setEnabled(False)
#        #MainWin.ouuSetupFrame.x4SampleSize_label.setEnabled(False)
#        #MainWin.ouuSetupFrame.x4SampleSize_spin.setEnabled(False)
#        MainWin.ouuSetupFrame.z4NewSample_radio.setChecked(False)
#        #MainWin.ouuSetupFrame.x4File_edit.setEnabled(True)
#        MainWin.ouuSetupFrame.z4LoadSample_radio.setChecked(True)
#        MainWin.ouuSetupFrame.x4FileBrowse_button.setEnabled(True)
#        #MainWin.ouuSetupFrame.x4FileBrowse_button.setChecked(True)
        MainWin.ouuSetupFrame.x4SampleSize_spin.setValue(100)
        errorTitle = "Enable Response Surface"
        MainWin.ouuSetupFrame.x4RSMethod_check.toggle()
        errorTitle = "Switch Tab to Run Tab and Run the OUU"
        MainWin.ouuSetupFrame.tabs.setCurrentIndex(3)
        MainWin.ouuSetupFrame.run_button.click()
        errNum = errorCount
        timers['msg_okay'].start(1000) 
        while MainWin.ouuSetupFrame.OUUobj.thread.isRunning(): # while is running
            if not go():
                MainWin.ouuSetupFrame.OUUobj.thread.terminate()
                break
            if MainWin.ouuSetupFrame.OUUobj.thread.isFinished():
                MainWin.ouuSetupFrame.OUUobj.thread.terminate()
                break
            if (errorCount > errNum):
                break
        time.sleep(1)
        timers['msg_okay'].stop()
        
        ## -----------------Stop Error Monitoring----------------------------
        if not timerWait('Error_okay'): break
        if not timerWait('Error_okay_text'): break
        ## -------------------------------------------------------------------

        break
    
except Exception as e:
    # if there is any exception make sure the timers are stopped
    # before reraising it
    print ("Exception stopping script")
    timersStop()
    with open(testOutFile, 'a') as f:
        f.write('ERROR: Exception: {0}\n'.format(e))
timersStop() #make sure all timers are stopped
#print("after exception")

#Try to close FOQUS
timers['msg_no'].start(1000)
MainWin.close()
timerWait('msg_no')
print("Exited Code: OUU Test 5")
