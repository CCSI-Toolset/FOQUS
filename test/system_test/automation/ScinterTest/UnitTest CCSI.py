###############################################################################
#           Automated Test of CCSIUnits for Scinter
#           Runs on Excel 2010
#           Uses Python 2.7, pywinauto 0.4.3
#           Gregory Pope, LLNL
#           April 12, 2013
#           For Acceptance Testing Scinter CCSIUnits
#           V1.0
###############################################################################
import pywinauto
from pywinauto import clipboard
import time
from random import *

pwa_app = pywinauto.application.Application()


def StartAp():
    # Start Application
    pwa_app.start_("C:\Program Files (x86)\Microsoft Office\Office14\EXCEL.EXE")
    print ('Started Application')
    return

def GetFile(FileName):
    #Get needed file
    print('Get needed file')
    w_handle = pywinauto.timings.WaitUntilPasses(30,0.5,lambda: pywinauto.findwindows.find_windows(title=u'Microsoft Excel - Book1', class_name='XLMAIN')[0])
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
    w_handle = pywinauto.timings.WaitUntilPasses(30,0.5,lambda: pywinauto.findwindows.find_windows(title=u'Microsoft Excel - UnitConverterTest.xlsm  [Read-Only]', class_name='XLMAIN')[0])
    window = pwa_app.window_(handle=w_handle)
    window.SetFocus()
    ctrl = window['11']
    ctrl.SetFocus()
    ctrl.TypeKeys(cell+'{ENTER}')
    time.sleep(1)
    return

def GetValue(cell):
    w_handle = pywinauto.timings.WaitUntilPasses(30,0.5,lambda: pywinauto.findwindows.find_windows(title=u'Microsoft Excel - UnitConverterTest.xlsm  [Read-Only]', class_name='XLMAIN')[0])
    window = pwa_app.window_(handle=w_handle)
    window.SetFocus()
    window.TypeKeys('^c')
    time.sleep(.75)
    value=pywinauto.clipboard.GetData(format=13)
    window.TypeKeys('{ESC}')
    time.sleep(.5)
    return(value)
    

def SetNum(value):
    #Set number to be coverted
    print('Run in grid area, value = '+ str(value))
    w_handle = pywinauto.timings.WaitUntilPasses(30,0.5,lambda: pywinauto.findwindows.find_windows(title=u'Microsoft Excel - UnitConverterTest.xlsm  [Read-Only]', class_name='XLMAIN')[0])
    window = pwa_app.window_(handle=w_handle)
    window.SetFocus()
    ctrl = window['13']
    ctrl.SetFocus()
    ctrl.TypeKeys(str(value)+'{ENTER}')

def SetConvert(ConvFrom,ConvTo):
    #Run conversion
    print('Set From ' + ConvFrom + ' To ' + ConvTo)
    w_handle = pywinauto.timings.WaitUntilPasses(30,0.5,lambda: pywinauto.findwindows.find_windows(title=u'Microsoft Excel - UnitConverterTest.xlsm  [Read-Only]', class_name='XLMAIN')[0])
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
    w_handle = pywinauto.timings.WaitUntilPasses(30,0.5,lambda: pywinauto.findwindows.find_windows(title=u'Microsoft Excel - UnitConverterTest.xlsm  [Read-Only]', class_name='XLMAIN')[0])
    window = pwa_app.window_(handle=w_handle)
    window.SetFocus()
    window.TypeKeys('%{F8}')
    w_handle = pywinauto.timings.WaitUntilPasses(20,0.5,lambda: pywinauto.findwindows.find_windows(title=u'Macro', class_name='bosa_sdm_XL9')[0])
    window = pwa_app.window_(handle=w_handle)
    window.SetFocus()
    window.TypeKeys('%r')
    return

#Main Program
iters=100       # max iterations
inc=1       # step size
num=1           # loop counter
index = 0       # conversion type index
value = 1        # intial value to be converted
tolerance = 4   # round difference to this decimal place
minvalue = -10000 # minimum value to convert
maxvalue = 10000  # maximum number to convert

#Conversion Formulas
def Conversion(index,value):
    if   index == 0: return value*.0254 #knovel(16)
    elif index == 1: return value*39.37007874015750 #knovel(16)
    elif index == 2: return (value-32.)*5./9.
    elif index == 3: return value*9./5.+32.
    elif index == 4: return value*2.204622621848780 #knovel(16)
    elif index == 5: return value*0.45359237 #knovel(16)
    elif index == 6: return value*0.001341022089563140  #knovel(16)
    elif index == 7: return value*745.6998715823 #Mech/Hyd. 746(elec) 735.49875(metric) #knovel(16)
    elif index == 8: return value*68.94757293  #knovel(16) #68.947572932
    elif index == 9: return value*0.01450377377337510 #knovel(16)
    elif index == 10: return value*0.01745329252088220  #knovel(16)
    elif index == 11: return value*57.29577951#knovel(16)
    elif index == 12: return value*0.09290304 #knovel(16)
    elif index == 13: return value*10.76391041670970 #knovel(16)
    elif index == 14: return value*0.2388458966275 #calorie (IT)
    elif index == 15: return value*4.1868 #4.1858(15C),4.1868(IT), 4186.8(nutr), 4.184 (TC) #knovel(16)
    elif index == 16: return value*0.000145037737733751 #knovel(16)
    elif index == 17: return value*6894.757293 #knovel(16)
    elif index == 18: return value*1.333223684 #knovel(16)
    elif index == 19: return value*0.75006168282261 #knovel(16)
    elif index == 20: return value*0.0009869232667160130 #knovel(16)
    elif index == 21: return value*1013.25  #knovel(16)
    elif index == 22: return value*13.59509806316 #Unit Conv
    elif index == 23: return value*.07355592400691 #Unit conv
    elif index == 24: return value*1055.056 #Unit conv
    elif index == 25: return value*0.0009478169879134 #Unit conv
    elif index >= 26: print ('index error =' +index)
    return


ConvFrom = [
            'inch',
            'meters',
            'degF',
            'degC',
            'kg',
            'pounds',
            'watts',
            'hp',
            'psi',
            'millibar',
            'degree',
            'radian',
            'ft2',
            'm2',
            'joule',
            'calorie',
            'pascal',
            'psi',
            'torr',
            'hectopascal',
            'millibar',
            'atmosphere',
            'mmhg',
            'kgf/m2',
            'btu/s',
            'watt'
            ]

ConvTo =   [
            'meters',
            'inches',
            'degC',
            'degF',
            'pounds',
            'kg',
            'hp',
            'watts',
            'millibar',
            'psi',
            'radian',
            'degree',
            'm2',
            'ft2',
            'calorie',
            'joule',
            'psi',
            'pascal',
            'hectopascal',
            'torr',
            'atmosphere',
            'millibar',
            'kgf/m2',
            'mmhg',
            'watt',
            'btu/s'
            ]


StartAp()
FileName="C:\Program Files {(}x86{)}\Berkeley Water Center\CCSIUnits\UnitConverterTest.xlsm"
GetFile(FileName)

#Try a bunch (iters worth) of random conversion types and values      


while (num<=iters):
        cell='b1'
        PointCell(cell)
        SetNum(value)
        SetConvert(ConvFrom [index],ConvTo[index])
        RunMacro()
        actual = float(GetValue(cell))
        expected = float(Conversion(index,value))
        diff = round (actual-expected,tolerance)
        percent = (diff/actual)*100
        if (abs(diff) <= .001):
            print('Pass- '+'actual= '+str(actual)+' expected= '+str(expected)+' diff = '+str(diff))
        else:
            print('\nFail- '+'actual= '+str(actual)+' expected= '+str(expected)+' diff = '+str(diff)+'\n')
                
        num =num+inc
        #Pick random value for conversion
        value = randrange(minvalue,maxvalue,1)
        #Pick random conversion pair
        index = randrange(0,26,1)
        print (index)


