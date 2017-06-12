# step_change.py
class StepChange(object):
    def __init__(self):
        self.npoint = 5
        self.nduration = 1
        self.ireverse = 1
        self.vduration = [10]
        
    def to_dictionary(self):
        dict_data = dict()
        dict_data['npoint'] = self.npoint
        dict_data['nduration'] = self.nduration
        dict_data['ireverse'] = self.ireverse
        dict_data['vduration'] = self.vduration
        return dict_data

    def from_dictionary(self, dict_data):
        self.npoint = dict_data['npoint']
        self.nduration = dict_data['nduration']
        self.ireverse = dict_data['ireverse']
        self.vduration = dict_data['vduration']