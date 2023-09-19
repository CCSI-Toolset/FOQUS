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

# Authors: Brayden Gess, Brandon Paul

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Data preprocessing
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

# Neural Net modules
import tensorflow as tf
from tensorflow.keras import Input
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense
from tensorflow.keras.callbacks import EarlyStopping

import os
import random as rn

# set seed values for reproducibility
os.environ["PYTHONHASHSEED"] = "0"
os.environ[
    "CUDA_VISIBLE_DEVICES"
] = ""  # changing "" to "0" or "-1" may solve import issues
np.random.seed(46)
rn.seed(1342)
tf.random.set_seed(62)


def finite_difference(m1, m2, y1, y2, n_x, use_simple_diff=False):
    """
    Calculate the first-order gradient between provided sample points m1 and
    m2, where each point is assumed to be a vector with one or more input
    variables x and exactly one output variable y. y1 is the value of y1 at m1,
    and y2 is the value of y at m2.

    The total gradient is calculated via chain rule assuming a multivariate
    function y(x1, x2, x3, ...). In the notation below, D/D denotes a total
    derivative and d/d denotes a partial derivative. Total derivatives are
    functions of all (x1, x2, x3, ...) whereas partial derivatives are
    functions of one input (e.g. x1) holding (x2, x3, ...) constant:

        Dy/Dx1 = (dy/dx1)(dx1/dx1) + (dy/dx2)(dx2/dx1) + (dy/dx3)(dx3/dx1) +...

    Note that (dx1/dx1) = 1. The partial derivatives dv2/dv1 are estimated
    between sample points m1 and m2 as:

        dv2/dv1 at (m1+m2)/2 = [v2 at m2 - v2 at m1]/[v1 at m2 - v1 at m1]

    The method assumes that m1 is the first point and m2 is the second point,
    and returns a vector dy_dm that is the same length as m1 and m2; m1 and m2
    must be the same length. y1 and y2 must be float or integer values.
    """

    def diff(y2, y1, x2, x1):
        """
        Calculate derivative of y w.r.t. x.
        """
        dv2_dv1 = (y2 - y1) / (x2 - x1)

        return dv2_dv1

    mid_m = [None] * n_x  # initialize dm vector, the midpoints of m1 and m2
    dy_dm = [None] * n_x  # initialize dy vector, this is dy_dm(midpoints)

    for i in range(n_x):  # for each input xi
        if use_simple_diff:
            dy_dm[i] = diff(y2, y1, m2[i], m1[i])
        else:  # use chain rule
            dy_dm[i] = sum(
                diff(y2, y1, m2[j], m1[j])
                * diff(m2[j], m1[j], m2[i], m1[i])  # dy/dxj  # dxj/dxi
                for j in range(n_x)
            )  # for each input xj

        mid_m[i] = m2[i] - m1[i]

    return mid_m, dy_dm


def predict_gradients(
    midpoints,
    gradients_midpoints,
    x,
    n_m,
    n_x,
    show_plots=True,
    optimize_training=False,
):
    """
    Train MLP regression model with data normalization on gradients at
    midpoints to predict gradients at sample point.

    Setting random_state to an integer and shuffle to False, along with the
    fixed seeds in the import section at the top of this file, will ensure
    reproducible results each time the file is run. However, calling the model
    training multiple times on the same data in the same file run will produce
    different results due to randomness in the random_state instance that is
    generated. Therefore, the training is performed for a preset list of model
    settings and the best option is selected.
    """
    # split into X_train and X_test
    # always split into X_train, X_test first THEN apply minmax scaler
    print("Normalizing data...")
    X_train, X_test, y_train, y_test = train_test_split(
        midpoints,
        gradients_midpoints,
        test_size=0.2,
        random_state=42,  # for reproducibility
        shuffle=False,
    )  # for reproducibility
    print(X_train.shape, X_test.shape, y_train.shape, y_test.shape)

    # use minMax scaler
    print("Normalizing data...")
    min_max_scaler = MinMaxScaler()
    X_train = min_max_scaler.fit_transform(X_train)
    X_test = min_max_scaler.transform(X_test)

    print("Training gradient prediction model...")
    best_loss = 1e30  # insanely high value that will for sure be beaten
    best_model = None
    best_settings = None
    progress = 0

    if optimize_training:
        optimizers = ["Adam", "rmsprop"]
        activations = ["relu", "sigmoid"]
        act_outs = ["linear", "relu"]
        num_neurons = [6, 12]
        num_hidden_layers = [2, 8]
    else:
        optimizers = [
            "Adam",
        ]
        activations = [
            "relu",
        ]
        act_outs = [
            "linear",
        ]
        num_neurons = [
            6,
        ]
        num_hidden_layers = [
            2,
        ]

    for optimizer in optimizers:
        for activation in activations:
            for act_out in act_outs:
                for neuron in num_neurons:
                    for num_hidden_layer in num_hidden_layers:
                        progress += 1
                        if optimize_training:
                            print(
                                "Trying ",
                                optimizer,
                                "solver with ",
                                activation,
                                "on hidden nodes, ",
                                act_out,
                                "on output node with ",
                                neuron,
                                "neurons per node and ",
                                num_hidden_layer,
                                "hidden layers",
                            )
                        inputs = Input(
                            shape=X_train.shape[1]
                        )  # input node, layer for x1, x2, ...
                        h = Dense(neuron, activation=activation)(inputs)
                        for num in range(num_hidden_layer):
                            h = Dense(neuron, activation=activation)(h)
                        outputs = Dense(n_x, activation=act_out)(
                            h
                        )  # output node, layer for dy/dx1, dy/dx2, ...
                        model = Model(inputs=inputs, outputs=outputs)
                        # model.summary() # see what your model looks like

                        # compile the model
                        model.compile(optimizer=optimizer, loss="mse", metrics=["mae"])

                        # early stopping callback
                        es = EarlyStopping(
                            monitor="val_loss",
                            mode="min",
                            patience=50,
                            restore_best_weights=True,
                        )

                        # fit the model!
                        # attach it to a new variable called 'history' in case
                        # to look at the learning curves
                        history = model.fit(
                            X_train,
                            y_train,
                            validation_data=(X_test, y_test),
                            callbacks=[es],
                            epochs=100,
                            batch_size=50,
                            verbose=0,
                        )
                        if len(history.history["loss"]) == 100:
                            print("Successfully completed, 100 epochs run.")
                        else:
                            print(
                                "Validation loss stopped improving after ",
                                len(history.history["loss"]),
                                "epochs. Successfully completed after early stopping.",
                            )
                        print("Loss: ", sum(history.history["loss"]))
                        if optimize_training:
                            print("Progress: ", 100 * progress / 32, "%")

                        if sum(history.history["loss"]) < best_loss:
                            best_loss = sum(history.history["loss"])
                            best_model = model
                            best_history = history
                            best_settings = [
                                optimizer,
                                activation,
                                act_out,
                                neuron,
                                num_hidden_layer,
                            ]

    if optimize_training:
        print("The best settings are: ", best_settings)

    if show_plots:
        history_dict = best_history.history
        loss_values = history_dict["loss"]  # you can change this
        val_loss_values = history_dict["val_loss"]  # you can also change this
        epochs = range(1, len(loss_values) + 1)  # range of X (no. of epochs)
        plt.plot(epochs, loss_values, "bo", label="Training loss")
        plt.plot(epochs, val_loss_values, "orange", label="Validation loss")
        plt.title("Training and validation loss")
        plt.xlabel("Epochs")
        plt.ylabel("Loss")
        plt.legend()
        plt.show()

    gradients = best_model.predict(x)  # predict against original sample points

    return gradients


def generate_gradients(xy_data, n_x, show_plots=True, optimize_training=False,
                       use_simple_diff=False):
    """
    This method implements finite difference approximation and NN regression
    to estimate the first-order derivatives of a given dataset with columns
    (x1, x2, ...., xN, y1, y2, ..., yM) where N is the number of input
    variables and M is the number of output variables. The method takes an
    array of size (m, n_x + n_y) where m is the number of samples, n_x is the
    number of input variables, and n_y is the number of output variables. The
    method returns an array of size (m, n_x, n_y) where the first dimension
    spans samples, the second dimension spans gradients dy/dx for each x, and
    the third dimension spans gradients dy/dx for each y.

    For example, passing an array with 100 samples, 8 inputs and 2 outputs will
    return an array of size (100, 8, 2) where (:, :, 0) contains all dy1/dx and
    (:, :, 1) contains all dy2/dx.

    The workflow of this method is as follows:
        1. Import xy data in array of size (m, n_x + n_y) and split into x, y
        2. Generate dy in n_y arrays of size (m-1, n_x) which correspond to
        points between samples
        3. Normalize x, dy on [0, 1] and train MLP model dy(x) for each dy
        4. Predict dy(x) for m samples from xy data to generate n_y arrays of
        size (m, n_x) which correspond to sample points
        5. Concatenate predicted gradients into array of size (m, n_x, n_y)
    """

    # split data into inputs and outputs
    x = xy_data[:, :n_x]  # there are n_x input variables/columns
    y = xy_data[:, n_x:]  # the rest are output variables/columns
    n_y = np.shape(y)[1]  # save number of outputs
    n_m = np.shape(y)[0]  # save number of samples

    gradients = []  # empty list to hold gradient arrays for multiple outputs

    for output in range(n_y):
        print("Generating gradients for output ", output, ":")
        # estimate first-order gradients using finite difference approximation
        # this will account for all input variables, but will be for the midpoints
        # between the sample points, i.e. len(y) - len(dy_midpoints) = 1.
        # in both midpoints and gradients_midpoints, each column corresponds to an
        # input variable xi and each row corresponds to a point between two samples
        midpoints = np.empty((n_m - 1, n_x))
        gradients_midpoints = np.empty((n_m - 1, n_x))

        # get midpoint gradients for one pair of samples at a time and save
        for m in range(n_m - 1):  # we have (n_m - 1) adjacent sample pairs
            print("Midpoint gradient ", m + 1, " of ", n_m - 1, " generated.")
            midpoints[m], gradients_midpoints[m] = finite_difference(
                m1=x[m, :],
                m2=x[m + 1, :],
                y1=y[m][output],  # each entry in y is an array somehow
                y2=y[m + 1][output],  # each entry in y is an array somehow
                n_x=n_x,
                use_simple_diff=use_simple_diff,
            )
        print("Midpoint gradient generation complete.")
        print()

        # leverage NN regression to predict gradients at sample points
        gradients.append(
            predict_gradients(
                midpoints=midpoints,
                gradients_midpoints=gradients_midpoints,
                x=x,
                n_m=n_m,
                n_x=n_x,
                show_plots=show_plots,
                optimize_training=optimize_training,
            )
        )

    return gradients


if __name__ == "__main__":
    data = pd.read_csv(r"MEA_carbon_capture_dataset_mimo.csv")
    data_array = np.array(data, ndmin=2)
    n_x = 6

    gradients = generate_gradients(
        xy_data=data_array, n_x=n_x, show_plots=False, optimize_training=True, use_simple_diff=True,
    )
    print("Gradient generation complete.")

    for output in range(len(gradients)):
        pd.DataFrame(gradients[output]).to_csv(
            "gradients_output" + str(output) + ".csv"
        )
        print(
            "Gradients for output ",
            str(output),
            " written to gradients_output" + str(output) + ".csv",
        )
