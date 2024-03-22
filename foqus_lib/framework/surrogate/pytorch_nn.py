#################################################################################
# FOQUS Copyright (c) 2012 - 2024, by the software owners: Oak Ridge Institute
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

import numpy as np
import pandas as pd
import torch  # pylint: disable=import-error
import torch.nn as nn  # pylint: disable=import-error

from foqus_lib.framework.listen import listen
from foqus_lib.framework.session.session import exePath

# from foqus_lib.framework.graph.graph import Graph
from foqus_lib.framework.surrogate.surrogate import surrogate
from foqus_lib.framework.uq.SurrogateParser import SurrogateParser

# custom class to define Keras NN layers
np.random.seed(46)
rn.seed(1342)
torch.manual_seed(62)
torch.cuda.manual_seed(62)
torch.cuda.manual_seed_all(62)
torch.backends.cudnn.benchmark = False
torch.backends.cudnn.deterministic = True

device = "cuda" if torch.cuda.is_available() else "cpu"

# Example follows the sequence below:
# 1) Code at end of file to import data and create model
# 2) Call create_model() to define inputs and outputs
# 3) Call CustomLayer to define network structure, which uses
#    call() to define layer connections and get_config to attach
#    attributes to CustomLayer class object
# 4) Back to create_model() to compile and train model
# 5) Back to code at end of file to save, load and test model

# custom class to define Pytorch NN layers


def validate_training_data(x_train: torch.Tensor, z_train: torch.Tensor):
    number_columns_in_x_train = x_train.size()[1]
    number_columns_in_z_train = z_train.size()[1]
    errors = []

    if number_columns_in_x_train < 1 and number_columns_in_z_train < 1:
        errors.append("Training data is empty")

    if number_columns_in_x_train < 1:
        errors.append("No columns in input training data")

    if number_columns_in_z_train < 1:
        errors.append("No columns in output training data")

    if errors:
        message = f"Invalid input:{errors}"
        raise ValueError(message)


class mea_column_model_customnormform_pytorch(nn.Module):
    def __init__(
        self,
        input_labels=None,
        output_labels=None,
        input_bounds=None,
        output_bounds=None,
        normalized=False,
        normalization_form="Linear",
        normalization_function=None,
        **kwargs,
    ):

        super(
            mea_column_model_customnormform_pytorch, self
        ).__init__()  # create callable object

        # add attributes from model data
        self.input_labels = input_labels
        self.output_labels = output_labels
        self.input_bounds = input_bounds
        self.output_bounds = output_bounds
        self.normalized = normalized  # FOQUS will read this and adjust accordingly
        self.normalization_form = (
            normalization_form  # tells FOQUS which scaling form to use
        )
        self.normalization_function = (
            normalization_function  # tells FOQUS scaling formula to use
        )

    def forward(self, x):
        return x


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
        "Description":"pytorch_nn model training FOQUS Plugin",
        "MIMEType":"application/ccsi+foqus",
        "Confidence":"testing",
        "Parents":[],
        "UpdateMetadata":True,
        "Version":""}
    """
    name = "pytorch_nn-model-training"

    def __init__(self, dat=None):
        """
        pytorch_nn interface constructor
        """
        surrogate.__init__(self, dat)
        self.name = "pytorch_nn"
        self.ex = None
        # still working on hanging indent for references
        self.methodDescription = (
            "<html>\n<head>"
            ".hangingindent {\n"
            "    margin-left: 22px ;\n"
            "    text-indent: -22px ;\n"
            "}\n"
            "</head>\n"
            "Pytorch is a machine learning framework based on the Torch library. "
            "The framework represents data using tensors, multidimensional arrays on which "
            "computations are performed and used to build deep learning neural networks. "
            "Users may follow the recommended workflow to install and use Pytorch, "
            "as described in the Pytorch documentation: https://pytorch.org/docs/stable/index.html."
            '<p class="pytorch_nn</p>"</html>'
        )
        self.alamoDir = "pytorch_nn"
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
            default="user_ml_ai_models/nn_model.pt",
            desc="Name of output file for model, should have file extension: .pt",
            hint="Enter a custom file name if desired",
        )

    def run(self):
        """
        This function overloads the Thread class function,
        and is called when you run start() to start a new thread.
        """
        np.random.seed(46)
        rn.seed(1342)
        torch.manual_seed(62)
        torch.cuda.manual_seed(62)
        torch.cuda.manual_seed_all(62)
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True

        device = "cuda" if torch.cuda.is_available() else "cpu"

        self.msgQueue.put("Starting training process")

        self.msgQueue.put(f"input vars: {self.input}")
        self.msgQueue.put(f"output vars: {self.output}")
        input_data, output_data = self.getSelectedInputOutputData()
        self.msgQueue.put(f"input data columns: {input_data.columns}")
        self.msgQueue.put(f"output data columns: {output_data.columns}")

        # Example follows the sequence below:
        # 1) Code at end of file to import data and create model
        # 2) Call create_model() to define inputs and outputs
        # 3) Call CustomLayer to define network structure, which uses
        #    call() to define layer connections and get_config to attach
        #    attributes to CustomLayer class object
        # 4) Back to create_model() to compile and train model
        # 5) Back to code at end of file to save, load and test model

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

        # raise exception here after BPC position
        # create model
        x_train = torch.from_numpy(xdata).float().to(device)
        z_train = torch.from_numpy(zdata).float().to(device)

        # print type at this point
        # can also print inside create_model

        try:
            model = create_model(
                x_train,
                z_train,
                xlabels,
                zlabels,
                input_bounds=xdata_bounds,
                output_bounds=zdata_bounds,
                normalized=True,
                normalization_form="Custom",
                normalization_function="(datavalue - dataminimum)/(datamaximum - dataminimum)",
            )
        except Exception as e:
            self.msgQueue.put(f"The training terminated with an error: {e}")
            return
        # else:
        self.msgQueue.put("Model created successfully")
        print(model)

        # x = torch.tensor(xdata, dtype=torch.float)
        # zfit = model(x).detach().numpy()

        # save model as PT format
        file_name = self.options["output_file"].value
        model_scripted = torch.jit.script(model)
        model_scripted.save(file_name)
        # self.msgQueue.put(type(x_train))
        # self.msgQueue.put(type(z_train))
        # self.msgQueue.put(x_train.size())
        # self.msgQueue.put(z_train.size())
        self.msgQueue.put(model)
        self.msgQueue.put("Training complete")
        self.msgQueue.put(f"Model saved to {file_name}")


class main_model(nn.Module):
    def __init__(self, input_labels=None, hidden=20, output_labels=None, **kwargs):
        super().__init__()
        self.linear = nn.Linear(len(input_labels), hidden)
        self.relu = nn.ReLU(inplace=False)
        self.sigmoid = nn.Sigmoid()
        self.out = nn.Linear(hidden, len(output_labels))
        self.custom = mea_column_model_customnormform_pytorch(
            input_labels=input_labels,
            output_labels=output_labels,
            **kwargs,
        )

    def forward(self, x):
        x = self.linear(x)
        x = self.relu(x)
        x = self.out(x)
        x = self.custom(x)

        return x


def create_model(x_train, z_train, x_labels, z_labels, **kwargs):
    # use print?
    print(f"using input variables: {x_labels}")
    print(f"using output variables: {z_labels}")
    validate_training_data(x_train, z_train)
    model = main_model(
        input_labels=x_labels, output_labels=z_labels, hidden=20, **kwargs
    )
    loss_function = nn.MSELoss()
    optimizer = torch.optim.RMSprop(model.parameters(), lr=0.01)
    epochs = 500
    final_losses = []

    for i in range(epochs):
        i = i + 1
        y_pred = model.forward(x_train)
        loss = loss_function(y_pred, z_train)
        final_losses.append(loss)
        if i == 1 or i % 25 == 0:
            print("Epoch number: {} and the loss : {}".format(i, loss.item()))
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    model.eval()  # evaluates the weights, not a specific output

    return model
