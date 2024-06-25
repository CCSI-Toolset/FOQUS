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
import numpy as np
import pandas as pd

# from smt.utils.neural_net.model import Model
from jenn.model import NeuralNet
import pickle
from types import SimpleNamespace


# Example follows the sequence below:
# 1) Code at end of file to import data and create model
# 2) Call create_model() to define inputs and outputs
# 3) Call CustomLayer to define network structure, which uses
#    call() to define layer connections and get_config to attach
#    attributes to CustomLayer class object
# 4) Back to create_model() to compile and train model
# 5) Back to code at end of file to save, load and test model


# method to create model
def create_model(x_train, y_train, grad_train):

    n_m, n_x = np.shape(x_train)
    _, n_y = np.shape(y_train)

    # check dimensions using grad_train
    assert np.shape(grad_train) == (n_y, n_m, n_x)

    # reshape arrays
    X = np.reshape(x_train, (n_x, n_m))
    Y = np.reshape(y_train, (n_y, n_m))
    J = np.reshape(grad_train, (n_y, n_x, n_m))

    # set up and train model
    idx = 0
    best_SSE = [0, 1e100]
    best_model = None
    best_y_pred = None

    runs = 20000  # reduce number of runs to reduce runtime
    for i in range(runs):
        idx += 1

        hidden_layer_sizes = [6, 6]
        model = NeuralNet(
            [X.shape[0]] + hidden_layer_sizes + [Y.shape[0]],
            hidden_activation="relu",
            output_activation="linear",
        )
        model.parameters.initialize()

        model.fit(
            x=X,  # input data
            y=Y,  # output data
            dydx=J,  # gradient data
            is_normalize=False,
            alpha=0.500,  # learning rate that controls optimizer step size
            lambd=0.000,  # lambd = 0. = no regularization, lambd > 0 = regularization
            gamma=1.000,  # gamma = 0. = no grad-enhancement, gamma > 0 = grad-enhancement
            beta1=0.90,  # tuning parameter to control ADAM optimization
            beta2=0.99,  # tuning parameter to control ADAM optimization
            epochs=1,  # number of passes through data
            batch_size=None,  # used to divide data into training batches (use for large data sets)
            max_iter=200,  # number of optimizer iterations per mini-batch
            shuffle=True,
            random_state=None,
            is_backtracking=False,
            is_verbose=False,
        )

        y_pred = np.transpose(model.predict(np.transpose(x_train)))
        SSE = sum((y_pred - y_train) ** 2)

        # y0 is 2.1 orders of magnitude larger than y1, so adjust the SSE check
        # CO2 capture rate and SRD should both be positive for all predictions
        # SSE =  [75589.3371621  13214.64474031] from running 1000
        # SSE =  [39801.73811642  436.51381078] from running 20000
        if (SSE[0] / 21 + SSE[1]) < (best_SSE[0] / 21 + best_SSE[1]) and np.all(
            y_pred
        ) > 0:
            best_SSE = SSE
            best_model = model
            best_y_pred = y_pred

        print(np.round(idx / runs * 100, 3), " % complete")

    best_model.custom = SimpleNamespace(
        input_labels=xlabels,
        output_labels=zlabels,
        input_bounds=xdata_bounds,
        output_bounds=ydata_bounds,
        normalized=False,  # JENN models are normalized during training, this should always be False
    )

    return best_model, best_y_pred, best_SSE


# Main code

# import data
data = pd.read_csv(r"../MEA_carbon_capture_dataset_mimo.csv")
grad0_data = pd.read_csv(r"gradients_output0.csv", index_col=0)  # ignore 1st col
grad1_data = pd.read_csv(r"gradients_output1.csv", index_col=0)  # ignore 1st col

xdata = data.iloc[:, :6]  # there are 6 input variables/columns
ydata = data.iloc[:, 6:]  # the rest are output variables/columns
xlabels = xdata.columns.tolist()  # set labels as a list (default) from pandas
zlabels = ydata.columns.tolist()  # is a set of IndexedDataSeries objects
xdata_bounds = {i: (xdata[i].min(), xdata[i].max()) for i in xdata}  # x bounds
ydata_bounds = {j: (ydata[j].min(), ydata[j].max()) for j in ydata}  # y bounds

xmax, xmin = xdata.max(axis=0), xdata.min(axis=0)
ymax, ymin = ydata.max(axis=0), ydata.min(axis=0)
xdata, ydata = np.array(xdata), np.array(ydata)  # (n_m, n_x) and (n_m, n_y)
gdata = np.stack([np.array(grad0_data), np.array(grad1_data)])  # (2, n_m, n_x)

model_data = np.concatenate(
    (xdata, ydata), axis=1
)  # JENN requires a Numpy array as input

# define x and y data, not used but will add to variable dictionary
xdata = model_data[:, :-2]
ydata = model_data[:, -2:]

# create model
model, y_pred, SSE = create_model(x_train=xdata, y_train=ydata, grad_train=gdata)

with open("mea_column_model_jenn.pkl", "wb") as file:
    pickle.dump(model, file)

# load model as pickle format
with open("mea_column_model_jenn.pkl", "rb") as file:
    loaded_model = pickle.load(file)


print(y_pred)
print("SSE = ", SSE)
