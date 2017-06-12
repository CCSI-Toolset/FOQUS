# narma_input.py
class NARMAInput(object):
    def __init__(self):
        self.nneuron_hid = 10
        self.nhistory = 2
        self.nmax_iter_bp = 10000

    def set_to_default_values(self):
        self.nneuron_hid = 10
        self.nhistory = 2
        self.nmax_iter_bp = 10000

    def to_dictionary(self):
        dict_data = dict()
        dict_data['nneuron_hid'] = self.nneuron_hid
        dict_data['nhistory'] = self.nhistory
        dict_data['nmax_iter_bp'] = self.nmax_iter_bp
        return dict_data

    def from_dictionary(self, dict_data):
        self.nneuron_hid = dict_data['nneuron_hid']
        self.nhistory = dict_data['nhistory']
        self.nmax_iter_bp = dict_data['nmax_iter_bp']