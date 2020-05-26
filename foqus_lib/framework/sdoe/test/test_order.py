"""
Tests for sdoe/order

See LICENSE.md for license and copyright details.
"""

import numpy as np
from foqus_lib.framework.sdoe import order

def test_mat2tuples():
    """ Test mat2tuples """
    arr = np.array([[1, 2, 3],
                    [4, 5, 6],
                    [7, 8, 9]])
    lte = order.mat2tuples(arr)
    assert lte == [(1, 0, 4), (2, 0, 7), (2, 1, 8)]
