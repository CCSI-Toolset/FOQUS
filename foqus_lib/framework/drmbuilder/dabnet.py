# dabnet.py

from state_space import StateSpace
from neural_network import NeuralNetwork


class DABNet(object):
    def __init__(self):
        self.ninput = 1
        self.noutput = 1        # should be always 1
        self.ioutput = 0        # index of output, currently not used
        self.state_space_lag = None
        self.state_space_red = None
        self.ann_lag = NeuralNetwork()
        self.ann_red = NeuralNetwork()

    def to_dictionary(self):
        dict_data = dict()
        dict_data['ninput'] = self.ninput
        dict_data['noutput'] = self.noutput
        dict_data['ioutput'] = self.ioutput
        list_lag = [None]*self.ninput
        for i in xrange(self.ninput):
            list_lag[i] = self.state_space_lag[i].to_dictionary()
        dict_data['state_space_lag'] = list_lag
        list_red = [None]*self.ninput
        for i in xrange(self.ninput):
            list_red[i] = self.state_space_red[i].to_dictionary()
        dict_data['state_space_red'] = list_red
        dict_data['ann_lag'] = self.ann_lag.to_dictionary()
        dict_data['ann_red'] = self.ann_red.to_dictionary()
        return dict_data

    def from_dictionary(self, dict_data):
        self.ninput = dict_data['ninput']
        self.noutput = dict_data['noutput']
        self.ioutput = dict_data['ioutput']
        self.state_space_lag = [None]*self.ninput
        for i in xrange(self.ninput):
            self.state_space_lag[i] = StateSpace()
            self.state_space_lag[i].from_dictionary(dict_data['state_space_lag'][i])
        self.state_space_red = [None]*self.ninput
        for i in xrange(self.ninput):
            self.state_space_red[i] = StateSpace()
            self.state_space_red[i].from_dictionary(dict_data['state_space_red'][i])
        self.ann_lag.from_dictionary(dict_data['ann_lag'])
        self.ann_red.from_dictionary(dict_data['ann_red'])

    def set_from_tuple(self, dat):
        self.ninput = dat[0]
        self.noutput = dat[1]
        self.ioutput = dat[2]
        self.state_space_lag = [None]*self.ninput
        self.state_space_red = [None]*self.ninput
        for i in xrange(self.ninput):
            self.state_space_lag[i] = StateSpace()
            self.state_space_lag[i].set_from_tuple(dat[3][i])
            self.state_space_red[i] = StateSpace()
            self.state_space_red[i].set_from_tuple(dat[5][i])
        self.ann_lag.set_from_tuple(dat[4])
        self.ann_red.set_from_tuple(dat[6])

    def write_to_matlab_file(self, fout, ipredict_opt_dabnet=1):
        # ipredict_opt_dabnet: 0 for Laguerre model, 1 for reduced model
        ioutput1 = self.ioutput + 1
        if ipredict_opt_dabnet == 1:    # reduced model
            for i in xrange(self.ninput):
                nstate = self.state_space_red[i].nstate
                line = "A{0}{1},{2}{3} = [".format('{', ioutput1, i+1, '}')
                fout.write(line)
                for j in xrange(nstate):
                    for k in xrange(nstate):
                        line = "{0} ".format(self.state_space_red[i].mA[j][k])
                        fout.write(line)
                    fout.write("\n")
                fout.write("];\n")
                line = "B{0}{1},{2}{3} = [".format('{', ioutput1, i+1, '}')
                fout.write(line)
                for j in xrange(nstate):
                    line = "{0} ".format(self.state_space_red[i].mB[j][0])
                    fout.write(line)
                fout.write("]\';\n")
            self.ann_red.write_to_matlab_file(fout, self.ioutput)
        else:   # Laguerre model
            for i in xrange(self.ninput):
                nstate = self.state_space_lag[i].nstate
                line = "A{0}{1},{2}{3} = [".format('{', ioutput1, i+1, '}')
                fout.write(line)
                for j in xrange(nstate):
                    for k in xrange(nstate):
                        line = "{0} ".format(self.state_space_lag[i].mA[j][k])
                        fout.write(line)
                    fout.write("\n")
                fout.write("];\n")
                line = "B{0}{1},{2}{3} = [".format('{', ioutput1, i+1, '}')
                fout.write(line)
                for j in xrange(nstate):
                    line = "{0} ".format(self.state_space_lag[i].mB[j][0])
                    fout.write(line)
                fout.write("]\';\n")
            self.ann_lag.write_to_matlab_file(fout, self.ioutput)

    def get_initial_state_variables(self, u0, ipredict_opt):
        # this function is also used to set the initial state vector assuming steady state condition
        # u0 is the initial input vector
        if ipredict_opt == 1:   # reduced model
            ann_input = [None]*self.ann_red.ninput
            for j in xrange(self.ninput):
                self.state_space_red[j].init_state_vector_to_steady_state(u0[j])
            n = 0
            for j in xrange(self.ninput):
                for k in xrange(self.state_space_red[j].nstate):
                    ann_input[n] = self.state_space_red[j].x[k][0]
                    n += 1
        else:
            ann_input = [None]*self.ann_lag.ninput
            for j in xrange(self.ninput):
                self.state_space_lag[j].init_state_vector_to_steady_state(u0[j])
            n = 0
            for j in xrange(self.ninput):
                for k in xrange(self.state_space_lag[j].nstate):
                    ann_input[n] = self.state_space_lag[j].x[k][0]
                    n += 1
        return ann_input

    def calc_next_state(self, u):
        # based on the reduced model
        # calculate the next state using the current state and current input u
        # u is the input vector
        for j in xrange(self.ninput):
            self.state_space_red[j].calc_next_state_vector(u[j])

    def calc_output_from_current_state(self):
        # based on the reduced model
        # return a scalar output
        ann_input = [None]*self.ann_red.ninput
        n = 0
        for j in xrange(self.ninput):
            for k in xrange(self.state_space_red[j].nstate):
                ann_input[n] = self.state_space_red[j].x[k][0]
                n += 1
        y = self.ann_red.predict(ann_input, 1, 0)[0]
        return y

    def predict(self, u, ipredict_opt):
        # predict the response given an input sequence
        # u: scaled input data, numpy array of [npair][ninput] or [npair][ninput+output]
        # ipredict_opt: 0 = Laguerre model, 1 = reduced model
        # y: returned list of [npair]
        npair = u.shape[0]
        y = [None]*npair
        if ipredict_opt == 1:   # reduced model
            ann_input = [None]*self.ann_red.ninput
            for j in xrange(self.ninput):
                self.state_space_red[j].init_state_vector_to_steady_state(u[0][j])
            for i in xrange(npair):
                n = 0
                for j in xrange(self.ninput):
                    for k in xrange(self.state_space_red[j].nstate):
                        ann_input[n] = self.state_space_red[j].x[k][0]
                        n += 1
                    self.state_space_red[j].calc_next_state_vector(u[i][j])
                # always scaling input but not scaling output
                y[i] = self.ann_red.predict(ann_input, 1, 0)[0]
        else:                   # Laguerre model
            ann_input = [None]*self.ann_lag.ninput
            for j in xrange(self.ninput):
                self.state_space_lag[j].init_state_vector_to_steady_state(u[0][j])
            for i in xrange(npair):
                n = 0
                for j in xrange(self.ninput):
                    for k in xrange(self.state_space_lag[j].nstate):
                        ann_input[n] = self.state_space_lag[j].x[k][0]
                        n += 1
                    self.state_space_lag[j].calc_next_state_vector(u[i][j])
                # always no scaling of input and output
                y[i] = self.ann_lag.predict(ann_input, 1, 0)[0]	#debug default 0 for scaling
        return y

