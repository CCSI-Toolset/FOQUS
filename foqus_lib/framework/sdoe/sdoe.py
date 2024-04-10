#################################################################################
# FOQUS Copyright (c) 2012 - 2024, by the software owners: Oak Ridge Institute
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
import configparser
import logging
import os
import platform
import re
import tempfile
import time
from typing import Tuple, Dict

from dask.distributed import get_client
import numpy as np
import pandas as pd
from python_tsp.exact import solve_tsp_dynamic_programming

from foqus_lib.framework.uq.Common import Common
from foqus_lib.framework.uq.ResponseSurfaces import ResponseSurfaces

from .df_utils import load, write


def save(fnames: Dict, results: Dict, elapsed_time: float, irsf: bool = False):
    if irsf:
        write(fnames["des"], results["des"])
        print("Designs saved to {}".format(fnames["des"]))
        write(fnames["pf"], results["pareto_front"])
        print("Pareto Front saved to {}".format(fnames["pf"]))

    else:
        write(fnames["cand"], results["best_cand"], index=True)
        print("Candidates saved to {}".format(fnames["cand"]))
        np.save(fnames["dmat"], results["best_dmat"])
        print(
            (
                "d={}, n={}: best_val={}, elapsed_time={}s".format(
                    results["design_size"],
                    results["num_restarts"],
                    results["best_val"],
                    elapsed_time,
                )
            )
        )
        print("Candidate distances saved to {}".format(fnames["dmat"]))


def run(config_file: str, nd: int, test: bool = False) -> Tuple[Dict, Dict, float]:
    # parse config file
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_file)

    mode = config["METHOD"]["mode"]
    nr = int(config["METHOD"]["number_random_starts"])

    hfile = config["INPUT"]["history_file"]
    cfile = config["INPUT"]["candidate_file"]
    include = [s.strip() for s in config["INPUT"]["include"].split(",")]

    max_vals = [float(s) for s in config["INPUT"]["max_vals"].split(",")]
    min_vals = [float(s) for s in config["INPUT"]["min_vals"].split(",")]

    types = [s.strip() for s in config["INPUT"]["types"].split(",")]
    difficulty = [s.strip() for s in config["INPUT"]["difficulty"].split(",")]
    type_idx = types.index("Index")
    diff_no_idx = difficulty.copy()
    del diff_no_idx[type_idx]
    # 'Input' columns
    idx = [x for x, t in zip(include, types) if t == "Input"]
    # 'Index' column (should only be one)
    id_ = [x for x, t in zip(include, types) if t == "Index"]
    if id_:
        assert (
            len(id_) == 1
        ), "Multiple INDEX columns detected. There should only be one INDEX column."
        id_ = id_[0]
    else:
        id_ = None

    outdir = config["OUTPUT"]["results_dir"]

    sf_method = config["SF"]["sf_method"]

    # check whether to use dask version of algorithms
    use_dask = False
    try:
        get_client()
        use_dask = True
    except ValueError:
        logging.getLogger("foqus." + __name__).warning(
            "Unable to load Dask client, continuing without it using original algorithms"
        )
        pass

    if sf_method == "nusf":
        # 'Weight' column (should only be one)
        idw = [x for x, t in zip(include, types) if t == "Weight"]
        assert (
            len(idw) == 1
        ), "Multiple WEIGHT columns detected. There should only be one WEIGHT column."
        idw = idw[0]

        weight_mode = config["WEIGHT"]["weight_mode"]
        assert weight_mode == "by_user", (
            "WEIGHT_MODE {} not recognized for NUSF. "
            "Only BY_USER is currently supported.".format(weight_mode)
        )

        scale_method = config["SF"]["scale_method"]
        assert scale_method in ["direct_mwr", "ranked_mwr"]
        mwr_values = [int(s) for s in config["SF"]["mwr_values"].split(",")]

        args = {
            "icol": id_,
            "xcols": idx,
            "wcol": idw,
            "max_iterations": 100,
            "mwr_values": mwr_values,
            "scale_method": scale_method,
        }
        if use_dask:
            from .nusf_dask import criterion
        else:
            from .nusf import criterion

    if sf_method == "usf":
        scl = np.array([ub - lb for ub, lb in zip(max_vals, min_vals)])
        args = {
            "icol": id_,
            "xcols": idx,
            "scale_factors": pd.Series(scl, index=include),
        }
        if use_dask:
            from .usf_dask import criterion
        else:
            from .usf import criterion

    if sf_method == "irsf":
        args = {
            "max_iterations": 1000,
            "ws": np.linspace(0.1, 0.9, 5),
            "icol": id_,
            "idx": idx,
            "idy": [x for x, t in zip(include, types) if t == "Response"],
        }
        from .irsf import criterion

    # create outdir as needed
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # load candidates
    if cfile:
        cand = load(cfile, index=id_)
        if len(include) == 1 and include[0] == "all":
            include = list(cand)

    # load history
    if hfile != "":
        hist = load(hfile, index=id_)
    else:
        hist = None

    # do a quick test to get an idea of runtime
    if test:
        if sf_method == "irsf":
            # WHY: the various criterion() function assigned conditionally have slightly different signature
            # irsf.criterion supports the `test` kwarg, so the function is called correctly in this branch
            # but pylint reports an error because it does not support conditionals
            # pylint: disable=unexpected-keyword-arg
            results = criterion(cand, args, nr, nd, mode=mode, hist=hist, test=True)
            # pylint: enable=unexpected-keyword-arg
            return results["t1"], results["t2"]
        else:
            t0 = time.time()
            criterion(cand, args, nr, nd, mode=mode, hist=hist)
            elapsed_time = time.time() - t0
            if use_dask:
                return (
                    elapsed_time - 1.4
                )  # Dask startup skews the test results so remove that
            return elapsed_time

    # otherwise, run sdoe for real
    t0 = time.time()
    results = criterion(cand, args, nr, nd, mode=mode, hist=hist)
    elapsed_time = time.time() - t0

    # save the output
    if sf_method == "nusf":
        fnames = {}
        for mwr in mwr_values:
            suffix = "d{}_n{}_m{}_{}".format(nd, nr, mwr, "+".join(include))
            fnames[mwr] = {
                "cand": os.path.join(outdir, "nusf_{}.csv".format(suffix)),
                "dmat": os.path.join(outdir, "nusf_dmat_{}.npy".format(suffix)),
            }
            save(fnames[mwr], results[mwr], elapsed_time)
            if all(x == "Hard" for x in diff_no_idx):
                rank(fnames[mwr])
            elif any(x == "Hard" for x in diff_no_idx):
                order_blocks(fnames[mwr], difficulty)

    if sf_method == "usf":
        suffix = "d{}_n{}_{}".format(nd, nr, "+".join(include))
        fnames = {
            "cand": os.path.join(outdir, "usf_{}.csv".format(suffix)),
            "dmat": os.path.join(outdir, "usf_dmat_{}.npy".format(suffix)),
        }
        save(fnames, results, elapsed_time)
        if all(x == "Hard" for x in diff_no_idx):
            rank(fnames)
        elif any(x == "Hard" for x in diff_no_idx):
            order_blocks(fnames, difficulty)

    if sf_method == "irsf":
        fnames = {}
        for design in range(1, results["num_designs"] + 1):
            suffix = "design{}_d{}_n{}_{}".format(design, nd, nr, "+".join(include))
            suffix_pareto = "paretoFront_d{}_n{}_{}".format(nd, nr, "+".join(include))
            fnames[design] = {
                "des": os.path.join(outdir, "irsf_{}.csv".format(suffix)),
                "pf": os.path.join(outdir, "irsf_{}.csv".format(suffix_pareto)),
            }
            sub_results = {
                "pareto_front": results["pareto_front"],
                "des": results["des"][design],
            }

            save(fnames[design], sub_results, elapsed_time, irsf=True)

    return fnames, results, elapsed_time


def rank(fnames):
    """return fnames ranked"""
    dist_mat = np.load(fnames["dmat"])

    permutation, _distance = solve_tsp_dynamic_programming(dist_mat)

    # retrieve ranked list
    cand = load(fnames["cand"])
    ranked_cand = cand.loc[permutation]

    # save the output
    fname_ranked = fnames["cand"]

    write(fname_ranked, ranked_cand)

    return fname_ranked


def order_blocks(fnames, difficulty):
    # load candidate set
    cand = load(fnames["cand"])
    cols = list(cand.columns)

    diff_arr = np.array(difficulty)
    diff_idx_arr = np.where(diff_arr == "Hard")[0]
    diff_idx = list(diff_idx_arr)

    col_order = []
    for i in diff_idx:
        col_order.append(cols[i])

    sorted_cand = cand.sort_values(col_order)

    # save the output
    fname_blocks = fnames["cand"]

    write(fname_blocks, sorted_cand)

    return fname_blocks


def dataImputation(fname: str, y: int, rsMethodName: str, eval_fname: str) -> str:
    """
    args: fname, y, rsMethodName, eval_fname
    returns: outfile filename
    """
    rsIndex = ResponseSurfaces.getEnumValue(rsMethodName)

    # write script
    f = tempfile.SpooledTemporaryFile(mode="wt")
    if platform.system() == "Windows":
        import win32api

        fname = win32api.GetShortPathName(fname)

    f.write("load %s\n" % fname)  # load data
    cmd = "rscreate"
    f.write("%s\n" % cmd)
    f.write("%d\n" % y)  # select output
    f.write("%d\n" % rsIndex)  # select response surface

    cmd = "rseval"
    f.write("%s\n" % cmd)
    f.write("y\n")  # data taken from register
    f.write("%s\n" % eval_fname)
    f.write("y\n")  # do fuzzy evaluation
    f.write("y\n")  # write data to file
    f.write("quit\n")
    f.seek(0)

    # invoke psuade
    out, error = Common.invokePsuade(f)
    f.close()
    if error:
        return None

    outfile = "eval_sample"
    assert os.path.exists(outfile)

    return outfile


def readEvalSample(fileName: str) -> Tuple[np.ndarray, np.ndarray, int, int]:
    """
    args: fileName
    returns: inputArray, outputArray, numInputs, numOutputs
    """
    f = open(fileName, "r")
    lines = f.readlines()
    f.close()

    # remove empty lines
    lines = [line for line in lines if len(line.strip()) > 0]

    # ignore text preceded by '%'
    c = "%"
    lines = [line.strip().split(c)[0] for line in lines if not line.startswith(c)]
    nlines = len(lines)

    # process header
    k = 0
    header = lines[k]
    nums = header.split()
    numSamples = int(nums[0])
    numInputs = int(nums[1])
    numOutputs = 0
    if len(nums) == 3:
        numOutputs = int(nums[2])

    # process samples
    data = [None] * numSamples
    for i in range(nlines - k - 1):
        line = lines[i + k + 1]
        nums = line.split()
        data[i] = [float(x) for x in nums]

    # split samples
    data = np.array(data)
    inputData = data[:, :numInputs]
    inputArray = np.array(inputData, dtype=float, ndmin=2)
    outputArray = None
    if numOutputs:
        outputData = data[:, numInputs:]
        outputArray = np.array(outputData, dtype=float, ndmin=2)

    return inputArray, outputArray, numInputs, numOutputs
