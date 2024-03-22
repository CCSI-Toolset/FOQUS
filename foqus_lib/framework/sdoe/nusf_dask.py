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
import time
from typing import Dict, List, Optional, Tuple, TypedDict, Union

import dask.bag as db
import numpy as np
import pandas as pd  # only used for the final output of criterion
from scipy.stats import rankdata

from .distance import compute_dist, compute_min_params
from .nusf import compute_dmat, scale_xs, scale_y, update_min_dist


def criterion(
    cand: pd.DataFrame,  # candidates
    args: TypedDict(
        "args",
        {
            "icol": str,
            "xcols": List,
            "wcol": str,
            "max_iterations": int,
            "mwr_values": List,
            "scale_method": str,
        },
    ),  # maximum number of iterations, mwr values, scale method, index types
    nr: int,  # number of restarts (each restart uses a random set of <nd> points)
    nd: int,  # design size <= len(candidates)
    mode: str = "maximin",
    hist: Optional[pd.DataFrame] = None,
    rand_seed: Union[int, None] = None,
) -> Dict:

    ncand = len(cand)
    if hist is not None:
        nhist = len(hist)
    assert nd <= ncand, "Number of designs exceeds number of available candidates."

    mode = mode.lower()
    assert (
        mode == "maximin"
    ), "MODE {} not recognized for NUSF. Only MAXIMIN is currently supported.".format(
        mode
    )

    T = args["max_iterations"]
    mwr_vals = args["mwr_values"]
    scale_method = args["scale_method"]

    # index types
    idx_np = [cand.columns.get_loc(i) for i in args["xcols"]]
    idw_np = cand.columns.get_loc(args["wcol"])

    cand_np_ = cand.to_numpy()
    cand_np_unscaled = cand_np_.copy()

    # Combine candidates and history before scaling
    if hist is None:
        cand_np_, _xmin, _xmax = scale_xs(cand_np_, idx_np)
    else:
        cand_np_, _xmin, _xmax = scale_xs(
            np.concatenate((cand_np_, hist.to_numpy())), idx_np
        )

    rand_gen = np.random.default_rng(rand_seed)

    def step(
        mwr_tuple: Tuple[int, List[int], np.ndarray, Union[np.ndarray, None]]
    ) -> Dict:
        mwr, rands, cand_np, hist_np = mwr_tuple

        best_cand = []
        best_md = 0
        best_mties = 0
        best_index = []

        t0 = time.time()

        def choose(rand_index):
            # extract the <nd> rows
            rcand = cand_np[rand_index]
            dmat = compute_dmat(rcand, idx_np, idw_np, hist=hist_np)
            md, mdpts, mties = compute_min_params(dmat)

            update_ = True
            t = 0

            while update_ and (t < T):

                (
                    rcand_,
                    md_,
                    mdpts_,
                    mties_,
                    dmat_,
                    added_,
                    removed_,
                    update_,
                ) = update_min_dist(
                    rcand,
                    cand_np,
                    ncand,
                    idx_np,
                    idw_np,
                    md,
                    mdpts,
                    mties,
                    dmat,
                    hist=hist_np,
                    rand_seed=rand_seed + rand_index if rand_seed is not None else None,
                )

                if update_:
                    rcand = rcand_
                    md = md_
                    mdpts = mdpts_
                    mties = mties_
                    dmat = dmat_
                    if added_:
                        rand_index[removed_] = added_

                t += 1
            return {
                "index": rand_index,
                "cand": rcand,
                "md": md,
                "mdpts": mdpts,
                "mties": mties,
                "dmat": dmat,
            }

        for x in db.from_sequence(rands).map(choose):
            if (x["md"] > best_md) or (
                (x["md"] == best_md) and (x["mties"] < best_mties)
            ):
                best_index = x["index"]
                best_cand = x["cand"]
                best_md = x["md"]
                best_mdpts = x["mdpts"]
                best_mties = x["mties"]
                best_dmat = x["dmat"]
            print("Best minimum distance for this random start: {}".format(best_md))

        elapsed_time = time.time() - t0

        # no need to inverse-scale; can just use the indices to look up original rows in cand_
        best_cand_unscaled = cand_np_unscaled[best_index]

        best_cand = pd.DataFrame(best_cand, index=best_index, columns=list(cand))
        best_cand_unscaled = pd.DataFrame(
            best_cand_unscaled, index=best_index, columns=list(cand)
        )

        results = {
            "best_cand_scaled": best_cand,
            "best_cand": best_cand_unscaled,
            "best_index": best_index,
            "best_val": best_md,
            "best_mdpts": best_mdpts,
            "best_mties": best_mties,
            "best_dmat": best_dmat,
            "mode": mode,
            "design_size": nd,
            "num_restarts": nr,
            "mwr": mwr,
            "elapsed_time": elapsed_time,
        }

        return results

    rands, cand_nps, hist_nps = [], [], []
    for mwr in mwr_vals:
        cand_np = scale_y(scale_method, mwr, cand_np_, idw_np)

        if hist is None:
            hist_np = None
        else:
            hist_np = cand_np[-nhist:]
            cand_np = cand_np[:ncand]

        wts = cand_np[:, idw_np]
        wts_sum = np.sum(wts)
        prob = wts / wts_sum
        rand = []
        for i in range(nr):
            # sample without replacement <nd> indices
            rand.append(rand_gen.choice(ncand, nd, replace=False, p=prob))
        rands.append(rand)
        cand_nps.append(cand_np)
        hist_nps.append(hist_np)

    results = db.from_sequence(zip(mwr_vals, rands, cand_nps, hist_nps)).map(step)
    return dict(zip(mwr_vals, results.compute()))
