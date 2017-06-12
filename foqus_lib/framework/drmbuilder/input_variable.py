# input_variable.py
class InputVariable(object):
    def __init__(self):
        self.key_sinter = 'sinter_key'
        self.name = "input"
        self.desc = "description"
        self.unit = "unit"
        self.bvaried = True
        self.bramp = False
        self.xdefault = 0.0
        self.xlower = 0.0
        self.xupper = 0.0
        self.ramp_rate = 1.0

    def to_dictionary(self):
        dict_data = dict()
        dict_data['key_sinter'] = self.key_sinter
        dict_data['name'] = self.name
        dict_data['desc'] = self.desc
        dict_data['unit'] = self.unit
        dict_data['bvaried'] = self.bvaried
        dict_data['bramp'] = self.bramp
        dict_data['xdefault'] = self.xdefault
        dict_data['xlower'] = self.xlower
        dict_data['xupper'] = self.xupper
        dict_data['ramp_rate'] = self.ramp_rate
        return dict_data

    def from_dictionary(self, dict_data):
        self.key_sinter = dict_data['key_sinter']
        self.name = dict_data['name']
        self.desc = dict_data['desc']
        self.unit = dict_data['unit']
        self.bvaried = dict_data['bvaried']
        self.bramp = dict_data['bramp']
        self.xdefault = dict_data['xdefault']
        self.xlower = dict_data['xlower']
        self.xupper = dict_data['xupper']
        self.ramp_rate = dict_data['ramp_rate']
