"""results.py

* This contains the class for sample results data heading

John Eslick, Carnegie Mellon University, 2014
See LICENSE.md for license and copyright details.
"""

import numpy as np
import pandas as pd
import re
import StringIO
import json
import datetime
import logging
import time

class dataFilter(object):
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
        return self

class dataFilterRule(object):
    OP_EQ = 0
    OP_L = 1
    OP_G = 2
    OP_LE = 3
    OP_GE = 4
    OP_IN = 5
    OP_NEQ = 6
    OP_AEQ = 7
    OP_TRUE = 11
    OP_FALSE = 12

    def __init__(self, op=0):
        self.op = op
        self.term1 = 'err'
        self.term2 = 0

    def saveDict(self):
        sd = {
            'op':self.op,
            'term1':self.term1,
            'term2':self.term2}
        return sd

    def loadDict(self, sd):
        self.op = sd['op']
        self.term1 = sd['term1']
        self.term2 = sd['term2']

def iso_time_str():
    return str(datetime.datetime.utcnow().isoformat())

def sd_col_list(sd, time=None):
    """
    Take a value dict saved from results and turn it into a list of columns
    labels and data
    """
    if time is None: time = iso_time_str()
    columns = ["time", "solution_time", "err"]
    dat = [time, sd["solTime"], sd["graphError"]]

    # input, output, and node settings columns
    for s in [["input"]*2, ["output"]*2, ["nodeSettings", "setting"]]:
        for n, d in sd[s[0]].iteritems():
            for v in d:
                columns.append("{}.{}.{}".format(s[1], n, v))
                el = sd[s[0]][n][v]
                if s[1] == "setting":
                    el = repr(el)
                dat.append(el)
    #node error and turbine messages columns
    for s in [["nodeError", "node_err"], ["turbineMessages", "turb"]]:
        for n in sd[s[0]]:
            columns.append("{}.{}".format(s[1], n))
            dat.append(sd[s[0]][n])
    # return the list of of columns and list of associated data.
    return (columns, dat)

def incriment_name(name, exnames):
    """
    Check if a name is already in a list of names. If it is generate a new
    unique name by adding an incimenting number at the end.
    """
    if not name in exnames:
        return name # name is already new
    index = 1
    for n in exnames:
        m = re.match(r"^%s_([0-9]+)$" % name, n)
        if m:
            i = int(m.group(1))
            if i >= index: index = i + 1
        else:
            "".join([name, "_", str(index).zfill(4)])
    return "".join([name, "_", str(index).zfill(4)])

def search_term_list(st):
    if st.startswith('['):
        try:
            st = json.loads(st)
        except:
            logging.getLogger("foqus." + __name__).exception(
                "Error reading filer sort terms")
            raise Exception('Error reading sort terms. When using multiple sort'
                'terms, enclose the column names in "". See log for deatils')
    else:
        st = [st]
    ascend = [True]*len(st)
    for i, t in enumerate(st):
        if t.startswith('-'):
            st[i] = t[1:]
            ascend[i] = False
    return st, ascend

class Results(pd.DataFrame):
    def __init__(self, *args, **kwargs):
        super(Results, self).__init__(*args, **kwargs)
        self.filters = None # do this to avoid set column from attribute warn
        self.filters = {} # now that atribute exists set to empty dict
        self.filters["none"] = \
            dataFilter().loadDict({"fstack":[[10,{"term2":0,"term1":1,"op":0}]]})
        self.filters["all"] = dataFilter()
        self._current_filter = None
        self._filter_indexes = None # avoid set column from attribute warn
        self._filter_indexes = [] # now that atribute exists set to empty list
        self.flatTable = True
        self["set"] = []
        self["result"] = []
        self._filter_mask = None

    def incrimentSetName(self, name):
        return incriment_name(name, list(self["set"]))

    def set_filter(self, fltr=None):
        """
        Set the current filter name, can be None for no filter
        """
        self._current_filter = fltr
        self.update_filter_indexes()

    def update_filter_indexes(self):
        """
        Apply the filter to the data to get a list of indexes of data rows that
        match filter.
        """
        self._filter_indexes, self._filter_mask = self.filter_indexes()

    def current_filter(self):
        """
        Get the name of the currently set data filter.
        """
        return self._current_filter

    def get_indexes(self, filtered=False):
        """
        Get a list of row indexes, if filtered use filtered indexes else return
        all row indexes.
        """
        if filtered:
            return self._filter_indexes
        else:
            return list(self.index)

    def copy_dataframe(self, filtered=False):
        if filtered:
            self.update_filter_indexes()
            return pd.DataFrame(self[self._filter_mask])
        else:
            return pd.DataFrame(self)

    def saveDict(self):
        """
        Save the data to a dict that can be dumped to json
        """
        sd = {
            "__columns":list(self.columns),
            "__indexes":list(self.index),
            "__filters":{},
            "__current_filter":self._current_filter}
        for f in self.filters:
            sd["__filters"][f] = self.filters[f].saveDict()
        for i in self.index:
            sd[i] = list(self.loc[i])
        return sd

    def loadDict(self, sd):
        """
        Load the data from a dict, the dict can be read from json
        """
        self.filters = {}
        self._current_filter = sd.get("__current_filter", None)
        self.drop(self.index, inplace=True)
        self.drop(self.columns, axis=1, inplace=True)
        self["set"] = []
        self["result"] = []
        try:
            columns = sd["__columns"]
            for c in columns:
                self[c] = []
            for i in sd["__indexes"]:
                self.loc[i] = sd[str(i)]
        except:
            logging.getLogger("foqus." + __name__).exception(
                "Error loading stored results")
        for i in sd.get("__filters", []):
            self.filters[i] = dataFilter().loadDict(sd["__filters"][i])

        if "none" not in self.filters:
            self.filters["none"] = \
                dataFilter().loadDict({"fstack":[[10,{"term2":0,"term1":1,"op":0}]]})
        if "all" not in self.filters:
            self.filters["all"] = dataFilter()
        self.update_filter_indexes()

    def data_sets(self):
        """Return a set of data set labels"""
        return set(self.loc[:,"set"])

    def addFromSavedValues(self, setName, name, time=None, valDict=None):
        """Temoprary function for compatablility
        should move to add_result()
        """
        self.add_result(valDict, set_name=setName, result_name=name, time=time)

    def add_result(self, sd, set_name="default", result_name="res", time=None):
        """
        Add a set of flowseheet results to the data frame
        """
        if len(self["set"]) > 0:
            names = list(self.loc[self["set"] == set_name].loc[:,"result"])
        else:
            names = []
        result_name = incriment_name(result_name, names)
        columns, dat = sd_col_list(sd, time=time)
        for c in columns:
            if c not in self.columns:
                self[c] = [np.nan]*self.count_rows(filtered=False)
        row = self.count_rows(filtered=False)
        self.loc[row, "set"] = set_name
        self.loc[row, "result"] = result_name
        for i, col in enumerate(columns):
            self.loc[row, col] = dat[i]
        self.update_filter_indexes()

    def read_csv(self, *args, **kwargs):
        """
        Read results into a data frame from a CSV file.
        """
        s = kwargs.pop("s", None)
        if s is not None:
            path = StringIO.StringIO(s)
            kwargs["filepath_or_buffer"] = path
        df = pd.read_csv(*args, **kwargs)
        col_del = []
        row = self.count_rows(filtered=False)
        for r in df.index:
            row += 1
            for c in df.columns:
                self.loc[row, c] = df.loc[r, c]
        self.update_filter_indexes()

    def count_rows(self, filtered=True):
        """
        Return the number of rows in a table. If filtered the number of rows in
        the data frame that match the filter.
        """
        return len(self.get_indexes(filtered=filtered))

    def count_cols(self):
        """
        Return the number of columns in the data frame
        """
        return len(self.columns)

    def filter_term(self, t):
        """
        Return the value of a filter term. Array for all rows.
        """
        if t in self.columns:
            return np.array(list(self.loc[:, t]))
        else:
            return np.array([t]*len(self.index))

    def filter_eval_rule(self, rule):
        """
        Evaluate whether a rule is true or false element-wise vector for all rows
        """
        t1 = self.filter_term(rule.term1)
        t2 = self.filter_term(rule.term2)
        if rule.op == dataFilterRule.OP_EQ: # Equal
            return np.equal(t1, t2)
        elif rule.op == dataFilterRule.OP_AEQ: # Approximatly equal
            return np.isclose(t1, t2, rtol=1e-5, atol=1e-6)
        elif rule.op == dataFilterRule.OP_L: # <
            return np.less(t1, t2)
        elif rule.op == dataFilterRule.OP_G: # >
            return np.greater(t1, t2)
        elif rule.op == dataFilterRule.OP_LE: # <=
            return np.less_equal(t1, t2)
        elif rule.op == dataFilterRule.OP_GE: # >=
            return np.greater_equal(t1, t2)
        elif rule.op == dataFilterRule.OP_NEQ: # not equal
            return np.not_equal(t1, t2)
        elif rule.op == dataFilterRule.OP_TRUE: # all true
            return np.array([True]*self.row_count())
        elif rule.op == dataFilterRule.OP_FALSE: # all false
            return np.array([False]*self.row_count())

    def filter_indexes(self, fltr=None):
        """
        Return a list of indexes matching a filter.
        """
        if fltr is None:
            fltr = self.current_filter()
        if fltr is None:
            self.sort_index(inplace=True)
            return (list(self.index), [True]*len(self.index))
        st = self.filters[fltr].sortTerm
        if st is None or st == "" or st == False:
            self.sort_index(inplace=True)
        else:
            st, ascend = search_term_list(st)
            self.sort_values(by=st, ascending=ascend, inplace=True)

        # Evaluate all the rules
        fstack = []
        for r in self.filters[fltr].fstack:
            if r[0] == dataFilter.DF_RULE:
                fstack.append([r[0], self.filter_eval_rule(r[1])])
            else:
                fstack.append(r)

        mask = [True]*len(self.index)
        tstack = []
        #combine the masks
        for item in fstack:
            if item[0] == dataFilter.DF_RULE:
                tstack.append(item[1])
            elif item[0] == dataFilter.DF_AND:
                t2 = tstack.pop()
                t1 = tstack.pop()
                tstack.append(np.logical_and(t1, t2))
            elif item[0] == dataFilter.DF_NOT:
                t1 = tstack.pop()
                tstack.append(np.logical_not(t1))
            elif item[0] == dataFilter.DF_OR:
                t2 = tstack.pop()
                t1 = tstack.pop()
                tstack.append(np.logical_or(t1))
            elif item[0] == dataFilter.DF_XOR:
                t2 = tstack.pop()
                t1 = tstack.pop()
                tstack.append(np.logical_xor(t1))
        if len(tstack) > 0:
            mask = tstack.pop()
        indexes = list(self[mask].index)
        return (indexes, mask)

    def clearData(self, *args, **kwargs):
        self.clear_data(*args, **kwargs)

    def clear_data(self, filtered=False):
        indexes = self.get_indexes(filtered=filtered)
        for i in indexes:
            self.drop(i, inplace=True)
        self.update_filter_indexes()

# This is old export to psuade function.  Hopefully can update:
"""
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
"""
