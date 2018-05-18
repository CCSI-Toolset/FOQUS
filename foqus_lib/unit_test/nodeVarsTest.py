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
        return NodeVars(
            value = 2.5,
            vmin = 1.0,
            vmax = 10.0,
            vdflt = 3.0)

    def makeVarVec(self):
        return NodeVars(
            value = [1.0, 2.0, 3.0, 4.0, 5.0],
            vmin = [1.0, 1.0, 1.0, 1.0, 1.0],
            vmax = [25.0, 25.0, 25.0, 25.0, 25.0],
            vdflt = [11.0, 12.0, 13.0, 14.0, 15.0])

    def testValue(self):
        var = self.makeVar()
        self.assertAlmostEqual(var.value, 2.5)

    def testValue2(self):
        var = self.makeVarVec()
        v = var.value
        self.assertAlmostEqual(v[0], 1.0)
        self.assertAlmostEqual(v[1], 2.0)
        self.assertAlmostEqual(v[2], 3.0)
        self.assertAlmostEqual(v[3], 4.0)
        self.assertAlmostEqual(v[4], 5.0)

    def testDefault(self):
        var = self.makeVar()
        self.assertAlmostEqual(var.default, 3.0)

    def testDefault2(self):
        var = self.makeVarVec()
        v = var.default
        self.assertAlmostEqual(v[0], 11.0)
        self.assertAlmostEqual(v[1], 12.0)
        self.assertAlmostEqual(v[2], 13.0)
        self.assertAlmostEqual(v[3], 14.0)
        self.assertAlmostEqual(v[4], 15.0)

    def testSetValue(self):
        var = self.makeVar()
        x = 4.27
        var.value = x
        self.assertAlmostEqual(var.value, x)

    def testSetTimeStepOutOfBounds(self):
        var = self.makeVar()
        with self.assertRaises(nodeVarEx) as cm:
            var.setTimeStep(2)
        e = cm.exception
        self.assertEqual(e.code, 22)

    def testSetTimeStepNegative(self):
        # This should not be an error it is the last
        # and only time step
        var = self.makeVar()
        var.setTimeStep(-1)

    def testSetTimeStepNegative2(self):
        # This should be an error it is the second to last
        # time step, and there is no second to last time step in
        # this case
        var = self.makeVar()
        with self.assertRaises(nodeVarEx) as cm:
            var.setTimeStep(-2)
        e = cm.exception
        self.assertEqual(e.code, 22)

    def testSetShape0(self):
        # set a scalar shape
        var = self.makeVar()
        var.setShape(())
        self.assertAlmostEqual(var.value, 2.5)

    def testSetShape1(self):
        # set a scalar shape
        var = self.makeVar()
        var.setShape((1,))
        self.assertAlmostEqual(var.value, 2.5)

    def testSetShape2(self):
        # set a shape
        var = self.makeVar()
        var.setShape((2,))
        self.assertAlmostEqual(var.value[0], 2.5)

    def testSetShape3(self):
        # set a shape and set the value, this should not cause an
        # error
        var = self.makeVar()
        var.setShape((2,))
        var.value = [2,2]

    def testSetShape4(self):
        # set a scalar shape and value
        var = self.makeVar()
        var.setShape(())
        var.value = 2.0

    def testSetShape5(self):
        # set a one element vector shape and value
        var = self.makeVar()
        var.setShape((1,))
        var.value = [2.0]

    def testSetShape6(self):
        # set am array shape and values
        var = self.makeVar()
        var.setShape((2,2))
        var.value = [[2.1, 2.2], [2.3, 2.4]]
        self.assertAlmostEqual(var.value[0][0], 2.1)
        self.assertAlmostEqual(var.value[0][1], 2.2)
        self.assertAlmostEqual(var.value[1][0], 2.3)
        self.assertAlmostEqual(var.value[1][1], 2.4)

    def testSetShape7(self):
        # set an array shape and try to set with something with wrong
        # shape, should raise an exception
        var = self.makeVar()
        var.setShape((2,2))
        with self.assertRaises(nodeVarEx) as cm:
            var.value = [[2.1, 2.2], [2.3]]
        e = cm.exception
        self.assertEqual(e.code, 0)

    def testConvertInt(self):
        var = self.makeVar()
        var.setType(int)
        self.assertEqual(var.value, 2)

    def testConvertInt2(self):
        var = self.makeVar()
        var.value = 2.55
        var.toIntRound()
        self.assertEqual(var.value, 3)

    def testRoundValueInt(self):
        var = self.makeVar()
        var.value = 2.55
        var.roundValueInt()
        self.assertAlmostEqual(var.value, 3.0)

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
        self.assertAlmostEqual(d['max'], 10.0)
        self.assertAlmostEqual(d['min'], 1.0)
        self.assertEqual(d['ts'], 0)
        self.assertAlmostEqual(d['hist'][0], 2.5)
        self.assertEqual(d['shape'], ())
        self.assertEqual(d['dtype'], 'float')

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
        var.scaling = 'Linear'
        var.scale()
        self.assertAlmostEqual(var.scaled, 1.3)

    def testScaleLog(self):
        var = self.makeVar()
        var.min = 1
        var.max = 25
        var.value = 4.12
        var.scaling = 'Log'
        var.scale()
        self.assertAlmostEqual(var.scaled, 4.3986, places=3)

    def testScalePower(self):
        var = self.makeVar()
        var.min = 0
        var.max = 2
        var.value = 0.2
        var.scaling = 'Power'
        var.scale()
        self.assertAlmostEqual(var.scaled, 0.0591, places=3)

    def testScaleLog2(self):
        var = self.makeVar()
        var.min = 1
        var.max = 25
        var.value = 4.12
        var.scaling = 'Log 2'
        var.scale()
        self.assertAlmostEqual(var.scaled, 3.3646, places=3)

    def testScalePower2(self):
        var = self.makeVar()
        var.min = 1
        var.max = 25
        var.value = 4.12
        var.scaling = 'Power 2'
        var.scale()
        self.assertAlmostEqual(var.scaled, 0.3877, places=3)

    def testUnScaleLinear(self):
        var = self.makeVar()
        var.min = 1
        var.max = 25
        var.scaled = 1.3
        var.scaling = 'Linear'
        var.unscale()
        self.assertAlmostEqual(var.value, 4.12)

    def testUnScaleLog(self):
        var = self.makeVar()
        var.min = 1
        var.max = 25
        var.scaled = 4.3986
        var.scaling = 'Log'
        var.unscale()
        self.assertAlmostEqual(var.value, 4.12, places=3)

    def testUnScalePower(self):
        var = self.makeVar()
        var.min = 0
        var.max = 2
        var.scaled = 0.059080120451
        var.scaling = 'Power'
        var.unscale()
        self.assertAlmostEqual(var.value, 0.2, places=3)

    def testUnScaleLog2(self):
        var = self.makeVar()
        var.min = 1
        var.max = 25
        var.scaled = 3.3646
        var.scaling = 'Log 2'
        var.unscale()
        self.assertAlmostEqual(var.value, 4.12, places=3)

    def testUnScalePower2(self):
        var = self.makeVar()
        var.min = 1
        var.max = 25
        var.scaled = 0.3877365362129
        var.scaling = 'Power 2'
        var.unscale()
        self.assertAlmostEqual(var.value, 4.12, places = 3)
