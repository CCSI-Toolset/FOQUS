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
# SOLVENTFIT EMULATOR predict function
# ---------------------------------------
def pred(modelfile, xdatfile, yhatfile, nsamples="50", transform="1"):
    p = subprocess.Popen(
        [
            "Rscript",
            "solvfit_emulpred.R",
            modelfile,
            xdatfile,
            yhatfile,
            nsamples,
            transform,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = p.communicate()
    print(stdout)
    print(stderr)

    return yhatfile


# ---------------------------------------
# Example usage
# ---------------------------------------
rdsfile = "solvfit_emulator.rds"
infile = "example/infile.emulpred"
outfile = "outfile.emulpred"
resfile = pred(rdsfile, infile, outfile)
print(resfile)
