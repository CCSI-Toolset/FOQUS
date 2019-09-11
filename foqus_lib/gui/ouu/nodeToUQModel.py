from foqus_lib.framework.graph.graph import *
from foqus_lib.framework.uq.Model import *
	
	
def nodeToUQModel(name, node):
    '''
		This function converts a node model to a UQ model for UQ analysis.  This is temporary solution.
		The extra python calculations that are include in a node are not converted, just the simulation.
	'''
    uqModel = Model()
    uqModel.setName( name )
    uqModel.setRunType(Model.GATEWAY) #Basically run through John's stuff
    keys = list(node.inVars.keys())
    typ     = []  # Type for each input (Fixed or Variable)
    val     = []  # Current value of inputs in the node
    min     = []  # minimums for inputs
    max     = []  # maximums for inputs
    dist    = []  # distributions for inputs
    default = []  # defaults for inputs
    for key in keys:  # key is input variable name, make lists
        #if node.inVars[key].uqVar:
        typ.append( Model.VARIABLE )
        #else:
        #    typ.append( Model.FIXED )
        val.append( node.inVars[key].value )
        min.append( node.inVars[key].min )
        max.append( node.inVars[key].max )
        dist.append( node.inVars[key].dist )
        default.append( node.inVars[key].default )
    # Set input values
    uqModel.setInputNames( ['%s.%s' % (name, key) for key in keys] )
    uqModel.setInputTypes( typ )
    uqModel.setInputMins( min )
    uqModel.setInputMaxs( max )
    uqModel.setInputDistributions( dist )
    uqModel.setInputDefaults( default )
    # Set output names and set all outputs as selected
    keys = list(node.outVars.keys())
    uqModel.setOutputNames(['%s.%s' % (name, key) for key in keys] )
    uqModel.setSelectedOutputs( list(range(len(keys))) )
    return uqModel
	
def printUQModel(self):
    '''
        Print the UQ model, to make sure things are working as expected.
    '''
    print("Model Name:")
    print(self.getName())
    print("\nRun File:")
    print(self.getRunFileName())
    print("\nRun Type (0 = Gateway, 1 = Local):")
    print(self.getRunType())
    print("\nInput Names:")
    print(self.getInputNames())
    print("\nInput Types (0 = Fixed, 1 = Variable):")
    print(self.getInputTypes())
    print("\nInput Minimums:")
    print(self.getInputMins())
    print("\nInput Maximums:")
    print(self.getInputMaxs())
    print("\nInput Defaults:")
    print(self.getInputDefaults())
    print("\nOutput Names:")
    print(self.getOutputNames())
    print("\nSelected Outputs:")
    print(self.getSelectedOutputs())
    print("\n\n")
