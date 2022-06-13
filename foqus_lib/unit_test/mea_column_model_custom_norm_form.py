import os
import numpy as np
import pandas as pd
import random as rn

# pylint: disable=import-error

import tensorflow as tf

# pylint: enable=import-error

# set seed values for reproducibility
os.environ["PYTHONHASHSEED"] = "0"
os.environ[
    "CUDA_VISIBLE_DEVICES"
] = ""  # changing "" to "0" or "-1" may solve import issues
np.random.seed(46)
rn.seed(1342)
tf.random.set_seed(62)

# custom class to define Keras NN layers
# note that this model is identical to mea_column_model in every aspect
# except for normalization, but needs a unique class name for the Keras
# registry - otherwise this will throw errors when both are loaded in FOQUS


@tf.keras.utils.register_keras_serializable()
class mea_column_model_custom_norm_form(tf.keras.layers.Layer):
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
        normalization_function=None,
        **kwargs
    ):

        super(
            mea_column_model_custom_norm_form, self
        ).__init__()  # create callable object

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
        self.normalization_function = (
            normalization_function  # tells FOQUS scaling formula to use
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
        config = super(mea_column_model_custom_norm_form, self).get_config()
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
                "normalization_function": self.normalization_function,
            }
        )
        return config
