# unscented_transform.py
from math import sqrt
import numpy as np


class UnscentedTransform(object):
    def __init__(self):
        self.nx = 2
        self.ny = 2
        self.npoint = 2*self.nx + 1
        self.alpha = 1.0
        self.beta = 0.0
        self.kappa = 1.0
        self.lamda = 1.0
        self.c_sqrt = 1.0
        self.weight_m = None
        self.weight_c = None

    def set_dimension_and_parameters(self, nx, ny, a=1.0, b=0.0):
        self.nx = nx
        self.ny = ny
        self.npoint = 2*self.nx + 1
        self.alpha = a
        self.beta = b
        self.kappa = 3.0 - self.nx
        self.lamda = self.alpha*self.alpha*(self.nx + self.kappa) - self.nx
        self.c_sqrt = sqrt(self.nx + self.lamda)
        # calculate weights
        self.weight_m = np.zeros(self.npoint)
        self.weight_c = np.zeros(self.npoint)
        self.weight_m[0] = self.lamda/(self.nx + self.lamda)
        self.weight_c[0] = self.weight_m[0] + 1.0 - self.alpha*self.alpha + self.beta
        for i in xrange(1, self.npoint):
            self.weight_m[i] = 1.0/2.0/(self.nx + self.lamda)
            self.weight_c[i] = self.weight_m[i]

    def transform(self, m, P, gfunc, *param):
        # m: 1-D vector of [nx]
        # P: 2-D matrix of [nx, nx]
        # gfunc: g() function
        # *param: additional parameters of g() besides sigma point vector. e.g. u
        # returns:
        # 1. mean of y as numpy 1-D array
        # 2. covariance matrix of y as numpy matrix
        # 3. cross-covariance of x and y as numpy matrix
        # first do chelosky decompostion to get P_half as a lower triangular matrix
        P_half = np.linalg.cholesky(P)
        x_sigma = np.zeros((self.npoint, self.nx))
        for j in xrange(self.nx):
            x_sigma[0][j] = m[j]
        for i in xrange(self.nx):
            for j in xrange(self.nx):
                # add column vector of P_half
                x_sigma[i+1][j] = m[j] + self.c_sqrt*P_half[j,i]
                x_sigma[i+1+self.nx][j] = m[j] - self.c_sqrt*P_half[j,i]
        y_sigma = np.zeros((self.npoint, self.ny))
        # call non-linear function g()
        for i in xrange(self.npoint):
            y = gfunc(x_sigma[i], *param)
            for j in xrange(self.ny):
                y_sigma[i][j] = y[j]
        # calculate mean
        y_mean = np.zeros(self.ny)
        for i in xrange(self.npoint):
            for j in xrange(self.ny):
                y_mean[j] += y_sigma[i][j]*self.weight_m[i]
        # calculate covariance of y
        dy = np.zeros(self.ny)
        y_cov = np.zeros((self.ny, self.ny))
        y_cov_mx = np.matrix(y_cov)
        for i in xrange(self.npoint):
            for j in xrange(self.ny):
                dy[j] = y_sigma[i][j] - y_mean[j]
            dy_mx = np.matrix(dy)
            dy_mx_t = dy_mx.T
            y_cov_mx += self.weight_c[i]*dy_mx_t*dy_mx
        # calculate cross covariance of x and y
        dx = np.zeros(self.nx)
        cross_cov = np.zeros((self.nx, self.ny))
        cross_cov_mx = np.matrix(cross_cov)
        for i in xrange(self.npoint):
            for j in xrange(self.ny):
                dy[j] = y_sigma[i][j] - y_mean[j]
            for j in xrange(self.nx):
                dx[j] = x_sigma[i][j] - m[j]
            dx_mx = np.matrix(dx)
            dx_mx_t = dx_mx.T
            dy_mx = np.matrix(dy)
            cross_cov_mx += self.weight_c[i]*dx_mx_t*dy_mx
        return (y_mean, y_cov_mx, cross_cov_mx)




