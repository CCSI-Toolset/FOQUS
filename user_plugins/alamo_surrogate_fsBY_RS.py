#FOQUS_PYMODEL_PLUGIN
#
# ALAMO surrogate export
# THIS FILE WAS AUTOMATICALLY GENERATED.
#
# ALAMO Model for Flowsheet
import numpy
import scipy
import subprocess
from math import *
from foqus_lib.framework.pymodel.pymodel import *
from foqus_lib.framework.graph.nodeVars import *

def checkAvailable():
    return True

class pymodel_pg(pymodel):
    def __init__(self):
        pymodel.__init__(self)
        self.inputs['samples.X1'] = NodeVars(
            value = 0.0,
            vmin = 3000.0,
            vmax = 13000.0,
            vdflt = 0.0,
            unit = "",
            vst = "pymodel",
            vdesc = "",
            tags = [],
            dtype = float)
        self.inputs['samples.X10'] = NodeVars(
            value = 0.0,
            vmin = -8169.735,
            vmax = -7392.909,
            vdflt = 0.0,
            unit = "",
            vst = "pymodel",
            vdesc = "",
            tags = [],
            dtype = float)
        self.inputs['samples.X11'] = NodeVars(
            value = 0.0,
            vmin = 2.0,
            vmax = 4.8,
            vdflt = 0.0,
            unit = "",
            vst = "pymodel",
            vdesc = "",
            tags = [],
            dtype = float)
        self.inputs['samples.X12'] = NodeVars(
            value = 0.0,
            vmin = 0.3,
            vmax = 7.83,
            vdflt = 0.0,
            unit = "",
            vst = "pymodel",
            vdesc = "",
            tags = [],
            dtype = float)
        self.inputs['samples.X13'] = NodeVars(
            value = 0.0,
            vmin = -3492.289,
            vmax = -1059.27,
            vdflt = 0.0,
            unit = "",
            vst = "pymodel",
            vdesc = "",
            tags = [],
            dtype = float)
        self.inputs['samples.X14'] = NodeVars(
            value = 0.0,
            vmin = 1.3,
            vmax = 1.61381,
            vdflt = 0.0,
            unit = "",
            vst = "pymodel",
            vdesc = "",
            tags = [],
            dtype = float)
        self.inputs['samples.X15'] = NodeVars(
            value = 0.0,
            vmin = -1.0,
            vmax = 1.0,
            vdflt = 0.0,
            unit = "",
            vst = "pymodel",
            vdesc = "",
            tags = [],
            dtype = float)
        self.inputs['samples.X16'] = NodeVars(
            value = 0.0,
            vmin = 7.849999,
            vmax = 15.12,
            vdflt = 0.0,
            unit = "",
            vst = "pymodel",
            vdesc = "",
            tags = [],
            dtype = float)
        self.inputs['samples.X17'] = NodeVars(
            value = 0.0,
            vmin = 0.3599,
            vmax = 0.92,
            vdflt = 0.0,
            unit = "",
            vst = "pymodel",
            vdesc = "",
            tags = [],
            dtype = float)
        self.inputs['samples.X2'] = NodeVars(
            value = 0.0,
            vmin = 1000.0,
            vmax = 3000.0,
            vdflt = 0.0,
            unit = "",
            vst = "pymodel",
            vdesc = "",
            tags = [],
            dtype = float)
        self.inputs['samples.X3'] = NodeVars(
            value = 0.0,
            vmin = 0.1,
            vmax = 0.176,
            vdflt = 0.0,
            unit = "",
            vst = "pymodel",
            vdesc = "",
            tags = [],
            dtype = float)
        self.inputs['samples.X4'] = NodeVars(
            value = 0.0,
            vmin = 0.1,
            vmax = 0.35,
            vdflt = 0.0,
            unit = "",
            vst = "pymodel",
            vdesc = "",
            tags = [],
            dtype = float)
        self.inputs['samples.X5'] = NodeVars(
            value = 0.0,
            vmin = -191640500.0,
            vmax = -188900000.0,
            vdflt = 0.0,
            unit = "",
            vst = "pymodel",
            vdesc = "",
            tags = [],
            dtype = float)
        self.inputs['samples.X6'] = NodeVars(
            value = 0.0,
            vmin = -493916400.0,
            vmax = -490361700.0,
            vdflt = 0.0,
            unit = "",
            vst = "pymodel",
            vdesc = "",
            tags = [],
            dtype = float)
        self.inputs['samples.X7'] = NodeVars(
            value = 0.0,
            vmin = -337842600.0,
            vmax = -322820000.0,
            vdflt = 0.0,
            unit = "",
            vst = "pymodel",
            vdesc = "",
            tags = [],
            dtype = float)
        self.inputs['samples.X8'] = NodeVars(
            value = 0.0,
            vmin = -699941900.0,
            vmax = -681019600.0,
            vdflt = 0.0,
            unit = "",
            vst = "pymodel",
            vdesc = "",
            tags = [],
            dtype = float)
        self.inputs['samples.X9'] = NodeVars(
            value = 0.0,
            vmin = 27.54205,
            vmax = 30.16494,
            vdflt = 0.0,
            unit = "",
            vst = "pymodel",
            vdesc = "",
            tags = [],
            dtype = float)
        self.inputvals = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.outputs['samples.Y1'] = NodeVars(
            value = 0.0,
            vmin = 0.0,
            vmax = 0.0,
            vdflt = 0.0,
            unit = "",
            vst = "pymodel",
            vdesc = "",
            tags = [],
            dtype = float)

    def run(self):
        self.outputs['samples.Y1'].value = 0.20535883157691607603379E-001 * self.inputs['samples.X1'].value + 0.22092142675737325846486E-001 * self.inputs['samples.X10'].value - 0.89370697863338366406794 * self.inputs['samples.X11'].value + 0.52392435165178008471543 * self.inputs['samples.X12'].value - 0.29456210485289194278558E-002 * self.inputs['samples.X13'].value + 4.5519124535115391694262 * self.inputs['samples.X14'].value + 0.86154716704330017162938E-001 * self.inputs['samples.X16'].value + 10.881504157214754613392 * self.inputs['samples.X17'].value - 0.67459511599064797549019E-001 * self.inputs['samples.X2'].value - 411.39620943553217102817 * self.inputs['samples.X3'].value - 250.51258170029498728582 * self.inputs['samples.X4'].value - 0.51873940815071121719567E-006 * self.inputs['samples.X5'].value + 0.33081517977826660601134E-006 * self.inputs['samples.X6'].value + 0.56892537070093651063521E-010 * self.inputs['samples.X7'].value - 0.62810982181409820530399E-007 * self.inputs['samples.X8'].value + 21.446715832668029833030 * self.inputs['samples.X9'].value - 0.89077510291370852891623E-006 * self.inputs['samples.X1'].value**2 + 0.10893231984449393892476E-005 * self.inputs['samples.X10'].value**2 - 0.21781927382043814178658 * self.inputs['samples.X12'].value**2 - 0.39887811249967158068114E-006 * self.inputs['samples.X13'].value**2 - 12.567077503005169347716 * self.inputs['samples.X17'].value**2 + 0.82942294676496348726545E-005 * self.inputs['samples.X2'].value**2 + 245.93300227786497202942 * self.inputs['samples.X3'].value**2 + 575.29734276562737704808 * self.inputs['samples.X4'].value**2 - 0.34436370626945789208406 * self.inputs['samples.X9'].value**2 + 0.15802496991317822178091E-001 * self.inputs['samples.X12'].value**3 - 1661.1073957937724117073 * self.inputs['samples.X4'].value**3
