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
"""listen.py

* This contains listeners to run simulations taking input from a socket
  interface this is used for sampling methods like ALAMO that can run a simultor
  (executable) to do additional sampling. The executable will tell FOQUS to run
  a simulation and return results by connecting to the socket of the listener.

John Eslick, Carnegie Mellon University, 2014
"""


import logging
from multiprocessing.connection import Listener
import threading
import time
import numpy as np
import copy


class foqusListener2(threading.Thread):
    """
    A multiprocessing listener to allow FOQUS to be controlled over a socket
    connection. The main purpose for this adaptive sampling.
    """

    def __init__(self, dat, host="localhost", port=56002):
        threading.Thread.__init__(self)
        self.daemon = True
        self.gt = None
        self.dat = dat
        # Create a listener
        self.address = (host, port)
        self.listener = Listener(self.address)

    def run(self):
        quitListening = False
        while True:
            # Wait for a connection to be made
            conn = self.listener.accept()
            while True:
                msg = conn.recv()
                if not (msg and isinstance(msg, list) and msg[0]):
                    # ignore improperly formatted messages
                    continue
                if msg[0] == "close":
                    # close the connection
                    conn.close()
                    break
                elif msg[0] == "quit":
                    # close the connection and don't wait for another
                    quitListening = True
                    if self.gt:
                        self.gt.terminate()
                    conn.close()
                    break
                elif msg[0] == "loadValues":
                    try:
                        self.dat.loadFlowsheetValues(msg[1])
                        conn.send([0])
                    except Exception as e:
                        logging.exception("Error loading values")
                        conn.send([1])
                elif msg[0] == "run":
                    try:
                        self.gt = self.dat.flowsheet.runAsThread()
                        conn.send([0])
                    except:
                        logging.exception("Error running flowsheet")
                        conn.send([1])
                elif msg[0] == "saveValues":
                    self.gt.join(10)
                    if self.gt.is_alive():
                        # still waiting but continue so you have a
                        # chance to shutdown the listener if you want
                        conn.send([1, "Still Running"])
                    else:
                        if self.gt.res:
                            self.dat.flowsheet.loadValues(self.gt.res)
                        else:
                            self.dat.flowsheet.errorStat = 19
                        self.dat.saveFlowsheetValues(msg[1])
                        conn.send([0])
            if quitListening:
                break
        self.listener.close()


class foqusListener(threading.Thread):
    """
    A multiprocessing listener to allow FOQUS to be controlled over a socket
    connection. The main purpose for this adaptive sampling.
    """

    def __init__(self, dat, host="localhost", port=56001):

        threading.Thread.__init__(self)
        self.daemon = True
        self.inputNames = []
        self.outputNames = []
        self.resStoreSet = "listener"
        self.runid = 0
        self.dat = dat
        self.failValue = -111111
        self.samples = []
        self.gt = None
        self.scaled = False
        # Create a listener
        self.address = (host, port)
        self.listener = Listener(self.address)

    def setInputs(self, l):
        self.inputNames = l

    def setOutputs(self, l):
        self.outputNames = l

    def run(self):
        """Called by Thread when you run start() method"""
        quitListening = False
        # create an input dictionary structure to load values from
        inpDict = self.dat.flowsheet.saveValues()["input"]
        # Enter loop waiting for requests from client
        while True:
            # Wait for a connection to be made
            conn = self.listener.accept()
            while True:
                msg = conn.recv()
                if not (msg and isinstance(msg, list) and msg[0]):
                    # ignore improperly formatted messages
                    continue
                if msg[0] == "close":
                    # close the connection
                    conn.close()
                    break
                elif msg[0] == "quit":
                    # close the connection and don't wait for another
                    quitListening = True
                    conn.close()
                    break
                elif msg[0] == "clear":
                    # clear the list of samples
                    self.samples = []
                elif msg[0] == "run":
                    # Start up a thread to run samples
                    # Run samples either locally or through Turbine
                    if self.dat.foqusSettings.runFlowsheetMethod == 0:
                        # run local
                        self.gt = self.dat.flowsheet.runListAsThread(self.samples)
                    else:  # run in turbine
                        self.gt = self.dat.flowsheet.runListAsThread(
                            self.samples, useTurbine=True
                        )
                    conn.send(["run", len(self.samples)])
                elif msg[0] == "submit":
                    # put a run on the input queue
                    varVals = msg[1]  # List of variable values
                    sampInput = copy.deepcopy(inpDict)
                    vals = self.dat.flowsheet.input.unflatten(
                        self.inputNames, varVals, unScale=self.scaled
                    )
                    for nkey in vals:
                        for vkey in vals[nkey]:
                            sampInput[nkey][vkey] = vals[nkey][vkey]
                    self.samples.append(sampInput)
                    runIndex = len(self.samples) - 1
                    conn.send(["submitted", runIndex])
                elif msg[0] == "status":
                    # send run status
                    conn.send(["status", self.gt.status])
                elif msg[0] == "result":
                    # Store results in FOQUS and send them to client also
                    self.gt.join()
                    ret = []
                    stat = []
                    # WHY pylint infers `res` as an unsubscriptable object
                    # (possibly because of None default value?)
                    # pylint: disable=unsubscriptable-object
                    for res in self.gt.res:
                        self.dat.flowsheet.results.addFromSavedValues(
                            self.resStoreSet, "res_{0}".format(self.runid), None, res
                        )
                        self.runid += 1
                        stat.append(res["graphError"])
                        r = []
                        for vn in self.outputNames:
                            vn = vn.split(".", 1)
                            nodeName = vn[0]
                            varName = vn[1]
                            r.append(res["output"][nodeName][varName])
                        if res["graphError"] != 0:
                            for i in range(len(r)):
                                r[i] = self.failValue
                        ret.append(r)
                    # pylint: enable=unsubscriptable-object
                    conn.send(["result", stat, ret])
                elif msg[0] == "save":
                    # Save the flow sheet
                    self.dat.save()
                elif msg[0] == "scaled":
                    # the default is not scaled input
                    # if you set this before starting workers
                    # you can make set to expect scaled input
                    self.scaled = msg[1]
                elif msg[0] == "inputNames":
                    # Set the input variables
                    self.setInputs(msg[1])
                    conn.send(["inputNames", self.inputNames])
                elif msg[0] == "outputNames":
                    # Set the output variable names.
                    self.setOutputs(msg[1])
                    conn.send(["outputNames", self.outputNames])
            if quitListening:
                break
        # do whatever to finish up
        print("exiting foqus listener")
        self.listener.close()
