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
"""option.py
     
This is an options class for FOQUS, mainly used for optimization and surrogate
model plugins.

John Eslick, Carnegie Mellon University, 2014
"""


class option:
    def __init__(
        self,
        default=0.0,
        value=None,
        desc="An option",
        vmin=None,
        vmax=None,
        dtype=None,
        validValues=[],
        optSet=0,
        disable=False,
        section="",
        hint="",
    ):
        """
        creates a new option, options are used in settings for
        optimization solvers, and surrogate model methods they
        may be used in more plases in the future.

        Args/attributes

        default -  a default value for the option (if dtype is
            not specified the type of the default will be used
            to set the option type
        value - the current option value
        desc - a string description of the option
        vmin - a min value optionally used to validate float and int
        vmax - a max value optionally used to validate float and int
        dtype - a data type for otpion if None, set by default value
        validValues - a list of valid values, empty list means no
            restriction
        """
        self.desc = desc
        if value == None:
            self.value = default
        self.default = default
        self.vmin = vmin
        self.vmax = vmax
        if dtype == None:
            self.dtype = type(default)
        else:
            self.dtype = dtype
        self.validValues = validValues
        self.optSet = optSet
        self.disable = disable

    def saveDict(self):
        sd = {
            "desc": self.desc,
            "value": self.value,
            "default": self.default,
            "vmax": self.vmax,
            "vmin": self.vmin,
            "dtype": self.typeToString(self.dtype),
            "validValues": self.validValues,
            "optSet": self.optSet,
            "disable": self.disable,
        }
        return sd

    def loadDict(self, sd):
        self.desc = sd.get("desc", self.desc)
        self.value = sd.get("value", self.value)
        self.default = sd.get("default", self.default)
        self.vmax = sd.get("vmax", self.vmax)
        self.vmin = sd.get("vmin", self.vmin)
        self.dtype = sd.get("dtype", None)
        self.disable = sd.get("disable", False)
        if self.dtype is None:
            self.dtype = self.stringToType(self.dtype)
        else:
            self.dtype = type(self.default)
        self.validValues = sd.get("validValues", self.validValues)
        self.optSet = sd.get("optSet", self.optSet)

    def validTypes(self):
        return [float, int, str, bool, list, dict]

    def typeToString(self, t):
        if t == float:
            return "float"
        elif t == int:
            return "int"
        elif t == str:
            return "str"
        elif t == bool:
            return "bool"
        elif t == list:
            return "list"
        elif t == dict:
            return "dict"
        else:
            return None

    def stringToType(self, s):
        if s == "float":
            return float
        elif s == "int":
            return int
        elif s == "str":
            return str
        elif s == "bool":
            return bool
        elif s == "list":
            return list
        elif s == "dict":
            return dict
        else:
            return None

    def set(self, value):
        if type(value) == int and self.dtype == float:
            self.value = float(value)
        else:
            self.value = value

    def get(self):
        return self.value

    def valid(self):
        return self.validateType() and self.validateRange() and self.validateList()

    def validateType(self):
        """
        Check that the value type matches the specified data type.
        Also allows int values for float.
        """
        if isinstance(self.value, self.dtype):
            return True
        elif isinstance(self.value, int) and self.dtype == float:
            return True
        else:
            return False

    def validateRange(self):
        """
        Check that if the value is an int or float that it is between
        less than vmax and more than vmin if vmax and vmin are given
        """
        if not isinstance(self.value, (int, float)):
            return True
        elif self.vmin != None and self.value < self.vmin:
            return False
        elif self.vmax != None and self.value > self.vmax:
            return False
        else:
            return True

    def validateList(self):
        """
        Check that the value is in the list of valid values
        """
        if self.validValues == []:
            return True
        elif self.value in self.validValues:
            return True
        else:
            return False
