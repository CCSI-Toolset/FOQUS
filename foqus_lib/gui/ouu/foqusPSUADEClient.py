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
"""foqusPSUADEClient.py

* The purpose of this script is to be the simulator executable for
* PSUADE.  It reads the input data from PSUADE sends it to FOQUS using
* a network socket connection, waits for the results and writes them
* in the format expected by PSUADE, then it closes the listener in
* FOQUS and exits.

Jeremy Ou, Lawrence Livermore National Laboratory, 2015
"""
import sys
from multiprocessing.connection import Client

# ==================================================
# Function to get input data for interpolation
# ==================================================
def getInputData(inFileName):
    import shutil

    shutil.copyfile(inFileName, "tempdata")
    inFile = open(inFileName, "r")
    lines = inFile.readlines()
    inFile.close()
    lines = [line for line in lines if len(line.strip()) != 0]
    lineIn = lines[0]
    toks = lineIn.split()
    nLines = eval(toks[0])
    multiSample = False
    nSamp = 1
    if len(toks) > 1:
        nSamp = nLines
        multiSample = True
    # WHY pylint report errors when iterating over inData assuming that each item is a list;
    # setting inData = nSamp * [[]] (i.e. initializing inData as an empty list of lists)
    # seems to fix the pylint errors, but it's not clear if this would be compatible
    # with the expected runtime behavior in all cases
    inData = nSamp * [0]
    if not multiSample:
        inData[0] = []
    for cnt in range(nLines):
        lineIn = lines[cnt + 1]
        nCols = lineIn.split()
        row = len(nCols) * [0]
        for ind in range(len(nCols)):
            row[ind] = eval(nCols[ind])
        if multiSample:
            inData[cnt] = row
        else:
            inData[0] += row
    if len(lines) > nLines + 1:
        lineIn = lines[nLines + 1]
        toks = lineIn.split()
        numFixed = int(toks[2])
        fixedVals = []
        for i in range(numFixed):
            lineIn = lines[nLines + 2 + i]
            toks = lineIn.split()
            fixedVals.append(float(toks[4]))
        for row in inData:
            row.extend(fixedVals)  # TODO pylint: disable=no-member

    outFile = open("tempdata", "a")
    outFile.write("%d\n" % nSamp)
    for row in inData:
        for col in row:  # TODO pylint: disable=not-an-iterable
            outFile.write("%f " % col)
        outFile.write("\n")
    outFile.close()
    return nSamp, inData


# ==================================================
# Function to generate output file
# ==================================================
def genOutputFile(outFileName, outData):
    nLeng = len(outData)
    outfile = open(outFileName, "w")
    for row in outData:
        outfile.write(" ".join([str(dat) for dat in row]))
        outfile.write("\n")
    outfile.close()
    return None


def main():
    f = open("foquspsuadeclient.log", "w")
    f.write(" ".join(sys.argv))
    f.write("\n")
    inputFile = sys.argv[1]
    outputFile = sys.argv[2]
    # Set the socket address, maybe someday this will change or
    # have some setting option, but for now is hard coded
    address = ("localhost", 56001)
    f.write("Create client\n")
    f.close()
    # Open the connection
    conn = Client(address)
    # Read the sample from the input file made by PSUADE
    f = open("foquspsuadeclient.log", "a")
    f.write("Get samples from file %s\n" % inputFile)
    f.close()
    (nSamples, samples) = getInputData(inputFile)
    f = open("foquspsuadeclient.log", "a")
    f.write("Number of samples is %d\n" % nSamples)
    f.close()
    f = open("foquspsuadeclient.log", "a")
    for row in samples:
        f.write(" ".join(map(str, row)))
        f.write("\n")
    f.close()

    # Submit the samples to FOQUS to be run
    f = open("foquspsuadeclient.log", "a")
    f.write("Send clear\n")
    f.close()
    conn.send(["clear"])
    f = open("foquspsuadeclient.log", "a")
    f.write("Write samples:\n")
    f.close()
    for sample in samples:
        f = open("foquspsuadeclient.log", "a")
        f.write(" ".join(map(str, sample)))
        f.write("\n")
        f.close()
        conn.send(["submit", sample])
        conn.recv()
    f = open("foquspsuadeclient.log", "a")
    f.write("Samples sent. Running...\n")
    f.close()
    conn.send(["run"])
    n = conn.recv()[1]
    # print 'Submitted {0} samples to FOQUS'.format(n)
    f = open("foquspsuadeclient.log", "a")
    f.write("Get results\n")
    f.close()
    conn.send(["result"])
    msg = conn.recv()
    status = msg[1]
    results = msg[2]
    conn.send(["close"])
    conn.close()
    f = open("foquspsuadeclient.log", "a")
    f.write("Done\n")
    f.close()

    # Write the output file that ALAMO can read
    genOutputFile(outputFile, results)


if __name__ == "__main__":
    main()
