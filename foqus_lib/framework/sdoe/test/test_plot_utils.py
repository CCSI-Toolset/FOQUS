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
import pytest
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from unittest.mock import Mock, patch
import tempfile
import os

from foqus_lib.framework.sdoe.plot_utils import (
    plot_hist,
    load_data,
    remove_xticklabels,
    remove_yticklabels,
    plot_candidates,
    plot_weights,
    plot,
    plot_pareto,
)


class TestPlotHist:
    """Test cases for plot_hist function"""

    def setup_method(self):
        """Set up test fixtures"""
        self.fig, self.ax = plt.subplots()
        self.sample_data = pd.Series([1, 2, 3, 4, 5, 2, 3, 4, 1, 5])

    def teardown_method(self):
        """Clean up after tests"""
        plt.close(self.fig)

    def test_plot_hist_basic(self):
        """Test basic histogram plotting"""
        result_ax = plot_hist(self.ax, self.sample_data, "test_var")

        assert isinstance(result_ax, Axes)
        assert result_ax.get_xlabel() == "test_var"
        assert result_ax.get_ylabel() == "Frequency"

    def test_plot_hist_horizontal(self):
        """Test horizontal histogram"""
        result_ax = plot_hist(self.ax, self.sample_data, "test_var", hbars=True)

        assert result_ax.get_ylabel() == "test_var"
        assert result_ax.get_xlabel() == "Frequency"

    def test_plot_hist_with_history(self):
        """Test histogram with historical data"""
        hist_data = pd.Series([0, 1, 2, 3, 4])
        result_ax = plot_hist(self.ax, self.sample_data, "test_var", hist=hist_data)

        # Should have both current and historical data plotted
        assert len(result_ax.patches) > len(self.sample_data.unique())

    def test_plot_hist_design_mode(self):
        """Test histogram in design mode"""
        result_ax = plot_hist(self.ax, self.sample_data, "test_var", design=True)

        # Check that design styling is applied
        assert len(result_ax.patches) > 0

    def test_plot_hist_custom_rgba(self):
        """Test histogram with custom RGBA colors"""
        custom_rgba = (0.5, 0.5, 0.5, 0.8)
        result_ax = plot_hist(
            self.ax, self.sample_data, "test_var", cand_rgba=custom_rgba, design=True
        )

        assert isinstance(result_ax, Axes)

    def test_plot_hist_xlimit(self):
        """Test histogram with x-axis limit"""
        result_ax = plot_hist(
            self.ax, self.sample_data, "test_var", x_limit=10, hbars=True
        )

        xlim = result_ax.get_xlim()
        assert xlim[1] <= 11  # Should be around 1.1 * 10

    def test_plot_hist_grid_and_styling(self):
        """Test grid and styling options"""
        result_ax = plot_hist(
            self.ax, self.sample_data, "test_var", show_grids=True, linewidth=2
        )

        assert result_ax.grid


class TestLoadData:
    """Test cases for load_data function"""

    def setup_method(self):
        """Create temporary test files"""
        self.test_data = pd.DataFrame(
            {"x1": [1, 2, 3, 4, 5], "x2": [2, 4, 6, 8, 10], "y": [1, 4, 9, 16, 25]}
        )

        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        )
        self.test_data.to_csv(self.temp_file.name, index=False)
        self.temp_file.close()

        self.hist_data = pd.DataFrame(
            {"x1": [0, 1, 2], "x2": [0, 2, 4], "y": [0, 1, 4]}
        )

        self.hist_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        )
        self.hist_data.to_csv(self.hist_file.name, index=False)
        self.hist_file.close()

    def teardown_method(self):
        """Clean up temporary files"""
        os.unlink(self.temp_file.name)
        os.unlink(self.hist_file.name)

    @patch("foqus_lib.framework.sdoe.plot_utils.load")
    def test_load_data_without_history(self, mock_load):
        """Test loading data without history file"""
        mock_load.return_value = self.test_data

        df, hf = load_data(self.temp_file.name, None)

        assert df.equals(self.test_data)
        assert hf is None
        mock_load.assert_called_once_with(self.temp_file.name)

    @patch("foqus_lib.framework.sdoe.plot_utils.load")
    def test_load_data_with_history(self, mock_load):
        """Test loading data with history file"""
        mock_load.side_effect = [self.test_data, self.hist_data]

        df, hf = load_data(self.temp_file.name, self.hist_file.name)

        assert df.equals(self.test_data)
        assert hf.equals(self.hist_data)
        assert mock_load.call_count == 2

    @patch("foqus_lib.framework.sdoe.plot_utils.load")
    def test_load_data_header_mismatch(self, mock_load):
        """Test error when headers don't match"""
        mismatched_hist = pd.DataFrame({"different": [1, 2, 3]})
        mock_load.side_effect = [self.test_data, mismatched_hist]

        with pytest.raises(AssertionError):
            load_data(self.temp_file.name, self.hist_file.name)


class TestAxisUtilities:
    """Test cases for axis utility functions"""

    def setup_method(self):
        self.fig, self.ax = plt.subplots()

    def teardown_method(self):
        plt.close(self.fig)

    def test_remove_xticklabels(self):
        """Test removing x-axis tick labels"""
        # Set some initial tick labels
        self.ax.set_xticks([1, 2, 3])
        self.ax.set_xticklabels(["a", "b", "c"])

        result_ax = remove_xticklabels(self.ax)

        assert isinstance(result_ax, Axes)
        labels = [label.get_text() for label in result_ax.get_xticklabels()]
        assert all(label == "" for label in labels)

    def test_remove_yticklabels(self):
        """Test removing y-axis tick labels"""
        # Set some initial tick labels
        self.ax.set_yticks([1, 2, 3])
        self.ax.set_yticklabels(["x", "y", "z"])

        result_ax = remove_yticklabels(self.ax)

        assert isinstance(result_ax, Axes)
        labels = [label.get_text() for label in result_ax.get_yticklabels()]
        assert all(label == "" for label in labels)


class TestPlotCandidates:
    """Test cases for plot_candidates function"""

    def setup_method(self):
        """Set up test data"""
        self.df = pd.DataFrame(
            {
                "x1": np.random.randn(20),
                "x2": np.random.randn(20),
                "x3": np.random.randn(20),
            }
        )

        self.hf = pd.DataFrame(
            {
                "x1": np.random.randn(10),
                "x2": np.random.randn(10),
                "x3": np.random.randn(10),
            }
        )

        self.cand = pd.DataFrame(
            {
                "x1": np.random.randn(15),
                "x2": np.random.randn(15),
                "x3": np.random.randn(15),
                "weight": np.random.rand(15),
            }
        )

    def test_plot_candidates_single_variable(self):
        """Test plotting with single variable"""
        fig = plot_candidates(
            self.df, self.hf, ["x1"], "Test Title", "Test Label", None
        )

        assert isinstance(fig, Figure)
        assert fig._suptitle.get_text() == "Test Title"
        plt.close(fig)

    def test_plot_candidates_multiple_variables(self):
        """Test plotting with multiple variables"""
        fig = plot_candidates(
            self.df, self.hf, ["x1", "x2"], "Test Title", "Test Label", None
        )

        assert isinstance(fig, Figure)
        # Should create a 2x2 subplot grid
        assert len(fig.axes) == 3  # 2 histograms + 1 scatter plot
        plt.close(fig)

    def test_plot_candidates_with_candidate_data(self):
        """Test plotting with candidate data"""
        fig = plot_candidates(
            self.df, self.hf, ["x1", "x2"], "Test Title", "Test Label", self.cand
        )

        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_plot_candidates_with_imputed_points(self):
        """Test plotting with imputed points"""
        fig = plot_candidates(
            self.df, self.hf, ["x1", "x2"], "Test Title", "Test Label", None, nImpPts=5
        )

        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_plot_candidates_no_history(self):
        """Test plotting without history data"""
        fig = plot_candidates(
            self.df, None, ["x1", "x2"], "Test Title", "Test Label", None
        )

        assert isinstance(fig, Figure)
        plt.close(fig)


class TestPlotWeights:
    """Test cases for plot_weights function"""

    def test_plot_weights_basic(self):
        """Test basic weight plotting"""
        xs = np.random.randn(10, 3)
        wt = np.random.rand(10, 1)
        wts = np.random.rand(100)

        fig = plot_weights(xs, wt, wts, "Test Weight Plot")

        assert isinstance(fig, Figure)
        assert len(fig.axes) == 2  # Two subplots
        assert fig._suptitle.get_text() == "Test Weight Plot"
        plt.close(fig)

    @patch("foqus_lib.framework.sdoe.distance.compute_dist")
    def test_plot_weights_with_mocked_distance(self, mock_compute_dist):
        """Test weight plotting with mocked distance calculation"""
        mock_compute_dist.return_value = np.array([[0, 1, 2], [1, 0, 1.5], [2, 1.5, 0]])

        xs = np.random.randn(3, 2)
        wt = np.random.rand(3, 1)
        wts = np.random.rand(50)

        fig = plot_weights(xs, wt, wts, "Test Weight Plot")

        assert isinstance(fig, Figure)
        mock_compute_dist.assert_called_once()
        plt.close(fig)


class TestPlotFunction:
    """Test cases for the main plot function"""

    def setup_method(self):
        """Set up test data"""
        self.test_data = pd.DataFrame(
            {"x1": np.random.randn(20), "x2": np.random.randn(20)}
        )

        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        )
        self.test_data.to_csv(self.temp_file.name, index=False)
        self.temp_file.close()

        self.cand_data = pd.DataFrame(
            {
                "x1": np.random.randn(15),
                "x2": np.random.randn(15),
                "weight": np.random.rand(15),
            }
        )

    def teardown_method(self):
        """Clean up"""
        os.unlink(self.temp_file.name)

    @patch("foqus_lib.framework.sdoe.plot_utils.load_data")
    @patch("foqus_lib.framework.sdoe.plot_utils.plot_candidates")
    def test_plot_basic(self, mock_plot_candidates, mock_load_data):
        """Test basic plot function"""
        mock_load_data.return_value = (self.test_data, None)
        mock_plot_candidates.return_value = Mock(spec=Figure)

        result = plot(self.temp_file.name, "Test Label")

        assert isinstance(result, Mock)
        mock_load_data.assert_called_once()
        mock_plot_candidates.assert_called_once()

    @patch("foqus_lib.framework.sdoe.plot_utils.load_data")
    @patch("foqus_lib.framework.sdoe.plot_utils.plot_candidates")
    def test_plot_with_usf(self, mock_plot_candidates, mock_load_data):
        """Test plot function with USF data"""
        mock_load_data.return_value = (self.test_data, None)
        mock_plot_candidates.return_value = Mock(spec=Figure)

        usf_data = {"cand": self.cand_data}
        result = plot(self.temp_file.name, "Test Label", usf=usf_data)

        assert isinstance(result, Mock)
        mock_plot_candidates.assert_called_once()

    @patch("foqus_lib.framework.sdoe.plot_utils.load_data")
    @patch("foqus_lib.framework.sdoe.plot_utils.plot_candidates")
    @patch("foqus_lib.framework.sdoe.plot_utils.plot_weights")
    @patch("foqus_lib.framework.sdoe.plot_utils.scale_y")
    def test_plot_with_nusf(
        self, mock_scale_y, mock_plot_weights, mock_plot_candidates, mock_load_data
    ):
        """Test plot function with NUSF data"""
        mock_load_data.return_value = (self.test_data, None)
        mock_plot_candidates.return_value = Mock(spec=Figure)
        mock_plot_weights.return_value = Mock(spec=Figure)
        mock_scale_y.return_value = np.random.rand(15, 3)

        nusf_data = {
            "cand": self.cand_data,
            "wcol": "weight",
            "scale_method": "max",
            "results": {
                "best_cand_scaled": pd.DataFrame(np.random.rand(10, 3)),
                "mwr": 0.5,
            },
        }

        result = plot(self.temp_file.name, "Test Label", nusf=nusf_data)

        assert isinstance(result, tuple)
        assert len(result) == 2
        mock_plot_candidates.assert_called_once()
        mock_plot_weights.assert_called_once()


class TestPlotPareto:
    """Test cases for plot_pareto function"""

    def setup_method(self):
        """Set up test data for Pareto plotting"""
        self.pf = pd.DataFrame(
            {
                "Design": [1, 2, 3],
                "Best Input": [0.1, 0.2, 0.3],
                "Best Response": [0.15, 0.25, 0.35],
            }
        )

        self.results = {
            "pareto_front": self.pf,
            "design_id": {1: 0, 2: 1, 3: 2},
            "des": {
                1: pd.DataFrame({"x1": [1, 2], "x2": [3, 4]}),
                2: pd.DataFrame({"x1": [5, 6], "x2": [7, 8]}),
                3: pd.DataFrame({"x1": [9, 10], "x2": [11, 12]}),
            },
            "mode": "test",
            "design_size": 2,
            "num_restarts": 1,
            "num_designs": 3,
        }

        self.cand = pd.DataFrame({"x1": np.random.randn(20), "x2": np.random.randn(20)})

    @patch("foqus_lib.framework.sdoe.plot_utils.load")
    def test_plot_pareto_basic(self, mock_load):
        """Test basic Pareto front plotting"""
        mock_load.return_value = pd.DataFrame({"x1": [1, 2], "x2": [3, 4]})

        fig = plot_pareto(self.pf, self.results, self.cand, "test_file.csv")

        assert isinstance(fig, Figure)
        assert fig._suptitle.get_text() == "SDoE (IRSF) Pareto Front"
        assert len(fig.axes) == 1
        plt.close(fig)

    def test_plot_pareto_no_history(self):
        """Test Pareto plotting without history file"""
        fig = plot_pareto(self.pf, self.results, self.cand, None)

        assert isinstance(fig, Figure)
        plt.close(fig)


# Test fixtures and parameterized tests
@pytest.fixture
def sample_dataframe():
    """Fixture providing sample DataFrame for tests"""
    return pd.DataFrame(
        {
            "x1": np.random.randn(100),
            "x2": np.random.randn(100),
            "x3": np.random.randn(100),
            "weight": np.random.rand(100),
        }
    )


@pytest.mark.parametrize("nbins", [10, 20, 50])
def test_plot_hist_different_bins(nbins):
    """Test histogram with different bin counts"""
    fig, ax = plt.subplots()
    data = pd.Series(np.random.randn(100))

    try:
        result_ax = plot_hist(ax, data, "test", nbins=nbins)
        assert isinstance(result_ax, Axes)
        # The number of bars should be related to nbins
        assert len(result_ax.patches) <= nbins
    finally:
        plt.close(fig)


@pytest.mark.parametrize("design_mode", [True, False])
def test_plot_hist_design_modes(design_mode):
    """Test histogram in different design modes"""
    fig, ax = plt.subplots()
    data = pd.Series(np.random.randn(50))

    try:
        result_ax = plot_hist(ax, data, "test", design=design_mode)
        assert isinstance(result_ax, Axes)
    finally:
        plt.close(fig)


if __name__ == "__main__":
    pytest.main([__file__])
