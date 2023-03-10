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
        self.description = "Steam cycle corrrelations..."
        # Input variables
        self.inputs["Net.Power"] = NodeVars(
            value=500.0,
            vmin=0.0,
            vmax=1000.0,
            vdflt=500.0,
            unit="MW",
            vst="pymodel",  # pymodel variable (not user variable)
            vdesc="Net power output without CCS",
            tags=[],
            dtype=float,
        )  # if dtype is not specified the type is taken
        # from the default vaule.
        self.inputs["Net.Efficiency"] = NodeVars(
            value=42.06,
            vmin=0.0,
            vmax=100.0,
            vdflt=42.06,
            unit="%",
            vst="pymodel",
            vdesc="Net efficiency without CCS",
            tags=[],
        )
        self.inputs["IP_Steam.Consumption"] = NodeVars(
            value=0.0,
            vmin=0.0,
            vmax=10000.0,
            vdflt=0.0,
            unit="GJ/hr",
            vdesc="Intermediate-pressure steam consumption for heating",
            vst="pymodel",
            tags=[],
        )
        self.inputs["LP_Steam.Consumption"] = NodeVars(
            value=0.0,
            vmin=0.0,
            vmax=10000.0,
            vdflt=0.0,
            unit="GJ/hr",
            vdesc="Low-pressure steam consumption for heating",
            vst="pymodel",
            tags=[],
        )
        self.inputs["IP_Steam.Injection"] = NodeVars(
            value=0.0,
            vmin=0.0,
            vmax=50000.0,
            vdflt=0.0,
            unit="kmol/hr",
            vdesc="Intermediate-pressure steam injection",
            vst="pymodel",
            tags=[],
        )
        self.inputs["LP_Steam.Injection"] = NodeVars(
            value=0.0,
            vmin=0.0,
            vmax=50000.0,
            vdflt=0.0,
            unit="kmol/hr",
            vdesc="Low-pressure steam injection",
            vst="pymodel",
            tags=[],
        )
        self.inputs["FH.Heat.Addition1"] = NodeVars(
            value=0,
            vmin=0,
            vmax=10000,
            vdflt=0,
            unit="GJ/hr",
            vdesc="Heat addition into feed water heater 1",
            vst="pymodel",
            tags=[],
        )
        self.inputs["FH.Heat.Addition2"] = NodeVars(
            value=0,
            vmin=0,
            vmax=10000,
            vdflt=0,
            unit="GJ/hr",
            vdesc="Heat addition into feed water heater 2",
            vst="pymodel",
            tags=[],
        )
        self.inputs["FH.Heat.Addition3"] = NodeVars(
            value=0,
            vmin=0,
            vmax=10000,
            vdflt=0,
            unit="GJ/hr",
            vdesc="Heat addition into feed water heater 3",
            vst="pymodel",
            tags=[],
        )
        self.inputs["FH.Heat.Addition4"] = NodeVars(
            value=0.0,
            vmin=0.0,
            vmax=10000,
            vdflt=0,
            unit="GJ/hr",
            vdesc="Heat addition into feed water heater 4",
            vst="pymodel",
            tags=[],
        )
        self.inputs["FH.Heat.Addition5"] = NodeVars(
            value=0,
            vmin=0,
            vmax=10000,
            vdflt=0,
            unit="GJ/hr",
            vdesc="Heat addition into feed water heater 5",
            vst="pymodel",
            tags=[],
        )
        self.inputs["Electricity.Consumption"] = NodeVars(
            value=0.0,
            vmin=0.0,
            vmax=1000.0,
            vdflt=0.0,
            unit="MW",
            vdesc="Electricity consumption",
            vst="pymodel",
            tags=[],
        )
        # Output variables
        self.outputs["Net.Power.CCS"] = NodeVars(
            unit="MW",
            vdesc="Net power output with CCS",
            vst="pymodel",
            dtype=float,
            tags=[],
        )
        self.outputs["Net.Efficiency.CCS"] = NodeVars(
            unit="%",
            vdesc="Net efficiency with CCS",
            vst="pymodel",
            dtype=float,
            tags=[],
        )
        self.outputs["Delta.Power.CCS"] = NodeVars(
            unit="MW",
            vdesc="Change of net power output due to CCS",
            vst="pymodel",
            dtype=float,
            tags=[],
        )
        self.outputs["Delta.Efficiency.CCS"] = NodeVars(
            unit="%",
            vdesc="Change of net efficiency due to CCS",
            vst="pymodel",
            dtype=float,
            tags=[],
        )
        self.outputs["Delta.Power.HI"] = NodeVars(
            unit="MW",
            vdesc="Change of net power output due to heat integration",
            vst="pymodel",
            dtype=float,
            tags=[],
        )
        self.outputs["Delta.Efficiency.HI"] = NodeVars(
            unit="%",
            vdesc="Change of net efficiency due to heat integration",
            vst="pymodel",
            dtype=float,
            tags=[],
        )

    def run(self):
        """
        perform steam cycle calculations
        """
        # net power output w/o CCS (MW)
        if self.inputs["Net.Power"].value > 0:
            NetPower = self.inputs["Net.Power"].value
        else:
            NetPower = 0
        # net efficiency w/o CCS (%)
        NetEfficiency = self.inputs["Net.Efficiency"].value
        # IP steam consumption for heating (GJ/hr)
        if self.inputs["IP_Steam.Consumption"].value > 0.0:
            conHP = self.inputs["IP_Steam.Consumption"].value
        else:
            conHP = 0.0
        # LP steam consumption for heating (GJ/hr)
        if self.inputs["LP_Steam.Consumption"].value > 0.0:
            conMP = self.inputs["LP_Steam.Consumption"].value
        else:
            conMP = 0.0
        # IP steam injection (GJ/hr)
        if self.inputs["IP_Steam.Injection"].value > 0.0:
            injHP = self.inputs["IP_Steam.Injection"].value
        else:
            injHP = 0.0
        # LP steam injection (GJ/hr)
        if self.inputs["LP_Steam.Injection"].value > 0.0:
            injMP = self.inputs["LP_Steam.Injection"].value
        else:
            injMP = 0.0
        # electricity consumption (MW)
        if self.inputs["Electricity.Consumption"].value > 0.0:
            conEle = self.inputs["Electricity.Consumption"].value
        else:
            conEle = 0.0
        # heat recovered in feed water heaters 1 - 5 (GJ/hr)
        FH_Heat_Addition_Values = [
            self.inputs["FH.Heat.Addition1"].value,
            self.inputs["FH.Heat.Addition2"].value,
            self.inputs["FH.Heat.Addition3"].value,
            self.inputs["FH.Heat.Addition4"].value,
            self.inputs["FH.Heat.Addition5"].value,
        ]
        #        if self.inputs["FH.Heat.Addition"].value.any():
        if [k != 0 for k in FH_Heat_Addition_Values]:
            hrFH1 = FH_Heat_Addition_Values[0]
            hrFH2 = FH_Heat_Addition_Values[1]
            hrFH3 = FH_Heat_Addition_Values[2]
            hrFH4 = FH_Heat_Addition_Values[3]
            hrFH5 = FH_Heat_Addition_Values[4]
        else:
            hrFH1 = 0.0
            hrFH2 = 0.0
            hrFH3 = 0.0
            hrFH4 = 0.0
            hrFH5 = 0.0
        # decrease of net power output due to steam extraction (MW)
        decPowSt = (
            0.0047109 * injHP + 0.0040667 * injMP + 0.11010 * conHP + 0.085589 * conMP
        )
        # increase of net power output due to heat addition into
        # feed water heaters (MW)
        incPowFh = (
            0.013895 * hrFH1
            + 0.034086 * hrFH2
            + 0.055540 * hrFH3
            + 0.073636 * hrFH4
            + 0.086699 * hrFH5
        )
        if NetPower > 0:
            # net power out with carbon capture and sequestration (MW)
            NetPowerCCS = NetPower - decPowSt + incPowFh - conEle
            # net efficiency with carbon capture and sequestration (%)
            NetEfficiencyCCS = NetPowerCCS / NetPower * NetEfficiency
            # change net power with carbon capture and sequest. (MW)
            DeltaPowerCCS = -decPowSt - conEle
            # change net eff. with carbon capture and sequest. (%)
            DeltaEfficiencyCCS = DeltaPowerCCS / NetPower * NetEfficiency
            # change of net power output due to heat integration (MW)
            DeltaPowerHI = incPowFh
            # change of net efficiency due to heat integration (%)
            DeltaEfficiencyHI = DeltaPowerHI / NetPower * NetEfficiency
        else:
            NetPowerCCS = numpy.nan
            NetEfficiencyCCS = numpy.nan
            DeltaPowerCCS = numpy.nan
            DeltaEfficiencyCCS = numpy.nan
            DeltaPowerHI = numpy.nan
            DeltaEfficiencyHI = numpy.nan
        # steam cycle node outputs
        self.outputs["Net.Power.CCS"].value = NetPowerCCS
        self.outputs["Net.Efficiency.CCS"].value = NetEfficiencyCCS
        self.outputs["Delta.Power.CCS"].value = DeltaPowerCCS
        self.outputs["Delta.Efficiency.CCS"].value = DeltaEfficiencyCCS
        self.outputs["Delta.Power.HI"].value = DeltaPowerHI
        self.outputs["Delta.Efficiency.HI"].value = DeltaEfficiencyHI
