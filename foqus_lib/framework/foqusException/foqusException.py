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
"""foqusException.py

This class can be inherited to create new FOQUS exception classes

John Eslick, Carnegie Mellon University, 2014
"""
import traceback


class foqusException(Exception):
    def __init__(self, code=0, msg="", e=None, tb=None):
        """
        code: an error code for the problem
        msg: string containing additional specific information
        e: the original exception that was caught if any
        tb: the trace back string to locate problem in code
        """
        self.code = code
        self.msg = msg
        if tb == None:
            l = traceback.extract_stack(limit=6)
            l2 = []
            for i in range(len(l) - 1):
                l2.append(
                    " ".join(
                        [
                            "line:",
                            str(l[i][1]),
                            "file:",
                            str(l[i][0]),
                            "\n  ",
                            str(l[i][3]),
                        ]
                    )
                )
            self.tb = str("\n".join(l2))
        else:
            self.tb = tb
        self.codeString = dict()
        self.setCodeStrings()
        super(foqusException, self).__init__(msg)

    def getCodeString(self):
        """
        Return the string error message accosiated with error code
        """
        return self.codeString.get(self.code, "Error code: {0}".format(self.code))

    def setCodeStrings(self):
        """
        This is a function that should be overloaded to add to the
        error code strings to the codeString dictionary, use integer
        keys.
        """
        pass

    def __str__(self):
        """
        This is function gets called when use use the str() function
        to turn the excepetion into a string.  This tries to turn
        the exception object into a nice helpful string message to
        print out.
        """
        if self.tb == None or self.tb[0:4] == "None":
            tb = ""
        else:
            tb = self.tb
        if self.msg == "":
            return "{0} - {1}, {2}\n".format(self.code, self.getCodeString(), tb)
        else:
            return "{0} - {1}, {2}\n{3}\n".format(
                self.code, self.getCodeString(), self.msg, tb
            )
