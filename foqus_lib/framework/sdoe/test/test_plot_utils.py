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
import pytest
from foqus_lib.framework.sdoe import plot_utils
from unittest import mock
from importlib import resources
from pathlib import Path


@mock.patch("foqus_lib.framework.sdoe.plot_utils.plt")
def test_plot(fake_plt: mock.MagicMock):

    fake_fig = mock.MagicMock()
    fake_axes = mock.MagicMock()
    fake_plt.subplots.return_value = (fake_fig, fake_axes)
    fname = "candidates_usf.csv"
    copy_from_package(fname)
    scatter_label = "something"

    plot_utils.plot(fname=fname, scatter_label=scatter_label)

    assert fake_plt.show.call_count > 0


def copy_from_package(file_name: str) -> None:
    content = resources.read_text(__package__, file_name)
    Path(file_name).write_text(content)
