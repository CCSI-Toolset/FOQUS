#!/usr/bin/env python
""" setup.py
John Eslick, Carnegie Mellon University, 2014
See LICENSE.md for license and copyright details.
"""
from setuptools import setup, find_packages
import sys
import os
import subprocess

# default_version is the version if "git describe --tags" falls through
# Addtional package info is set in foqus_lib/version/version.template.
# The version module, just makes it a bit easier for FOQUS to pull package info
default_version = "3.0.0"

try:
    version=subprocess.check_output(
        ["git", "describe", "--tags"]).decode('utf-8').strip()
except:
    version=default_version

if "ssh" in sys.argv:
    connectType = 'ssh'
    sys.argv.remove("ssh")
elif "https" in sys.argv:
    connectType = 'https'
    sys.argv.remove("https")
else:
    connectType = 'https'

# Write the version module
with open("foqus_lib/version/version.template", 'r') as f:
    verfile = f.read()
verfile = verfile.format(VERSION=version)
with open("foqus_lib/version/version.py", 'w') as f:
    f.write(verfile)

#now import version.
import foqus_lib.version.version as ver
print("Setting version as {0}".format(ver.version))

install_requires=[
    'TurbineClient',
    'PyQt5',
    'sip',   # not sure if I need this
    'matplotlib',
    'scipy',
    'numpy',
    'cma',
    'tqdm',
    'pandas>0.20'],

if os.name == 'nt':
    install_requires.append("adodbapi>=2.6.0.7")
    install_requires.append("pywin23")

dependency_links=[]
if connectType == 'https':
    dependency_links=['git+https://git@github.com/CCSI-Toolset/turb_client.git#egg=TurbineClient']
elif connectType == 'ssh':
    dependency_links=['git+ssh://git@github.com/CCSI-Toolset/turb_client.git#egg=TurbineClient']

setup(
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
    install_requires=install_requires,
    dependency_links=dependency_links
)

print("\n\n\n")
print("==============================================================")
print("The following packages can be installed by the user")
print("==============================================================")
print("PSUADE (Required for UQ features): ")
print("    https://github.com/LLNL/psuade\n")
print("Turbine (Windows only, run Aspen, Excel, and gPROMS): ")
print("    (url tbd)\n")
print("ALAMO (ALAMO Surogate models): ")
print("    (url tbd)\n")
print("NLOpt Python (Additional optimization solvers):")
print("    https://nlopt.readthedocs.io/en/latest/NLopt_Installation/\n")
print("==============================================================")
print("\n")
