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
import os
import tempfile
import re
import platform

from foqus_lib.framework.uq.RSAnalyzer import RSAnalyzer
from foqus_lib.framework.uq.ResponseSurfaces import ResponseSurfaces
from foqus_lib.framework.uq.Common import Common

dname = os.path.join(os.getcwd(), "ODOE_files")


def writeSample(fname, data):
    xdat = data.getInputData()
    RSAnalyzer.writeRSsample(fname, xdat, row=True)
    return fname


def getSampleShape(data):
    nrows = data.getNumSamples()
    ncols = data.getNumInputs()
    return nrows, ncols


def rseval(rsdata, pdata, cdata, rstypes):
    # rsdata: SampleData containing the RS training data
    # pdata: SampleData containing the sample representing the prior over uncertain variables
    # cdata: SampleData containing the candidate set
    # rstypes: dictionary with output index as key and string denote RS types as value; possible values: ['MARS',
    # 'linear', 'quadratic', 'cubic']

    # convert the data into psuade files
    cfile = os.path.join(dname, "CandidateSet")
    pfile = os.path.join(dname, "PriorSample")
    rsfile = os.path.join(dname, "RSTrainData")
    cfile = writeSample(cfile, cdata)
    pfile = writeSample(pfile, pdata)
    y = 1
    rsfile = RSAnalyzer.writeRSdata(rsfile, y, rsdata)

    cmd = "odoeu_rseval"

    inputNames = rsdata.getInputNames()
    priorNames = pdata.getInputNames()
    priorIndices = []
    for name in priorNames:
        priorIndices.append(inputNames.index(name) + 1)

    rs_list = ["MARS", "linear", "quadratic", "cubic", "GP3"]

    # extract the indices of RS types for outputs
    rs_idx = [ResponseSurfaces.getEnumValue(s) for s in rs_list]
    rsdict = dict(zip(rs_list, rs_idx))

    # write script
    f = tempfile.SpooledTemporaryFile(mode="wt")
    if platform.system() == "Windows":
        import win32api

        cfile = win32api.GetShortPathName(cfile)
        pfile = win32api.GetShortPathName(pfile)
        rsfile = win32api.GetShortPathName(rsfile)
    f.write("load %s\n" % rsfile)
    f.write("%s\n" % cmd)
    f.write("y\n")
    for i in priorIndices:
        f.write(
            "%d\n" % i
        )  # specify random variables, should be consistent with vars in prior
    f.write("0\n")  # 0 to proceed
    f.write("%s\n" % pfile)  # file containing the prior sample (psuade sample format)
    f.write("%s\n" % cfile)  # file containing the candidate set (psuade sample format)
    for rs in rstypes:  # for each output, specify RS index
        f.write("%d\n" % rsdict[rstypes[rs]])
    f.write("quit\n")
    f.seek(0)

    # invoke psuade
    out, error = Common.invokePsuade(f)
    if error:
        return None

    outfile = "odoeu_rseval.out"
    assert os.path.exists(outfile)
    return outfile


def odoeu(
    cdata,
    cfile,
    pdata,
    rsdata,
    rstypes,
    method,
    opt,
    nd,
    max_iters=100,
    multi_starts=20,
    edata=None,
):

    # cdata: SampleData containing the original candidate set
    # cfile: PSUADE sample file containing the original candidates with the mean/std of the selected output
    # cdata: SampleData containing the candidate set
    # pdata: SampleData containing the sample representing the prior over uncertain variables
    # rsdata: SampleData containing the RS training data
    # rstypes: dictionary with output index as key and string denote RS types as value; possible values: ['MARS',
    # 'linear', 'quadratic', 'cubic']
    # nd: int denoting design size
    # max_iters: int denoting maximum number of iterations for the optimization routine [default: 100]
    # multi_starts: int denoting number of multi-starts for the optimization [default: 20]
    # edata: SampleData containing the evaluation set

    # parse params
    methods = ["fisher", "bayesian"]
    assert method in methods
    opts = ["G", "I", "D", "A", "E"]
    assert opt in opts
    optdict = dict(zip(opts, range(1, len(opts) + 1)))
    opt_index = optdict[opt]
    if method == "fisher":
        cmd = "odoeu_foptn"
    elif method == "bayesian":
        cmd = "odoeu_boptn"

    # TO DO for Pedro: check in GUI?
    # maximum iterations should be in range [100, 1000]
    assert 99 < max_iters < 1001

    # initialize constants
    ncand = cdata.getNumSamples()
    nOutputs = rsdata.getNumOutputs()
    nprior = pdata.getNumSamples()

    # extract the indices of random variables
    inputNames = rsdata.getInputNames()
    priorNames = pdata.getInputNames()
    priorIndices = []
    for name in priorNames:
        priorIndices.append(inputNames.index(name) + 1)

    rs_list = ["MARS", "linear", "quadratic", "cubic", "GP3"]
    # TO DO for Pedro: check in GUI?
    # this checks to see if user is trying to pass an unsupported RS
    for rs in rstypes:
        assert rstypes[rs] in rs_list
    assert len(rstypes) == nOutputs

    # extract the indices of RS types for outputs
    rs_idx = [ResponseSurfaces.getEnumValue(s) for s in rs_list]
    rsdict = dict(zip(rs_list, rs_idx))

    # convert the data into psuade files
    pfile = os.path.join(dname, "PriorSample")
    rsfile = os.path.join(dname, "RSTrainData")
    pfile = writeSample(pfile, pdata)
    efile = os.path.join(dname, "EvaluationSet")
    if edata is None:
        efile = writeSample(efile, cdata)
    else:
        efile = writeSample(efile, edata)
    y = 1
    rsfile = RSAnalyzer.writeRSdata(rsfile, y, rsdata)

    # write script
    f = tempfile.SpooledTemporaryFile(mode="wt")
    if platform.system() == "Windows":
        import win32api

        pfile = win32api.GetShortPathName(pfile)
        rsfile = win32api.GetShortPathName(rsfile)
        efile = win32api.GetShortPathName(efile)

    f.write("%s\n" % cmd)
    f.write("y\n")
    f.write("%d\n" % opt_index)  # choose G, I, D, A, E
    f.write("%d\n" % ncand)  # size of the candidate set
    f.write("%d\n" % nd)  # design size
    f.write(
        "%d\n" % max_iters
    )  # max number of iterations, must be greater or equal to 100
    f.write("y\n")  # yes multi-start optimization
    f.write("%d\n" % multi_starts)  # number of starts
    f.write("%s\n" % rsfile)  # file containing RS training data (psuade format)
    for i in priorIndices:
        f.write(
            "%d\n" % i
        )  # specify random variables, should be consistent with vars in prior
    f.write("0\n")  # 0 to proceed
    f.write("%s\n" % pfile)  # file containing the prior sample (psuade sample format)
    if method == "fisher":
        if nprior > 1000:
            f.write("y\n")  # collapsing prior sample into smaller sample when g.t. 1000
            f.write("2\n")
            f.write("1000\n")
        else:
            f.write(
                "n\n"
            )  # no collapsing prior sample into smaller sample when l.t.e. 1000
    f.write("%s\n" % cfile)  # file containing the candidate set (psuade sample format)
    f.write(
        "%s\n" % efile
    )  # ... evaluate the optimality values on the (same) candidate set
    for rs in rstypes:  # for each output, specify RS index
        f.write("%d\n" % rsdict[rstypes[rs]])
        # TO DO: as we add more RS, may need to port more code from RSAnalyzer.py to handle different RS types
    f.write("quit\n")
    f.seek(0)

    # invoke psuade
    out, error = Common.invokePsuade(f)
    if error:
        return None

    # parse output
    best_indices = None
    best_optval = None
    m = re.findall(cmd + r" best selection = (\d+ \d+)", out)
    if m:
        best_indices = [i for i in m[0].split()]
        s = r"\s*".join([i for i in best_indices])
        best_optvals = re.findall(s + r"\s*===> output = (\S*)", out)

        best_indices = [int(i) for i in best_indices]
        best_optval = float(best_optvals[0])

    return best_indices, best_optval
