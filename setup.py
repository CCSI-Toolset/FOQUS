#!/usr/bin/env python
'''
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
'''
from setuptools import setup
import os
import sys
import pip

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
print "Setting version as {0}".format(ver.version)

# Set all the package parameters
pkg_name             = "foqus"
pkg_version          = ver.version
pkg_license          = ver.license
pkg_description      = (
    "FOQUS tool for simulation based optimization"
    "and uncertainty quantification")
pkg_author           = ver.author
pkg_author_email     = ver.support
pkg_maintainer       = ver.maintainer
pkg_maintainer_email = ver.maintainer_email
pkg_url              = ver.webpage
pkg_packages         = ['foqus_lib',
                        'foqus_lib.gui',
                        'foqus_lib.gui.main',
                        'foqus_lib.gui.basic_data',
                        'foqus_lib.gui.solventfit',
                        'foqus_lib.gui.optimization',
                        'foqus_lib.gui.flowsheet',
                        'foqus_lib.gui.dialogs',
                        'foqus_lib.gui.help',
                        'foqus_lib.gui.helpers',
                        'foqus_lib.gui.model',
                        'foqus_lib.gui.uq',
                        'foqus_lib.gui.heatIntegration',
                        'foqus_lib.gui.surrogate',
                        'foqus_lib.gui.ouu',
                        'foqus_lib.gui.pysyntax_hl',
                        'foqus_lib.gui.drmbuilder',
                        'foqus_lib.help',
                        'foqus_lib.version',
                        'foqus_lib.unit_test',
                        'foqus_lib.framework',
                        'foqus_lib.framework.graph',
                        'foqus_lib.framework.sim',
                        'foqus_lib.framework.session',
                        'foqus_lib.framework.optimizer',
                        'foqus_lib.framework.listen',
                        'foqus_lib.framework.uq',
                        'foqus_lib.framework.solventfit',
                        'foqus_lib.framework.surrogate',
                        'foqus_lib.framework.plugins',
                        'foqus_lib.framework.foqusException',
                        'foqus_lib.framework.foqusOptions',
                        'foqus_lib.framework.pymodel',
                        'foqus_lib.framework.sampleResults',
                        'foqus_lib.framework.ouu',
                        'foqus_lib.framework.drmbuilder',
                        #'turb_hydro.Hydro',
                        #'turb_hydro.Hydro.hydro',
                        'dmf_lib',
                        'dmf_lib.alfresco',
                        'dmf_lib.alfresco.share',
                        'dmf_lib.alfresco.service',
                        'dmf_lib.basic_data',
                        'dmf_lib.common',
                        'dmf_lib.dialogs',
                        'dmf_lib.filesystem',
                        'dmf_lib.gateway',
                        'dmf_lib.git',
                        'dmf_lib.gui',
                        'dmf_lib.gui.splash',
                        'dmf_lib.graph',
                        'dmf_lib.mimetype_dict']

# install TurbineClient.  having some trouble figuring out how to add to
# requirments when is on private github.
pip.main(['install', 'git+https://github.com/CCSI-Toolset/turb_client'])

setup(
    name             = pkg_name,
    version          = pkg_version,
    license          = pkg_license,
    description      = pkg_description,
    author           = pkg_author,
    author_email     = pkg_author_email,
    maintainer       = pkg_maintainer,
    maintainer_email = pkg_maintainer_email,
    url              = pkg_url,
    packages         = pkg_packages,
    scripts          = [
        'foqus.py',
        'foqusClient.py',
        'DMF_Browser.py',
        'DMF_BasicDataIngest.py',
        'DMF_Sim_Ingester.py'],
    install_requires=[
        'TurbineClient',
        'pyparsing',
        'py4j',
        'requests',
        'networkx',
        'adodbapi > 2.6.0',
        'redis',
        #'pymssql',
        'logstash_formatter',
        'matplotlib',
        'scipy',
        'numpy',
        'cma'],
    dependency_links=[
        'https://git@github.com/CCSI-Toolset/turb_client'
    ]
)
