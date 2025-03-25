#################################################################################
# FOQUS Copyright (c) 2012 - 2025, by the software owners: Oak Ridge Institute
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
import copy
import json
import unittest

from foqus_lib.framework.graph.nodeVars import NodeVars


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
        var.min = 2
        var.max = 25
        var.value = 4.12
        var.scaling = "Linear"
        var.scale()
        self.assertAlmostEqual(var.scaled, 0.9217, places=3)

    def testScaleLog(self):
        var = self.makeVar()
        var.min = 2
        var.max = 25
        var.value = 4.12
        var.scaling = "Log"
        var.scale()
        self.assertAlmostEqual(var.scaled, 2.8614, places=3)

    def testScalePower(self):
        var = self.makeVar()
        var.min = 0.1
        var.max = 2
        var.value = 0.2
        var.scaling = "Power"
        var.scale()
        self.assertAlmostEqual(var.scaled, 0.0330, places=3)

    def testScaleLog2(self):
        var = self.makeVar()
        var.min = 2
        var.max = 25
        var.value = 4.12
        var.scaling = "Log 2"
        var.scale()
        self.assertAlmostEqual(var.scaled, 2.6235, places=3)

    def testScalePower2(self):
        var = self.makeVar()
        var.min = 2
        var.max = 25
        var.value = 4.12
        var.scaling = "Power 2"
        var.scale()
        self.assertAlmostEqual(var.scaled, 0.2627, places=3)

    def testUnScaleLinear(self):
        var = self.makeVar()
        var.min = 2
        var.max = 25
        var.scaled = 0.9217
        var.scaling = "Linear"
        var.unscale()
        self.assertAlmostEqual(var.value, 4.12, places=3)

    def testUnScaleLog(self):
        var = self.makeVar()
        var.min = 2
        var.max = 25
        var.scaled = 2.8614
        var.scaling = "Log"
        var.unscale()
        self.assertAlmostEqual(var.value, 4.12, places=3)

    def testUnScalePower(self):
        var = self.makeVar()
        var.min = 0.1
        var.max = 2
        var.scaled = 0.0330
        var.scaling = "Power"
        var.unscale()
        self.assertAlmostEqual(var.value, 0.2, places=3)

    def testUnScaleLog2(self):
        var = self.makeVar()
        var.min = 2
        var.max = 25
        var.scaled = 2.6235
        var.scaling = "Log 2"
        var.unscale()
        self.assertAlmostEqual(var.value, 4.12, places=3)

    def testUnScalePower2(self):
        var = self.makeVar()
        var.min = 2
        var.max = 25
        var.scaled = 0.2627
        var.scaling = "Power 2"
        var.unscale()
        self.assertAlmostEqual(var.value, 4.12, places=3)
