#################################################################################
# FOQUS Copyright (c) 2012 - 2025, by the software owners: Oak Ridge Institute
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
from typing import List, Optional, TypedDict

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.spatial.distance import pdist
from scipy.spatial.distance import squareform as scipy_squareform

from .irsf import unit_scale, inv_unit_scale


def criterion(
    cand: pd.DataFrame,
    args: TypedDict(
        "args",
        {
            "icol": str,
            "xcols": List,
            "min_scale_factors": pd.Series,
            "max_scale_factors": pd.Series,
        },
    ),
    nd: int,
    max_iter: int,
    hist: Optional[pd.DataFrame] = None,
    test: bool = False,
) -> TypedDict(
    "results",
    {
        "design": pd.DataFrame,
        "measure": float,  # Square the measure for consistency with R version
        "n_total": int,
        "elapsed_time": float,
    },
):
    if hist is None:
        result = maxpro_lhd(nd, len(args["xcols"]), itermax=max_iter)
        if not test:
            design = result["Design"]
            time_rec = result["time_rec"]
            n_total = result["ntotal"]
            result = maxpro(design)
            result["time_rec"] = time_rec
            result["ntotal"] = n_total

        # transform design in numpy array format to pandas dataframe
        column_names = args["xcols"]
        min_scaling_factors = args["min_scale_factors"][column_names]
        max_scaling_factors = args["max_scale_factors"][column_names]

        df = (
            pd.DataFrame(result["Design"], columns=column_names)
            * (max_scaling_factors - min_scaling_factors)
            + min_scaling_factors
        )
    else:
        idx = args["xcols"]
        cand_xs = cand[idx].to_numpy()
        hist_xs = hist[idx].to_numpy()

        scaled_cand_xs, cand_xmin, cand_xmax = unit_scale(cand_xs)
        scaled_hist_xs, hist_xmin, hist_xmax = unit_scale(hist_xs)
        xmin = np.minimum(cand_xmin, hist_xmin)
        xmax = np.maximum(cand_xmax, hist_xmax)
        if test:
            result = maxpro_augment(scaled_hist_xs, scaled_cand_xs, 3)
            result["ntotal"] = "N/A"
        else:
            result = maxpro_augment(scaled_hist_xs, scaled_cand_xs, nd)
            result["ntotal"] = "N/A"

        # get new points indices
        new_points = result["Design"][len(hist_xs) :]
        indices = find_indices(new_points, scaled_cand_xs)

        # Reverse scaling
        reversed_design = inv_unit_scale(new_points, xmin, xmax)

        # Insert indices as first column in array
        final_design = np.column_stack([indices, reversed_design])

        # transform design in numpy array format to pandas dataframe
        column_names = ["__id"] + args["xcols"]

        df = pd.DataFrame(final_design, columns=column_names)

    results = {
        "design": df,
        "measure": result["measure"],
        "n_total": result["ntotal"],
        "elapsed_time": result["time_rec"],
    }

    return results


def maxpro_lhd(n, p, s=2, temp0=0, nstarts=1, itermax=400, total_iter=1000000):
    """
    Create a MaxPro Latin Hypercube Design

    Parameters
    ----------
    n : int
        Number of runs (design points)
    p : int
        Number of factors (dimensions)
    s : int, optional
        Exponent in MaxPro criterion, default is 2
    temp0 : float, optional
        Initial temperature for simulated annealing
        If 0, will be calculated automatically
    nstarts : int, optional
        Number of random starts, default is 1
    itermax : int, optional
        Maximum number of iterations per start, default is 400
    total_iter : int, optional
        Total maximum number of iterations, default is 1000000

    Returns
    -------
    dict
        A dictionary containing:
        - Design: Optimized Latin Hypercube Design with values in [0,1]
        - temp0: The temperature used
        - measure: MaxPro criterion value
        - time_rec: Time taken for optimization
        - ntotal: Total number of iterations performed
    """

    # Call core implementation
    design, measure, itotal, time_rec = maxpro_lhd_core(
        n, p, s, temp0, nstarts, itermax, total_iter
    )

    # Return results in a dictionary
    return {
        "Design": design,
        "temp0": temp0,
        "measure": measure**2,  # Square the measure for consistency with R version
        "time_rec": time_rec,
        "ntotal": itotal,
    }


def maxpro(initial_design, s=2, iteration=10, eps=1e-8):
    """
    Perform Maximum Projection (MaxPro) design optimization

    Parameters
    ----------
    initial_design : numpy.ndarray
        Initial design matrix, with rows as design points and columns as factors
    s : int, optional
        Exponent for the MaxPro criterion, default is 2
    iteration : int, optional
        Number of optimization iterations, default is 10
    eps : float, optional
        Small value to prevent division by zero, default is 1e-8

    Returns
    -------
    dict
        A dictionary containing:
        - Design: Optimized design matrix
        - measure: MaxPro criterion value
    """
    # Convert to numpy array and normalize to [0,1]
    D0 = np.asarray(initial_design)
    if D0.ndim == 1:
        D0 = D0.reshape(-1, 1)
    n, p = D0.shape

    # Normalize to [0,1] with safety check
    col_ranges = D0.max(axis=0) - D0.min(axis=0)
    col_ranges = np.maximum(col_ranges, eps)  # Prevent division by zero
    D0 = (D0 - D0.min(axis=0)) / col_ranges

    def fgr(x):
        # Reshape design matrix
        D = x.reshape(n, p)

        # Calculate distances in each dimension and multiply
        dis = pdist(D[:, 0].reshape(-1, 1)) ** s
        # Add small epsilon to prevent zero distances
        dis = np.maximum(dis, eps)

        for j in range(1, p):
            dis_j = pdist(D[:, j].reshape(-1, 1)) ** s
            dis_j = np.maximum(dis_j, eps)  # Prevent zero distances
            dis = dis * dis_j

        # Ensure dis is never zero
        dis = np.maximum(dis, eps)

        # Create distance matrix for calculations
        dist_mat = squareform(dis)
        # Set diagonal to a small positive value instead of 1
        np.fill_diagonal(dist_mat, eps)

        # Objective function (log of sum of reciprocal distances)
        fn = np.sum(1 / dis)

        # Prevent log of zero or negative values
        fn = max(fn, eps)
        lfn = np.log(fn)

        # Calculate gradient
        I = np.eye(n)
        gradient = np.zeros((n, p))

        for j in range(p):
            # Calculate differences in dimension j
            D_col = D[:, j].reshape(-1, 1)
            A = squareform(pdist(D_col, lambda u, v: u - v))

            # Prevent division by zero in A
            A_safe = np.where(np.abs(A) < eps, eps * np.sign(A), A)
            np.fill_diagonal(A_safe, eps)

            # Calculate gradient for dimension j with safety checks
            term1 = 1 / A_safe
            term2 = 1 / dist_mat

            # Remove diagonal elements by subtracting identity
            gradient_term = np.dot(term1 - I, term2 - I)
            gradient[:, j] = np.diag(gradient_term)

        # Scale gradient and flatten with safety check
        fn = max(fn, eps)  # Ensure fn is not zero
        G = s * gradient / fn
        G = G.flatten()

        # Replace any NaN or inf values
        G = np.nan_to_num(G, nan=0.0, posinf=1e6, neginf=-1e6)

        return lfn, G

    def objective(x):
        obj, _ = fgr(x)
        return obj

    def gradient(x):
        _, grad = fgr(x)
        return grad

    # Start with initial design
    D1 = D0.copy()
    x0 = D1.flatten()

    # Perform optimization iterations
    for i in range(iteration):
        try:
            # Use L-BFGS-B optimizer
            result = minimize(
                objective,
                x0,
                method="L-BFGS-B",
                jac=gradient,
                bounds=[(0, 1) for _ in range(n * p)],
                options={"maxiter": 100, "ftol": 1e-9},
            )

            # Update design
            D1 = result.x.reshape(n, p)
            x0 = D1.flatten()

        except (np.linalg.LinAlgError, ValueError) as e:
            print(f"Optimization warning at iteration {i}: {e}")
            # Continue with current design
            break

    # Calculate final criterion
    q1 = prod_criterion(D1, s)

    return {"Design": D1, "measure": q1}


def maxpro_augment(
    exist_design, cand_design, n_new, p_disnum=0, l_disnum=None, p_nom=0, l_nom=None
):
    """
    Sequentially augment an existing design with new points from a candidate set

    Parameters
    ----------
    exist_design : numpy.ndarray
        Existing design matrix, with rows as design points and columns as factors
    cand_design : numpy.ndarray
        Candidate design points from which to select new points
    n_new : int
        Number of new points to add
    p_disnum : int, optional
        Number of discrete numeric variables, default is 0
    l_disnum : list, optional
        List containing number of levels for each discrete numeric variable
    p_nom : int, optional
        Number of nominal variables, default is 0
    l_nom : list, optional
        List containing number of levels for each nominal variable

    Returns
    -------
    dict
        A dictionary containing:
        - Design: Augmented design matrix
        - measure: MaxPro criterion value
        - time_rec: Time taken for augmentation
    """
    # Convert inputs to numpy arrays
    exist_design = np.asarray(exist_design)
    cand_design = np.asarray(cand_design)

    # Check dimensions
    if exist_design.ndim == 1:
        exist_design = exist_design.reshape(1, -1)

    if cand_design.shape[1] != exist_design.shape[1]:
        raise ValueError(
            "Candidate design points and existing design points have different dimensions."
        )

    # Extract dimensions
    k = exist_design.shape[1]
    p_cont = k - p_disnum - p_nom

    if p_cont < 0:
        raise ValueError(
            "Input error: Summation of p_disnum and p_nom exceeds the total number of columns."
        )

    # Create lambda values (weights for different variable types)
    lambda_vals = np.zeros(k)

    # Handle discrete numeric variables
    if p_disnum > 0 and p_nom == 0:
        if l_disnum is None:
            combined = np.vstack((exist_design, cand_design))
            l_disnum = [
                len(np.unique(combined[:, p_cont + i])) for i in range(p_disnum)
            ]

        if len(l_disnum) != p_disnum:
            raise ValueError("Input error: Length of l_disnum does not match p_disnum.")

        lambda_vals[p_cont : p_cont + p_disnum] = 1.0 / np.array(l_disnum)

    # Handle nominal variables
    if p_disnum == 0 and p_nom > 0:
        if l_nom is None:
            combined = np.vstack((exist_design, cand_design))
            l_nom = [len(np.unique(combined[:, p_cont + i])) for i in range(p_nom)]

        if len(l_nom) != p_nom:
            raise ValueError("Input error: Length of l_nom does not match p_nom.")

        lambda_vals[p_cont:] = 1.0 / np.array(l_nom)

    # Handle both discrete numeric and nominal variables
    if p_disnum > 0 and p_nom > 0:
        if l_nom is None:
            combined = np.vstack((exist_design, cand_design))
            l_nom = [len(np.unique(combined[:, k - p_nom + i])) for i in range(p_nom)]

        if l_disnum is None:
            combined = np.vstack((exist_design, cand_design))
            l_disnum = [
                len(np.unique(combined[:, p_cont + i])) for i in range(p_disnum)
            ]

        if len(l_nom) != p_nom:
            raise ValueError("Input error: Length of l_nom does not match p_nom.")

        if len(l_disnum) != p_disnum:
            raise ValueError("Input error: Length of l_disnum does not match p_disnum.")

        lambda_vals[p_cont : p_cont + p_disnum] = 1.0 / np.array(l_disnum)
        lambda_vals[k - p_nom :] = 1.0 / np.array(l_nom)

    # Start timer
    t00 = time.time()

    # Call core augmentation function
    augmented_design, measure, success_flag = maxpro_augment_core(
        lambda_vals, exist_design, cand_design, n_new, p_nom, s=2
    )

    # End timer
    t01 = time.time()
    time_rec = t01 - t00

    if success_flag == 0:
        print(
            "Note: Not enough candidate rows. For a continuous factor, any new added level must be distinct "
            "from the existing ones in the design. If repeated levels are needed, please specify the factor "
            "as discrete numeric."
        )

    return {
        "Design": augmented_design,
        "measure": measure**2,  # Square the measure for consistency with R version
        "time_rec": time_rec,
    }


def prod_criterion(D, s=2):
    """
    Calculate product space MaxPro criterion

    Parameters
    ----------
    D : np.ndarray
        Design matrix with shape (n, p)
    s : int, optional
        Exponent in MaxPro criterion

    Returns
    -------
    float
        MaxPro criterion value (squared)
    """
    n, p = D.shape

    # Calculate log distances for each dimension
    log_dist = s * np.log(pdist(D[:, 0].reshape(-1, 1)))
    for j in range(1, p):
        log_dist += s * np.log(pdist(D[:, j].reshape(-1, 1)))

    # Find minimum distance
    i_min = np.argmin(log_dist)

    # Calculate criterion
    value = -log_dist[i_min] + np.log(np.sum(np.exp(log_dist[i_min] - log_dist)))

    # Scale by dimensions
    n_choose_2 = n * (n - 1) / 2
    return np.exp((value - np.log(n_choose_2)) / p)


def squareform(v):
    """
    Convert a condensed distance vector to a square distance matrix.
    Simplified version for clarity.

    Parameters
    ----------
    v : np.ndarray
        Condensed distance vector from pdist

    Returns
    -------
    np.ndarray
        Square-form distance matrix
    """

    return scipy_squareform(v)


def slhd(m, t, k):
    """
    Generate Sliced Latin Hypercube Design

    Parameters
    ----------
    m : int
        Number of runs per slice
    t : int
        Number of slices
    k : int
        Number of factors

    Returns
    -------
    np.ndarray
        The SLHD matrix with shape (m*t, k)
    """
    n = m * t
    slhd_mat = np.zeros((k, n), dtype=np.int32)

    # First column is repeated blocks of 1:m
    for js in range(t):
        for j2 in range(m):
            slhd_mat[0, m * js + j2] = j2 + 1

    # Remaining columns are random permutations
    for j1 in range(k - 1):
        for jss in range(t):
            r = list(range(1, m + 1))
            for c in range(m):
                # Random choice from remaining values
                idx = int(np.random.randint(0, m - c))
                slhd_mat[j1 + 1, jss * m + c] = r[idx]
                # Remove the selected value
                r.pop(idx)

    # Convert to expanded indices
    slhds = np.zeros((k, n), dtype=np.int32)
    for j3 in range(k):
        for j5 in range(m):
            xsubs = j5 * t + 1
            for j4 in range(n):
                if slhd_mat[j3, j4] == (j5 + 1):
                    slhds[j3, j4] = xsubs
                    xsubs += 1

    return slhds


def dist_matrix(A, n, k, s=2):
    """
    Compute distance matrix for MaxPro criterion

    Parameters
    ----------
    A : np.ndarray
        Design matrix with shape (k, n)
    n : int
        Number of rows
    k : int
        Number of columns
    s : int, optional
        Exponent in MaxPro criterion

    Returns
    -------
    np.ndarray
        Vector of pairwise distances (upper triangular of distance matrix)
    """
    dim = int(n * (n - 1) / 2)
    d = np.zeros(dim)
    count = 0

    for k1 in range(n - 1):
        for k2 in range(k1 + 1, n):
            for k3 in range(k):
                d[count] += s * np.log(np.abs(float(A[k3, k1] - A[k3, k2])))
            count += 1

    return d


def avgdist(n, k, d, s=2):
    """
    Compute average distance measure for MaxPro criterion

    Parameters
    ----------
    n : int
        Number of rows
    k : int
        Number of columns
    d : np.ndarray
        Vector of pairwise distances
    s : int, optional
        Exponent in MaxPro criterion

    Returns
    -------
    float
        Average distance measure
    """
    dim = int(n * (n - 1) / 2)

    # Find minimum distance
    d_min = np.min(d)

    # Compute average distance
    avgdist_val = np.sum(np.exp(d_min - d))

    # Apply log transform
    avgdist_val = np.log(avgdist_val) - d_min

    # Scale by dimensions
    avgdist_val = np.exp((avgdist_val - np.log(dim)) / (k * s))

    return avgdist_val


def comb_avgdist(n, k, d, s=2):
    """
    Combined average distance for MaxPro criterion

    Parameters
    ----------
    n : int
        Number of rows
    k : int
        Number of columns
    d : np.ndarray
        Vector of pairwise distances
    s : int, optional
        Exponent in MaxPro criterion

    Returns
    -------
    float
        Combined average distance
    """
    return avgdist(n, k, d, s)


def update_dist_matrix(A, n, col, selrow1, selrow2, d, d_old, s=2):
    """
    Update distance matrix after swapping two rows in one column

    Parameters
    ----------
    A : np.ndarray
        Design matrix
    n : int
        Number of rows
    col : int
        Column where swap occurred
    selrow1, selrow2 : int
        Rows that were swapped
    d : np.ndarray
        Current distance vector
    d_old : np.ndarray
        Buffer for storing old distances
    s : int, optional
        Exponent in MaxPro criterion

    Returns
    -------
    None (updates d and d_old in place)
    """
    row1 = min(selrow1, selrow2)
    row2 = max(selrow1, selrow2)

    # Update distances for rows h < row1 < row2
    if row1 > 0:
        for h in range(row1):
            # Calculate positions in condensed distance matrix
            position1 = int(row1 + 1 - ((h + 1) ** 2) / 2 + (n - 0.5) * (h + 1) - n - 1)
            position2 = int(row2 + 1 - ((h + 1) ** 2) / 2 + (n - 0.5) * (h + 1) - n - 1)

            # Save old distances
            d_old[position1] = d[position1]
            d_old[position2] = d[position2]

            # Update distances with the swapped values
            d[position1] = (
                d[position1]
                + s * np.log(np.abs(float(A[col, row1] - A[col, h])))
                - s * np.log(np.abs(float(A[col, row2] - A[col, h])))
            )
            d[position2] = (
                d[position2]
                + s * np.log(np.abs(float(A[col, row2] - A[col, h])))
                - s * np.log(np.abs(float(A[col, row1] - A[col, h])))
            )

    # Update distances for rows row1 < h < row2
    for h in range(row1 + 1, row2):
        position1 = int(h + 1 - ((row1 + 1) ** 2) / 2 + (n - 0.5) * (row1 + 1) - n - 1)
        position2 = int(row2 + 1 - ((h + 1) ** 2) / 2 + (n - 0.5) * (h + 1) - n - 1)

        d_old[position1] = d[position1]
        d_old[position2] = d[position2]

        d[position1] = (
            d[position1]
            + s * np.log(np.abs(float(A[col, row1] - A[col, h])))
            - s * np.log(np.abs(float(A[col, row2] - A[col, h])))
        )
        d[position2] = (
            d[position2]
            + s * np.log(np.abs(float(A[col, row2] - A[col, h])))
            - s * np.log(np.abs(float(A[col, row1] - A[col, h])))
        )

    # Update distances for rows row1 < row2 < h
    if row2 < (n - 1):
        for h in range(row2 + 1, n):
            position1 = int(
                h + 1 - ((row1 + 1) ** 2) / 2 + (n - 0.5) * (row1 + 1) - n - 1
            )
            position2 = int(
                h + 1 - ((row2 + 1) ** 2) / 2 + (n - 0.5) * (row2 + 1) - n - 1
            )

            d_old[position1] = d[position1]
            d_old[position2] = d[position2]

            d[position1] = (
                d[position1]
                + s * np.log(np.abs(float(A[col, row1] - A[col, h])))
                - s * np.log(np.abs(float(A[col, row2] - A[col, h])))
            )
            d[position2] = (
                d[position2]
                + s * np.log(np.abs(float(A[col, row2] - A[col, h])))
                - s * np.log(np.abs(float(A[col, row1] - A[col, h])))
            )


def revert_dist_matrix(n, selrow1, selrow2, d, d_old):
    """
    Revert distance matrix updates

    Parameters
    ----------
    n : int
        Number of rows
    selrow1, selrow2 : int
        Rows that were swapped
    d : np.ndarray
        Current distance vector
    d_old : np.ndarray
        Buffer with old distances

    Returns
    -------
    None (updates d in place)
    """
    row1 = min(selrow1, selrow2)
    row2 = max(selrow1, selrow2)

    # Revert distances for rows h < row1 < row2
    if row1 > 0:
        for h in range(row1):
            position1 = int(row1 + 1 - ((h + 1) ** 2) / 2 + (n - 0.5) * (h + 1) - n - 1)
            position2 = int(row2 + 1 - ((h + 1) ** 2) / 2 + (n - 0.5) * (h + 1) - n - 1)

            d[position1] = d_old[position1]
            d[position2] = d_old[position2]

    # Revert distances for rows row1 < h < row2
    for h in range(row1 + 1, row2):
        position1 = int(h + 1 - ((row1 + 1) ** 2) / 2 + (n - 0.5) * (row1 + 1) - n - 1)
        position2 = int(row2 + 1 - ((h + 1) ** 2) / 2 + (n - 0.5) * (h + 1) - n - 1)

        d[position1] = d_old[position1]
        d[position2] = d_old[position2]

    # Revert distances for rows row1 < row2 < h
    if row2 < (n - 1):
        for h in range(row2 + 1, n):
            position1 = int(
                h + 1 - ((row1 + 1) ** 2) / 2 + (n - 0.5) * (row1 + 1) - n - 1
            )
            position2 = int(
                h + 1 - ((row2 + 1) ** 2) / 2 + (n - 0.5) * (row2 + 1) - n - 1
            )

            d[position1] = d_old[position1]
            d[position2] = d_old[position2]


def update_avgdist(n, k, d, avgdist_old, avgdist_cur, s=2):
    """
    Update average distance after changes to distance matrix

    Parameters
    ----------
    n : int
        Number of rows
    k : int
        Number of columns
    d : np.ndarray
        Current distance vector
    avgdist_old : float
        Old average distance value
    avgdist_cur : float
        Current average distance value
    s : int, optional
        Exponent in MaxPro criterion

    Returns
    -------
    float
        Updated average distance
    """
    # Store old value
    avgdist_old_val = avgdist_cur

    # Calculate new avgdist
    dim = int(n * (n - 1) / 2)

    # Find minimum distance
    d_min = np.min(d)

    # Compute average distance
    avgdist_val = np.sum(np.exp(d_min - d))

    # Apply log transform
    avgdist_val = np.log(avgdist_val) - d_min

    # Scale by dimensions
    avgdist_val = np.exp((avgdist_val - np.log(dim)) / (k * s))

    return avgdist_val, avgdist_old_val


def update_comb_avgdist(n, k, d, avgdist_old, avgdist_cur, s=2):
    """
    Update combined average distance

    Parameters
    ----------
    n : int
        Number of rows
    k : int
        Number of columns
    d : np.ndarray
        Current distance vector
    avgdist_old : float
        Old average distance value
    avgdist_cur : float
        Current average distance value
    s : int, optional
        Exponent in MaxPro criterion

    Returns
    -------
    float
        Updated combined average distance
    """
    new_avgdist, old_avgdist = update_avgdist(n, k, d, avgdist_old, avgdist_cur, s)
    return new_avgdist


def dist_matrix_qq(lambda_vals, A, n, k, n_nom, s=2):
    """
    Compute distance matrix for MaxPro criterion with mixed variable types

    Parameters
    ----------
    lambda_vals : np.ndarray
        Weights for different types of variables
    A : np.ndarray
        Design matrix with shape (k, n)
    n : int
        Number of rows
    k : int
        Number of columns
    n_nom : int
        Number of nominal variables
    s : int, optional
        Exponent in MaxPro criterion

    Returns
    -------
    np.ndarray
        Vector of pairwise distances
    """
    dim = int(n * (n - 1) / 2)
    d = np.zeros(dim)
    count = 0

    for k1 in range(n - 1):
        for k2 in range(k1 + 1, n):
            # Handle continuous and discrete numeric variables
            for k3 in range(k - n_nom):
                d[count] += s * np.log(
                    np.abs(float(A[k3, k1] - A[k3, k2])) + lambda_vals[k3]
                )

            # Handle nominal variables
            if n_nom > 0:
                for k3 in range(k - n_nom, k):
                    # If values are the same, use lambda weight
                    if A[k3, k1] == A[k3, k2]:
                        d[count] += s * np.log(lambda_vals[k3])
                    else:
                        d[count] += s * np.log(1.0 + lambda_vals[k3])

            count += 1

    return d


def update_dist_matrix_qq(lambda_vals, A, n, k, n_nom, selrow1, selrow2, d, d_old, s=2):
    """
    Update distance matrix for mixed variable types after swapping two rows

    Parameters
    ----------
    lambda_vals : np.ndarray
        Weights for different types of variables
    A : np.ndarray
        Design matrix
    n : int
        Number of rows
    k : int
        Number of columns
    n_nom : int
        Number of nominal variables
    selrow1, selrow2 : int
        Rows that were swapped
    d : np.ndarray
        Current distance vector
    d_old : np.ndarray
        Buffer for storing old distances
    s : int, optional
        Exponent in MaxPro criterion

    Returns
    -------
    None (updates d and d_old in place)
    """
    row1 = min(selrow1, selrow2)
    row2 = max(selrow1, selrow2)

    # Update for rows h < row1 < row2
    if row1 > 0:
        for h in range(row1):
            position1 = int(row1 + 1 - ((h + 1) ** 2) / 2 + (n - 0.5) * (h + 1) - n - 1)
            position2 = int(row2 + 1 - ((h + 1) ** 2) / 2 + (n - 0.5) * (h + 1) - n - 1)

            d_old[position1] = d[position1]
            d_old[position2] = d[position2]

            # Recalculate distances completely
            d[position1] = 0
            d[position2] = 0

            # Handle continuous and discrete numeric variables
            for k3 in range(k - n_nom):
                d[position1] += s * np.log(
                    np.abs(float(A[k3, row1] - A[k3, h])) + lambda_vals[k3]
                )
                d[position2] += s * np.log(
                    np.abs(float(A[k3, row2] - A[k3, h])) + lambda_vals[k3]
                )

            # Handle nominal variables
            if n_nom > 0:
                for k3 in range(k - n_nom, k):
                    if A[k3, row1] == A[k3, h]:
                        d[position1] += s * np.log(lambda_vals[k3])
                    else:
                        d[position1] += s * np.log(1.0 + lambda_vals[k3])

                    if A[k3, row2] == A[k3, h]:
                        d[position2] += s * np.log(lambda_vals[k3])
                    else:
                        d[position2] += s * np.log(1.0 + lambda_vals[k3])

    # Similar updates for other pairs of rows
    # ... code for other pairs ...

    # Update for rows row1 < h < row2
    for h in range(row1 + 1, row2):
        position1 = int(h + 1 - ((row1 + 1) ** 2) / 2 + (n - 0.5) * (row1 + 1) - n - 1)
        position2 = int(row2 + 1 - ((h + 1) ** 2) / 2 + (n - 0.5) * (h + 1) - n - 1)

        d_old[position1] = d[position1]
        d_old[position2] = d[position2]

        # Recalculate distances completely
        d[position1] = 0
        d[position2] = 0

        # Handle continuous and discrete numeric variables
        for k3 in range(k - n_nom):
            d[position1] += s * np.log(
                np.abs(float(A[k3, row1] - A[k3, h])) + lambda_vals[k3]
            )
            d[position2] += s * np.log(
                np.abs(float(A[k3, row2] - A[k3, h])) + lambda_vals[k3]
            )

        # Handle nominal variables
        if n_nom > 0:
            for k3 in range(k - n_nom, k):
                if A[k3, row1] == A[k3, h]:
                    d[position1] += s * np.log(lambda_vals[k3])
                else:
                    d[position1] += s * np.log(1.0 + lambda_vals[k3])

                if A[k3, row2] == A[k3, h]:
                    d[position2] += s * np.log(lambda_vals[k3])
                else:
                    d[position2] += s * np.log(1.0 + lambda_vals[k3])

    # Update for rows row1 < row2 < h
    if row2 < (n - 1):
        for h in range(row2 + 1, n):
            position1 = int(
                h + 1 - ((row1 + 1) ** 2) / 2 + (n - 0.5) * (row1 + 1) - n - 1
            )
            position2 = int(
                h + 1 - ((row2 + 1) ** 2) / 2 + (n - 0.5) * (row2 + 1) - n - 1
            )

            d_old[position1] = d[position1]
            d_old[position2] = d[position2]

            # Recalculate distances completely
            d[position1] = 0
            d[position2] = 0

            # Handle continuous and discrete numeric variables
            for k3 in range(k - n_nom):
                d[position1] += s * np.log(
                    np.abs(float(A[k3, row1] - A[k3, h])) + lambda_vals[k3]
                )
                d[position2] += s * np.log(
                    np.abs(float(A[k3, row2] - A[k3, h])) + lambda_vals[k3]
                )

            # Handle nominal variables
            if n_nom > 0:
                for k3 in range(k - n_nom, k):
                    if A[k3, row1] == A[k3, h]:
                        d[position1] += s * np.log(lambda_vals[k3])
                    else:
                        d[position1] += s * np.log(1.0 + lambda_vals[k3])

                    if A[k3, row2] == A[k3, h]:
                        d[position2] += s * np.log(lambda_vals[k3])
                    else:
                        d[position2] += s * np.log(1.0 + lambda_vals[k3])


def dist_newrow_qq(lambda_vals, A, B, n, k, n_nom, s=2):
    """
    Compute distances between a candidate row and existing design

    Parameters
    ----------
    lambda_vals : np.ndarray
        Weights for different types of variables
    A : np.ndarray
        Existing design matrix with shape (k, n)
    B : np.ndarray
        New candidate row with shape (k,)
    n : int
        Number of rows in existing design
    k : int
        Number of columns
    n_nom : int
        Number of nominal variables
    s : int, optional
        Exponent in MaxPro criterion

    Returns
    -------
    np.ndarray
        Vector of distances from candidate to existing points
    """
    dnewrow = np.zeros(n)

    for k1 in range(n):
        # Handle continuous and discrete numeric variables
        for k3 in range(k - n_nom):
            dnewrow[k1] += s * np.log(
                np.abs(float(A[k3, k1] - B[k3])) + lambda_vals[k3]
            )

        # Handle nominal variables
        if n_nom > 0:
            for k3 in range(k - n_nom, k):
                if A[k3, k1] == B[k3]:
                    dnewrow[k1] += s * np.log(lambda_vals[k3])
                else:
                    dnewrow[k1] += s * np.log(1.0 + lambda_vals[k3])

    return dnewrow


def avgdist_newrow(n, k, dnewrow, s=2):
    """
    Compute average distance measure for a candidate row

    Parameters
    ----------
    n : int
        Number of existing rows
    k : int
        Number of columns
    dnewrow : np.ndarray
        Vector of distances from candidate to existing points
    s : int, optional
        Exponent in MaxPro criterion

    Returns
    -------
    float
        Average distance measure for the candidate row
    """
    # Find minimum distance
    d_min = np.min(dnewrow)

    # Compute average distance
    avgdist_val = np.sum(np.exp(d_min - dnewrow))

    # Apply log transform
    avgdist_val = np.log(avgdist_val) - d_min

    # Scale by dimensions
    avgdist_val = np.exp((avgdist_val - np.log(n)) / (k * s))

    return avgdist_val


def maxpro_qq(
    lambda_vals,
    design,
    n_nom,
    local_opt=1,
    n_starts=1,
    iter_max=400,
    total_iter=1000000,
    temp0=0.1,
    s=2,
):
    """
    Perform MaxPro optimization for mixed variable types

    Parameters
    ----------
    lambda_vals : np.ndarray
        Weights for different types of variables
    design : np.ndarray
        Initial design matrix with shape (n, k)
    n_nom : int
        Number of nominal variables
    local_opt : int, optional
        Whether to use local optimization (1) or simulated annealing (0)
    n_starts : int, optional
        Number of random starts
    iter_max : int, optional
        Maximum number of iterations per start
    total_iter : int, optional
        Total maximum number of iterations
    temp0 : float, optional
        Initial temperature for simulated annealing
    s : int, optional
        Exponent in MaxPro criterion

    Returns
    -------
    tuple
        (optimized design, criterion value, number of iterations)
    """
    # Extract dimensions
    n, k = design.shape
    design_T = design.T.copy()  # Transpose for column-major operations

    # Initialize variables
    dim = int(n * (n - 1) / 2)
    d = np.zeros(dim)
    d_old = np.zeros(dim)

    # Precompute criterion for initial design
    d = dist_matrix_qq(lambda_vals, design_T, n, k, n_nom, s)
    avgdist_cur = avgdist(n, k, d, s)
    critbest = avgdist_cur

    # Best design so far
    xbest = design_T.copy()

    # Total iterations counter
    itotal = 0

    # Number of iterations per search is capped
    n_imax = min(5 * n * (n - 1) * k, iter_max)

    # For each random start
    for isearch in range(n_starts):
        # Start with a copy of the initial design
        x = design_T.copy()
        xtry = design_T.copy()

        # Recalculate criterion
        d = dist_matrix_qq(lambda_vals, xtry, n, k, n_nom, s)
        avgdist_cur = avgdist(n, k, d, s)
        xcrit = avgdist_cur
        crittry = xcrit

        # Initial temperature
        temp = temp0
        ichange = 1

        # Continue while improvements are found
        while ichange == 1:
            ichange = 0

            # Perturbation loop
            ipert = 1
            while ipert < n_imax:
                # Check total iterations limit
                if itotal > total_iter:
                    break
                itotal += 1

                # Select column and two rows to swap
                # Only swap in continuous or discrete numeric columns
                col = np.random.randint(0, k - n_nom)
                tran1 = np.random.randint(0, n)

                # Select another row different from tran1
                while True:
                    tran2 = np.random.randint(0, n)
                    if tran2 != tran1:
                        break

                # Swap values
                xtry[col, tran1], xtry[col, tran2] = xtry[col, tran2], xtry[col, tran1]

                # Update distances and criterion
                update_dist_matrix_qq(
                    lambda_vals, xtry, n, k, n_nom, tran1, tran2, d, d_old, s
                )
                avgdist_old = avgdist_cur
                avgdist_cur = avgdist(n, k, d, s)
                crittry = avgdist_cur

                # If new design is better than the best so far
                if crittry < critbest:
                    ichange = 1
                    xbest = xtry.copy()
                    x[col, tran1], x[col, tran2] = x[col, tran2], x[col, tran1]
                    critbest = crittry
                    ipert = 1
                    xcrit = crittry
                else:
                    ipert += 1

                    # If new design is better than current
                    if crittry < xcrit:
                        x[col, tran1], x[col, tran2] = x[col, tran2], x[col, tran1]
                        ichange = 1
                        xcrit = crittry
                    else:
                        # Simulated annealing step
                        if local_opt == 0:
                            delta1 = crittry - xcrit
                            prob = np.exp(-delta1 / temp)
                            if prob >= np.random.random():
                                x[col, tran1], x[col, tran2] = (
                                    x[col, tran2],
                                    x[col, tran1],
                                )
                                xcrit = crittry
                            else:
                                # Revert to previous state
                                xtry[col, tran1], xtry[col, tran2] = (
                                    xtry[col, tran2],
                                    xtry[col, tran1],
                                )
                                revert_dist_matrix(n, tran1, tran2, d, d_old)
                                avgdist_cur = avgdist_old
                        else:
                            # Local optimization - always revert if not better
                            xtry[col, tran1], xtry[col, tran2] = (
                                xtry[col, tran2],
                                xtry[col, tran1],
                            )
                            revert_dist_matrix(n, tran1, tran2, d, d_old)
                            avgdist_cur = avgdist_old

            # Break after one iteration of local optimization
            if local_opt == 1:
                break

            # Cool the temperature
            temp = temp * 0.95

    # Return the best design (transposed back to original shape)
    return xbest.T, critbest, itotal


def maxpro_augment_core(lambda_vals, existing_design, cand_design, n_new, n_nom=0, s=2):
    """
    Sequentially augment an existing design with new points

    Parameters
    ----------
    lambda_vals : np.ndarray
        Weights for different types of variables
    existing_design : np.ndarray
        Existing design matrix with shape (n_exist, k)
    cand_design : np.ndarray
        Candidate points with shape (n_cand, k)
    n_new : int
        Number of new points to add
    n_nom : int, optional
        Number of nominal variables
    s : int, optional
        Exponent in MaxPro criterion

    Returns
    -------
    tuple
        (augmented design, criterion value, status)
    """
    # Extract dimensions
    n_exist, k = existing_design.shape
    n_cand = cand_design.shape[0]
    n_total = n_exist + n_new

    # Check if enough candidate points
    if n_cand < n_new:
        print(
            "Error: The number of candidate design points is less than the number of new points to add."
        )
        return None, 0, 0

    # Transpose designs for column-major operations
    exist_d = existing_design.T.copy()
    cand_d = cand_design.T.copy()

    # Initialize augmented design
    augmented_design = np.zeros((k, n_total))
    augmented_design[:, :n_exist] = exist_d

    # Buffer for distances
    d_new = np.zeros(n_exist)

    # Current number of points in the design
    n_current = n_exist

    # Flag for successful augmentation
    success_flag = 0

    # For each new point to add
    for niter in range(n_new):
        min_i = 0
        min_avgdist = float("inf")
        vio_rule = 0
        flag = 0

        # Evaluate each candidate point
        for i in range(n_cand):
            vio_rule = 0

            # Check if this candidate violates any constraints
            # For example, if lambda is 0, the value must be distinct
            x_row = cand_d[:, i]

            for j in range(k):
                if lambda_vals[j] == 0:
                    for ccc in range(n_current):
                        if x_row[j] == augmented_design[j, ccc]:
                            vio_rule = 1
                            break

                if vio_rule == 1:
                    break

            if vio_rule == 1:
                continue

            # Calculate distances to existing points
            d_new = dist_newrow_qq(
                lambda_vals,
                augmented_design[:, :n_current],
                x_row,
                n_current,
                k,
                n_nom,
                s,
            )
            avg_dist_nr = avgdist_newrow(n_current, k, d_new, s)

            # Update best candidate if better
            if avg_dist_nr < min_avgdist:
                min_avgdist = avg_dist_nr
                min_i = i
                flag = 1

        # If no valid candidate found, break
        if flag == 0:
            break
        else:
            # Add the best candidate to the design
            augmented_design[:, n_current] = cand_d[:, min_i]
            n_current += 1
            success_flag = 1

    # Calculate final criterion if successful
    final_measure = 0
    if success_flag == 1:
        dim = int(n_total * (n_total - 1) / 2)
        d_all = np.zeros(dim)

        d_all = dist_matrix_qq(lambda_vals, augmented_design, n_total, k, n_nom, s)
        final_measure = avgdist(n_total, k, d_all, s)

    # Return the augmented design (transposed back to original shape)
    return augmented_design.T, final_measure, success_flag


def maxpro_lhd_core(n, p, s=2, temp0=0, n_starts=1, iter_max=400, total_iter=1000000):
    """
    Create a MaxPro Latin Hypercube Design

    Parameters
    ----------
    n : int
        Number of runs
    p : int
        Number of factors
    s : int, optional
        Exponent in MaxPro criterion
    temp0 : float, optional
        Initial temperature for simulated annealing
        If 0, will be calculated automatically
    n_starts : int, optional
        Number of random starts
    iter_max : int, optional
        Maximum number of iterations per start
    total_iter : int, optional
        Total maximum number of iterations

    Returns
    -------
    tuple
        (optimized LHD, criterion value, number of iterations, time)
    """
    # Input validation
    if n < 2:
        raise ValueError("Number of runs (n) must be at least 2")
    if p < 1:
        raise ValueError("Number of factors (p) must be at least 1")

    # Set m (rows per slice) = n for a regular LHD (not sliced)
    m = n
    k = p
    t = 1  # Only one slice

    # Calculate temperature if not provided
    if temp0 == 0:
        temp0 = calculate_initial_temperature(n, k, s)

    # Start timer
    t00 = time.time()

    # Number of iterations per search is capped
    n_imax = min(5 * n * (n - 1) * k, iter_max)

    # Initialize variables
    dim = int(n * (n - 1) / 2)
    d = np.zeros(dim)
    d_old = np.zeros(dim)

    # Initial design (Sliced Latin Hypercube)
    xbest = slhd(m, t, k)

    # Calculate initial criterion
    d = dist_matrix(xbest, n, k, s)
    avgdist_cur = avgdist(n, k, d, s)
    critbest = avgdist_cur

    # Total iterations counter
    itotal = 0

    # For each random start
    for isearch in range(n_starts):
        # Generate new random LHD
        x = slhd(m, t, k)
        xtry = x.copy()

        # Calculate criterion
        d = dist_matrix(xtry, n, k, s)
        avgdist_cur = avgdist(n, k, d, s)
        xcrit = avgdist_cur
        crittry = xcrit

        # Initial temperature
        temp = temp0
        ichange = 1

        # Continue while improvements are found
        while ichange == 1:
            ichange = 0

            # Perturbation loop
            ipert = 1
            while ipert < n_imax:
                # Check total iterations limit
                if itotal > total_iter:
                    break
                itotal += 1

                # Select column and two rows to swap
                ind = np.random.randint(0, k)
                tran1 = np.random.randint(0, m)

                # Select another row different from tran1
                while True:
                    tran2 = np.random.randint(0, m)
                    if tran2 != tran1:
                        break

                # Swap values
                xtry[ind, tran1], xtry[ind, tran2] = xtry[ind, tran2], xtry[ind, tran1]

                # Update distances and criterion
                update_dist_matrix(xtry, n, ind, tran1, tran2, d, d_old, s)
                avgdist_old = avgdist_cur
                avgdist_cur = avgdist(n, k, d, s)
                crittry = avgdist_cur

                # If new design is better than the best so far
                if crittry < critbest:
                    ichange = 1
                    xbest = xtry.copy()
                    x[ind, tran1], x[ind, tran2] = x[ind, tran2], x[ind, tran1]
                    critbest = crittry
                    ipert = 1
                    xcrit = crittry
                else:
                    ipert += 1

                    # If new design is better than current
                    if crittry < xcrit:
                        x[ind, tran1], x[ind, tran2] = x[ind, tran2], x[ind, tran1]
                        ichange = 1
                        xcrit = crittry
                    else:
                        # Simulated annealing step
                        delta1 = crittry - xcrit
                        prob = np.exp(-delta1 / temp)
                        if prob >= np.random.random():
                            x[ind, tran1], x[ind, tran2] = x[ind, tran2], x[ind, tran1]
                            xcrit = crittry
                        else:
                            # Revert to previous state
                            xtry[ind, tran1], xtry[ind, tran2] = (
                                xtry[ind, tran2],
                                xtry[ind, tran1],
                            )
                            revert_dist_matrix(n, tran1, tran2, d, d_old)
                            avgdist_cur = avgdist_old

            # Cool the temperature
            temp = temp * 0.95

    # End timer
    t01 = time.time()
    time_rec = t01 - t00

    # Scale the LHD to [0,1]
    scaled_design = np.zeros((n, k))
    for j in range(k):
        # Use ranks to scale (equivalent to R's rank function)
        ranks = np.argsort(np.argsort(xbest[j, :])) + 1
        scaled_design[:, j] = (ranks - 0.5) / n

    # Calculate final criterion
    measure = prod_criterion_core(scaled_design, s)

    return scaled_design, measure, itotal, time_rec


def calculate_initial_temperature(n, k, s=2):
    """
    Calculate initial temperature for simulated annealing

    Parameters
    ----------
    n : int
        Number of runs
    k : int
        Number of factors
    s : int
        Exponent for MaxPro criterion

    Returns
    -------
    float
        Initial temperature
    """
    # Handle edge cases
    if n <= 1:
        return 1.0  # Default temperature

    # Calculate avgdist1 (always safe)
    avgdist1 = 1 / (n - 1)

    # Calculate avgdist2 with protection against division by zero
    if n == 2:
        # Special case for n=2: use a reasonable approximation
        # When n=2, the original formula becomes undefined
        # Use a heuristic based on the dimension
        avgdist2 = (0.5) ** (1 / k)  # Approximate average distance
    elif n == 3 and k > 1:
        # For n=3, be extra careful with small denominators
        denominator = (n - 1) ** (k - 1) * (n - 2)  # = 2^(k-1) * 1
        if denominator <= 0:
            avgdist2 = avgdist1 * 0.5  # Fallback
        else:
            avgdist2 = (1 / denominator) ** (1 / k)
    else:
        # Standard calculation for n >= 3
        try:
            denominator = (n - 1) ** (k - 1) * (n - 2)
            if denominator <= 0:
                avgdist2 = avgdist1 * 0.5  # Fallback
            else:
                avgdist2 = (1 / denominator) ** (1 / k)
        except (ZeroDivisionError, ValueError):
            avgdist2 = avgdist1 * 0.5  # Fallback

    # Calculate delta and temperature
    delta = avgdist2 - avgdist1

    # Protect against log(0) or negative values
    try:
        if delta != 0:
            temp0 = -delta / np.log(0.99)
        else:
            temp0 = 1.0  # Default temperature
    except (ZeroDivisionError, ValueError):
        temp0 = 1.0  # Default temperature

    # Ensure temperature is positive and reasonable
    if not np.isfinite(temp0) or temp0 <= 0:
        temp0 = 1.0

    # Cap temperature to reasonable bounds
    temp0 = max(0.001, min(temp0, 100.0))

    return temp0


def prod_criterion_core(D, s=2):
    """
    Calculate product space MaxPro criterion

    Parameters
    ----------
    D : np.ndarray
        Design matrix with shape (n, p)
    s : int, optional
        Exponent in MaxPro criterion

    Returns
    -------
    float
        MaxPro criterion value
    """
    n, p = D.shape

    # Calculate log distances for each dimension
    log_dist = s * np.log(pdist(D[:, 0].reshape(-1, 1)))
    for j in range(1, p):
        log_dist += s * np.log(pdist(D[:, j].reshape(-1, 1)))

    # Find minimum distance
    i_min = np.argmin(log_dist)

    # Calculate criterion
    value = -log_dist[i_min] + np.log(np.sum(np.exp(log_dist[i_min] - log_dist)))

    # Scale by dimensions
    n_choose_2 = n * (n - 1) / 2
    return np.exp((value - np.log(n_choose_2)) / (p * s))


def find_indices(new_points: np.ndarray, candidate_set: np.ndarray) -> np.ndarray:
    # Reshape for broadcasting: new_points vs candidate_set
    new_points_expanded = new_points[:, np.newaxis, :]
    candidate_set_expanded = candidate_set[np.newaxis, :, :]

    # Calculate distances for all pairs at once
    distances = np.linalg.norm(new_points_expanded - candidate_set_expanded, axis=2)

    # Find closest match for each new point
    indices = np.argmin(distances, axis=1)

    # Verify they're exact matches
    min_distances = np.min(distances, axis=1)
    exact_matches = min_distances < 1e-10

    final_indices = indices[exact_matches]

    return np.array(final_indices)
