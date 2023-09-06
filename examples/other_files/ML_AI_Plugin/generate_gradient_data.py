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
from sklearn.neural_network import MLPRegressor
import pickle
from types import SimpleNamespace

def finite_difference(m1, m2, y1, y2, n_x):

    def diff(y2, y1, x2, x1):
        dv2_dv1 = (y2 - y1)/(x2 - x1)

        return dv2_dv1

    mid_m = [None] * n_x  # initialize dm vector, the midpoints of m1 and m2
    dy_dm = [None] * n_x  # initialize dy vector, this is dy_dm(midpoints)

    for i in range(n_x):  # for each input xi
        dy_dm[i] = sum(
            diff(y2, y1, m2[j], m1[j]) *  # dy/dxj
            diff(m2[j], m1[j], m2[i], m1[i])  # dxj/dxi
            for j in range(n_x)
            )  # for each input xj

        mid_m[i] = m2[i] - m1[i]

    return mid_m, dy_dm

def generate_gradients(xy_data, n_x):

    # split data into inputs and outputs
    x = xy_data[:, :n_x]  # there are n_x input variables/columns
    y = xy_data[:, n_x:]  # the rest are output variables/columns
    n_m = np.shape(y)[0]  # save number of samples

    # estimate first-order gradients using finite difference approximation

    midpoints = np.empty((n_m-1, n_x))
    gradients_midpoints = np.empty((n_m-1, n_x))

    # get midpoint gradients for one pair of samples at a time and save
    for m in range(n_m-1):  # we have (n_m - 1) adjacent sample pairs
        print(m+1, " of ", n_m-1)
        midpoints[m], gradients_midpoints[m] = finite_difference(
            m1 = x[m,:],
            m2 = x[m+1,:],
            y1 = y[m][0],  # each entry in y is an array somehow
            y2 = y[m+1][0],  # each entry in y is an array somehow
            n_x = n_x
            )

    return midpoints, gradients_midpoints

if __name__ == "__main__":
    data = pd.read_csv(r"MEA_carbon_capture_dataset_mimo.csv")
    data_array = np.array(data, ndmin=2)
    data_array = data_array[:, :-1]  # take only one output column
    n_x = 6

    midpoints, gradients = generate_gradients(xy_data=data_array, n_x=n_x)
    print("Gradient generation complete.")