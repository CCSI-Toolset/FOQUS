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
import numpy as np
import pandas as pd
from smt.utils.neural_net.model import Model
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
def create_model(x_train, z_train, grad_train):

    # already have X, Y and J, don't need to create and populate GENN() to
    # load SMT data into Model(); GENN() doesn't support multiple outputs

    # Model() does support multiple outputs, so we just need to reshape the
    # arrays so that Model() can use them
    # we have x_train = (n_m, n_x), z_train = (n_m, n_y) and grad_train = (n_y, n_m, n_x)
    n_m, n_x = np.shape(x_train)
    _, n_y = np.shape(z_train)
    
    # check dimensions using grad_train
    assert np.shape(grad_train) == (n_y, n_m, n_x)
    
    # reshape arrays
    X = np.reshape(x_train, (n_x, n_m))
    Y = np.reshape(z_train, (n_y, n_m))
    J = np.reshape(grad_train, (n_y, n_x, n_m))
    
    # set up and train model

    # Train neural net
    model = Model.initialize(X.shape[0], Y.shape[0], deep=2, wide=6)  # 2 hidden layers with 6 neurons each
    model.train(
        X=X,  # input data
        Y=Y,  # output data
        J=J,  # gradient data
        num_iterations=25,  # number of optimizer iterations per mini-batch
        mini_batch_size=int(np.floor(n_m/5)), # used to divide data into training batches (use for large data sets)
        num_epochs=20,  # number of passes through data
        alpha=0.15,  # learning rate that controls optimizer step size
        beta1=0.99,  # tuning parameter to control ADAM optimization
        beta2=0.99,  # tuning parameter to control ADAM optimization
        lambd=0.1,  # lambd = 0. = no regularization, lambd > 0 = regularization
        gamma=0.0001,  # gamma = 0. = no grad-enhancement, gamma > 0 = grad-enhancement
        seed=None,  # set to value for reproducibility
        silent=True,  # set to True to suppress training output
    )

    model.custom = SimpleNamespace(
        input_labels=xlabels,
        output_labels=zlabels,
        input_bounds=xdata_bounds,
        output_bounds=zdata_bounds,
        normalized=False,  # SMT GENN models are normalized during training, this should always be False
    )

    return model

# Main code

# import data
data = pd.read_csv(r"MEA_carbon_capture_dataset_mimo.csv")
grad0_data = pd.read_csv(r"gradients_output0.csv", index_col=0)  # ignore 1st col
grad1_data = pd.read_csv(r"gradients_output1.csv", index_col=0)  # ignore 1st col

xdata = data.iloc[:, :6]  # there are 6 input variables/columns
zdata = data.iloc[:, 6:]  # the rest are output variables/columns
xlabels = xdata.columns.tolist()  # set labels as a list (default) from pandas
zlabels = zdata.columns.tolist()  # is a set of IndexedDataSeries objects
xdata_bounds = {i: (xdata[i].min(), xdata[i].max()) for i in xdata}  # x bounds
zdata_bounds = {j: (zdata[j].min(), zdata[j].max()) for j in zdata}  # z bounds

xmax, xmin = xdata.max(axis=0), xdata.min(axis=0)
zmax, zmin = zdata.max(axis=0), zdata.min(axis=0)
xdata, zdata = np.array(xdata), np.array(zdata) # (n_m, n_x) and (n_m, n_y)
gdata = np.stack([np.array(grad0_data), np.array(grad1_data)])  # (2, n_m, n_x)

model_data = np.concatenate(
    (xdata, zdata), axis=1
)  # Surrogate Modeling Toolbox requires a Numpy array as input

# define x and z data, not used but will add to variable dictionary
xdata = model_data[:, :-2]
zdata = model_data[:, -2:]

# create model
model = create_model(x_train=xdata, z_train=zdata, grad_train=gdata)

with open("mea_column_model_customnormform_smt.pkl", "wb") as file:
     pickle.dump(model, file)

# load model as pickle format
with open("mea_column_model_customnormform_smt.pkl", "rb") as file:
    loaded_model = pickle.load(file)
