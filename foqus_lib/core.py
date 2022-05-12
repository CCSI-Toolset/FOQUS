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
"""
Joshua Boverhof, Lawrence Berkeley National Labs, 2022
"""
import shutil


class DependencyTracker:
    pass


class ModuleDependencyTracker:
    """tracks imported python modules"""

    python_modules_available = {}
    python_modules_unavailable = {}
    module = None

    @classmethod
    def available(cls):
        return tuple(cls.python_modules_available.values())

    @classmethod
    def unavailable(cls):
        return tuple(cls.python_modules_unavailable.values())

    @classmethod
    def load(cls):
        instance = cls.python_modules_available.get(cls.python_module_name)
        if instance is not None:
            return instance
        instance = cls()
        try:
            exec("import %s" % (instance.python_module_name))
        except ModuleNotFoundError:
            cls.python_modules_unavailable[instance.python_module_name] = instance
            raise
        self._module = eval(instance.python_module_name)
        cls.python_modules_available[instance.python_module_name] = instance
        return instance

    @classmethod
    def load_capture_error(cls):
        instance = None
        try:
            instance = cls.load()
        except ModuleNotFoundError:
            pass
        return instance

    def __init__(self):
        self._module = None

    @property
    def module(self):
        return self._module


class ExecutableDependencyTracker(DependencyTracker):
    """tracks optional executables"""

    executable_name = None

    @classmethod
    def available(cls):
        exe = shutil.which(executable_name)
        return exe is not None

    @classmethod
    def unavailable(cls):
        return tuple(cls.python_modules_unavailable.values())


class PsuadeDependencyTracker(ExecutableDependencyTracker):
    """
    plugin = PsuadeDependencyTracker.load()
    if plugin == None:  print("unavailable")
    elif plugin.nomad is False: print("nomand unavailable")
    """

    executable_name = "psuade"

    @property
    def nomad(self):
        return False


class TensorFlowDependencyTracker(ModuleDependencyTracker):
    python_module_name = "tensorflow"
