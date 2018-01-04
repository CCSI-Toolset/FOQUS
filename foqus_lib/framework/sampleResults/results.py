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
import pandas as pd
import StringIO
import numpy as np
import copy
import csv
import string
import numpy
import json
import datetime
import logging
import re
import math
import time
from foqus_lib.framework.session.hhmmss import *

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

class dataFilterRule(object):
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
                dat.append(sd[s[0]][n][v])
    #node error and turbine messages columns
    for s in [["nodeError", "node_err"], ["turbineMessages", "turb"]]:
        for n in sd[s[0]]:
            columns.append("{}.{}".format(s[1], n))
            dat.append(sd[s[0]][n])
    # return the list of of columns and list of accosiated data.
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


class Results(pd.DataFrame):
    def __init__(self, *args, **kwargs):
        super(Results, self).__init__(*args, **kwargs)
        self.filters = {}
        self._currentFilter = None
        self.flatTable = True
        self["set"] = []
        self["result"] = []

    def currentFilter(self):
        return self._currentFilter

    def saveDict(self):
        sd = {"__columns":list(self.columns), "__indexes":list(self.index)}
        for i in self.index:
            sd[i] = list(self.loc[i])
        return sd

    def loadDict(self, sd):
        self.drop(self.index, inplace=True)
        self.drop(self.columns, axis=1, inplace=True)
        try:
            columns = sd["__columns"]
            for c in columns:
                self[c] = []
            for i in sd["__indexes"]:
                self.loc[i] = sd[str(i)]
        except:
            logging.getLogger("foqus." + __name__).exception(
                "Error loading stored results")

    def data_sets(self):
        return list(self.loc[:,"set"])

    def add_result(self, sd, set_name="default", result_name="res", time=None):
        #set_name = incrimentName(set_name, )
        #result_name = incrimentName(result_name, )
        names = list(self.loc[self["set"] == set_name].loc[:,"result"])
        result_name = incriment_name(result_name, names)
        columns, dat = sd_col_list(sd, time=time)
        for c in columns:
            if c not in self.columns:
                self[c] = [np.nan]*self.rowCount()
        row = self.rowCount()
        self.loc[row, "set"] = set_name
        self.loc[row, "result"] = result_name
        for i, col in enumerate(columns):
            self.loc[row, col] = dat[i]

    def read_csv(self, *args, **kwargs):
        s = kwargs.pop("s", None)
        if s is not None:
            path = StringIO.StringIO(s)
            kwargs["filepath_or_buffer"] = path
        df = pd.read_csv(*args, **kwargs)
        col_del = []
        for r in df.index:
            row = self.rowCount()
            for c in df.columns:
                self.loc[row, c] = df.loc[r, c]

    def rowCount(self, filtered=None):
        return len(self.index)

    def columnCount(self):
        return len(self.columns)

    def colCount(self):
        return self.columnCount()


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
