#################################################################################
# FOQUS Copyright (c) 2012 - 2026, by the software owners: Oak Ridge Institute
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
from sklearn.neural_network import MLPRegressor
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
def create_model(x_train, z_train):

    mlp = MLPRegressor(
        solver="lbfgs",
        activation="relu",
        hidden_layer_sizes=[12] * 3,  # 3 hidden layers, each with 12 neurons
        max_iter=1000,
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


# Main code

# import data
data = pd.read_csv(r"../MEA_carbon_capture_dataset_mimo.csv")

xdata = data.iloc[:, :6]  # there are 6 input variables/columns
zdata = data.iloc[:, 6:]  # the rest are output variables/columns
xlabels = xdata.columns.tolist()  # set labels as a list (default) from pandas
zlabels = zdata.columns.tolist()  # is a set of IndexedDataSeries objects
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
)  # SciKit Learn requires a Numpy array as input

# define x and z data, not used but will add to variable dictionary
xdata = model_data[:, :-2]
zdata = model_data[:, -2:]

# create model
model = create_model(x_train=xdata, z_train=zdata)

with open("mea_column_model_customnormform_scikitlearn.pkl", "wb") as file:
    pickle.dump(model, file)

# load model as pickle format
with open("mea_column_model_customnormform_scikitlearn.pkl", "rb") as file:
    loaded_model = pickle.load(file)
