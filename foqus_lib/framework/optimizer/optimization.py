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
"""optimization.py

* Base class for optimization plugins

John Eslick, Carnegie Mellon University, 2014
"""

import queue
import logging
import threading
import copy
from foqus_lib.framework.foqusOptions.optionList import optionList
from .problem import *
import sys
import os
import importlib
import traceback


class optimization(threading.Thread):
    """
    base class for optimization modules
    """

    def __init__(self, dat=None):
        """
        Initialize CMA-ES optimization module
        """
        threading.Thread.__init__(self)
        self.stop = threading.Event()
        self.daemon = True
        self.setData(dat)
        self.options = optionList()
        self.name = "Optimization Base"
        self.description = "Optimization Base Class"
        self.mp = True
        self.mobj = False
        self.requireScaling = True
        self.minVars = 1
        self.maxVars = 100
        self.msgQueue = queue.Queue()  # queue for messages to print
        self.resQueue = queue.Queue()  # a queue for plots and monitoring
        self.ex = None
        self.updateGraph = False

    def setData(self, dat=None):
        """
        Set the session data so the optimization routine can get
        the flowsheet and whatever else it may need.
        """
        self.dat = dat
        if dat:
            self.graph = dat.flowsheet
            self.prob = self.dat.optProblem
        else:
            self.graph = None
            self.prob = None

    def terminate(self):
        """
        This sets the stop flag to indicate that you want to stop
        the optimization.  The optimize function needs to check the
        stop flag periodically for this to work, so the optimization
        may take some time to stop, or may not stop at all if the
        flag is not checked in the derived class.
        """
        self.stop.set()
        self.msgQueue.put("User Interrupt")

    def optimize(self):
        raise NotImplementedError

    def run(self):
        """
        This function overloads the Thread class function, and is
        called when you run start() to start a new thread.
        """
        try:
            if self.dat.foqusSettings.runFlowsheetMethod == 1:
                self.dat.flowsheet.uploadFlowseetToTurbine(self.dat, reset=False)
            self.optimize()
        except Exception as e:
            logging.getLogger("foqus." + __name__).exception(
                "Exception in optimization thread"
            )
