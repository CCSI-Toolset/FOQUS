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
# FOQUS_PYMODEL_PLUGIN
#
from foqus_lib.framework.pymodel.pymodel import *
import time
import subprocess

# Check that the MATLAB engine module is available and import it if possible.
# If not the MATLAB plug-in cannot be used.
try:
    import matlab.engine

    matlab_engine_available = True
except ImportError as e:
    matlab_engine_available = False


def checkAvailable():
    return matlab_engine_available


class pymodel_pg(pymodel):
    def __init__(self):
        pymodel.__init__(self)
        engs = matlab.engine.find_matlab()
        if len(engs) == 0 or "MatlabEngine" not in engs:
            eng = subprocess.Popen(
                "matlab -nosplash -minimize -r \"matlab.engine.shareEngine('MatlabEngine')\""
            )

    def run(self):
        no_matlab_engine = True
        while no_matlab_engine:
            if len(matlab.engine.find_matlab()) > 0:
                no_matlab_engine = False
        time.sleep(0.1)
