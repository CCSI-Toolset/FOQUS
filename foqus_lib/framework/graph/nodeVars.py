'''
    nodeVars.py
     
    * This contains the classes for node variables
    * Class for lists on node variables

    John Eslick, Carnegie Mellon University, 2014

    This Material was produced under the DOE Carbon Capture Simulation
    Initiative (CCSI), and copyright is held by the software owners:
    ORISE, LANS, LLNS, LBL, PNNL, CMU, WVU, et al. The software owners
    and/or the U.S. Government retain ownership of all rights in the 
    CCSI software and the copyright and patents subsisting therein. Any
    distribution or dissemination is governed under the terms and 
    conditions of the CCSI Test and Evaluation License, CCSI Master
    Non-Disclosure Agreement, and the CCSI Intellectual Property 
    Management Plan. No rights are granted except as expressly recited
    in one of the aforementioned agreements.
'''
from collections import OrderedDict
import json
import math
import logging
import numpy as np
import traceback
import copy
from foqus_lib.framework.foqusException.foqusException import *
from foqus_lib.framework.uq.Distribution import Distribution

ivarScales = [ # list of scaling options for input variables
    'None', 
    'Linear', 
    'Log', 
    'Power', 
    'Log 2', 
    'Power 2']
    
class nodeVarEx(foqusException):
    def setCodeStrings(self):
        self.codeString[0] = 'Other exception'
        self.codeString[1] = 'Variable dimension is too high'
        self.codeString[2] = (
            'Dimension error, the variable' 
            'dimenstions should be a tuple')
        self.codeString[3] = 'Not a valid variable attribute'
        self.codeString[4] = 'New value does not match current shape'
        self.codeString[8] = 'Error unscaling'
        self.codeString[9] = 'Error scaling'
        self.codeString[10] = 'Error hist type should be list'
        self.codeString[11] = 'Invalid data type'
        self.codeString[22] = 'Time step index out of range'
    
class nodeVarListEx(foqusException):
    def setCodeStrings(self):
        self.codeString[0] = 'Other exception'
        self.codeString[2] = 'Node does not exist'
        self.codeString[3] = 'Variable does not exist'
        self.codeString[5] = 'Node name already in use, cannont add'
        self.codeString[6] = ('graph is reserved and cannot be used'
                              ' as a node name')
        self.codeString[7] = 'Var name already in use, cannont add'
        
class nodeVarList(OrderedDict):
    '''
        This class contains a dictionary of dictionaries
        the first key is the node name, the second key is
        the variable name.  This also provides methods for
        flattening variable lists if they include arrays.
    '''
    def __init__(self):
        OrderedDict.__init__(self)
    
    def clone(self):
        newOne = nodeVarList()
        sd = self.saveDict()
        newOne.loadDict(sd)
        return newOne
        
    def addNode(self, nodeName):
        if nodeName in self:
            raise nodeVarListEx(code=5, msg = str(nodeName))
        self[nodeName] = OrderedDict()
    
    def addVariable(self, nodeName, varName, var=None):
        if nodeName not in self:
            raise nodeVarListEx(2, msg=nodeName)
        if varName in self[nodeName]:
            raise nodeVarListEx(7, msg=varName)
        if not var:
            var = nodeVars()
        self[nodeName][varName] = var
        return var
        
    def get(self, name, varName=None):
        '''
            This returns a variable looked up by a name string where 
            the node name is separated from the variable name by a 
            period or if two arguments are given they are the node 
            name and variable name.  For one argument, the first period
            in the name is assumed to be the separator.  This means 
            the node names should not contain periods, but it okay for
            the variable name to contain a period.
        '''
        if varName == None:
            n = name.split('.', 1) #n[0] = node name, n[1] = var name
            name = n[0]
            varName = n[1]
        try:
            return self[name][varName]
        except KeyError as e:
            if n[0] in self:
                raise nodeVarListEx(3, msg=n[1])
            else:
                raise nodeVarListEx(2, msg=n[0])
                
    def createOldStyleDict(self):
        '''
            This can be used to create the f and x dictionaries for a
            graph.  I'm trying to phase this out, but I'm using in for
            now so I can make smaller changes working to new variable
            list objects
        '''
        self.odict = OrderedDict()
        for node in sorted(self.keys(), key=lambda s: s.lower()):
            for var in sorted(self[node].keys(), key=lambda s: s.lower()):
                self.odict['.'.join([node, var])] = self[node][var]
        return self.odict
    
    def compoundNames(self, sort=True):
        l = []
        for node in self.keys():
            for var in self[node].keys():
                l.append('.'.join([node, var]))
        if sort:
            return sorted(l, key = lambda s: s.lower())
        else:
            return l
        
    def splitName(self, name):
        return name.split('.',1)
        
    def saveValues(self):
        sd = dict()
        for node in self:
            sd[node] = OrderedDict()
            for var in self[node]:
                sd[node][var] = [None]*len(self[node][var].hist)
                for i in range(len(self[node][var].hist)):
                    if type(self[node][var].hist[i]).__module__\
                        == np.__name__:
                        sd[node][var][i] = self[node][var].hist[i].tolist()
                    else:
                        sd[node][var][i] = self[node][var].hist[i]
        return sd
        
    def loadValues(self, sd, hist=True):
        self.odict = None
        for node in sd:
            if node not in self:
                logging.getLogger("foqus." + __name__).debug(
                    "Cannot load variable node not in flowsheet, node:"
                    " {0} not in {1}".format(node, self.keys()))
                raise nodeVarListEx(2, msg=node)
            for var in sd[node]:
                try:
                    typ = self[node][var].dtype
                except:
                    typ = float
                if hist:
                    for i in range(len(sd[node][var])):
                        self[node][var].hist[i] = np.array(
                            sd[node][var][i],typ)
                else:
                    self[node][var].value = np.array(sd[node][var],typ)

    def valueDict(self, sd):
        '''
            Makes a dictionary that stores only variable values at
            the current time step.  This is use for optimization
            in the evaluation of the python code for objective functions
            and constriants.
        '''
        rd = {}
        for node in sd:
            if node not in self:
                raise nodeVarListEx(2, msg=node)
            rd[node] = {}
            for var in sd[node]:
                ts = self[node][var].ts
                rd[node][var] = np.array(sd[node][var][ts])
        return rd

    def saveDict(self):
        sd = dict()
        for node in self:
            sd[node] = OrderedDict()
            for var in self[node]:
                sd[node][var] = self[node][var].saveDict()
        return sd
        
    def loadDict(self, sd):
        self.clear()
        for node in sd:
            self.addNode(node)
            for var in sd[node]:
                self.addVariable(node, var)\
                    .loadDict(sd[node][var])
                
    def scale(self):
        for key, nodeVars in self.iteritems():
            for vkey, var in nodeVars.iteritems():
                var.scale()
                
    def makeNaN(self):
        for key, nodeVars in self.iteritems():
            for vkey, var in nodeVars.iteritems():
                var.makeNaN()
                
    def getFlat(self, names, scaled=False):
        res = []
        if scaled:
            for name in names:
                self.get(name).scale()
                res.extend(self.get(name).scaled.flatten())
        else:
            for name in names:
                res.extend(self.get(name).value.flatten())
        return res
        
    def count(self, flat=False):
        cn = self.compoundNames()
        if not flat:
            return len(cn)
        else:
            return len(self.getFlat(cn))
    
    def unflatten(self, nameList, valueList, unScale=False):
        '''
            This takes a list of variable names, and a flat list
            of values.  This function then un-flattens the values
            and creates a dictionary of variable values
        '''
        sd = {}
        pos = 0
        for i, name in enumerate(nameList):
            if not isinstance(name, (list,tuple)):
                name = self.splitName(name)
            shape = self[name[0]][name[1]].shape
            size = self[name[0]][name[1]].value.size
            if not name[0] in sd:
                sd[name[0]] = {}
            sd[name[0]][name[1]] = \
                np.array(valueList[pos:pos+size]).reshape(shape)
            pos+=size
            if unScale:
                sd[name[0]][name[1]] = \
                    self[name[0]][name[1]].unscale2(
                        sd[name[0]][name[1]])
        return sd
        
    
class nodeVars(object):
    '''
        Class for input variable attributes, variable scaling, 
        and saving/loading.  I usually expect variables values
        (the elements of the hist list to be numpy arrays.  If
        the are not for some reason there could be problems.
    '''
    def __init__(
        self, 
        value=0.0, 
        vmin=None,
        vmax=None, 
        vdflt=None, 
        unit="", 
        vst="user", 
        vdesc="", 
        tags=[],
        nTime=1,
        ts=0,
        dtype=float,
        dist=Distribution(Distribution.UNIFORM)
    ):
        self.dtype = dtype
        value = np.array(value, dtype)
        self.shape = (value.shape)
        if vmin is None:
            vmin = value
        if vmax is None:
            vmax = value
        if vdflt is None:
            vdflt = value
        self.hist = [np.zeros(self.shape, dtype)]*nTime #value history
        self.ts = ts # Current time step
        self.min = vmin # maximum value
        self.max = vmax # minimum value
        self.default = vdflt # default value
        self.unit = unit # units of measure
        self.set = vst # variable set name user or sinter so I know if
                       # user added it or from sinter configuration file
        self.desc = vdesc # variable description
        self.scaled = 0.0 # scaled value for the variable
        self.scaling = 'None' # type of variable scaling
        self.minScaled = 0.0 # scaled minimum
        self.maxScaled = 0.0 # scaled maximum
        self.tags = tags # set of tags for use in heat integration or 
                         # other searching and sorting 
        self.con = False # true if the input is set through connection
        self.toNumpy() # I generally expect variable values to be numpy
                       # objects, but need to convert to lists before 
                       # saving and sometimes the value may be set as
                       # a python float or list.
        self.setValue(value) # value of the variable
        self.setType(dtype)
        self.dist = copy.copy(dist)
        
    def typeStr(self):
        if self.dtype == float:
            return 'float'
        elif self.dtype == int:
            return 'int'
        elif self.dtype == str:
            return 'str'
        else:
            raise nodeVarEx(11, msg=str(dtype)) 
    
    def setShape(self, shape = ()):
        '''
            This sets the shape of the array for the variable
            if the shapes of the values in hist, max, min, or default
            does not match up with shape they will be reshaped. When
            reshaping all elements will be set to 0.0.  If shape has
            no elements values will be scalars
        '''
        nodeVarMaxDim = 2
        try:
            assert isinstance(shape, (tuple))
        except:
            raise nodeVarEx(
                code = 2, 
                msg = "dimension given: " + str(shape), 
                tb = traceback.format_exc())
        if isinstance(shape, int):
            if 1 > nodeVarMaxDim: 
                # in this case you don't even want to allow vectors
                raise nodeVarEx(
                    code = 3, 
                    msg = "dim = " + 1, 
                    tb = None)
        elif len(shape) > nodeVarMaxDim:
            raise nodeVarEx(
                code = 3, 
                msg = "dim = " + len(shape), 
                tb = None)
        self.shape = shape
        self.min = np.resize(self.min, shape)
        self.max = np.resize(self.max, shape)
        self.default = np.resize(self.default, shape)
        for i in range(len(self.hist)):
            self.hist[i] = np.resize(self.hist[i], shape)
    
    def listIndexes(self):
        if len(self.shape) == 0:
            #no indexes (its a scalar)
            return None
        l1 = [0]*len(self.shape)
        l2 = []
        pos = len(self.shape) - 1
        while(l1[0] < self.shape[0]):
            if l1[pos] == self.shape[pos] and pos != 0:
                l1[pos] = 0
                pos -= 1
            elif pos != len(self.shape) - 1:
                pos = len(self.shape) - 1
                l2.append(copy.copy(l1))
            else:
                l2.append(tuple(l1))
            l1[pos] += 1     
        return l2
        
    def indexToString(self, index):
        sl = ['']*len(index)
        for p in range(len(index)):
            sl[p] = '[{0}]'.format(index[p])
        return ''.join(sl)
       
    def stringToIndex(self, istr):
        l = istr.strip('[]').split('][')
        for i in range(len(l)):
            l[i] = int(float(l[i]))
        return l
    
    def roundHistInt(self):
        '''
            This rounds the whole history to 
            to nearest int, still float type
        '''
        for i in range(len(self.hist)):
            self.hist[i] = np.rint(self.hist[i])
        
    def roundValueInt(self):
        '''
            This rounds the value at the current
            time step to nearest int, still float type
        '''
        self.value = np.rint(self.value)
    
    def makeNaN(self):
        for i in range(len(self.hist)):
            self.hist[i] = self.hist[i]*np.nan
    
    def toIntRound(self):
        '''
            This rounds everything in a variable to an int
            this includes the max, mix, and default. And 
            changes the type to int
        '''
        self.min = np.rint(self.min)
        self.max = np.rint(self.max)
        self.default = np.rint(self.default)
        for i in range(len(self.hist)):
            self.hist[i] = np.rint(self.hist[i])
        self.setType(int)
    
    def setType(self, dtype=float):
        # for now only float and int are accepted but
        # may add more types later
        if dtype == "float":
            dtype = float
        elif dtype == 'int':
            dtype = int
        elif dtype == "str":
            dtype = str
        if not dtype in [float, int, str]:
            raise nodeVarEx(11, msg=str(dtype))
        self.dtype = dtype 
        for i in range(len(self.hist)):
            self.hist[i] = self.hist[i].astype(dtype)
        self.min = self.min.astype(dtype)
        self.max = self.max.astype(dtype)
        self.default = self.default.astype(dtype)

    def setTimeStep(self, step):
        try:
            self.value = self.hist[step]
        except IndexError:
            raise nodeVarEx(
                code = 22, 
                msg = "index = " + str(step), 
                tb = traceback.format_exc())
        except Exception as e:
            raise nodeVarEx(
                code = 0, 
                msg = "Error setting value from history", 
                e = e, 
                tb = traceback.format_exc())
        self.ts = step
    
    def setMin(self, val):
        val = np.array(val, dtype=self.dtype)
        if val.shape != self.shape:
            raise nodeVarEx(
                code = 4, 
                msg = "current shape: {0}, new value shape {1}".\
                    format(self.shape, val.shape),
                tb = None)
        self.__min = val
        
    def setMax(self, val):
        val = np.array(val, dtype=self.dtype)
        if val.shape != self.shape:
            raise nodeVarEx(
                code = 4, 
                msg = "current shape: {0}, new value shape {1}".\
                    format(self.shape, val.shape),
                tb = None)
        self.__max = val
        
    def setDefault(self, val):
        val = np.array(val, dtype=self.dtype)
        if val.shape != self.shape:
            raise nodeVarEx(
                code = 4, 
                msg = "current shape: {0}, new value shape {1}".\
                    format(self.shape, val.shape),
                tb = None)
        self.__default = val
    
    def getValue(self):
        try:
            return self.hist[self.ts]
        except IndexError:
            raise nodeVarEx(
                code = 22, 
                msg = "index = " + str(step), 
                tb = traceback.format_exc())
        except Exception as e:
            raise nodeVarEx(
                code = 0, 
                msg = "Error getting value from history", 
                e = e, 
                tb = traceback.format_exc())
    
    def setValue(self, val):
        '''
            Set the value of a variable = is overloaded to use this
        '''
        val = np.array(val)
        if val.shape != self.shape:
            # try to reshape, this lets you change the size of vector
            # and matrix varaibles by entering a value with a new shape
            # this may be a little dangerous.
            self.setShape(val.shape)
        try:
            self.hist[self.ts] = np.array(val)
            self.hist[self.ts] = self.hist[self.ts].astype(self.dtype)
        except IndexError:
            raise nodeVarEx(
                code = 22, 
                msg = "index = " + str(step), 
                tb = traceback.format_exc())
        except Exception as e:
            raise nodeVarEx(
                code = 0, 
                msg = "Error setting value from history", 
                e = e, 
                tb = traceback.format_exc())

    def __getattr__(self, name):
        '''
            This should only be called if a variable doesn't have the
            attribute name.  If the attribute is value we should return
            the value at the curent time step.  Otherwise just raise an
            attribute error, because the variable has no attribute name.
        '''
        if name == 'value':
            return self.getValue()
        elif name == 'min':
            return self.__min
        elif name == 'max':
            return self.__max
        elif name == 'default':
            return self.__default
        else:
            raise AttributeError
        
    def __setattr__(self, name, val):
        '''
            This is called when setting an attribute, if the attribute
            is value, want to set the value at the current time step
            otherwise just do the noramal thing
        '''
        if name == 'value':
            self.setValue(val)
        elif name == 'min':
            self.setMin(val)
        elif name == 'max':
            self.setMax(val)
        elif name == 'default':
            self.setDefault(val)
        else:
            object.__setattr__(self, name, val)
    
    def isScalar(self):
        if len(self.value.shape) == 0:
            return True
        return False
    
    def nElements(self):
        if len(self.value.shape) == 0:
            return 1
        n = 1
        for x in self.value.shape:
            n *= x
        return n
    
    def toNumpy(self):
        '''
            Converts python numbers or lists of numbers to numpy form.
            When reading json back from saved files or GUI forms the 
            results are Python numbers or lists, so this makes sure
            all numerical values are in numpy form.
        '''
        for i in range(len(self.hist)):
            self.hist[i] = np.array(self.hist[i])
        self.min       = np.array( self.min )
        self.max       = np.array( self.max )
        self.default   = np.array( self.default )
        self.scaled    = np.array( self.scaled )
        self.minScaled = np.array( self.minScaled )
        self.maxScaled = np.array( self.maxScaled )
    
    def scale(self):
        '''
            Scale the value stored in the value field and
            put the result in the scaled field.
        '''
        self.scaled = self.scale2(self.value)
    
    def unscale(self):
        '''
            Unscale the value stored in the scaled field and
            put the result in the value field.
        '''
        self.value = self.unscale2(self.scaled)
    
    def scaleBounds(self):
        '''
            Calculate the scaled bounds and store the results in 
            the minScaled and maxScaled fields.
        '''
        self.minScaled = self.scale2(self.min)
        self.maxScaled = self.scale2(self.max)
    
    def scale2(self, val):
        '''
            Use the variable's bounds and scale type to scale a 
            numpy vector.  The scales all run from 0 at the minimum 
            to 10 at the maximum, except None which does nothing.
        '''
        try:
            if self.scaling == 'None':
                out = val
            elif self.scaling == 'Linear':
                out = 10*(val - self.min)/(self.max - self.min)
            elif self.scaling == 'Log':
                out = 10*(np.log10(val) - np.log10(self.min))/ \
                    (np.log10(self.max) - np.log10(self.min))
            elif self.scaling == 'Power':
                out = 10*(np.power(10, val) - np.power(10,self.min))/ \
                    (np.power(10, self.max) - np.power(10, self.min))
            elif self.scaling == 'Log 2':
                out = 10*np.log10(9*(val - self.min)/ \
                    (self.max - self.min)+1)
            elif self.scaling == 'Power 2':
                out = 10.0/9.0*(np.power(10,(val - self.min)/ \
                    (self.max - self.min))-1)
            else:
                raise
        except:
            raise nodeVarEx(
                code = 9, 
                msg = "value = {0}, scaling method = {1}" \
                    .format(val, self.scaling),
                tb = traceback.format_exc())
        return np.array(out)
    
    def unscale2(self, val):
        '''
            Convert value to an unscaled value using the 
            variables settings.
        '''
        try:
            if self.scaling == 'None':
                out = val
            elif self.scaling == 'Linear':
                out = val*(self.max - self.min)/10.0 + self.min
            elif self.scaling == 'Log':
                out = np.power(self.min*(self.max/self.min),(val/10.0))
            elif self.scaling == 'Power':
                out = np.log10((val/10.0)*(np.power(10,self.max) - \
                    np.power(10,self.min))+np.power(10, self.min))
            elif self.scaling == 'Log 2':
                out = (np.power(10, val/10.0)-1)*(self.max-self.min)/ \
                    9.0 + self.min
            elif self.scaling == 'Power 2':
                out = np.log10(9.0*val/10.0 + 1)*(self.max-self.min) + \
                    self.min
            else:
                raise
        except:
            raise nodeVarEx(
                code = 9, 
                msg = "value = {0}, scaling method = {1}". \
                    format(val, self.scaling),
                tb = traceback.format_exc())
        return np.array(out)
            
    def saveDict(self):
        '''
            Save an input variable's content to a dictionary.  This is
            mostly used to save to a file but can also be used as an 
            ugly way to make a copy of a variable.
        '''
        sd = dict()
        # if values are in numpy format (they almost always are)
        # convert to list or python number
        vmin = self.min
        vmax = self.max
        vdefault = self.default
        hist = [0]*len(self.hist)
        for i in range(len(self.hist)):
            if type(self.hist[i]).__module__ == np.__name__:
                hist[i] = self.hist[i].tolist()
            else:
                logging.getLogger("foqus." + __name__).debug(
                   "Variable not in numpy format Val: {0}, Desc: {1}"\
                    .format(value, self.desc)) 
        if type(self.min).__module__ == np.__name__:
            vmin = self.min.tolist()
        if type(self.max).__module__ == np.__name__:
            vmax = self.max.tolist()
        if type(self.default).__module__ == np.__name__: 
            vdefault = self.default.tolist()
        sd["shape"]      = self.shape
        sd["hist"]       = hist
        sd["ts"]         = self.ts
        if self.dtype == float:
            sd["dtype"] = 'float'
        elif self.dtype == int:
            sd["dtype"] = 'int'
        elif self.dtype == str:
            sd["dtype"] = 'str'
        else:
            raise nodeVarEx(11, msg = str(dtype))
        sd["min"]        = vmin
        sd["max"]        = vmax
        sd["default"]    = vdefault
        sd["unit"]       = self.unit
        sd["set"]        = self.set
        sd["desc"]       = self.desc
        sd["scaling"]    = self.scaling
        sd["tags"]       = self.tags
        sd["dist"]       = self.dist.saveDict()
        return sd
    
    def loadDict(self, sd):
        '''
            Load the contents of a dictionary created by saveDict(), 
            and possibly read back in as part of a json file.
        '''
        assert isinstance(sd, dict) 
        dtype = sd.get('dtype', 'float')
        if dtype == 'float':
            self.dtype = float
        elif dtype == 'int':
            self.dtype = int
        elif dtype == 'str':
            self.dtype = str
        else:
            raise nodeVarEx(11, msg=str(dtype))
        self.ts = sd.get("ts", 0)
        self.shape = sd.get("shape", None)
        if self.shape != None: self.shape = tuple(self.shape)
        # Depending on how old the session file is
        # that we are trying to read it should either
        # have history or value
        hist = sd.get("hist", None)
        value = sd.get("value", None)
        if hist:
            try:
                assert isinstance(hist, list)
            except:
                raise nodeVarEx(10)
            self.hist = hist
            for i in range(len(hist)):
                hist[i] = np.array(hist[i], dtype=self.dtype)
        elif not value == None:
            value = np.array(value, dtype = dtype)
            if not self.shape:
                self.setShape(value.shape)
            self.value = value
        self.min = np.array(sd.get("min", 0), dtype=self.dtype)
        self.max = np.array(sd.get("max", 0), dtype=self.dtype)
        self.default = \
            np.array(sd.get("default", 0), dtype=self.dtype)
        self.unit = sd.get("unit", "")
        self.set = sd.get("set", "user")
        self.desc = sd.get("desc", "")
        self.scaling = sd.get("scaling", 'None')
        self.tags = sd.get("tags", [])
        dist = sd.get("dist", None)
        if dist:
            self.dist.loadDict(dist)            
        self.scale()
        self.scaleBounds()
            
class nodeOutVars(nodeVars):
    pass

class nodeInVars(nodeVars):
    pass
