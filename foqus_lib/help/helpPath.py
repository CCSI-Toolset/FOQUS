import os

def helpPath():
	'''
		Returns the directory of the help files
	'''
	instDir = os.path.abspath(__file__)  # path to this file
	instDir = os.path.dirname(instDir)   # take off file name (path to help)
	return(instDir)
