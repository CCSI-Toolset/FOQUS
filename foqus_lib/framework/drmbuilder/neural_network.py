# neural_network.py
from math import exp


class NeuralNetwork(object):
    def __init__(self):
        self.ninput = 1
        self.noutput = 1
        self.nlayer_hid = 1
        self.nneuron_layer_hid = []    # number of neurons in hidden layers excluding the bias neuron
        self.steepness_hid = 1.0
        self.steepness_out = 1.0
        self.iactivation_hid = 2
        self.iactivation_out = 0
        self.weight = []
        self.mean_in = []
        self.sigma_in = []
        self.mean_out = []
        self.sigma_out = []

    def to_dictionary(self):
        dict_data = dict()
        dict_data['ninput'] = self.ninput
        dict_data['noutput'] = self.noutput
        dict_data['nlayer_hid'] = self.nlayer_hid
        dict_data['nneuron_layer_hid'] = self.nneuron_layer_hid
        dict_data['steepness_hid'] = self.steepness_hid
        dict_data['steepness_out'] = self.steepness_out
        dict_data['iactivation_hid'] = self.iactivation_hid
        dict_data['iactivation_out'] = self.iactivation_out
        dict_data['weight'] = self.weight
        dict_data['mean_in'] = self.mean_in
        dict_data['sigma_in'] = self.sigma_in
        dict_data['mean_out'] = self.mean_out
        dict_data['sigma_out'] = self.sigma_out
        return dict_data

    def from_dictionary(self, dict_data):
        self.ninput = dict_data['ninput']
        self.noutput = dict_data['noutput']
        self.nlayer_hid = dict_data['nlayer_hid']
        self.nneuron_layer_hid = dict_data['nneuron_layer_hid']
        self.steepness_hid = dict_data['steepness_hid']
        self.steepness_out = dict_data['steepness_out']
        self.iactivation_hid = dict_data['iactivation_hid']
        self.iactivation_out = dict_data['iactivation_out']
        self.weight = dict_data['weight']
        self.mean_in = dict_data['mean_in']
        self.sigma_in = dict_data['sigma_in']
        self.mean_out = dict_data['mean_out']
        self.sigma_out = dict_data['sigma_out']

    def set_from_tuple(self, dat):
        self.ninput = dat[0]
        self.noutput = dat[1]
        self.nlayer_hid = dat[2]
        self.nneuron_layer_hid = [None]*self.nlayer_hid
        icount = 3
        for i in xrange(self.nlayer_hid):
            self.nneuron_layer_hid[i] = dat[icount]
            icount += 1
        self.iactivation_hid = dat[icount]
        icount += 1
        self.iactivation_out = dat[icount]
        icount += 1
        self.steepness_hid = dat[icount]
        icount += 1
        self.steepness_out = dat[icount]
        icount += 1
        nconnection = dat[icount]
        icount += 1
        self.weight = [None]*nconnection
        for i in xrange(nconnection):
            self.weight[i] = dat[icount]
            icount += 1
        self.mean_in = [None]*self.ninput
        self.sigma_in = [None]*self.ninput
        self.mean_out = [None]*self.noutput
        self.sigma_out = [None]*self.noutput
        for i in xrange(self.ninput):
            self.mean_in[i] = dat[icount]
            icount += 1
        for i in xrange(self.noutput):
            self.mean_out[i] = dat[icount]
            icount += 1
        for i in xrange(self.ninput):
            self.sigma_in[i] = dat[icount]
            icount += 1
        for i in xrange(self.noutput):
            self.sigma_out[i] = dat[icount]
            icount += 1

    def write_to_matlab_file(self, fout, iann=0):
        # iann is the index of output for DABNet model, use default if NARMA model
        iann += 1
        line = "NN({0}).nx = {1};\n".format(iann, self.ninput)
        fout.write(line)
        line = "NN({0}).ny = {1};\n".format(iann, self.noutput)
        fout.write(line)
        line = "NN({0}).nhid = {1};\n".format(iann, self.nlayer_hid)
        fout.write(line)
        for i in xrange(self.nlayer_hid):   # nlayer_hid is always 1 for NARMA or DABNet and nneuron_hid is not array here
            line = "NN({0}).nneuron_hid = {1};\n".format(iann, self.nneuron_layer_hid[i])
            fout.write(line)
        line = "NN({0}).iactivation_hidden = {1};\n".format(iann, self.iactivation_hid)
        fout.write(line)
        line = "NN({0}).iactivation_output = {1};\n".format(iann, self.iactivation_out)
        fout.write(line)
        line = "NN({0}).steepness_hidden = {1};\n".format(iann, self.steepness_hid)
        fout.write(line)
        line = "NN({0}).steepness_output = {1};\n".format(iann, self.steepness_out)
        fout.write(line)
        nconnection = len(self.weight)
        for i in xrange(nconnection):
            line = "NN({0}).weight({1}) = {2};\n".format(iann, i+1, self.weight[i])
            fout.write(line)
        for i in xrange(self.ninput):
            line = "NN({0}).mean_in({1}) = {2};\n".format(iann, i+1, self.mean_in[i])
            fout.write(line)
        for i in xrange(self.noutput):
            line = "NN({0}).mean_out({1}) = {2};\n".format(iann, i+1, self.mean_out[i])
            fout.write(line)
        for i in xrange(self.ninput):
            line = "NN({0}).sigma_in({1}) = {2};\n".format(iann, i+1, self.sigma_in[i])
            fout.write(line)
        for i in xrange(self.noutput):
            line = "NN({0}).sigma_out({1}) = {2};\n".format(iann, i+1, self.sigma_out[i])
            fout.write(line)

    def predict(self, xinput, iscale_input, iscale_output):
        # xinput: list of input
        # iscale_input: 0=no scaling of input, 1=scaling input
        # iscale_output: 0=no scaling of output, 1=scaling output
        # calculate total number of neurons
        nneuron = self.ninput + self.noutput + self.nlayer_hid + 2
        for i in xrange(self.nlayer_hid):
            nneuron += self.nneuron_layer_hid[i]
        y_neuron = [None]*nneuron
        if iscale_input == 1:   # scale input
            for i in xrange(self.ninput):
                y_neuron[i] = (xinput[i] - self.mean_in[i])/self.sigma_in[i]
        else:                   # does not scale input
            for i in xrange(self.ninput):
                y_neuron[i] = xinput[i]
        y_neuron[self.ninput] = 1.0
        ianterior1st = 0
        nanterior_with_bias = self.ninput + 1
        iconn = 0
        ineuron = 0
        for i in xrange(self.nlayer_hid+1):
            if i < self.nlayer_hid:
                ncurrent_without_bias = self.nneuron_layer_hid[i]
            else:
                ncurrent_without_bias = self.noutput
            icurrent1st = ianterior1st + nanterior_with_bias
            if i < self.nlayer_hid:
                iactivation = self.iactivation_hid
                steepness = self.steepness_hid
            else:
                iactivation = self.iactivation_out
                steepness = self.steepness_out
            for j in xrange(ncurrent_without_bias):
                ineuron = icurrent1st + j
                sum_x = 0
                for k in xrange(nanterior_with_bias):
                    sum_x += y_neuron[ianterior1st + k]*self.weight[iconn]
                    iconn += 1
                sum_x *= steepness
                if iactivation == 2:
                    if sum_x < -100:
                        sum_x = -1.0
                    else:
                        sum_x = 2/(1+exp(-2*sum_x)) - 1
                    y_neuron[ineuron] = sum_x
                else:
                    y_neuron[ineuron] = sum_x
            ineuron += 1
            y_neuron[ineuron] = 1.0
            ianterior1st = icurrent1st
            nanterior_with_bias = ncurrent_without_bias + 1
        # scale output variable
        youtput = [None]*self.noutput
        ineuron = icurrent1st
        if iscale_output == 1:  # scale output
            for i in xrange(self.noutput):
                youtput[i] = y_neuron[ineuron+i]*self.sigma_out[i] + self.mean_out[i]
        else:                   # not scale output
            for i in xrange(self.noutput):
                youtput[i] = y_neuron[ineuron+i]
        return tuple(youtput)