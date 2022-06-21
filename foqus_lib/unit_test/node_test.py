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
from foqus_lib.framework.graph.node import (
    attempt_load_tensorflow,
    attempt_load_sympy,
    pymodel_ml_ai,
)
import unittest
import os
import pytest

curdir = os.getcwd()
if "unit_test" in curdir:  # current directory is models directory
    modelsdir = curdir
else:  # somehow a different home directory is being used (CI client)
    modelsdir = os.path.join(os.path.join(curdir, "foqus_lib"), "unit_test")


class testImports(unittest.TestCase):
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
        # skip this test if tensorflow is not available
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


# ----------------------------------------------------------------------------
# The goal of these methods is to test the core functionality of the node build
# script, focusing only on steps after the node and model type (ML AI = 5)
# are set but before the results are passed back to the graph. The node run
# method is tested for exception behavior only, not run status (this is handled
# in the main ML AI test module)

# for maximum coverage/stability, if tensorflow is not available all tests
# using the fixtures are skipped; if sympy is not available, only tests
# requiring sympy as skipped on a individual basis


class TestPymodelMLAI:

    # create fixture for loading ML AI models for testing
    # models are loaded directly from data folder so they don't need to be
    # copied to a temporary directory
    # will only need to load each model once and modify attributes from there

    @pytest.fixture(scope="function")
    def example_1(self):  # no custom layer or normalization
        # no tests using this fixture should run if tensorflow is not installed
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # the models are all loaded a single time, and copies of individual
        # models are modified to test model exceptions

        load = attempt_load_tensorflow()  # alias for load method

        # has no custom layer or normalization
        model = load(os.path.join(modelsdir, "AR_nocustomlayer.h5"))

        return model

    @pytest.fixture(scope="function")
    def example_2(self):  # custom layer with preset normalization form
        # no tests using this fixture should run if tensorflow is not installed
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # the models are all loaded a single time, and copies of individual
        # models are modified to test model exceptions

        load = attempt_load_tensorflow()  # alias for load method
        from foqus_lib.unit_test import mea_column_model

        # has a custom layer with a preset normalization option
        model = load(
            os.path.join(modelsdir, "mea_column_model.h5"),
            custom_objects={"mea_column_model": mea_column_model.mea_column_model},
        )

        return model

    @pytest.fixture(scope="function")
    def example_3(self):  # custom layer with custom normalization form
        # no tests using this fixture should run if tensorflow is not installed
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # the models are all loaded a single time, and copies of individual
        # models are modified to test model exceptions

        load = attempt_load_tensorflow()  # alias for load method
        from foqus_lib.unit_test import mea_column_model_custom_norm_form

        # has a custom layer with a custom normalization option
        model = load(
            os.path.join(modelsdir, "mea_column_model_custom_norm_form.h5"),
            custom_objects={
                "mea_column_model_custom_norm_form": mea_column_model_custom_norm_form.mea_column_model_custom_norm_form
            },
        )

        return model

    # ----------------------------------------------------------------------------
    # this set of tests builds and runs the pymodel class, and checks functionality
    # these tests are intended to test functionality and calculations, not results,
    # for the scaling tests, the results may be incorrect for bad scaling but
    # the formulas should yield the expected values (which is what is tested here)

    def test_build_and_run_as_expected_1(self, example_1):
        # test that the loaded models run with no issues without modifications
        # as in subsequent tests, an alias is created to preserve the fixture
        test_pymodel = pymodel_ml_ai(example_1)
        test_pymodel.run()

    def test_build_and_run_as_expected_2(self, example_2):
        # test that the loaded models run with no issues without modifications
        # as in subsequent tests, an alias is created to preserve the fixture
        test_pymodel = pymodel_ml_ai(example_2)
        test_pymodel.run()

    def test_build_and_run_as_expected_3(self, example_3):
        # only run if SymPy if available; test run for custom norm example
        pytest.importorskip("sympy", reason="sympy not installed")
        # test that the loaded models run with no issues without modifications
        # as in subsequent tests, an alias is created to preserve the fixture
        test_pymodel = pymodel_ml_ai(example_3)
        test_pymodel.run()

    def test_defaults_no_custom_layer(self, example_1):
        test_pymodel = pymodel_ml_ai(example_1)

        dummyidx = 0
        for idx in test_pymodel.inputs:
            dummyidx += 1
            d = test_pymodel.inputs[idx].saveDict()

            assert idx == "x" + str(dummyidx)
            assert d["min"] == pytest.approx(0, abs=1e-5)
            assert d["max"] == pytest.approx(1e5, rel=1e-5)
            assert d["value"] == pytest.approx((d["min"] + d["max"]) * 0.5, rel=1e-5)
            assert d["desc"] == "input var " + str(dummyidx)

        dummyidx = 0
        for idx in test_pymodel.outputs:
            dummyidx += 1
            d = test_pymodel.outputs[idx].saveDict()

            assert idx == "z" + str(dummyidx)
            assert d["min"] == pytest.approx(0, abs=1e-5)
            assert d["max"] == pytest.approx(1e5, rel=1e-5)
            assert d["value"] == pytest.approx((d["min"] + d["max"]) * 0.5, rel=1e-5)
            assert d["desc"] == "output var " + str(dummyidx)

        assert test_pymodel.normalized is False

    def test_no_scaling(self, example_2):
        test_pymodel = pymodel_ml_ai(example_2)
        setattr(test_pymodel, "normalized", False)
        test_pymodel.run()

        scaled_in = test_pymodel.scaled_inputs
        scaled_out = test_pymodel.scaled_outputs
        unscaled_out = [test_pymodel.outputs[idx].value for idx in test_pymodel.outputs]

        expected_in = [
            2499.82,
            0.191561,
            5759.63,
            189.973,
            0.315366,
            0.199638,
        ]  # these are actual inputs
        expected_out = [1.00000, 0.00000]
        expected_soln = [1.00000, 0.00000]  # no scaling gives bad output

        for i in range(len(scaled_in)):
            print("i = ", str(i))  # for debugging, fails on last idx printed
            assert scaled_in[i] == pytest.approx(expected_in[i], rel=1e-5)
        for j in range(len(scaled_out)):
            print("j = ", str(j))  # for debugging, fails on last idx printed
            assert scaled_out[j] == pytest.approx(expected_out[j], rel=1e-5)
        for k in range(len(unscaled_out)):
            print("k = ", str(k))  # for debugging, fails on last idx printed
            assert unscaled_out[k] == pytest.approx(expected_soln[k], rel=1e-5)

    def test_linear_scaling(self, example_2):
        test_pymodel = pymodel_ml_ai(example_2)
        setattr(test_pymodel.model.layers[1], "normalization_form", "Linear")
        test_pymodel.run()

        scaled_in = test_pymodel.scaled_inputs
        scaled_out = test_pymodel.scaled_outputs
        unscaled_out = [test_pymodel.outputs[idx].value for idx in test_pymodel.outputs]

        expected_in = [0.500000, 0.500000, 0.500000, 0.500000, 0.500000, 0.500000]
        expected_out = [0.649966, 0.0181869]
        expected_soln = [78.5314, 3.28505]  # best scaling for this problem

        for i in range(len(scaled_in)):
            print("i = ", str(i))  # for debugging, fails on last idx printed
            assert scaled_in[i] == pytest.approx(expected_in[i], rel=1e-5)
        for j in range(len(scaled_out)):
            print("j = ", str(j))  # for debugging, fails on last idx printed
            assert scaled_out[j] == pytest.approx(expected_out[j], rel=1e-5)
        for k in range(len(unscaled_out)):
            print("k = ", str(k))  # for debugging, fails on last idx printed
            assert unscaled_out[k] == pytest.approx(expected_soln[k], rel=1e-5)

    def test_log_scaling(self, example_2):
        test_pymodel = pymodel_ml_ai(example_2)
        setattr(test_pymodel.model.layers[1], "normalization_form", "Log")
        test_pymodel.run()

        scaled_in = test_pymodel.scaled_inputs
        scaled_out = test_pymodel.scaled_outputs
        unscaled_out = [test_pymodel.outputs[idx].value for idx in test_pymodel.outputs]

        expected_in = [0.550111, 0.523938, 0.554206, 0.513060, 0.527202, 0.629837]
        expected_out = [0.518656, 0.00672531]
        expected_soln = [63.3111, 3.2209]

        for i in range(len(scaled_in)):
            print("i = ", str(i))  # for debugging, fails on last idx printed
            assert scaled_in[i] == pytest.approx(expected_in[i], rel=1e-5)
        for j in range(len(scaled_out)):
            print("j = ", str(j))  # for debugging, fails on last idx printed
            assert scaled_out[j] == pytest.approx(expected_out[j], rel=1e-5)
        for k in range(len(unscaled_out)):
            print("k = ", str(k))  # for debugging, fails on last idx printed
            assert unscaled_out[k] == pytest.approx(expected_soln[k], rel=1e-5)

    def test_power_scaling(self, example_2):
        # For this example, the inputs values for some variables are large per
        # the expected_in in the no_scaling test above, and attempting to scale
        # by 10^value breaks the intepreter with a math overflow error
        # To test this method, we need to arbitrarily scale down the values.
        # An issue like this would not break the plugin, as the user would not
        # be able to train the neural network with this formulation at all.
        # Therefore, a brute force fix is okay for this test.
        test_model = example_2
        for var in test_model.layers[1].input_bounds:
            # scale down the bounds; the default values will be (min + max)/2
            test_model.layers[1].input_bounds[var][0] *= 0.01  # input_min
            test_model.layers[1].input_bounds[var][1] *= 0.01  # input_max

        test_pymodel = pymodel_ml_ai(test_model)
        setattr(test_pymodel.model.layers[1], "normalization_form", "Power")
        test_pymodel.run()

        scaled_in = test_pymodel.scaled_inputs
        scaled_out = test_pymodel.scaled_outputs
        unscaled_out = [test_pymodel.outputs[idx].value for idx in test_pymodel.outputs]

        # note that these values can't be compared to the other test results
        # since the input data was scaled down by a factor of 100
        expected_in = [1.05368e-05, 0.499895, 4.06959e-13, 0.443145, 0.499803, 0.499430]
        expected_out = [0.646331, 0.0269324]
        expected_soln = [99.7962, 6.21637]

        for i in range(len(scaled_in)):
            print("i = ", str(i))  # for debugging, fails on last idx printed
            assert scaled_in[i] == pytest.approx(expected_in[i], rel=1e-5)
        for j in range(len(scaled_out)):
            print("j = ", str(j))  # for debugging, fails on last idx printed
            assert scaled_out[j] == pytest.approx(expected_out[j], rel=1e-5)
        for k in range(len(unscaled_out)):
            print("k = ", str(k))  # for debugging, fails on last idx printed
            assert unscaled_out[k] == pytest.approx(expected_soln[k], rel=1e-5)

    def test_log2_scaling(self, example_2):
        test_pymodel = pymodel_ml_ai(example_2)
        setattr(test_pymodel.model.layers[1], "normalization_form", "Log 2")
        test_pymodel.run()

        scaled_in = test_pymodel.scaled_inputs
        scaled_out = test_pymodel.scaled_outputs
        unscaled_out = [test_pymodel.outputs[idx].value for idx in test_pymodel.outputs]

        expected_in = [0.740363, 0.740363, 0.740363, 0.740363, 0.740363, 0.740363]
        expected_out = [0.411243, 0.00187266]
        expected_soln = [49.43844, 3.20389]

        for i in range(len(scaled_in)):
            print("i = ", str(i))  # for debugging, fails on last idx printed
            assert scaled_in[i] == pytest.approx(expected_in[i], rel=1e-5)
        for j in range(len(scaled_out)):
            print("j = ", str(j))  # for debugging, fails on last idx printed
            assert scaled_out[j] == pytest.approx(expected_out[j], rel=1e-5)
        for k in range(len(unscaled_out)):
            print("k = ", str(k))  # for debugging, fails on last idx printed
            assert unscaled_out[k] == pytest.approx(expected_soln[k], rel=1e-5)

    def test_power2_scaling(self, example_2):
        test_pymodel = pymodel_ml_ai(example_2)
        setattr(test_pymodel.model.layers[1], "normalization_form", "Power 2")
        test_pymodel.run()

        scaled_in = test_pymodel.scaled_inputs
        scaled_out = test_pymodel.scaled_outputs
        unscaled_out = [test_pymodel.outputs[idx].value for idx in test_pymodel.outputs]

        expected_in = [-0.648636, -0.648636, -0.648636, -0.648636, -0.648636, -0.648636]
        expected_out = [0.956094, 0.768611]
        expected_soln = [157.278, 11.6360]

        for i in range(len(scaled_in)):
            print("i = ", str(i))  # for debugging, fails on last idx printed
            assert scaled_in[i] == pytest.approx(expected_in[i], rel=1e-5)
        for j in range(len(scaled_out)):
            print("j = ", str(j))  # for debugging, fails on last idx printed
            assert scaled_out[j] == pytest.approx(expected_out[j], rel=1e-5)
        for k in range(len(unscaled_out)):
            print("k = ", str(k))  # for debugging, fails on last idx printed
            assert unscaled_out[k] == pytest.approx(expected_soln[k], rel=1e-5)

    def test_custom_scaling(self, example_3):
        # only run if SymPy if available; checks custom form of linear scaling
        pytest.importorskip("sympy", reason="sympy not installed")

        test_pymodel = pymodel_ml_ai(example_3)
        test_pymodel.run()

        scaled_in = test_pymodel.scaled_inputs
        scaled_out = test_pymodel.scaled_outputs
        unscaled_out = [test_pymodel.outputs[idx].value for idx in test_pymodel.outputs]
        print()
        print(unscaled_out)

        expected_in = [0.500000, 0.500000, 0.500000, 0.500000, 0.500000, 0.500000]
        expected_out = [0.649966, 0.0181869]
        expected_soln = [78.5314, 3.28505]

        for i in range(len(scaled_in)):
            print("i = ", str(i))  # for debugging, fails on last idx printed
            assert scaled_in[i] == pytest.approx(expected_in[i], rel=1e-5)
        for j in range(len(scaled_out)):
            print("j = ", str(j))  # for debugging, fails on last idx printed
            assert scaled_out[j] == pytest.approx(expected_out[j], rel=1e-5)
        for k in range(len(unscaled_out)):
            print("k = ", str(k))  # for debugging, fails on last idx printed
            assert unscaled_out[k] == pytest.approx(expected_soln[k], rel=1e-5)

    # ----------------------------------------------------------------------------
    # this set of tests bulids and runs the pymodel class, and checks exceptions

    def test_no_norm_form(self, example_2):
        test_pymodel = pymodel_ml_ai(example_2)

        # check that fixture contained expected attributes
        assert test_pymodel.normalized is True  # flag to check norm form
        assert test_pymodel.model.layers[1].normalization_form == "Linear"

        # delete the attrbute and check that proper exception is thrown
        delattr(test_pymodel.model.layers[1], "normalization_form")

        with pytest.raises(AttributeError):
            test_pymodel.run()

    def test_disallowed_norm_form(self, example_2):
        test_pymodel = pymodel_ml_ai(example_2)

        # check that fixture contained expected attributes
        assert test_pymodel.normalized is True  # flag to check norm form
        assert test_pymodel.model.layers[1].normalization_form == "Linear"

        # set to disallowed value and check that proper exception is thrown
        setattr(test_pymodel.model.layers[1], "normalization_form", "linear")

        with pytest.raises(AttributeError):
            test_pymodel.run()

    def test_no_norm_function(self, example_3):
        test_pymodel = pymodel_ml_ai(example_3)

        # check that fixture contained expected attributes
        assert test_pymodel.normalized is True  # flag to check norm form
        assert test_pymodel.model.layers[1].normalization_form == "Custom"
        assert (
            test_pymodel.model.layers[1].normalization_function
            == "(datavalue - dataminimum)/(datamaximum - dataminimum)"
        )

        # delete the attrbute and check that proper exception is thrown
        delattr(test_pymodel.model.layers[1], "normalization_function")

        with pytest.raises(AttributeError):
            test_pymodel.run()

    def test_nonstring_norm_function(self, example_3):
        test_pymodel = pymodel_ml_ai(example_3)

        # check that fixture contained expected attributes
        assert test_pymodel.normalized is True  # flag to check norm form
        assert test_pymodel.model.layers[1].normalization_form == "Custom"
        assert (
            test_pymodel.model.layers[1].normalization_function
            == "(datavalue - dataminimum)/(datamaximum - dataminimum)"
        )

        # set to disallowed type and check that proper exception is thrown
        setattr(test_pymodel.model.layers[1], "normalization_function", None)

        with pytest.raises(TypeError):
            test_pymodel.run()

    def test_no_datavalue_reference(self, example_3):
        test_pymodel = pymodel_ml_ai(example_3)

        # check that fixture contained expected attributes
        assert test_pymodel.normalized is True  # flag to check norm form
        assert test_pymodel.model.layers[1].normalization_form == "Custom"
        assert (
            test_pymodel.model.layers[1].normalization_function
            == "(datavalue - dataminimum)/(datamaximum - dataminimum)"
        )

        # set to disallowed value and check that proper exception is thrown
        setattr(
            test_pymodel.model.layers[1],
            "normalization_function",
            "(value - dataminimum)/(datamaximum - dataminimum)",
        )

        with pytest.raises(ValueError):
            test_pymodel.run()

    def test_no_dataminimum_reference(self, example_3):
        test_pymodel = pymodel_ml_ai(example_3)

        # check that fixture contained expected attributes
        assert test_pymodel.normalized is True  # flag to check norm form
        assert test_pymodel.model.layers[1].normalization_form == "Custom"
        assert (
            test_pymodel.model.layers[1].normalization_function
            == "(datavalue - dataminimum)/(datamaximum - dataminimum)"
        )

        # set to disallowed value and check that proper exception is thrown
        setattr(
            test_pymodel.model.layers[1],
            "normalization_function",
            "(datavalue - minimum)/(datamaximum - minimum)",
        )

        with pytest.raises(ValueError):
            test_pymodel.run()

    def test_no_datamaximum_reference(self, example_3):
        test_pymodel = pymodel_ml_ai(example_3)

        # check that fixture contained expected attributes
        assert test_pymodel.normalized is True  # flag to check norm form
        assert test_pymodel.model.layers[1].normalization_form == "Custom"
        assert (
            test_pymodel.model.layers[1].normalization_function
            == "(datavalue - dataminimum)/(datamaximum - dataminimum)"
        )

        # set to disallowed value and check that proper exception is thrown
        setattr(
            test_pymodel.model.layers[1],
            "normalization_function",
            "(datavalue - dataminimum)/(maximum - dataminimum)",
        )

        with pytest.raises(ValueError):
            test_pymodel.run()

    def test_parse_norm_function(self, example_3):
        # only run if SymPy if available; checks syntax of passed norm function
        pytest.importorskip("sympy", reason="sympy not installed")

        test_pymodel = pymodel_ml_ai(example_3)

        # check that fixture contained expected attributes
        assert test_pymodel.normalized is True  # flag to check norm form
        assert test_pymodel.model.layers[1].normalization_form == "Custom"
        assert (
            test_pymodel.model.layers[1].normalization_function
            == "(datavalue - dataminimum)/(datamaximum - dataminimum)"
        )

        # set to disallowed value and check that proper exception is thrown
        setattr(
            test_pymodel.model.layers[1],
            "normalization_function",
            "(datavalue - dataminimum) * (datamaximum - dataminimum)^(-1)",
        )

        with pytest.raises(TypeError):
            # the user is presented with a ValueError in the console, but SymPy
            # throws a TypeError as well which supercedes it
            test_pymodel.run()

    def test_solve_norm_function(self, example_3):
        # only run if SymPy if available; checks solve of passed norm function
        pytest.importorskip("sympy", reason="sympy not installed")

        test_pymodel = pymodel_ml_ai(example_3)

        # check that fixture contained expected attributes
        assert test_pymodel.normalized is True  # flag to check norm form
        assert test_pymodel.model.layers[1].normalization_form == "Custom"
        assert (
            test_pymodel.model.layers[1].normalization_function
            == "(datavalue - dataminimum)/(datamaximum - dataminimum)"
        )

        # set to nonsolveable form and check that proper exception is thrown
        setattr(
            test_pymodel.model.layers[1],
            "normalization_function",
            "(datavalue - dataminimum**datavalue) * "
            + " (datamaximum**datavalue - dataminimum**datavalue)",
        )
        # SymPy can't solve this form, no algorithms are implemented (yet)
        # SymPy is extremely stable, so this is unlikely to happen unless
        # forced (as in this test) - "good practice" norm forms shouldn't fail

        with pytest.raises(NotImplementedError):
            # the user is presented with a ValueError in the console, but SymPy
            # throws a NotImplementedError as well which supercedes it
            test_pymodel.run()
