#  This script just makes python files from the Qt resource files
#  and UI files.  This can be run if anything is changed, icons, help
#  files, ui files.  This isn't needed by the end used, just for development
#  to make things  slightly easier.

import subprocess
import time
import sys
import os

# pyside command paths
pyside_rcc = 'c:\Python27\Lib\site-packages\PySide\pyside-rcc'
#pyside_rcc = 'pyside-rcc'
pyside_uic = 'c:\Python27\scripts\pyside-uic'

ofiles = {
    "Dash_UI": "main",
    "gatewayUploadDialog_UI": "model",
    "modelSetupDialog_UI": "model",
    "edgePanel_UI": "flowsheet",
    "nodePanel_UI": "flowsheet",
    "optMonitor_UI": "optimization",
    "optSetupFrame_UI": "optimization",
    "optMessageWindow_UI": "optimization",
    "sessionDescriptionEdit_UI": "main",
    "helpBrowser_UI": "help",
    "variableBrowser_UI": "dialogs",
    "turbineConfig_UI": "main",
    "alamoSetupFrame_UI": "alamo",
    "flowsheetSettingsDialog_UI": "flowsheet",
    "logSettingsDialog_UI": "main",
    "tagSelectDialog_UI": "dialogs",
    "dataBrowserDialog_UI": "flowsheet",
    "dataFilterDialog_UI": "flowsheet",
    #"Preview_UI": "uq",
    #"SimSetup_UI": "uq",
    #"updateUQModelDialog_UI": "uq",
    #"uqSetupFrame_UI": "uq"
    }

def buildUI(name):
    ui_file = os.path.join(ofiles[name], name) + ".ui"
    py_file = os.path.join(ofiles[name], name) + ".py"
    args = [pyside_uic, ui_file, "-o", py_file]
    process = subprocess.Popen(args, cwd = "gui")
    process.wait()
    # since I moved the ui stuff to sub directories of gui
    # and I still want to import the icon file from foqus_qui
    # I need this work around.  I have yet to figure out a better
    # way. I just replace 
    #    import icons_rc 
    #      with 
    #    import foqus_lib.gui.icons_rc as icons_rc
    # in the generated python that I an not supposed to edit
    py_file = os.path.join("gui", py_file)
    with open (py_file, "r") as f:
        content = f.read().replace(
            'import icons_rc',
            'import foqus_lib.gui.icons_rc as icons_rc')
    with open (py_file, "w") as f:
        f.write(content)
        
if sys.argv[1] == 'icons':
    process = subprocess.Popen(
        [pyside_rcc, 'icons.qrc', '-o','icons_rc.py'], 
        cwd = 'gui')
    process.wait()
elif sys.argv[1] == 'all':
    for key, item in ofiles.iteritems():
        buildUI(key)
else:
    if sys.argv[1] in ofiles:
        buildUI(sys.argv[1])



