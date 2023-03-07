from unittest import result
import numpy as np
import pandas as pd
from foqus_lib.framework.sdoe import nusf


def test_criterion():

    cand = pd.DataFrame([(1, 1, 1), (2, 2, 1), (3, 3, 1), (4, 4, 1)])
    args = {
        "icol": "",
        "xcols": [0, 1],
        "scale_factors": pd.Series(1.0, index=range(len(cand))),
        "wcol": 2,
        "max_iterations": 100,
        "mwr_values": [1, 2, 4, 8, 16],
        "scale_method": "direct_mwr",
    }
    nr = 3
    nd = 2
    mode = "maximin"
    hist = None

    result = nusf.criterion(cand=cand, args=args, nr=nr, nd=nd, mode=mode, hist=None)

    for mwr in args["mwr_values"]:
        assert result[mwr].get("best_cand") is not None
