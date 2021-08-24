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
from PySide import QtCore
from PySide.QtGui import *
from PySide.QtCore import *

import matplotlib.pyplot as plt
from foqus_lib.framework.uq.Common import Common

MAX_RUN_TIME = 5000000 #Maximum time to let script run in ms.
TIME_STEP = 1
TEXT_NOTEXT = 0
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

def rsAnalyze(self=self, MainWin=MainWin, getButton=getButton, timers=timers):
    TIME_STEP = 1
    w = MainWin.app.activeWindow()
    if 'AnalysisDialog' in str(type(w)):
       timers['rs_analyze'].stop()
       MainWin.app.processEvents()
       time.sleep(TIME_STEP)
       ### switch to expert mode
       w.modeButton.click()
       MainWin.app.processEvents()
       time.sleep(TIME_STEP)
       ### select output V (index=1, index=0 is NULL)
       w.output_combo.setCurrentIndex(1)
       MainWin.app.processEvents()
       time.sleep(TIME_STEP)
       ### enable the validate button
       MainWin.app.processEvents()
       time.sleep(TIME_STEP)
       ### select MARS (1 - MARS, 3 - sum of trees) with 100 bases
       w.RS_combo1.setCurrentIndex(1)
       time.sleep(TIME_STEP)
       w.RSMarsBasis_spin.setValue(100)
       w.RSValidationGroups_spin.setValue(5)
       MainWin.app.processEvents()
       time.sleep(TIME_STEP)

       ### validate 
       w.RSValidate_button.click()
       MainWin.app.processEvents()
       time.sleep(TIME_STEP)

       ### run UA on default set up for all inputs (uniform PDF)
       w.RSAnalyze_button.click()
       MainWin.app.processEvents()
       time.sleep(TIME_STEP)

       ### get the prior table for modification
       c = w.inputPrior_table

       ### Set up Viscosity input pdf
       #fname1 = '/g/g0/chtong/FOQUS/FOQUS/examples/UQ/test_suite/'
       fname1 = '../examples/UQ/test_suite/'
       fname1 = fname1 + 'Phoenix/Viscosity/VisPostSample'
       data1 = LocalExecutionModule.readDataFromSimpleFile(fname1)
       nInputs1 = data1[0].shape[1];
       c.sampleFiles.append(fname1)
       c.dispSampleFiles.append('VisPostSample')
       c.sampleNumInputs.append(nInputs1)

       ### Set up Density input pdf
       #fname2 = '/g/g0/chtong/FOQUS/FOQUS/examples/UQ/test_suite/'
       fname2 = '../examples/UQ/test_suite/'
       fname2 = fname2 + 'Phoenix/DensityModel/DenPostSample'
       data2 = LocalExecutionModule.readDataFromSimpleFile(fname2)
       nInputs2 = data2[0].shape[1];
       c.sampleFiles.append(fname2)
       c.dispSampleFiles.append('DenPostSample')
       c.sampleNumInputs.append(nInputs2)

       ### Set up Surface Tension input pdf
       #fname3 = '/g/g0/chtong/FOQUS/FOQUS/examples/UQ/test_suite/'
       fname3 = '../examples/UQ/test_suite/'
       fname3 = fname3 + 'Phoenix/SurfaceTension/STPostSample'
       data3 = LocalExecutionModule.readDataFromSimpleFile(fname3)
       nInputs3 = data3[0].shape[1];
       c.sampleFiles.append(fname3)
       c.dispSampleFiles.append('STPostSample')
       c.sampleNumInputs.append(nInputs3)

       ### Set up Surface Tension input numbers
       def changeValue(row, fileNum, fileIndex):
           c.verticalScrollBar().setValue(max([0, row - 2]))
           p = c.cellWidget(row,c.col_index['pdf'])
           p.setCurrentIndex(8) #Set pdf to sample
           MainWin.app.processEvents()
           combo = c.cellWidget(row, c.col_index['p1'])
           combo.setCurrentIndex(fileNum)
           MainWin.app.processEvents()
           time.sleep(TIME_STEP/2)
           table = c.cellWidget(row, c.col_index['p2'])
           spinbox = table.cellWidget(0,1)
           spinbox.setValue(fileIndex)
           MainWin.app.processEvents()
           time.sleep(TIME_STEP)

       ### Set up Viscosity input numbers
       # -- first input mapped to posterior input 4
       changeValue(0, 1, 4)
       # -- second input mapped to posterior input 9
       changeValue(1, 1, 9)
       # -- third input mapped to posterior input 5
       changeValue(2, 1, 5)
       # -- fourth input mapped to posterior input 10
       changeValue(3, 1, 10)
       # -- fifth input mapped to posterior input 6
       changeValue(4, 1, 6)
       # -- sixth input mapped to posterior input 7
       changeValue(5, 1, 7)
       # -- seventh input mapped to posterior input 8
       changeValue(6, 1, 8)

       ### Set up Density input numbers
       for ii in range(5):
           changeValue(ii + 17, 2, ii + 4)

       ### Set up Surface Tension input numbers
       # -- first input mapped to posterior input 4
       changeValue(7, 3, 4)
       # -- second input mapped to posterior input 9
       changeValue(8, 3, 9)
       # -- third mapped to posterior input 5
       changeValue(9, 3, 5)
       # -- fourth mapped to posterior input 10
       changeValue(10, 3, 10)
       # -- fifth mapped to posterior input 6
       changeValue(11, 3, 6)
       # -- sixth mapped to posterior input 11
       changeValue(12, 3, 11)
       # -- seventh mapped to posterior input 7
       changeValue(13, 3, 7)
       # -- eighth mapped to posterior input 12
       changeValue(14, 3, 12)
       # -- ninth mapped to posterior input 8
       changeValue(15, 3, 8)
       # -- tenth mapped to posterior input 13
       changeValue(16, 3, 13)

       ### perform UA on new distributions
       #w.expertRSAnalyze()
       w.RSAnalyze_button.click()

       ### wait before termination
       for ii in range(3):
          MainWin.app.processEvents()
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
        if TEXT_NOTEXT == 1:
           dialog = Common.textDialog(MainWin)
           dialog.show() 
           textedit = dialog.textedit 
           pText = 'Do not move your mouse or type anything until the end\n'
           textedit.insertPlainText(pText)
           textedit.ensureCursorVisible() # Scroll the window to the bottom

        ### Go to main window home
        if TEXT_NOTEXT == 1:
           textedit.insertPlainText('Entering the home screen\n')
           textedit.ensureCursorVisible() # Scroll the window to the bottom
        if not go(): break
        time.sleep(TIME_STEP)
        MainWin.homeAction.trigger()
        if not go(): break
        time.sleep(TIME_STEP)

        ### Enter session name 
        if TEXT_NOTEXT == 1:
           textedit.insertPlainText('Typing in the session name = Full model\n')
           textedit.ensureCursorVisible() # Scroll the window to the bottom
        if not go(): break
        time.sleep(TIME_STEP)
        MainWin.dashFrame.sessionNameEdit.setText("Full Model UQ")
        if not go(): break
        time.sleep(TIME_STEP)

        ###===========================================
        ### Go to UQ module (click the top icon)
        ###===========================================
        if TEXT_NOTEXT == 1:
           textedit.insertPlainText('Clicking the Uncertainty icon (top)\n')
           textedit.ensureCursorVisible() # Scroll the window to the bottom
        if not go(): break
        time.sleep(TIME_STEP)
        MainWin.uqSetupAction.trigger()
        if not go(): break
        time.sleep(TIME_STEP)

        ### add simulation in UQ module ('Load File') 
        if TEXT_NOTEXT == 1:
           pText = '   Clicking the load file button, enter file name\n'
           textedit.insertPlainText(pText)
           textedit.ensureCursorVisible() # Scroll the window to the bottom
        if not go(): break
        time.sleep(TIME_STEP)
        ###MainWin.uqSetupFrame.loadSimulationButton.click()
        #fname = '/g/g0/chtong/FOQUS/FOQUS/examples/UQ/test_suite/'
        fname = '../examples/UQ/test_suite/'
        fname = fname + 'Phoenix/FullModel/dataSet.psuade'
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
        if TEXT_NOTEXT == 1:
           pText = '   Clicking the Analysis button for Ensemble 1\n'
           textedit.insertPlainText(pText)
           textedit.ensureCursorVisible() # Scroll the window to the bottom
           pText = '      - perform uncertainty analysis using default PDFs\n'
           textedit.insertPlainText(pText)
           textedit.ensureCursorVisible() # Scroll the window to the bottom
           pText = '      - perform uncertainty analysis using posterior samples\n'
           textedit.insertPlainText(pText)
           textedit.ensureCursorVisible() # Scroll the window to the bottom
        if not go(): break
        time.sleep(TIME_STEP)
        timers['rs_analyze'].start(1000)
        w = MainWin.uqSetupFrame.simulationTable.cellWidget(0,4)
        w.click()
        timers['rs_analyze'].stop()
        if not go(): break

        ### Wait 
        if TEXT_NOTEXT == 1:
           textedit.insertPlainText('This test will terminate in 30 seconds\n')
           textedit.ensureCursorVisible() # Scroll the window to the bottom
        if not go(): break
        time.sleep(TIME_STEP)
        for ii in range(30):
           if not go(): break
           time.sleep(1)

        ### Close FOQUS
        #w = MainWin.app.activeWindow()
        #if 'AnalysisDialog' in str(type(w)):
        #   w.close()
        timers['msg_no'].start(20)
        if TEXT_NOTEXT == 1:
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
