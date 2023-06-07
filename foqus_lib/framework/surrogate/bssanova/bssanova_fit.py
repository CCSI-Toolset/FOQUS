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
import subprocess

# ---------------------------------------
# BSSANOVA fit function
# ---------------------------------------
def fit(
    xdatfile,
    ydatfile,
    modelfile,
    bte="[200,1000,1]",
    categorical="auto",
    nterms="25",
    order="2",
    priorprob="0.5",
):
    p = subprocess.Popen(
        [
            "Rscript",
            "bssanova_fit.R",
            xdatfile,
            ydatfile,
            modelfile,
            bte,
            categorical,
            nterms,
            order,
            priorprob,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = p.communicate()
    #   print stdout
    #   print stderr

    return modelfile


# ---------------------------------------
# Example usage
# ---------------------------------------
rdsfile = fit("xdat.csv", "ydat.csv", "bssanova_fit.rds")
print(rdsfile)
