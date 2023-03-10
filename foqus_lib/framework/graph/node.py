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
"""node.py

* This contains the classes for nodes

John Eslick, Carnegie Mellon University, 2014
"""

import os
import json
import math
import numpy as np
import logging
from foqus_lib.framework.pymodel.pymodel import *
from foqus_lib.framework.graph.nodeVars import *
from foqus_lib.framework.graph.nodeModelTypes import nodeModelTypes
from collections import OrderedDict
from foqus_lib.framework.foqusOptions.optionList import optionList
from foqus_lib.framework.sim.turbineConfiguration import TurbineInterfaceEx
from foqus_lib.framework.at_dict.at_dict import AtDict
from importlib import import_module

_logger = logging.getLogger("foqus." + __name__)

# pylint: disable=import-error

# wrapping try/except optional imports in function for testing purposes
# try_imports is ignored in normal usage; it is set to False in test module to
# test exceptions when test environments with packages installed without
# having to mock missing imports or modify the available package list


def attempt_load_tensorflow(try_imports=True):
    try:
        assert try_imports  # if False will auto-trigger exceptions
        # tensorflow should be installed, but not required for non ML/AI models
        import tensorflow as tf

        load = tf.keras.models.load_model
        json_load = tf.keras.models.model_from_json

    # throw warning if manually failed for test or if package actually not available
    except (AssertionError, ImportError, ModuleNotFoundError):
        # if tensorFlow is not available, create a proxy function that will
        # raise an exception whenever code tries to use `load()` at runtime
        def load(*args, **kwargs):
            raise ModuleNotFoundError(
                f"`load()` was called with args={args},"
                "kwargs={kwargs} but `tensorflow` is not available"
            )

        def json_load(*args, **kwargs):
            raise ModuleNotFoundError(
                f"`load()` was called with args={args},"
                "kwargs={kwargs} but `tensorflow` is not available"
            )

    return load, json_load


def attempt_load_sympy(try_imports=True):
    try:
        assert try_imports  # if False will auto-trigger exceptions
        # sympy should be installed, but not required if normalization is not
        # set to True, or if preset normalization option is used
        import sympy as sy

        parse = sy.parsing.sympy_parser.parse_expr
        symbol = sy.Symbol
        solve = sy.solve

    # throw warning if manually failed for test or if package actually not available
    except (AssertionError, ImportError, ModuleNotFoundError):
        # if sympy is not available, create proxy functions that will raise
        # an exception whenever code tries to use a sympy method at runtime
        def parse(*args, **kwargs):
            raise ModuleNotFoundError(
                f"`parse()` was called with args={args},"
                "kwargs={kwargs} but `sympy` is not available"
            )

        def symbol(*args, **kwargs):
            raise ModuleNotFoundError(
                f"`symbol()` was called with args={args},"
                "kwargs={kwargs} but `sympy` is not available"
            )

        def solve(*args, **kwargs):
            raise ModuleNotFoundError(
                f"`solve()` was called with args={args},"
                "kwargs={kwargs} but `sympy` is not available"
            )

    return parse, symbol, solve


def attempt_load_pytorch(try_imports=True):
    try:
        assert try_imports  # if False will auto-trigger exceptions
        # torch should be installed, but not required for non ML/AI models
        import torch

        torch_load = torch.jit.load
        torch_tensor = torch.tensor
        torch_float = torch.float

    # throw warning if manually failed for test or if package actually not available
    except (AssertionError, ImportError, ModuleNotFoundError):
        # if torch is not available, create a proxy function that will
        # raise an exception whenever code tries to use `load()` at runtime
        def torch_load(*args, **kwargs):
            raise ModuleNotFoundError(
                f"`load()` was called with args={args},"
                "kwargs={kwargs} but `torch` is not available"
            )

        def torch_tensor(*args, **kwargs):
            raise ModuleNotFoundError(
                f"`load()` was called with args={args},"
                "kwargs={kwargs} but `torch` is not available"
            )

        def torch_float(*args, **kwargs):
            raise ModuleNotFoundError(
                f"`load()` was called with args={args},"
                "kwargs={kwargs} but `torch` is not available"
            )

    return torch_load, torch_tensor, torch_float


def attempt_load_sklearn(try_imports=True):
    try:
        assert try_imports  # if False will auto-trigger exceptions
        # sklearn should be installed, but not required for non ML/AI models
        import sklearn
        import pickle

        pickle_load = pickle.load

    # throw warning if manually failed for test or if package actually not available
    except (AssertionError, ImportError, ModuleNotFoundError):
        # if sklearn is not available, create a proxy function that will
        # raise an exception whenever code tries to use `load()` at runtime
        def pickle_load(*args, **kwargs):
            raise ModuleNotFoundError(
                f"`load()` was called with args={args},"
                "kwargs={kwargs} but `sklearn` is not available"
            )

    return pickle_load


# attempt to load optional dependenices for node script
load, json_load = attempt_load_tensorflow()
parse, symbol, solve = attempt_load_sympy()
torch_load, torch_tensor, torch_float = attempt_load_pytorch()
pickle_load = attempt_load_sklearn()

# pylint: enable=import-error


class NodeOptionSets:
    OTHER_OPTIONS = 0
    NODE_OPTIONS = 1
    TURBINE_OPTIONS = 2
    SINTER_OPTIONS = 3
    PLUGIN_OPTIONS = 4
    ML_AI_OPTIONS = 5


class PyCodeInterupt(Exception):
    pass


class NpCodeEx(Exception):
    def __init__(self, msg="", code=100):
        self.code = code
        self.msg = msg

    def __str__(self):
        return str(self.msg)


class NodeEx(foqusException):
    """Refactor so ERROR Codes that are Unique across all
    foqusException.
    """

    ERROR_CONFIGURATION_MISSING = 10000
    ERROR_NODE_FLOWSHEET = 10001

    def __init__(self, code=0, msg="", e=None, tb=None):
        super(NodeEx, self).__init__(code=code, msg=msg, e=e, tb=tb)
        self.setCodeStrings()

    @classmethod
    def GetInstance(cls, code):
        """Move this to the base class and return
        the correct Exception based on unique error codes.
        """
        if code < cls.ERROR_CONFIGURATION_MISSING:
            return None
        inst = NodeEx(code)
        if code in inst.codeString.keys():
            return inst
        return None

    def setCodeStrings(self):
        # 100's reserved for python code script errors
        self.codeString[-1] = "Did not finish"
        self.codeString[0] = "Finished Normally"
        self.codeString[1] = "Simulation error (see job logs)"
        self.codeString[3] = "Maximum wait time exceeded"
        self.codeString[4] = "Failed to create Turbine session ID"
        self.codeString[6] = "Maximum run time exceeded"
        self.codeString[5] = "Failed to add job to Turbine"
        self.codeString[7] = "Turbine simulation error"
        self.codeString[8] = "Failed to start Turbine Job"
        self.codeString[9] = "Unknown model type"
        self.codeString[10] = "Failed to get job status"
        self.codeString[11] = "Graph thread terminated"
        self.codeString[20] = "Error in Python node script code"
        self.codeString[21] = "Error in Python node script code"
        self.codeString[23] = "Could not convert numpy value to list"
        self.codeString[27] = "Can't read variable in results (see log)"
        self.codeString[50] = "Node script interupt exception"
        self.codeString[61] = "Unknow type string"
        self.codeString[
            self.ERROR_CONFIGURATION_MISSING
        ] = "Model Missing Configuration"
        self.codeString[self.ERROR_NODE_FLOWSHEET] = "Node cannot be set to a flowsheet"


class pymodel_ml_ai(pymodel):
    def __init__(self, model, trainer):
        pymodel.__init__(self)
        self.model = model  # attach it to self so we can call it in the run method
        self.trainer = trainer  # attach it to self so we can call it in the run method

        # determine the ML model type
        if self.trainer == "keras":
            # set the custom layer object
            custom_layer = self.model.layers[1]
            # set the model input and output sizes
            model_input_size = np.shape(self.model.inputs[0])[1]
            model_output_size = np.shape(self.model.outputs[0])[1]

        elif self.trainer == "torch":
            # find the custom layer object, if it exists - there's probably a more direct way to do this
            for attribute in dir(self.model):
                # assuming that a custom layer would define input labels
                # at a minimum, it should be safe to expect this
                if hasattr(getattr(self.model, attribute), "input_labels"):
                    # there should only be one custom layer in the model
                    # since it is used to hold attributes, not network data
                    custom_layer = getattr(self.model, attribute)

            # find the model input and output sizes
            named_layers = dict(
                self.model.named_modules()
            )  # dictionary of neural network layers
            # assuming the layers are in order, we don't want to include the custom layer or "blank" key
            if "" in list(named_layers.keys()):
                named_layers.pop("")
            for name, layer in named_layers.items():
                if layer == custom_layer:  # exclude the custom layer
                    named_layers.pop(name)
                    break  # stop the loop to prevent a size-change error
            # now, get the model input/output sizes from the first and last layers
            named_layers_keys = list(named_layers.keys())
            model_input_size = named_layers[
                named_layers_keys[0]
            ].in_features  # first layer has model inputs
            model_output_size = named_layers[
                named_layers_keys[-1]
            ].out_features  # last layer has model outputs

        elif self.trainer == "sklearn":
            # set the custom layer object
            custom_layer = self.model.custom
            # set the model input and output sizes
            model_input_size = self.model.n_features_in_
            model_output_size = self.model.n_outputs_

        else:  # this shouldn't occur, adding failsafe just in case
            raise AttributeError(
                "Unknown file type: " + self.trainer + ", this "
                "should not have occurred. Please contact the "
                "FOQUS developers if this error occurs; the "
                "trainer should be set internally to `keras`, 'torch' or "
                "`sklearn` and should not be able to take any other value."
            )

        self.custom_layer = (
            custom_layer  # attach it to self so we can call it in the run method
        )
        # attempt to retrieve required information from loaded model, and set defaults otherwise
        for i in range(model_input_size):
            try:
                input_label = self.custom_layer.input_labels[i]
            except AttributeError:
                _logger.info(
                    "Model has no attribute input_label, using default x"
                    + str(i + 1)
                    + ". If attribute should exist, check that "
                    + "machine learning model was correctly saved with "
                    + "CustomLayer. Otherwise, this is not an error and model "
                    + "will load "
                    + "as expected using default attributes."
                )
                input_label = "x" + str(i + 1)
            try:
                input_min = self.custom_layer.input_bounds[input_label][0]
            except AttributeError:
                _logger.info(
                    "Model has no attribute input_min, using default 0"
                    + ". If attribute should exist, check that "
                    + "machine learning model was correctly saved with "
                    + "CustomLayer. Otherwise, this is not an error and model "
                    + "will load as expected using default attributes."
                )
                input_min = 0  # not necessarily a good default
            try:
                input_max = self.custom_layer.input_bounds[input_label][1]
            except AttributeError:
                _logger.info(
                    "Model has no attribute input_max, using default 1E5"
                    + ". If attribute should exist, check that "
                    + "machine learning model was correctly saved with "
                    + "CustomLayer. Otherwise, this is not an error and model "
                    + "will load as expected using default attributes."
                )
                input_max = 1e5  # not necessarily a good default

            self.inputs[input_label] = NodeVars(
                value=(input_min + input_max) / 2,
                vmin=input_min,
                vmax=input_max,
                vdflt=0.0,
                unit="",
                vst="pymodel",
                vdesc="input var " + str(i + 1),
                tags=[],
                dtype=float,
            )

        for j in range(model_output_size):
            try:
                output_label = self.custom_layer.output_labels[j]
            except AttributeError:
                _logger.info(
                    "Model has no attribute output_label, using default z"
                    + str(j + 1)
                    + ". If attribute should exist, check that "
                    + "machine learning model was correctly saved with "
                    + "CustomLayer. Otherwise, this is not an error and model "
                    + "will load as expected using default attributes."
                )
                output_label = "z" + str(j + 1)
            try:
                output_min = self.custom_layer.output_bounds[output_label][0]
            except AttributeError:
                _logger.info(
                    "Model has no attribute output_min, using default 0"
                    + ". If attribute should exist, check that "
                    + "machine learning model was correctly saved with "
                    + "CustomLayer. Otherwise, this is not an error and model "
                    + "will load as expected using default attributes."
                )
                output_min = 0  # not necessarily a good default
            try:
                output_max = self.custom_layer.output_bounds[output_label][1]
            except AttributeError:
                _logger.info(
                    "Model has no attribute output_max, using default 1E5"
                    + ". If attribute should exist, check that "
                    + "machine learning model was correctly saved with "
                    + "CustomLayer. Otherwise, this is not an error and model "
                    + "will load as expected using default attributes."
                )
                output_max = 1e5  # not necessarily a good default

            self.outputs[output_label] = NodeVars(
                value=(output_min + output_max) / 2,
                vmin=output_min,
                vmax=output_max,
                vdflt=0.0,
                unit="",
                vst="pymodel",
                vdesc="output var " + str(j + 1),
                tags=[],
                dtype=float,
            )

        # check if user passed a model for normalized data - FOQUS will automatically scale/un-scale
        try:  # if attribute exists, user has specified a model form
            self.normalized = self.custom_layer.normalized
        except AttributeError:  # otherwise user did not pass a normalized model
            _logger.info(
                "Model has no attribute normalized, using default False"
                + ". If attribute should exist, check that "
                + "machine learning model was correctly saved with "
                + "CustomLayer. Otherwise, this is not an error and model "
                + "will load as expected using default attributes."
            )
            self.normalized = False

    def run(self):
        # the bulk of this method checks whether model is normalized and if so
        # how, and then defines input scaling and output unscaling if needed
        import numpy as np

        # first, consider if model is not normalized - the simplest case
        if self.normalized is False:  # no scaling needed
            self.scaled_inputs = [self.inputs[i].value for i in self.inputs]

        # next, consider if model is normalized - must include a method type
        elif self.normalized is True:  # scale actual inputs

            # select normalization type - users need to explicitly pass a form flag
            # don't set a default - if users are setting this to True they should
            # be aware of that FOQUS requires a normalization form flag as well
            try:  # see if form flag exists and throw useful error if not
                self.normalization_form = self.custom_layer.normalization_form
            except AttributeError:
                raise AttributeError(  # raise to ensure code stops here
                    "Model has no attribute normalization_form, and existing "
                    "attribute normalization was set to True. Users must "
                    "provide a normalization type for FOQUS to automatically "
                    "scale flowsheet inputs and unscale flowsheet outputs."
                )

            # define a list of allowed forms; "Custom" requires norm_function
            allowed_norm_forms = [
                "Linear",
                "Log",
                "Power",
                "Log 2",
                "Power 2",
                "Custom",
            ]
            # see if form flag is an allowed type and throw useful error if not
            if self.normalization_form not in allowed_norm_forms:
                raise AttributeError(
                    "Value {} not valid for normalization_form, please ensure the model uses "
                    "the appropriate flag from the following list and restart FOQUS: {}".format(
                        str(self.normalization_form), str(allowed_norm_forms)
                    )
                )

            # chose to prevent quiet failures, and will not use 'hasattr' below
            # users should not try to normalize without setting a form flag
            if self.normalization_form == "Linear":
                self.scaled_inputs = [
                    (self.inputs[i].value - self.inputs[i].min)
                    / (self.inputs[i].max - self.inputs[i].min)
                    for i in self.inputs
                ]
            elif self.normalization_form == "Log":
                self.scaled_inputs = [
                    (math.log10(self.inputs[i].value) - math.log10(self.inputs[i].min))
                    / (math.log10(self.inputs[i].max) - math.log10(self.inputs[i].min))
                    for i in self.inputs
                ]
            elif self.normalization_form == "Power":
                self.scaled_inputs = [
                    (
                        math.pow(10, self.inputs[i].value)
                        - math.pow(10, self.inputs[i].min)
                    )
                    / (
                        math.pow(10, self.inputs[i].max)
                        - math.pow(10, self.inputs[i].min)
                    )
                    for i in self.inputs
                ]
            elif self.normalization_form == "Log 2":
                # if F = (value - min) / (max - min), then
                # scaled = log10[9*F + 1]
                self.scaled_inputs = [
                    math.log10(
                        9
                        * (self.inputs[i].value - self.inputs[i].min)
                        / (self.inputs[i].max - self.inputs[i].min)
                        + 1
                    )
                    for i in self.inputs
                ]
            elif self.normalization_form == "Power 2":
                # if F = (value - min) / (max - min), then
                # scaled = (1/9) * (10^F - 1)
                self.scaled_inputs = [
                    (1 / 9)
                    * math.pow(
                        10,
                        (self.inputs[i].value - self.inputs[i].min)
                        / (self.inputs[i].max - self.inputs[i].min),
                    )
                    - 1
                    for i in self.inputs
                ]

            elif self.normalization_form == "Custom":
                # check custom normalization form for requirements
                try:  # see if function is passed and throw useful error if not
                    self.normalization_function = (
                        self.custom_layer.normalization_function
                    )
                except AttributeError:
                    raise AttributeError(
                        "Model has no attribute normalization_function, and existing "
                        "attribute normalization_form was set to Custom. Users must "
                        "provide a normalization function for FOQUS to automatically "
                        "scale flowsheet inputs and unscale flowsheet outputs."
                    )

                if type(self.normalization_function) is not str:
                    raise TypeError(
                        "Model attribute normalization_function is not a string. "
                        "Please pass a string for the sympy parser to convert."
                    )
                elif "datavalue" not in self.normalization_function:
                    raise ValueError(
                        "Custom normalization function {} does not reference "
                        " 'datavalue', expression must use 'datavalue' to "
                        " refer to unscaled data values.".format(
                            self.normalization_function
                        )
                    )
                elif "dataminimum" not in self.normalization_function:
                    raise ValueError(
                        "Custom normalization function {} does not reference "
                        " 'dataminimum', expression must use 'dataminimum' to "
                        " refer to unscaled data values.".format(
                            self.normalization_function
                        )
                    )
                elif "datamaximum" not in self.normalization_function:
                    raise ValueError(
                        "Custom normalization function {} does not reference "
                        " 'datamaximum', expression must use 'datamaximum' to "
                        " refer to unscaled data values.".format(
                            self.normalization_function
                        )
                    )

                try:  # parse function and throw useful error if syntax error
                    scaling_function = parse(self.normalization_function)
                except TypeError:
                    raise ValueError(  # raise to ensure code stops here
                        "Model attribute normalization_function has value {} which "
                        "is not a valid SymPy expression. Please refer to the "
                        "latest documentation for syntax guidelines and standards: "
                        "https://docs.sympy.org/latest/index.html".format(
                            self.normalization_function
                        )
                    )

                # use parsed function to scale actual inputs to model inputs

                # create symbols for input datavalue, datamin and datamax
                # we will be substituting numerical entries sequenitally below
                datavalue = symbol("datavalue")
                dataminimum = symbol("dataminimum")
                datamaximum = symbol("datamaximum")

                # set scaled input values from custom function
                # put substitution in method so list comprehension is cleaner
                def sub_symbols(i):
                    # substitute values for symbols in scaling function
                    # break it up so it's easier to follow, but could do in one line if desired
                    scaling_evaluated = scaling_function
                    scaling_evaluated = scaling_evaluated.subs(
                        datavalue, self.inputs[i].value
                    )
                    scaling_evaluated = scaling_evaluated.subs(
                        dataminimum, self.inputs[i].min
                    )
                    scaling_evaluated = scaling_evaluated.subs(
                        datamaximum, self.inputs[i].max
                    )

                    return scaling_evaluated

                self.scaled_inputs = [
                    float(sub_symbols(i).evalf()) for i in self.inputs
                ]

        # set output values to be generated from NN surrogate
        if self.trainer == "keras":
            self.scaled_outputs = self.model.predict(
                np.array(self.scaled_inputs, ndmin=2)
            )[0]
        elif self.trainer == "torch":
            self.scaled_outputs = (
                self.model(torch_tensor(self.scaled_inputs, dtype=torch_float))
                .detach()
                .numpy()
            )
        elif self.trainer == "sklearn":
            self.scaled_outputs = self.model.predict(
                np.array(self.scaled_inputs, ndmin=2)
            )[0]
        else:  # this shouldn't occur, adding failsafe just in case
            raise AttributeError(
                "Unknown file type: " + self.trainer + ", this "
                "should not have occurred. Please contact the "
                "FOQUS developers if this error occurs; the "
                "trainer should be set internally to `keras`, 'torch' or "
                "`sklearn` and should not be able to take any other value."
            )

        outidx = 0
        for j in self.outputs:

            # first, consider if model is not normalized - the simplest case
            if self.normalized is False:  # no unscaling needed
                self.outputs[j].value = self.scaled_outputs[outidx]

            # next, consider if model is normalized - must include a method type
            # at this point any missing arguments or errors would have been caught
            # so don't need to check for those here as well
            elif self.normalized is True:  # unscale to obtain actual output values

                # select normalization type - should be user defined and must be set.
                # don't set a default - if users are setting this to True they should
                # be aware of that FOQUS requires a normalization form flag as well

                if self.normalization_form == "Linear":
                    self.outputs[j].value = (
                        self.scaled_outputs[outidx]
                        * (self.outputs[j].max - self.outputs[j].min)
                        + self.outputs[j].min
                    )
                elif self.normalization_form == "Log":
                    self.outputs[j].value = math.pow(
                        10,
                        self.scaled_outputs[outidx]
                        * (
                            math.log10(self.outputs[j].max)
                            - math.log10(self.outputs[j].min)
                        )
                        + math.log10(self.outputs[j].min),
                    )
                elif self.normalization_form == "Power":
                    self.outputs[j].value = math.log10(
                        self.scaled_outputs[outidx]
                        * (
                            math.pow(10, self.outputs[j].max)
                            - math.pow(10, self.outputs[j].min)
                        )
                        + math.pow(10, self.outputs[j].min)
                    )
                elif self.normalization_form == "Log 2":
                    self.outputs[j].value = (
                        math.pow(10, self.scaled_outputs[outidx]) - 1
                    ) * (self.outputs[j].max - self.outputs[j].min) / 9 + self.outputs[
                        j
                    ].min
                elif self.normalization_form == "Power 2":
                    self.outputs[j].value = (
                        math.log10(9 * self.scaled_outputs[outidx]) + 1
                    ) * (self.outputs[j].max - self.outputs[j].min) + self.outputs[
                        j
                    ].min

                elif self.normalization_form == "Custom":
                    # create symbol for scaled outputs
                    datascaled = symbol("datascaled")

                    # solve for inverse function to return unscaled values
                    try:  # solve function and throw useful error if error
                        # the method below write an equation
                        # datascaled = func(datavalue, dataminimum, datamaximum)
                        # and returns an equation
                        # datavalue = func(datascaled, dataminimum, datamaximum)
                        # the flag `rational=False` tells sympy not to reduce
                        # fractions in the expression, which saves memory
                        unscaling_function = solve(
                            datascaled - scaling_function, datavalue, rational=False
                        )[0]
                    except NotImplementedError:
                        raise ValueError(  # raise to ensure code stops here
                            "Model attribute normalization_function has value {} which"
                            "is not a solvable sympy expression. Please refer to the "
                            "latest documentation for syntax guidelines and standards: "
                            "https://docs.sympy.org/latest/index.html".format(
                                self.normalization_function
                            )
                        )

                    # use inverse function to unscale model outputs to actual outputs
                    # set unscaled output values from inverse function
                    unscaling_evaluated = unscaling_function
                    unscaling_evaluated = unscaling_evaluated.subs(
                        datascaled, self.scaled_outputs[outidx]
                    )
                    unscaling_evaluated = unscaling_evaluated.subs(
                        dataminimum, self.outputs[j].min
                    )
                    unscaling_evaluated = unscaling_evaluated.subs(
                        datamaximum, self.outputs[j].max
                    )

                    # set actual output value to unscaled output value
                    self.outputs[j].value = float(unscaling_evaluated.evalf())

            outidx += 1


class Node:
    """
    This class stores information for graph nodes.  It also contains
    function for running a calculations and simulations associated
    with a node.  The varaibles associated with nodes are all stored
    at the graph level, so the parent graph of a node needs to be
    set before running any calculations, so the node knows where
    to find variables, turbine config info,...
    """

    def __init__(self, x=0, y=0, z=0, parent=None, name=None):
        #
        self.setGraph(parent, name)  # set parent graph and node name
        self.modelType = nodeModelTypes.MODEL_NONE  # Model type
        self.modelName = ""  # name of node model
        self.calcCount = 0
        self.altInput = None
        self.vis = True  # whether or not to display node
        self.seq = True  # whether or not to include in calculation order
        self.x = x  # coordinate for drawing graph
        self.y = y  # coordinate for drawing graph
        self.z = z  # coordinate for drawing graph
        self.calcError = -1  # error code, 0 = good
        ## node calculations
        self.scriptMode = "post"
        self.pythonCode = ""
        ## Node/Model Options
        self.options = optionList()
        ## Turbine stuff
        self.turbSession = 0  # turbine session id
        self.turbJobID = None  # turbine job id
        self.turbApp = None  # application that runs model
        self.turbineMessages = ""
        ## Python Plugin Stuff
        self.pyModel = None
        ##
        self.running = False
        self.synced = True

    @property
    def isModelTurbine(self) -> bool:
        return self.modelType == nodeModelTypes.MODEL_TURBINE

    @property
    def isModelNone(self) -> bool:
        return self.modelType == nodeModelTypes.MODEL_NONE

    @property
    def isModelPlugin(self) -> bool:
        return self.modelType == nodeModelTypes.MODEL_PLUGIN

    @property
    def isModelML(self) -> bool:
        return self.modelType == nodeModelTypes.MODEL_ML_AI

    def setGraph(self, gr, name=None):
        """
        Set the parent graph, node name, location of inputs and
        location of outputs.
        """
        self.gr = gr
        if name != None:
            self.name = name
        self.inVars = gr.input[self.name]
        self.outVars = gr.output[self.name]
        self.inVarsVector = gr.input_vectorlist[self.name]
        self.outVarsVector = gr.output_vectorlist[self.name]

    def addTurbineOptions(self):
        """
        Add options related to how FOQUS deals with Turbine.  These
        options should only be in nodes that run a model from
        turbine.
        """
        app = self.turbApp
        if app == "Excel":  # excel reset to true by default
            resetSim = False
            resetDisable = False
        else:
            resetSim = False
            resetDisable = False
        self.options.addIfNew(
            name="Visible",
            default=False,
            dtype=bool,
            desc=("This options show the simulator window"),
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Initialize Model",
            default=False,
            dtype=bool,
            desc=(
                "If this is true, the simulation is run with default"
                " values to initialize it before running the "
                " model inputs. This is often useful with Aspen Plus"
            ),
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Reset",
            default=resetSim,
            dtype=bool,
            desc=(
                "This options will cause a simulation to be reset to" " after each run."
            ),
            disable=resetDisable,
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Reset on Fail",
            default=True,
            dtype=bool,
            desc=(
                "This option causes the consumer to shut down if a si"
                "mulation fails.  A new one will start on next run."
            ),
            disable=resetDisable,
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Retry",
            default=False,
            dtype=bool,
            desc=("If a simulation fails retry one time."),
            disable=resetDisable,
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Allow Simulation Warnings",
            default=True,
            desc=(
                "Consider a simulation successful if it completes "
                "with warnings. (AspenPlus only for now)"
            ),
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Max consumer reuse",
            default=90,
            desc=(
                "Number maximum of times to reuse a Turbine consumer"
                " before forcing it to restart"
            ),
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Maximum Wait Time (s)",
            default=1440.0,
            dtype=float,
            desc=(
                "This is the ammount of time in seconds that FOQUS "
                "should wait for results to come back from Turbine."
            ),
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Maximum Run Time (s)",
            default=840.0,
            desc=(
                "This is the ammount of time in seconds that FOQUS "
                "should wait for results to come back from Turbine "
                "once the simulation starts running."
            ),
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Min Status Check Interval",
            default=4.0,
            desc=("This is the minimum amount of time between job " "status checks."),
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Max Status Check Interval",
            default=5.0,
            desc=("This is the maximum ammount of time between job " "status"),
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )
        self.options.addIfNew(
            name="Override Turbine Configuration",
            default="",
            desc=(
                "Optional, provide a path to a Trubine config to "
                "submit models for this node to a alternative Turbine "
                "gateway.  This can be used for special simualtions."
            ),
            optSet=NodeOptionSets.TURBINE_OPTIONS,
        )

    def errorLookup(self, i):
        """
        Give a descriptive error message to go with an integer
        error code.
        """
        ex = NodeEx()
        return ex.codeString.get(i, "unknown error")

    def saveDict(self):
        """
        Put the contents of a node into a dictionary.  This can be
        used as part of a method to save a graph to a file or to
        make a copy of the node, although there are probably better
        ways to make a copy.
        """
        sd = dict()
        sd["modelType"] = self.modelType
        sd["modelName"] = self.modelName
        sd["x"] = self.x
        sd["y"] = self.y
        sd["z"] = self.z
        sd["scriptMode"] = self.scriptMode
        sd["pythonCode"] = self.pythonCode
        sd["calcError"] = self.calcError
        sd["options"] = self.options.saveDict()
        sd["turbApp"] = self.turbApp
        sd["turbSession"] = self.turbSession
        sd["synced"] = self.synced
        return sd

    def loadDict(self, sd):
        """
        Read the node attributes fro a dictionary created by
        saveDict().
        """
        self.modelType = sd.get("modelType", nodeModelTypes.MODEL_NONE)
        self.x = sd.get("x", 0)
        self.y = sd.get("y", 0)
        self.z = sd.get("z", 0)
        self.synced = sd.get("synced", False)
        self.modelName = sd.get("modelName", "")
        self.modelType = sd.get("modelType", nodeModelTypes.MODEL_NONE)
        self.scriptMode = sd.get("scriptMode", "post")
        self.pythonCode = sd.get("pythonCode", "")
        self.calcError = sd.get("calcError", -1)
        self.turbApp = sd.get("turbApp", None)
        self.turbSession = sd.get("turbSession", 0)
        self.options = optionList()
        o = sd.get("options", None)
        if o:
            self.options.loadDict(o)
        if self.isModelTurbine:
            self.addTurbineOptions()
        # Below is just to maintain compatibility with older session files
        # It may be deleted at some point in the future
        if "inVars" in sd:
            for vkey, var in sd["inVars"].items():
                v = self.gr.input.addVariable(self.name, vkey)
                v.loadDict(var)
        if "outVars" in sd:
            for vkey, var in sd["outVars"].items():
                v = self.gr.output.addVariable(self.name, vkey)
                v.loadDict(var)
        if "inVarsVector" in sd:
            for vkey, var in sd["inVarsVector"].items():
                v = self.gr.input_vectorlist.addVectorVariable(self.name, vkey)
                v.loadDict(var)
        if "outVarsVector" in sd:
            for vkey, var in sd["outVarsVector"].items():
                v = self.gr.output_vectorlist.addVectorVariable(self.name, vkey)
                v.loadDict(var)

    def stringToType(self, s):
        # only check start of string since sinter inclued dimensions
        # after foqus will pick up dimensions from the default value
        if s[:6] == "double":
            return float
        elif s[:5] == "float":
            return float
        elif s[:3] == "int":
            # Covers int and integer
            return int
        elif s[:3] == "str":
            # covers string and str
            return str
        else:
            raise NodeEx(code=61, msg=str(s))

    def setSim(self, newType=None, newModel=None, force=False, ids=None):
        """
        Set-up the node to run a simulation with Turbine
        """
        if newModel == self.modelName and newType == self.modelType and force == False:
            # no change the simulation is already set maybe use force
            # if something about simulation changes and you want to
            # reset the model
            return
        if newModel == None or newModel == "" or newType == nodeModelTypes.MODEL_NONE:
            # No model specified set model to none
            self.modelName = ""
            self.modelType = nodeModelTypes.MODEL_NONE
        else:  # A model name was specified
            self.modelName = newModel
            self.modelType = newType
        # Delete the options will add back options for the new simulation
        self.options.clear()
        # delete all variables where set == sinter other variables
        # where added by user and can stay.  the sinter set name may
        # be a little out dated, but I'll stick with it for now
        # the only variable sets should be sinter and user
        names = list(self.inVars.keys())
        delSets = ["sinter", "pymodel"]
        for name in names:
            if self.gr.input[self.name][name].set in delSets:
                del self.gr.input[self.name][name]
        names = list(self.outVars.keys())
        for name in names:
            if self.gr.output[self.name][name].set in delSets:
                del self.gr.output[self.name][name]
        # clear the pyModel since it may be old now
        self.pyModel = None
        # Now add stuff to the node depending on the model type
        if self.isModelNone:
            # no model don't add any variables and do nothing
            return
        elif self.isModelPlugin:
            # python plugin worry about this later
            inst = self.gr.pymodels.plugins[self.modelName].pymodel_pg()
            # the node can have the pymodel instances variables since
            # i'm not going to use the pymodel instance for anything
            # else there is no need to copy them.  I'll create a
            # different instance for running the model.
            for vkey, v in inst.inputs.items():
                self.gr.input[self.name][vkey] = v
            for vkey, v in inst.outputs.items():
                self.gr.output[self.name][vkey] = v
        elif self.isModelTurbine:
            try:
                sc = self.gr.turbConfig.getSinterConfig(self.modelName)
            except Exception as ex:
                _logger.error(
                    "Turbine: Model %s Missing Sinter Configuration", self.modelName
                )
                _logger.exception(ex)
                self.calcError = NodeEx.ERROR_CONFIGURATION_MISSING
                raise NodeEx(code=NodeEx.ERROR_CONFIGURATION_MISSING)

            if sc.get("Type") == "FOQUS_Session":
                self.calcError = NodeEx.ERROR_NODE_FLOWSHEET
                raise NodeEx(code=NodeEx.ERROR_NODE_FLOWSHEET)
            modelTitle = str(sc.get("title", ""))
            modelAuthor = str(sc.get("author", ""))
            modelDate = str(sc.get("date", ""))
            modelDesc = str(sc.get("description", ""))
            modelFile = self.gr.turbConfig.getModelFileFromSinterConfigDict(sc)
            app = self.gr.turbConfig.getAppByExtension(modelFile)
            self.turbApp = app
            # Create input vectors, if any
            for name, item in sc["inputs"].items():
                if "vector" in item:
                    vector_name = item.get("vector", None)
                    if vector_name not in self.gr.input_vectorlist[self.name]:
                        self.gr.input_vectorlist[self.name][
                            vector_name
                        ] = NodeVarVector()
                        self.gr.input_vectorlist[self.name][vector_name].dtype = object
            # Add inputs
            for name, item in sc["inputs"].items():
                dtype = self.stringToType(item.get("type", "float"))
                if "vector" in item:
                    vector_name = item.get("vector", None)
                    vector_index = item.get("index", None)
                    name = vector_name + "_{0}".format(vector_index)
                self.gr.input[self.name][name] = NodeVars(
                    value=item.get("default", 0.0),
                    vmin=item.get("min", None),
                    vmax=item.get("max", None),
                    vdflt=item.get("default", None),
                    unit=str(item.get("units", "")),
                    vst="sinter",
                    dtype=dtype,
                    vdesc=str(item.get("description", "")),
                    tags=[],
                )
                # If the variable is part of a vector, add it to the vector variable
                if "vector" in item:
                    self.gr.input_vectorlist[self.name][vector_name].vector[
                        vector_index
                    ] = self.gr.input[self.name][name]
                    self.gr.input_vectorlist[self.name][vector_name].ipvname = (
                        self.name,
                        name,
                    )

            # Create output vectors, if any
            for name, item in sc["outputs"].items():
                if "vector" in item:
                    vector_name = item.get("vector", None)
                    if vector_name not in self.gr.output_vectorlist[self.name]:
                        self.gr.output_vectorlist[self.name][
                            vector_name
                        ] = NodeVarVector()
                        self.gr.output_vectorlist[self.name][vector_name].dtype = object
            # Add outputs
            for name, item in sc["outputs"].items():
                dtype = self.stringToType(item.get("type", "float"))
                if "vector" in item:
                    vector_name = item.get("vector", None)
                    vector_index = item.get("index", None)
                    name = vector_name + "_{0}".format(vector_index)
                self.gr.output[self.name][name] = NodeVars(
                    value=item.get("default", 0.0),
                    unit=str(item.get("units", "")),
                    vdesc=str(item.get("description", "")),
                    vst="sinter",
                    dtype=dtype,
                    tags=[],
                )
                # If the variable is part of a vector, add it to the vector variable
                if "vector" in item:
                    self.gr.output_vectorlist[self.name][vector_name].vector[
                        vector_index
                    ] = self.gr.output[self.name][name]
                    self.gr.output_vectorlist[self.name][vector_name].opvname = (
                        self.name,
                        name,
                    )

            # Add an extra output variable for simulation status
            # I think this comes out of all simulation run through
            # SimSinter, but its not in the sinter config file.
            self.gr.output[self.name]["status"] = NodeVars(
                value=0, vdesc="Simulation Status Code", vst="sinter"
            )
            # addTurbineOptions
            self.addTurbineOptions()
            if "settings" in sc:
                for name, item in sc["settings"].items():
                    self.options.add(
                        name=name,
                        default=item["default"],
                        desc=item["description"],
                        optSet=NodeOptionSets.SINTER_OPTIONS,
                    )
        elif self.isModelML:
            # link to pymodel class for ml/ai models
            cwd = os.getcwd()
            if "user_ml_ai_models" not in os.getcwd():
                os.chdir(os.path.join(os.getcwd(), "user_ml_ai_models"))

            # check which type of file Keras needs to load
            if os.path.exists(os.path.join(os.getcwd(), str(self.modelName) + ".h5")):
                extension = ".h5"
            elif os.path.exists(
                os.path.join(os.getcwd(), str(self.modelName) + ".json")
            ):
                extension = ".json"
            elif os.path.exists(os.path.join(os.getcwd(), str(self.modelName) + ".pt")):
                extension = ".pt"  # this is for PyTorch models
            elif os.path.exists(
                os.path.join(os.getcwd(), str(self.modelName) + ".pkl")
            ):
                extension = ".pkl"  # this is for Sci Kit Learn models
            else:  # assume it's a folder with no extension
                extension = ""

            if extension == ".pt":  # use Pytorch loading syntax
                # attempt to unserialize using torch.jit.load command
                self.model = torch_load(str(self.modelName) + extension)
                trainer = "torch"
            elif (
                extension == ".pkl"
            ):  # use importlib/pickle loading syntax for SciKitLearn models
                with open(str(self.modelName) + extension, "rb") as file:
                    self.model = pickle_load(file)
                trainer = "sklearn"
            elif extension != ".json":  # use standard Keras load method
                try:  # see if custom layer script exists
                    module = import_module(str(self.modelName))  # contains CustomLayer
                    self.model = load(
                        str(self.modelName) + extension,
                        custom_objects={
                            str(self.modelName): getattr(module, str(self.modelName))
                        },
                    )
                    trainer = "keras"
                except (
                    ImportError,
                    ModuleNotFoundError,
                ):  # try to load model without custom layer
                    _logger.info(
                        "Cannot detect CustomLayer object to import, FOQUS "
                        + "will import model without custom attributes."
                    )
                    self.model = load(str(self.modelName) + extension)
                    trainer = "keras"
            else:  # model is a json file, use read method to load dictionary
                with open(str(self.modelName) + extension, "r") as json_file:
                    loaded_json = json_file.read()
                try:  # attempt to load model and weights with custom layer
                    module = import_module(str(self.modelName))  # contains CustomLayer
                    self.model = json_load(
                        loaded_json,
                        custom_objects={
                            str(self.modelName): getattr(module, str(self.modelName))
                        },
                    )  # load architecture
                    trainer = "keras"
                except (
                    ImportError,
                    ModuleNotFoundError,
                ):  # try to load model without custom layer
                    _logger.info(
                        "Cannot detect CustomLayer object to import, FOQUS "
                        + "will import model without custom attributes."
                    )
                    self.model = json_load(loaded_json)  # load architecture
                    trainer = "keras"
                finally:
                    self.model.load_weights(
                        str(self.modelName) + "_weights.h5"
                    )  # load pretrained weights
            os.chdir(cwd)  # reset to original working directory
            inst = pymodel_ml_ai(self.model, trainer)
            for vkey, v in inst.inputs.items():
                self.gr.input[self.name][vkey] = v
            for vkey, v in inst.outputs.items():
                self.gr.output[self.name][vkey] = v

    def updateSCDefaults(self, outfile=None):
        if outfile is None:
            outfile = "{0}.json".format(self.modelName)
        sc = self.gr.turbConfig.getSinterConfig(self.modelName)
        for name, item in sc["inputs"].items():
            if name in self.gr.input[self.name]:
                item["default"] = self.gr.input[self.name][name].value
                item["default"] = item["default"]
        with open(outfile, "wb") as f:
            json.dump(sc, f, indent=2)

    def loadDefaultValues(self):
        """
        Change the current input values to their defaults
        """
        for key, var in self.inVars.items():
            var.value = var.default

        for key, var in self.inVarsVector.items():
            var.value = var.default

    def runCalc(self, nanout=False):
        """
        This function calculates the node's output values from
        the inputs.  First it does the model calculations then
        any Python post-processing calculations.  The model and
        or the post-processing calculations can be omitted.  If
        niether are pressent the model will successfully execute
        but do nothing.
        """
        self.turbineMessages = ""
        self.calcError = -1  # set error code to incomplete
        self.calcCount += 1
        self.altInput = None
        # raise Exception("Test exeception")
        if nanout:
            # Set all outputs to numpy.nan to avoid confusion about
            # whether the output value is valid.  After successful
            # completion the nan values will be replaced.  May want
            # ouput values for initial guess though so I made this
            # optional and disabled for now.  Should check node status
            # instead of depending on nan
            for vname, var in self.outVars.items():
                var.makeNaN()
        # Run Python script before model
        if (
            self.pythonCode != ""
            and self.pythonCode is not None
            and self.scriptMode == "pre"
        ):
            self.runPython()
        # Run model or python script that should run model
        if (
            self.pythonCode != ""
            and self.pythonCode is not None
            and self.scriptMode == "total"
        ):
            self.runPython()
        else:
            self.runModel()
        # Run python script after model.
        if (
            self.pythonCode != ""
            and self.pythonCode is not None
            and self.scriptMode == "post"
        ):
            self.runPython()
        # If you made it here and nothing threw an exception or reset
        # the error code, the cacluation finished succesfully
        if self.calcError == -1:
            self.calcError = 0

    def runModel(self):
        """
        Run the Model associated with the node.
        """
        self.calcError = -1
        if self.isModelNone:
            pass
        elif self.isModelPlugin:
            self.runPymodelPlugin()
        elif self.isModelTurbine:
            self.runTurbineCalc(retry=self.options["Retry"].value)
        elif self.isModelML:
            self.runPymodelMLAI()
        else:
            # This shouldn't happen from the GUI there should
            # be no way to select an unknown model type.
            _logger.error("unknown run type: " + str(self.modelType))
            self.calcError = 9

    def getValues(self):
        x = dict()
        f = dict()
        xvector = dict()
        fvector = dict()
        # Copy the inputs and outputs to easy-to-use temporary dicts
        for vkey, var in self.inVars.items():
            x[vkey] = var.value
        for vkey, var in self.outVars.items():
            f[vkey] = var.value
        for vkey, var in self.inVarsVector.items():
            xvector[vkey] = [var.vector[i].value for i in range(len(var.vector))]
        for vkey, var in self.outVarsVector.items():
            fvector[vkey] = [var.vector[i].value for i in range(len(var.vector))]
        return x, f

    def resetModel(self):
        """
        Stop consumer, when the model is run next a new consumer
        will start up for it.  This is useful if a model fails.
        """
        if self.isModelTurbine:
            self.gr.turbConfig.stopConsumer(self.name)

    def runPymodelPlugin(self):
        """
        Runs a Python node plugin model.
        """
        # create a python model instance if needed
        if not self.pyModel:
            self.pyModel = self.gr.pymodels.plugins[self.modelName].pymodel_pg()
        # set the instance inputs
        for vkey, v in self.gr.input[self.name].items():
            if vkey in self.pyModel.inputs:
                self.pyModel.inputs[vkey].value = v.value
        # run the model
        self.pyModel.setNode(self)
        self.pyModel.run()
        # set the node outputs
        for vkey, v in self.gr.output[self.name].items():
            if vkey in self.pyModel.outputs:
                v.value = self.pyModel.outputs[vkey].value

    def runPython(self):
        # Run the python post code for a node.  I know this could be a
        # big security risk, but for this use it should be okay for now
        #
        # Input variable values are stored in the x dictionary and
        # outputs are stored in the f dictionary
        x = AtDict()
        f = AtDict()
        # Copy the inputs and outputs to easy-to-use temporary dicts
        for vkey, var in self.inVars.items():
            x[vkey] = var.value
        for vkey, var in self.outVars.items():
            f[vkey] = var.value
        # Now try to execute the post code
        try:
            exec(self.pythonCode)
            # copy the output variables values back, and don't allow
            # modification of the input values (you can if you get
            # tricky but don't know why you would.  That would be very
            # confusing.
            for vkey, var in f.items():
                if vkey in self.outVars:
                    self.outVars[vkey].value = var
                    for vec in self.outVarsVector:
                        if vec in vkey:
                            idx = int(vkey.split("_")[-1])
                            self.outVars[vkey].value = self.outVarsVector[vec].vector[
                                idx
                            ]["value"]
        except PyCodeInterupt as e:
            _logger.error("Node script interupt: " + str(e))
            if self.calcError == -1:
                # if no error code set go with 50
                # otherwise the sim would appear to be successful
                self.calcError = 50
        except NpCodeEx as e:
            _logger.exception(
                "Error in node python code: {0}, {1}".format(e.code, e.msg)
            )
            self.calcError = e.code
        except Exception as e:
            _logger.exception("Error in node python code")
            self.calcError = 21

    def generateInputJSON(self):
        # Takes the input variables in the sinter set and generates
        # a json input file in the format expected by the turbine
        # gateway currently this json file is just for one at a time
        try:
            cid = self.gr.turbConfig.consumerID(self.name)
        except:
            cid = None
        inputSetL1 = dict()
        inputSetL2 = dict()
        inputSetL1["Simulation"] = self.modelName
        inputSetL1["Initialize"] = self.options["Initialize Model"].value
        inputSetL1["Reset"] = self.options["Reset"].value
        inputSetL1["Visible"] = self.options["Visible"].value
        inputSetL1["Input"] = inputSetL2
        if cid is not None and cid != 0:
            inputSetL1["ConsumerId"] = cid
            # inputSetL1["ConsumerId"] = cid.replace('-', "")
        runList = [inputSetL1]
        for vkey, var in self.gr.input[self.name].items():
            if var.set == "sinter":
                try:
                    if self.altInput is not None:
                        # WHY pylint erroneously reports this as an error,
                        # because it is not able to take the "is not None" check into account
                        # pylint: disable=unsubscriptable-object
                        inputSetL2[vkey] = self.altInput[vkey]
                        # pylint: enable=unsubscriptable-object
                    else:
                        inputSetL2[vkey] = var.value
                except:
                    self.calcError = 23
                    raise NodeEx(
                        code=23,
                        msg="Node: {0}, Var: {1}, Value: {2}".format(
                            self.name, vkey, var.value
                        ),
                    )
        for vkey, var in self.options.items():
            if var.optSet == NodeOptionSets.SINTER_OPTIONS:
                inputSetL1["Input"][vkey] = var.value
        s = json.dumps(runList, sort_keys=True, indent=2)
        _logger.debug("Generated Job JSON:\n" + s)
        return s

    def runTurbineCalc(self, retry=False):
        """
        This function runs turbine models
        """
        res = None
        altTurb = self.options["Override Turbine Configuration"].value
        maxWaitTime = self.options["Maximum Wait Time (s)"].value
        maxRunTime = self.options["Maximum Run Time (s)"].value
        minCheckInt = self.options["Min Status Check Interval"].value
        maxCheckInt = self.options["Max Status Check Interval"].value
        alwarn = self.options["Allow Simulation Warnings"].value
        maxConsumerUse = self.options["Max consumer reuse"].value
        app = self.turbApp
        # app = self.gr.turbConfig.getSimApplication(self.modelName)
        configProfile = self.gr.turbConfig
        if altTurb != "":
            # use alternate to local TurbineLite
            # less good but sometimes needed to run a special kind of
            # simulation that can't be run locally.
            localRun = False
        else:
            # This is always the first choice, almost always use this
            localRun = True  # use local
        # Reload the TurbineConfig depending on run type.
        if localRun:
            configProfile.updateSettings()
        else:
            configProfile.updateSettings(altConfig=altTurb)
            _logger.debug(
                "Alternate Turbine configuration: {0} for node: {1}".format(
                    altTurb, self.name
                )
            )
        # turbine session id
        sid = self.createTurbineSession(forceNew=False)
        # check consumer reuse counter
        # Count that the consumer has been used. stop if hit maxuse
        if localRun and maxConsumerUse > 0:
            count = configProfile.consumerCount(self.name)
            if count >= maxConsumerUse:
                _logger.debug(
                    "Max consumer use exceeded restarting consumer {0}".format(
                        self.name
                    )
                )
                configProfile.stopConsumer(self.name)
        # Start consumer for this model.  If already started this
        # does nothing.
        if localRun:
            configProfile.startConsumer(self.name, self.modelName)
            configProfile.consumerCountInc(self.name)
        # Generate json string for job and load it
        inputjson = self.generateInputJSON()
        inputData = json.loads(inputjson)
        try:  # try to append job to turbine session
            jobID = configProfile.retryFunction(
                5, 30, 1, configProfile.createJobsInSession, sid, inputData
            )[0]
        except Exception as e:
            _logger.exception("Failed create job")
            self.calcError = 5
            configProfile.updateSettings()
            return
        # Try to start jobs if doesn't start at first try some more
        try:
            configProfile.retryFunction(5, 30, 1, configProfile.startSession, sid)
        except Exception as e:
            _logger.exception("Failed start job: {0}".format(jobID))
            self.calcError = 8
            configProfile.updateSettings()
            return
        _logger.debug("Started Job: {0} Turbin SID: {1}".format(jobID, sid))
        # Monitor jobs, there are some timeouts if jobs fail to finish
        # in an allowed amount of time they are terminated
        try:
            # passing the node name and model name allows the consumer
            # to be monitored and restarted if it stops unexpectedly.
            res = configProfile.monitorJob(
                jobID,
                maxWaitTime=maxWaitTime,
                maxRunTime=maxRunTime,
                minCheckInt=minCheckInt,
                maxCheckInt=maxCheckInt,
                stopFlag=self.gr.stop,
                nodeName=self.name,
                simName=self.modelName,
                allowWarnings=alwarn,
                app=app,
                checkConsumer=localRun,
            )
            _logger.debug("Job finished successfully: " + str(jobID))
        except TurbineInterfaceEx as e:
            res = configProfile.res
            if e.code == 351:
                self.calcError = 1
            elif e.code == 352:
                self.calcError = 6
            elif e.code == 353:
                self.calcError = 3
            elif e.code == 354:
                self.calcError = 10
            elif e.code == 355:
                self.calcError = 11
            else:
                self.calcError = 7
            _logger.error(
                "Error while motoring job: {0}, Ex: {1}".format(str(jobID), str(e))
            )
        except Exception as e:
            self.calcError = 10
            res = configProfile.res
            _logger.warning(
                "Error while motoring job: {0}, Ex: {1}".format(str(jobID), str(e))
            )
        # if error code is not -1 some other error and sim not successful
        readResults = True
        if self.calcError == -1:
            _logger.info("Job " + str(jobID) + " Finished Successfully")
        else:
            # The job failed, don't know why but I'll restart the
            # consumer so that the next run will be less likely to fail.
            if localRun and self.options["Reset on Fail"].value:
                _logger.info(
                    "Job failed, stopping consumer for {0}".format(self.modelName)
                )
                self.resetModel()
            elif localRun:
                _logger.info(
                    "Job failed, will not stop consumer for {0}".format(self.modelName)
                )
            # Possibly retry the simulation if it failed
            if retry and not self.gr.stop.isSet():
                _logger.info("Retrying Failed Job " + str(jobID))
                # rerun this function
                # reset error code so doesn't automatically think
                # the retry fails.
                self.calcError = -1
                self.runTurbineCalc(retry=False)
                # don't read results if retrying because the results
                # will be read in the retry call if successful
                readResults = False
            else:
                _logger.info("Job " + str(jobID) + " Failed will not retry")
        # Even if there was an error try to read output
        _logger.debug("Job " + str(jobID) + " Results:\n" + json.dumps(res))
        if res is not None:
            m = res.get("Messages", "")
            if m is None or m == "":
                self.turbineMessages = ""
            else:
                self.turbineMessages = json.dumps(m)
            # single quotes are bad news when trying to instert this into
            # the TurbineLite database in consumer mode so they gone
            self.turbineMessages = self.turbineMessages.replace("'", '"')
        if res and readResults and "Output" in res and res["Output"]:
            outputlog = []
            for vname in res["Output"]:
                try:
                    self.gr.output[self.name][vname].value = res["Output"][vname][
                        "value"
                    ]
                    outputlog.append(
                        "{0} = {1}".format(vname, res["Output"][vname]["value"])
                    )
                except KeyError:
                    # if there is an output of the simulation that
                    # doesn't match the outputs in the node that's
                    # okay may have deleted a variable.  Simulation may
                    # also have failed before producing any output.
                    _logger.exception()
            _logger.debug("Outputs: {0}\n".format("\n".join(outputlog)))
        # reset the turbine config back to whatever is in the settings
        # in case an alternative config was used.
        configProfile.updateSettings()

    def createTurbineSession(self, forceNew=True):
        """
        Create a new Turbine session for grouping
        simulation results on Turbine.
        """
        # Check that a simulation is assigned to this node and that the
        # run type is turbine otherwise return None, this will mean that
        # the node is not using turbine to run
        if self.modelType != nodeModelTypes.MODEL_TURBINE:
            self.turbSession = None
            return None
        # If force new loose the old session so need a new one
        if forceNew:
            self.turbSession = None
        # Try to get a new session id from the gateway if exists
        if self.turbSession:
            # check that it is valid
            try:
                if self.gr.turbConfig.sessionExists(self.turbSession):
                    return self.turbSession
            except Exception as e:
                _logger.exception(
                    "Failed to check for existence of session while"
                    " creating session, Exception: "
                )
                return 0
        # Session didn't exist so create a new id
        try:
            self.turbSession = self.gr.turbConfig.createSession()
        except Exception as e:
            _logger.exception("Failed to create a new session.")
            self.turbSession = 0
            return 0
        return self.turbSession

    def killTurbineSession(self):
        """
        Tries to kill all turbine jobs associated with this node
        started by any thread or process.
        """
        if self.modelType != nodeModelTypes.MODEL_TURBINE:
            return
        if self.modelName == "" or self.modelName == None:
            return
        sid = self.turbSession
        if sid == 0 or sid == "" or sid == None:
            return
        try:
            self.gr.turbConfig.killSession(sid)
        except Exception as e:
            _logger.error(
                "Failed to kill session sid: {0} Exception: {1}".format(sid, str(e))
            )

    def runPymodelMLAI(self):
        """
        Runs a Neural Network machine learning/artificial intelligence model.
        """
        # create a python model instance if needed
        if not self.pyModel:
            # load ml_ai_model and build pymodel class object
            cwd = os.getcwd()
            if "user_ml_ai_models" not in os.getcwd():
                os.chdir(os.path.join(os.getcwd(), "user_ml_ai_models"))

            # check which type of file Keras needs to load
            if os.path.exists(os.path.join(os.getcwd(), str(self.modelName) + ".h5")):
                extension = ".h5"
            elif os.path.exists(
                os.path.join(os.getcwd(), str(self.modelName) + ".json")
            ):
                extension = ".json"
            elif os.path.exists(os.path.join(os.getcwd(), str(self.modelName) + ".pt")):
                extension = ".pt"  # this is for PyTorch models
            elif os.path.exists(
                os.path.join(os.getcwd(), str(self.modelName) + ".pkl")
            ):
                extension = ".pkl"  # this is for Sci Kit Learn models
            else:  # assume it's a folder with no extension
                extension = ""

            if extension == ".pt":  # use Pytorch loading syntax
                # attempt to unserialize using torch.jit.load command
                self.model = torch_load(str(self.modelName) + extension)
                trainer = "torch"
            elif (
                extension == ".pkl"
            ):  # use importlib/pickle loading syntax for SciKitLearn models
                with open(str(self.modelName) + extension, "rb") as file:
                    self.model = pickle_load(file)
                trainer = "sklearn"
            elif extension != ".json":  # use standard Keras load method
                try:  # see if custom layer script exists
                    module = import_module(str(self.modelName))  # contains CustomLayer
                    self.model = load(
                        str(self.modelName) + extension,
                        custom_objects={
                            str(self.modelName): getattr(module, str(self.modelName))
                        },
                    )
                    trainer = "keras"
                except (
                    ImportError,
                    ModuleNotFoundError,
                ):  # try to load model without custom layer
                    _logger.info(
                        "Cannot detect CustomLayer object to import, FOQUS "
                        + "will import model without custom attributes."
                    )
                    self.model = load(str(self.modelName) + extension)
                    trainer = "keras"
            else:  # model is a json file, use read method to load dictionary
                with open(str(self.modelName) + extension, "r") as json_file:
                    loaded_json = json_file.read()
                try:  # attempt to load model and weights with custom layer
                    module = import_module(str(self.modelName))  # contains CustomLayer
                    self.model = json_load(
                        loaded_json,
                        custom_objects={
                            str(self.modelName): getattr(module, str(self.modelName))
                        },
                    )  # load architecture
                    trainer = "keras"
                except (
                    ImportError,
                    ModuleNotFoundError,
                ):  # try to load model without custom layer
                    _logger.info(
                        "Cannot detect CustomLayer object to import, FOQUS "
                        + "will import model without custom attributes."
                    )
                    self.model = json_load(loaded_json)  # load architecture
                    trainer = "keras"
                finally:
                    self.model.load_weights(
                        str(self.modelName) + "_weights.h5"
                    )  # load pretrained weights
            os.chdir(cwd)  # reset to original working directory
            self.pyModel = pymodel_ml_ai(self.model, trainer)
        # set the instance inputs
        for vkey, v in self.gr.input[self.name].items():
            if vkey in self.pyModel.inputs:
                self.pyModel.inputs[vkey].value = v.value
        # run the model
        self.pyModel.setNode(self)
        self.pyModel.run()
        # set the node outputs
        for vkey, v in self.gr.output[self.name].items():
            if vkey in self.pyModel.outputs:
                v.value = self.pyModel.outputs[vkey].value
