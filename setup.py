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
default_version = "3.0.0"

try:
    version=subprocess.check_output(
        ["git", "describe", "--tags"]).decode('utf-8').strip()
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
        'icons_rc.py']
)

if os.name == 'nt': # Write a batch file on windows to make it easier to launch
    #first see if this is a conda env
    foqus_path = subprocess.check_output(
        ["where", "$PATH:foqus.py"]).decode('utf-8').split("\n")[0].strip()
    if "CONDA_DEFAULT_ENV" in os.environ:
        #we're using conda
        env = os.environ["CONDA_DEFAULT_ENV"]
        conda_path = shutil.which("conda")
    else:
        env = None
    with open("foqus.bat", 'w') as f:
        if env is not None:
            f.write('cmd /c "{} activate {} && python {}'\
                .format(conda_path, env, foqus_path))
        else:
            f.write('"cmd /c python {}"\n'.format(foqus_path))

print("""

==============================================================
**Installed FOQUS {}**

**Optional addtional sotfware**

PSUADE (Required for UQ features):
   https://github.com/LLNL/psuade

Turbine (Windows only, run Aspen, Excel, and gPROMS):
    https://github.com/CCSI-Toolset/turb_sci_gate/releases

ALAMO (ALAMO Surogate models):
    http://archimedes.cheme.cmu.edu/?q=alamo

NLOpt Python (Additional optimization solvers):
    https://nlopt.readthedocs.io/en/latest/NLopt_Installation/

**Batch file/Running FOQUS**

Linux:
    Run the command
    > foqus.py

Windows:
    On Windows, this script makes a batch file to run FOQUS.
    This batch file can be placed in any conveinient location.
==============================================================
""".format(ver.version))
