#!/usr/bin/env python
"""
    setup.py

    John Eslick, Carnegie Mellon University, 2014

    This Material was produced under the DOE Carbon Capture Simulation
    Initiative (CCSI), and copyright is held by the software owners:
    ORISE, LANS, LLNS, LBL, PNNL, CMU, WVU, et al. The software owners
    and/or the U.S. Government retain ownership of all rights in the
    CCSI software and the copyright and patents subsisting therein. Any
    distribution or dissemination is governed under the terms and
    conditions of the CCSI Test and Evaluation License, CCSI Master
    Non-Disclosure Agreement, and the CCSI Intellectual Property
    Management Plan. No rights are granted except as expressly recited
    in one of the aforementioned agreements.
"""
from __future__ import print_function
from setuptools import setup, find_packages
import os

# Add build number file to help if BUILD_NUMBER env var is set
# this is mostly for building on Jenkins, but you could set the
# env var on a local setup too.  If build number doesn't exist
# it defaults to 0.
build_name = os.environ.get('BUILD_NUMBER', '0')
# change version.py to include the build_number
with open("foqus_lib/version/version.template", 'r') as f:
    verfile = f.read()
verfile = verfile.replace("{BUILDNUMBER}", build_name)
with open("foqus_lib/version/version.py", 'w') as f:
    f.write(verfile)
#now import version.
import foqus_lib.version.version as ver
print("Setting version as {0}".format(ver.version))

install_requires=[
    'TurbineClient',
    'pyparsing',
    #'py4j',
    'requests',
    #'networkx',
    'adodbapi,
    #'redis',
    #'logstash_formatter',
    'matplotlib',
    'scipy',
    'numpy',
    'cma',
    'pandas'],

#dependency_links=[]
dependency_links=['git+https://github.com/CCSI-Toolset/turb_client@2.0.0-alpha#egg=TurbineClient']

# Set all the package parameters
pkg_name             = "foqus"
pkg_version          = ver.version
pkg_license          = ver.license
pkg_description      = "FOQUS tool for simulation based optimization,"\
                       " uncertainty quantification, and surrogate models"
pkg_author           = ver.author
pkg_author_email     = ver.support
pkg_maintainer       = ver.maintainer
pkg_maintainer_email = ver.maintainer_email
pkg_url              = ver.webpage

setup(
    name = pkg_name,
    version = pkg_version,
    license = pkg_license,
    description = pkg_description,
    author = pkg_author,
    author_email = pkg_author_email,
    maintainer = pkg_maintainer,
    maintainer_email = pkg_maintainer_email,
    url = pkg_url,
    packages = find_packages(),
    include_package_data=True,
    scripts = [
        'foqus.py',
        'icons_rc.py',
        'foqusClient.py'],
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
