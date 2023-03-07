from unittest import result
import numpy as np
import pandas as pd
from foqus_lib.framework.sdoe import usf


def test_criterion():

    cand = pd.DataFrame([(1, 1), (2, 2), (3, 3), (4, 4)])
    args = {
        "icol": "",
        "xcols": [0, 1],
        "scale_factors": pd.Series(1.0, index=range(len(cand))),
    }
    nr = 3
    nd = 2
    mode = "maximin"
    hist = None

    result = usf.criterion(cand=cand, args=args, nr=nr, nd=nd, mode=mode, hist=None)

    assert result.get("best_cand") is not None
