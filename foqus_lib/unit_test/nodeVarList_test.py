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


class testNodeVarListSteady(unittest.TestCase):
    def makeTestList1(self):
        l = NodeVarList()
        l.addNode("N1")
        l.addNode("N2")
        l.addVariable("N1", "V1", NodeVars(value=1.0, vmin=1.0, vmax=10.0, vdflt=3.0))

        l.addVariable("N2", "V1", NodeVars(value=2.0, vmin=1.0, vmax=10.0, vdflt=3.0))
        return l

    def testGet1(self):
        l = self.makeTestList1()
        v = l.get("N1", "V1")
        self.assertAlmostEqual(v.value, 1.0)

    def testGet2(self):
        l = self.makeTestList1()
        v = l.get("N1.V1")
        self.assertAlmostEqual(v.value, 1.0)

    def testGet3(self):
        l = self.makeTestList1()
        v = l.get("N2.V1")
        self.assertAlmostEqual(v.value, 2.0)

    def testFlatten1(self):
        l = self.makeTestList1()
        names = ["N1.V1", "N2.V1"]
        v = l.getFlat(names)
        self.assertAlmostEqual(v[0], 1.0)
        self.assertAlmostEqual(v[1], 2.0)

    def testFlatten2(self):
        l = self.makeTestList1()
        names = ["N1.V1", "N2.V1"]
        l.get("N1.V1").scaling = "Linear"
        l.get("N2.V1").scaling = "Linear"
        v = l.getFlat(names, scaled=True)
        self.assertAlmostEqual(v[0], 0.0)
        self.assertAlmostEqual(v[1], 1.111111, places=5)

    def testUnFlatten1(self):
        l = self.makeTestList1()
        names = ["N1.V1", "N2.V1"]
        values = [1.0, 2.0]
        v = l.unflatten(names, values)
        self.assertAlmostEqual(v["N1"]["V1"], 1.0)
        self.assertAlmostEqual(v["N2"]["V1"], 2.0)

    def testUnFlatten2(self):
        l = self.makeTestList1()
        l.get("N1.V1").scaling = "Linear"
        l.get("N2.V1").scaling = "Linear"
        names = ["N1.V1", "N2.V1"]
        values = [0.0, 1.111111]
        v = l.unflatten(names, values, unScale=True)
        self.assertAlmostEqual(v["N1"]["V1"], 1.0, places=5)
        self.assertAlmostEqual(v["N2"]["V1"], 2.0, places=5)
