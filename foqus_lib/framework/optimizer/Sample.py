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
""" #FOQUS_OPT_PLUGIN

Optimization plugins need to have the string "#FOQUS_OPT_PLUGIN" near the
begining of the file (see pluginSearch.plugins() for exact character count of
text).  They also need to have a .py extension and inherit the optimization class.

* Just evaluates the objective function for flowsheet results and picks the best
  result.  If the status for any result is -1 the result is rerun.

John Eslick, Carnegie Mellon University, 2014
"""

import time
import copy
import csv
import queue
import sys
import logging
import math
import numpy
import os
import traceback
from foqus_lib.framework.optimizer.optimization import optimization


def checkAvailable():
    """
    Plugins should have this function to check availability of any
    additional required software.  If requirements are not available
    plugin will not be available.
    """
    return True


class opt(optimization):
    """
    CSV_Sample
    """

    def __init__(self, dat=None):
        """
        Initialize CMA-ES optimization module
        """
        optimization.__init__(self, dat)
        self.name = "CMA-ES"
        self.methodDescription = (
            "This plugin just runs samples evaluetes all the flowsheet "
            "samples and picks out the best one.  If any samples have "
            "not been evaluted (status -1), they will be evaluted.  "
            "This works with the currently selected data filter, and "
            "is mostly used for testing."
        )
        self.mp = True
        self.mobj = False
        self.requireScaling = False
        self.minVars = 0
        self.maxVars = 500
        self.options.add(
            name="Backup interval",
            default=0,
            desc=(
                "Time between saving FOQUS session backups (sec)" " ( < 15 no backup)"
            ),
        )

    def optimize(self):
        """
        This is the optimization routine.
        """
        backupInt = self.options["Backup interval"].value
        start = time.process_time()
        self.msgQueue.put(
            "Started at {0}".format(
                time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
            )
        )
        rerunList = []
        rerunSamp = []
        bestObj = numpy.array(self.prob.obj[0].fail)
        bestRes = -1
        for i in range(self.graph.results.subsetLen()):
            r = self.graph.results.subsetResult(i)
            if r.error == -1:
                # If r not run add it to the
                rerunList.append(i)
                rerunSamp.append(r.toSavedInputValues())
                # otherwise calculate the objective
                objValues, cv, pv = self.prob.calculateObj([r.toSavedValuesFormat()])
                obj = objValues[0][0]
                if obj < bestObj:
                    bestObj = obj
                    bestRes = i
        self.msgQueue.put("Running {0} samples".format(len(rerunSamp)))
        err = 0
        # now rerun samples that were not alreay run
        self.resQueue.put(["PROG", 0, len(rerunSamp), 0, 0, 0, 0])
        timeOfBackup = time.process_time()
        if len(rerunSamp) > 0:
            finished = 0
            userInterupt = False
            gt = self.graph.runListAsThread(rerunSamp)
            doneList = []
            while gt.is_alive():
                gt.join(2)
                if self.stop.isSet():  # check for stop flag
                    userInterupt = True
                    gt.terminate()
                if gt.status["finished"] != finished:
                    for i, res in enumerate(gt.res):
                        if res != None:
                            if i not in doneList:
                                doneList.append(i)
                                r = self.graph.results.subsetResult(rerunList[i])
                                r.resetResultFromValues(res)
                    finished = gt.status["finished"]
                    # put out status
                    self.resQueue.put(
                        [
                            "PROG",
                            finished,
                            len(rerunSamp),
                            gt.status["error"],
                            0,
                            finished,
                            gt.status["error"],
                        ]
                    )
                # back up if its time.  Don't back up for intervals
                # of less than 15 seconds, because that setting dosen't
                # make sense even 15 seconds is crazy.
                timeSinceBackup = time.process_time() - timeOfBackup
                if backupInt > 15.0 and timeSinceBackup > backupInt:
                    self.dat.save(
                        filename="".join(["Opt_Backup_", self.dat.name, ".json"]),
                        updateCurrentFile=False,
                        bkp=False,
                    )
                if userInterupt:
                    break
            # finish rerun loop
            if gt.res:
                for i, res in enumerate(gt.res):
                    if i not in doneList:
                        if res:
                            doneList.append(i)
                        r = self.graph.results.subsetResult(rerunList[i])
                        r.resetResultFromValues(res)
        # Calculate objectives
        bestObj = numpy.array(self.prob.obj[0].fail)
        bestRes = -1
        for i in range(self.graph.results.subsetLen()):
            r = self.graph.results.subsetResult(i)
            # otherwise calculate the objective
            objValues, cv, pv = self.prob.calculateObj([r.toSavedValuesFormat()])
            obj = objValues[0][0]
            if obj < bestObj:
                bestObj = obj
                bestRes = i
        if bestRes == -1:
            self.msgQueue.put("No good results found.")
        else:
            self.msgQueue.put("Storing best result in the flowsheet")
            self.msgQueue.put("Best result index {0}".format(bestRes))
            self.msgQueue.put("Best objective: {0}".format(bestObj))
            r = self.graph.results.subsetResult(bestRes)
            self.graph.loadValues(r.toSavedValuesFormat())
