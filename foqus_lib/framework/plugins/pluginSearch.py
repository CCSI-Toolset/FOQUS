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
""" pluginSearch.py

* This class looks for plugins and creates a dictionary containing.
  the plugin models.  Plugin objects can be instanciated elsewhere.
  The plugins are identified by a certain string contained in the
  first x charcters of the python file.  Plugins should have a .py
  extension.

John Eslick, Carnegie Mellon University, 2014
"""

import sys
import os
import importlib
import logging
import imp
import re
import traceback

_log = logging.getLogger("foqus." + __name__)


class plugins:
    """
    This class maintains a list of DFO solver plugins
    """

    def __init__(self, idString, pathList, charLimit=1150):
        self.idString = idString
        self.pathList = pathList
        self.charLimit = charLimit
        self.plugins = {}
        self.check_available_error_d = None
        self.importPlugins()

    def importPlugins(self):
        """
        check files in self.pathList to see if they are plugins
        """
        self.check_available_error_d = dict()
        for p in self.pathList:
            if os.path.exists(p):
                sys.path.append(p)
                pgfiles = os.listdir(p)
                for fname in pgfiles:
                    mname = fname.rsplit(".", 1)  # split off extension
                    if len(mname) > 1 and mname[1] == "py":
                        with open(os.path.join(p, fname), "r", encoding="utf-8") as f:
                            is_found = None
                            try:
                                text_to_search_in = f.read(self.charLimit)
                                pattern = self.idString
                                instances_found_in_text = list(
                                    re.findall(pattern, text_to_search_in)
                                )
                                is_found = bool(instances_found_in_text)
                            except:
                                _log.exception("error reading py file")
                                is_found = False
                        if not is_found:
                            continue
                        try:
                            if mname[0] in self.plugins:
                                _log.info(
                                    "Reloading Plugin: {}".format(
                                        os.path.join(p, fname)
                                    )
                                )
                                self.plugins[mname[0]] = imp.reload(
                                    self.plugins[mname[0]]
                                )
                            else:
                                logging.getLogger("foqus." + __name__).info(
                                    "Loading Plugin: " + os.path.join(p, fname)
                                )
                                self.plugins[mname[0]] = importlib.import_module(
                                    mname[0]
                                )
                        except:
                            _log.exception(
                                "Error Loading Plugin: {}".format(
                                    os.path.join(p, fname)
                                )
                            )
        # Now check that the plugins have what they need to be used
        for pkey, p in list(self.plugins.items()):
            _log.debug("check plugin available: %s" % (pkey))
            try:
                av = p.checkAvailable()
            except Exception as ex:
                _log.exception("Exception Plugin checkAvailable")
                self.check_available_error_d[pkey] = traceback.format_exc()
                av = False
            if not av:
                del self.plugins[pkey]
                _log.info("Removing plugin, due to missing dependency: " + pkey)
