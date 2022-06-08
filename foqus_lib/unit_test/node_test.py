###############################################################################
# FOQUS Copyright (c) 2012 - 2021, by the software owners: Oak Ridge Institute
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
#
###############################################################################
from foqus_lib.framework.graph.node import *
import pytest


class TestImports:

    def test_import_tensorflow_failure(self):

        # method loaded from node module as * import
        load = attempt_load_tensorflow(try_imports=False)

        # check that the returned load function prints the expected warning
        with pytest.raises(ModuleNotFoundError):
            load(None)

    def test_import_sympy_failure(self):

        # method loaded from node module as * import
        parse, symbol, solve = attempt_load_sympy(try_imports=False)

        # check that the returned functions print the expected warnings
        with pytest.raises(ModuleNotFoundError):
            parse(None)
        with pytest.raises(ModuleNotFoundError):
            symbol(None)
        with pytest.raises(ModuleNotFoundError):
            solve(None)

    def test_import_tensorflow_success(self):
        # skip this test if tensorflow is not available
        pytest.importorskip("tensorflow", reason="tensorflow not installed")

        # method loaded from node module as * import
        load = attempt_load_tensorflow(try_imports=True)

        # check that the returned function expects the correct input as a way
        # of confirming that the class (function) type is correct
        with pytest.raises(OSError):
            load(None)  # expects HDF5 filepath, should throw load path error

    def test_import_sympy_success(self):
        pytest.importorskip("sympy", reason="sympy not installed")

        # method loaded from node module as * import
        parse, symbol, solve = attempt_load_sympy(try_imports=True)

        # check that the returned functions expect the correct input as a way
        # of confirming that the class (function) types are correct
        with pytest.raises(AttributeError):
            parse(None)  # should fail to find attribute 'strip'
        with pytest.raises(TypeError):
            symbol(None)  # should fail to create symbol from non-string
        with pytest.raises(AttributeError):
            solve(None)  # should fail to find attribute 'free_symbols'
