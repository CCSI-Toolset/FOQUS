#################################################################################
# FOQUS Copyright (c) 2012 - 2024, by the software owners: Oak Ridge Institute
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
from importlib import resources
from pathlib import Path

import pandas as pd

from foqus_lib.framework.sdoe.df_utils import write, load, merge, check


def test_write():
    fname = "test_data.csv"
    df = pd.DataFrame([(1, 1), (2, 2), (3, 3), (4, 4)])

    write(fname, df)

    obj = Path(fname)

    test_results = obj.exists()

    # Clean up
    obj.unlink()

    assert test_results


def test_load():
    fname = "candidates_usf.csv"
    copy_from_package(fname)

    df = load(fname)

    assert df is not None


def test_merge():
    fnames = ["candidates_usf.csv", "previous_data.csv"]
    for fname in fnames:
        copy_from_package(fname)

    df = merge(fnames)

    assert df is not None


def test_check():
    cfiles = ["cand1.csv", "cand2.csv"]
    hfiles = ["prev1.csv", "prev2.csv"]

    for cfile in cfiles:
        copy_from_package(cfile)

    for hfile in hfiles:
        copy_from_package(hfile)

    cand_df, hist_df = check(cfiles, hfiles)

    assert cand_df is not None
    assert hist_df is not None


def copy_from_package(file_name: str) -> None:
    content = resources.read_text(__package__, file_name)
    Path(file_name).write_text(content)
