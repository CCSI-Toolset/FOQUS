#
#FOQUS_PYMODEL_PLUGIN

import numpy
from foqus_lib.framework.pymodel.pymodel import *
from foqus_lib.framework.graph.nodeVars import *

def checkAvailable():
    '''
        Plugins should have this function to check availability of any
        additional required software.  If requirements are not available
        plugin will not be available.
    '''
    return True

class pymodel_pg(pymodel):
    def __init__(self):
        pymodel.__init__(self)
        self.inputs['x1'] = NodeVars(
            value = 1.0,
            vmin = 0.0,
            vmax = 10.0,
            vdflt = 1.0,
            unit = "",
            vst = "pymodel",
            vdesc = "Test 1",
            tags = [],
            dtype = float)
        self.inputs['x2'] = NodeVars(
            value = 1.0,
            vmin = 0.0,
            vmax = 10.0,
            vdflt = 1.0,
            unit = "",
            vst = "pymodel",
            vdesc = "Test 2",
            tags = [],
            dtype = float)
        self.outputs['y'] = NodeVars(
            vdesc = 'test out',
            dtype = float)

    def run(self):
        y = self.inputs['x1'].value + self.inputs['x2'].value
        self.outputs['y'].value = y
