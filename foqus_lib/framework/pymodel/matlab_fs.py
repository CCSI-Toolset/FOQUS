#FOQUS_PYMODEL_PLUGIN
#
from foqus_lib.framework.pymodel.pymodel import *
import matlab.engine
import time
import subprocess


def checkAvailable():
    return True


class pymodel_pg(pymodel):
    def __init__(self):
        pymodel.__init__(self)
        engs = matlab.engine.find_matlab()
        if len(engs) == 0 or 'MatlabEngine' not in engs:
            eng = subprocess.Popen("matlab -nosplash -minimize -r \"matlab.engine.shareEngine('MatlabEngine')\"")

    def run(self):
        no_matlab_engine = True
        while no_matlab_engine:
            if len(matlab.engine.find_matlab()) > 0:
                no_matlab_engine = False
        time.sleep(0.1)
