""" pluginSearch.py

* This class looks for plugins and creates a dictionary containing.
  the plugin models.  Plugin objects can be instanciated elsewhere.
  The plugins are identified by a certain string contained in the
  first x charcters of the python file.  Plugins should have a .py
  extension.

John Eslick, Carnegie Mellon University, 2014
See LICENSE.md for license and copyright details.
"""

import sys
import os
import importlib
import logging
import imp

_log = logging.getLogger("foqus." + __name__)

class plugins():
    """
    This class maintains a list of DFO solver plugins
    """
    def __init__(self, idString, pathList, charLimit=200):
        self.idString = idString
        self.pathList = pathList
        self.charLimit = charLimit
        self.plugins = {}
        self.importPlugins()

    def importPlugins(self):
        '''
            check files in self.pathList to see if they are plugins
        '''
        for p in self.pathList:
            if os.path.exists(p):
                sys.path.append(p)
                pgfiles = os.listdir(p)
                for fname in pgfiles:
                    mname = fname.rsplit('.', 1) #split off extension
                    if len(mname) > 1 and mname[1] == 'py':
                        with open(os.path.join(p, fname), 'r',
                            encoding="utf-8") as f:
                            try:
                                l = self.idString in f.read(self.charLimit)
                            except:
                                _log.exception("error reading py file")
                                l = False
                        if not l:
                            continue
                        try:
                            if mname[0] in self.plugins:
                                _log.info("Reloading Plugin: {}".format(
                                    os.path.join(p, fname)))
                                self.plugins[mname[0]] = \
                                    imp.reload(self.plugins[mname[0]])
                            else:
                                logging.getLogger("foqus." + __name__).\
                                    info("Loading Plugin: " + \
                                    os.path.join(p, fname))
                                self.plugins[mname[0]] = \
                                    importlib.import_module(mname[0])
                        except:
                            _log.exception("Error Loading Plugin: {}".format(
                                os.path.join(p, fname)))
        # Now check that the plugins have what they need to be used
        for pkey, p in list(self.plugins.items()):
            try:
                av = p.checkAvailable()
            except:
                av = False
            if not av:
                del self.plugins[pkey]
                _log.info("Removing plugin, due to missing dependency: " + pkey)
