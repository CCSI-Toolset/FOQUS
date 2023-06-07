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
"""
    Distribution class

    ***** Here are all the static methods dealing with the enum value ****
    def getFullName(num):
        Get full name of method from its enum value
    
    getPsuadeName(num):
        Get psuade name of method from its enum value

    getInfo(num):
        Returns tuple of (full name, psuade name)

    getEnumValue(name):
        Returns enum value from full or psuade name

    getParameterNames(num):
        Returns tuple of the names of the two parameters associated
            with the distribution of that enum value.
            A None valuein the tuple means no parameter.
            

    **** Here are all the methods for the Distribution object *****
    Distribution(distType):
        Instantiates object of type distType

    setDistributionType(distType):
        Change distribution type
        
    getDistributionType():
        Returns the distribution type of this object

    getParameterValues():
        Returns the parameter values associated with this object

    setParameterValues(value1, value2 = None):
        Sets the values of the parameters.  Calling with just one parameter
        sets the first parameter and makes the second None.
"""


import numbers


class Distribution:
    (
        UNIFORM,
        NORMAL,
        LOGNORMAL,
        TRIANGLE,
        GAMMA,
        BETA,
        EXPONENTIAL,
        WEIBULL,
        SAMPLE,
    ) = list(range(9))
    fullNames = (
        "Uniform",
        "Normal",
        "Lognormal",
        "Triangle",
        "Gamma",
        "Beta",
        "Exponential",
        "Weibull",
        "Sample",
    )
    psuadeNames = ("U", "N", "L", "T", "G", "B", "E", "W", "S")
    firstParamNames = (
        None,
        "Mean",
        "Mean",
        "Mode",
        "Alpha",
        "Alpha",
        "Lambda",
        "Lambda",
        None,
    )
    secondParamNames = (
        None,
        "Std Dev",
        "Std Dev",
        "Width",
        "Beta",
        "Beta",
        None,
        "k",
        None,
    )

    # Here are all the static methods dealing with the enum value
    @staticmethod
    def getFullName(num):
        return Distribution.fullNames[num]

    @staticmethod
    def getPsuadeName(num):
        return Distribution.psuadeNames[num]

    @staticmethod
    def getInfo(num):
        return (Distribution.fullNames[num], Distribution.psuadeNames[num])

    @staticmethod
    def getEnumValue(name):
        try:
            index = Distribution.fullNames.index(name)
            return index
        except ValueError:
            index = Distribution.psuadeNames.index(name)
            return index

    @staticmethod
    def getParameterNames(num):
        return (Distribution.firstParamNames[num], Distribution.secondParamNames[num])

    # Here are all the methods for the Distribution object
    def __init__(self, distType):
        self.setDistributionType(distType)
        self.firstParamValue = None
        self.secondParamValue = None

    def __repr__(self):  # Command prompt behavior
        returnString = "<" + self.getPsuadeName(self.type) + " Distribution instance"
        if self.firstParamValue is not None:
            returnString = returnString + " " + str(self.firstParamValue)
        if self.secondParamValue is not None:
            returnString = returnString + " " + str(self.secondParamValue)
        returnString = returnString + ">"
        return returnString

    def saveDict(self):
        sd = dict()
        sd["type"] = self.getPsuadeName(self.type)
        sd["firstParamValue"] = self.firstParamValue
        sd["secondParamValue"] = self.secondParamValue
        return sd

    def loadDict(self, sd):
        self.setDistributionType(sd.get("type", "Uniform"))
        self.firstParamValue = sd.get("firstParamValue", None)
        self.secondParamValue = sd.get("secondParamValue", None)

    def setDistributionType(self, distType):
        if isinstance(distType, numbers.Number):
            self.type = distType
        else:
            self.type = self.getEnumValue(distType)

    def getDistributionType(self):
        return self.type

    def getParameterValues(self):
        return (self.firstParamValue, self.secondParamValue)

    def setParameterValues(self, value1, value2=None):
        self.firstParamValue = value1
        self.secondParamValue = value2
