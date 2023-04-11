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
# SOLVENTFIT CALIBRATION predict function
# ---------------------------------------
def pred(modelfile, xdatfile, yhatfile, disc=True, nsamples="100", transform="1"):
    booldict = {True: "1", False: "0"}
    disc = booldict[disc]

    emul = "1"  # if emul is set to False, then extra arguments are required
    p = subprocess.Popen(
        [
            "Rscript",
            "solvfit_calibpred.R",
            modelfile,
            xdatfile,
            yhatfile,
            disc,
            nsamples,
            transform,
            emul,
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
rdsfile = "solvfit_calibrator.rds"
infile = "example/infile.calibpred"
outfile = "outfile.calibpred"
resfile = pred(rdsfile, infile, outfile, disc=True)
print(resfile)
