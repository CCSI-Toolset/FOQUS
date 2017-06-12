#!/usr/bin/env python
import os
import sys
import json
import platform
import argparse
import textwrap
from PySide.QtGui import QApplication

try:
    dmf_home = os.path.dirname(os.path.abspath(__file__))
except:
    dmf_home = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.insert(0, dmf_home)

from dmf_lib.common.common import DMF_HOME
from dmf_lib.common.common import JAVA_HOME
from dmf_lib.common.common import REPO_PROPERTIES_WIN_PATH
from dmf_lib.common.common import REPO_PROPERTIES_UNIX_PATH
from dmf_lib.common.common import WIN_PATH_SEPARATOR
from dmf_lib.common.common import UNIX_PATH_SEPARATOR
from dmf_lib.common.common import PROP_HEADER
from dmf_lib.common.common import PROPERTIES_EXT
from dmf_lib.common.common import SC_DEP_APP
from dmf_lib.common.common import SC_DESC
from dmf_lib.common.common import SC_FILE_DESG
from dmf_lib.common.common import SC_GENERIC_SIM
from dmf_lib.common.common import SC_INPUT
from dmf_lib.common.common import SC_MODEL
from dmf_lib.common.common import SC_TITLE
from dmf_lib.common.common import SC_TYPE
from dmf_lib.common.common import SC_TYPENAME
from dmf_lib.common.common import SHARE_LOGIN_EXT
from dmf_lib.common.common import REQUESTS_TIMEOUT
from dmf_lib.common.common import WINDOWS
from dmf_lib.common.methods import Common
from dmf_lib.dmf_browser import DMFBrowser
from dmf_lib.dialogs.select_repo_dialog import SelectRepoDialog
from urllib2 import urlopen
try:
    from StringIO import StringIO
except:
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='DMF_Browser',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
        -------------------------------------------------
        The DMF simulation ingester is a standalone CLI that
        allows users to upload simulations to the CCSI
        Data Management Framework.
        -------------------------------------------------
        '''))
    parser.add_argument(
        '-V',
        '--verbose',
        action="store_true",
        help="verbose mode")
    parser.add_argument('sinter_conf_path',
                        help="Sinter configuration path")
    args = parser.parse_args()
    read_opt = 'rb'
    sim_bytestream = None
    sc_bytestream = None
    sc_contents = None
    resource_bytestream_list = []
    resource_name_list = []
    with open(args.sinter_conf_path, read_opt) as f:
        sc_contents = f.read()

    if not sc_contents:
        print("Error reading sinter config file.")
        sys.exit(-1)

    scn = os.path.basename(args.sinter_conf_path)
    sc_basepath = os.path.dirname(args.sinter_conf_path)
    sc_bytestream = bytearray(sc_contents)
    sc_json = json.loads(sc_contents.decode('utf-8'))
    if sc_json.get(SC_TYPE) != SC_TYPENAME:
        print ("Sinter config file path is not of type {t}".format(
            t=SC_TYPENAME))
        sys.exit(-2)

    desc = sc_json.get(SC_DESC, None)
    if sc_json.get(SC_MODEL, None):
        sim_name = sc_json[SC_MODEL][SC_FILE_DESG]
        sim_path = os.path.join(sc_basepath, sim_name)
        with open(sim_path, read_opt) as f:
            sim_bytestream = bytearray(f.read())
    else:
        print "No simulation specified in sinter config."
        sys.exit(-3)
    input_files = sc_json.get(SC_INPUT, None)
    if input_files:
        for input_file in input_files:
            input_filename = input_file[SC_FILE_DESG]
            input_filepath = os.path.join(
                sc_basepath, input_filename)
            with open(input_filepath, read_opt) as f:
                resource_bytestream_list.append(bytearray(f.read()))
                resource_name_list.append(input_filename)
    dep_app = sc_json.get(SC_DEP_APP, None)
    sim_title = sc_json.get(SC_TITLE, SC_GENERIC_SIM)
    if not sim_title:
        if sim_name:
            sim_title = os.path.splitext(sim_name)[0]
        else:
            sim_title = SC_GENERIC_SIM
    ver_req_list = []
    ver_req_list.append(dep_app.get("constraint"))
    ver_req_list.append(dep_app.get("name"))
    ver_req_list.append(dep_app.get("version"))
    ver_req = ' '.join(ver_req_list)

    app = QApplication(sys.argv)
    try:
        os.environ[JAVA_HOME]
        if platform.system().startswith(WINDOWS):  # We are on Windows
            os.environ[JAVA_HOME] = Common().getNewJavaHomeForWindowsEnv(
                os.environ[JAVA_HOME])
            print "Using %JAVA_HOME%:", os.environ[JAVA_HOME]
        else:
            print "Using $JAVA_HOME:", os.environ[JAVA_HOME]
        has_java = True
    except:
        has_java = False
        if platform.system().startswith(WINDOWS):  # We are on Windows
            print "%JAVA_HOME% is not set"
        else:
            print "$JAVA_HOME is not set"

    # Set DMF_HOME
    os.environ[DMF_HOME] = dmf_home
    if platform.system().startswith(WINDOWS):  # We are on Windows
        print "Using %DMF_HOME%:", os.environ[DMF_HOME]
    else:
        print "Using $DMF_HOME:", os.environ[DMF_HOME]

    try:
        if platform.system().startswith(WINDOWS):  # We are on Windows
            PROP_LOC = (os.environ[REPO_PROPERTIES_WIN_PATH]
                        + WIN_PATH_SEPARATOR)
        else:
            PROP_LOC = (os.environ[REPO_PROPERTIES_UNIX_PATH]
                        + UNIX_PATH_SEPARATOR)

        config = StringIO()
        # Fake properties header to allow working with configParser
        config.write('[' + PROP_HEADER + ']\n')
        # Get a list of property files for repositories
        repo_properties = [p for p in os.listdir(PROP_LOC)
                           if os.path.isfile(os.path.join(PROP_LOC, p))
                           and p.endswith(PROPERTIES_EXT)]
        repo_name_list = []
        status_list = []

        i = 0
        if len(repo_properties) > 0:
            print "Validating the following properties file(s):"
        while i < len(repo_properties) and has_java:
            is_valid, return_vals = Common().validateAndGetKeyProps(
                os.path.join(PROP_LOC, repo_properties[i]))
            if is_valid:
                try:
                    response = urlopen(
                        return_vals[1] + SHARE_LOGIN_EXT,
                        timeout=REQUESTS_TIMEOUT)
                    status_code = response.getcode()
                    response.getcode()
                except:
                    status_code = 500
                repo_name_list.append(return_vals[0])
                status_list.append(status_code)
                i += 1
            else:
                repo_properties.remove(repo_properties[i])
        n_repos = len(repo_properties)
        repo_properties = [PROP_LOC + e for e in repo_properties]

        while True:
            dialog = SelectRepoDialog()
            result, index, repo_name = dialog.getDialog(
                repo_name_list, status_list, dmf_home, show_dmf_lite=True)
            if not result:
                sys.exit(0)

            if index < len(repo_name_list):
                config = repo_properties[index]
            else:
                config = None
            dmf = DMFBrowser(
                config,
                repo_name,
                use_external_gateway=False,
                verbose=args.verbose,
                app=app)
            dmf.filesystem.uploadSimulationFiles(
                sc_bytestream,
                scn,
                '',
                '',
                sim_bytestream,
                None,
                sim_name,
                resource_bytestream_list,
                resource_name_list,
                version_reqs=ver_req,
                description=desc,
                sim_title=sim_title,
                disable_save_dialog=True)
            break

    except Exception, e:
        print e
