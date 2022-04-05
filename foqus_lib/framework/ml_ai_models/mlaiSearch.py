###############################################################################
# FOQUS Copyright (c) 2012 - 2021, by the software owners: Oak Ridge Institute
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
#
###############################################################################
""" mlaiSearch.py

* This class looks for ml_ai model files and creates a list containing the
  NN model names. The ml_ai models are identified by a certain string contained
  in the file name. Files containing ml_ai models should have a .h5 extension.

John Eslick, Carnegie Mellon University, 2014
"""

import sys
import os
import importlib
import logging
import imp

_log = logging.getLogger("foqus." + __name__)


class ml_ai_models:
    """
    This class maintains a list of NN ml_ai models
    """

    def __init__(self, pathList):
        self.pathList = pathList
        self.ml_ai_models = {}
        self.getMLAIList()

    def getMLAIList(self):
        """
        check files in self.pathList to see if they are ml_ai models
        """
        for p in self.pathList:
            if os.path.exists(p):
                sys.path.append(p)
                pgfiles = os.listdir(p)
                for fname in pgfiles:
                    mname = fname.rsplit(".", 1)  # split off extension
                    if len(mname) > 1 and mname[1] == "h5":
                        try:
                            if mname[0] in self.ml_ai_models:
                                _log.info(
                                    "Reloading ML_AI Model: {}".format(
                                        os.path.join(p, fname)
                                    )
                                )
                                self.ml_ai_models[mname[0]] = mname[0]
                            else:
                                logging.getLogger("foqus." + __name__).info(
                                    "Loading ML_AI Model: " + os.path.join(p, fname)
                                )
                                self.ml_ai_models[mname[0]] = mname[0]
                        except:
                            _log.exception(
                                "Error Loading ML_AI Model: {}".format(
                                    os.path.join(p, fname)
                                )
                            )
