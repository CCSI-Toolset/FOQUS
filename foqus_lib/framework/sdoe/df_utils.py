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
from typing import Optional, Union, Tuple, List
import pandas as pd


def write(fname: str, df: pd.DataFrame, index: bool = False) -> None:
    """
    Writes data frame as csv file
    args: fname, df, index
    returns: None, saves df to csv file
    """
    if index:
        index_label = "__id"
    else:
        index_label = None

    df.to_csv(fname, index=index, index_label=index_label)  # do not write row names


def load(fname: str, index: Optional[str] = None) -> pd.DataFrame:
    """
    Loads file as data frame
    args: fname, index
    returns: df
    """
    df = pd.read_csv(fname)
    df.rename(columns=lambda x: x.strip(), inplace=True)
    if index:
        df.set_index(index, inplace=True)
    return df


def merge(fnames: List) -> pd.DataFrame:
    """
    Merges multiple files into single data frame
    args: fnames
    returns: df
    """

    dfs = [load(fname) for fname in fnames]

    if len(dfs) == 1:
        return dfs[0]

    df = pd.concat(dfs, join="inner", ignore_index=True)
    df = df.drop_duplicates()  # remove duplicate rows
    return df


def check(
    cfiles: List, hfiles: Optional[List]
) -> Tuple[pd.DataFrame, Union[List, pd.DataFrame]]:
    """
    Aggregates files and ensure consistent columns
    args: cfiles, hfiles
    returns: cand_df, hist_df
    """

    cand_df = merge(cfiles)
    if not hfiles:
        return cand_df, []

    hist_df = merge(hfiles)

    cols = cand_df.columns.tolist()
    hist_df = hist_df[cols]

    return cand_df, hist_df
