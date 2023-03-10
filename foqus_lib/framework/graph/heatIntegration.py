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
from . import node as gn
import subprocess


def makeHeatIntegrationNode(node):
    # setup whatever i need for heat integration
    # this gets called when you set the simulation type to "Heat Integration"
    # should only need to be called once after that everything gets saved
    #
    # Input variables
    node.inVars["Hrat"] = gn.NodeVars(
        value=10.0,
        vmax=500.0,
        vdflt=10.0,
        unit="K",
        vdesc="Minimum approach temperature",
        vst="sinter",
    )
    node.inVars["Max.Time"] = gn.NodeVars(
        value=60.0,
        vmax=10000.0,
        vdflt=60.0,
        unit="second",
        vdesc="Maximum allowable time for heat integration",
        vst="sinter",
    )
    node.inVars["Net.Power"] = gn.NodeVars(
        value=None,
        vmax=1000.0,
        unit="MW",
        vdesc="Net power output without CCS",
        vst="sinter",
    )
    # Output variables
    node.outVars["Utility.Cost"] = gn.NodeVars(
        unit="$/hr", vdesc="Total utility cost", vst="sinter"
    )
    node.outVars["HP_Steam.Consumption"] = gn.NodeVars(
        unit="GJ/hr",
        vdesc="High-pressure steam (230 C) consumption (Cost: $8.04/GJ)",
        vst="sinter",
    )
    node.outVars["MP_Steam.Consumption"] = gn.NodeVars(
        unit="GJ/hr",
        vdesc="Medium-pressure steam (164 C) consumption (Cost: $6.25/GJ)",
        vst="sinter",
    )
    node.outVars["Cooling_Water.Consumption"] = gn.NodeVars(
        unit="GJ/hr",
        vdesc="Cooling water (20 C) consumption (Cost: $0.21/GJ)",
        vst="sinter",
    )
    node.outVars["FH.Heat.Addition"] = gn.NodeVars(
        unit="GJ/hr", vdesc="Heat addition to feed water heaters", vst="sinter"
    )
    node.outVars["Min.No.HX"] = gn.NodeVars(
        unit="None", vdesc="Minimum number of heat exchangers", vst="sinter"
    )


def heatIntegrationCalc(node):
    # Search for the block tag and create a set of blocks
    blockSet = set()  # set of all blocks
    heaterSet = set()  # set of heater blocks
    hxHSet = set()  # set of hot side of heat exchanger blocks
    hxCSet = set()  # set of cold side of heat exchanger blocks
    pointHSet = set()  # set of point sources for heat
    pointCSet = set()  # set of point sinks for heat
    blockLookup = dict()  # look up the block given a variable name

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

    hxHFCp = dict()  # flow rate * heat capacity for heat exchanger hot side (GJ/hr/C)
    hxHTin = dict()  # inlet temperature for heat exchanger hot side (C)
    hxHTout = dict()  # outlet temperature for heat exchanger hot side (C)
    hxHIsH = dict()  # heat exchanger hot side is really a hot stream
    hxHIsC = dict()  # heat exchanger hot side is actually a cold stream

    hxCFCp = dict()  # flow rate * heat capacity for heat exchanger cold side (GJ/hr/C)
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
    for ii in range(2):  # do this loop twice (first pass inputs second pass outputs)
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
    hotUSet = set(["HP_Steam", "MP_Steam"])  # set of hot utility
    coldUSet = set(["Cooling_Water"])  # set of cold utility
    hotUTin = dict(
        [("HP_Steam", 230), ("MP_Steam", 164)]
    )  # inlet temperature of hot utility (C)
    coldUTin = dict([("Cooling_Water", 20)])  # inlet temperature of cold utility (C)
    hotUTout = dict(
        [("HP_Steam", 229), ("MP_Steam", 163)]
    )  # outlet temperature of hot utility (C)
    coldUTout = dict([("Cooling_Water", 21)])  # outlet temperature of cold utility (C)
    coldUW = dict(
        [("Cooling_Water", 1)]
    )  # indicator whether cold utility is cooling water
    coldUToutA = dict(
        [("Cooling_Water", 30)]
    )  # actual outlet temperature of cold utility (C)
    hotUCost = dict(
        [("HP_Steam", 8.04), ("MP_Steam", 6.25)]
    )  # cost of hot utility ($/GJ)
    coldUCost = dict([("Cooling_Water", 0.21)])  # cost of cold utility ($/GJ)

    # grab values from input variables
    HRAT = node.inVars["Hrat"].value  # heat recovery approach temperature (K or C)
    MaxTime = node.inVars[
        "Max.Time"
    ].value  # maximum allowable time for heat integration (second)
    NetPower = node.inVars["Net.Power"].value  # net power output (MW)

    # heat integration information for feed water heaters
    feedSet = set(["FH1", "FH2", "FH3", "FH4", "FH5"])  # set of feed water heaters
    feedTin = dict(
        [("FH1", 34.0), ("FH2", 64.7), ("FH3", 95.9), ("FH4", 127.8), ("FH5", 159.6)]
    )  # inlet temperature of feed water heater (C)
    feedTout = dict(
        [("FH1", 64.7), ("FH2", 95.9), ("FH3", 127.8), ("FH4", 159.6), ("FH5", 194.6)]
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
    f.write("/ \n")
    for hotU in hotUSet:
        f.write("\t" + hotU + "\n")
    f.write("/;\n\n")
    # cold utility set
    f.write("Set W  cold utility streams\n")
    f.write("/ \n")
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
    # minimum temperature difference
    f.write("Scalar dT  minimum recovery approach temperature\n")
    f.write("/\n")
    f.write("\t" + str(HRAT) + "\n")
    f.write("/;\n\n")
    # maximum allowable time for heat integration
    f.write("Scalar MaxTime  maximum allowable time\n")
    f.write("/\n")
    f.write("\t" + str(MaxTime) + "\n")
    f.write("/;\n\n")
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
        process = subprocess.Popen(["gams", "HeatIntegration.gms", "lo=0"], cwd="gams")
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
    node.outVars["Utility.Cost"].value = float((f.readline()).strip())  # utility cost
    Uhot = dict()  # hot utility consumption
    Ucold = dict()  # cold utility consumption
    for hotU in hotUSet:
        Uhot[hotU] = float((f.readline()).strip())
    for coldU in coldUSet:
        Ucold[coldU] = float((f.readline()).strip())
    node.outVars["HP_Steam.Consumption"].value = Uhot[
        "HP_Steam"
    ]  # high-pressure steam consumption
    node.outVars["MP_Steam.Consumption"].value = Uhot[
        "MP_Steam"
    ]  # medium-pressure steam consumption
    node.outVars["Cooling_Water.Consumption"].value = Ucold[
        "Cooling_Water"
    ]  # cooling water consumption
    if feedIs:
        node.outVars["FH.Heat.Addition"].value = [0, 0, 0, 0, 0]
        for i in range(len(feedSet)):
            node.outVars["FH.Heat.Addition"].value[i] = float(
                (f.readline()).strip()
            )  # heat addition to feed water heater
    else:
        node.outVars["FH.Heat.Addition"].value = None
    node.outVars["Min.No.HX"].value = int(
        float((f.readline()).strip())
    )  # minimum number of heat exchangers
    print("done with hi calc")

    for var in node.outVars:
        if node.outVars[var]:
            node.outVars[var].toNumpy()
    # done reading GAMS output
    f.close()
