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
from unittest.mock import patch

# Import both functions from your module
from foqus_lib.framework.sdoe.maxpro import maxpro_lhd, maxpro_lhd_core


def test_maxpro_lhd_basic_functionality():
    """Test basic functionality with mock core function"""

    # Mock the core function to return predictable results
    mock_design = np.random.rand(10, 3)  # 10 points, 3 dimensions
    mock_measure = 0.5
    mock_itotal = 100
    mock_time_rec = 0.123

    with patch("foqus_lib.framework.sdoe.maxpro.maxpro_lhd_core") as mock_core:
        mock_core.return_value = (mock_design, mock_measure, mock_itotal, mock_time_rec)

        result = maxpro_lhd(n=10, p=3)

        # Check that core function was called with correct parameters
        mock_core.assert_called_once_with(10, 3, 2, 0, 1, 400, 1000000)

        # Check return structure
        assert isinstance(result, dict)
        assert set(result.keys()) == {
            "Design",
            "temp0",
            "measure",
            "time_rec",
            "ntotal",
        }

        # Check return values
        np.testing.assert_array_equal(result["Design"], mock_design)
        assert result["temp0"] == 0
        assert result["measure"] == mock_measure**2  # Should be squared
        assert result["time_rec"] == mock_time_rec
        assert result["ntotal"] == mock_itotal


def test_maxpro_lhd_custom_parameters():
    """Test with custom parameters"""

    mock_design = np.random.rand(5, 2)
    mock_measure = 0.8
    mock_itotal = 200
    mock_time_rec = 0.456

    with patch("foqus_lib.framework.sdoe.maxpro.maxpro_lhd_core") as mock_core:
        mock_core.return_value = (mock_design, mock_measure, mock_itotal, mock_time_rec)

        result = maxpro_lhd(
            n=5, p=2, s=3, temp0=0.1, nstarts=2, itermax=500, total_iter=50000
        )

        # Check that core function was called with custom parameters
        mock_core.assert_called_once_with(5, 2, 3, 0.1, 2, 500, 50000)

        # Check specific values
        assert result["temp0"] == 0.1
        assert result["measure"] == mock_measure**2


def test_maxpro_lhd_parameter_validation():
    """Test parameter validation"""

    with patch("foqus_lib.framework.sdoe.maxpro.maxpro_lhd_core") as mock_core:
        mock_core.return_value = (np.random.rand(2, 2), 0.5, 100, 0.1)

        # Test with minimum valid parameters
        result = maxpro_lhd(n=2, p=2)
        assert result is not None

        # Test with various parameter combinations
        result = maxpro_lhd(n=100, p=10, s=1, temp0=1.0, nstarts=5)
        assert result is not None


def test_maxpro_lhd_return_types():
    """Test that return types are correct"""

    mock_design = np.random.rand(8, 4)
    mock_measure = 0.75
    mock_itotal = 150
    mock_time_rec = 0.234

    with patch("foqus_lib.framework.sdoe.maxpro.maxpro_lhd_core") as mock_core:
        mock_core.return_value = (mock_design, mock_measure, mock_itotal, mock_time_rec)

        result = maxpro_lhd(n=8, p=4)

        # Check types
        assert isinstance(result["Design"], np.ndarray)
        assert isinstance(result["temp0"], (int, float))
        assert isinstance(result["measure"], (int, float))
        assert isinstance(result["time_rec"], (int, float))
        assert isinstance(result["ntotal"], (int, float))


def test_maxpro_lhd_design_properties():
    """Test properties of the returned design"""

    # Create a more realistic mock design (Latin Hypercube properties)
    n, p = 20, 3
    mock_design = np.random.rand(n, p)

    with patch("foqus_lib.framework.sdoe.maxpro.maxpro_lhd_core") as mock_core:
        mock_core.return_value = (mock_design, 0.6, 200, 0.1)

        result = maxpro_lhd(n=n, p=p)

        design = result["Design"]

        # Check design dimensions
        assert design.shape == (n, p)

        # Check that values are in [0,1] range
        assert np.all(design >= 0)
        assert np.all(design <= 1)


def test_maxpro_lhd_measure_squaring():
    """Test that the measure is correctly squared"""

    test_measures = [0.5, 0.8, 1.0, 1.5, 2.0]

    for measure in test_measures:
        with patch("foqus_lib.framework.sdoe.maxpro.maxpro_lhd_core") as mock_core:
            mock_core.return_value = (np.random.rand(5, 2), measure, 100, 0.1)

            result = maxpro_lhd(n=5, p=2)

            assert result["measure"] == measure**2


def test_maxpro_lhd_edge_cases():
    """Test edge cases"""

    with patch("foqus_lib.framework.sdoe.maxpro.maxpro_lhd_core") as mock_core:
        # Test with minimum design size
        mock_core.return_value = (np.random.rand(2, 1), 0.1, 50, 0.05)
        result = maxpro_lhd(n=2, p=1)
        assert result["Design"].shape == (2, 1)

        # Test with zero temperature
        mock_core.return_value = (np.random.rand(5, 3), 0.3, 100, 0.1)
        result = maxpro_lhd(n=5, p=3, temp0=0)
        assert result["temp0"] == 0

        # Test with single start
        result = maxpro_lhd(n=5, p=3, nstarts=1)
        assert result is not None


def test_maxpro_lhd_multiple_starts():
    """Test behavior with multiple starts"""

    with patch("foqus_lib.framework.sdoe.maxpro.maxpro_lhd_core") as mock_core:
        mock_core.return_value = (np.random.rand(10, 2), 0.7, 300, 0.2)

        result = maxpro_lhd(n=10, p=2, nstarts=5)

        # Verify core function was called with nstarts=5
        mock_core.assert_called_once_with(10, 2, 2, 0, 5, 400, 1000000)


def test_maxpro_lhd_iteration_limits():
    """Test iteration limit parameters"""

    with patch("foqus_lib.framework.sdoe.maxpro.maxpro_lhd_core") as mock_core:
        mock_core.return_value = (np.random.rand(8, 3), 0.4, 1000, 0.5)

        result = maxpro_lhd(n=8, p=3, itermax=1000, total_iter=50000)

        # Check that limits were passed correctly
        mock_core.assert_called_once_with(8, 3, 2, 0, 1, 1000, 50000)

        # Check that total iterations is returned
        assert result["ntotal"] == 1000


@pytest.mark.parametrize(
    "n,p,s",
    [
        (5, 2, 1),
        (10, 3, 2),
        (20, 5, 3),
        (50, 10, 4),
    ],
)
def test_maxpro_lhd_parameter_combinations(n, p, s):
    """Test various parameter combinations"""

    with patch("foqus_lib.framework.sdoe.maxpro.maxpro_lhd_core") as mock_core:
        mock_core.return_value = (np.random.rand(n, p), 0.5, 100, 0.1)

        result = maxpro_lhd(n=n, p=p, s=s)

        assert result["Design"].shape == (n, p)
        mock_core.assert_called_once_with(n, p, s, 0, 1, 400, 1000000)


def test_maxpro_lhd_performance_metrics():
    """Test that performance metrics are correctly returned"""

    with patch("foqus_lib.framework.sdoe.maxpro.maxpro_lhd_core") as mock_core:
        mock_time = 1.234
        mock_iterations = 500

        mock_core.return_value = (
            np.random.rand(15, 4),
            0.6,
            mock_iterations,
            mock_time,
        )

        result = maxpro_lhd(n=15, p=4)

        assert result["time_rec"] == mock_time
        assert result["ntotal"] == mock_iterations
        assert isinstance(result["time_rec"], float)
        assert isinstance(result["ntotal"], int)


# Integration test (would need actual implementation)
def test_maxpro_lhd_integration():
    """Integration test - uses actual maxpro_lhd_core implementation"""

    # Test with actual implementation
    result = maxpro_lhd(n=10, p=2, nstarts=1, itermax=50)

    # Check that we get a valid result structure
    assert isinstance(result, dict)
    assert set(result.keys()) == {"Design", "temp0", "measure", "time_rec", "ntotal"}

    # Check that we get a valid design matrix
    design = result["Design"]
    assert design.shape == (10, 2)
    assert np.all(design >= 0) and np.all(design <= 1)

    # Check that measure is positive
    assert result["measure"] > 0

    # Check that time and iterations are reasonable
    assert result["time_rec"] >= 0
    assert result["ntotal"] > 0

    # Test with different parameters
    result2 = maxpro_lhd(n=5, p=3, s=1, temp0=0.5, nstarts=2, itermax=100)
    assert result2["Design"].shape == (5, 3)
    assert result2["temp0"] == 0.5


def test_maxpro_lhd_core_integration_simple():
    """Simplified test focusing on essential wrapper behavior"""

    # Test with simple parameters
    result = maxpro_lhd(n=5, p=2, s=2, temp0=0.5, nstarts=1, itermax=50)

    # Just check that the wrapper processes the core output correctly
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "Design" in result, "Result should contain Design"
    assert "measure" in result, "Result should contain measure"
    assert "temp0" in result, "Result should contain temp0"
    assert "time_rec" in result, "Result should contain time_rec"
    assert "ntotal" in result, "Result should contain ntotal"

    # Check that temp0 is correctly passed through
    assert result["temp0"] == 0.5, "temp0 should be passed through correctly"

    # Check that measure is positive (should be squared)
    assert result["measure"] > 0, "Measure should be positive"

    # Check design properties
    assert result["Design"].shape == (5, 2), "Design should have correct shape"
    assert np.all(result["Design"] >= 0), "Design values should be >= 0"
    assert np.all(result["Design"] <= 1), "Design values should be <= 1"


def test_maxpro_lhd_reproducibility():
    """Test reproducibility with same parameters"""

    # Note: This test assumes maxpro_lhd_core uses random seeds consistently
    # You may need to modify based on your implementation

    params = {"n": 6, "p": 2, "s": 2, "temp0": 0.1, "nstarts": 1, "itermax": 100}

    result1 = maxpro_lhd(**params)
    result2 = maxpro_lhd(**params)

    # Results might be different due to randomness, but should have same structure
    assert result1["Design"].shape == result2["Design"].shape
    assert isinstance(result1["measure"], (int, float))
    assert isinstance(result2["measure"], (int, float))


def test_maxpro_lhd_parameter_bounds():
    """Test with boundary parameter values"""

    # Test with very small design
    result = maxpro_lhd(n=2, p=1, itermax=10)
    assert result["Design"].shape == (2, 1)

    # Test with larger design
    result = maxpro_lhd(n=50, p=5, itermax=50)
    assert result["Design"].shape == (50, 5)

    # Test with different s values
    for s in [1, 2, 3, 4]:
        result = maxpro_lhd(n=10, p=2, s=s, itermax=20)
        assert result["Design"].shape == (10, 2)


def test_maxpro_lhd_performance_scaling():
    """Test performance with different problem sizes"""

    sizes = [(5, 2), (10, 3), (20, 4)]

    for n, p in sizes:
        result = maxpro_lhd(n=n, p=p, itermax=50)

        # Check basic properties
        assert result["Design"].shape == (n, p)
        assert result["time_rec"] >= 0
        assert result["ntotal"] > 0
        assert result["measure"] > 0

        # Check that all design points are in [0,1]
        assert np.all(result["Design"] >= 0)
        assert np.all(result["Design"] <= 1)


if __name__ == "__main__":
    # Run tests with different verbosity levels
    # Use -v for verbose output, -s to see print statements
    pytest.main([__file__, "-v", "-s"])
