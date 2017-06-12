# uq_input.py
class UQInput(object):
    def __init__(self):
        # process noise of state variables and output variables
        self.fq_state = 0.02
        self.fr_output = [0.05]

    def set_default_output_noise(self, nout, fr):
        self.fr_output = [None]*nout
        for i in xrange(nout):
            self.fr_output[i] = fr

    def to_dictionary(self):
        dict_data = dict()
        dict_data['fq_state'] = self.fq_state
        dict_data['fr_output'] = self.fr_output
        return dict_data

    def from_dictionary(self, dict_data):
        self.fq_state = dict_data['fq_state']
        self.fr_output = dict_data['fr_output']

