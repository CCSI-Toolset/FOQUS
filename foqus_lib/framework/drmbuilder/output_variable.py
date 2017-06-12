# output_variable.py
class OutputVariable(object):
    def __init__(self):
        self.key_sinter = 'key_sinter'
        self.name = "output"
        self.desc = "description"
        self.unit = "unit"
        self.bvaried = True
        self.xdefault = 0.0

    def to_dictionary(self):
        dict_data = dict()
        dict_data['key_sinter'] = self.key_sinter
        dict_data['name'] = self.name
        dict_data['desc'] = self.desc
        dict_data['unit'] = self.unit
        dict_data['bvaried'] = self.bvaried
        dict_data['xdefault'] = self.xdefault
        return dict_data

    def from_dictionary(self, dict_data):
        self.key_sinter = dict_data['key_sinter']
        self.name = dict_data['name']
        self.desc = dict_data['desc']
        self.unit = dict_data['unit']
        self.bvaried = dict_data['bvaried']
        self.xdefault = dict_data['xdefault']

