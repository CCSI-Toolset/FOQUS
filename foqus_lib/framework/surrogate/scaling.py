import copy
import json
import logging
import math
from collections import OrderedDict

import numpy as np


def validate_for_scaling(array_in, lo, hi) -> None:
    if not np.all(np.isfinite(array_in)):
        raise ValueError("Input data cannot contain NaN or inf values")
    if array_in.ndim != 1:
        raise ValueError("Only 1D arrays supported")
    if array_in.size < 2:
        raise ValueError("Array must have at least 2 values")
    if lo == hi:
        raise ValueError("Array must contain non-identical values")
    if not check_under_or_overflow(array_in):
        raise ValueError("Array contains under/overflow values for dtype")        

def check_under_or_overflow(arr):
    if np.issubdtype(arr.dtype, np.integer):
        info = np.iinfo(arr.dtype)
    elif np.issubdtype(arr.dtype, np.floating):
        info = np.finfo(arr.dtype)
    else:
        raise ValueError("Unsupported data type")
    max_value = info.max 
    min_value = info.min
    return np.all(arr < max_value) & np.all(arr > min_value)


def scale_linear(array_in, lo=None, hi=None):
    if lo is None:
        lo = np.min(array_in)
    if hi is None:
        hi = np.max(array_in)
    validate_for_scaling(array_in, lo, hi)
    if (hi - lo) == 0:
        result = 0
    else:
        result = (array_in - lo) / (hi - lo)
    return result

def scale_log(array_in, lo=None, hi=None):
# need to account for log domain 
    if np.any(array_in <= 0):
        raise ValueError("All values must be > 0 to use scale_log")
    if lo is None:
        lo = np.min(array_in)
    if hi is None:
        hi = np.max(array_in)
    validate_for_scaling(array_in, lo, hi)
    result = ((np.log10(array_in) - np.log10(lo))
                 / (np.log10(hi) - np.log10(lo)))
    return result

def scale_log2(array_in, lo=None, hi=None):
    if lo is None:
        lo = np.min(array_in)
    if hi is None:
        hi = np.max(array_in)
    validate_for_scaling(array_in, lo, hi)
    result = np.log10(9 * (array_in - lo) / (hi - lo) + 1)
    return result
# fix expected values in test

def scale_power(array_in, lo=None, hi=None):
    if lo is None:
        lo = np.min(array_in)
    if hi is None:
        hi = np.max(array_in)
    validate_for_scaling(array_in, lo, hi)
    result = (np.power(10, array_in) - np.power(10, lo)) / (np.power(10, hi) - np.power(10, lo))
    return result

def scale_power2(array_in, lo=None, hi=None):
    if lo is None:
        lo = np.min(array_in)
    if hi is None:
        hi = np.max(array_in)
    validate_for_scaling(array_in, lo, hi)
    result = (1/9 *
                (np.power(10, (array_in - lo) / (hi - lo)) - 1)
                )
    return result

def unscale_linear(array_in, lo, hi):
    result = array_in * (hi - lo) / 1.0 + lo
    return result

def unscale_log(array_in, lo, hi):
    result = lo * np.power(hi / lo, array_in)

    # result = ((np.log10(array_in) - np.log10(lo))
    #              / (np.log10(hi) - np.log10(lo)))
# out = math.pow(lo * (hi / lo), (array_in / 10.0))
#                 out = (
#                     10
#                     * (math.log10(array_in) - math.log10(lo))
#                     / (math.log10(hi) - math.log10(lo))
#                 )
    return result

def unscale_log2(array_in, lo=None, hi=None):
    result = (np.power(10, array_in / 1.0) - 1) * (
                        hi - lo
                    ) / 9.0 + lo
                # out = (math.pow(10, array_in / 10.0) - 1) * (
                #     hi - lo
                # ) / 9.0 + lo
                
    return result

def unscale_power(array_in, lo, hi):
    # check if lo and hi were provided 
    # result = np.log10((array_in / 10.0) * (np.power(10, hi) - np.power(10, lo))
    #                 + np.power(10, lo))
    result = np.log10(
                    (array_in / 1.0) * (np.power(10, hi) - np.power(10, lo))
                    + np.power(10, lo)
                )
    return result

def unscale_power2(array_in, lo, hi):
    result = (
                    np.log10(9.0 * array_in / 1.0 + 1) * (hi - lo) + lo
                )
    return result

class BaseScaler:

    def fit(self, X: np.ndarray):
        self.lo_ = np.min(X)
        self.hi_ = np.max(X)
        return self

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return (
            self
            .fit(X)
            .transform(X)
        )

    def transform(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError


class LinearScaler(BaseScaler):
    def transform(self, X: np.ndarray) -> np.ndarray:
        return scale_linear(X, self.lo_, self.hi_)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        return unscale_linear(X, self.lo_, self.hi_)
    
class LogScaler(BaseScaler):
    def transform(self, X: np.ndarray) -> np.ndarray:
        return scale_log(X, self.lo_, self.hi_)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        return unscale_log(X, self.lo_, self.hi_)

class LogScaler2(BaseScaler):
    def transform(self, X: np.ndarray) -> np.ndarray:
        return scale_log2(X, self.lo_, self.hi_)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        return unscale_log2(X, self.lo_, self.hi_)

class PowerScaler(BaseScaler):
    def transform(self, X: np.ndarray) -> np.ndarray:
        return scale_power(X, self.lo_, self.hi_)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        return unscale_power(X, self.lo_, self.hi_)

class PowerScaler2(BaseScaler):
    def transform(self, X: np.ndarray) -> np.ndarray:
        return scale_power2(X, self.lo_, self.hi_)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        return unscale_power2(X, self.lo_, self.hi_)
    