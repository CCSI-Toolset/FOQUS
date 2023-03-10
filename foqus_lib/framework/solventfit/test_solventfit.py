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
from foqus_lib.framework.uq.Distribution import Distribution
from .SolventFit import SolventFit as S

xdatfile = "example/xdat.csv"
ydatfile = "example/ydat.csv"
ytable = [{"rsIndex": -1}]
xtable = [
    {"type": "Design"},
    {
        "type": "Variable",
        "min": 0,
        "max": 1,
        "pdf": Distribution.UNIFORM,
        "param1": 0,
        "param2": 1,
    },
    {
        "type": "Variable",
        "min": 0,
        "max": 1,
        "pdf": Distribution.UNIFORM,
        "param1": 0,
        "param2": 1,
    },
    {
        "type": "Variable",
        "min": 0,
        "max": 1,
        "pdf": Distribution.UNIFORM,
        "param1": 0,
        "param2": 1,
    },
]
exptable = [
    [0.2, 0.126357041975311],
    [0.4, 0.627533837178948],
    [0.6, 1.69355439930246],
    [0.8, 3.02791922863551],
]
S.fit(xdatfile, ydatfile, ytable, xtable, exptable, addDisc=None)
