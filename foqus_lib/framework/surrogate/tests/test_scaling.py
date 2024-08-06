import numpy as np
import pytest
from foqus_lib.framework.surrogate.scaling import (
    scale_linear,
    unscale_linear,
    scale_log,
    unscale_log,
    scale_log2,
    unscale_log2,
    scale_power,
    unscale_power,
    scale_power2,
    unscale_power2,
    validate_for_scaling,
    map_name_to_scaler,
    BaseScaler,
    LinearScaler,
    LogScaler,
    LogScaler2,
    PowerScaler,
    PowerScaler2,
)

from hypothesis.extra import numpy as hypothesis_np
from hypothesis import given, example, assume
from contextlib import contextmanager

POSITIVE_VALS_ONLY = {scale_log}


@contextmanager
def does_not_raise():
    yield


def test_scale_linear():
    # Test case 1: Basic scaling
    input_array = np.array([1, 2, 3, 4, 5])
    scaled_array = scale_linear(input_array)
    assert np.all(scaled_array >= 0)
    assert np.all(scaled_array <= 1)
    assert np.allclose(scaled_array, [0.0, 0.25, 0.5, 0.75, 1.0])

    # Test case 2: Custom range scaling
    input_array = np.array([10, 20, 30, 40, 50])
    scaled_array = scale_linear(input_array, lo=10, hi=50)
    assert np.all(scaled_array >= 0)
    assert np.all(scaled_array <= 1)
    assert np.allclose(scaled_array, [0.0, 0.25, 0.5, 0.75, 1.0])

    # Test case 3: Scaling with negative values
    input_array = np.array([-5, 0, 5])
    scaled_array = scale_linear(input_array)
    assert np.all(scaled_array >= 0)
    assert np.all(scaled_array <= 1)
    assert np.allclose(scaled_array, [0.0, 0.5, 1.0])


def test_unscale_linear():
    # Test case 1: Basic unscaling
    input_array = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    unscaled_array = unscale_linear(input_array, lo=1, hi=5)
    assert np.allclose(unscaled_array, [1, 2, 3, 4, 5])

    # Test case 2: Custom range unscaling
    input_array = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    unscaled_array = unscale_linear(input_array, lo=10, hi=50)
    assert np.allclose(unscaled_array, [10, 20, 30, 40, 50])

    # Test case 3: Unscaling with negative values
    input_array = np.array([0.0, 0.5, 1.0])
    unscaled_array = unscale_linear(input_array, lo=-5, hi=5)
    assert np.allclose(unscaled_array, [-5, 0, 5])

    # Test case 4: Unscaling with repeated values
    input_array = np.array([0.0, 0.0, 0.0, 0.0])
    unscaled_array = unscale_linear(input_array, lo=0, hi=5)
    assert np.allclose(unscaled_array, [0, 0, 0, 0])


def test_scale_log():
    # Test case 1: Basic log scaling
    input_array = np.array([1, 2, 3, 4, 5])
    scaled_array = scale_log(input_array)
    assert np.all(scaled_array >= 0)
    assert np.all(scaled_array <= 1)
    assert np.allclose(scaled_array, [0.0, 0.43067656, 0.68260619, 0.86135312, 1.0])

    # Test case 2: Custom range log scaling
    input_array = np.array([10, 20, 30, 40, 50])
    scaled_array = scale_log(input_array, lo=10, hi=50)
    assert np.all(scaled_array >= 0)
    assert np.all(scaled_array <= 1)
    assert np.allclose(scaled_array, [0.0, 0.43067656, 0.68260619, 0.86135312, 1.0])


def test_scale_log2():
    # Test case 1: Basic log2 scaling
    input_array = np.array([1, 2, 3, 4, 5])
    scaled_array = scale_log2(input_array)
    assert np.all(scaled_array >= 0)
    assert np.all(scaled_array <= 1)
    assert np.allclose(scaled_array, [0.0, 0.51188336, 0.74036269, 0.8893017, 1.0])

    # Test case 2: Custom range log2 scaling
    input_array = np.array([10, 20, 30, 40, 50])
    scaled_array = scale_log2(input_array, lo=10, hi=50)
    assert np.all(scaled_array >= 0)
    assert np.all(scaled_array <= 1)
    assert np.allclose(scaled_array, [0.0, 0.51188336, 0.74036269, 0.8893017, 1.0])


def test_scale_power():
    # Test case 1: Basic power scaling
    input_array = np.array([1, 2, 3, 4, 5])
    scaled_array = scale_power(input_array)
    assert np.all(scaled_array >= 0)
    assert np.all(scaled_array <= 1)
    assert np.allclose(
        scaled_array,
        [0.00000000e00, 9.00090009e-04, 9.90099010e-03, 9.99099910e-02, 1.00000000e00],
    )

    # Test case 2: Custom range power scaling
    input_array = np.array([1.0, 4.7, 4.8, 4.999, 5.0])
    scaled_array = scale_power(input_array)
    print(scaled_array)
    assert np.all(scaled_array >= 0)
    assert np.all(scaled_array <= 1)
    assert np.allclose(scaled_array, [0.0, 0.50113735, 0.63092044, 0.99769983, 1.0])


def test_scale_power2():
    # Test case 1: Basic power scaling
    input_array = np.array([1, 2, 3, 4, 5])
    scaled_array = scale_power2(input_array)
    assert np.all(scaled_array >= 0)
    assert np.all(scaled_array <= 1)
    assert np.allclose(scaled_array, [0.0, 0.08647549, 0.24025307, 0.51371258, 1.0])

    # Test case 2: Custom range power scaling
    input_array = np.array([1.0, 4.7, 4.8, 4.999, 5.0])
    scaled_array = scale_power2(input_array)
    assert np.all(scaled_array >= 0)
    assert np.all(scaled_array <= 1)
    assert np.allclose(scaled_array, [0.0, 0.82377238, 0.87916771, 0.99936058, 1.0])


# @pytest.mark.xfail(reason="function formula is wrong", strict=True)
def test_unscale_log():
    input_array = np.array([0.0, 0.43067656, 0.68260619, 0.86135312, 1.0])
    unscaled_array = unscale_log(input_array, lo=1, hi=5)
    assert np.allclose(unscaled_array, [1, 2, 3, 4, 5])

    input_array = np.array([0.0, 0.43067656, 0.68260619, 0.86135312, 1.0])
    unscaled_array = unscale_log(input_array, lo=10, hi=50)
    assert np.allclose(unscaled_array, [10, 20, 30, 40, 50])


def test_unscale_log2():
    input_array = np.array([0.0, 0.51188336, 0.74036269, 0.8893017, 1.0])
    unscaled_array = unscale_log2(input_array, lo=1, hi=5)
    assert np.allclose(unscaled_array, [1, 2, 3, 4, 5])

    input_array = np.array([0.0, 0.51188336, 0.74036269, 0.8893017, 1.0])
    unscaled_array = unscale_log2(input_array, lo=10, hi=50)
    assert np.allclose(unscaled_array, [10, 20, 30, 40, 50])


def test_unscale_power():
    input_array = np.array(
        [0.00000000e00, 9.00090009e-04, 9.90099010e-03, 9.99099910e-02, 1.00000000e00]
    )
    unscaled_array = unscale_power(input_array, lo=1, hi=5)
    assert np.allclose(unscaled_array, [1, 2, 3, 4, 5])

    input_array = np.array([0.0, 0.50113735, 0.63092044, 0.99769983, 1.0])
    unscaled_array = unscale_power(input_array, lo=1.0, hi=5.0)
    assert np.allclose(unscaled_array, [1.0, 4.7, 4.8, 4.999, 5.0])


def test_unscale_power2():
    input_array = np.array([0.0, 0.08647549, 0.24025307, 0.51371258, 1.0])
    unscaled_array = unscale_power2(input_array, lo=1, hi=5)
    assert np.allclose(unscaled_array, [1, 2, 3, 4, 5])

    input_array = np.array([0.0, 0.82377238, 0.87916771, 0.99936058, 1.0])
    unscaled_array = unscale_power2(input_array, lo=1.0, hi=5.0)
    assert np.allclose(unscaled_array, [1.0, 4.7, 4.8, 4.999, 5.0])


@given(
    x=hypothesis_np.arrays(
        np.float64,
        hypothesis_np.array_shapes(),
        # TODO: see if these bounds can be relaxed
        # larger values cause failures in scale_power
        elements={"min_value": -5, "max_value": 5},
    )
)
@pytest.mark.parametrize(
    "scale,unscale",
    [
        (scale_linear, unscale_linear),
        (scale_log, unscale_log),
        (scale_log2, unscale_log2),
        (scale_power, unscale_power),
        (scale_power2, unscale_power2),
    ],
)
def test_roundtrip(x, scale, unscale):

    lo = np.min(x)
    hi = np.max(x)
    if not passes_validation(x, lo, hi):
        expected_failure = pytest.raises(ValueError)
    elif lo < 1e-08 and scale in POSITIVE_VALS_ONLY:
        expected_failure = pytest.raises(
            ValueError, match="All values must be greater than 1e-08"
        )
    else:
        expected_failure = does_not_raise()
    with expected_failure:
        scaled = scale(x, lo=lo, hi=hi)
        unscaled = unscale(scaled, lo=lo, hi=hi)
        assert np.allclose(x, unscaled)


@pytest.mark.parametrize(
    "variant",
    [
        "Linear",
        "Log",
        "Log2",
        "Power",
        "Power2",
    ],
)
def test_use_scaler_objects(variant):
    input_array = np.array([1, 3, 5, 6, 8, 9, 10])
    scaler_instance = map_name_to_scaler[variant]

    result_arr = scaler_instance.fit_transform(input_array)

    print(result_arr)
    assert np.all(result_arr >= 0)
    assert np.all(result_arr <= 1)


def passes_validation(array_in, lo, hi):
    try:
        validate_for_scaling(array_in, lo, hi)
    except Exception:
        return False
    else:
        return True


# Run the tests
if __name__ == "__main__":
    pytest.main()
