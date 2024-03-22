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
import configparser
import json
from importlib import resources
from pathlib import Path
from unittest import mock

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from foqus_lib.framework.sdoe import df_utils, nusf, plot_utils, sdoe


@mock.patch("foqus_lib.framework.sdoe.plot_utils.plt")
def test_plot(fake_plt: mock.MagicMock):

    fake_fig = mock.MagicMock()
    fake_axes = mock.MagicMock()
    fake_plt.subplots.return_value = (fake_fig, fake_axes)
    fname = "candidates_usf.csv"
    copy_from_package(fname)
    scatter_label = "something"

    fig = plot_utils.plot(fname=fname, scatter_label=scatter_label)

    assert fig is not None


@mock.patch("foqus_lib.framework.sdoe.plot_utils.plt")
def test_plot_weights(fake_plt: mock.MagicMock):

    fake_fig = mock.MagicMock()
    fake_ax1 = mock.MagicMock()
    fake_ax2 = mock.MagicMock()
    fake_plt.subplots.return_value = (fake_fig, (fake_ax1, fake_ax2))

    config_file = "config_nusf.ini"
    copy_from_package(config_file)

    cand_file = "candidates_nusf.csv"
    copy_from_package(cand_file)
    cand = df_utils.load(cand_file)

    results_file = "results_nusf.json"
    copy_from_package(results_file)
    with open(results_file) as file:
        results_dict = json.load(file)

    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_file)
    scale_method = config["SF"]["scale_method"]
    include = [s.strip() for s in config["INPUT"]["include"].split(",")]
    types = [s.strip() for s in config["INPUT"]["types"].split(",")]

    i = types.index("Weight")
    wcol = include[i]  # weight column name

    des = pd.DataFrame.from_dict(results_dict["best_cand_scaled"]).values
    xs = des[:, :-1]  # scaled coordinates from best candidate
    wt = des[:, -1]  # scaled weights from best candidate

    idw_np = cand.columns.get_loc(wcol)
    cand_np = cand.to_numpy()
    mwr = results_dict["mwr"]
    cand_ = nusf.scale_y(scale_method, mwr, cand_np, idw_np)
    wts = cand_[:, idw_np]  # scaled weights from all candidates
    title = "SDOE (NUSF) Weight Visualization for MWR={}".format(mwr)
    fig = plot_utils.plot_weights(xs, wt, wts, title)

    assert fig is not None


@mock.patch("foqus_lib.framework.sdoe.plot_utils.plt")
def test_plot_pareto(fake_plt: mock.MagicMock):

    fake_fig = mock.MagicMock()
    fake_axes = mock.MagicMock()
    fake_plt.subplots.return_value = (fake_fig, fake_axes)

    cand_file = "candidates_irsf.csv"
    copy_from_package(cand_file)
    cand = df_utils.load(cand_file)

    results_file = "results_irsf.json"
    copy_from_package(results_file)
    with open(results_file) as file:
        results_dict = json.load(file)

    pf = pd.DataFrame.from_dict(results_dict["pareto_front"])

    fig = plot_utils.plot_pareto(pf, results_dict, cand, None)

    assert fig is not None


def copy_from_package(file_name: str) -> None:
    content = resources.read_text(__package__, file_name)
    Path(file_name).write_text(content)
