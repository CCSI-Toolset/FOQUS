#################################################################################
# FOQUS Copyright (c) 2012 - 2023, by the software owners: Oak Ridge Institute
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
#################################################################################
from foqus_lib.framework.graph.nodeVars import *
import traceback
import unittest
import copy
import numpy
import json


class testNodeVarsSteady(unittest.TestCase):
    # Used assertAlmostEqual here a lot because I'm concerned about
    # using equal on floating points
    def makeVar(self):
        return NodeVars(value=2.5, vmin=1.0, vmax=10.0, vdflt=3.0)

    def testValue(self):
        var = self.makeVar()
        self.assertAlmostEqual(var.value, 2.5)

    def testDefault(self):
        var = self.makeVar()
        self.assertAlmostEqual(var.default, 3.0)

    def testSetValue(self):
        var = self.makeVar()
        x = 4.27
        var.value = x
        self.assertAlmostEqual(var.value, x)

    def testConvertInt(self):
        var = self.makeVar()
        var.setType(int)
        self.assertEqual(var.value, 2)

    def testConvertInt2(self):
        var = self.makeVar()
        var.value = 2.55
        r = round(var.value)
        self.assertEqual(r, 3)

    def testCopy(self):
        var = self.makeVar()
        var2 = copy.copy(var)
        self.assertAlmostEqual(var2.value, 2.5)

    def testDeepCopy(self):
        var = self.makeVar()
        var2 = copy.deepcopy(var)
        self.assertAlmostEqual(var2.value, 2.5)

    def testSaveDict(self):
        var = self.makeVar()
        d = var.saveDict()
        self.assertAlmostEqual(d["max"], 10.0)
        self.assertAlmostEqual(d["min"], 1.0)
        self.assertEqual(d["dtype"], "float")

    def testSaveJSON(self):
        var = self.makeVar()
        d = var.saveDict()
        x = json.dumps(d)

    def testloadDict(self):
        var = self.makeVar()
        d = var.saveDict()
        var.loadDict(d)
        self.assertEqual(var.dtype, float)

    def testLoadJSON(self):
        var = self.makeVar()
        d = var.saveDict()
        x = json.dumps(d)
        x = json.loads(x)
        var.loadDict(x)
        self.assertEqual(var.dtype, float)

    def testScaleLinear(self):
        var = self.makeVar()
        var.min = 1
        var.max = 25
        var.value = 4.12
        var.scaling = "Linear"
        var.scale()
        self.assertAlmostEqual(var.scaled, 1.3)

    def testScaleLog(self):
        var = self.makeVar()
        var.min = 1
        var.max = 25
        var.value = 4.12
        var.scaling = "Log"
        var.scale()
        self.assertAlmostEqual(var.scaled, 4.3986, places=3)

    def testScalePower(self):
        var = self.makeVar()
        var.min = 0
        var.max = 2
        var.value = 0.2
        var.scaling = "Power"
        var.scale()
        self.assertAlmostEqual(var.scaled, 0.0591, places=3)

    def testScaleLog2(self):
        var = self.makeVar()
        var.min = 1
        var.max = 25
        var.value = 4.12
        var.scaling = "Log 2"
        var.scale()
        self.assertAlmostEqual(var.scaled, 3.3646, places=3)

    def testScalePower2(self):
        var = self.makeVar()
        var.min = 1
        var.max = 25
        var.value = 4.12
        var.scaling = "Power 2"
        var.scale()
        self.assertAlmostEqual(var.scaled, 0.3877, places=3)

    def testUnScaleLinear(self):
        var = self.makeVar()
        var.min = 1
        var.max = 25
        var.scaled = 1.3
        var.scaling = "Linear"
        var.unscale()
        self.assertAlmostEqual(var.value, 4.12)

    def testUnScaleLog(self):
        var = self.makeVar()
        var.min = 1
        var.max = 25
        var.scaled = 4.3986
        var.scaling = "Log"
        var.unscale()
        self.assertAlmostEqual(var.value, 4.12, places=3)

    def testUnScalePower(self):
        var = self.makeVar()
        var.min = 0
        var.max = 2
        var.scaled = 0.059080120451
        var.scaling = "Power"
        var.unscale()
        self.assertAlmostEqual(var.value, 0.2, places=3)

    def testUnScaleLog2(self):
        var = self.makeVar()
        var.min = 1
        var.max = 25
        var.scaled = 3.3646
        var.scaling = "Log 2"
        var.unscale()
        self.assertAlmostEqual(var.value, 4.12, places=3)

    def testUnScalePower2(self):
        var = self.makeVar()
        var.min = 1
        var.max = 25
        var.scaled = 0.3877365362129
        var.scaling = "Power 2"
        var.unscale()
        self.assertAlmostEqual(var.value, 4.12, places=3)
