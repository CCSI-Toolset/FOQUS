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
""" #FOQUS_SURROGATE_PLUGIN

Surrogate plugins need to have the string "#FOQUS_SURROGATE_PLUGIN" near the
beginning of the file (see pluginSearch.plugins() for exact character count of
text).  They also need to have a .py extension and inherit the surrogate class.

"""


import copy
import logging
import math
import os
import pickle
import queue
import random as rn
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
from contextlib import nullcontext
from multiprocessing.connection import Client
from pathlib import Path
from tokenize import String
from types import SimpleNamespace

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor  # pylint: disable=import-error

from foqus_lib.framework.listen import listen
from foqus_lib.framework.session.session import exePath

# from foqus_lib.framework.graph.graph import Graph
from foqus_lib.framework.surrogate.surrogate import surrogate
from foqus_lib.framework.uq.SurrogateParser import SurrogateParser


def validate_training_data(xdata: np.ndarray, zdata: np.ndarray):
    number_columns_in_xdata = xdata.shape[1]
    number_columns_in_zdata = zdata.shape[1]
    errors = []

    if number_columns_in_xdata < 1 and number_columns_in_zdata < 1:
        errors.append("Training data is empty")

    if number_columns_in_xdata < 1:
        errors.append("No columns in input training data")

    if number_columns_in_zdata < 1:
        errors.append("No columns in output training data")

    if number_columns_in_zdata > 1:
        errors.append("Support for multicolumn dataset output not yet available")
        # todo: check if MLPRegressor works with multiple output columns
    if errors:
        message = f"Invalid input:{errors}"
        raise ValueError(message)


# define network layer connections
def call(self, inputs):

    x = inputs  # single input layer, input defined in create_model()
    for layer in self.dense_layers:  # hidden layers
        x = layer(x)  # h1 = f(input), h2 = f(h1), ... using act func
    for layer in self.dropout:  # no dropout layers used in this example
        x = layer(x)
    x = self.dense_layers_out(x)  # single output layer, output = f(h_last)

    return x


# attach attributes to class CONFIG


def checkAvailable():
    """Plug-ins should have this function to check availability of any
    additional required software.  If requirements are not available
    plug-in will not be available.
    """
    # I don't really check anything for now the ALAMO exec location is
    # just a setting of the plug-in, you may or may not need GAMS or
    # MATLAB
    return True


class surrogateMethod(surrogate):
    metaDataJsonString = """
    "CCSIFileMetaData":{
        "ID":"uuid",
        "CreationTime":"",
        "ModificationTime":"",
        "ChangeLog":[],
        "DisplayName":"",
        "OriginalFilename":"",
        "Application":"foqus_surogate_plugin",
        "Description":"scikit_nn model training FOQUS Plugin",
        "MIMEType":"application/ccsi+foqus",
        "Confidence":"testing",
        "Parents":[],
        "UpdateMetadata":True,
        "Version":""}
    """
    name = "scikit_nn-model-training"

    def __init__(self, dat=None):
        """
        scikit_nn interface constructor
        """
        surrogate.__init__(self, dat)
        self.name = "scikit_nn"
        self.ex = None
        # still working on hanging indent for references
        self.methodDescription = (
            "<html>\n<head>"
            ".hangingindent {\n"
            "    margin-left: 22px ;\n"
            "    text-indent: -22px ;\n"
            "}\n"
            "</head>\n"
            "Scikit-learn is an open-source machine learning library in Python, "
            "primarily focused on predictive data analysis using superivised and unsupervised learning. "
            "The library supports classification, regression, model selection, preprocessing, and more. "
            "More information on scikit-learn's design is described by (Buitinck et al. 2013). "
            "Users may follow the recommended workflow to install and use scikit-learn, "
            "as described in the scikit-learn documentation: https://scikit-learn.org/stable/install.html."
            '<p class="scikit_nn</p>"</html>'
        )
        self.alamoDir = "scikit_nn"
        self.updateVarCols()
        # include a Section called DATA Settings
        # Check the ALAMOSettings_v2.xlsx with hints and new labels
        self.options.add(
            name="Initial Data Filter",
            section="DATA Settings",
            default="All",
            dtype=str,
            desc="Filter to be applied to the initial data set.",
            hint="Data filters help the user to generate models based"
            "on specific data for each variable.",
            validValues=["All", "None"],
        )

        self.options.add(
            name="n_hidden",
            section="DATA Settings",
            dtype=int,
            default=1,
            desc="Number of hidden layers",
            hint="Number of hidden layers",
        )

        self.options.add(
            name="n_neurons",
            section="DATA Settings",
            dtype=int,
            default=12,
            desc="Number of neurons",
            hint="Number of neurons",
        )
        self.options.add(
            name="layer_act",
            section="DATA Settings",
            dtype=str,
            default="relu",
            desc="Layer activation function",
            hint="Layer activation function",
            validValues=["relu", "sigmoid"],
        )

        self.options.add(
            name="out_act",
            section="DATA Settings",
            dtype=str,
            default="sigmoid",
            desc="Output activation function",
            hint="Output activation function",
            validValues=["relu", "sigmoid"],
        )

        self.options.add(
            name="numpy_seed",
            section="DATA Settings",
            dtype=int,
            default=46,
            desc="Seed for numpy",
            hint="Seed for numpy",
        )

        self.options.add(
            name="random_seed",
            section="DATA Settings",
            dtype=int,
            default=1342,
            desc="Seed for random",
            hint="Seed for random",
        )

        self.options.add(
            name="tensorflow_seed",
            section="DATA Settings",
            dtype=int,
            default=62,
            desc="Seed for tensorflow",
            hint="Seed for tensorflow",
        )

        self.options.add(
            name="epoch",
            section="DATA Settings",
            dtype=int,
            default=500,
            desc="Number of epochs",
            hint="Number of epochs",
        )

        self.options.add(
            name="verbose",
            section="DATA Settings",
            dtype=int,
            default=0,
            desc="Verbose setting",
            hint="Takes only 0 or 1",
        )

        self.options.add(
            name="output_file",
            section="DATA Settings",
            dtype=str,
            default="user_ml_ai_models/nn_model.pkl",
            desc="Name of output file for model, should have file extension: .pkl",
            hint="Enter a custom file name if desired",
        )

    def run(self):
        """
        This function overloads the Thread class function,
        and is called when you run start() to start a new thread.
        """
        # current_directory = os.path.dirname(__file__)

        self.msgQueue.put(f"input vars: {self.input}")
        self.msgQueue.put(f"output vars: {self.output}")
        input_data, output_data = self.getSelectedInputOutputData()
        self.msgQueue.put(f"input data columns: {input_data.columns}")
        self.msgQueue.put(f"output data columns: {output_data.columns}")

        self.msgQueue.put("Starting training process")

        # method to create model
        # def create_model(x_train, z_train):
        #     self.msgQueue.put(f"using input variables: {xlabels}")
        #     self.msgQueue.put(f"using output variables: {zlabels}")
        #     validate_training_data(x_train, z_train)
        #     mlp = MLPRegressor(
        #         solver="lbfgs",
        #         activation="relu",
        #         hidden_layer_sizes=[12] * 3,  # 3 hidden layers, each with 12 neurons
        #         max_iter=10000,
        #     )
        #     model = mlp.fit(x_train, z_train)
        #     model.custom = SimpleNamespace(
        #         input_labels=xlabels,
        #         output_labels=zlabels,
        #         input_bounds=xdata_bounds,
        #         output_bounds=zdata_bounds,
        #         normalized=True,
        #         normalization_form="Custom",
        #         normalization_function="(datavalue - dataminimum)/(datamaximum - dataminimum)",
        #     )

        #     return model

        # Main code

        # import data
        # data = pd.read_csv(r"MEA_carbon_capture_dataset_mimo.csv")

        xlabels = list(input_data.columns)
        zlabels = list(output_data.columns)

        xdata = input_data
        zdata = output_data

        xdata_bounds = {i: (xdata[i].min(), xdata[i].max()) for i in xdata}  # x bounds
        zdata_bounds = {j: (zdata[j].min(), zdata[j].max()) for j in zdata}  # z bounds

        # normalize data using Linear form, pass as custom string and parse with SymPy
        # users can normalize with any allowed form # manually, and then pass the
        # appropriate flag to FOQUS from the allowed list:
        # ["Linear", "Log", "Power", "Log 2", "Power 2", "Custom] - see the
        # documentation for details on the scaling formulations
        xmax, xmin = xdata.max(axis=0), xdata.min(axis=0)
        zmax, zmin = zdata.max(axis=0), zdata.min(axis=0)
        xdata, zdata = np.array(xdata), np.array(zdata)
        for i in range(len(xdata)):
            for j in range(len(xlabels)):
                xdata[i, j] = (xdata[i, j] - xmin[j]) / (xmax[j] - xmin[j])
            for j in range(len(zlabels)):
                zdata[i, j] = (zdata[i, j] - zmin[j]) / (zmax[j] - zmin[j])

        model_data = np.concatenate(
            (xdata, zdata), axis=1
        )  # PyTorch requires a Numpy array as input

        # define x and z data, not used but will add to variable dictionary
        # xdata = model_data[:, :-2]
        # zdata = model_data[:, -2:]

        # create model

        try:
            model = create_model(
                xlabels=xlabels,
                zlabels=zlabels,
                x_train=xdata,
                z_train=zdata,
                xdata_bounds=xdata_bounds,
                zdata_bounds=zdata_bounds,
            )
        except Exception as e:
            self.msgQueue.put(f"The training terminated with an error: {e}")
            return
        # else:
        self.msgQueue.put("Model created successfully")

        file_name = self.options["output_file"].value
        with open(file_name, "wb") as file:
            pickle.dump(model, file)

        # load model as pickle format
        with open(file_name, "rb") as file:
            loaded_model = pickle.load(file)
            self.msgQueue.put(loaded_model)

        self.msgQueue.put("Training complete")
        self.msgQueue.put(f"Model saved to {file_name}")


def create_model(xlabels, zlabels, x_train, z_train, xdata_bounds, zdata_bounds):
    print(f"using input variables: {xdata_bounds}")
    print(f"using output variables: {zdata_bounds}")
    print(x_train.shape)
    print(z_train.shape)
    validate_training_data(x_train, z_train)
    # if np.ravel is not called on the output, a DataConversionWarning is emitted
    # However, using np.ravel will cause an error if output data contains > 1 columns
    # reshaped = np.ravel(z_train)
    # print(reshaped.shape)
    mlp = MLPRegressor(
        solver="lbfgs",
        activation="relu",
        hidden_layer_sizes=[12] * 3,  # 3 hidden layers, each with 12 neurons
        # trying to set hidden_layer_sizes to resolve DataConversionWarning
        # but does not appear to fix the issue
        # hidden_layer_sizes=(x_train.shape[1], z_train.shape[1]),
        max_iter=10000,
    )
    model = mlp.fit(x_train, z_train)
    model.custom = SimpleNamespace(
        input_labels=xlabels,
        output_labels=zlabels,
        input_bounds=xdata_bounds,
        output_bounds=zdata_bounds,
        normalized=True,
        normalization_form="Custom",
        normalization_function="(datavalue - dataminimum)/(datamaximum - dataminimum)",
    )

    return model
