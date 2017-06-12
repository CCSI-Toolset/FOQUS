# state_space.py
import numpy as np


class StateSpace(object):
    def __init__(self):
        self.nstate = 1
        self.x = None
        self.mA = None
        self.mB = None

    def to_dictionary(self):
        dict_data = dict()
        dict_data['nstate'] = self.nstate
        x_list = [None]*self.nstate
        for i in xrange(self.nstate):
            x_list[i] = self.x[i][0]
        dict_data['x'] = x_list
        mA_list = [None]*self.nstate*self.nstate
        for i in xrange(self.nstate):
            for j in xrange(self.nstate):
                mA_list[i*self.nstate + j] = self.mA[i][j]
        dict_data['mA'] = mA_list
        mB_list = [None]*self.nstate
        for i in xrange(self.nstate):
            mB_list[i] = self.mB[i][0]
        dict_data['mB'] = mB_list
        return dict_data

    def from_dictionary(self, dict_data):
        self.nstate = dict_data['nstate']
        dim_mB = (self.nstate,1)
        dim_mA = (self.nstate, self.nstate)
        self.x = np.zeros(dim_mB)
        self.mA = np.zeros(dim_mA)
        self.mB = np.zeros(dim_mB)
        for i in xrange(self.nstate):
            self.x[i][0] = dict_data['x'][i]
        for i in xrange(self.nstate):
            for j in xrange(self.nstate):
                self.mA[i][j] = dict_data['mA'][i*self.nstate + j]
        for i in xrange(self.nstate):
            self.mB[i][0] = dict_data['mB'][i]

    def set_from_tuple(self, dat):
        self.nstate = dat[0]
        dim_mB = (self.nstate,1)
        dim_mA = (self.nstate, self.nstate)
        self.x = np.zeros(dim_mB)
        self.mA = np.zeros(dim_mA)
        self.mB = np.zeros(dim_mB)
        k = 1
        for i in xrange(self.nstate):
            for j in xrange(self.nstate):
                self.mA[i][j] = dat[k]
                k += 1
        for i in xrange(self.nstate):
            self.mB[i][0] = dat[k]
            k += 1

    def init_state_vector_to_steady_state(self, u0):
        # u0 is a scalar input
        # obtain steady-state state vector by solving (A-I)x = -Bu, assuming converging A,B matrices
        mI = np.eye(self.nstate)
        mA_I = self.mA - mI
        m_Bu = (-u0)*self.mB
        self.x = np.linalg.solve(mA_I, m_Bu)

    def calc_next_state_vector(self, u):
        # u is a scalar input
        x_next = self.mA.dot(self.x) + u*self.mB
        self.x = x_next
