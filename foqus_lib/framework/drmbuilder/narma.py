# narma.py
from numpy import *
from neural_network import NeuralNetwork

class NARMA(object):
    def __init__(self):
        self.ninput = 1
        self.noutput = 1
        self.nhistory = 2
        self.ann = NeuralNetwork()

    def set_from_tuple(self, dat):
        self.ninput = dat[0]
        self.noutput = dat[1]
        self.nhistory = dat[2]
        self.ann.set_from_tuple(dat[3])

    def to_dictionary(self):
        dict_data = dict()
        dict_data['ninput'] = self.ninput
        dict_data['noutput'] = self.noutput
        dict_data['nhistory'] = self.nhistory
        dict_data['ann'] = self.ann.to_dictionary()
        return dict_data

    def from_dictionary(self, dict_data):
        self.ninput = dict_data['ninput']
        self.noutput = dict_data['noutput']
        self.nhistory = dict_data['nhistory']
        self.ann.from_dictionary(dict_data['ann'])

    def write_to_matlab_file(self, fout):
        line = "nhistory = {0};\n".format(self.nhistory)
        fout.write(line)
        self.ann.write_to_matlab_file(fout)

    def predict(self, u, ipredict_opt):
        # ipredict_opt: 0=use high-fidelity model history, 1=accumulated
        # u: scaled input data, numpy array of [npair][ninput+output], at least [0][ninput+noutput] is given for ipredict==1
        # y: returned scaled output as list of list [noutput][npair]
        npair = u.shape[0]
        y_arr = zeros((npair,self.noutput))     # NARMA prediction array
        ann_input = [None]*self.nhistory*(self.ninput+self.noutput)
        if ipredict_opt == 1:       # use accumulated history data, assign as steady-state data from u
            for j in xrange(self.noutput):
                y_arr[0][j] = u[0][self.ninput+j]
        for i in xrange(npair):
            n = 0
            for j in xrange(self.ninput):
                for k in xrange(self.nhistory):
                    m = i - self.nhistory + k
                    if m < 0:
                        m = 0
                    ann_input[n] = u[m][j]
                    n += 1
            if ipredict_opt == 1:       # use NARMA predicted data as history data
                for j in xrange(self.noutput):
                    for k in xrange(self.nhistory):
                        m = i - self.nhistory + k
                        if m < 0:
                            m = 0
                        ann_input[n] = y_arr[m][j]
                        n += 1
            else:
                for j in xrange(self.noutput):
                    for k in xrange(self.nhistory):
                        m = i - self.nhistory + k
                        if m < 0:
                            m = 0
                        ann_input[n] = u[m][self.ninput+j]
                        n += 1
            yrow = self.ann.predict(ann_input, 0, 0)    # does not scale input and output data within ANN
            for j in xrange(self.noutput):
                y_arr[i][j] = yrow[j]
        # convert to y as list of list
        y = [None]*self.noutput
        for i in xrange(self.noutput):
            y[i] = [None]*npair
            for j in xrange(npair):
                y[i][j] = y_arr[j][i]
        return y