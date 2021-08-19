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
from PyQt5 import QtCore
import matplotlib.pyplot as plt
from foqus_lib.framework.uq.Common import Common

global TIME_STEP, HAVE_TEXT
MAX_RUN_TIME = 5000000 #Maximum time to let script run in ms.
TIME_STEP = 5
HAVE_TEXT = 1
testOutFile = 'ui_test_out.txt'
with open(testOutFile, 'w') as f:
    f.write('')
timers = {}

if HAVE_TEXT == 1:
    global dialog, textedit
    dialog = Common.textDialog(MainWin)
    textedit = dialog.textedit

global go
def go(MainWin=MainWin):
    '''
        Process gui events so that gui can still function(ish) while 
        script is running also add delay between calls to GUI stuff to
        make the execution fun to watch.  Also checks the stop flag and 
        returns True keep going or False to stop.
    '''
    MainWin.app.processEvents()
    time.sleep(0.05) 
    return not MainWin.helpDock.stop

def getButton(w, label):
    blist = w.buttons()
    #print [b.text() for b in blist]
    for b in blist:
        if b.text().replace("&", "") == label:
            return b
    return None

def rsAnalyze(self=self, MainWin = MainWin, getButton=getButton, timers=timers):
    w = MainWin.app.activeWindow()
    if 'AnalysisDialog' in str(type(w)):
        timers['rs_analyze'].stop()
        ### set response surface mode
        #w.setWizardRSAnalysisMode(True)
        ### need to check the response surface button
        #w.wizardRS_radio.setChecked(True)
        if HAVE_TEXT == 1:
           textedit.insertPlainText('      Performing response surface validation\n')
           textedit.ensureCursorVisible() # Scroll the window to the bottom
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
           textedit.insertPlainText('      Generating plots for response surfaces\n')
           textedit.ensureCursorVisible() # Scroll the window to the bottom
           if not go():
               w.close()
               return
           time.sleep(TIME_STEP)
        w.wizardViz_combo1.setCurrentIndex(1)
        w.wizardViz_combo2.setCurrentIndex(2)
        w.wizardViz_button.click()
        time.sleep(TIME_STEP)
        ### visualization (1D, input 1)
        w.wizardViz_combo1.setCurrentIndex(1)
        w.wizardViz_combo2.setCurrentIndex(0)
        w.wizardViz_button.click()
        time.sleep(TIME_STEP)
        ### visualization (1D, input 2)
        w.wizardViz_combo1.setCurrentIndex(2)
        w.wizardViz_button.click()
        time.sleep(TIME_STEP)

        ### UA
        if HAVE_TEXT == 1:
           textedit.insertPlainText('      Performing uncertainty analysis\n')
           textedit.ensureCursorVisible() # Scroll the window to the bottom
           if not go():
               w.close()
               return
           time.sleep(TIME_STEP)
        w.wizardAnalyze_button.click()
        time.sleep(TIME_STEP)

        ### SA
        if HAVE_TEXT == 1:
           textedit.insertPlainText('      Performing sensitivity analysis\n')
           textedit.ensureCursorVisible() # Scroll the window to the bottom
           if not go():
               w.close()
               return
           time.sleep(TIME_STEP)
        ### sensitivity analysis (first order)
        w.wizardAnalyze_combo1.setCurrentIndex(1)
        # w.wizardAnalyze()
        w.wizardAnalyze_button.click()
        time.sleep(TIME_STEP)
        ### sensitivity analysis (total order)
        w.wizardAnalyze_combo2.setCurrentIndex(2)
        # w.wizardAnalyze()
        w.wizardAnalyze_button.click()
        time.sleep(TIME_STEP)

        w.close()

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
    for key, t in timers.items():
        t.stop()
        
# make the timers that will be needed just start and stop as needed
# need to make sure that when this script exits all timers are stopped
# or some crazy stuff may happen untill you exit FOQUS.
addTimer('time_out', MainWin.helpDock.setStopTrue) #stop script for taking too long
addTimer('msg_okay', MainWin.helpDock.msgBoxOK) #click okay on a pop up message box
addTimer('msg_no', MainWin.helpDock.msgBoxNo) #Click no on a popup message box
addTimer('rs_analyze', rsAnalyze)
# Start timer to stop script for running too long
# This won't work it execution of the script is blocked.
timers['time_out'].start(MAX_RUN_TIME) 

try:
    #raise(Exception("Test excpetion handeling"))
    while(1):

        ### This is the dialog I created for this type of stuff
        if HAVE_TEXT == 1:
            #dialog = Common.textDialog(MainWin)
            dialog.show()
            #textedit = dialog.textedit
            textedit.insertPlainText('Do not move your mouse or type anything until the end\n')
            textedit.ensureCursorVisible() # Scroll the window to the bottom

        ### Go to main window home
        if HAVE_TEXT == 1:
           textedit.insertPlainText('Entering the home screen\n')
           textedit.ensureCursorVisible() # Scroll the window to the bottom
           if not go(): break
           time.sleep(TIME_STEP)
        MainWin.homeAction.trigger()
        if not go(): break
        time.sleep(TIME_STEP)

        ### Enter session name 
        if HAVE_TEXT == 1:
           textedit.insertPlainText('Typing in the session name = UQ GUI test\n')
           textedit.ensureCursorVisible() # Scroll the window to the bottom
           if not go(): break
           time.sleep(TIME_STEP)
        MainWin.dashFrame.sessionNameEdit.setText("UQ GUI test - use sample file")
        if not go(): break
        time.sleep(TIME_STEP)

        ###===========================================
        ### Go to UQ module (click the top icon)
        ###===========================================
        if HAVE_TEXT == 1:
           textedit.insertPlainText('Clicking the Uncertainty icon (at the top)\n')
           textedit.ensureCursorVisible() # Scroll the window to the bottom
           if not go(): break
           time.sleep(TIME_STEP)
        MainWin.uqSetupAction.trigger()
        if not go(): break
        time.sleep(TIME_STEP)

        ### add simulation in UQ module ('Load File') 
        if HAVE_TEXT == 1:
           textedit.insertPlainText('   Clicking the load file button, enter file name\n')
           textedit.ensureCursorVisible() # Scroll the window to the bottom
           if not go(): break
           time.sleep(TIME_STEP)
        ###MainWin.uqSetupFrame.loadSimulationButton.click()
        fname = '../GitHub/FOQUS/foqus/examples/UQ/test_suite/'
        fname = fname + 'Branin/BraninSample.psuade'
        data = LocalExecutionModule.readSampleFromPsuadeFile(fname)
        data.setSession(MainWin.uqSetupFrame.dat)
        MainWin.uqSetupFrame.dat.uqSimList.append(data)
        if not go(): break
        MainWin.uqSetupFrame.updateSimTable()
        if not go(): break
        MainWin.uqSetupFrame.dataTabs.setEnabled(True)
        if not go(): break
        time.sleep(TIME_STEP)

        ### go to analyze screen
        if HAVE_TEXT == 1:
           textedit.insertPlainText('   Clicking the Analysis button for ensemble 1\n')
           textedit.ensureCursorVisible() # Scroll the window to the bottom
           if not go(): break
           time.sleep(TIME_STEP)
        timers['rs_analyze'].start(1000)
        timers['msg_okay'].start(1000)
        w = MainWin.uqSetupFrame.simulationTable.cellWidget(0,4)
        time.sleep(TIME_STEP)
        w.click()
        timers['rs_analyze'].stop()
        timers['msg_okay'].stop()
        if not go(): break
        time.sleep(TIME_STEP)

        ### Wait 
        if HAVE_TEXT == 1:
           textedit.insertPlainText('This test will terminate in 30 seconds\n')
           textedit.ensureCursorVisible() # Scroll the window to the bottom
        for ii in range(30):
           if not go(): break
           time.sleep(1)

        ### Close FOQUS
        timers['msg_no'].start(1000)
        if HAVE_TEXT == 1:
           dialog.close() 
        MainWin.close()
        timers['msg_no'].stop()
        break

except Exception as e:
    # if there is any exception make sure the timers are stopped
    # before reraising it
    print ("Exception stopping script")
    timersStop()
    with open(testOutFile, 'a') as f:
        f.write('Exception: {0}\n'.format(e))
    raise(e)
timersStop() #make sure all timers are stopped 
