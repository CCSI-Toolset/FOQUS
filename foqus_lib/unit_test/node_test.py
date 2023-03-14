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
from foqus_lib.framework.graph.node import (
    attempt_load_tensorflow,
    attempt_load_sympy,
    attempt_load_pytorch,
    attempt_load_sklearn,
    pymodel_ml_ai,
    Node,
    NodeEx,
)

from foqus_lib.framework.graph.graph import Graph
from foqus_lib.framework.graph.nodeModelTypes import nodeModelTypes
from foqus_lib.framework.pymodel.pymodel import pymodel
from foqus_lib.framework.pymodel import pymodel_test

from importlib import import_module
from pathlib import Path
from typing import List, Tuple
from collections import OrderedDict
import unittest
import os
import sys
import pytest


@pytest.fixture(scope="session")
def model_files(
    foqus_ml_ai_models_dir: Path,
    install_ml_ai_model_files,
    suffixes: Tuple[str] = (".py", ".h5", ".json", ".pt", ".pkl"),
) -> List[Path]:
    paths = []
    for path in sorted(foqus_ml_ai_models_dir.glob("*")):
        if all(
            [
                ((path.is_file() and path.suffix in suffixes) or path.is_dir()),
                path.stat().st_size > 0,
                path.name != "__init__.py",
            ]
        ):
            paths.append(path)
    return paths


def test_model_files_are_present(model_files: List[Path]):
    assert model_files


class testImports(unittest.TestCase):
    def test_import_tensorflow_failure(self):

        # method loaded from node module as * import
        load, json_load = attempt_load_tensorflow(try_imports=False)

        # check that the returned load functions print the expected warning
        with pytest.raises(ModuleNotFoundError):
            load(None)
        with pytest.raises(ModuleNotFoundError):
            json_load(None)

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

    def test_import_pytorch_failure(self):

        # method loaded from node module as * import
        torch_load, torch_tensor, torch_float = attempt_load_pytorch(try_imports=False)

        # check that the returned functions print the expected warnings
        with pytest.raises(ModuleNotFoundError):
            torch_load(None)
        with pytest.raises(ModuleNotFoundError):
            torch_tensor(None)
        with pytest.raises(ModuleNotFoundError):
            torch_float(None)

    def test_import_sklearn_failure(self):
        # this is a pretty common package, so this probably would never occur
        # but it's good to test the exception anyways

        # method loaded from node module as * import
        pickle_load = attempt_load_sklearn(try_imports=False)

        # check that the returned functions print the expected warnings
        with pytest.raises(ModuleNotFoundError):
            pickle_load(None)

    def test_import_tensorflow_success(self):
        # skip this test if tensorflow is not available
        pytest.importorskip("tensorflow", reason="tensorflow not installed")

        # method loaded from node module as * import
        load, json_load = attempt_load_tensorflow(try_imports=True)

        # check that the returned function expects the correct input as a way
        # of confirming that the class (function) type is correct
        with pytest.raises(OSError):
            load(None)  # expects HDF5 filepath, should throw load path error
        with pytest.raises(TypeError):
            json_load(None)  # expects JSON object, should throw type error

    def test_import_sympy_success(self):
        # skip this test if sympy is not available
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

    def test_import_pytorch_success(self):
        # skip this test if torch is not available
        pytest.importorskip("torch", reason="torch not installed")

        # method loaded from node module as * import
        torch_load, torch_tensor, torch_float = attempt_load_pytorch(try_imports=True)

        # check that the returned functions expect the correct input as a way
        # of confirming that the class (function) types are correct
        with pytest.raises(AttributeError):
            torch_load(None)  # should fail to find attribute 'read'
        with pytest.raises(RuntimeError):
            torch_tensor(None)  # should fail to infer dtype of 'None' object
        with pytest.raises(TypeError):
            torch_float(None)  # should fail to call torch.dtype object

    def test_import_sklearn_success(self):
        # skip this test if sklearn is not available
        pytest.importorskip("sklearn", reason="sklearn not installed")

        # method loaded from node module as * import
        pickle_load = attempt_load_sklearn(try_imports=True)

        # check that the returned functions expect the correct input as a way
        # of confirming that the class (function) types are correct
        with pytest.raises(TypeError):
            pickle_load(None)  # should fail to find 'read' and 'readline' attributes


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
    def example_1(self, model_files):  # no custom layer or normalization
        # no tests using this fixture should run if tensorflow is not installed
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # the models are all loaded a single time, and copies of individual
        # models are modified to test model exceptions

        load, json_load = attempt_load_tensorflow()  # alias for load methods

        # get model files from previously defined model_files pathlist
        model_h5 = [
            path for path in model_files if str(path).endswith("AR_nocustomlayer.h5")
        ]

        # has no custom layer or normalization
        model = load(model_h5[0])

        return model

    @pytest.fixture(scope="function")
    def example_2(self, model_files):  # custom layer with preset normalization form
        # no tests using this fixture should run if tensorflow is not installed
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # the models are all loaded a single time, and copies of individual
        # models are modified to test model exceptions

        load, json_load = attempt_load_tensorflow()  # alias for load methods

        # get model files from previously defined model_files pathlist
        model_h5 = [
            path for path in model_files if str(path).endswith("mea_column_model.h5")
        ]
        model_py = [
            path for path in model_files if str(path).endswith("mea_column_model.py")
        ]

        sys.path.append(os.path.dirname(model_py[0]))
        module = import_module("mea_column_model")

        # has a custom layer with a preset normalization option
        model = load(
            model_h5[0], custom_objects={"mea_column_model": module.mea_column_model}
        )

        return model

    @pytest.fixture(scope="function")
    def example_3(self, model_files):  # custom layer with custom normalization form
        # no tests using this fixture should run if tensorflow and sympy are not installed
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        pytest.importorskip("sympy", reason="sympy not installed")
        # the models are all loaded a single time, and copies of individual
        # models are modified to test model exceptions

        load, json_load = attempt_load_tensorflow()  # alias for load methods

        # get model files from previously defined model_files pathlist
        model_h5 = [
            path
            for path in model_files
            if str(path).endswith("mea_column_model_customnormform.h5")
        ]
        model_py = [
            path
            for path in model_files
            if str(path).endswith("mea_column_model_customnormform.py")
        ]

        sys.path.append(os.path.dirname(model_py[0]))
        module = import_module("mea_column_model_customnormform")

        # has a custom layer with a preset normalization option
        model = load(
            model_h5[0],
            custom_objects={
                "mea_column_model_customnormform": module.mea_column_model_customnormform
            },
        )

        return model

    @pytest.fixture(scope="function")
    def example_4(self, model_files):  # model saved in SavedModel file format
        # no tests using this fixture should run if tensorflow and sympy are not installed
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        pytest.importorskip("sympy", reason="sympy not installed")
        # the models are all loaded a single time, and copies of individual
        # models are modified to test model exceptions

        load, json_load = attempt_load_tensorflow()  # alias for load methods

        # get model files from previously defined model_files pathlist
        model_folder = [
            path
            for path in model_files
            if str(path).endswith("mea_column_model_customnormform_savedmodel")
        ]

        model_py = [
            path
            for path in model_files
            if str(path).endswith("mea_column_model_customnormform_savedmodel.py")
        ]

        sys.path.append(os.path.dirname(model_py[0]))
        module = import_module("mea_column_model_customnormform_savedmodel")

        # has a custom layer with a custom normalization option
        model = load(
            model_folder[0],
            custom_objects={
                "mea_column_model_customnormform_savedmodel": module.mea_column_model_customnormform_savedmodel
            },
        )

        return model

    @pytest.fixture(scope="function")
    def example_5(self, model_files):  # model saved in json form with h5 weights
        # no tests using this fixture should run if tensorflow and sympy are not installed
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        pytest.importorskip("sympy", reason="sympy not installed")
        # the models are all loaded a single time, and copies of individual
        # models are modified to test model exceptions

        load, json_load = attempt_load_tensorflow()  # alias for load methods

        # get model files from previously defined model_files pathlist
        model_json = [
            path
            for path in model_files
            if str(path).endswith("mea_column_model_customnormform_json.json")
        ]
        model_weights_h5 = [
            path
            for path in model_files
            if str(path).endswith("mea_column_model_customnormform_json_weights.h5")
        ]
        model_py = [
            path
            for path in model_files
            if str(path).endswith("mea_column_model_customnormform_json.py")
        ]

        sys.path.append(os.path.dirname(model_py[0]))
        module = import_module("mea_column_model_customnormform_json")

        # load json dictionary, load weights and compile
        json_path = os.path.join(
            os.path.dirname(model_py[0]), "mea_column_model_customnormform_json.json"
        )
        with open(json_path, "r") as json_file:
            loaded_json = json_file.read()
        model = json_load(
            loaded_json,
            custom_objects={
                "mea_column_model_customnormform_json": module.mea_column_model_customnormform_json
            },
        )  # load architecture
        h5_path = os.path.join(
            os.path.dirname(model_py[0]),
            "mea_column_model_customnormform_json_weights.h5",
        )
        model.load_weights(h5_path)  # load pretrained weights

        return model

    @pytest.fixture(scope="function")
    def example_6(self, model_files):  # custom layer with custom normalization form
        # no tests using this fixture should run if torch and sympy are not installed
        pytest.importorskip("torch", reason="torch not installed")
        pytest.importorskip("sympy", reason="sympy not installed")
        # the models are all loaded a single time, and copies of individual
        # models are modified to test model exceptions

        (
            torch_load,
            torch_tensor,
            torch_float,
        ) = attempt_load_pytorch()  # alias for load methods

        # get model files from previously defined model_files pathlist
        model_pt = [
            path
            for path in model_files
            if str(path).endswith("mea_column_model_customnormform_pytorch.pt")
        ]

        # has a custom layer with a custom normalization option
        model = torch_load(str(model_pt[0]))

        return model

    @pytest.fixture(scope="function")
    def example_7(self, model_files):  # custom layer with custom normalization form
        # no tests using this fixture should run if sklearn and sympy are not installed
        pytest.importorskip("sklearn", reason="sklearn not installed")
        pytest.importorskip("sympy", reason="sympy not installed")
        # the models are all loaded a single time, and copies of individual
        # models are modified to test model exceptions

        pickle_load = attempt_load_sklearn()  # alias for load method

        # get model files from previously defined model_files pathlist
        model_pkl = [
            path
            for path in model_files
            if str(path).endswith("mea_column_model_customnormform_scikitlearn.pkl")
        ]

        # has a custom layer with a custom normalization option
        with open(model_pkl[0], "rb") as file:
            model = pickle_load(file)

        return model

    # ----------------------------------------------------------------------------
    # this set of tests builds and runs the pymodel class functionality

    def test_build_and_run_as_expected_1(self, example_1):
        # test that the loaded models run with no issues without modifications
        # as in subsequent tests, an alias is created to preserve the fixture
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        test_pymodel = pymodel_ml_ai(example_1, trainer="keras")
        test_pymodel.run()

    def test_build_and_run_as_expected_2(self, example_2):
        # test that the loaded models run with no issues without modifications
        # as in subsequent tests, an alias is created to preserve the fixture
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        test_pymodel = pymodel_ml_ai(example_2, trainer="keras")
        test_pymodel.run()

    def test_build_and_run_as_expected_3(self, example_3):
        # only run if TensorFlow and SymPy are available; test run for custom norm example
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        pytest.importorskip("sympy", reason="sympy not installed")
        # test that the loaded models run with no issues without modifications
        # as in subsequent tests, an alias is created to preserve the fixture
        test_pymodel = pymodel_ml_ai(example_3, trainer="keras")
        test_pymodel.run()

    def test_build_and_run_as_expected_4(self, example_4):
        # only run if TensorFlow and SymPy are available; test run for custom norm SavedModel
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        pytest.importorskip("sympy", reason="sympy not installed")
        # test that the loaded models run with no issues without modifications
        # as in subsequent tests, an alias is created to preserve the fixture
        test_pymodel = pymodel_ml_ai(example_4, trainer="keras")
        test_pymodel.run()

    def test_build_and_run_as_expected_5(self, example_5):
        # only run if TensorFlow and SymPy are available; test run for custom norm json
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        pytest.importorskip("sympy", reason="sympy not installed")
        # test that the loaded models run with no issues without modifications
        # as in subsequent tests, an alias is created to preserve the fixture
        test_pymodel = pymodel_ml_ai(example_5, trainer="keras")
        test_pymodel.run()

    def test_build_and_run_as_expected_6(self, example_6):
        # only run if PyTorch and SymPy are available; test run for custom norm example
        pytest.importorskip("torch", reason="torch not installed")
        pytest.importorskip("sympy", reason="sympy not installed")
        # test that the loaded models run with no issues without modifications
        # as in subsequent tests, an alias is created to preserve the fixture
        test_pymodel = pymodel_ml_ai(example_6, trainer="torch")
        test_pymodel.run()

    def test_build_and_run_as_expected_7(self, example_7):
        # only run if sklearn and SymPy are available; test run for custom norm example
        pytest.importorskip("sklearn", reason="sklearn not installed")
        pytest.importorskip("sympy", reason="sympy not installed")
        # test that the loaded models run with no issues without modifications
        # as in subsequent tests, an alias is created to preserve the fixture
        test_pymodel = pymodel_ml_ai(example_7, trainer="sklearn")
        test_pymodel.run()

    def test_build_invalid_trainer_type(self, example_1):
        # note, this should never happen since users can never set this value
        with pytest.raises(
            AttributeError,
            match="Unknown file type: "
            "notavalidtype, this should not have occurred. "
            "Please contact the FOQUS developers if this error "
            "occurs; the trainer should be set internally to "
            "`keras`, 'torch' or `sklearn` and should not be "
            "able to take any other value.",
        ):
            test_pymodel = pymodel_ml_ai(example_1, trainer="notavalidtype")

    def test_run_invalid_trainer_type(self, example_1):
        # note, this should never happen since users can never set this value
        # and the error tested above will be detected and raised first
        test_pymodel = pymodel_ml_ai(example_1, trainer="keras")  # valid type
        test_pymodel.trainer = "notavalidtype"  # now change it and run
        with pytest.raises(
            AttributeError,
            match="Unknown file type: "
            "notavalidtype, this should not have occurred. "
            "Please contact the FOQUS developers if this error "
            "occurs; the trainer should be set internally to "
            "`keras`, 'torch' or `sklearn` and should not be "
            "able to take any other value.",
        ):
            test_pymodel.run()

    def test_defaults_no_custom_layer(self, example_1):
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        test_pymodel = pymodel_ml_ai(example_1, trainer="keras")

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
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        test_pymodel = pymodel_ml_ai(example_2, trainer="keras")
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
        expected_out = [1.00000, 1.00000]
        expected_soln = [1.00000, 1.00000]  # no scaling gives bad output

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
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        test_pymodel = pymodel_ml_ai(example_2, trainer="keras")
        setattr(test_pymodel.model.layers[1], "normalization_form", "Linear")
        test_pymodel.run()

        scaled_in = test_pymodel.scaled_inputs
        scaled_out = test_pymodel.scaled_outputs
        unscaled_out = [test_pymodel.outputs[idx].value for idx in test_pymodel.outputs]

        expected_in = [0.500000, 0.500000, 0.500000, 0.500000, 0.500000, 0.500000]
        expected_out = [0.664945, 0.01849853]
        expected_soln = [79.44945, 3.28648]  # best scaling for this problem

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
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        test_pymodel = pymodel_ml_ai(example_2, trainer="keras")
        setattr(test_pymodel.model.layers[1], "normalization_form", "Log")
        test_pymodel.run()

        scaled_in = test_pymodel.scaled_inputs
        scaled_out = test_pymodel.scaled_outputs
        unscaled_out = [test_pymodel.outputs[idx].value for idx in test_pymodel.outputs]

        expected_in = [0.550111, 0.523938, 0.554206, 0.513060, 0.527202, 0.629837]
        expected_out = [0.5392884, 0.0070636244]
        expected_soln = [64.56342, 3.22185]

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
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
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

        test_pymodel = pymodel_ml_ai(test_model, trainer="keras")
        setattr(test_pymodel.model.layers[1], "normalization_form", "Power")
        test_pymodel.run()

        scaled_in = test_pymodel.scaled_inputs
        scaled_out = test_pymodel.scaled_outputs
        unscaled_out = [test_pymodel.outputs[idx].value for idx in test_pymodel.outputs]

        # note that these values can't be compared to the other test results
        # since the input data was scaled down by a factor of 100
        expected_in = [1.05368e-05, 0.499895, 4.06959e-13, 0.443145, 0.499803, 0.499430]
        expected_out = [0.6696245, 0.023079345]
        expected_soln = [99.81156, 6.149386]

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
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        test_pymodel = pymodel_ml_ai(example_2, trainer="keras")
        setattr(test_pymodel.model.layers[1], "normalization_form", "Log 2")
        test_pymodel.run()

        scaled_in = test_pymodel.scaled_inputs
        scaled_out = test_pymodel.scaled_outputs
        unscaled_out = [test_pymodel.outputs[idx].value for idx in test_pymodel.outputs]

        expected_in = [0.740363, 0.740363, 0.740363, 0.740363, 0.740363, 0.740363]
        expected_out = [0.4296973, 0.0021386303]
        expected_soln = [50.200485, 3.2042003]

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
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        test_pymodel = pymodel_ml_ai(example_2, trainer="keras")
        setattr(test_pymodel.model.layers[1], "normalization_form", "Power 2")
        test_pymodel.run()

        scaled_in = test_pymodel.scaled_inputs
        scaled_out = test_pymodel.scaled_outputs
        unscaled_out = [test_pymodel.outputs[idx].value for idx in test_pymodel.outputs]

        expected_in = [-0.648636, -0.648636, -0.648636, -0.648636, -0.648636, -0.648636]
        expected_out = [0.75565094, 0.7382201]
        expected_soln = [151.01542, 11.555694]

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
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # only run if SymPy is available; checks custom form of linear scaling
        pytest.importorskip("sympy", reason="sympy not installed")

        test_pymodel = pymodel_ml_ai(example_3, trainer="keras")
        test_pymodel.run()

        scaled_in = test_pymodel.scaled_inputs
        scaled_out = test_pymodel.scaled_outputs
        unscaled_out = [test_pymodel.outputs[idx].value for idx in test_pymodel.outputs]
        print()
        print(unscaled_out)

        expected_in = [0.500000, 0.500000, 0.500000, 0.500000, 0.500000, 0.500000]
        expected_out = [0.664945, 0.01849853]
        expected_soln = [79.44945, 3.286483]

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
    # this set of tests bulids and runs the pymodel class and checks exceptions

    def test_no_norm_form(self, example_2):
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        test_pymodel = pymodel_ml_ai(example_2, trainer="keras")

        # check that fixture contained expected attributes
        assert test_pymodel.normalized is True  # flag to check norm form
        assert test_pymodel.model.layers[1].normalization_form == "Linear"

        # delete the attrbute and check that proper exception is thrown
        delattr(test_pymodel.model.layers[1], "normalization_form")

        with pytest.raises(AttributeError):
            test_pymodel.run()

    def test_disallowed_norm_form(self, example_2):
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        test_pymodel = pymodel_ml_ai(example_2, trainer="keras")

        # check that fixture contained expected attributes
        assert test_pymodel.normalized is True  # flag to check norm form
        assert test_pymodel.model.layers[1].normalization_form == "Linear"

        # set to disallowed value and check that proper exception is thrown
        setattr(test_pymodel.model.layers[1], "normalization_form", "linear")

        with pytest.raises(AttributeError):
            test_pymodel.run()

    def test_no_norm_function(self, example_3):
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # only run if SymPy is available; checks custom form of linear scaling
        pytest.importorskip("sympy", reason="sympy not installed")
        test_pymodel = pymodel_ml_ai(example_3, trainer="keras")

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
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # only run if SymPy is available; checks custom form of linear scaling
        pytest.importorskip("sympy", reason="sympy not installed")
        test_pymodel = pymodel_ml_ai(example_3, trainer="keras")

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
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # only run if SymPy is available; checks custom form of linear scaling
        pytest.importorskip("sympy", reason="sympy not installed")
        test_pymodel = pymodel_ml_ai(example_3, trainer="keras")

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
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # only run if SymPy is available; checks custom form of linear scaling
        pytest.importorskip("sympy", reason="sympy not installed")
        test_pymodel = pymodel_ml_ai(example_3, trainer="keras")

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
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # only run if SymPy is available; checks custom form of linear scaling
        pytest.importorskip("sympy", reason="sympy not installed")
        test_pymodel = pymodel_ml_ai(example_3, trainer="keras")

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
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # only run if SymPy is available; checks syntax of passed norm function
        pytest.importorskip("sympy", reason="sympy not installed")

        test_pymodel = pymodel_ml_ai(example_3, trainer="keras")

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

        with pytest.raises(ValueError):
            test_pymodel.run()

    def test_solve_norm_function(self, example_3):
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # only run if SymPy is available; checks solve of passed norm function
        pytest.importorskip("sympy", reason="sympy not installed")

        test_pymodel = pymodel_ml_ai(example_3, trainer="keras")

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

        with pytest.raises(ValueError):
            test_pymodel.run()


# ----------------------------------------------------------------------------
# The goal of these methods is to test the core functionality of the Node class
# within the node script module, with a large focus on Turbine actions


class TestNode:
    @pytest.fixture(scope="function")
    def node(self):
        # build graph, add node and return node
        gr = Graph()
        gr.addNode("testnode")
        n = Node(parent=gr, name="testnode")

        return n

    def test_init_attributes(self, node):
        # check initialized node attributes

        assert type(node) is Node

        assert node.inVars == OrderedDict()
        assert node.outVars == OrderedDict()
        assert node.inVarsVector == OrderedDict()
        assert node.outVarsVector == OrderedDict()
        assert node.modelType == 0  # MODEL_NONE
        assert node.modelName == ""
        assert node.calcCount == 0
        assert node.altInput is None
        assert node.vis is True  # whether or not to display node
        assert node.seq is True  # whether or not to include in calculations
        assert node.x == 0  # coordinate for drawing graph
        assert node.y == 0  # coordinate for drawing graph
        assert node.z == 0  # coordinate for drawing graph
        assert node.calcError == -1  # error code, 0 = good

        # node calculations
        assert node.scriptMode == "post"
        assert node.pythonCode == ""

        # Node/Model Options
        assert node.options == {}

        # Turbine stuff
        assert node.turbSession == 0  # turbine session id
        assert node.turbJobID is None  # turbine job id
        assert node.turbApp is None  # application that runs model
        assert node.turbineMessages == ""

        # Python Plugin Stuff
        assert node.pyModel is None

        #
        assert node.running is False
        assert node.synced is True

    def test_modelType(self, node):
        node.modelType = 2
        assert node.isModelTurbine is True

        node.modelType = 1
        assert node.isModelPlugin is True

        node.modelType = 5
        assert node.isModelML is True

        node.modelType = 0
        assert node.isModelNone is True

    def test_setGraph(self, node):
        assert hasattr(node, "name")
        assert hasattr(node, "inVars")
        assert hasattr(node, "outVars")
        assert hasattr(node, "inVarsVector")
        assert hasattr(node, "outVarsVector")

        delattr(node, "name")
        delattr(node, "inVars")
        delattr(node, "outVars")
        delattr(node, "inVarsVector")
        delattr(node, "outVarsVector")

        g = Graph()
        g.addNode("testnode")
        node.setGraph(g, name="testnode")

        assert node.inVars == g.input[node.name]
        assert node.outVars == g.output[node.name]
        assert node.inVarsVector == g.input_vectorlist[node.name]
        assert node.outVarsVector == g.output_vectorlist[node.name]

    def test_addTurbineOptions(self, node):
        node.addTurbineOptions()

        assert node.options["Visible"].value is False
        assert node.options["Initialize Model"].value is False
        assert node.options["Reset"].value is False
        assert node.options["Reset on Fail"].value is True
        assert node.options["Retry"].value is False
        assert node.options["Allow Simulation Warnings"].value is True
        assert node.options["Max consumer reuse"].value == 90
        assert node.options["Maximum Wait Time (s)"].value == 1440.0
        assert node.options["Maximum Run Time (s)"].value == 840.0
        assert node.options["Min Status Check Interval"].value == 4.0
        assert node.options["Max Status Check Interval"].value == 5.0
        assert node.options["Override Turbine Configuration"].value == ""

    def test_errorLookup(self, node):
        ex = NodeEx()
        ex.setCodeStrings()
        for i in [-1, 0, 1, 3, 4, 6, 5, 7, 8, 9, 10, 11, 20, 21, 23, 27, 50, 61]:
            assert node.errorLookup(i) == ex.codeString[i]

    def test_saveDict(self, node):
        sd = node.saveDict()

        assert isinstance(sd, dict)
        assert sd["modelType"] == node.modelType
        assert sd["modelName"] == node.modelName
        assert sd["x"] == node.x
        assert sd["y"] == node.y
        assert sd["z"] == node.z
        assert sd["scriptMode"] == node.scriptMode
        assert sd["pythonCode"] == node.pythonCode
        assert sd["calcError"] == node.calcError
        assert sd["options"] == node.options.saveDict()
        assert sd["turbApp"] == node.turbApp
        assert sd["turbSession"] == node.turbSession
        assert sd["synced"] == node.synced

    def test_loadDict(self, node):
        node.modelType = 2
        assert node.isModelTurbine is True

        # add some attributes to test more of the load method
        # as mentioned in node.py L829, may become obsolete at some point
        sd = node.saveDict()
        sd["inVars"] = node.inVars
        sd["outVars"] = node.outVars
        sd["inVarsVector"] = node.inVarsVector
        sd["outVarsVector"] = node.outVarsVector

        node.loadDict(sd)

    def test_stringToType(self, node):
        # pass strings and check returned object
        assert node.stringToType(s="double") == float
        assert node.stringToType(s="float") == float
        assert node.stringToType(s="int") == int
        assert node.stringToType(s="str") == str
        with pytest.raises(NodeEx):
            node.stringToType(s="other")

    def test_setSim_nochange(self, node):
        original_node = node  # alias to check against
        node.setSim(newType=node.modelType, newModel=node.modelName)
        assert node == original_node  # nothing should have changed

    def test_setSim_nonemodelname(self, node):
        node.setSim(newModel=None)
        assert node.modelName == ""
        assert node.modelType == 0

    def test_setSim_emptymodelname(self, node):
        node.setSim(newModel="")
        assert node.modelName == ""
        assert node.modelType == 0

    def test_setSim_nonemodeltype(self, node):
        node.setSim(newType=nodeModelTypes.MODEL_NONE)
        assert node.modelName == ""
        assert node.modelType == 0

    def test_setSim_newmodel(self, node):
        node.setSim(newModel="newName", newType="newType")
        assert node.modelName == "newName"
        assert node.modelType == "newType"  # not actuall a valid type, just
        # checking that the new attribute matches the passed argument above

    def test_setSim_modelNone(self, node):
        original_graph = node.gr  # alias to check against
        node.setSim(newModel="newName", newType=0)
        assert node.gr == original_graph  # nothing should have changed

    def test_run_modelNone(self, node):
        original_graph = node.gr  # alias to check against
        node.setSim(newModel="newName", newType=0)
        node.runCalc()  # covers node.runModel()
        assert node.gr == original_graph  # nothing should have changed

    def test_setSim_modelPlugin(self, node):
        # manually add plugin model to test
        node.gr.pymodels = pymodel()
        node.gr.pymodels.plugins = dict()
        node.gr.pymodels.plugins["plugin_model"] = pymodel_test
        node.setSim(newModel="plugin_model", newType=1)

        inst = node.gr.pymodels.plugins[node.modelName].pymodel_pg()

        for attribute in [
            "dtype",
            "min",
            "max",
            "default",
            "unit",
            "set",
            "desc",
            "tags",
        ]:
            for vkey, v in inst.inputs.items():
                assert getattr(node.gr.input[node.name][vkey], attribute) == getattr(
                    v, attribute
                )
            for vkey, v in inst.outputs.items():
                assert getattr(node.gr.output[node.name][vkey], attribute) == getattr(
                    v, attribute
                )

    def test_runPymodelPlugin(self, node):
        # manually add plugin model to test
        node.gr.pymodels = pymodel()
        node.gr.pymodels.plugins = dict()
        node.gr.pymodels.plugins["plugin_model"] = pymodel_test
        node.setSim(newModel="plugin_model", newType=1)
        node.runCalc()  # covers node.runPymodelPlugin()

        inst = node.gr.pymodels.plugins[node.modelName].pymodel_pg()
        inst.run()

        for attribute in [
            "dtype",
            "min",
            "max",
            "default",
            "unit",
            "set",
            "desc",
            "tags",
        ]:
            for vkey, v in inst.inputs.items():
                assert getattr(node.gr.input[node.name][vkey], attribute) == getattr(
                    v, attribute
                )
            for vkey, v in inst.outputs.items():
                assert getattr(node.gr.output[node.name][vkey], attribute) == getattr(
                    v, attribute
                )

    def test_setSim_modelMLAI_example1(self, node, model_files):
        # skip this test if tensorflow is not available
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # change directories
        curdir = os.getcwd()
        os.chdir(os.path.dirname(model_files[0]))
        # manually add ML AI model to test
        node.setSim(newModel="AR_nocustomlayer", newType=5)
        os.chdir(curdir)

        inst = pymodel_ml_ai(node.model, trainer="keras")

        for attribute in [
            "dtype",
            "min",
            "max",
            "default",
            "unit",
            "set",
            "desc",
            "tags",
        ]:
            for vkey, v in inst.inputs.items():
                assert getattr(node.gr.input[node.name][vkey], attribute) == getattr(
                    v, attribute
                )
            for vkey, v in inst.outputs.items():
                assert getattr(node.gr.output[node.name][vkey], attribute) == getattr(
                    v, attribute
                )

    def test_runPymodelMLAI_example1(self, node, model_files):
        # skip this test if tensorflow is not available
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # change directories
        curdir = os.getcwd()
        os.chdir(os.path.dirname(model_files[0]))
        # manually add ML AI model to test
        node.setSim(newModel="AR_nocustomlayer", newType=5)
        node.runCalc()  # covers node.runMLAIPlugin()
        os.chdir(curdir)

        inst = pymodel_ml_ai(node.model, trainer="keras")
        inst.run()

        for attribute in [
            "dtype",
            "min",
            "max",
            "default",
            "unit",
            "set",
            "desc",
            "tags",
        ]:
            for vkey, v in inst.inputs.items():
                assert getattr(node.gr.input[node.name][vkey], attribute) == getattr(
                    v, attribute
                )
            for vkey, v in inst.outputs.items():
                assert getattr(node.gr.output[node.name][vkey], attribute) == getattr(
                    v, attribute
                )

    def test_setSim_modelMLAI_example2(self, node, model_files):
        # skip this test if tensorflow is not available
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # change directories
        curdir = os.getcwd()
        os.chdir(os.path.dirname(model_files[0]))
        # manually add ML AI model to test
        node.setSim(newModel="mea_column_model", newType=5)
        os.chdir(curdir)

        inst = pymodel_ml_ai(node.model, trainer="keras")

        for attribute in [
            "dtype",
            "min",
            "max",
            "default",
            "unit",
            "set",
            "desc",
            "tags",
        ]:
            for vkey, v in inst.inputs.items():
                assert getattr(node.gr.input[node.name][vkey], attribute) == getattr(
                    v, attribute
                )
            for vkey, v in inst.outputs.items():
                assert getattr(node.gr.output[node.name][vkey], attribute) == getattr(
                    v, attribute
                )

    def test_runPymodelMLAI_example2(self, node, model_files):
        # skip this test if tensorflow is not available
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # change directories
        curdir = os.getcwd()
        os.chdir(os.path.dirname(model_files[0]))
        # manually add ML AI model to test
        node.setSim(newModel="mea_column_model", newType=5)
        node.runCalc()  # covers node.runMLAIPlugin()
        os.chdir(curdir)

        inst = pymodel_ml_ai(node.model, trainer="keras")
        inst.run()

        for attribute in [
            "dtype",
            "min",
            "max",
            "default",
            "unit",
            "set",
            "desc",
            "tags",
        ]:
            for vkey, v in inst.inputs.items():
                assert getattr(node.gr.input[node.name][vkey], attribute) == getattr(
                    v, attribute
                )
            for vkey, v in inst.outputs.items():
                assert getattr(node.gr.output[node.name][vkey], attribute) == getattr(
                    v, attribute
                )

    def test_setSim_modelMLAI_example3(self, node, model_files):
        # skip this test if tensorflow is not available
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # skip this test if sympy is not available
        pytest.importorskip("sympy", reason="sympy not installed")
        # change directories
        curdir = os.getcwd()
        os.chdir(os.path.dirname(model_files[0]))
        # manually add ML AI model to test
        node.setSim(newModel="mea_column_model_customnormform", newType=5)
        os.chdir(curdir)

        inst = pymodel_ml_ai(node.model, trainer="keras")

        for attribute in [
            "dtype",
            "min",
            "max",
            "default",
            "unit",
            "set",
            "desc",
            "tags",
        ]:
            for vkey, v in inst.inputs.items():
                assert getattr(node.gr.input[node.name][vkey], attribute) == getattr(
                    v, attribute
                )
            for vkey, v in inst.outputs.items():
                assert getattr(node.gr.output[node.name][vkey], attribute) == getattr(
                    v, attribute
                )

    def test_runPymodelMLAI_example3(self, node, model_files):
        # skip this test if tensorflow is not available
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # skip this test if sympy is not available
        pytest.importorskip("sympy", reason="sympy not installed")
        # change directories
        curdir = os.getcwd()
        os.chdir(os.path.dirname(model_files[0]))
        # manually add ML AI model to test
        node.setSim(newModel="mea_column_model_customnormform", newType=5)
        node.runCalc()  # covers node.runMLAIPlugin()
        os.chdir(curdir)

        inst = pymodel_ml_ai(node.model, trainer="keras")
        inst.run()

        for attribute in [
            "dtype",
            "min",
            "max",
            "default",
            "unit",
            "set",
            "desc",
            "tags",
        ]:
            for vkey, v in inst.inputs.items():
                assert getattr(node.gr.input[node.name][vkey], attribute) == getattr(
                    v, attribute
                )
            for vkey, v in inst.outputs.items():
                assert getattr(node.gr.output[node.name][vkey], attribute) == getattr(
                    v, attribute
                )

    def test_setSim_modelMLAI_example4(self, node, model_files):
        # skip this test if tensorflow is not available
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # skip this test if sympy is not available
        pytest.importorskip("sympy", reason="sympy not installed")
        # change directories
        curdir = os.getcwd()
        os.chdir(os.path.dirname(model_files[0]))
        # manually add ML AI model to test
        node.setSim(newModel="mea_column_model_customnormform_savedmodel", newType=5)
        os.chdir(curdir)

        inst = pymodel_ml_ai(node.model, trainer="keras")

        for attribute in [
            "dtype",
            "min",
            "max",
            "default",
            "unit",
            "set",
            "desc",
            "tags",
        ]:
            for vkey, v in inst.inputs.items():
                assert getattr(node.gr.input[node.name][vkey], attribute) == getattr(
                    v, attribute
                )
            for vkey, v in inst.outputs.items():
                assert getattr(node.gr.output[node.name][vkey], attribute) == getattr(
                    v, attribute
                )

    def test_runPymodelMLAI_example4(self, node, model_files):
        # skip this test if tensorflow is not available
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # skip this test if sympy is not available
        pytest.importorskip("sympy", reason="sympy not installed")
        # change directories
        curdir = os.getcwd()
        os.chdir(os.path.dirname(model_files[0]))
        # manually add ML AI model to test
        node.setSim(newModel="mea_column_model_customnormform_savedmodel", newType=5)
        node.runCalc()  # covers node.runMLAIPlugin()
        os.chdir(curdir)

        inst = pymodel_ml_ai(node.model, trainer="keras")
        inst.run()

        for attribute in [
            "dtype",
            "min",
            "max",
            "default",
            "unit",
            "set",
            "desc",
            "tags",
        ]:
            for vkey, v in inst.inputs.items():
                assert getattr(node.gr.input[node.name][vkey], attribute) == getattr(
                    v, attribute
                )
            for vkey, v in inst.outputs.items():
                assert getattr(node.gr.output[node.name][vkey], attribute) == getattr(
                    v, attribute
                )

    def test_setSim_modelMLAI_example5(self, node, model_files):
        # skip this test if tensorflow is not available
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # skip this test if sympy is not available
        pytest.importorskip("sympy", reason="sympy not installed")
        # change directories
        curdir = os.getcwd()
        os.chdir(os.path.dirname(model_files[0]))
        # manually add ML AI model to test
        node.setSim(newModel="mea_column_model_customnormform_json", newType=5)
        os.chdir(curdir)

        inst = pymodel_ml_ai(node.model, trainer="keras")

        for attribute in [
            "dtype",
            "min",
            "max",
            "default",
            "unit",
            "set",
            "desc",
            "tags",
        ]:
            for vkey, v in inst.inputs.items():
                assert getattr(node.gr.input[node.name][vkey], attribute) == getattr(
                    v, attribute
                )
            for vkey, v in inst.outputs.items():
                assert getattr(node.gr.output[node.name][vkey], attribute) == getattr(
                    v, attribute
                )

    def test_runPymodelMLAI_example5(self, node, model_files):
        # skip this test if tensorflow is not available
        pytest.importorskip("tensorflow", reason="tensorflow not installed")
        # skip this test if sympy is not available
        pytest.importorskip("sympy", reason="sympy not installed")
        # change directories
        curdir = os.getcwd()
        os.chdir(os.path.dirname(model_files[0]))
        # manually add ML AI model to test
        node.setSim(newModel="mea_column_model_customnormform_json", newType=5)
        node.runCalc()  # covers node.runMLAIPlugin()
        os.chdir(curdir)

        inst = pymodel_ml_ai(node.model, trainer="keras")
        inst.run()

        for attribute in [
            "dtype",
            "min",
            "max",
            "default",
            "unit",
            "set",
            "desc",
            "tags",
        ]:
            for vkey, v in inst.inputs.items():
                assert getattr(node.gr.input[node.name][vkey], attribute) == getattr(
                    v, attribute
                )
            for vkey, v in inst.outputs.items():
                assert getattr(node.gr.output[node.name][vkey], attribute) == getattr(
                    v, attribute
                )

    def test_setSim_modelMLAI_example6(self, node, model_files):
        # skip this test if torch is not available
        pytest.importorskip("torch", reason="torch not installed")
        # skip this test if sympy is not available
        pytest.importorskip("sympy", reason="sympy not installed")
        # change directories
        curdir = os.getcwd()
        os.chdir(os.path.dirname(model_files[0]))
        # manually add ML AI model to test
        node.setSim(newModel="mea_column_model_customnormform_pytorch", newType=5)
        os.chdir(curdir)

        inst = pymodel_ml_ai(node.model, trainer="torch")

        for attribute in [
            "dtype",
            "min",
            "max",
            "default",
            "unit",
            "set",
            "desc",
            "tags",
        ]:
            for vkey, v in inst.inputs.items():
                assert getattr(node.gr.input[node.name][vkey], attribute) == getattr(
                    v, attribute
                )
            for vkey, v in inst.outputs.items():
                assert getattr(node.gr.output[node.name][vkey], attribute) == getattr(
                    v, attribute
                )

    def test_runPymodelMLAI_example6(self, node, model_files):
        # skip this test if torch is not available
        pytest.importorskip("torch", reason="torch not installed")
        # skip this test if sympy is not available
        pytest.importorskip("sympy", reason="sympy not installed")
        # change directories
        curdir = os.getcwd()
        os.chdir(os.path.dirname(model_files[0]))
        # manually add ML AI model to test
        node.setSim(newModel="mea_column_model_customnormform_pytorch", newType=5)
        node.runCalc()  # covers node.runMLAIPlugin()
        os.chdir(curdir)

        inst = pymodel_ml_ai(node.model, trainer="torch")
        inst.run()

        for attribute in [
            "dtype",
            "min",
            "max",
            "default",
            "unit",
            "set",
            "desc",
            "tags",
        ]:
            for vkey, v in inst.inputs.items():
                assert getattr(node.gr.input[node.name][vkey], attribute) == getattr(
                    v, attribute
                )
            for vkey, v in inst.outputs.items():
                assert getattr(node.gr.output[node.name][vkey], attribute) == getattr(
                    v, attribute
                )

    def test_setSim_modelMLAI_example7(self, node, model_files):
        # skip this test if sklearn is not available
        pytest.importorskip("sklearn", reason="sklearn not installed")
        # skip this test if sympy is not available
        pytest.importorskip("sympy", reason="sympy not installed")
        # change directories
        curdir = os.getcwd()
        os.chdir(os.path.dirname(model_files[0]))
        # manually add ML AI model to test
        node.setSim(newModel="mea_column_model_customnormform_scikitlearn", newType=5)
        os.chdir(curdir)

        inst = pymodel_ml_ai(node.model, trainer="sklearn")

        for attribute in [
            "dtype",
            "min",
            "max",
            "default",
            "unit",
            "set",
            "desc",
            "tags",
        ]:
            for vkey, v in inst.inputs.items():
                assert getattr(node.gr.input[node.name][vkey], attribute) == getattr(
                    v, attribute
                )
            for vkey, v in inst.outputs.items():
                assert getattr(node.gr.output[node.name][vkey], attribute) == getattr(
                    v, attribute
                )

    def test_runPymodelMLAI_example7(self, node, model_files):
        # skip this test if sklearn is not available
        pytest.importorskip("sklearn", reason="sklearn not installed")
        # skip this test if sympy is not available
        pytest.importorskip("sympy", reason="sympy not installed")
        # change directories
        curdir = os.getcwd()
        os.chdir(os.path.dirname(model_files[0]))
        # manually add ML AI model to test
        node.setSim(newModel="mea_column_model_customnormform_scikitlearn", newType=5)
        node.runCalc()  # covers node.runMLAIPlugin()
        os.chdir(curdir)

        inst = pymodel_ml_ai(node.model, trainer="sklearn")
        inst.run()

        for attribute in [
            "dtype",
            "min",
            "max",
            "default",
            "unit",
            "set",
            "desc",
            "tags",
        ]:
            for vkey, v in inst.inputs.items():
                assert getattr(node.gr.input[node.name][vkey], attribute) == getattr(
                    v, attribute
                )
            for vkey, v in inst.outputs.items():
                assert getattr(node.gr.output[node.name][vkey], attribute) == getattr(
                    v, attribute
                )
