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
#
#################################################################################
import numpy as np
import pandas as pd
import random as rn
import torch
import torch.nn as nn

# set seed values for reproducibility
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
        **kwargs
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


class main_model(nn.Module):
    def __init__(self, input_features=6, hidden=20, out_features=2):
        super().__init__()
        self.linear = nn.Linear(input_features, hidden)
        self.relu = nn.ReLU(inplace=False)
        self.sigmoid = nn.Sigmoid()
        self.out = nn.Linear(hidden, out_features)
        self.custom = mea_column_model_customnormform_pytorch(
            input_labels=xlabels,
            output_labels=zlabels,
            input_bounds=xdata_bounds,
            output_bounds=zdata_bounds,
            normalized=True,
            normalization_form="Custom",
            normalization_function="(datavalue - dataminimum)/(datamaximum - dataminimum)",
        )

    def forward(self, x):
        x = self.linear(x)
        x = self.relu(x)
        x = self.out(x)
        x = self.custom(x)

        return x


# method to create model
def create_model(x_train, z_train):

    model = main_model(
        input_features=len(xlabels), hidden=20, out_features=len(zlabels)
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


# Main code

# import data
data = pd.read_csv(r"MEA_carbon_capture_dataset_mimo.csv")

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
)  # PyTorch requires a Numpy array as input

# define x and z data, not used but will add to variable dictionary
xdata = model_data[:, :-2]
zdata = model_data[:, -2:]

# create model
x_train = torch.from_numpy(xdata).float().to(device)
z_train = torch.from_numpy(zdata).float().to(device)
model = create_model(x_train=x_train, z_train=z_train)

print(model)

x = torch.tensor(xdata, dtype=torch.float)
zfit = model(x).detach().numpy()

# save model as PT format
model_scripted = torch.jit.script(model)
model_scripted.save("mea_column_model_customnormform_pytorch.pt")
