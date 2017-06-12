#!/usr/bin/env python
import os
import sys
import platform
import argparse
import textwrap
from PySide.QtGui import QApplication

try:
    dmf_home = os.path.dirname(os.path.abspath(__file__))
except:
    dmf_home = os.path.dirname(os.path.abspath(sys.argv[0]))

from dmf_lib.common.common import BROWSER_MODE
from dmf_lib.common.common import DMF_HOME
from dmf_lib.common.common import JAVA_HOME
from dmf_lib.common.common import REPO_PROPERTIES_WIN_PATH
from dmf_lib.common.common import REPO_PROPERTIES_UNIX_PATH
from dmf_lib.common.common import WIN_PATH_SEPARATOR
from dmf_lib.common.common import UNIX_PATH_SEPARATOR
from dmf_lib.common.common import PROP_HEADER
from dmf_lib.common.common import PROPERTIES_EXT
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
    app = QApplication(sys.argv)
    sys.path.insert(0, dmf_home)

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
        repo_properties = [f for f in os.listdir(PROP_LOC)
                           if os.path.isfile(os.path.join(PROP_LOC, f))
                           and f.endswith(PROPERTIES_EXT)]
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
                    # Implementation using requests (depreciated because
                    # python-requests uses Apache v2 license)
                    # status_code = requests.get(
                    #     return_vals[1] + SHARE_LOGIN_EXT,
                    #     timeout=REQUESTS_TIMEOUT,
                    #     verify=False).status_code
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
            # Only allow browsing
            parser = argparse.ArgumentParser(
                prog='DMF_Browser',
                formatter_class=argparse.RawDescriptionHelpFormatter,
                description=textwrap.dedent('''\
                -------------------------------------------------
                The DMF Browser is a standalone GUI that allows
                users to access the CCSI Data Management Framework.
                -------------------------------------------------
                '''))
            parser.add_argument(
                '-V',
                '--verbose',
                action="store_true",
                help="verbose mode")
            args = parser.parse_args()
            frame = DMFBrowser(
                config,
                repo_name,
                mode=BROWSER_MODE,
                use_external_gateway=False,
                verbose=args.verbose,
                app=app)
            try:
                frame.filesystem
                app.exec_()
            except Exception, e:
                if n_repos == 1:
                    sys.exit(0)

    except Exception, e:
        print e
        pass
