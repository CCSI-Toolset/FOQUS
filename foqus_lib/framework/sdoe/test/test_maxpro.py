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
from unittest import result

import pandas as pd

from foqus_lib.framework.sdoe import maxpro


def test_criterion():

    cand = pd.DataFrame([(1, 1), (2, 2), (3, 3), (4, 4)])
    args = {
        "icol": "",
        "xcols": [0, 1],
        "min_scale_factors": pd.Series(1.0, index=range(len(cand))),
        "max_scale_factors": pd.Series(1.0, index=range(len(cand))),
    }
    nd = 2
    max_iter = 25
    hist = None

    result = maxpro.criterion(cand=cand, args=args, nd=nd, max_iter=max_iter, hist=hist)

    assert result.get("design") is not None
