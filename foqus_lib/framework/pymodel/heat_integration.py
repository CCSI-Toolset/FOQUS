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
#
# FOQUS_PYMODEL_PLUGIN

import subprocess
import logging
import numpy
from foqus_lib.framework.pymodel.pymodel import *
from foqus_lib.framework.graph.nodeVars import *


def checkAvailable():
    """
    Plugins should have this function to check availability of any
    additional required software.  If requirements are not available
    plugin will not be available.
    """
    return True


class pymodel_pg(pymodel):
    """
    This is a plugin model for a supercritical power plant using
    some simple coorelations.
    """

    def __init__(self):
        """
        Initialize steam cycle object
        """
        pymodel.__init__(self)
        self.description = "Heat integration..."
        # Input variables
        self.inputs["HRAT"] = NodeVars(
            value=10.0,
            vmax=500.0,
            vdflt=10.0,
            unit="K",
            vdesc="Heat recovery approach temperature",
            vst="pymodel",
            tags=[],
            dtype=float,
        )
        self.inputs["EMAT"] = NodeVars(
            value=5.0,
            vmax=500.0,
            vdflt=5.0,
            unit="K",
            vdesc="Exchanger minimum approach temperature",
            vst="pymodel",
            tags=[],
            dtype=float,
        )
        self.inputs["Net.Power"] = NodeVars(
            value=0,
            vmax=1000.0,
            unit="MW",
            vdesc="Net power output without CCS",
            vst="pymodel",
            tags=[],
        )
        self.inputs["ROR"] = NodeVars(
            value=10.0,
            vmax=100.0,
            vdflt=10.0,
            unit="%",
            vdesc="Rate of return",
            vst="pymodel",
            tags=[],
            dtype=float,
        )
        self.inputs["Life.Plant"] = NodeVars(
            value=20.0,
            vmax=100.0,
            vdflt=20.0,
            unit="yr",
            vdesc="Operating life of plant",
            vst="pymodel",
            tags=[],
            dtype=float,
        )
        self.inputs["Operation.Hours"] = NodeVars(
            value=8000.0,
            vmax=8766.0,
            vdflt=8000.0,
            unit="hr/yr",
            vdesc="Annual operational hours",
            vst="pymodel",
            tags=[],
            dtype=float,
        )
        self.inputs["No.Stream"] = NodeVars(
            value=0,
            vmax=500.0,
            unit="",
            vdesc="Number of process streams for heat integration",
            vst="pymodel",
            tags=[],
        )
        # Output variables
        self.outputs["Utility.Cost"] = NodeVars(
            unit="$MM/yr", vdesc="Utility cost", vst="pymodel", dtype=float, tags=[]
        )
        self.outputs["IP_Steam.Consumption"] = NodeVars(
            unit="GJ/hr",
            vdesc="Intermediate-pressure steam (230 C) consumption (Cost: $8.04/GJ)",
            vst="pymodel",
            dtype=float,
            tags=[],
        )
        self.outputs["LP_Steam.Consumption"] = NodeVars(
            unit="GJ/hr",
            vdesc="Low-pressure steam (164 C) consumption (Cost: $6.25/GJ)",
            vst="pymodel",
            dtype=float,
            tags=[],
        )
        self.outputs["Cooling_Water.Consumption"] = NodeVars(
            unit="GJ/hr",
            vdesc="Cooling water (20 C) consumption (Cost: $0.21/GJ)",
            vst="pymodel",
            dtype=float,
            tags=[],
        )
        self.outputs["FH.Heat.Addition1"] = NodeVars(
            unit="GJ/hr",
            vdesc="Heat addition to feed water heater 1",
            vst="pymodel",
            dtype=float,
            tags=[],
        )
        self.outputs["FH.Heat.Addition2"] = NodeVars(
            unit="GJ/hr",
            vdesc="Heat addition to feed water heater 2",
            vst="pymodel",
            dtype=float,
            tags=[],
        )
        self.outputs["FH.Heat.Addition3"] = NodeVars(
            unit="GJ/hr",
            vdesc="Heat addition to feed water heater 3",
            vst="pymodel",
            dtype=float,
            tags=[],
        )
        self.outputs["FH.Heat.Addition4"] = NodeVars(
            unit="GJ/hr",
            vdesc="Heat addition to feed water heater 4",
            vst="pymodel",
            dtype=float,
            tags=[],
        )
        self.outputs["FH.Heat.Addition5"] = NodeVars(
            unit="GJ/hr",
            vdesc="Heat addition to feed water heater 5",
            vst="pymodel",
            dtype=float,
            tags=[],
        )
        #        self.outputs["FH.Heat.Addition"].shape=(5,)
        self.outputs["Heat.Exchanger.Area"] = NodeVars(
            unit="m^2", vdesc="Heat exchanger area", vst="pymodel", dtype=float, tags=[]
        )
        self.outputs["Capital.Cost"] = NodeVars(
            unit="$MM",
            vdesc="Approximated capital cost for heat exchanger network",
            vst="pymodel",
            dtype=float,
            tags=[],
        )
        self.outputs["Total.Cost"] = NodeVars(
            unit="$MM/yr",
            vdesc="Approximated total annualized cost for heat exchanger network",
            vst="pymodel",
            dtype=float,
            tags=[],
        )

    def run(self):
        # Search for the block tag and create a set of blocks
        blockSet = set()  # set of all blocks
        heaterSet = set()  # set of heater blocks
        hxHSet = set()  # set of hot side of heat exchanger blocks
        hxCSet = set()  # set of cold side of heat exchanger blocks
        pointHSet = set()  # set of point sources for heat
        pointCSet = set()  # set of point sinks for heat
        blockLookup = dict()  # look up the block given a variable name
        node = self.node
        nameSets = [node.gr.xnames, node.gr.fnames]  # input and output variable names
        varSets = [node.gr.x, node.gr.f]  # input and output variables
        for ii in range(2):
            vnames = nameSets[ii]
            vars = varSets[ii]
            for name in vnames:  # All the inputs
                blktgs = [tag.split() for tag in vars[name].tags if "Block" in tag]
                # I think there should only be one block tag per variable but
                # maybe there is a reason for more
                for tag in blktgs:
                    blockName = tag[1].strip()
                    blockSet.add(blockName)
                    blockLookup[name] = blockName
                    if "heater" in vars[name].tags:
                        heaterSet.add(blockName)
                    if "HX_Hot" in vars[name].tags:
                        hxHSet.add(blockName)
                    if "HX_Cold" in vars[name].tags:
                        hxCSet.add(blockName)
                    if "Point_Hot" in vars[name].tags:
                        pointHSet.add(blockName)
                    if "Point_Cold" in vars[name].tags:
                        pointCSet.add(blockName)

        heaterVars = dict()  # format [Tin, Tout, Qin, Qout]
        hxHVars = dict()  # [Tin, Tout, Q] (heat exchanger hot side)
        hxCVars = dict()  # [Tin, Tout, Q] (heat exchanger cold side)
        pointHVars = dict()  # [T, Q] (point source)
        pointCVars = dict()  # [T, Q] (point sink)

        heaterFCp = dict()  # flow rate * heat capacity for heater (GJ/hr/C)
        heaterTin = dict()  # inlet temperature for heater (C)
        heaterTout = dict()  # outlet temperature for heater (C)
        heaterIsH = dict()  # heater is a hot stream
        heaterIsC = dict()  # heater is a cold stream

        hxHFCp = (
            dict()
        )  # flow rate * heat capacity for heat exchanger hot side (GJ/hr/C)
        hxHTin = dict()  # inlet temperature for heat exchanger hot side (C)
        hxHTout = dict()  # outlet temperature for heat exchanger hot side (C)
        hxHIsH = dict()  # heat exchanger hot side is really a hot stream
        hxHIsC = dict()  # heat exchanger hot side is actually a cold stream

        hxCFCp = (
            dict()
        )  # flow rate * heat capacity for heat exchanger cold side (GJ/hr/C)
        hxCTin = dict()  # inlet temperature for heat exchanger cold side (C)
        hxCTout = dict()  # outlet temperature for heat exchanger cold side (C)
        hxCIsC = dict()  # heat exchanger cold side is really a cold stream
        hxCIsH = dict()  # heat exchanger cold side is actually a hot stream

        pointHFCp = dict()  # flow rate * heat capacity for point source (GJ/hr/C)
        pointHTin = dict()  # inlet temperature for point source (C)
        pointHTout = dict()  # outlet temperature for point source (C)
        pointHIsH = dict()  # point source is a hot stream

        pointCFCp = dict()  # flow rate * heat capacity for point sink (GJ/hr/C)
        pointCTin = dict()  # inlet temperature for point sink (C)
        pointCTout = dict()  # outlet temperature for point sink (C)
        pointCIsC = dict()  # point sink is a cold stream

        tol = 1e-6  # tolerance for no heat exchange

        # now pull out variables
        for ii in range(
            2
        ):  # do this loop twice (first pass inputs second pass outputs)
            vnames = nameSets[ii]
            vars = varSets[ii]
            for name in vnames:  # loop through all variables
                tags = vars[name].tags  # get variable tags
                blk = blockLookup.get(
                    name, None
                )  # get the blocks that a varible is associated with
                if blk != None:
                    if (
                        blk in heaterSet and "heater" in tags
                    ):  # if the block is a heater look for heater variables
                        if heaterVars.get(blk, None) == None:
                            heaterVars[blk] = [0, 0, 0, 0]
                        if "Port_Material_In" in tags:
                            if "T" in tags:
                                heaterVars[blk][0] = vars[name].value
                        elif "Port_Material_Out" in tags:
                            if "T" in tags:
                                heaterVars[blk][1] = vars[name].value
                        elif "Port_Heat_In" in tags:
                            if "Q" in tags:
                                heaterVars[blk][2] = vars[name].value
                        elif "Port_Heat_Out" in tags:
                            if "Q" in tags:
                                heaterVars[blk][3] = vars[name].value
                        elif "Blk_Var" in tags:
                            if "Q" in tags:
                                heaterVars[blk][2] = vars[name].value
                                heaterVars[blk][3] = 0.0
                    if (
                        blk in hxHSet and "HX_Hot" in tags
                    ):  # if the block is a heat exchanger hot side
                        if hxHVars.get(blk, None) == None:
                            hxHVars[blk] = [0, 0, 0]
                        if "Port_Material_In" in tags:
                            if "T" in tags:
                                hxHVars[blk][0] = vars[name].value
                        elif "Port_Material_Out" in tags:
                            if "T" in tags:
                                hxHVars[blk][1] = vars[name].value
                        elif "Blk_Var" in tags:
                            if "Q" in tags:
                                hxHVars[blk][2] = vars[name].value
                    if (
                        blk in hxCSet and "HX_Cold" in tags
                    ):  # if the block is a heat exchanger cold side
                        if hxCVars.get(blk, None) == None:
                            hxCVars[blk] = [0, 0, 0]
                        if "Port_Material_In" in tags:
                            if "T" in tags:
                                hxCVars[blk][0] = vars[name].value
                        elif "Port_Material_Out" in tags:
                            if "T" in tags:
                                hxCVars[blk][1] = vars[name].value
                        elif "Blk_Var" in tags:
                            if "Q" in tags:
                                hxCVars[blk][2] = vars[name].value
                    if (
                        blk in pointHSet and "Point_Hot" in tags
                    ):  # if the block is a point source for heat
                        if pointHVars.get(blk, None) == None:
                            pointHVars[blk] = [0, 0]
                        if "Blk_Var" in tags:
                            if "T" in tags:
                                pointHVars[blk][0] = vars[name].value
                            elif "Q" in tags:
                                pointHVars[blk][1] = vars[name].value
                    if (
                        blk in pointCSet and "Point_Cold" in tags
                    ):  # if the block is a point sink for heat
                        if pointCVars.get(blk, None) == None:
                            pointCVars[blk] = [0, 0]
                        if "Blk_Var" in tags:
                            if "T" in tags:
                                pointCVars[blk][0] = vars[name].value
                            elif "Q" in tags:
                                pointCVars[blk][1] = vars[name].value

        # calculate heat integration parameters for process streams
        for (
            heater
        ) in (
            heaterSet
        ):  # parameters for hot and cold streams involved in heaters and coolers
            heaterIsH[heater] = False
            heaterIsC[heater] = False
            if abs(heaterVars[heater][1] - heaterVars[heater][0]) > tol * max(
                abs(heaterVars[heater][0]), abs(heaterVars[heater][1]), 1.0
            ):
                heaterTin[heater] = heaterVars[heater][0]
                heaterTout[heater] = heaterVars[heater][1]
                heaterFCp[heater] = abs(
                    (heaterVars[heater][3] - heaterVars[heater][2] + 0.0)
                    / (heaterTout[heater] - heaterTin[heater])
                )
                if heaterTout[heater] < heaterTin[heater]:
                    heaterIsH[heater] = True
                else:
                    heaterIsC[heater] = True
        for (
            hxH
        ) in (
            hxHSet
        ):  # parameters for hot (or cold) streams involved in the hot side of heat exchangers
            hxHIsH[hxH] = False
            hxHIsC[hxH] = False
            if abs(hxHVars[hxH][1] - hxHVars[hxH][0]) > tol * max(
                abs(hxHVars[hxH][0]), abs(hxHVars[hxH][1]), 1.0
            ):
                hxHTin[hxH] = hxHVars[hxH][0]
                hxHTout[hxH] = hxHVars[hxH][1]
                if hxHTin[hxH] > hxHTout[hxH]:
                    hxHFCp[hxH] = (abs(hxHVars[hxH][2]) + 0.0) / (
                        hxHTin[hxH] - hxHTout[hxH]
                    )
                    hxHIsH[hxH] = True
                else:
                    hxHFCp[hxH] = (abs(hxHVars[hxH][2]) + 0.0) / (
                        hxHTout[hxH] - hxHTin[hxH]
                    )
                    hxHIsC[hxH] = True
        for (
            hxC
        ) in (
            hxCSet
        ):  # parameters for cold (or hot) streams involved in the cold side of heat exchangers
            hxCIsC[hxC] = False
            hxCIsH[hxC] = False
            if abs(hxCVars[hxC][1] - hxCVars[hxC][0]) > tol * max(
                abs(hxCVars[hxC][0]), abs(hxCVars[hxC][1]), 1.0
            ):
                hxCTin[hxC] = hxCVars[hxC][0]
                hxCTout[hxC] = hxCVars[hxC][1]
                if hxCTin[hxC] < hxCTout[hxC]:
                    hxCFCp[hxC] = (abs(hxCVars[hxC][2]) + 0.0) / (
                        hxCTout[hxC] - hxCTin[hxC]
                    )
                    hxCIsC[hxC] = True
                else:
                    hxCFCp[hxC] = (abs(hxCVars[hxC][2]) + 0.0) / (
                        hxCTin[hxC] - hxCTout[hxC]
                    )
                    hxCIsH[hxC] = True
        for pointH in pointHSet:  # parameters for hot streams involved in point sources
            pointHIsH[pointH] = False
            if abs(pointHVars[pointH][1]) > tol:
                pointHTin[pointH] = pointHVars[pointH][0]
                pointHTout[pointH] = pointHTin[pointH] - 1.0
                pointHFCp[pointH] = abs(pointHVars[pointH][1])
                pointHIsH[pointH] = True
        for pointC in pointCSet:  # parameters for cold streams involved in point sinks
            pointCIsC[pointC] = False
            if abs(pointCVars[pointC][1]) > tol:
                pointCTin[pointC] = pointCVars[pointC][0]
                pointCTout[pointC] = pointCTin[pointC] + 1.0
                pointCFCp[pointC] = abs(pointCVars[pointC][1])
                pointCIsC[pointC] = True

        # utility information
        hotUSet = set(["IP_Steam", "LP_Steam"])  # set of hot utility
        coldUSet = set(["Cooling_Water"])  # set of cold utility
        hotUTin = dict(
            [("IP_Steam", 230), ("LP_Steam", 164)]
        )  # inlet temperature of hot utility (C)
        coldUTin = dict(
            [("Cooling_Water", 20)]
        )  # inlet temperature of cold utility (C)
        hotUTout = dict(
            [("IP_Steam", 229), ("LP_Steam", 163)]
        )  # outlet temperature of hot utility (C)
        coldUTout = dict(
            [("Cooling_Water", 21)]
        )  # outlet temperature of cold utility (C)
        coldUW = dict(
            [("Cooling_Water", 1)]
        )  # indicator whether cold utility is cooling water
        coldUToutA = dict(
            [("Cooling_Water", 30)]
        )  # actual outlet temperature of cold utility (C)
        hotUCost = dict(
            [("IP_Steam", 8.04), ("LP_Steam", 6.25)]
        )  # cost of hot utility ($/GJ)
        coldUCost = dict([("Cooling_Water", 0.21)])  # cost of cold utility ($/GJ)

        # grab values from input variables
        HRAT = self.inputs["HRAT"].value  # heat recovery approach temperature (K or C)
        EMAT = self.inputs[
            "EMAT"
        ].value  # exchanger minimum approach temperature (K or C)
        NetPower = self.inputs["Net.Power"].value  # net power output (MW)

        # temperature interval
        if (
            len(heaterSet) + len(hxHSet) + len(hxCSet) + len(pointHSet) + len(pointCSet)
            > 500
        ):
            NumK = 1000
        else:
            NumK = 500

        # correction factor for a noncountercurrent flow pattern
        # CorrFac = 1               # counter current
        CorrFac = 0.81  # 1-2 shell & tube

        # stream film heat-transfer coefficient
        hCoefHotP = 7.20e-4  # stream film heat-transfer coefficient for hot process streams (GJ/hr/m^2/C)
        hCoefColdP = 7.20e-4  # stream film heat-transfer coefficient for cold process streams (GJ/hr/m^2/C)
        hCoefHotU = 2.16e-2  # stream film heat-transfer coefficient for hot utilities (GJ/hr/m^2/C)
        hCoefColdU = 1.35e-2  # stream film heat-transfer coefficient for cold utilities (GJ/hr/m^2/C)

        # capital and total cost calculations
        ROR = self.inputs["ROR"].value  # rate of return (%)
        lifeOpe = self.inputs["Life.Plant"].value  # operating life of plant (yr)
        timeOpe = self.inputs["Operation.Hours"].value  # annual operating hours (hr/yr)

        AnnuFac = (
            numpy.power((1.0 + ROR / 100.0), lifeOpe) / lifeOpe
        )  # annualized factor for the capital cost

        coeff_a = 10000.0  # capital cost coefficent a
        coeff_b = 800.0  # capital cost coefficent b
        coeff_c = 0.8  # capital cost coefficent c

        # heat integration information for feed water heaters
        feedSet = set(["FH1", "FH2", "FH3", "FH4", "FH5"])  # set of feed water heaters
        feedTin = dict(
            [
                ("FH1", 34.0),
                ("FH2", 64.7),
                ("FH3", 95.9),
                ("FH4", 127.8),
                ("FH5", 159.6),
            ]
        )  # inlet temperature of feed water heater (C)
        feedTout = dict(
            [
                ("FH1", 64.7),
                ("FH2", 95.9),
                ("FH3", 127.8),
                ("FH4", 159.6),
                ("FH5", 194.6),
            ]
        )  # outlet temperature of feed water heater (C)
        feedFCp = dict()  # flow rate * heat capacity for feed water heater (GJ/hr)
        feedRank = dict(
            [("FH1", 1), ("FH2", 2), ("FH3", 3), ("FH4", 4), ("FH5", 5)]
        )  # order of feed water heaters
        feedIs = False  # whether feed water heaters exist

        if NetPower > 0:
            feedIs = True
            feedFCp["FH1"] = 4.5091 * NetPower / 650.33
            feedFCp["FH2"] = 5.6958 * NetPower / 650.33
            feedFCp["FH3"] = 5.7213 * NetPower / 650.33
            feedFCp["FH4"] = 5.8258 * NetPower / 650.33
            feedFCp["FH5"] = 5.9617 * NetPower / 650.33

        # number of shells
        numStr = self.inputs[
            "No.Stream"
        ].value  # number of process streams for heat integration

        if numStr > 0:
            if feedIs:
                numShell_1 = (
                    numStr + 5 - 1
                )  # number of shells (the first calculation way)
            else:
                numShell_1 = numStr - 1
        else:
            if feedIs:
                numShell_1 = (
                    len(heaterSet)
                    + len(hxHSet)
                    + len(hxCSet)
                    + len(pointHSet)
                    + len(pointCSet)
                    + 5
                    - 1
                )
            else:
                numShell_1 = (
                    len(heaterSet)
                    + len(hxHSet)
                    + len(hxCSet)
                    + len(pointHSet)
                    + len(pointCSet)
                    - 1
                )

        maxAreaShell = 500.0
        # maximum area per shell (m^2)

        # write GAMS input
        #
        try:
            f = open("gams/GamsInput.inc", "w")
        except:
            print("Couldn't open GAMS input file")
            return
        # Comments
        f.write("* Input parameters \n\n")
        # hot stream set
        f.write("Set H  hot process streams\n")
        f.write("/ \n")
        for heater in heaterSet:
            if heaterIsH[heater]:
                f.write("\t" + heater + "\n")
        for hxH in hxHSet:
            if hxHIsH[hxH]:
                f.write("\t" + hxH + "\n")
        for hxC in hxCSet:
            if hxCIsH[hxC]:
                f.write("\t" + hxC + "\n")
        for pointH in pointHSet:
            if pointHIsH[pointH]:
                f.write("\t" + pointH + "\n")
        f.write("/;\n\n")
        # cold stream set
        f.write("Set C  cold process streams\n")
        f.write("/\n")
        for heater in heaterSet:
            if heaterIsC[heater]:
                f.write("\t" + heater + "\n")
        for hxC in hxCSet:
            if hxCIsC[hxC]:
                f.write("\t" + hxC + "\n")
        for hxH in hxHSet:
            if hxHIsC[hxH]:
                f.write("\t" + hxH + "\n")
        for pointC in pointCSet:
            if pointCIsC[pointC]:
                f.write("\t" + pointC + "\n")
        if feedIs:
            for feedC in feedSet:
                f.write("\t" + feedC + "\n")
        f.write("/;\n\n")
        # hot stream FCps
        f.write("Parameter FCpH(H)  F*Cp for hot process streams\n")
        f.write("/\n")
        # Ignoring trailing digits in a number
        f.write("$offDigit\n")
        for heater in heaterSet:
            if heaterIsH[heater]:
                f.write("\t" + heater + "\t" + str(heaterFCp[heater]) + "\n")
        for hxH in hxHSet:
            if hxHIsH[hxH]:
                f.write("\t" + hxH + "\t" + str(hxHFCp[hxH]) + "\n")
        for hxC in hxCSet:
            if hxCIsH[hxC]:
                f.write("\t" + hxC + "\t" + str(hxCFCp[hxC]) + "\n")
        for pointH in pointHSet:
            if pointHIsH[pointH]:
                f.write("\t" + pointH + "\t" + str(pointHFCp[pointH]) + "\n")
        f.write("/;\n\n")
        # cold stream FCps
        f.write("Parameter FCpC(C)  F*Cp for cold process streams\n")
        f.write("/\n")
        # Ignoring trailing digits in a number
        f.write("$offDigit\n")
        for heater in heaterSet:
            if heaterIsC[heater]:
                f.write("\t" + heater + "\t" + str(heaterFCp[heater]) + "\n")
        for hxC in hxCSet:
            if hxCIsC[hxC]:
                f.write("\t" + hxC + "\t" + str(hxCFCp[hxC]) + "\n")
        for hxH in hxHSet:
            if hxHIsC[hxH]:
                f.write("\t" + hxH + "\t" + str(hxHFCp[hxH]) + "\n")
        for pointC in pointCSet:
            if pointCIsC[pointC]:
                f.write("\t" + pointC + "\t" + str(pointCFCp[pointC]) + "\n")
        if feedIs:
            for feedC in feedSet:
                f.write("\t" + feedC + "\t" + str(feedFCp[feedC]) + "\n")
        f.write("/;\n\n")
        # hot stream inlet temperatures
        f.write("Parameter TinH(H)  inlet temperature of hot process streams\n")
        f.write("/\n")
        # Ignoring trailing digits in a number
        f.write("$offDigit\n")
        for heater in heaterSet:
            if heaterIsH[heater]:
                f.write("\t" + heater + "\t" + str(heaterTin[heater]) + "\n")
        for hxH in hxHSet:
            if hxHIsH[hxH]:
                f.write("\t" + hxH + "\t" + str(hxHTin[hxH]) + "\n")
        for hxC in hxCSet:
            if hxCIsH[hxC]:
                f.write("\t" + hxC + "\t" + str(hxCTin[hxC]) + "\n")
        for pointH in pointHSet:
            if pointHIsH[pointH]:
                f.write("\t" + pointH + "\t" + str(pointHTin[pointH]) + "\n")
        f.write("/;\n\n")
        # hot stream outlet temperatures
        f.write("Parameter ToutH(H)  outlet temperature of hot process streams\n")
        f.write("/\n")
        # Ignoring trailing digits in a number
        f.write("$offDigit\n")
        for heater in heaterSet:
            if heaterIsH[heater]:
                f.write("\t" + heater + "\t" + str(heaterTout[heater]) + "\n")
        for hxH in hxHSet:
            if hxHIsH[hxH]:
                f.write("\t" + hxH + "\t" + str(hxHTout[hxH]) + "\n")
        for hxC in hxCSet:
            if hxCIsH[hxC]:
                f.write("\t" + hxC + "\t" + str(hxCTout[hxC]) + "\n")
        for pointH in pointHSet:
            if pointHIsH[pointH]:
                f.write("\t" + pointH + "\t" + str(pointHTout[pointH]) + "\n")
        f.write("/;\n\n")
        # cold stream inlet temperatures
        f.write("Parameter TinC(C)  inlet temperature of cold process streams\n")
        f.write("/\n")
        # Ignoring trailing digits in a number
        f.write("$offDigit\n")
        for heater in heaterSet:
            if heaterIsC[heater]:
                f.write("\t" + heater + "\t" + str(heaterTin[heater]) + "\n")
        for hxC in hxCSet:
            if hxCIsC[hxC]:
                f.write("\t" + hxC + "\t" + str(hxCTin[hxC]) + "\n")
        for hxH in hxHSet:
            if hxHIsC[hxH]:
                f.write("\t" + hxH + "\t" + str(hxHTin[hxH]) + "\n")
        for pointC in pointCSet:
            if pointCIsC[pointC]:
                f.write("\t" + pointC + "\t" + str(pointCTin[pointC]) + "\n")
        if feedIs:
            for feedC in feedSet:
                f.write("\t" + feedC + "\t" + str(feedTin[feedC]) + "\n")
        f.write("/;\n\n")
        # cold stream outlet temperatures
        f.write("Parameter ToutC(C)  outlet temperature of cold process streams\n")
        f.write("/\n")
        # Ignoring trailing digits in a number
        f.write("$offDigit\n")
        for heater in heaterSet:
            if heaterIsC[heater]:
                f.write("\t" + heater + "\t" + str(heaterTout[heater]) + "\n")
        for hxC in hxCSet:
            if hxCIsC[hxC]:
                f.write("\t" + hxC + "\t" + str(hxCTout[hxC]) + "\n")
        for hxH in hxHSet:
            if hxHIsC[hxH]:
                f.write("\t" + hxH + "\t" + str(hxHTout[hxH]) + "\n")
        for pointC in pointCSet:
            if pointCIsC[pointC]:
                f.write("\t" + pointC + "\t" + str(pointCTout[pointC]) + "\n")
        if feedIs:
            for feedC in feedSet:
                f.write("\t" + feedC + "\t" + str(feedTout[feedC]) + "\n")
        f.write("/;\n\n")
        # hot utility set
        f.write("Set S  hot utility streams\n")
        f.write("/\n")
        for hotU in hotUSet:
            f.write("\t" + hotU + "\n")
        f.write("/;\n\n")
        # cold utility set
        f.write("Set W  cold utility streams\n")
        f.write("/\n")
        for coldU in coldUSet:
            f.write("\t" + coldU + "\n")
        f.write("/;\n\n")
        # hot utility inlet temperatures
        f.write("Parameter TinS(S)  inlet temperature of hot utility streams\n")
        f.write("/\n")
        for hotU in hotUSet:
            f.write("\t" + hotU + "\t" + str(hotUTin[hotU]) + "\n")
        f.write("/;\n\n")
        # hot utility outlet temperatures
        f.write("Parameter ToutS(S)  outlet temperature of hot utility streams\n")
        f.write("/\n")
        for hotU in hotUSet:
            f.write("\t" + hotU + "\t" + str(hotUTout[hotU]) + "\n")
        f.write("/;\n\n")
        # cold utility inlet temperatures
        f.write("Parameter TinW(W)  inlet temperature of cold utility streams\n")
        f.write("/\n")
        for coldU in coldUSet:
            f.write("\t" + coldU + "\t" + str(coldUTin[coldU]) + "\n")
        f.write("/;\n\n")
        # cold utility outlet temperatures
        f.write("Parameter ToutW(W)  outlet temperature of cold utility streams\n")
        f.write("/\n")
        for coldU in coldUSet:
            f.write("\t" + coldU + "\t" + str(coldUTout[coldU]) + "\n")
        f.write("/;\n\n")
        # whether cold utility is cooling water
        f.write("Parameter WW(W)  whether the cold utility is cooling water\n")
        f.write("/\n")
        for coldU in coldUSet:
            f.write("\t" + coldU + "\t" + str(coldUW[coldU]) + "\n")
        f.write("/;\n\n")
        # cold utility actual outlet temperatures
        f.write("Parameter ToutWA(W)  actual outlet temperature of cold utility\n")
        f.write("/\n")
        for coldU in coldUSet:
            f.write("\t" + coldU + "\t" + str(coldUToutA[coldU]) + "\n")
        f.write("/;\n\n")
        # hot utility cost
        f.write("Parameter CS(S)  cost of hot utilities\n")
        f.write("/\n")
        for hotU in hotUSet:
            f.write("\t" + hotU + "\t" + str(hotUCost[hotU]) + "\n")
        f.write("/;\n\n")
        # cold utility cost
        f.write("Parameter CW(W)  cost of cold utilities\n")
        f.write("/\n")
        for coldU in coldUSet:
            f.write("\t" + coldU + "\t" + str(coldUCost[coldU]) + "\n")
        f.write("/;\n\n")
        # temperature interval set
        f.write("Set K  possible temperature intervals\n")
        f.write("/\n")
        f.write("\t" + "1*" + str(NumK) + "\n")
        f.write("/;\n\n")
        # heat recovery approach temperature
        f.write("Scalar dT  heat recovery approach temperature (HRAT)\n")
        f.write("/\n")
        f.write("\t" + str(HRAT) + "\n")
        f.write("/;\n\n")
        # minimum exchanger approach temperature
        f.write("Scalar dTA  exchanger minimum approach temperature (EMAT)\n")
        f.write("/\n")
        f.write("\t" + str(EMAT) + "\n")
        f.write("/;\n\n")
        # correction factor for a noncountercurrent flow pattern
        f.write("Scalar Ft  correction factor for a noncountercurrent flow pattern\n")
        f.write("/\n")
        f.write("\t" + str(CorrFac) + "\n")
        f.write("/;\n\n")
        # stream film heat-transfer coefficient
        f.write(
            "Parameter hH(H)  stream film heat-transfer coefficient for hot process streams;\n"
        )
        f.write(
            "Parameter hC(C)  stream film heat-transfer coefficient for cold process streams;\n"
        )
        f.write(
            "Parameter hS(S)  stream film heat-transfer coefficient for hot utilities;\n"
        )
        f.write(
            "Parameter hW(W)  stream film heat-transfer coefficient for cold utilities;\n"
        )
        f.write("\n")
        f.write("hH(H) = " + str(hCoefHotP) + ";\n")
        f.write("hC(C) = " + str(hCoefColdP) + ";\n")
        f.write("hS(S) = " + str(hCoefHotU) + ";\n")
        f.write("hW(W) = " + str(hCoefColdU) + ";\n")
        f.write("\n")
        # define set for feed water heaters
        f.write("Set CR(C)  set of cold streams except feed water streams;\n\n")
        f.write("    CR(C) = yes;\n")
        if feedIs:
            for feedC in feedSet:
                f.write('    CR("' + feedC + '") = no;\n')
        f.write("\n")
        f.write("Set CF(C)  set of feed water streams;\n\n")
        f.write("    CF(C) = no;\n")
        if feedIs:
            for feedC in feedSet:
                f.write('    CF("' + feedC + '") = yes;\n')
        f.write("\n")
        f.write("Parameter RankCF(C)  order of feed water streams;\n\n")
        f.write("    RankCF(C) = 0;\n")
        if feedIs:
            for feedC in feedSet:
                f.write('    RankCF("' + feedC + '") = ' + str(feedRank[feedC]) + ";\n")

        # write whatever

        # done writing GAMS input
        f.close()

        # execute gams code with system call
        try:
            process = subprocess.Popen(
                ["gams", "HeatIntegration.gms", "lo=0"], cwd="gams"
            )
            process.wait()  # could get fancy later and add a timeout
        except:
            node.calcError = -2
            print("Is GAMS installed?  Are the heat integration GAMS files available?")
            return

        # read GAMS output file
        try:
            f = open("gams\GamsOutput.txt", "r")
        except:
            print("couldn't open GAMS output file")
            return
        # pull GAMS results in the node variables
        costUtiHr = float((f.readline()).strip())  # utility cost (hourly) ($MM/hr)
        costUtiYr = costUtiHr * timeOpe / 1e6  # utility cost (annually) ($MM/yr)
        self.outputs[
            "Utility.Cost"
        ].value = costUtiYr  # utility cost (annually) ($MM/yr)
        areaHx = float((f.readline()).strip())  # heat exchanger area (m^2)
        self.outputs["Heat.Exchanger.Area"].value = areaHx  # heat exchanger area (m^2)
        numShell_2 = numpy.ceil(
            areaHx / maxAreaShell
        )  # number of shells (the second calculation way)
        numShell = max(numShell_1, numShell_2)  # number of shells
        costCap = (
            coeff_a + coeff_b * numpy.power(areaHx / numShell, coeff_c) * numShell
        ) / 1e6  # approximated capital cost ($MM)
        self.outputs["Capital.Cost"].value = costCap  # approximated capital cost ($MM)
        costTot = costUtiYr + AnnuFac * costCap  # approximated total cost ($MM/yr)
        self.outputs["Total.Cost"].value = costTot  # approximated total cost ($MM/yr)
        Uhot = dict()  # hot utility consumption (GJ/hr)
        Ucold = dict()  # cold utility consumption (GJ/hr)
        for hotU in hotUSet:
            Uhot[hotU] = float((f.readline()).strip())
        for coldU in coldUSet:
            Ucold[coldU] = float((f.readline()).strip())
        self.outputs["IP_Steam.Consumption"].value = Uhot[
            "IP_Steam"
        ]  # intermediate-pressure steam consumption (GJ/hr)
        self.outputs["LP_Steam.Consumption"].value = Uhot[
            "LP_Steam"
        ]  # low-pressure steam consumption (GJ/hr)
        self.outputs["Cooling_Water.Consumption"].value = Ucold[
            "Cooling_Water"
        ]  # cooling water consumption (GJ/hr)
        #        self.outputs["FH.Heat.Addition"].value = 10000  ### romove after testing 7/11/2019
        if feedIs:
            #            self.outputs["FH.Heat.Addition"].value = [0, 0, 0, 0, 0]
            FH_Heat_Addition = [
                self.outputs["FH.Heat.Addition1"],
                self.outputs["FH.Heat.Addition2"],
                self.outputs["FH.Heat.Addition3"],
                self.outputs["FH.Heat.Addition4"],
                self.outputs["FH.Heat.Addition5"],
            ]
            for i in range(len(feedSet)):
                #                self.outputs["FH.Heat.Addition"].value[i] = float((f.readline()).strip())      # heat addition to feed water heater (GJ/hr)
                FH_Heat_Addition[i].value = float(
                    (f.readline()).strip()
                )  # heat addition to feed water heater (GJ/hr)
        else:
            #            self.outputs["FH.Heat.Addition"].value = [
            #                numpy.nan,
            #                numpy.nan,
            #                numpy.nan,
            #                numpy.nan,
            #                numpy.nan]
            self.outputs["FH.Heat.Addition1"].value = numpy.nan
            self.outputs["FH.Heat.Addition2"].value = numpy.nan
            self.outputs["FH.Heat.Addition3"].value = numpy.nan
            self.outputs["FH.Heat.Addition4"].value = numpy.nan
            self.outputs["FH.Heat.Addition5"].value = numpy.nan

        print("done with hi calc")

        # Vector Variables not supported
        #        for var in node.outVars:
        #            if self.outputs[var]:
        #                self.outputs[var].toNumpy()

        # done reading GAMS output
        f.close()
