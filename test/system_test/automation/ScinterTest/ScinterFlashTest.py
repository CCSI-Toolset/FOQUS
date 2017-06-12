###############################################################################
#           Automated test for Scinter Flash Test
#           Runs on Excel 2010
#           Uses Python 2.7, pywinauto 0.4.3
#           Gregory Pope, LLNL
#           April 19, 2013
#           For Acceptance Testing Scinter Flash
#           V1.0
###############################################################################
import pywinauto
from pywinauto import clipboard
import time
from random import *

pwa_app = pywinauto.application.Application()

#initial values
feedT=100
feedP=50
feedF=48.748
feedetOHmolefrac=0.08905
feedH2Omolefrac=0.91095
flashT=150
flashP=20

# Initial duration seconds
dur = 20




def StartAp():
    # Start Application
    pwa_app.start_("C:\Program Files (x86)\Microsoft Office\Office14\EXCEL.EXE")
    print ('Started Application')
    return

def GetFile(FileName):
    #Get needed file
    print('Get needed file')
    w_handle = pywinauto.timings.WaitUntilPasses(30,0.5,lambda: pywinauto.findwindows.find_windows(title=u'Microsoft Excel - Book1')[0])
    window = pwa_app.window_(handle=w_handle)
    window.SetFocus()
    window.TypeKeys('%f')
    window.TypeKeys('o')
    w_handle = pywinauto.timings.WaitUntilPasses(30,0.5,lambda: pywinauto.findwindows.find_windows(title=u'Open', class_name='#32770')[0])
    window = pwa_app.window_(handle=w_handle)
    window.SetFocus()
    ctrl = window['Edit']
    ctrl.SetFocus()
    ctrl.TypeKeys(FileName,with_spaces=True)
    time.sleep(1)
    ctrl = window['&Open']
    ctrl.ClickInput()
    return


def PointCell(cell):
    #Pick cell in edit area
    print ('Pick cell in edit area '+cell)
    w_handle = pywinauto.timings.WaitUntilPasses(30,0.5,lambda: pywinauto.findwindows.find_windows(title=u'Microsoft Excel - Flash_Example_ACM.xlsm', class_name='XLMAIN')[0])
    window = pwa_app.window_(handle=w_handle)
    window.SetFocus()
    ctrl = window['11']
    ctrl.SetFocus()
    ctrl.TypeKeys(cell+'{ENTER}')
    time.sleep(1)
    return

def GetValue(cell):
    PointCell(cell)
    w_handle = pywinauto.timings.WaitUntilPasses(30,0.5,lambda: pywinauto.findwindows.find_windows(title=u'Microsoft Excel - Flash_Example_ACM.xlsm', class_name='XLMAIN')[0])
    window = pwa_app.window_(handle=w_handle)
    window.SetFocus()
    window.TypeKeys('^c')
    time.sleep(.5)
    value=pywinauto.clipboard.GetData(format=13)
    window.TypeKeys('{ESC}')
    time.sleep(.5)
    return(value)
    

def SetNum(value):
    #Set number to be coverted
    print('Run in grid area, value = '+ str(value))
    w_handle = pywinauto.timings.WaitUntilPasses(30,0.5,lambda: pywinauto.findwindows.find_windows(title=u'Microsoft Excel - Flash_Example_ACM.xlsm', class_name='XLMAIN')[0])
    window = pwa_app.window_(handle=w_handle)
    window.SetFocus()
    ctrl = window['13']
    ctrl.SetFocus()
    ctrl.TypeKeys(str(value)+'{ENTER}')

def SetConvert(ConvFrom,ConvTo):
    #Run conversion
    print('Set From ' + ConvFrom + ' To ' + ConvTo)
    w_handle = pywinauto.timings.WaitUntilPasses(30,0.5,lambda: pywinauto.findwindows.find_windows(title=u'Microsoft Excel - Flash_Example_ACM.xlsm', class_name='XLMAIN')[0])
    window = pwa_app.window_(handle=w_handle)
    window.SetFocus()
    ctrl = window['13']
    ctrl.SetFocus()
    ctrl.TypeKeys(ConvFrom+'{ENTER}')
    time.sleep(.75)
    ctrl.TypeKeys(ConvTo+'{ENTER}')
    time.sleep(.75)
    return

def RunMacro():
    #Run Macro
    print ('Run Macro')
    w_handle = pywinauto.timings.WaitUntilPasses(30,0.5,lambda: pywinauto.findwindows.find_windows(title=u'Microsoft Excel - Flash_Example_ACM.xlsm', class_name='XLMAIN')[0])
    window = pwa_app.window_(handle=w_handle)
    window.SetFocus()
    window.TypeKeys('%{F8}')
    w_handle = pywinauto.timings.WaitUntilPasses(20,0.5,lambda: pywinauto.findwindows.find_windows(title=u'Macro', class_name='bosa_sdm_XL9')[0])
    window = pwa_app.window_(handle=w_handle)
    window.SetFocus()
    ctrl = window['EDTBX']
    ctrl.TypeKeys('runSim')
    window.TypeKeys('%r')
    return




########################################
#Main program

print ('Start Application')
StartAp()
FileName="C:\AspenSinterFiles\ACM_Install_Test\Flash_Example_ACM.xlsm"
   
#Open File
print('Get File '+ FileName)
GetFile(FileName)

iters = 10
i = 1

while (i<=iters):

    #set values
    PointCell('c10')
    SetNum(feedT)
    SetNum(feedP)
    SetNum(feedF)
    SetNum(feedetOHmolefrac)
    SetNum(feedH2Omolefrac)
    SetNum(flashT)
    SetNum(flashP)

    RunMacro()

    #wait until process complete
    time.sleep(dur)

    #check for correct answer
    duration = float(GetValue ('c6'))
    status = float (GetValue ('c7'))

    if (duration >= 0 and status == 0):

        print ("Pass- Duration = " + str(duration)+' Status = ' + str(status)+' '+time.asctime())
    else:
        print ("Fail- Duration = " + str(duration)+' Status = ' + str(status)+' '+time.asctime())
    
    # use random values values
    feedT=randrange(145,155,1)
    feedP=randrange(45,55,1)
    feedF=randrange(40000, 50000,1)*.001
    feedetOHmolefrac=randrange(8500,9500,1)*.00001
    feedH2Omolefrac=randrange(85000,95000,1)*.00001
    flashT=randrange(145,155,1)
    flashP=randrange(15,25,1)
    
    # Shorten Duration
    dur = 2

    i+=1
