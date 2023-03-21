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
"""
Tests for sdoe/irsf

See LICENSE.md for license and copyright details.
"""
from unittest import result
import pytest
import numpy as np
import pandas as pd
from foqus_lib.framework.sdoe import irsf
from importlib import resources


@pytest.mark.skip
def test_inv_scale_cand():
    cand = np.array([[1, 1, 1], [2, 2, 2], [3, 3, 3]])
    norm_cand, xmin, xmax = irsf.unit_scale(cand)

    norm_cand_reversed = irsf.inv_unit_scale(norm_cand, xmin, xmax)

    assert np.array_equal(
        cand, norm_cand_reversed
    ), "inv_unit_scale function not working properly."


def test_criterion():

    with resources.path(__package__, "candidates_irsf.csv") as p:
        df = pd.read_csv(p)
    print(df.head())
    args = {
        "icol": "__id",
        # "xcols": [0, 1],
        # "scale_factors": pd.Series(1., index=range(len(cand))),
        "max_iterations": 1000,
        "ws": np.linspace(0.1, 0.9, 5),
        "idy": ["Y"],
        "idx": ["V1", "V2"],
    }
    nr = 3
    nd = 2
    mode = "maximin"
    hist = None

    # result = irsf.criterion(cand=cand, args=args,nr=nr, nd=nd, mode=mode, hist=None)

    # with pytest.raises(ValueError):
    result = irsf.criterion(cand=df, args=args, nr=nr, nd=nd, mode=mode, hist=hist)

    assert result.get("pareto_front") is not None
