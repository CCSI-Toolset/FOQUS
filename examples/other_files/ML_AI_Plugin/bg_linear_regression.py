import numpy as np
import matplotlib.pyplot as plt  # To visualize
import pandas as pd  # To read data
from sklearn.linear_model import LinearRegression
from pyomo.common.fileutils import this_file_dir
import os

def get_data(file,y_values):
    data = pd.read_csv(file, sep=';', header=None)  # load data set
    X = data.iloc[:, :data.shape[1]-y_values]
    Y = data.iloc[:, data.shape[1]-y_values]
    return X,Y


def main(file,y_values):
    X,Y = get_data(file,y_values)

    from sklearn import linear_model

    regr = linear_model.LinearRegression()
    regr.fit(X, Y)
    print('Regression Coefficients')
    print(regr.coef_)
    with open('derivatives.csv', 'w') as f:
        for index in range(X.shape[0]):
            print(index)
            for i in range(len(regr.coef_)):
                f.write(str(regr.coef_[i]))
                if i == len(regr.coef_) - 1:
                    f.write('\n')
                else:
                    f.write(';')
    f.close()

file = os.path.join(this_file_dir(), 'cd_x_y.csv')
y_values = 1
main(file,y_values)