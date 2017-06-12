import numpy
from foqus_lib.framework.graph.nodeVars import *
from collections import OrderedDict

class pymodel:
    def __init__(self):
        self.inputs = OrderedDict()
        self.outputs = OrderedDict()
        self.status = -1 # Caclulation status code
        self.description = "A Python model plugin"
        self.node = None
    
    def setNode(self, node=None):
        self.node = node
        
    def run(self):
        '''
            Override this function with python model
        '''
        pass

    
