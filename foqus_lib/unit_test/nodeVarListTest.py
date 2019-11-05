from foqus_lib.framework.graph.nodeVars import nodeVarList
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
        l.addVariable(
            "N1",
            "V1",
            NodeVars(
                value = 1.0,
                vmin = 1.0,
                vmax = 10.0,
                vdflt = 3.0))
        l.addVariable(
            "N1",
            "V2",
            NodeVars(
                value = [1.0, 2.0, 3.0, 4.0, 5.0],
                vmin = [1.0, 1.0, 1.0, 1.0, 1.0],
                vmax = [25.0, 25.0, 25.0, 25.0, 25.0],
                vdflt = [11.0, 12.0, 13.0, 14.0, 15.0]))
        l.addVariable(
            "N2",
            "V1",
            NodeVars(
                value = 2.0,
                vmin = 1.0,
                vmax = 10.0,
                vdflt = 3.0))
        return l

    def makeTestList2(self):
        l = NodeVarList()
        l.addNode("N1")
        l.addVariable(
            "N1",
            "V1",
            NodeVars(
                value = 1.0,
                vmin = 1.0,
                vmax = 10.0,
                vdflt = 3.0))
        l.addVariable(
            "N1",
            "V2",
            NodeVars(
                value = [[1.0, 2.0], [3.0, 4.0]],
                vmin = [[1.0, 1.0], [1.0, 1.0]],
                vmax = [[25.0, 25.0], [25.0, 25.0]],
                vdflt = [[11.0, 12.0], [13.0, 14.0]]))
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

    def testGet4(self):
        l = self.makeTestList1()
        v = l.get("N1.V2")
        self.assertAlmostEqual(v.value[2], 3.0)

    def testFlatten1(self):
        l = self.makeTestList1()
        names = ["N1.V1", "N1.V2", "N2.V1"]
        v = l.getFlat(names)
        self.assertAlmostEqual(v[0], 1.0)
        self.assertAlmostEqual(v[1], 1.0)
        self.assertAlmostEqual(v[2], 2.0)
        self.assertAlmostEqual(v[3], 3.0)
        self.assertAlmostEqual(v[4], 4.0)
        self.assertAlmostEqual(v[5], 5.0)
        self.assertAlmostEqual(v[6], 2.0)

    def testFlatten2(self):
        l = self.makeTestList1()
        names = ["N1.V1", "N1.V2", "N2.V1"]
        l.get("N1.V1").scaling = 'Linear'
        l.get("N1.V2").scaling = 'Linear'
        l.get("N2.V1").scaling = 'Linear'
        v = l.getFlat(names, scaled = True)
        self.assertAlmostEqual(v[0], 0.0)
        self.assertAlmostEqual(v[1], 0.0)
        self.assertAlmostEqual(v[2], 0.416667, places=5)
        self.assertAlmostEqual(v[3], 0.833333, places=5)
        self.assertAlmostEqual(v[4], 1.250000, places=5)
        self.assertAlmostEqual(v[5], 1.666667, places=5)
        self.assertAlmostEqual(v[6], 1.111111, places=5)

    def testFlatten3(self):
        l = self.makeTestList1()
        names = ["N1.V1", "N1.V2"]
        v = l.getFlat(names)
        self.assertAlmostEqual(v[0], 1.0)
        self.assertAlmostEqual(v[1], 1.0)
        self.assertAlmostEqual(v[2], 2.0)
        self.assertAlmostEqual(v[3], 3.0)
        self.assertAlmostEqual(v[4], 4.0)

    def testFlatten4(self):
        l = self.makeTestList1()
        names = ["N1.V1", "N1.V2"]
        l.get("N1.V1").scaling = 'Linear'
        l.get("N1.V2").scaling = 'Linear'
        v = l.getFlat(names, scaled=True)
        self.assertAlmostEqual(v[0], 0.0)
        self.assertAlmostEqual(v[1], 0.0)
        self.assertAlmostEqual(v[2], 0.416667, places=5)
        self.assertAlmostEqual(v[3], 0.833333, places=5)
        self.assertAlmostEqual(v[4], 1.250000, places=5)

    def testUnFlatten1(self):
        l = self.makeTestList1()
        names = ["N1.V1", "N1.V2", "N2.V1"]
        values = [1.0, 1.0, 2.0, 3.0, 4.0, 5.0, 2.0]
        v = l.unflatten(names, values)
        self.assertAlmostEqual(v["N1"]["V1"], 1.0)
        self.assertAlmostEqual(v["N2"]["V1"], 2.0)
        self.assertAlmostEqual(v["N1"]["V2"][0], 1.0)
        self.assertAlmostEqual(v["N1"]["V2"][1], 2.0)
        self.assertAlmostEqual(v["N1"]["V2"][2], 3.0)
        self.assertAlmostEqual(v["N1"]["V2"][3], 4.0)
        self.assertAlmostEqual(v["N1"]["V2"][4], 5.0)

    def testUnFlatten2(self):
        l = self.makeTestList1()
        l.get("N1.V1").scaling = 'Linear'
        l.get("N1.V2").scaling = 'Linear'
        l.get("N2.V1").scaling = 'Linear'
        names = ["N1.V1", "N1.V2", "N2.V1"]
        values = [
            0.0,
            0.0,
            0.416667,
            0.833333,
            1.250000,
            1.666667,
            1.111111]
        v = l.unflatten(names, values, unScale=True)
        self.assertAlmostEqual(v["N1"]["V1"], 1.0, places=5)
        self.assertAlmostEqual(v["N2"]["V1"], 2.0, places=5)
        self.assertAlmostEqual(v["N1"]["V2"][0], 1.0, places=5)
        self.assertAlmostEqual(v["N1"]["V2"][1], 2.0, places=5)
        self.assertAlmostEqual(v["N1"]["V2"][2], 3.0, places=5)
        self.assertAlmostEqual(v["N1"]["V2"][3], 4.0, places=5)
        self.assertAlmostEqual(v["N1"]["V2"][4], 5.0, places=5)

    def testUnFlatten3(self):
        l = self.makeTestList2()
        names = ["N1.V1", "N1.V2"]
        values = [
            1.0,
            1.0,
            2.0,
            3.0,
            4.0]
        v = l.unflatten(names, values)
        self.assertAlmostEqual(v["N1"]["V1"], 1.0, places=5)
        self.assertAlmostEqual(v["N1"]["V2"][0][0], 1.0, places=5)
        self.assertAlmostEqual(v["N1"]["V2"][0][1], 2.0, places=5)
        self.assertAlmostEqual(v["N1"]["V2"][1][0], 3.0, places=5)
        self.assertAlmostEqual(v["N1"]["V2"][1][1], 4.0, places=5)

    def testUnFlatten4(self):
        l = self.makeTestList2()
        l.get("N1.V1").scaling = 'Linear'
        l.get("N1.V2").scaling = 'Linear'
        names = ["N1.V1", "N1.V2"]
        values = [
            0.0,
            0.0,
            0.416667,
            0.833333,
            1.250000]
        v = l.unflatten(names, values, unScale=True)
        self.assertAlmostEqual(v["N1"]["V1"], 1.0, places=5)
        self.assertAlmostEqual(v["N1"]["V2"][0][0], 1.0, places=5)
        self.assertAlmostEqual(v["N1"]["V2"][0][1], 2.0, places=5)
        self.assertAlmostEqual(v["N1"]["V2"][1][0], 3.0, places=5)
        self.assertAlmostEqual(v["N1"]["V2"][1][1], 4.0, places=5)
