#!/usr/bin/env python
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
from setuptools import setup, find_packages
import sys
import os
import subprocess
import shutil

# default_version is the version if "git describe --tags" falls through
# Addtional package info is set in foqus_lib/version/version.template.
# The version module, just makes it a bit easier for FOQUS to pull package info
default_version = "3.17.0.rc1"

try:
    version = (
        subprocess.check_output(
            ## Undo the 'n' here, this is just testing without having to put in a real tag ##
            ["ngit", "describe", "--tags", "--abbrev=0"]
        )
        .decode("utf-8")
        .strip()
    )
    version = version.replace("-", ".dev", 1)
    version = version.replace("-", "+", 1)
except:
    version = default_version

# Write the version module
with open("foqus_lib/version/version.template", "r") as f:
    verfile = f.read()
verfile = verfile.format(VERSION=version)
with open("foqus_lib/version/version.py", "w") as f:
    f.write(verfile)

# now import version.
import foqus_lib.version.version as ver

print("Setting version as {0}".format(ver.version))

dist = setup(
    name=ver.name,
    version=ver.version,
    license=ver.license,
    description=ver.description,
    author=ver.author,
    author_email=ver.support,
    maintainer=ver.maintainer,
    maintainer_email=ver.maintainer_email,
    url=ver.webpage,
    packages=find_packages(),
    py_modules=["pytest_qt_extras"],
    package_data={
        "": [
            "*.template",
            "*.json",
            "*.dll",
            "*.so",
            "*.svg",
            "*.png",
            "*.html",
            "*.gms",
            "*.gpr",
            "*.ccs",
            "*.ico",
            "*.R",
        ]
    },
    include_package_data=True,
    scripts=["cloud/aws/foqus_service.py"],
    entry_points={
        "console_scripts": [
            "foqus = foqus_lib.foqus:main",
            "foqusPSUADEClient = foqus_lib.gui.ouu.foqusPSUADEClient:main",
        ],
    },
    # Required packages needed in the users env go here (non-versioned strongly preferred).
    # requirements.txt should stay empty (other than the "-e .")
    install_requires=[
        "boto3",
        "cma",
        "matplotlib<3.6",
        "mlrose_hiive==2.1.3",
        "mplcursors",
        "numpy",
        "pandas",
        "psutil",
        "PyQt5==5.15.7",
        "pywin32<305; sys_platform == 'win32'",
        "requests",
        "scipy",
        "tqdm",
        "TurbineClient ~= 4.0, >= 4.0.3",
        "winshell; sys_platform == 'win32'",
        "websocket_client>=1.1.0",
    ],
)

print(
    f"""

==============================================================================
**Installed FOQUS {ver.version}**

**Optional additional software**

Optional software is not installed during the FOQUS installation, and is not
strictly required to run FOQUS, however this software is highly recommended.
Some FOQUS features will not be available without these packages.

PSUADE (Required for UQ features):
    https://github.com/LLNL/psuade
    PSUADE is required for FOQUS UQ and OUU features.

SimSinter (Required by Turbine):
    https://github.com/CCSI-Toolset/SimSinter/releases
    This provides a standard API for interacting with process simulation
    software; currently it supports Aspen Plus, Aspen Custom Modeler, Excel,
    and gPROMS. This is required for TurbineLite.

TurbineLite (Windows only, run Aspen, Excel, and gPROMS):
    https://github.com/CCSI-Toolset/turb_sci_gate/releases
    This requires SimSinter to be installed first.  TurbineLite allows local
    execution of Aspen Plus, ACM, Excel, and gPROMS nodes in FOQUS.

ALAMO (ALAMO Surogate models):
    http://archimedes.cheme.cmu.edu/?q=alamo
    ALAMO is software to develop algebraic surrogate models for complex
    processes. Among other uses, these model can be used in algebraic modeling
    languages such as GAMS, AMPL, and Pyomo. FOQUS provides an interface to
    ALAMO allowing surrogates to be easily created from complex process models.

NLOpt Python (Additional optimization solvers):
    https://nlopt.readthedocs.io/en/latest/NLopt_Installation/
    FOQUS will make the NLOpt routines available if the NLOpt Python module is
    installed.  NLOpt can be installed through conda using the conda-forge
    channel.
==============================================================================

To start FOQUS run (within this Anaconda env):
  > foqus

To create a Windows Desktop shortcut for easy start-up of FOQUS,
run once (within this Anaconda env):
  > foqus --make-shortcut
"""
)
