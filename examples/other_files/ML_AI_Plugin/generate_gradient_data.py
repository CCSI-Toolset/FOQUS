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
    """
    Calculate the first-order gradient between provided sample points m1 and 
    m2, where each point is assumed to be a vector with one or more input 
    variables x and exactly one output variable y. y1 is the value of y1 at m1,
    and y2 is the value of y at m2.
    
    The total graident is calculated via chain rule assuming a multivariate 
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
    """
    This method implements finite difference approximation and MLP regression 
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
    n_m = np.shape(y)[0]  # save number of samples

    # estimate first-order gradients using finite difference approximation
    # this will account for all input variables, but will be for the midpoints
    # between the sample points, i.e. len(y) - len(dy_midpoints) = 1.
    # in both midpoints and gradients_midpoints, each column corresponds to an
    # input variable xi and each row corresponds to a point between two samples
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