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
"""
Joshua Boverhof, Lawrence Berkeley National Labs, 2024
"""
import os, shutil, logging

# from foqus_lib.framework.session.session import generalSettings as FoqusSettings


class DependencyTracker:
    @classmethod
    def available(cls):
        """Returns set of available packages"""
        raise NotImplementedError()

    @classmethod
    def unavailable(cls):
        """Returns set of unavailable packages"""
        raise NotImplementedError()


class ModuleDependencyTracker:
    """tracks imported python modules"""

    python_modules_available = {}
    python_modules_unavailable = {}
    python_module_name = None

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
        instance._module = eval(instance.python_module_name)
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

    executables_available = dict()
    executables_unavailable = dict()
    executable_name = None
    default_path = None
    required = False

    @classmethod
    def available(cls):
        return cls.executables_available.values()

    @classmethod
    def unavailable(cls):
        return cls.executables_unavailable.values()

    @classmethod
    def path(cls):
        raise NotImplementedError()

    @classmethod
    def load(cls):
        assert cls.executable_name is not None
        instance = cls.executables_available.get(cls.executable_name)
        if instance is not None:
            return instance
        instance = cls()
        if not os.path.isfile(instance.path()):
            raise RuntimeError("%r:  Failed to Load Dependency" % (instance))
        if not os.access(instance.path(), os.X_OK):
            raise RuntimeError(
                "%r:  Dependency Path is not Executable:  %s" % (instance.path())
            )
        cls.executables_available[instance.executable_name] = instance


class PsuadeDependencyTracker(ExecutableDependencyTracker):
    """
    plugin = PsuadeDependencyTracker.load()
    if plugin == None:  print("unavailable")
    elif plugin.nomad is False: print("nomand unavailable")
    """

    required = False
    executable_name = "psuade"
    default_path = "C:/Program Files (x86)/psuade_project 1.7.5/bin/psuade.exe"

    def path(self):
        return shutil.which("psuade") or self.default_path


class RScriptDependencyTracker(ExecutableDependencyTracker):
    required = False
    executable_name = "Rscript.exe"
    default_path = "C:\\Program Files\\R\\R-3.1.2\\bin\\x64\\Rscript.exe"

    @classmethod
    def path(cls):
        return shutil.which(cls.executable_name) or cls.default_path


class WindowsPackageDependencyTracker(DependencyTracker):
    """tracks installed Windows Packages"""

    windows_packages_available = {}
    windows_packages_unavailable = {}
    package_name = None
    install_path = None
    required = False

    @classmethod
    def available(cls):
        return cls.windows_packages_available.values()

    @classmethod
    def unavailable(cls):
        return cls.windows_packages_unavailable.values()

    @classmethod
    def load(cls):
        instance = cls.windows_packages_available.get(cls.package_name)
        instance = instance or cls()
        if not os.path.isdir(instance.path):
            if cls.required:
                raise RuntimeError("Install Path Does Not Exist: %s" % (instance.path))
            if instance.package_name not in cls.windows_packages_unavailable:
                cls.windows_packages_unavailable[instance.package_name] = (
                    cls.windows_packages_unavailable
                )
            logging.getLogger().warning(
                "Install Path Does Not Exist: %s" % (instance.path)
            )
        cls.windows_packages_available[instance.package_name] = instance
        return instance

    @classmethod
    def path(cls):
        raise NotImplementedError()


class SimSinterDependencyTracker(WindowsPackageDependencyTracker):
    """
    plugin = PsuadeDependencyTracker.load()
    if plugin == None:  print("unavailable")
    elif plugin.nomad is False: print("nomand unavailable")
    """

    package_name = "SimSinter"
    install_path = "C:/Program Files/CCSI/SimSinter"

    @property
    def path(self):
        return self.install_path


class TurbineLiteDependencyTracker(WindowsPackageDependencyTracker):
    """
    plugin = PsuadeDependencyTracker.load()
    if plugin == None:  print("unavailable")
    elif plugin.nomad is False: print("nomand unavailable")
    """

    package_name = "TurbineLite"
    install_path = "C:/Program Files/Turbine/Lite"

    @property
    def path(self):
        return self.install_path
