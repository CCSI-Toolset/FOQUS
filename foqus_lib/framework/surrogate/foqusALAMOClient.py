#!/usr/bin/env python
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
"""foqusALAMOClient.py

* The purpose of this scrip is to be the simulator executable for
* ALAMO.  It reads the input data from ALAMO sends it to FOQUS using
* a network socket connection, waits for the results and writes them
* in the format expected by ALAMO, then it closes the listener in
* FOQUS and exits.

John Eslick, Carnegie Mellon University, 2014
"""
import numpy as np
import time
import sys
from multiprocessing.connection import Client

if __name__ == "__main__":
    inputFile = "input.txt"
    outputFile = "output.txt"
    # Set the socket address, maybe someday this will change or
    # have some setting option, but for now is hard coded
    address = ("localhost", 56001)
    # Open the connection
    conn = Client(address)
    # Read the samples from the input file made by ALAMO
    samples = []
    with open(inputFile, "r") as f:
        print("Reading Input File {}".format(inputFile))
        line = f.readline()  # read and ignore first line
        line = f.readline()
        while line:
            line = line.strip()
            line = line.split()
            if line[0] == "T":
                break
            for i in range(len(line)):
                try:
                    line[i] = float(line[i])
                except:
                    # failed to convert to float I guess is not a number
                    line[i] = float("NaN")
            if len(line) != 0:
                samples.append(line)
            line = f.readline()
    # Submit the samples to FOQUS to be run
    conn.send(["clear"])
    for sample in samples:
        conn.send(["submit", sample])
        conn.recv()
    conn.send(["run"])
    n = conn.recv()[1]
    print("Submitted {0} samples to FOQUS".format(n))
    conn.send(["result"])
    msg = conn.recv()
    status = msg[1]
    results = msg[2]
    conn.send(["close"])
    conn.close()
    # Write the output file that ALAMO can read
    with open(outputFile, "w") as f:
        # f.write(str(k))
        # f.write('\n')
        # Write the input lines
        for i, sample in enumerate(samples):
            result = results[i]
            f.write(" ".join([str(x) for x in sample]))
            f.write(" ")
            f.write(" ".join([str(x) for x in result]))
            f.write("\n")
