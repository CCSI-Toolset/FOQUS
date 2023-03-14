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
from foqus_lib.framework.graph.graph import *
import traceback
import unittest
import copy
import numpy
import json
import os


class testMassBalance(unittest.TestCase):
    def loadGraph(self, fname):
        gr = Graph()
        testfile = os.path.join(os.path.dirname(__file__), fname)
        with open(testfile, "r") as f:
            sd = json.load(f)
        gr.loadDict(sd["flowsheet"])
        return gr

    def testDirect1(self):
        gr = self.loadGraph("data/Mass_Bal_Test_01.json")
        gr.tearSolver = "Direct"
        gr.solve()
        x1 = gr.output["Sep"]["FA_2"].value
        x2 = gr.output["Sep"]["FB_2"].value
        err = numpy.abs(1.0 - x1 - x2)
        self.assertLess(err, 0.001)

    def testWegstein1(self):
        gr = self.loadGraph("data/Mass_Bal_Test_01.json")
        gr.tearSolver = "Wegstein"
        gr.solve()
        x1 = gr.output["Sep"]["FA_2"].value
        x2 = gr.output["Sep"]["FB_2"].value
        err = numpy.abs(1.0 - x1 - x2)
        self.assertLess(err, 0.001)

    def testDirect2(self):
        gr = self.loadGraph("data/Mass_Bal_Test_02.json")
        gr.tearSolver = "Direct"
        gr.solve()
        x1 = gr.output["Sep_02"]["FA_Bottom"].value
        x2 = gr.output["Sep_02"]["FB_Bottom"].value
        x3 = gr.output["Sep_02"]["FC_Bottom"].value
        x4 = gr.output["Splt_01"]["FA_Out2"].value
        x5 = gr.output["Splt_01"]["FB_Out2"].value
        x6 = gr.output["Splt_01"]["FC_Out2"].value
        x7 = gr.output["Split_02"]["FA_Out2"].value
        x8 = gr.output["Split_02"]["FB_Out2"].value
        x9 = gr.output["Split_02"]["FC_Out2"].value
        err = numpy.abs(1000.0 - x1 - x2 - x3 - x4 - x5 - x6 - x7 - x8 - x9)
        self.assertLess(err, 0.001)

    def testWegstein2(self):
        gr = self.loadGraph("data/Mass_Bal_Test_02.json")
        gr.tearSolver = "Wegstein"
        gr.solve()
        x1 = gr.output["Sep_02"]["FA_Bottom"].value
        x2 = gr.output["Sep_02"]["FB_Bottom"].value
        x3 = gr.output["Sep_02"]["FC_Bottom"].value
        x4 = gr.output["Splt_01"]["FA_Out2"].value
        x5 = gr.output["Splt_01"]["FB_Out2"].value
        x6 = gr.output["Splt_01"]["FC_Out2"].value
        x7 = gr.output["Split_02"]["FA_Out2"].value
        x8 = gr.output["Split_02"]["FB_Out2"].value
        x9 = gr.output["Split_02"]["FC_Out2"].value
        err = numpy.abs(1000.0 - x1 - x2 - x3 - x4 - x5 - x6 - x7 - x8 - x9)
        self.assertLess(err, 0.001)

    def testDirect3(self):
        gr = self.loadGraph("data/Mass_Bal_Test_03.json")
        gr.tearSolver = "Direct"
        gr.solve()
        x1 = gr.output["Sep_02"]["FA_Bottom"].value
        x2 = gr.output["Sep_02"]["FB_Bottom"].value
        x3 = gr.output["Sep_02"]["FC_Bottom"].value
        x4 = gr.output["Splt_01"]["FA_Out2"].value
        x5 = gr.output["Splt_01"]["FB_Out2"].value
        x6 = gr.output["Splt_01"]["FC_Out2"].value
        x7 = gr.output["Split_02"]["FA_Out2"].value
        x8 = gr.output["Split_02"]["FB_Out2"].value
        x9 = gr.output["Split_02"]["FC_Out2"].value
        err = numpy.abs(1300.0 - x1 - x2 - x3 - x4 - x5 - x6 - x7 - x8 - x9)
        self.assertLess(err, 0.001)

    def testWegstein3(self):
        gr = self.loadGraph("data/Mass_Bal_Test_03.json")
        gr.tearSolver = "Wegstein"
        gr.solve()
        x1 = gr.output["Sep_02"]["FA_Bottom"].value
        x2 = gr.output["Sep_02"]["FB_Bottom"].value
        x3 = gr.output["Sep_02"]["FC_Bottom"].value
        x4 = gr.output["Splt_01"]["FA_Out2"].value
        x5 = gr.output["Splt_01"]["FB_Out2"].value
        x6 = gr.output["Splt_01"]["FC_Out2"].value
        x7 = gr.output["Split_02"]["FA_Out2"].value
        x8 = gr.output["Split_02"]["FB_Out2"].value
        x9 = gr.output["Split_02"]["FC_Out2"].value
        err = numpy.abs(1300.0 - x1 - x2 - x3 - x4 - x5 - x6 - x7 - x8 - x9)
        self.assertLess(err, 0.001)
