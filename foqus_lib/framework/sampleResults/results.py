#################################################################################
# FOQUS Copyright (c) 2012 - 2023, by the software owners: Oak Ridge Institute
# for Science and Education (ORISE), TRIAD National Security, LLC., Lawrence
# Livermore National Security, LLC., The Regents of the University of
# California, through Lawrence Berkeley National Laboratory, Battelle Memorial
# Institute, Pacific Northwest Division through Pacific Northwest National
# Laboratory, Carnegie Mellon University, West Virginia University, Boston
# University, the Trustees of Princeton University, The University of Texas at
# Austin, URS Energy & Construction, Inc., et al.  All rights reserved.
#
# Please see the file LICENSE.md for full copyright and license information,
# respectively. This file is also available online at the URL
# "https://github.com/CCSI-Toolset/FOQUS".
#################################################################################
"""results.py

* This contains the class for sample results data heading

John Eslick, Carnegie Mellon University, 2014
"""

import numpy as np
import pandas as pd
import re
from io import StringIO
import json
import datetime
import logging
import time
from collections import OrderedDict

_log = logging.getLogger("foqus.{}".format(__name__))


class dataFilter(object):
    def __init__(self, no_results=False):
        self.filterTerm = None  # list of columns to filter by
        self.sortTerm = None  # list of columns to sort by
        self.no_results = no_results  # if true return no matches

    def saveDict(self):
        sd = {
            "filterTerm": self.filterTerm,
            "sortTerm": self.sortTerm,
            "no_results": self.no_results,
        }
        return sd

    def loadDict(self, sd):
        self.filterTerm = sd.get("filterTerm", None)
        self.sortTerm = sd.get("sortTerm", None)
        self.no_results = sd.get("no_results", False)
        return self


def iso_time_str():
    return str(datetime.datetime.utcnow().isoformat())


def sd_col_list(sd, time=None):
    """
    Take a value dict saved from results and turn it into a list of columns
    labels and data
    """
    if time is None:
        time = iso_time_str()

    try:
        assert "nodeError" in sd
        assert "turbineMessages" in sd
        assert "input" in sd
        assert "output" in sd
        assert "graphError" in sd
        assert "solTime" in sd
        assert "nodeSettings" in sd
    except AssertionError:
        columns = ["time", "err"]
        dat = [time, 1001]
        return columns, dat

    columns = ["time", "solution_time", "err"]
    dat = [time, sd["solTime"], sd["graphError"]]
    # input, output, and node settings columns
    for s in [["input"] * 2, ["output"] * 2, ["nodeSettings", "setting"]]:
        for n, d in sd[s[0]].items():
            for v in d:
                columns.append("{}.{}.{}".format(s[1], n, v))
                el = sd[s[0]][n][v]
                if s[1] == "setting":
                    el = repr(el)
                dat.append(el)
    # node error and turbine messages columns
    for s in [["nodeError", "node_err"], ["turbineMessages", "turb"]]:
        for n in sd[s[0]]:
            columns.append("{}.{}".format(s[1], n))
            dat.append(sd[s[0]][n])
    # return the list of of columns and list of associated data.
    return columns, dat


def uq_sd_col_list(sd):

    xvals = sd.getInputData()
    yvals = sd.getOutputData()
    xnames = ["input." + name for name in sd.getInputNames()]
    ynames = ["output." + name for name in sd.getOutputNames()]

    if len(yvals) == 0:
        return xnames, xvals

    else:
        return xnames + ynames, np.concatenate([xvals, yvals], axis=1)


def sdoe_sd_col_list(sd):

    xvals = sd.getInputData()
    yvals = sd.getOutputData()
    xnames = ["input." + name for name in sd.getInputNames()]
    ynames = ["output." + name for name in sd.getOutputNames()]

    if len(yvals) == 0:
        return xnames, xvals

    else:
        return xnames + ynames, np.concatenate([xvals, yvals], axis=1)


def odoe_sd_col_list(sd):

    xvals = sd.getInputData()
    yvals = sd.getOutputData()
    xnames = ["input." + name for name in sd.getInputNames()]
    ynames = ["output." + name for name in sd.getOutputNames()]

    if len(yvals) == 0:
        return xnames, xvals

    else:
        return xnames + ynames, np.concatenate([xvals, yvals], axis=1)


def eval_sd_col_list(sd):

    xvals = sd.getInputData()
    yvals = sd.getOutputData()
    xnames = ["input." + name for name in sd.getInputNames()]
    ynames = ["output." + name for name in sd.getOutputNames()]

    if len(yvals) == 0:
        return xnames, xvals

    else:
        return xnames + ynames, np.concatenate([xvals, yvals], axis=1)


def incriment_name(name, exnames):
    """
    Check if a name is already in a list of names. If it is generate a new
    unique name by adding an incimenting number at the end.
    """
    if not name in exnames:
        return name  # name is already new
    index = 1
    for n in exnames:
        m = re.match(r"^%s_([0-9]+)$" % name, n)
        if m:
            i = int(m.group(1))
            if i >= index:
                index = i + 1
        else:
            "".join([name, "_", str(index).zfill(4)])
    return "".join([name, "_", str(index).zfill(4)])


def search_term_list(st):
    st = st.strip()
    if st.startswith("["):
        try:
            st = json.loads(st)
        except:
            logging.getLogger("foqus." + __name__).exception(
                "Error reading filer sort terms"
            )
            raise Exception(
                "Error reading sort terms. When using multiple sort"
                'terms, enclose the column names in "". See log for deatils'
            )
    else:
        if st.startswith('"'):
            st = json.loads(st)
        st = [st]
    ascend = [True] * len(st)
    for i, t in enumerate(st):
        if t.startswith("-"):
            st[i] = t[1:]
            ascend[i] = False
    return st, ascend


class Results(pd.DataFrame):
    @property
    def _constructor(self):
        return Results

    @property
    def _constructor_sliced(self):
        return pd.Series

    def __init__(self, *args, **kwargs):
        super(Results, self).__init__(*args, **kwargs)
        if "set" not in self.columns:
            self.filters = None  # do this to avoid set column from attribute warn
            self.filters = {}  # now that atribute exists set to empty dict
            self.filters["none"] = dataFilter(no_results=True)
            self.filters["all"] = dataFilter()
            self._current_filter = None
            self._filter_indexes = None  # avoid set column from attribute warn
            self._filter_indexes = []  # now that atribute exists set to empty list
            self.flatTable = None  # avoid set column from attribute warn
            self.flatTable = True
            self["set"] = []
            self["result"] = []
            self._filter_mask = None
            self.hidden_cols = None  # avoid set column from attribute warn
            self.hidden_cols = []
            self.calculated_columns = None  # avoid set column from attribute warn
            self.calculated_columns = OrderedDict()

    def row_to_flow(self, fs, row, filtered=True):
        idx = list(self.get_indexes(filtered=filtered))[row]
        _log.debug("Row to flowsheet, table row {} dataframe index {}".format(row, idx))
        for col in self.columns:
            try:
                (typ, node, var) = col.split(".", 2)
            except ValueError:
                # this would happen for cols with less than two .'s and is
                # totally fine
                continue
            if typ == "input":
                try:
                    fs.nodes[node].inVars[var].value = self.loc[idx, col]
                except KeyError:
                    pass
            elif typ == "output":
                try:
                    fs.nodes[node].outVars[var].value = self.loc[idx, col]
                except KeyError:
                    pass

    def set_calculated_column(self, name, expr):
        self.calculated_columns[name] = expr
        c = "calc.{}".format(name)
        if c not in self.columns:
            self[c] = [np.nan] * self.count_rows(filtered=False)

    def calculate_columns(self):
        def c(key):
            return self.filter_term(key)

        for key in self.calculated_columns:
            self["calc." + key] = eval(self.calculated_columns[key])

    def calculate_filter_expr(self, expr):
        def c(key):
            return self.filter_term(key)

        return np.array(eval(expr), dtype=bool)

    def delete_calculation(self, name):
        try:
            del self.calculated_columns[name]
        except:
            pass
        try:
            self.drop("calc." + name, axis=1, inplace=True)
        except:
            pass

    def delete_rows(self, rows, filtered=True):
        idxs = [list(self.get_indexes(filtered=filtered))[i] for i in rows]
        self.drop(idxs, axis=0, inplace=True)
        self.update_filter_indexes()

    def edit_set_name(self, name, rows, filtered=True):
        idxs = [list(self.get_indexes(filtered=filtered))[i] for i in rows]
        for idx in idxs:
            self.loc[idx, "set"] = name
        self.update_filter_indexes()

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

        def convertIndex(n):
            try:
                return int(n.item())
            except:
                return n

        sd = {
            "__columns": list(self.columns),
            "__indexes": list(map(convertIndex, list(self.index))),
            "__filters": {},
            "__current_filter": self._current_filter,
        }
        for f in self.filters:
            sd["__filters"][f] = self.filters[f].saveDict()
        for i in self.index:
            key = str(i)
            sd[key] = list(self.loc[i])
            for j, e in enumerate(sd[key]):
                if isinstance(e, np.float64):
                    sd[key][j] = e.item()
                elif isinstance(e, np.bool_):
                    sd[key][j] = bool(e)
        sd["calculated_columns"] = self.calculated_columns
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
                "Error loading stored results"
            )
        for i in sd.get("__filters", []):
            self.filters[i] = dataFilter().loadDict(sd["__filters"][i])

        if "none" not in self.filters:
            self.filters["none"] = dataFilter().loadDict(
                {"fstack": [[10, {"term2": 0, "term1": 1, "op": 0}]]}
            )
        if "all" not in self.filters:
            self.filters["all"] = dataFilter()
        self.calculated_columns = sd.get("calculated_columns", OrderedDict())

        self.update_filter_indexes()

    def data_sets(self):
        """Return a set of data set labels"""
        return set(self.loc[:, "set"])

    def addFromSavedValues(self, setName, name, time=None, valDict=None):
        """Temoprary function for compatablility
        should move to add_result()
        """
        self.add_result(valDict, set_name=setName, result_name=name, time=time)

    def add_result(
        self, sd, set_name="default", result_name="res", time=None, empty=False
    ):
        """
        Add a set of flowseheet results to the data frame.  If sd is missing
        anything most values will be left NaN and the graph error will be 1001
        """
        if len(self["set"]) > 0:
            names = list(self.loc[self["set"] == set_name].loc[:, "result"])
        else:
            names = []
        result_name = incriment_name(result_name, names)
        if sd is not None:
            columns, dat = sd_col_list(sd, time=time)
        else:
            columns, dat = (tuple(), tuple())
        for c in columns:
            if c not in self.columns:
                self[c] = [np.nan] * self.count_rows(filtered=False)
        row = self.count_rows(filtered=False)
        self.loc[row, "set"] = set_name
        self.loc[row, "result"] = result_name
        if not empty:
            for i, col in enumerate(columns):
                # if type(dat[i])==list:
                #     self.loc[row, col] = str(dat[i])
                # else:
                self.loc[row, col] = dat[i]
        self.update_filter_indexes()

    def uq_add_result(self, data, set_name="default", result_name="res", time=None):

        if len(self["set"]) > 0:
            names = list(self.loc[self["set"] == set_name].loc[:, "result"])
        else:
            names = []
        result_name = incriment_name(result_name, names)
        columns, dat = uq_sd_col_list(data)

        for c in columns:
            if c not in self.columns:
                self[c] = [np.nan] * self.count_rows(filtered=False)
        for row in range(data.getNumSamples()):
            self.loc[row, "set"] = set_name
            self.loc[row, "result"] = result_name
            for i, col in enumerate(columns):
                self.loc[row, col] = dat[row][i]
        self.update_filter_indexes()

    def sdoe_add_result(self, data, set_name="default", result_name="res", time=None):

        if len(self["set"]) > 0:
            names = list(self.loc[self["set"] == set_name].loc[:, "result"])
        else:
            names = []
        result_name = incriment_name(result_name, names)
        columns, dat = sdoe_sd_col_list(data)

        for c in columns:
            if c not in self.columns:
                self[c] = [np.nan] * self.count_rows(filtered=False)
        for row in range(data.getNumSamples()):
            self.loc[row, "set"] = set_name
            self.loc[row, "result"] = result_name
            for i, col in enumerate(columns):
                self.loc[row, col] = dat[row][i]
        self.update_filter_indexes()

    def odoe_add_result(self, data, set_name="default", result_name="res", time=None):

        if len(self["set"]) > 0:
            names = list(self.loc[self["set"] == set_name].loc[:, "result"])
        else:
            names = []
        result_name = incriment_name(result_name, names)
        columns, dat = odoe_sd_col_list(data)

        for c in columns:
            if c not in self.columns:
                self[c] = [np.nan] * self.count_rows(filtered=False)
        for row in range(data.getNumSamples()):
            self.loc[row, "set"] = set_name
            self.loc[row, "result"] = result_name
            for i, col in enumerate(columns):
                self.loc[row, col] = dat[row][i]
        self.update_filter_indexes()

    def eval_add_result(self, data, set_name="default", result_name="res", time=None):

        if len(self["set"]) > 0:
            names = list(self.loc[self["set"] == set_name].loc[:, "result"])
        else:
            names = []
        result_name = incriment_name(result_name, names)
        columns, dat = eval_sd_col_list(data)

        for c in columns:
            if c not in self.columns:
                self[c] = [np.nan] * self.count_rows(filtered=False)
        for row in range(data.getNumSamples()):
            self.loc[row, "set"] = set_name
            self.loc[row, "result"] = result_name
            for i, col in enumerate(columns):
                self.loc[row, col] = dat[row][i]
        self.update_filter_indexes()

    def exportVarsCSV(self, file, inputs, outputs, flat=True):
        # flat isn't used, just there for compatablility from when there were vector vars.
        df = pd.DataFrame(columns=inputs + outputs)
        for c in inputs:
            df[c] = self["input." + c]
        for c in outputs:
            df[c] = self["output." + c]
        df.to_csv(file)

    def read_csv(self, *args, **kwargs):
        """
        Read results into a data frame from a CSV file.
        """
        s = kwargs.pop("s", None)
        if s is not None:
            path = StringIO(s)
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

    def clearData(self, *args, **kwargs):
        self.clear_data(*args, **kwargs)

    def clear_data(self, filtered=False):
        indexes = self.get_indexes(filtered=filtered)
        for i in indexes:
            self.drop(i, inplace=True)
        self.update_filter_indexes()

    def filter_term(self, t):
        """
        Return the value of a filter term. Array for all rows.
        """
        if t in self.columns:
            return np.array(list(self.loc[:, t]))
        else:
            raise Exception("Filter term ({}) not in columns".format(t))

    def filter_indexes(self, fltr=None):
        """
        Return a list of indexes matching a filter.  FOQUS should also have
        standard "all" and "none" filters.  This treats those names special and
        returns all no results ignoring any changes that may have been made.
        Also all doesn't sort, you need to make a filter for that.
        """
        # Get the filter or resort and return all if none
        if fltr is None:
            fltr = self.current_filter()
        if fltr is None or fltr == "all":
            self.sort_index(inplace=True)
            return list(self.index), [True] * len(self.index)
        if fltr == "none" or self.filters[fltr].no_results:
            return [], [False] * len(self.index)
        # Swap the name for the actual filter object
        fltr = self.filters[fltr]
        # If a sort term string is provided, sort
        st = fltr.sortTerm
        if st is None or st == "" or st == False:
            self.sort_index(inplace=True)
        else:
            st, ascend = search_term_list(st)
            if len(st) == 0:
                self.sort_index(inplace=True)
            else:
                self.sort_values(by=st, ascending=ascend, inplace=True)
        # now look at the filter columns
        ft = fltr.filterTerm
        mask = [True] * len(self.index)
        if ft is None or ft == "" or ft == False:
            return list(self.index), mask
        else:
            mask = self.calculate_filter_expr(ft)
        indexes = list(map(int, list(self[mask].index)))
        return indexes, mask
