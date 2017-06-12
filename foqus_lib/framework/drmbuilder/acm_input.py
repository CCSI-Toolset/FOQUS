# acm_input.py

class ACMInput(object):
    def __init__(self):
        self.dt_sampling = 0.01
        self.dt_min_solver = 0.001
        self.dt_ramp = 0.001
        self.unit_time = "sec"

    def to_dictionary(self):
        dict_data = dict()
        dict_data['dt_sampling'] = self.dt_sampling
        dict_data['dt_min_solver'] = self.dt_min_solver
        dict_data['dt_ramp'] = self.dt_ramp
        dict_data['unit_time'] = self.unit_time
        return dict_data

    def from_dictionary(self, dict_data):
        self.dt_sampling = dict_data['dt_sampling']
        self.dt_min_solver = dict_data['dt_min_solver']
        if dict_data.get('dt_ramp')!=None:
            self.dt_ramp = dict_data['dt_ramp']
        self.unit_time = dict_data['unit_time']

