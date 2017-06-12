'''
    results.py

    * This contains the class for sample results data heading

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
import copy
import csv
import string
import numpy
import json
import datetime
import logging
import re
import math

class dataFilter():
    DF_NOT = 0
    DF_AND = 1
    DF_OR = 2
    DF_XOR = 3
    DF_END_OP = 9
    DF_RULE = 10

    def __init__(self):
        self.fstack = []
        self.sortTerm = None
        
    def saveDict(self):
        sd = {
            'fstack':[],
            'sortTerm':self.sortTerm}
        for i in self.fstack:
            if i[0] < self.DF_END_OP:
                sd['fstack'].append(i)
            elif i[0] == self.DF_RULE:
                sd['fstack'].append([i[0], i[1].saveDict()])
        return sd
        
    def loadDict(self, sd):
        self.sortTerm = sd.get('sortTerm', None)
        self.fstack = []
        fs = sd.get('fstack', [])
        for i in fs:
            if i[0] < self.DF_END_OP:
                self.fstack.append(i)
            elif i[0] == self.DF_RULE:
                dfr = dataFilterRule()
                dfr.loadDict(i[1])
                self.fstack.append([i[0], dfr])

class dataFilterRule():
    OP_EQ = 0
    OP_L = 1
    OP_G = 2
    OP_LE = 3
    OP_GE = 4
    OP_IN = 5
    OP_NEQ = 6
    OP_TRUE = 11
    OP_FALSE = 12

    TERM_CONST = 0
    TERM_INPUT = 3
    TERM_OUTPUT = 4
    TERM_OTHERCOL = 7
    TERM_INDEX = 8

    def __init__(self, op=0):
        self.anyEl = False
        self.op = op
        self.term1 = [self.TERM_OTHERCOL, 'Error']
        self.term2 = [self.TERM_CONST, 0]
        
    def saveDict(self):
        sd = {
            'anyEl':self.anyEl,
            'op':self.op,
            'term1':self.term1,
            'term2':self.term2}
        return sd
            
    def loadDict(self, sd):
        self.anyEl = sd.get('anyEl', False)
        self.op = sd['op']
        self.term1 = sd['term1']
        self.term2 = sd['term2']

class results():
    '''
        The results are saved in a list of lists.  The first list is a
        list of flow sheet evaluation results.  The second list is a
        list of values that make up a result.  A data header dictates
        the position of differnt values in the result list.

        For a single result the list is formatted like:

        [
            set name,
            result name,
            time,
            elapsed time,
            flowsheet error code,
            FOQUS session uid,
            [<node name> Code], #list of node error codes
            [<node name> Simulation id], #list, simulation id or None
            [<node name>.<input> value], #input value list
            [<node name>.<output> value], #output value list
            [<node name>.<setting> value] #setting value
        ]

        If the flowsheet changes so that there are differnt variables
        the results will no longer match the flowsheet and the old
        values will not be able to be mixed with the new values.
    '''

    def __init__(self, gr=None):
        #dictionary that points to result column in this
        # head the the input and outputs are not flattened
        self.clear()
        self.gr = gr

    def clear(self):
        self.filters = {}
        self.filters["All"] = dataFilter()
        self.filters["None"] = dataFilter()
        rule = dataFilterRule()
        rule.term1 = [rule.TERM_INDEX]
        rule.term2 = [rule.TERM_CONST, 0]
        rule.op = rule.OP_L
        self.filters["None"].fstack.append(
            [self.filters["None"].DF_RULE, rule])
        self.curFilter = None
        self.timestep = 0
        self.hiddenCols = []
        self.headMap = OrderedDict()
        self.headMapI = {}
        self.headType = []
        self.inputMap = OrderedDict()
        self.inputMapI = {}
        self.outputMap = OrderedDict()
        self.outputMapI = {}
        self.inputShape = {}
        self.inputType = {}
        self.outputShape = {}
        self.outputType = {}
        self.inputSize = {}
        self.outputSize = {}
        self.nsettingsMap = OrderedDict()
        self.nsettingsMapI = {}
        self.nodeErrorMap = OrderedDict()
        self.nodeErrorMapI = {}
        self.nodeSimIDMap = OrderedDict()
        self.nodeSimIDMapI = {}
        self.colSortOrder = []
        self.rlist = [] # a list of lists the lists in row list are the
            #results.
        self.rowSortOrder = [] # list of row indexes for filtering and
            #sorting results.
        self.flatTable = True  # display table as flat if true
        self.__flat_valid__ = False
        self.__flat_sort__ = False
        
    def clearData(self):
        '''
            Clear all the results and remake the header from the 
            current stae=te of the flowsheet.
        '''
        self.rowSortOrder = []
        self.rlist = []
        self.headersFromGraph()
        
    def sortByTerm(self, term, fltr = True):
        '''
            Sort results can sort on multiple columns and reverse
            selected columns by using a - before a sort term
        '''
        if fltr:
            rows = self.rowSortOrder
        else:
            rows = range(len(self.rlist))
        term = term.strip()
        if term[0] == '[' and term[-1] == ']':
            terms = json.loads(term)
        elif term[0] == '"' and term[-1] == '"':
            terms = [json.loads(term)]
        else:
            terms = [term]
        terms2 = [None]*len(terms)
        rev = [False]*len(terms)
        for i, t in enumerate(terms):
            t = t.strip()
            if t[0] == '-':
                rev[i] = True
                t = t[1:].strip()
            terms2[i] = self.filterTerm(t)
        col = [(0, 0)]*len(rows)
        for i, row in enumerate(rows):
            try:
                sk = []
                for t in terms2:
                    sk.append(self.dataFilterGetTerm(t, row))
                col[i] = (row, tuple(sk))
            except:
                logging.getLogger("foqus." + __name__).exception(
                    "Error sorting data")
                return
        for i in range(len(terms2)-1,-1,-1):
            # do this step by step so I can reverse order some keys
            if rev[i]:
                col.sort(key=lambda x:x[1][i], reverse=True)
            else:
                col.sort(key=lambda x:x[1][i])
        scol = [i[0] for i in col]
        self.rowSortOrder = scol
        return scol
        
    def rowToFlowsheet(self, row, gr, fltr=True):
        '''
            Copy the stored values in a row to a flowsheet
        '''
        if fltr:
            row = self.rowSortOrder[row]
        rdat = self.rlist[row]
        gr.setErrorCode(rdat[self.headMap['Error']])
        gr.solTime = self.headMap['ElapsedTime']
        for nkey, node in gr.nodes.iteritems():
            if nkey in self.nodeErrorMap:
                node.calcError = rdat[self.nodeErrorMap[nkey]]
            else:
                node.calcError = -1
        for nkey in gr.input:
            for vkey, var in gr.input[nkey].iteritems():
                if nkey in self.inputMap and vkey in self.inputMap[nkey]:
                    var.value = rdat[self.inputMap[nkey][vkey]][var.ts]
        for nkey in gr.output:
            for vkey, var in gr.output[nkey].iteritems():
                if nkey in self.outputMap and vkey in self.outputMap[nkey]:
                    var.value = rdat[self.outputMap[nkey][vkey]][var.ts]

        
    def deleteRows(self, rows, fltr = True):
        '''
            Delete selected rows of the data set.
        '''
        rows.sort()
        it = reversed(rows)
        if fltr:
            ri = [0]*len(rows)
            for i, row in enumerate(it):
                ri[i] = self.rowSortOrder[row]
            it2 = reversed(sorted(ri))
            for row in it2:
                del self.rlist[row]
            de = 0
            for rowf, row in enumerate(self.rowSortOrder):
                if row in rows:
                    de += 1
                self.rowSortOrder[row] -= de
            it = reversed(rows)
            for row in it:
                del self.rowSortOrder[row]
        else:
            for row in it:
                del self.rlist[row]
                self.rowSortOrder.remove(row)
                for i, r in enumerate(self.rowSortOrder):
                    if r > row:
                        self.rowSortOrder -= 1
    
    def setSetName(self, name, row, fltr=True):
        '''
            Set tag list or add to tags
        '''
        if fltr:
            row = self.rowSortOrder[row]
        col = self.headMap['SetName']
        self.rlist[row][col] = name
    
    def setTags(self, tags, row, add=False, fltr=True):
        '''
            Set tag list or add to tags
        '''
        if type(tags) != list:
            tags = list(tags)
        if fltr:
            row = self.rowSortOrder[row]
        col = self.headMap['Tags']
        if add:
            self.rlist[row][col] += tags
        else:
            self.rlist[row][col] = tags
        self.rlist[row][col] = sorted(set(self.rlist[row][col]))

    def incrimentSetName(self, name):
        '''
            This function returns a non-existent set name.
            if name is not already a set name return name
            otherwise use a format like name_n where n is an
            incrementing number.
        '''
        sets = self.getSets()
        if not name in sets:
            return name
        index = 1
        for n in sets:
            m = re.match(r"^%s_([0-9]+)$" % name, n)
            if m:
                i = int(float( m.group(1) ))
                if i >= index: index = i + 1
            else:
                "".join([name, "_", str(index).zfill(4)])
        return "".join([name, "_", str(index).zfill(4)])

    def getSets(self):
        col = self.headMap.get('SetName', None)
        names = set()
        if col != None:
            for r in self.rlist:
                names.add(self.resultElement(r, col))
        return names

    def setFlatTable(self, b):
        self.flatTable = b

    def rowCount(self, filtered = False):
        if filtered:
            return len(self.rowSortOrder)
        else:
            return len(self.rlist)

    def colCount(self):
        if self.flatTable:
            # Construct flat header if needed
            # does nothing if already made
            self.constructFlatHead()
            return len(self.headStringsFlat)
        else:
            return len(self.colSortOrder)

    def currentFilter(self):
        return self.curFilter

    def tableData(self, row, col, filtered=False):
        if filtered:
            row = self.rowSortOrder[row]
        if self.flatTable:
            m = self.headMapFlat[col]
            r = self.rlist[row]
            return self.resultElement(r, m[0], m[1])
        else:
            m = self.colSortOrder[col]
            r = self.rlist[row]
            val = self.resultElement(r, m, ())
            if type(val).__module__ == numpy.__name__:
                val = val.tolist()
            return val

    def setTableData(self, row, col, value, filtered=False):
        val = json.loads(value)
        if filtered:
            row = self.rowSortOrder[row]
        if self.flatTable:
            m = self.headMapFlat[col]
            r = self.rlist[row]
            self.resultElementSet(val, r, m[0], m[1])
        else:
            m = self.colSortOrder[col]
            r = self.rlist[row]
            return self.resultElementSet(val, r, m, ())
            
    def tableHeaderDataH(self, i):
        if self.flatTable:
            self.constructFlatHead()
            return self.headStringsFlat[i]
        else:
            return self.headMapI[self.colSortOrder[i]]

    def tableHeaderDataV(self, i, filtered=False):
        if filtered:
            try:
                return self.rowSortOrder[i]
            except:
                return "error"
        else:
            return i
        
    def setFilter(self, dfName):
        '''
            Set the name of the current filter, also apply it to 
            generate the list of rows (self.rowSortOrder)
        '''
        if dfName in self.filters:
            #if filter exists execute filter
            self.curFilter = dfName
            rows = self.dataFilterEval(self.filters[dfName])
            self.rowSortOrder = numpy.where(numpy.array(rows)==True)
            self.rowSortOrder = self.rowSortOrder[0].tolist()
            if self.filters[dfName].sortTerm:
                self.sortByTerm(self.filters[dfName].sortTerm)
        else:
            #if no filter just ruturn all the results.
            self.curFilter = None
            self.rowSortOrder = range(len(self.rlist))

    def dataFilterEval(self, df):
        '''
            Apply the given filter to all the rows.  Returns a vector 
            the same length as the number of rows.  An elemnt is True
            if the row is in the filtered results and False if out
        '''
        n = len(self.rlist)
        test = [False]*n
        for i in range(n):
            test[i] = self.dataFilterEval2(df, i)
        return test

    def dataFilterEval2(self, df, row_index):
        '''
            Evaluate one row againts filter and return true if passes
            through the filter.
        '''
        c = len(df.fstack)
        rstack = []
        if c == 0:
            rstack.append(
                dataFilterRule(op=dataFilterRule.OP_TRUE))
        for i in range(c):
            if df.fstack[i][0] == dataFilter.DF_RULE:
                rstack.append(df.fstack[i][1])
            elif df.fstack[i][0] == dataFilter.DF_NOT:
                if self.dataFilterRuleEval2(rstack.pop(), row_index):
                    rstack.append(
                        dataFilterRule(op=dataFilterRule.OP_FALSE))
                else:
                    rstack.append(
                        dataFilterRule(op=dataFilterRule.OP_TRUE))
            else: # The rest of the possible operations are binary ops
                r2 = self.dataFilterRuleEval2(rstack.pop(), row_index)
                r1 = self.dataFilterRuleEval2(rstack.pop(), row_index)
                if df.fstack[i][0] == dataFilter.DF_AND:
                    test = r1 and r2
                elif df.fstack[i][0] == dataFilter.DF_OR:
                    test = r1 or r2
                elif df.fstack[i][0] == dataFilter.DF_XOR:
                    test = (r1 or r2) and (not r1 or not r2)
                if test:
                    rstack.append(
                        dataFilterRule(op=dataFilterRule.OP_TRUE))
                else:
                    rstack.append(
                        dataFilterRule(op=dataFilterRule.OP_FALSE))
        return self.dataFilterRuleEval2(rstack.pop(), row_index)

    def filterTermString(self, term):
        '''
            Take a filter term and turn it back into a string to
            display.
            
            term - a filter term first element is type other elements
                   specify details depending on type
            
            returns a string that can be turned back into a term by
               filter term and is readable.
        '''
        if term[0] == dataFilterRule.TERM_INPUT:
            return "Input.{0}.{1}".format(term[1], term[2])
        elif term[0] == dataFilterRule.TERM_OUTPUT:
            return "Output.{0}.{1}".format(term[1], term[2])
        elif term[0] == dataFilterRule.TERM_INDEX:
            return "Index"
        elif term[0] == dataFilterRule.TERM_OTHERCOL:
            return term[1]
        elif term[0] == dataFilterRule.TERM_CONST:
            return json.dumps(term[1])
        else:
            return "0"
    
    def filterTerm(self, s):
        '''
            This function takes a string that the use may type as a 
            term when creating a filter rule and figures out what type
            of term it is and returns a filter term.
            
            s - string representing a filter term
            returns:
                - filter term if proper format
                - None if string didn't match anything
        '''
        ssplt = s.split('.',1)
        if ssplt[0].lower() == 'input': # check if input.
            v = ssplt[1].split('.',1)
            if len(v) == 2:
                return [dataFilterRule.TERM_INPUT, v[0], v[1]]
        elif ssplt[0].lower() == 'output': # check if output.
            v = ssplt[1].split('.',1)
            if len(v) == 2:
                return [dataFilterRule.TERM_OUTPUT, v[0], v[1]]
        elif s.lower() == 'index': # check if index
            try:
                return [dataFilterRule.TERM_INDEX]
            except:
                pass
        elif s in self.headMap: # check if other column
            return [dataFilterRule.TERM_OTHERCOL, s]
        else: #assume constant
            try:
                c = json.loads(s)
                return [dataFilterRule.TERM_CONST, c]
            except:
                pass
        return None

    def dataFilterGetTerm(self, term, row_index):
        '''
            Get the value of a filter term for a given row index.
            The row index is for the entire data set not the filtered
            set.
            
            term: a filter term
            row_index: row index in full data set
        '''
        if term[0] == dataFilterRule.TERM_OTHERCOL:
            col = self.headMap[term[1]]
            return numpy.array(self.rlist[row_index][col])
        elif term[0] == dataFilterRule.TERM_CONST:
            return numpy.array(term[1])
        elif term[0] == dataFilterRule.TERM_INPUT:
            if '__' in term[2]: #looking for an element
                s = term[2].split('__',1)
                vkey = s[0]
                s = s[1]
                s = s.split('_')
                s = map(float, s)
                s = tuple(map(int, s))
                col = self.inputMap[term[1]][vkey]
                return self.resultElement(self.rlist[row_index], col, s)
            else:
                col = self.inputMap[term[1]][term[2]]
                return numpy.array(
                    self.rlist[row_index][col][self.timestep])
        elif term[0] == dataFilterRule.TERM_OUTPUT:
            if '__' in term[1]: #looking for an element
                s = term[2].split('__',1)
                vkey = s[0]
                s = s[1]
                s = s.split('_')
                s = map(float, s)
                s = tuple(map(int, s))
                col = self.inputMap[term[1]][vkey]
                return self.resultElement(self.rlist[row_index], col, s)
            else:
                col = self.outputMap[term[1]][term[2]]
                return numpy.array(
                    self.rlist[row_index][col][self.timestep])
        elif term[0] == dataFilterRule.TERM_INDEX:
            return numpy.array(row_index)
        raise Exception("Unrecognized flowsheet result data filter term")

    def dataFilterRuleEval(self, rule):
        n = len(self.rlist)
        test = [False]*n
        for i in range(n):
            test[i] = self.dataFilterRuleEval2(rule, i)
        return test

    def dataFilterRuleEval2(self, rule, row_index):
        '''
            Evaluate a filter rule
        '''
        #first get the two terms to compare if variables are arrays
        #comaprison must be true for all elements for rule to be true.
        t1 = self.dataFilterGetTerm(rule.term1, row_index)
        t2 = self.dataFilterGetTerm(rule.term2, row_index)
        test = numpy.array(False)
        if rule.op == rule.OP_TRUE:
            test = numpy.array(True)
        elif rule.op == rule.OP_FALSE:
            test = numpy.array(False)
        elif rule.op == rule.OP_EQ:
            if t1.dtype.char in ['S', 'a', 'U']:
                test = t1 == t2
            else:
                test = numpy.equal(t1, t2)
        elif rule.op == rule.OP_NEQ:
            if t1.dtype.char in ['S', 'a', 'U']:
                test = t1 != t2
            else:
                test = numpy.not_equal(t1, t2)
        elif rule.op == rule.OP_L:
            test = numpy.less(t1, t2)
        elif rule.op == rule.OP_G:
            test = numpy.greater(t1, t2)
        elif rule.op == rule.OP_LE:
            test = numpy.less_equal(t1, t2)
        elif rule.op == rule.OP_GE:
            test = numpy.greater_equal(t1, t2)
        elif rule.op == rule.OP_IN:
            t2_list = numpy.array(t2).tolist()
            if type(t2_list) != list:
                t2_list = [t2_list]
            test = numpy.array(t1.tolist() in t2_list)
        else:
            test = numpy.array(False)
            logging.getLogger("foqus." + __name__).error(
                    "Unknown rule type in data filter rule.")
        test = numpy.array(test)
        if rule.anyEl:
            test = test.any()
        else:
            test = test.all()
        return test

    def headersFromGraph(self):
        '''
            Create the header to layout the data from the graph
            if the graph matches the data already in the headers
            then nothing will be changed.

            If some chnage has been made, like a node or variable added
            or deleted, the headers will be rebuilt and all the old data
            will be deleted.  Changes like this probably mean that new
            data would not be compatable with the old, but also probably
            should do something to prevent unitentionally deleting data.
        '''
        gr = self.gr
        nodes = gr.nodes.keys()
        ni = []
        for nkey in gr.input:
            for vkey in gr.input[nkey]:
                ni.append((
                    nkey,
                    vkey,
                    gr.input[nkey][vkey].shape,
                    gr.input[nkey][vkey].dtype))
        no = []
        for nkey in gr.output:
            for vkey in gr.output[nkey]:
                no.append((
                    nkey,
                    vkey,
                    gr.output[nkey][vkey].shape,
                    gr.output[nkey][vkey].dtype))
        ns = []
        for nkey in gr.nodes:
            for vkey in gr.nodes[nkey].options.keys():
                ns.append((nkey, vkey))
        # Check if already right.  If so do nothing
        # Check Node list:
        nodes2 = self.nodeErrorMap.keys()
        if set(nodes) != set(nodes2):
            self.constructHead(nodes, ni, no, ns)
            return True
        # Check number of inputs
        if len(ni) != len(self.inputMapI):
            self.constructHead(nodes, ni, no, ns)
            return True
        # Check Number of outputs
        if len(no) != len(self.outputMapI):
            self.constructHead(nodes, ni, no, ns)
            return True
        # Check Number of node settings
        if len(ns) != len(self.nsettingsMapI):
            self.constructHead(nodes, ni, no, ns)
            return True
        # Check that input variables are the same
        for e in ni:
            try:
                if self.inputShape[e[0]][e[1]] != e[2] \
                    or self.inputType[e[0]][e[1]] != e[3]:
                    #different type or shape
                    self.constructHead(nodes, ni, no, ns)
                    return True
            except KeyError:
                #this probably means the variables are not the same
                self.constructHead(nodes, ni, no, ns)
                return True
        #check output variables
        for e in no:
            try:
                if self.outputShape[e[0]][e[1]] != e[2] \
                    or self.outputType[e[0]][e[1]] != e[3]:
                    #different type or shape
                    self.constructHead(nodes, ni, no, ns)
                    return True
            except KeyError:
                #this probably means the variables are not the same
                self.constructHead(nodes, ni, no, ns)
                return True
        #check node settings
        for e in ns:
            try:
                self.nsettingsMap[e[0]][e[1]]
            except KeyError:
                #this probably means the variables are not the same
                self.constructHead(nodes, ni, no, ns)
                return True
        return False # header not changed

    def constructHead(self, nodes, ni, no, ns):
        '''
            Make a header for results table.
            
            Args:
            nodes, list of node names (list of stings)
            ni, list of input variables each element is (node, var,
                shape, type) node and var are the node and variable name
                strings, shape is a tuple that is that variable array
                shape, and type is the data type
            no, list of output variables same form as ni
            ns, list of node settings each element is (node, setting)
                node is the node name and setting is the setting name
        '''
        self.clear()
        self.headMap['SetName'] = 0
        self.headMap['ResultName'] = 1
        self.headMap['Error'] = 2
        self.headMap['Time'] = 3
        self.headMap['ElapsedTime'] = 4
        self.headMap['SessionID'] = 5
        self.headMap['Tags'] = 6
        self.hiddenCols = ['Time', 'SessionID', 'Tags']
        i = 7
        # Add node error code columns
        for nkey in nodes:
            key = 'Error.{0}'.format(nkey)
            self.hiddenCols.append(key)
            self.headMap[key] = i
            self.nodeErrorMap[nkey] = i
            i += 1
        # Add node simulaion id columns
        for nkey in nodes:
            key = 'SimID.{0}'.format(nkey)
            self.hiddenCols.append(key)
            self.headMap[key] = i
            self.nodeSimIDMap[nkey] = i
            i += 1
        # Add input variables
        for v in ni:
            nkey = v[0]
            vname = v[1]
            vshape = v[2]
            vtype = v[3]
            self.headMap['Input.{0}.{1}'.format(nkey, vname)] = i
            if nkey not in self.inputMap:
                self.inputMap[nkey] = OrderedDict()
                self.inputShape[nkey] = {}
                self.inputSize[nkey] = {}
                self.inputType[nkey] = {}
            self.inputMap[nkey][vname] = i
            self.inputShape[nkey][vname] = vshape
            self.inputSize[nkey][vname] = self.product(vshape)
            self.inputType[nkey][vname] = vtype
            i += 1
        # Add Output variables
        for v in no:
            nkey = v[0]
            vname = v[1]
            vshape = v[2]
            vtype = v[3]
            self.headMap['Output.{0}.{1}'.format(nkey, vname)] = i
            if nkey not in self.outputMap:
                self.outputMap[nkey] = OrderedDict()
                self.outputShape[nkey] = {}
                self.outputSize[nkey] = {}
                self.outputType[nkey] = {}
            self.outputMap[nkey][vname] = i
            self.outputShape[nkey][vname] = vshape
            self.outputSize[nkey][vname] = self.product(vshape)
            self.outputType[nkey][vname] = vtype
            i += 1
        # Add Node Settings
        for s in ns:
            nkey = s[0]
            sname = s[1]
            key = 'NodeSetting.{0}.{1}'.format(nkey, sname)
            self.hiddenCols.append(key)
            self.headMap[key] = i
            if nkey not in self.nsettingsMap:
                self.nsettingsMap[nkey] = OrderedDict()
            self.nsettingsMap[nkey][sname] = i
            i += 1
        self.colSortOrder = range(len(self.headMap))
        #make the reverse headmap
        for h, c in self.headMap.iteritems():
            self.headMapI[c] = h
        for nkey, vdict in self.inputMap.iteritems():
            for vkey, c in vdict.iteritems():
                self.inputMapI[c] = (nkey, vkey)
        for nkey, vdict in self.outputMap.iteritems():
            for vkey, c in vdict.iteritems():
                self.outputMapI[c] = (nkey, vkey)
        for nkey, sdict in self.nsettingsMap.iteritems():
            for skey, c in sdict.iteritems():
                self.nsettingsMapI[c] = (nkey, skey)
        for nkey, c in self.nodeSimIDMap.iteritems():
            self.nodeSimIDMapI[c] = nkey
        for nkey, c in self.nodeErrorMap.iteritems():
            self.nodeErrorMapI[c] = nkey
        #set the column data types
        self.headType = [0]*len(self.headMap)
        for i in range(len(self.headType)):
            self.headType[i] = str
        #now just reset the columns that are not strings
        self.headType[self.headMap['Error']] = int
        self.headType[self.headMap['ElapsedTime']] = float
        self.headType[self.headMap['Tags']] = list
        for c in self.nodeErrorMapI:
            self.headType[c] = int
        for c, vkeys in self.inputMapI.iteritems():
            self.headType[c] = self.inputType[vkeys[0]][vkeys[1]]
        for c, vkeys in self.outputMapI.iteritems():
            self.headType[c] = self.outputType[vkeys[0]][vkeys[1]]

    def resultElement(self, row, cindex, eindex = ()):
        if type(row) == int:
            row = self.rlist[row]
        el = row[cindex]
        if len(eindex) == 0:
            eindex = None
        if cindex in self.inputMapI or cindex in self.outputMapI:
            el = el[self.timestep]
        if eindex != None and type(el).__module__ == numpy.__name__:
            el = el[eindex]
        elif eindex != None:
            for i in eindex:
                el = el[i]
        return el

    def resultElementSet(self, val, row, cindex, eindex = ()):
        '''
            Set an element in the results table.
            
            val = new value for cell
            row = row list (contains content for a table row)
            cindex = column index
            eindex = for variables that are arrays this is a tuple of
                the element index.  If empty () just set the cell 
                contents
        '''
        if len(eindex) == 0:
            eindex = None
        if cindex in self.inputMapI or cindex in self.outputMapI:
            if cindex in self.inputMapI:
                name = self.inputMapI[cindex]
                shp = self.inputShape[name[0]][name[1]]
            if cindex in self.outputMapI:
                name = self.outputMapI[cindex]
                shp = self.outputShape[name[0]][name[1]]  
            if eindex == None:
                if numpy.array(val).shape != shp:
                    return
                row[cindex][self.timestep] = val
            elif type(row[cindex][self.timestep]).\
                __module__ == numpy.__name__:
                if numpy.array(val).size != 1:
                    return
                row[cindex][self.timestep][eindex] = val
            else:
                l = row[cindex][self.timestep]
                for i in range(len(eindex)-1):
                    l = l[eindex[i]]
                l[eindex[-1]] = val
        else:
            if eindex == None:
                row[cindex] = val
            elif type(row[cindex]).__module__ == numpy.__name__:
                row[cindex][eindex] = val
            else:
                l = row[cindex][self.timestep]
                for i in range(len(eindex)-1):
                    l = l[eindex[i]]
                l[eindex[-1]] = val

    def indexToFlatIndex(self, shape, index):
        '''
            Convert an array variable index into a flat index

            shape: is a tuple that represents the shape of the array
            index: is a list or tuple of array indexes
        '''
        flat = 0
        for i, v in enumerate(index):
            s = 1
            for j in shape[i+1:]:
                s *= j
            flat += v*s
        return flat

    def flatIndexToIndex(self, shape, flat):
        '''
            Convert a flat index back to an array index

            shape is the sape of the array
            flat is the flat index integer
        '''
        index = [0]*len(shape)
        for i in range(len(shape)):
            s = 1
            for j in shape[i+1:]:
                s *= j
            index[i] = int(flat//s)
            flat = flat % s
        return tuple(index)

    def indexToString(self, index):
        '''
            Convert an array index to a string that can be appended to
            a variable name to represent a particular element in an
            array
        '''
        sep1 = '__' # the separator between var name and index string
        sep2 = '_' # the separator between indexes
        s = sep2.join(map(str, index))
        return sep1 + s

    def stringToIndex(self, s):
        '''
            Convert the string representation of an array index back to
            a list of integers that is the array index
        '''
        sep1 = '__' # the sperator between var name and index string
        sep2 = '_' # the seperator between indexes
        if sep1 not in s:
            return None
        si = string.rsplit(s, sep1, 1)[1]
        si = string.split(si, sep2)
        si = map(float, si)
        i = map(int, si)
        return i
        
    def inputSize(self, name1, name2=None):
        '''
            return the number of elements in an input array variable
            should return 1 for scalar
            
            args:
            name1 = node name or name in form "{node}.{variables}"
            name2 = variable name or None if jusing the dot form
        '''
        if name2 == None:
            name = string.split('.', 1)
            name1 = name[0]
            name2 = name[1]
        return self.product(self.inputShape[name1][name2])
            
    def outputSize(self, name1, name2=None):
        '''
            return the number of elements in an output array variable
            should return 1 for scalar
            
            args:
            name1 = node name or name in form "{node}.{variables}"
            name2 = variable name or None if jusing the dot form
        '''
        if name2 == None:
            name = string.split('.', 1)
            name1 = name[0]
            name2 = name[1]
        return self.product(self.outputShape[name1][name2])

    def product(self, t):
        p = 1
        for e in t:
            p *= e
        return p

    def makeEmptyResultRow(self):
        r = [None]*len(self.headMap)
        r[self.headMap['SetName']] = ""
        r[self.headMap['ResultName']] = ""
        r[self.headMap['Error']] = -1
        r[self.headMap['Time']] = ""
        r[self.headMap['ElapsedTime']] = 0.0
        r[self.headMap['SessionID']] = ""
        r[self.headMap['Tags']] = []
        for col in self.nodeErrorMapI:
            r[col] = -1
        for col in self.nodeSimIDMapI:
            r[col] = "None"
        for col, vkeys in self.inputMapI.iteritems():
            r[col] = [numpy.nan*numpy.ones(
                self.inputShape[vkeys[0]][vkeys[1]],
                dtype=self.headType[col])]
            r[col][0] = r[col][0].tolist()
        for col, vkeys in self.outputMapI.iteritems():
            r[col] = [numpy.nan*numpy.ones(
                self.outputShape[vkeys[0]][vkeys[1]],
                dtype=self.headType[col])]
            r[col][0] = r[col][0].tolist()
        for col in self.nsettingsMapI:
            r[col] = float('nan')
        return r
    
    def getVarColumn(self, name, pre='Output'):
        if isinstance(name, tuple) or isinstance(name, list):
            name = '.'.join(name)
        i = self.headMap['.'.join((pre, name))]
        l = [self.resultElement(r, i, ()) for r in self.rowSortOrder]
        return l

    def addResult(
        self,
        setName="None",
        name="Sample",
        sampleTime=None,
        eTime=0.0,
        errorCode=-1,
        sessionID=0,
        tags=[],
        nodeErrors={},
        nodeSid={},
        inputs={},
        outputs={},
        settings={},
        mult=1):
        '''
            This function adds a result to the result list and returns
            the index.

            arguments:
            setName - name of set the sample belongs to
            name - name of the sample
            sampleTime - time/date that sample completed or waas added
               either datatime object or ISO 8601 string
            eTime - the amount of time is seconds use to evaluate
            errorCode - the flowsheet error code
            sessionID - the FOQUS session unique id
            nodeErrors - dictionary of node error code, key is node name
            nodeSid - dict of simulation uids, key is node name
            inputs - dict of dict of input values, keys [node][var]
                     can be array values.  Values should be a time
                     series list.
            output - dict of dict of output values, keys [node][var]
                     can be array values
            settings - node settings dict of dicts, keys [node][setting]
        '''
        if sampleTime is None:
            sampleTime = datetime.datetime.utcnow()
        if isinstance(sampleTime, datetime.datetime):
            sampleTime = sampleTime.isoformat()
        r = [None]*len(self.headMap)
        r[self.headMap['SetName']] = setName
        r[self.headMap['ResultName']] = name
        r[self.headMap['Error']] = errorCode
        r[self.headMap['Time']] = sampleTime
        r[self.headMap['ElapsedTime']] = eTime
        r[self.headMap['SessionID']] = sessionID
        r[self.headMap['Tags']] = tags
        for col, nkey in self.nodeErrorMapI.iteritems():
            if nkey in nodeErrors:
                r[col] = nodeErrors[nkey]
            else:
                r[col] = -1
        for col, nkey in self.nodeSimIDMapI.iteritems():
            if nkey in nodeSid:
                r[col] = nodeSid[nkey]
            else:
                r[col] = "None"
        for col, vkeys in self.inputMapI.iteritems():
            if vkeys[0] in inputs and vkeys[1] in inputs[vkeys[0]]:
                r[col] = inputs[vkeys[0]][vkeys[1]]
            else:
                r[col] = [numpy.nan*numpy.ones(
                    self.inputShape[vkeys[0]][vkeys[1]],
                    dtype=self.headType[col])]
                r[col][0] = r[col][0].tolist()
        for col, vkeys in self.outputMapI.iteritems():
            if vkeys[0] in outputs and vkeys[1] in outputs[vkeys[0]]:
                r[col] = outputs[vkeys[0]][vkeys[1]]
            else:
                r[col] = [numpy.nan*numpy.ones(
                    self.outputShape[vkeys[0]][vkeys[1]],
                    dtype=self.headType[col])]
                r[col][0] = r[col][0].tolist()
        for col, skeys in self.nsettingsMapI.iteritems():
            nkey = skeys[0]
            skey = skeys[1]
            if nkey in settings and skey in settings[nkey]:
                r[col] = settings[nkey][skey]
            else:
                r[col] = float('nan')
        self.rlist.append(r)
        if self.curFilter in self.filters:
            df = self.filters[self.curFilter]
            if self.dataFilterEval2(df, len(self.rlist)-1):
                self.rowSortOrder.append(len(self.rlist)-1)
        else:
            self.rowSortOrder.append(len(self.rlist)-1)
        return(len(self.rlist)-1)

    def addFromSavedValues(
        self,
        setName = "1",
        name = 'result',
        sampleTime = None,
        valDict = {'input':{}, 'output':{}},
        tags = [],
        nodeSid={}):
        if valDict == None:
            # if there is no result just add an empty row with not run 
            # error not best but shows the run failed somehow, would be 
            # nice to have input, but currently if no valdict no way to 
            # get input here.
            try:
                self.addResult(setName=setName, name=name, errorCode=-1)
            except:
                logging.getLogger("foqus." + __name__).exception(
                    "Error adding a row for None valDict")
            return
        # If add a result from a graph make sure the header information
        # is up to date.  Unfortunatly have to extract information from
        # graph and check that it matches the current heder info to know
        # if headers need reconstructed.  This is a potential area for
        # imporvement.  One simple thing would be to allow for adding a
        # list of savedValue dicts.  Other more complicated things could
        # track when graph has been changed
        self.headersFromGraph()
        #
        inputs = valDict.get('input', {})
        outputs = valDict.get('output', {})
        settings = valDict.get('nodeSettings', {})
        errorCode = valDict.get('graphError', -1)
        nodeErrors = valDict.get('nodeError', {})
        eTime = valDict.get('solTime', 0.0)
        sessionID = valDict.get('session', 0)
        tags = copy.copy(tags)
        tm = valDict.get("turbineMessages", None)
        tmtag = []
        if tm is not None:
            for nkey, tme in tm.iteritems():
                if tme != "" and tme is not None:
                    tmtag.append("{0} Turbine Msg: {1}".format(nkey, tme))
        tags.extend(tmtag)
        if valDict.get('resub', 0) > 0:
            tags.append("resub {0}".format(valDict['resub']))
        jid = valDict.get('Id', None)
        if jid is not None:
            tags.append("Job {0}".format(jid))
        if sampleTime is None:
            sampleTime = datetime.datetime.utcnow()
        if isinstance(sampleTime, datetime.datetime):
            sampleTime = sampleTime.isoformat()
        r = [None]*len(self.headMap)
        r[self.headMap['SetName']] = setName
        r[self.headMap['ResultName']] = name
        r[self.headMap['Error']] = errorCode
        r[self.headMap['Time']] = sampleTime
        r[self.headMap['ElapsedTime']] = eTime
        r[self.headMap['SessionID']] = sessionID
        r[self.headMap['Tags']] = tags
        for col, nkey in self.nodeErrorMapI.iteritems():
            if nkey in nodeErrors:
                r[col] = nodeErrors[nkey]
            else:
                r[col] = -1
        for col, nkey in self.nodeSimIDMapI.iteritems():
            if nkey in nodeSid:
                r[col] = nodeSid[nkey]
            else:
                r[col] = "None"
        for col, vkeys in self.inputMapI.iteritems():
            if vkeys[0] in inputs and vkeys[1] in inputs[vkeys[0]]:
                r[col] = inputs[vkeys[0]][vkeys[1]]
            else:
                r[col] = [numpy.nan*numpy.ones(
                    self.inputShape[vkeys[0]][vkeys[1]],
                    dtype=self.headType[col])]
        for col, vkeys in self.outputMapI.iteritems():
            if vkeys[0] in outputs and vkeys[1] in outputs[vkeys[0]]:
                r[col] = outputs[vkeys[0]][vkeys[1]]
            else:
                r[col] = [numpy.nan*numpy.ones(
                    self.outputShape[vkeys[0]][vkeys[1]],
                    dtype=self.headType[col])]
        for col, skeys in self.nsettingsMapI.iteritems():
            nkey = skeys[0]
            skey = skeys[1]
            if nkey in settings and skey in settings[nkey]:
                r[col] = settings[nkey][skey]
            else:
                r[col] = numpy.nan
        self.rlist.append(r)
        if self.curFilter in self.filters:
            df = self.filters[self.curFilter]
            if self.dataFilterEval2(df, len(self.rlist)-1):
                self.rowSortOrder.append(len(self.rlist)-1)
        else:
            self.rowSortOrder.append(len(self.rlist)-1)
        return(len(self.rlist)-1)

    def saveDict(self):
        sd = {
            'headMap': self.headMap,
            'hiddenCols': self.hiddenCols,
            'headType': self.headType,
            'inputShape': self.inputShape,
            'outputShape': self.outputShape,
            'timestep': self.timestep,
            'curFileter': '',
            'filters': {},
            'rlist': self.rlist
        }
        for key, fltr in self.filters.iteritems():
            sd['filters'][key] = fltr.saveDict()
        for i, t in enumerate(sd['headType']):
            if t == int:
                typ_str = 'int'
            elif t == float:
                typ_str = 'float'
            elif t == str:
                typ_str = 'str'
            elif t == list: 
                # only tags column is list type
                # tags should be strings
                typ_str = 'list'
            else:
                #it probably float so if no valid type assume float
                typ_str = 'float'
            sd['headType'][i] = typ_str
        return sd

    def loadDict(self, sd):
        self.clear()
        for key, fltr in sd['filters'].iteritems():
            df = dataFilter()
            df.loadDict(fltr)
            self.filters[key] = df
        try:
            self.headMap = sd['headMap'] #there has to be a head map
        except:
            logging.getLogger("foqus." + __name__).debug(
                "error loading saved data, missing head map")
            return
        self.hiddenCols = sd.get('hiddenCols', [])
        self.timestep = sd.get('timestep', 0)
        self.colSortOrder = range(len(self.headMap))
        self.headType = sd['headType']
        for i, typ_str in enumerate(self.headType):
            if typ_str == 'str':
                self.headType[i] = str
            elif typ_str == 'float':
                self.headType[i] = float
            elif typ_str == 'int':
                self.headType[i] = int
            elif typ_str == 'list':
                self.headType[i] = list
            else:
                self.headType[i] = float
        for ckey, c in self.headMap.iteritems():
            if ckey[:6] == 'Error.':
                nkey = ckey[6:]
                self.nodeErrorMap[nkey] = c
            elif ckey[:6] == 'SimID.':
                nkey = ckey[6:]
                self.nodeSimIDMap[nkey] = c
            elif ckey[:6] == 'Input.':
                [nkey, vkey] = ckey[6:].split('.' ,1)
                if nkey not in self.inputMap:
                    self.inputMap[nkey] = OrderedDict()
                    self.inputShape[nkey] = {}
                    self.inputSize[nkey] = {}
                    self.inputType[nkey] = {}
                self.inputMap[nkey][vkey] = c
                shape = tuple(sd['inputShape'][nkey][vkey])
                self.inputShape[nkey][vkey] = shape
                self.inputSize[nkey][vkey] = self.product(shape)
                self.inputType[nkey][vkey] = self.headType[c]
            elif ckey[:7] == 'Output.':
                [nkey, vkey] = ckey[7:].split('.' ,1)
                if nkey not in self.outputMap:
                    self.outputMap[nkey] = OrderedDict()
                    self.outputShape[nkey] = {}
                    self.outputSize[nkey] = {}
                    self.outputType[nkey] = {}
                self.outputMap[nkey][vkey] = c
                shape = tuple(sd['outputShape'][nkey][vkey])
                self.outputShape[nkey][vkey] = shape
                self.outputSize[nkey][vkey] = self.product(shape)
                self.outputType[nkey][vkey] = self.headType[c]
            elif ckey[:12] == 'NodeSetting.':
                [nkey, skey] = ckey[12:].split('.' ,1)
                if nkey not in self.nsettingsMap:
                    self.nsettingsMap[nkey] = OrderedDict()
                self.nsettingsMap[nkey][skey] = c
        for h, c in self.headMap.iteritems():
            self.headMapI[c] = h
        for nkey, vdict in self.inputMap.iteritems():
            for vkey, c in vdict.iteritems():
                self.inputMapI[c] = (nkey, vkey)
        for nkey, vdict in self.outputMap.iteritems():
            for vkey, c in vdict.iteritems():
                self.outputMapI[c] = (nkey, vkey)
        for nkey, sdict in self.nsettingsMap.iteritems():
            for skey, c in sdict.iteritems():
                self.nsettingsMapI[c] = (nkey, skey)
        for nkey, c in self.nodeSimIDMap.iteritems():
            self.nodeSimIDMapI[c] = nkey
        for nkey, c in self.nodeErrorMap.iteritems():
            self.nodeErrorMapI[c] = nkey
        self.rlist = sd['rlist']
        self.setFilter(sd.get('curFilter', None))

    def constructFlatHead(self, sort=False, force=True):
        self.headStringsFlat = []
        self.headMapFlat = []
        if self.__flat_sort__ != sort:
            self.__flat_valid__ = False
        if self.__flat_valid__ and not force:
            return
        for c in self.colSortOrder:
            if c in self.inputMapI:
                nkey = self.inputMapI[c][0]
                vkey = self.inputMapI[c][1]
                if self.inputSize[nkey][vkey] > 1:
                    for i in range(self.inputSize[nkey][vkey]):
                        vshape = self.inputShape[nkey][vkey]
                        index = self.flatIndexToIndex(vshape, i)
                        istr = self.indexToString(index)
                        self.headStringsFlat.append(
                            self.headMap.keys()[c]+istr)
                        self.headMapFlat.append((c, index))
                else:
                    self.headStringsFlat.append(self.headMap.keys()[c])
                    self.headMapFlat.append((c, ()))
            elif c in self.outputMapI:
                nkey = self.outputMapI[c][0]
                vkey = self.outputMapI[c][1]
                if self.outputSize[nkey][vkey] > 1:
                    for i in range(self.outputSize[nkey][vkey]):
                        vshape = self.outputShape[nkey][vkey]
                        index = self.flatIndexToIndex(vshape, i)
                        istr = self.indexToString(index)
                        self.headStringsFlat.append(
                            self.headMap.keys()[c]+istr)
                        self.headMapFlat.append((c, index))
                else:
                    self.headStringsFlat.append(self.headMap.keys()[c])
                    self.headMapFlat.append((c, ()))
            else:
                self.headStringsFlat.append(self.headMap.keys()[c])
                self.headMapFlat.append((c, ()))
        self.__flat_valid__ = True
        self.__flat_sort__ = sort

    def dumpCSV(self, fileName='test.csv'):
        if self.flatTable:
            self.exportCSV(fileName, flat=True)
        else:
            self.exportCSV(fileName, flat=False)

    def dumpString(self, fileName='test.csv'):
        if self.flatTable:
            return self.exportCSVString(fileName, flat=True)
        else:
            return self.exportCSVString(fileName, flat=False)

    def exportVarsCVS(self, fileName, inputs=[], outputs=[], flat=True):
        '''
            Explort input and output varialbe values to a csv file
            
            args:
            fileName -- name of csv file
            inputs -- list of strings, input variable names to export
            outputs -- list of strings, output variable names to export
            flat -- Ture to export elements of array variable in their
               own columm
            
            no return value
        '''
        headRow = []
        headRowIndex = []
        if flat:
            self.constructFlatHead()
            for var in inputs:
                key = var.split('.', 1)
                nkey = key[0]
                vkey = key[1]
                shp = self.inputShape[nkey][vkey]
                sz = self.inputSize[nkey][vkey]
                if sz > 1:
                    pass
                else:
                    headRow.append(var)
                    headRowIndex.append(
                        [self.inputMap[nkey][vkey], ()])
            for var in outputs:
                key = var.split('.', 1)
                nkey = key[0]
                vkey = key[1]
                shp = self.outputShape[nkey][vkey]
                sz = self.outputSize[nkey][vkey]
                if sz > 1:
                    pass
                else:
                    headRow.append(var)
                    headRowIndex.append(
                        [self.outputMap[nkey][vkey], ()])
        else:
            for var in inputs:
                key = var.split('.', 1)
                nkey = key[0]
                vkey = key[1]
                headRow.append(var)
                headRowIndex.append([self.inputMapI[nkey][vkey]])
                w.writerow(headRow)
            for var in outputs:
                key = var.split('.', 1)
                nkey = key[0]
                vkey = key[1]
                headRow.append(var)
                headRowIndex.append([self.outputMapI[nkey][vkey]])
        with open(fileName, 'wb') as csvfile:
            w = csv.writer(csvfile)
            w.writerow(headRow)
            for rindex in self.rowSortOrder:
                r = self.rlist[rindex]
                row = [numpy.nan]*len(headRowIndex)
                for i, m in enumerate(headRowIndex):
                    row[i] = self.resultElement(r, m[0], ())
                w.writerow(row)
        
    def exportCSV(self, fileName, flat=True):
        '''
            Export results to a CSV file.
            
            args:
            fileName -- name of csv file
            flat -- if flat export arrays with a column for each element
                if not flat the whole array will be places in a single
                column.
        '''
        if flat:
            self.constructFlatHead()
            with open(fileName, 'wb') as csvfile:
                w = csv.writer(csvfile)
                w.writerow(self.headStringsFlat)
                for rindex in self.rowSortOrder:
                    r = self.rlist[rindex]
                    row = [numpy.nan]*len(self.headMapFlat)
                    for i, m in enumerate(self.headMapFlat):
                        row[i] = self.resultElement(r, m[0], m[1])
                        if type(row[i]) == list:
                            row[i] = json.dumps(row[i])
                    w.writerow(row)
        else:
            headrow = ['']*len(self.colSortOrder)
            for c in self.colSortOrder:
                headrow[c] = self.headMapI[c]
            with open(fileName, 'wb') as csvfile:
                w = csv.writer(csvfile)
                w.writerow(headrow)
                for rindex in self.rowSortOrder:
                    r = self.rlist[rindex]
                    row = [numpy.nan]*len(self.colSortOrder)
                    for i, m in enumerate(self.colSortOrder):
                        row[i] = json.dumpsself.resultElement(r, m, ())
                        if type(row[i]).__module__ == numpy.__name__:
                            row[i] = row[i].tolist()
                        if type(row[i]) == list:
                            row[i] = json.dumps(row[i])
                    w.writerow(row)

    def exportCSVString(self, fileName='test.csv', flat=True):
        s = []
        if flat:
            self.constructFlatHead()
            s.append('\t'.join(self.headStringsFlat))
            for rindex in self.rowSortOrder:
                r = self.rlist[rindex]
                row = [numpy.nan]*len(self.headMapFlat)
                for i, m in enumerate(self.headMapFlat):
                    row[i] = self.resultElement(r, m[0], m[1])
                if type(row[i]) == list:
                    row[i] = json.dumps(row[i])
                s.append('\t'.join(map(str,row)))
        else:
            headrow = ['']*len(self.colSortOrder)
            for c in self.colSortOrder:
                headrow[c] = self.headMapI[c]
            s.append('\t'.join(headrow))
            for rindex in self.rowSortOrder:
                r = self.rlist[rindex]
                row = [numpy.nan]*len(self.colSortOrder)
                for i, m in enumerate(self.colSortOrder):
                    row[i] = self.resultElement(r, m, ())
                    if type(row[i]).__module__ == numpy.__name__:
                        row[i] = row[i].tolist()
                    if type(row[i]) == list:
                        row[i] = json.dumps(row[i])
                s.append('\t'.join(map(str,row)))
        s = '\n'.join(s)
        return s

    @staticmethod
    def approxEqual(x, y, sig=5, zeroTol = 1e-200):
        if x==y:
            # exacly same
            return True
        elif abs(x) < zeroTol and abs(y) < zeroTol:
            # both zero
            return True
        ezero = int(math.log10(abs(zeroTol)))
        # Calculate sicentific notation exp if to small use zero tol
        if abs(x) > 1e-200:
            e1 = int(math.floor(math.log10(abs(x))))
        else:
            e1 = int(math.floor(math.log10(abs(zeroTol))))
        if abs(y) > 1e-200:
            e2 = int(math.floor(math.log10(abs(y))))
        else:
            e2 = int(math.floor(math.log10(abs(zeroTol))))
        return abs(x-y)*10**int((sig - max(e1,e2))) < 1
        
    def exportPSUADE(self, fileName='test.dat'):
        self.constructFlatHead(sort=False)
        samplen = self.rowCount(filtered=True)
        inputn = 0
        outputn=0
        for col, name in self.inputMapI.iteritems():
            inputn += self.inputSize[name[0]][name[1]]
        for col, name in self.outputMapI.iteritems():
            outputn += self.outputSize[name[0]][name[1]]
        input_index = 0
        output_index = 0
        inputNames = ['']*inputn
        outputNames = ['']*outputn
        inputValues = [0]*samplen
        outputValues = [0]*samplen
        for si in range(samplen):
            inputValues[si] = [numpy.nan]*inputn
            outputValues[si] = [numpy.nan]*outputn
            inputMin = [numpy.nan]*inputn
            inputMax = [numpy.nan]*inputn
        error = ['1']*samplen
        for i, el in enumerate(self.headMapFlat):
            col = el[0]
            elIndex = el[1]
            if col in self.inputMapI:
                #Strip the 'Input.' off from of name
                inputNames[input_index] = self.headStringsFlat[i][6:]
                for si, rindex in enumerate(self.rowSortOrder):
                    row = self.rlist[rindex]
                    inputValues[si][input_index] = \
                        self.resultElement(row, col, elIndex)
                    if si == 0:
                        inputMin[input_index]=inputValues[si][input_index]
                        inputMax[input_index]=inputValues[si][input_index]
                    elif inputValues[si][input_index]<inputMin[input_index]:
                        inputMin[input_index]=inputValues[si][input_index]
                    elif inputValues[si][input_index]>inputMax[input_index]:
                        inputMax[input_index]=inputValues[si][input_index]
                input_index += 1
            elif col in self.outputMapI:
                #Strip the 'Output.' off name
                outputNames[output_index] = self.headStringsFlat[i][7:]
                for si, rindex in enumerate(self.rowSortOrder):
                    row = self.rlist[rindex]
                    outputValues[si][output_index] = \
                        self.resultElement(row, col, elIndex)
                output_index +=1
            elif col == self.headMap['Error']:
                for si, rindex in enumerate(self.rowSortOrder):
                    row = self.rlist[rindex]
                    error[si] = self.resultElement(row, col, elIndex)
        #get the number of inputs that are fixed or variable.
        v = [False]*inputn
        nvar = 0
        for i, name in enumerate(inputNames):
            if not self.approxEqual(inputMin[i], inputMax[i], sig=6):
                nvar += 1
                v[i] = True
        with open(fileName, 'w') as f:
            f.write("#NAMESHAVENODES\n")
            f.write("PSUADE_IO\n")
            f.write("{0} {1} {2}\n".format(nvar, outputn, samplen))
            for si in range(samplen):
                if not error[si]:
                    hasRun = 1
                else:
                    hasRun = 0
                f.write("{0} {1}\n".format(si+1, hasRun))
                for i in range(inputn):
                    if v[i]:
                        f.write('{0}\n'.format(inputValues[si][i]))
                for i in range(outputn):
                    f.write('{0}\n'.format(outputValues[si][i]))
            f.write("PSUADE_IO\n")
            f.write("PSUADE\n")
            f.write("INPUT\n")
            f.write("\tnum_fixed = {0}\n".format(inputn-nvar))
            f.write("\tdimension = {0}\n".format(nvar))
            for i, name in enumerate(inputNames):
                if not v[i]:
                    f.write('\tfixed {0} {1} = {2}\n'.format(
                        i+1, name, inputMin[i]))
                else:
                    f.write('\tvariable {0} {1} = {2} {3}\n'.format(
                        i+1, name, inputMin[i], inputMax[i]))
            f.write("END\n")
            f.write("OUTPUT\n")
            f.write("\tdimension = {0}\n".format(outputn))
            for i, name in enumerate(outputNames):
                f.write('\tvariable {0} {1}\n'.format(i+1, name))
            f.write("END\n")
            f.write("END\n")

    def importCSV(self, fileName='test.csv', overwrite=True, flat=True):
        sampleNameCol = None
        setNameCol = None
        with open(fileName, 'rb') as f:
            csvreader = csv.reader(f, delimiter=",")
            rowcount = 0
            for row in csvreader:
                rowcount += 1
        with open(fileName, 'rb') as f:
            csvreader = csv.reader(f, delimiter=",")
            dataHead = csvreader.next() #get the header
            valmap = [None]*len(dataHead)
            if flat:
                self.constructFlatHead(sort=False)
                for i, h in enumerate(dataHead):
                    if overwrite == True and h == 'SetName':
                        setNameCol = i
                    elif overwrite == True and h == 'ResultName':
                        sampleNameCol = i
                    try:
                        col = self.headStringsFlat.index(h)
                        valmap[i] = self.headMapFlat[col]
                    except:
                        pass
            else:
                for i, h in enumerate(dataHead):
                    if overwrite == True and h == 'SetName':
                        setNameCol = i
                    elif overwrite == True and h == 'ResultName':
                        sampleNameCol = i
                    try:
                        valmap[i] = [self.headMap.keys().index(h), ()]
                    except:
                        pass
            # Now I have the csv file columns mapped to stored data
            gotType = False
            typ = {}
            typ2 = {}
            mtrow = self.makeEmptyResultRow()
            lastIndex = 0
            newrows = [0]*rowcount
            for row in csvreader:
                ri = None
                if sampleNameCol != None and setNameCol != None:
                    sampleName = row[sampleNameCol]
                    setName = row[setNameCol]
                    for j, r in enumerate(self.rlist):
                        if setName == r[self.headMap['SetName']] and\
                            sampleName == r[self.headMap['ResultName']]:
                            ri = j
                if ri == None:
                    ri = len(self.rlist)
                    result = copy.deepcopy(mtrow)
                    newrows[lastIndex] = result
                    lastIndex += 1
                else:
                    result = self.rlist[ri]
                for i, item in enumerate(row):
                    if valmap[i] != None:
                        #read strings from csv so need to convert
                        #to proper data type.
                        col = valmap[i][0]
                        if not gotType:
                            typ[col] = self.getTyp(item)
                        if typ[col] != None:
                            # this is a type the json parser can 
                            # probably handle.  otherwise assume
                            # un-quoted string
                            item = json.loads(item)
                        if typ[col] == list and len(item) > 0:
                            typ2[col] = self.getTyp(item[0])
                        t2 = typ2.get(col, None)
                        if typ[col]==list and (t2==int or t2==float):
                            item = numpy.array(item, dtype=typ2[col])
                        self.resultElementSet(
                            item,
                            result,
                            valmap[i][0],
                            valmap[i][1])
                gotType = True
        self.rlist = self.rlist + newrows[0:lastIndex]
        self.setFilter(self.curFilter)
    
    @staticmethod
    def getTyp(s):
        if re.match("^[-0-9]*[e]?[-0-9]*[0-9]$", s):
            return int
        elif re.match("^[-.0-9][0-9]*[.]?[e]?[-0-9]?[0-9]*[0-9.]$", s):
            return float
        elif re.match("^[\\[].*[\\]]$", s):
            return list
        elif re.match('^["].*["]$', s):
            return str
        else:
            return None

    def importCSVString(self, s, overwrite=True, flat=True):
        s = s.strip()
        s = s.split('\n')
        dataHead = s[0].split('\t')
        sampleNameCol = None
        setNameCol = None
        valmap = [None]*len(dataHead)
        if flat:
            self.constructFlatHead(sort=False)
            for i, h in enumerate(dataHead):
                if overwrite == True and h == 'SetName':
                    setNameCol = i
                elif overwrite == True and h == 'ResultName':
                    sampleNameCol = i
                try:
                    col = self.headStringsFlat.index(h)
                    valmap[i] = self.headMapFlat[col]
                except:
                    pass
        else:
            for i, h in enumerate(dataHead):
                if overwrite == True and h == 'SetName':
                    setNameCol = i
                elif overwrite == True and h == 'ResultName':
                    sampleNameCol = i
                try:
                    valmap[i] = [self.headMap.keys().index(h), ()]
                except:
                    pass
        # Now I have the csv file columns mapped to stored data
        gotType = False
        typ = {}
        typ2 = {}
        mtrow = self.makeEmptyResultRow()
        lastIndex = 0
        newrows = [0]*len(s)
        for row in s[1:]:
            row = row.split('\t')
            ri = None
            if sampleNameCol != None and setNameCol != None:
                sampleName = row[sampleNameCol]
                setName = row[setNameCol]
                for j, r in enumerate(self.rlist):
                    if setName == r[self.headMap['SetName']] and\
                        sampleName == r[self.headMap['ResultName']]:
                        ri = j
            if ri == None:
                ri = len(self.rlist)
                result = copy.deepcopy(mtrow)
                newrows[lastIndex] = result
                lastIndex += 1
            else:
                result = self.rlist[ri]
            for i, item in enumerate(row):
                if valmap[i] != None:
                    #read strings from csv so need to convert
                    #to proper data type.
                    col = valmap[i][0]
                    if not gotType:
                        typ[col] = self.getTyp(item)
                    if typ[col] != None:
                        # this is a type the json parser can 
                        # probably handle.  otherwise assume
                        # un-quoted string
                        item = json.loads(item)
                    if typ[col] == list and len(item) > 0:
                        typ2[col] = self.getTyp(item[0])
                    t2 = typ2.get(col, None)
                    if typ[col]==list and (t2==int or t2==float):
                        item = numpy.array(item, dtype=typ2[col])
                    self.resultElementSet(
                        item,
                        result,
                        valmap[i][0],
                        valmap[i][1])
            gotType = True
        self.rlist = self.rlist + newrows[0:lastIndex]
        self.setFilter(self.curFilter)

    def importPSUADE(self):
        pass

if __name__ == '__main__':
    r = results()
    r.constructHead(
        ['node1', 'node2'],
        ni = [
            ['node1', 'x1', (2,2), float],
            ['node2', 'x2', (), float]],
        no = [
            ['node1', 'y1', (), float],
            ['node2', 'y2', (), float]],
        ns = [
            ['node1', 'homotopy']])
    r.addResult(
        setName="TestSet",
        name="Sample1",
        sampleTime=datetime.datetime.utcnow(),
        eTime=100,
        errorCode=0,
        sessionID="0",
        tags = ['toast', 'doctor'],
        nodeErrors={
            'node1': 0,
            'node2': 1},
        nodeSid={
            'node1': "None",
            'node2': "None"},
        inputs={
            'node1':{'x1':[numpy.array([[1.1, 1.2],[1.3, 1.4]])]},
            'node2':{'x2':[numpy.array(2.2)]}},
        outputs={
            'node1':{'y1':[numpy.array(0.1)]},
            'node2':{'y2':[numpy.array(0.2)]}},
        settings={
            'node1':{'homotopy':1}})

    r.exportCSV(flat=True)
    r.exportPSUADE()
    r.importCSV(flat=True)
    r.exportCSV(fileName='test2.csv', flat=False)
    r.importCSV(fileName='test2.csv', flat=False, overwrite=False)
    r.exportCSV(fileName='test3.csv', flat=True)
    s = r.exportCSVString(flat=True)
    s = r.importCSVString(s, flat=True)
    r.exportCSV(fileName='test4.csv', flat=True)
    r.loadDict(r.saveDict())
    r.exportCSV(fileName='test5.csv', flat=True)

    dfilter = dataFilter()
    rule = dataFilterRule()
    rule2 = dataFilterRule()

    rule.term1 = [rule.TERM_INPUT, 'node1', 'x1__1_0']
    rule.term2 = [rule.TERM_CONST, 2.0]
    rule.op = rule.OP_L

    rule2.term1 = [rule2.TERM_INPUT, 'node1', 'x1__0_0']
    rule2.term2 = [rule2.TERM_CONST, 2.0]
    rule2.op = rule2.OP_L

    dfilter.fstack.append([dfilter.DF_RULE, rule])
    dfilter.fstack.append([dfilter.DF_RULE, rule2])
    dfilter.fstack.append([dfilter.DF_XOR])

    print numpy.array(r.dataFilterEval(dfilter))
