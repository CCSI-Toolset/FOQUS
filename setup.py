#!/usr/bin/env python
""" setup.py
John Eslick, Carnegie Mellon University, 2014
See LICENSE.md for license and copyright details.
"""
from setuptools import setup, find_packages
import sys
import os
import subprocess
import shutil

# default_version is the version if "git describe --tags" falls through
# Addtional package info is set in foqus_lib/version/version.template.
# The version module, just makes it a bit easier for FOQUS to pull package info
default_version = "3.5.0"

try:
    version=subprocess.check_output(
        ["git", "describe", "--tags", "--abbrev=0"]).decode('utf-8').strip()
    version = version.replace("-", ".dev", 1)
    version = version.replace("-", "+", 1)
except:
    version=default_version

# Write the version module
with open("foqus_lib/version/version.template", 'r') as f:
    verfile = f.read()
verfile = verfile.format(VERSION=version)
with open("foqus_lib/version/version.py", 'w') as f:
    f.write(verfile)

#now import version.
import foqus_lib.version.version as ver
print("Setting version as {0}".format(ver.version))

dist = setup(
    name = ver.name,
    version = ver.version,
    license = ver.license,
    description = ver.description,
    author = ver.author,
    author_email = ver.support,
    maintainer = ver.maintainer,
    maintainer_email = ver.maintainer_email,
    url = ver.webpage,
    packages = find_packages(),
    package_data={
        '':['*.template', '*.json', '*.dll', '*.so', '*.svg', '*.png',
            '*.html', '*.gms', '*.gpr', '*.ccs']},
    include_package_data=True,
    scripts = [
        'foqus.py',
        'cloud/aws/foqus_worker.py',
        'cloud/aws/foqus_service.py',
        'icons_rc.py'],
    # Required packages needed in the users env go here (non-versioned strongly preferred).
    # requirements.txt should stay empty (other than the "-e .")
    install_requires=[
        "adodbapi>=2.6.0.7; sys_platform == 'win32'",
        "boto3",
        "cma",
        "matplotlib",
        "mlrose",
        "numpy",
        "pandas",
        "psutil",
        "PyQt5==5.13.*",
        "pywin32; sys_platform == 'win32'",
        "requests",
        "scipy",
        "tqdm",
        "TurbineClient",
        ],
)

def write_bat(bat_file, python_path, conda_path, conda_env, foqus_path, switch):
    with open(bat_file, 'w') as f:
        if conda_env is not None and conda_path is not None:
            f.write('cmd {} ""{}" activate {} && "{}" "{}" %*"'.format(
                switch, conda_path, conda_env, python_path, foqus_path))
        else:
            f.write('cmd {} ""{}" "{}" %*"'.format(
                switch, python_path, foqus_path))

if os.name == 'nt': # Write a batch file on windows to make it easier to launch
    #first see if this is a conda env
    foqus_path = subprocess.check_output(
        ["where", "foqus.py"]).decode('utf-8').split(os.linesep)[0].strip()
    if "CONDA_DEFAULT_ENV" in os.environ: # we're using conda probably
        conda_env = os.environ["CONDA_DEFAULT_ENV"]
        conda_path = shutil.which("conda") # unless conda is not found
    else:
        conda_path = None
        conda_env = None
    python_path = shutil.which("python")
    if conda_path is None:
        print("** conda not found bat file will not activate conda environment")
    if python_path is None:
        print("** python not found, no bat file written")
    else:
        write_bat("foqus.bat", python_path, conda_path, conda_env, foqus_path, "/C")
        write_bat("foqus_debug.bat", python_path, conda_path, conda_env, foqus_path, "/K")

print("""

==============================================================================
**Installed FOQUS {}**

**Optional addtional sotfware**

Optional software is not installed during the FOQUS installation, and is not
strictly required to run FOQUS, however this software is highly recomended.
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
    ALAMO is software to develop algebric surrogate models for complex
    processes. Among other uses, these model can be used in algebraic modeling
    laguages such as GAMS, AMPL, and Pyomo. FOQUS provides an interface to
    ALAMO allowing surragtes to be easily created from complex process models.

NLOpt Python (Additional optimization solvers):
    https://nlopt.readthedocs.io/en/latest/NLopt_Installation/
    FOQUS will make the NLOpt routines available if the NLOpt Python module is
    installed.  NLOpt can be installed through conda using the conda-forge
    channel.

**Batch file/Running FOQUS**

Linux:
    Run the command
    > foqus.py

Windows:
    On Windows, this script makes batch files to run FOQUS.  This batch files
    can be placed in any conveinient location.
        - foqus.bat: run FOQUS and close cmd window when FOQUS exits
        - foqus_debug.bat: run FOQUS and leave cmd window open  
==============================================================================
""".format(ver.version))
