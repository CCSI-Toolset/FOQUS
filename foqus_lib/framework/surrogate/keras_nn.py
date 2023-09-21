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
begining of the file (see pluginSearch.plugins() for exact character count of
text).  They also need to have a .py extension and inherit the surrogate class.

* This is an example of a surrogate model builder plugin for FOQUS,
  it uses the ALAMO surrogate model builder program ref:

  Cozad, A., N. V. Sahinidis and D. C. Miller, Automatic Learning of
      Algebraic Models for Optimization, AIChE Journal, accepted, 2014.

* A setting of this plugin is the location of the ALAMO executable

John Eslick, Carnegie Mellon University, 2014

"""


from contextlib import nullcontext
from tokenize import String
from pathlib import Path
import numpy as np
import pandas as pd
import threading
import queue
import logging
import subprocess
import os
import sys
import copy
import traceback
import time
import shutil
import re
import math

try:
    import win32api  # used to get short file name for alamo sim exe
    import win32process
except:
    pass
# from foqus_lib.framework.graph.graph import Graph
from foqus_lib.framework.surrogate.surrogate import surrogate
from foqus_lib.framework.uq.SurrogateParser import SurrogateParser
from foqus_lib.framework.listen import listen
from foqus_lib.framework.session.session import exePath
from multiprocessing.connection import Client

import random as rn
import tensorflow as tf  # pylint: disable=import-error

# custom class to define Keras NN layers
@tf.keras.utils.register_keras_serializable()
class keras_nn(tf.keras.layers.Layer):
    def __init__(
        self,
        n_hidden=1,
        n_neurons=12,
        layer_act="relu",
        out_act="sigmoid",
        input_labels=None,
        output_labels=None,
        input_bounds=None,
        output_bounds=None,
        normalized=False,
        normalization_form="Linear",
        **kwargs,
    ):

        super().__init__()  # create callable object

        # add attributes from training settings
        self.n_hidden = n_hidden
        self.n_neurons = n_neurons
        self.layer_act = layer_act
        self.out_act = out_act

        # add attributes from model data
        self.input_labels = input_labels
        self.output_labels = output_labels
        self.input_bounds = input_bounds
        self.output_bounds = output_bounds
        self.normalized = normalized  # FOQUS will read this and adjust accordingly
        self.normalization_form = (
            normalization_form  # tells FOQUS which scaling form to use
        )

        # create lists to contain new layer objects
        self.dense_layers = []  # hidden or output layers
        self.dropout = []  # for large number of neurons, certain neurons
        # can be randomly dropped out to reduce overfitting

        for layer in range(self.n_hidden):
            self.dense_layers.append(
                tf.keras.layers.Dense(self.n_neurons, activation=self.layer_act)
            )

        self.dense_layers_out = tf.keras.layers.Dense(2, activation=self.out_act)

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
    def get_config(self):
        config = super().get_config()
        config.update(
            {
                "n_hidden": self.n_hidden,
                "n_neurons": self.n_neurons,
                "layer_act": self.layer_act,
                "out_act": self.out_act,
                "input_labels": self.input_labels,
                "output_labels": self.output_labels,
                "input_bounds": self.input_bounds,
                "output_bounds": self.output_bounds,
                "normalized": self.normalized,
                "normalization_form": self.normalization_form,
            }
        )
        return config


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
        "Description":"keras_nn model training FOQUS Plugin",
        "MIMEType":"application/ccsi+foqus",
        "Confidence":"testing",
        "Parents":[],
        "UpdateMetadata":True,
        "Version":""}
    """
    name = "keras_nn-model-training"

    def __init__(self, dat=None):
        """
        keras_nn interface constructor
        """
        surrogate.__init__(self, dat)
        self.name = "keras_nn"
        self.ex = None
        # still working on hanging indent for references
        self.methodDescription = (
            "<html>\n<head>"
            ".hangingindent {\n"
            "    margin-left: 22px ;\n"
            "    text-indent: -22px ;\n"
            "}\n"
            "</head>\n"
            "The high-level neural network library of Keras integrates with TensorFlow’s"
            "machine learning library to train complex models within Python’s user-friendly framework."
            "Keras models may be largely split into two types: Sequential which build linearly connected"
            "model layers, and Functional which build multiple interconnected layers in a complex system."
            "More information on TensorFlow Keras model building is described by (Wu et al. 2020)."
            "Users may follow the recommended workflow to install and use TensorFlow in a Python environment,"
            "as described in the TensorFlow documentation: https://www.tensorflow.org/install."
            '<p class="keras_nn</p>"</html>'
        )
        self.alamoDir = "keras_nn"
        self.inputCols = [
            ("FGIN (kg/hr)", float, 1.0),
            ("FGIN_CO2MASSFRAC", float, 1.0),
            ("SOLVENTIN (kg/hr)", float, 1.0),
            ("STRIPPER_PRESSURE (kPa)", float, 1.0),
            ("SOLVENTAMINECONC", float, 1.0),
            ("SOLVENTCO2LOADING", float, 1.0),
            ("CO2CAPTUREPERC", float, 1.0),
            ("SRD (MJ/kg CO2)", float, 1.0),
        ]

        self.outputCols = [
            ("FGIN (kg/hr)", float, 1.0),
            ("FGIN_CO2MASSFRAC", float, 1.0),
            ("SOLVENTIN (kg/hr)", float, 1.0),
            ("STRIPPER_PRESSURE (kPa)", float, 1.0),
            ("SOLVENTAMINECONC", float, 1.0),
            ("SOLVENTCO2LOADING", float, 1.0),
            ("CO2CAPTUREPERC", float, 1.0),
            ("SRD (MJ/kg CO2)", float, 1.0),
        ]
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
            name="input_file",
            section="DATA Settings",
            dtype=str,
            default=str(
                Path(__file__).with_name("MEA_carbon_capture_dataset_mimo.csv")
            ),
            desc="Input file",
            hint="Input file path",
        )

        self.options.add(
            name="input_labels",
            section="DATA Settings",
            dtype=str,
            default="FGIN (kg/hr),FGIN_CO2MASSFRAC,SOLVENTIN (kg/hr),STRIPPER_PRESSURE (kPa),SOLVENTAMINECONC,SOLVENTCO2LOADING",
            desc="comma separated",
            hint="Input columns",
        )

        self.options.add(
            name="output_labels",
            section="DATA Settings",
            dtype=str,
            default="CO2CAPTUREPERC,SRD (MJ/kg CO2)",
            desc="comma separated",
            hint="Output columns",
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

    def run(self):
        """
        This function overloads the Thread class function,
        and is called when you run start() to start a new thread.
        """
        # set seed values for reproducibility
        os.environ["PYTHONHASHSEED"] = "0"
        os.environ[
            "CUDA_VISIBLE_DEVICES"
        ] = ""  # changing "" to "0" or "-1" may solve import issues
        np_seed = self.options["numpy_seed"].value
        rn_seed = self.options["random_seed"].value
        tf_seed = self.options["tensorflow_seed"].value

        epochs_count = self.options["epoch"].value
        verbose_setting = self.options["verbose"].value
        self.msgQueue.put(f"{self.input=}")
        self.msgQueue.put(f"{self.output=}")
        input_data, output_data = self.getSelectedInputOutputData()
        self.msgQueue.put(f"{input_data.columns=}")
        self.msgQueue.put(f"{output_data.columns=}")

        # np.random.seed(46)
        # rn.seed(1342)
        # tf.random.set_seed(62)

        np.random.seed(np_seed)
        rn.seed(rn_seed)
        tf.random.set_seed(tf_seed)

        self.msgQueue.put("Starting training process")

        # Example follows the sequence below:
        # 1) Code at end of file to import data and create model
        # 2) Call create_model() to define inputs and outputs
        # 3) Call CustomLayer to define network structure, which uses
        #    call() to define layer connections and get_config to attach
        #    attributes to CustomLayer class object
        # 4) Back to create_model() to compile and train model
        # 5) Back to code at end of file to save, load and test model

        # import data
        # data = pd.read_csv(r"/Users/sfhome/Desktop/CCI_Spring_2023/foqus/CCSI-Toolset/FOQUS/examples/other_files/ML_AI_Plugin/MEA_carbon_capture_dataset_mimo.csv")
        current_directory = os.path.dirname(__file__)

        input_file = str(self.options["input_file"].value)

        # data = pd.read_csv(current_directory + os.path.sep + input_file)
        data = pd.read_csv(input_file)
        # define these two after xlabels and zlabels
        # xdata = data.iloc[:, :6]  # there are 6 input variables/columns
        # zdata = data.iloc[:, 6:]  # the rest are output variables/columns

        # xlabels = xdata.columns.tolist()  # set labels as a list (default) from pandas
        # zlabels = zdata.columns.tolist()  #    is a set of IndexedDataSeries objects

        xlabels = str(self.options["input_labels"].value).split(",")
        zlabels = str(self.options["output_labels"].value).split(",")

        # tried the below code that didn't work
        xdata = data.loc[:, xlabels]  # there are 6 input variables/columns
        zdata = data.loc[:, zlabels]  # the rest are output variables/columns

        xdata_bounds = {i: (xdata[i].min(), xdata[i].max()) for i in xdata}  # x bounds
        zdata_bounds = {j: (zdata[j].min(), zdata[j].max()) for j in zdata}  # z bounds

        # normalize data using Linear form
        # users can normalize with any allowed form # manually, and then pass the
        # appropriate flag to FOQUS from the allowed list:
        # ["Linear", "Log", "Power", "Log 2", "Power 2"] - see the documentation for
        # details on the scaling formulations
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
        )  # Keras requires a Numpy array as input

        # define x and z data, not used but will add to variable dictionary
        xdata = model_data[:, :-2]
        zdata = model_data[:, -2:]

        # method to create model
        def create_model(data):

            inputs = tf.keras.Input(shape=(np.shape(data)[1],))  # create input layer

            layers = keras_nn(  # define the rest of network using our custom class
                # add our 4 options
                input_labels=xlabels,
                output_labels=zlabels,
                input_bounds=xdata_bounds,
                output_bounds=zdata_bounds,
                normalized=True,
                normalization_form="Linear",
            )

            outputs = layers(inputs)  # use network as function outputs = f(inputs)

            model = tf.keras.Model(inputs=inputs, outputs=outputs)  # create model

            model.compile(loss="mse", optimizer="RMSprop", metrics=["mae", "mse"])

            model.fit(
                xdata, zdata, epochs=epochs_count, verbose=verbose_setting
            )  # train model

            return model

        # create model
        model = create_model(xdata)
        model.summary()
        # self.msgQueue.put(model)

        self.msgQueue.put("Training complete")
        # save model as H5
        model.save("keras_nn.h5")
