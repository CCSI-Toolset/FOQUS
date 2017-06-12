# drm_container.py
from math import sqrt, fabs
from dabnet import DABNet
from narma import NARMA
from unscented_kalman_filter import UnscentedKalmanFilter
import numpy as np


class DRMContainer(object):
    def __init__(self):
        self.bdabnet = False
        self.bnarma = False
        self.ninput = 1
        self.noutput = 1
        self.mean_in = []
        self.sigma_in = []
        self.mean_out = []
        self.sigma_out = []
        self.mean_state = []        # only for DABNet model
        self.sigma_state = []       # only for DABNet model
        self.drm_dabnet = None
        self.drm_narma = None

    def set_from_tuple(self, dat):
        imodel_type = dat[0]
        drm = dat[1]
        self.ninput = drm[0]
        self.noutput = drm[1]
        self.mean_in = [None]*self.ninput
        self.sigma_in = [None]*self.ninput
        self.mean_out = [None]*self.noutput
        self.sigma_out = [None]*self.noutput
        for i in xrange(self.ninput):
            self.mean_in[i] = drm[2][i]
            self.sigma_in[i] = drm[3][i]
        for i in xrange(self.noutput):
            self.mean_out[i] = drm[4][i]
            self.sigma_out[i] = drm[5][i]
        if imodel_type == 1:
            self.drm_narma = NARMA()
            self.drm_narma.set_from_tuple(drm[6])
        else:
            dabnet_list = drm[6]
            self.drm_dabnet = [None]*self.noutput
            for i in xrange(self.noutput):
                self.drm_dabnet[i] = DABNet()
                self.drm_dabnet[i].set_from_tuple(dabnet_list[i])
            nstate_red = len(drm[7])
            self.mean_state = [None]*nstate_red
            self.sigma_state = [None]*nstate_red
            for i in xrange(nstate_red):
                self.mean_state[i] = drm[7][i]
                self.sigma_state[i] = drm[8][i]
        if imodel_type == 1:
            self.bnarma = True
        else:
            self.bdabnet = True

    def to_dictionary(self):
        dict_data = dict()
        dict_data['bdabnet'] = self.bdabnet
        dict_data['bnarma'] = self.bnarma
        dict_data['ninput'] = self.ninput
        dict_data['noutput'] = self.noutput
        # mean and sigma should have been assigned
        dict_data['mean_in'] = self.mean_in
        dict_data['sigma_in'] = self.sigma_in
        dict_data['mean_out'] = self.mean_out
        dict_data['sigma_out'] = self.sigma_out
        if self.bdabnet:
            dabnet_list = [None]*self.noutput
            for i in xrange(self.noutput):
                dabnet_list[i] = self.drm_dabnet[i].to_dictionary()
            dict_data['drm_dabnet'] = dabnet_list
            dict_data['mean_state'] = self.mean_state
            dict_data['sigma_state'] = self.sigma_state
        if self.bnarma:
            dict_data['drm_narma'] = self.drm_narma.to_dictionary()
        return dict_data

    def from_dictionary(self, dict_data):
        self.bdabnet = dict_data['bdabnet']
        self.bnarma = dict_data['bnarma']
        self.ninput = dict_data['ninput']
        self.noutput = dict_data['noutput']
        self.mean_in = dict_data['mean_in']
        self.sigma_in = dict_data['sigma_in']
        self.mean_out = dict_data['mean_out']
        self.sigma_out = dict_data['sigma_out']
        if self.bdabnet:
            self.drm_dabnet = [None]*self.noutput
            for i in xrange(self.noutput):
                self.drm_dabnet[i] = DABNet()
                self.drm_dabnet[i].from_dictionary(dict_data['drm_dabnet'][i])
            self.mean_state = dict_data['mean_state']
            self.sigma_state = dict_data['sigma_state']
        if self.bnarma:
            self.drm_narma = NARMA()
            self.drm_narma.from_dictionary(dict_data['drm_narma'])

    def write_to_matlab_file(self, imodel_type, fout):
        line = "nu = {};\n".format(self.ninput)
        fout.write(line)
        line = "ny = {};\n".format(self.noutput)
        fout.write(line)
        for i in xrange(self.ninput):
            line = "u_mean({0}) = {1};\n".format(i+1,self.mean_in[i])
            fout.write(line)
        for i in xrange(self.noutput):
            line = "y_mean({0}) = {1};\n".format(i+1,self.mean_out[i])
            fout.write(line)
        for i in xrange(self.ninput):
            line = "u_sigma({0}) = {1};\n".format(i+1,self.sigma_in[i])
            fout.write(line)
        for i in xrange(self.noutput):
            line = "y_sigma({0}) = {1};\n".format(i+1,self.sigma_out[i])
            fout.write(line)
        if imodel_type == 0:
            for i in xrange(self.noutput):
                self.drm_dabnet[i].write_to_matlab_file(fout)
        else:
            self.drm_narma.write_to_matlab_file(fout)

    def predict_dabnet(self, varied_data, ipredict_opt):
        # varied_data could contain input only or both input and output
        # ipredict_opt: 0 for Laguerre model, 1 for reduced model
        # return the list of list of size [nouput][npair]
        npair = len(varied_data[0])
        # first convert varied_data from the list of list to numpy array
        arr_varied_data = np.array(varied_data)
        t_varied_data = arr_varied_data.transpose()
        # scale input data first
        dim_input = (npair, self.ninput)
        scaled_input = np.zeros(dim_input)
        for i in xrange(npair):
            for j in xrange(self.ninput):
                scaled_input[i][j] = (t_varied_data[i][j] - self.mean_in[j])/self.sigma_in[j]
        y = [None]*self.noutput
        for i in xrange(self.noutput):
            y[i] = self.drm_dabnet[i].predict(scaled_input, ipredict_opt)
        # unscale the output
        for i in xrange(self.noutput):
            for j in xrange(npair):
                y[i][j] = y[i][j]*self.sigma_out[i] + self.mean_out[i]
        return y

    def predict_narma(self, varied_data, ipredict_opt):
        # varied_data: if ipredict_opt==0, it must contain output data; otherwise it must contain initial output data
        # ipredict_opt: 0=using ACM history data, 1=using accumulated prediction data as history
        # return the list of list of size [nouput][npair]
        npair = len(varied_data[0])
        # first convert varied_data from the list of list to numpy np.array
        arr_varied_data = np.array(varied_data)
        t_varied_data = arr_varied_data.transpose()
        # scale input and output data first
        dim_input = (npair, self.ninput+self.noutput)
        scaled_input = np.zeros(dim_input)
        for i in xrange(npair):
            for j in xrange(self.ninput):
                scaled_input[i][j] = (t_varied_data[i][j] - self.mean_in[j])/self.sigma_in[j]
            for j in xrange(self.noutput):
                scaled_input[i][self.ninput + j] = (t_varied_data[i][self.ninput + j] - self.mean_out[j])/self.sigma_out[j]
        y = self.drm_narma.predict(scaled_input, ipredict_opt)
        # unscale the output
        for i in xrange(self.noutput):
            for j in xrange(npair):
                y[i][j] = y[i][j]*self.sigma_out[i] + self.mean_out[i]
        return y

    def perform_uq_analysis(self, varied_data, uq_input):
        # use the validation data to perform UQ analysis based on Unscented Kalman Filter (UKF)
        # this is for DABNet reduced model only assuming bdabnet is True
        # varied_data is the acm validation varied input and varied output
        # prepare scaled data
        npair = len(varied_data[0])
        # first convert varied_data from the list of list to numpy array
        arr_varied_data = np.array(varied_data)
        t_varied_data = arr_varied_data.transpose()
        # scale input data
        u = np.zeros((npair, self.ninput))
        for i in xrange(npair):
            for j in xrange(self.ninput):
                u[i][j] = (t_varied_data[i][j] - self.mean_in[j])/self.sigma_in[j]
        # do not scale output data
        y_acm = np.zeros((npair, self.noutput))
        for i in xrange(npair):
            for j in xrange(self.noutput):
                y_acm[i][j] = t_varied_data[i][self.ninput+j]
        # calculate the total number of state based on the reduced model
        nstate_red = 0
        for i in xrange(self.noutput):
            nstate_red += self.drm_dabnet[i].ann_red.ninput
        # set non-zero flag for the P matrix to avoid non-definite-positiveness
        non_zero = np.zeros((nstate_red, nstate_red),np.int8)
        n = 0
        #for i in xrange(self.noutput):
        #    nstate_i = self.drm_dabnet[i].ann_red.ninput
        #    for j in xrange(nstate_i):
        #        for k in xrange(nstate_i):
        #            non_zero[n+j][n+k] = 1
        #    n += nstate_i
        for i in xrange(self.noutput):
            for j in xrange(self.ninput):
                nstate_ij = self.drm_dabnet[i].state_space_red[j].nstate
                for k in xrange(nstate_ij):
                    for l in xrange(nstate_ij):
                        non_zero[n+k][n+l] = 1
                n += nstate_ij
        # calculate initial state variables
        u0 = u[0]
        x0 = np.zeros(nstate_red)
        p0 = np.zeros((nstate_red, nstate_red))
        # initialize state and output variables assuming steady state
        n = 0
        for i in xrange(self.noutput):
            xi = self.drm_dabnet[i].get_initial_state_variables(u0, 1)
            ni = len(xi)
            for j in xrange(ni):
                x0[n] = xi[j]
                n += 1
        q = np.zeros((nstate_red, nstate_red))
        r = np.zeros((self.noutput, self.noutput))
        # use standard deviation of state variables from training sequence to define the process noise (Q matrix)
        # also hard-wired the initial P matrix as diagonal matrix with (0.001*std)^2 as variance
        for i in xrange(nstate_red):
            diag = uq_input.fq_state*self.sigma_state[i]
            q[i][i] = diag*diag
            diag = 0.001*self.sigma_state[i]
            p0[i][i] = diag*diag
        # use standard deviation of output variables from training sequence to define measurement noise (R matrix)
        for i in xrange(self.noutput):
            diag = uq_input.fr_output[i]*self.sigma_out[i]
            r[i][i] = diag*diag
        ukf = UnscentedKalmanFilter()
        ukf.set_noise_matrices(q,r)
        ukf.set_drm_and_output_scale_parameters(self.drm_dabnet, self.mean_out, self.sigma_out)
        ukf.set_default_ut_parameters()
        xk = x0
        Pk = np.matrix(p0)
        y_obs = np.zeros((npair, self.noutput))
        y_ukf = np.zeros((npair, self.noutput))
        y_std = np.zeros((npair, self.noutput))
        for j in xrange(self.noutput):
            y_obs[0][j] = y_acm[0][j]
            y_ukf[0][j] = y_acm[0][j]
            y_std[0][j] = fabs(self.sigma_out[j]*uq_input.fr_output[j])
        # starting the iteration loop
        for k in xrange(1,npair):
            x_predict, P_predict = ukf.predict(xk, Pk, u[k-1])
            for j in xrange(self.noutput):
                y_obs[k][j] = y_acm[k][j] + np.random.normal()*uq_input.fr_output[j]*self.sigma_out[j]
            mu, S_update, x_update, P_update = ukf.update(x_predict, P_predict, y_obs[k])
            # set certain off-diagonal terms of P_update to zero for independent states
            for i in xrange(nstate_red):
                for j in xrange(nstate_red):
                    if non_zero[i][j]==0:
                        P_update[i,j] = 0.0
            for j in xrange(self.noutput):
                y_ukf[k][j] = mu[j]
                y_std[k][j] = sqrt(S_update[j,j])
            xk = x_update
            Pk = P_update
        # prepare the output as list
        yobs = [None]*self.noutput
        yukf = [None]*self.noutput
        ystd = [None]*self.noutput
        for j in xrange(self.noutput):
            yobs[j] = [None]*npair
            yukf[j] = [None]*npair
            ystd[j] = [None]*npair
        for k in xrange(npair):
            for j in xrange(self.noutput):
                yobs[j][k] = y_obs[k][j]
                yukf[j][k] = y_ukf[k][j]
                ystd[j][k] = y_std[k][j]
        return (yobs, yukf, ystd, P_update, S_update)


