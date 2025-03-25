#################################################################################
# FOQUS Copyright (c) 2012 - 2025, by the software owners: Oak Ridge Institute
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
import os
import numpy as np
import pandas as pd
import random as rn
import tensorflow as tf

# set seed values for reproducibility
os.environ["PYTHONHASHSEED"] = "0"
os.environ["CUDA_VISIBLE_DEVICES"] = (
    ""  # changing "" to "0" or "-1" may solve import issues
)
np.random.seed(46)
rn.seed(1342)
tf.random.set_seed(62)


# method to create model
def create_model(data):

    inputs = tf.keras.Input(shape=(np.shape(data)[1],))  # create input layer

    # create lists to contain new layer objects
    dense_layers = []  # hidden or output layers
    dropout = []  # for large number of neurons, certain neurons
    # can be randomly dropped out to reduce overfitting

    n_hidden, n_neurons, layer_act, out_act = 1, 12, "relu", "sigmoid"

    for layer in range(n_hidden):
        dense_layers.append(tf.keras.layers.Dense(n_neurons, activation=layer_act))

    dense_layers_out = tf.keras.layers.Dense(2, activation=out_act)

    x = inputs  # single input layer
    for layer in dense_layers:  # hidden layers
        x = layer(x)  # h1 = f(input), h2 = f(h1), ... using act func
    for layer in dropout:  # no dropout layers used in this example
        x = layer(x)
    x = dense_layers_out(x)  # single output layer, output = f(h_last)

    outputs = x  # assign outputs as last layer

    model = tf.keras.Model(inputs=inputs, outputs=outputs)  # create model

    model.compile(loss="mse", optimizer="RMSprop", metrics=["mae", "mse"])

    model.fit(xdata, zdata, epochs=500, verbose=0)  # train model

    return model


# Main code

# import data
data = pd.read_csv(r"../MEA_carbon_capture_dataset_mimo.csv")

xdata = data.iloc[:, :6]  # there are 6 input variables/columns
zdata = data.iloc[:, 6:]  # the rest are output variables/columns

model_data = np.concatenate(
    (xdata, zdata), axis=1
)  # Keras requires a Numpy array as input

# define x and z data, not used but will add to variable dictionary
xdata = model_data[:, :-2]
zdata = model_data[:, -2:]

# create model
model = create_model(xdata)
model.summary()

# save model as standard Keras file format
model.save("mea_column_model_nocustomlayer.keras")
