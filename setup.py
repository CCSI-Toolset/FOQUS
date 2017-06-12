#!/usr/bin/env python
'''
    setup.py  (foqus GUI setup)

    * This is the normal Python installer script with extra junk to
        build a py2exe distribution and msi installer with wix
    * the normal usage is:
        setup.py install
    * or with no root/admin permission
        setup.py install --user
    * to build py2exe dist use:
        setup.py py2exe
    * to build a py2exe dist and make msi use
        setup.py wix
    * If you are developing FOQUS you don't need to install it.  You
        can just execute foqus.py, but you will need the turbine client
        installed.  I can be installed separately if you do not wish to
        install FOQUS.

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
from distutils.core import setup
from distutils.dir_util import copy_tree
import os
import traceback
import shutil
import subprocess
import sys
from setup.data_files import recursiveFiles, recursiveFileList


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
import foqus_lib.help.writeCCSILicenseHelpFiles
import foqus_lib.help.writeThirdPartyHelpFiles

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
                        'turbine_hydro.Hydro',
                        'turbine_hydro.Hydro.hydro',
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
# py2exe doesn't use the package data argument for setup so
# these files need to be copied by some other means if using
# py2exe, so be careful changing this, as it may require other
# changes further on.
dmf_files = recursiveFileList("dmf_lib/java", [], 'dmf_lib')
pkg_package_data = {
    "foqus_lib.help": ["html/*", "LICENSE/*"],
    "foqus_lib.unit_test": ["data/*"],
    "foqus_lib.framework": ["gams/*"],
    "dmf_lib": dmf_files.extend("mimetype_dict/*")}
#set a list of additional files to be copyied to the dist directory
#when using py2exe.  Need to copy standard plugins since they are not
#imported anywhere in the FOQUS code py2exe will not copy them, also
#documentation and some other things
# (dist dir is where py2exe will put its FOQUS distribution)

#dist_dir = "_".join([pkg_name, pkg_version])
dist_dir = pkg_name

pkg_dist_files = [
    ["foqus_console.bat", os.path.join(dist_dir, 'dist')],
    ["dmf_browser_console.bat",os.path.join(dist_dir,'dist')],
    ["turbine_console.bat", os.path.join(dist_dir, 'dist')],
    ["hydro_master.bat", os.path.join(dist_dir, 'dist')],
    ["turbine_hydro/nssm.exe", os.path.join(dist_dir, 'dist')],
    ["turbine_hydro/SqlCeCmd40.exe", os.path.join(dist_dir, 'dist')],
    ["turbine_hydro/logging.conf", os.path.join(dist_dir, 'dist')],
    ["docs/FOQUS_Install_Manual.pdf", os.path.join(dist_dir, "doc")],
    ["docs/FOQUS_User_Manual.pdf", os.path.join(dist_dir, "doc")],
    ["docs/SimSinter Technical Manual.pdf", os.path.join(dist_dir, "doc")],
    ["docs/SimSinter gPROMS Technical Manual.pdf", os.path.join(dist_dir, "doc")],
    ["docs/iREVEAL_User_Manual.pdf", os.path.join(dist_dir, "doc")],
    ["Copyright_Assertion_Approval.pdf", os.path.join(dist_dir, "doc")],
    ["foqus_lib/gui/ouu/foqusPSUADEClient.py",
        os.path.join(dist_dir, "dist/foqus_lib/gui/ouu")],
    ["foqus_lib/framework/optimizer/OptCMA.py",
        os.path.join(dist_dir, "dist/foqus_lib/framework/optimizer")],
    ["foqus_lib/framework/optimizer/cma.py",
        os.path.join(dist_dir, "dist/foqus_lib/framework/optimizer")],
    ["foqus_lib/framework/optimizer/Sample.py",
        os.path.join(dist_dir, "dist/foqus_lib/framework/optimizer")],
    ["foqus_lib/framework/optimizer/NLopt.py",
        os.path.join(dist_dir, "dist/foqus_lib/framework/optimizer")],
    ["foqus_lib/framework/optimizer/SLSQP.py",
        os.path.join(dist_dir, "dist/foqus_lib/framework/optimizer")],
    ["foqus_lib/framework/optimizer/BFGS.py",
        os.path.join(dist_dir, "dist/foqus_lib/framework/optimizer")],
    ["foqus_lib/framework/surrogate/ALAMO.py",
        os.path.join(dist_dir, "dist/foqus_lib/framework/surrogate")],
    ["foqus_lib/framework/surrogate/foqusALAMOClient.py",
        os.path.join(dist_dir, "dist/foqus_lib/framework/surrogate")],
    ["foqus_lib/framework/surrogate/ACOSSO.py",
        os.path.join(dist_dir, "dist/foqus_lib/framework/surrogate")],
    ["foqus_lib/framework/surrogate/BSS-ANOVA.py",
        os.path.join(dist_dir, "dist/foqus_lib/framework/surrogate")],
    ["foqus_lib/framework/pymodel/pymodel_test.py",
        os.path.join(dist_dir, "dist/foqus_lib/framework/pymodel")],
    ["foqus_lib/framework/pymodel/steam_cycle.py",
        os.path.join(dist_dir, "dist/foqus_lib/framework/pymodel")],
    ["foqus_lib/framework/pymodel/heat_integration.py",
        os.path.join(dist_dir, "dist/foqus_lib/framework/pymodel")],
    ["foqus_lib/framework/surrogate/iREVEAL.py",
        os.path.join(dist_dir, "dist/foqus_lib/framework/surrogate")],
    ["dmf_lib/basic_data/ingest.py",
     os.path.join(dist_dir, "dist/dmf_lib/basic_data")]
    ]
pkg_dist_dirs = [
        ["foqus_lib/unit_test/data",
            os.path.join(dist_dir, "dist/foqus_lib/unit_test/data")],
        ["examples", os.path.join(dist_dir, "examples")],
        ["dmf_lib/mimetype_dict", os.path.join(dist_dir,
            "dist/dmf_lib/mimetype_dict")],
        ["test", os.path.join(dist_dir, "test")],
        ["foqus_lib/framework/surrogate/iREVEAL", os.path.join(dist_dir,
            "dist/foqus_lib/framework/surrogate/iREVEAL")],
        ["foqus_lib/framework/surrogate/acosso", os.path.join(dist_dir,
            "dist/foqus_lib/framework/surrogate/acosso")],
        ["foqus_lib/framework/surrogate/bssanova", os.path.join(dist_dir,
            "dist/foqus_lib/framework/surrogate/bssanova")],
        ["foqus_lib/framework/solventfit", os.path.join(dist_dir,
            "dist/foqus_lib/framework/solventfit")],
        ["dmf_lib/graph/template", os.path.join(dist_dir,
            "dist/dmf_lib/graph/template")],
        ["turbine_hydro/foqus_test_files", os.path.join(dist_dir,
            "foqus_test_files")],
        ["turbine_hydro/Hydro/hydro", os.path.join(dist_dir,
            "dist/hydro")]
    ]

# If use the wix option just switch it to the py2exe option
# and set buildMSI to True
if sys.argv[1] == "wix":
    sys.argv[1] = "py2exe"
    buildMSI = True
elif sys.argv[1] == "wix_only":
    buildMSI = True
else:
    buildMSI = False
# Save the original working directory so can change back later
odir = os.getcwd()
# add the turbine client dir to the module search path
sys.path.append('turbine_client')
sys.path.append('turbine_hydro')
#
if len(sys.argv)>1 and sys.argv[1] == "py2exe":
    if os.name != 'nt':
        print "py2exe and wix are windows only options"
        sys.exit(1)
    usePy2exe = True
    # Import modules so I can find the locations of data files
    # and copy data only need this for the msi installer
    # I guess if you are using the msi may as well expect to be
    # able to have gui components
    try:
        import py2exe
        # need to import some extra packages for py2exe so I can
        # copy some data and stuff missed by py2exe to dist dir
        import numpy
        import scipy
        import matplotlib
        import PySide
        import nlopt
    except Exception as e:
        print "Could not find some required module for building msi"
        print e
        sys.exit(1)
    # if using py2exe do something special to install turbine client
    # py2exe has trouble with zipped eggs so be sure it is not zipped
    # the -Z option says to setuptools that it is not zip safe.
    os.chdir('turbine_client') # to turbine client directory
    process = subprocess.Popen([
        'python',
        'setup.py',
        'easy_install',
        '-Z',
        '-H',
        '-f',
        './',
        './'])
    process.wait()
    if process.returncode:
        #if failed to install turbine client bail out here
        print "Some error installing turbine client"
        print process.returncode
        sys.exit(process.returncode)
    os.chdir(odir) # back to origianl dir
elif len(sys.argv)>1 and sys.argv[1] == "wix_only":
    usePy2exe = False
else: # normal setup (no py2exe stuff)
    usePy2exe = False
    # install turbine, just pass argument form the command line
    os.chdir('turbine_client') # to turbine client directory
    process = subprocess.Popen(['python', 'setup.py'] + sys.argv[1:])
    process.wait()
    if process.returncode:
        #if failed to install turbine client bail out here
        print "Some error installing turbine client"
        print process.returncode
        sys.exit(process.returncode)
    os.chdir(odir) # back to origianl dir
if (len(sys.argv)>1 and sys.argv[1] != "wix_only") or len(sys.argv)<=1:
    # Install some of the dependancies that are pure python
    # things that need complied often don't work so not gonna try
    os.chdir('setup') #
    # I don't know why but installing a new package fails on the first run
    # and succeeds on the second so I run this twice
    for i in [1,2]:
        process = subprocess.Popen([
            'python',
            'setup_dep.py',
            'install'] + sys.argv[2:])
        process.wait()
    if process.returncode:
        #if failed to run dependancy install bail out here
        print "Some error running dependancy install"
        print process.returncode
        sys.exit(process.returncode)
    os.chdir(odir) # back to origianl dir
    #Auto generate some help files
    os.chdir('foqus_lib/help') #set working directory to ./foqus_help
    # Make HTML versions of CCSI license files
    foqus_lib.help.writeCCSILicenseHelpFiles.writeHelpFiles()
    # third party module list and licenses
    foqus_lib.help.writeThirdPartyHelpFiles.writeHelpFiles()
    os.chdir(odir) #set working directory back to install directory
    # The next part sets up a list of data files to be copied by the
    # py2exe setup this is not needed for normal install so will only
    # do this for the p2exe option
if usePy2exe:
    # make copy a of foqus.py to create a separate executable
    # that is a console application
    shutil.copy("foqus.py", "foqus_console.py")
    #Create a set of data files to copy
    df = matplotlib.get_py2exe_datafiles() +\
        recursiveFiles("foqus_lib/help/html") +\
        recursiveFiles("foqus_lib/help/LICENSE") +\
        recursiveFiles("foqus_lib/framework/gams") +\
        recursiveFiles("dmf_lib/gui") +\
        recursiveFiles("dmf_lib/java",
                       excludeDirs=['src', 'bin', 'lib', '.ant']) +\
        recursiveFiles("DLLs")
    #delete old stuff if its there
    try:
        shutil.rmtree(dist_dir)
    except:
        pass
    # fix matplotlib_toolkits module so py2exe sees it
    process = subprocess.Popen(['python', 'setup/fix_mpl_toolkits.py'])
    process.wait()
    #
    #
    setup(
        options = {
            'py2exe': {
                'excludes': ['_gtkagg', '_tkagg'],
                'includes': [
                    "numpy",
                    "scipy",
                    "py4j",
                    "git",
                    "smmap"],
                'packages': [
                    "encodings",
                    "email",
                    "networkx",
                    "nlopt",
                    "logstash_formatter"],
                'dll_excludes': [
                    "MSVCP90.dll",
                    "libmmd.dll",
                    "libifcoremd.dll"],
                'dist_dir': os.path.join(dist_dir, "dist"),
                'skip_archive':1
            }
        },
        data_files       = df,
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
        console          = [
            "foqusClient.py",
            "foqusTest.py",
            "foqus_console.py",
            "DMF_Browser.py",
            "DMF_BasicDataIngest.py",
            "DMF_Sim_Ingester.py",
            "foqus_lib/framework/surrogate/foqusALAMOClient.py",
            "foqus_lib/gui/ouu/foqusPSUADEClient.py",
            "turbine_client/scripts/turbine_job_script",
            "turbine_client/scripts/turbine_application_list",
            "turbine_client/scripts/turbine_simulation_list",
            "turbine_client/scripts/turbine_simulation_update",
            "turbine_client/scripts/turbine_simulation_create",
            "turbine_client/scripts/turbine_simulation_get",
            "turbine_client/scripts/turbine_session_list",
            "turbine_client/scripts/turbine_session_create",
            "turbine_client/scripts/turbine_session_append",
            "turbine_client/scripts/turbine_session_kill",
            "turbine_client/scripts/turbine_session_start",
            "turbine_client/scripts/turbine_session_stop",
            "turbine_client/scripts/turbine_session_status",
            "turbine_client/scripts/turbine_session_stats",
            "turbine_client/scripts/turbine_session_get_results",
            "turbine_client/scripts/turbine_session_delete",
            "turbine_client/scripts/turbine_session_graphs",
            "turbine_client/scripts/turbine_consumer_log",
            "turbine_client/scripts/turbine_consumer_list",
            "turbine_hydro/Hydro/turbine_cluster_script.py",
            "turbine_hydro/Hydro/turbine_lite_script.py"
        ],
        windows=[{
            'script':'foqus.py',
            'icon_resources':[
                (1,"foqus_lib/gui/icons/icons_exe/foqus.ico")]
        }]
    )
    # delete the extra foqus_console.py file we made
    os.remove("foqus_console.py")
    #
    # copy missing pyssql file _mssql.pyd
    import pymssql
    pymssql_dir = os.path.abspath(pymssql.__file__)
    pymssql_dir = os.path.dirname(pymssql_dir)
    try:
        shutil.copy(
            os.path.join(pymssql_dir,"_mssql.pyd"),
            os.path.join(dist_dir, "dist"))
    except:
        pass
    # Also need the image format plug-ins for PySide,
    # because all my icons are SVG, and py2exe doesn't
    # copy it by default
    pyside_dir = os.path.abspath(PySide.__file__)
    pyside_dir = os.path.dirname(pyside_dir)
    pyside_pg_dir = os.path.join(
        pyside_dir,
        "plugins\\imageformats")
    print "Copying image format plug-ins directory for PySide"
    print "  from " + pyside_pg_dir
    print "  to " + os.path.join(dist_dir, "dist") + "\n"
    try:
        shutil.rmtree(os.path.join(dist_dir, "dist", "imageformats"))
    except:
        pass
    shutil.copytree(
        pyside_pg_dir,
        os.path.join(dist_dir, "dist", "imageformats"))
    # copy all scipy and numpy just in case
    numpy_dir = os.path.abspath(numpy.__file__)
    numpy_dir = os.path.dirname(numpy_dir)
    print "Copying numpy directory"
    print "  from " + numpy_dir
    print "  to " + os.path.join(dist_dir, "dist") + "\n"
    shutil.rmtree(os.path.join(dist_dir, "dist", "numpy"))
    shutil.copytree(numpy_dir, os.path.join(dist_dir, "dist", "numpy"))
    # now scipy
    scipy_dir = os.path.abspath(scipy.__file__)
    scipy_dir = os.path.dirname(scipy_dir)
    print "Copying scipy directory"
    print "  from " + scipy_dir
    print "  to " + os.path.join(dist_dir, "dist") + "\n"
    shutil.rmtree(os.path.join(dist_dir, "dist", "scipy"))
    shutil.copytree(scipy_dir, os.path.join(dist_dir, "dist", "scipy"))
    # nlopt too
    nlopt_dir = os.path.abspath(nlopt.__file__)
    nlopt_dir = os.path.dirname(nlopt_dir)
    print "nlopt files, nlopt.py is picked up by py2exe, but"
    print "  need _nlopt.pyd and libnlopt-0.dll also"
    print "  source dir: " + nlopt_dir
    shutil.copyfile(
        os.path.join(nlopt_dir, "_nlopt.pyd"),
        os.path.join(dist_dir, "dist" ,"_nlopt.pyd"))
    shutil.copyfile(
        os.path.join(nlopt_dir, "libnlopt-0.dll"),
        os.path.join(dist_dir, "dist" ,"libnlopt-0.dll"))
    # copy py4j because py2exe seems to be missing some
    try:
        import py4j
    except:
        print "Could not find py4j"
        sys.exit(1)
    py4j_dir = os.path.abspath(py4j.__file__)
    py4j_dir = os.path.dirname(py4j_dir)
    print "Copying py4j directory"
    print "  from " + py4j_dir
    print "  to " + os.path.join(dist_dir, "dist") + "\n"
    shutil.rmtree(os.path.join(dist_dir, "dist", "py4j"))
    shutil.copytree(py4j_dir, os.path.join(dist_dir, "dist", "py4j"))
    # copy gitpython
    try:
        import git
    except:
        print "Could not find gitpython"
        sys.exit(1)
    git_dir = os.path.abspath(git.__file__)
    git_dir = os.path.dirname(git_dir)
    print "Copying git directory"
    print "  from " + git_dir
    print "  to " + os.path.join(dist_dir, "dist") + "\n"
    try:
        shutil.rmtree(os.path.join(dist_dir, "dist", "git"))
    except:
        pass
    shutil.copytree(git_dir, os.path.join(dist_dir, "dist", "git"))
    # copy smmap
    try:
        import smmap
    except:
        print "Could not find smmap"
        sys.exit(1)
    smmap_dir = os.path.abspath(smmap.__file__)
    smmap_dir = os.path.dirname(smmap_dir)
    print "Copying smmap directory"
    print "  from " + smmap_dir
    print "  to " + os.path.join(dist_dir, "dist") + "\n"
    shutil.rmtree(os.path.join(dist_dir, "dist", "smmap"))
    shutil.copytree(smmap_dir, os.path.join(dist_dir, "dist", "smmap"))
    #Copy lib2to3 text files
    import lib2to3
    lib2to3_dir = os.path.dirname(os.path.abspath(lib2to3.__file__))
    print "Copying lib2to3 directory"
    print "  from " + lib2to3_dir
    print "  to " + os.path.join(dist_dir, "dist") + "\n"
    try:
        shutil.rmtree(os.path.join(dist_dir, "dist", "lib2to3"))
    except:
        pass
    shutil.copytree(lib2to3_dir, os.path.join(dist_dir, "dist", "lib2to3"))
    # copy examples, documentation, plugins ...
    os.makedirs( os.path.join(dist_dir, "doc") )
    for f in pkg_dist_files:
        if not os.path.exists(os.path.dirname(f[1])):
            os.makedirs(os.path.dirname(f[1]))
        try:
            shutil.copy(f[0],f[1])
        except:
            print "failed to copy {0}".format(f[0])
    for d in pkg_dist_dirs:
        copy_tree(d[0], d[1])
    # Copy License Information
    shutil.copy(
        ".ccsi_common/CCSI_TE_LICENSE.txt",
        os.path.join(
            dist_dir,
            pkg_name + "_" + str(pkg_version) + "_license.txt"))
    for f in os.listdir("foqus_lib/help/LICENSE"):
        if os.path.isfile(os.path.join("foqus_lib/help/LICENSE", f)):
            shutil.copy(
                os.path.join("foqus_lib/help/LICENSE", f), dist_dir)
    ##
    ##
    #
    # Delete the dist/win32com/gen_py directory
    try:
        shutil.rmtree(os.path.join(dist_dir, "dist", "win23com/gen_py"))
    except:
        pass

elif not buildMSI:
    # no py2exe option, so just do the regular set up
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
        package_data     = pkg_package_data,
        scripts          = [
            'foqus.py',
            'foqusClient.py',
            'foqusTest.py',
            'DMF_Browser.py',
            'DMF_BasicDataIngest.py',
            'DMF_Sim_Ingester.py']
    )
# All the normal setup stuff is done if you used the wix
# option go on and use wix to make msi
if buildMSI:
    # Set env variables for making a WiX installer.
    os.environ['foqus_dist_dir'] = os.path.join(dist_dir)
    os.environ['fver'] = str(ver.version)
    # Write version.wsi for wix installer build
    print os.getcwd()
    with open("versionTemplate.wxi", 'r') as f:
        verfile = f.read()
    #need to remove first to numbers from year
    # MS won't allow major version > 256
    #and using year as major version
    verfile = verfile.replace("{version}", pkg_version[2:])
    with open("version.wxi", 'w') as f:
        f.write(verfile)
    process = subprocess.Popen([
        os.environ['WIX'] + 'bin\heat.exe',
        'dir',
        dist_dir,
        '-gg',
        '-suid',
        '-sfrag',
        '-template',
        'fragment',
        '-scom',
        '-sreg',
        '-var',
        'env.foqus_dist_dir',
        '-dr',
        'INSTALLLOCATION',
        '-cg',
        'FOQUS_files',
        '-out',
        'files.wxs'
    ])
    process.wait()
    if process.returncode: sys.exit(process.returncode)
    process = subprocess.Popen([
        os.environ['WIX'] + 'bin\candle.exe',
        'installer.wxs',
        'files.wxs'
    ])
    process.wait()
    if process.returncode: sys.exit(process.returncode)
    process = subprocess.Popen([
        os.environ['WIX'] + 'bin\light.exe',
        'installer.wixobj',
        'files.wixobj',
        '-o',
        'foqus_installer.msi'
    ])
    process.wait()
    if process.returncode: sys.exit(process.returncode)
