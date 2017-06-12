import numpy as np
from unscented_transform import UnscentedTransform


class UnscentedKalmanFilter(object):
    def __init__(self):
        self.nx = 1             # number of total state variables
        self.ny = 1             # number of output variables
        self.Q = None           # noise matrix of state variables
        self.R = None           # noise matrix of output variables
        self.drm = None         # D-RM model (reduced DABNet list)
        self.mean_out = None    # mean of output variables
        self.sigma_out = None   # std of output variables
        self.ut_predict = UnscentedTransform()
        self.ut_update = UnscentedTransform()

    def set_noise_matrices(self, q, r):
        # q is numpy array of process noise
        # r is numpy array of output (measurement) noise
        self.Q = np.matrix(q)
        self.R = np.matrix(r)
        self.nx = q.shape[0]
        self.ny = r.shape[0]

    def set_drm_and_output_scale_parameters(self, drm_dabnet, mean, sigma):
        # use the reduced DABNet model for UKF
        self.drm = drm_dabnet
        self.mean_out = mean
        self.sigma_out = sigma

    def set_default_ut_parameters(self):
        # used default UT parameters through default function parameters
        self.ut_predict.set_dimension_and_parameters(self.nx, self.nx)
        self.ut_update.set_dimension_and_parameters(self.nx, self.ny)

    def set_reduced_drm_state_vector(self, x):
        # x is the state vector for all outputs as numpy 1-D array
        n = 0
        for i in xrange(self.ny):
            for j in xrange(self.drm[i].ninput):
                for k in xrange(self.drm[i].state_space_red[j].nstate):
                    self.drm[i].state_space_red[j].x[k][0] = x[n]
                    n += 1

    def get_reduced_drm_state_vector(self):
        # get the current state vector
        x = np.zeros(self.nx)
        n = 0
        for i in xrange(self.ny):
            for j in xrange(self.drm[i].ninput):
                for k in xrange(self.drm[i].state_space_red[j].nstate):
                    x[n] = self.drm[i].state_space_red[j].x[k][0]
                    n += 1
        return x

    def calc_next_state(self, x, *param):
        # use the given current state vector and current input vector to calculate the state vector of next step
        # x is the current state vector
        # param[0] is the u
        # returns state vector of next step
        u = param[0]
        self.set_reduced_drm_state_vector(x)
        for i in xrange(self.ny):
            self.drm[i].calc_next_state(u)
        x_next = self.get_reduced_drm_state_vector()
        return x_next

    def calc_output(self, x, *param):
        # x is the state vector
        # *param is None
        # returns the output vector
        self.set_reduced_drm_state_vector(x)
        y = np.zeros(self.ny)
        for i in xrange(self.ny):
            y[i] = self.drm[i].calc_output_from_current_state()*self.sigma_out[i] + self.mean_out[i]
        return y

    def predict(self, x, P, u):
        # x is the current state vector as numpy 1-D array
        # P is the current covariance matrix of the state variables as numpy matrix
        # u is the input vector as numpy 1-D array
        # returns predicted state vector of next step and its variance
        param = (u,)
        x_predict, P_predict, C = self.ut_predict.transform(x, P, self.calc_next_state, *param)
        P_predict += self.Q
        # cross-variance is calculated by UT but not needed
        return (x_predict, P_predict)


    def update(self, x, P, y):
        # x is the mean of the sigma points of the predicted state vector as numpy 1-D array
        # P is the predicted covariance plus process noise as numpy matrix
        # y is the output vector with measurement noise added as numpy 1-D array
        # returns mean output vector, its covariance matrix, updated state vector and its covariance matrix
        param = (None,)
        # call UT to calculate y mean of sigma points mu, covariance of measurement S and cross-variance C of x and y
        mu, S, C = self.ut_update.transform(x, P, self.calc_output, *param)
        S += self.R
        # calculate Kalman filter gain K
        K = C*S.I
        # update state vector and its covariance, not sure if
        dy = y - mu
        dy_mx = np.matrix(dy)
        x_mx = np.matrix(x)
        x_update_mx = x_mx.T + K*dy_mx.T
        x_update_arr = np.array(x_update_mx.T)
        x_update = x_update_arr[0]
        P_update = P - K*S*K.T
        # make sure P_update is positive finite
        return (mu, S, x_update, P_update)
