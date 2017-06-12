#!/usr/bin/env python
import os
import sys
import codecs
import base64
import getpass
import platform
import argparse
import textwrap

try:
    from py4j.java_gateway import JavaGateway
except:
    print "Error: Py4j not detected. Please install Py4j."
    sys.exit(-1)

dmf_home = os.sep.join(os.getcwd().split(os.sep)[:-2]) + '/'
sys.path.insert(1, dmf_home)

from urllib2 import urlopen
from StringIO import StringIO
from Crypto.Cipher import AES

from dmf_lib.common.methods import Common
from dmf_lib.gateway.gateway import Py4JGateway
from dmf_lib.common.common import BLOCK_SIZE
from dmf_lib.common.common import GATEWAY_ENTRYPOINT_CONNECTION_RETRY
from dmf_lib.common.common import PADDING
from dmf_lib.common.common import DMF_HOME
from dmf_lib.common.common import WINDOWS
from dmf_lib.common.common import WIN_PATH_SEPARATOR
from dmf_lib.common.common import UNIX_PATH_SEPARATOR
from dmf_lib.common.common import REPO_PROPERTIES_WIN_PATH
from dmf_lib.common.common import REPO_PROPERTIES_UNIX_PATH
from dmf_lib.common.common import PROP_HEADER
from dmf_lib.common.common import PROPERTIES_EXT
from dmf_lib.common.common import REQUESTS_TIMEOUT
from dmf_lib.common.common import SCRIPT_EXT


def getCredentials():
    user = raw_input('User: ')
    password = getpass.getpass()
    return (user, password)


def uploadFiles(
        src_folder,
        confidence,
        user='',
        password='',
        external=None,
        use_gateway=True,
        repo_index=None):

    JAVA_HOME = "JAVA_HOME"
    SHARE_LOGIN_EXT = "/share/page/"

    platform_win32 = ''.join(platform.win32_ver())
    secret = ''.join(
        platform.machine() + platform.version() + platform_win32)[:BLOCK_SIZE]
    pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
    cipher = AES.new(secret)
    EncodeAES = lambda c, s: base64.urlsafe_b64encode(c.encrypt(pad(s)))
    DecodeAES = lambda c, e: c.decrypt(
        base64.urlsafe_b64decode(e)).rstrip(PADDING)

    os.environ[DMF_HOME] = dmf_home

    if platform.system().startswith(WINDOWS):
        PROP_LOC = os.environ[REPO_PROPERTIES_WIN_PATH] + WIN_PATH_SEPARATOR
    else:
        PROP_LOC = os.environ[REPO_PROPERTIES_UNIX_PATH] + UNIX_PATH_SEPARATOR

    # Check if JAVA_HOME is defined
    try:
        os.environ[JAVA_HOME]
        if os.environ[JAVA_HOME] == '':
            raise
        else:
            print "Using JAVA_HOME:", os.environ[JAVA_HOME]
    except Exception, e:
        print ("Error getting JAVA_HOME. JAVA_HOME is not set: " +
               os.environ[JAVA_HOME])

    config = StringIO()
    # Fake properties header to allow working with configParser
    config.write('[' + PROP_HEADER + ']\n')
    # Get a list of property files for repositories
    repo_properties = [f for f in os.listdir(PROP_LOC)
                       if os.path.isfile(os.path.join(PROP_LOC, f))
                       and f.endswith(PROPERTIES_EXT)]
    repo_name_list = []
    url_list = []
    status_list = []
    ori_repo_properties = repo_properties[:]
    i = 0
    if len(repo_properties) > 0:
        print "Validating keys for detected property files:"
    while i < len(repo_properties):
        is_valid, return_val = Common().validateAndGetKeyProps(
            PROP_LOC + repo_properties[i])
        if is_valid:
            repo_name_list.append(return_val[0])
            url_list.append(return_val[1])
            try:
                response = urlopen(
                    return_val[1] + SHARE_LOGIN_EXT,
                    timeout=REQUESTS_TIMEOUT)
                status_code = response.getcode()
                response.close()
            except:
                status_code = 500
            status_list.append(status_code)
            i += 1
        else:
            repo_properties.remove(repo_properties[i])

    n_repos = len(ori_repo_properties)
    if len(repo_properties) == 0:
        print "Exiting. No valid property files detected."
        sys.exit(-4)

    update_user_password = False if user and password else True

    if n_repos > 0:
        print
        if n_repos > 1 and use_gateway:
            print ("Multiple property files detected, "
                   "listing valid property files with "
                   "status code of repository.")

            for i in range(len(repo_name_list)):
                print (
                    "[" + str(i+1) + "] " +
                    repo_name_list[i] + " [" +
                    str(status_list[i]) + "]")
            nb = raw_input("Choose a properties file (Q/q to exit): ")

            if nb == 'q' or nb == 'Q':
                print "Exiting."
                sys.exit(0)

            try:
                index = int(nb)-1
                if index not in range(len(repo_name_list)):
                    raise
            except:
                print "Invalid index."
                sys.exit(-1)
        elif use_gateway:
            index = 0
        else:
            index = int(repo_index)

        repo_properties = [PROP_LOC + p for p in repo_properties]
        selected_config = repo_properties[index]
        # get user and password
        fname = PROP_LOC + '.' + repo_name_list[index].replace(
            " ", "_") + SCRIPT_EXT
        if os.path.isfile(fname) and user == '' and password == '':
            f = codecs.open(fname, 'r')
            line = f.readline()
            line_split = line.split('\t')
            user = DecodeAES(cipher, line_split[0])
            password = DecodeAES(cipher, line_split[1])
            f.close()
            if use_gateway:
                respond = raw_input("\nLogin as " + user + "? (Y/N):")
                if respond[0] == 'n' or respond[0] == 'N':
                    user = ""
                    password = ""
                    os.remove(fname)
                else:
                    update_user_password = False
    else:
        if platform.system().startswith(WINDOWS):
            print (
                "Exiting. No properties file specified in %" +
                REPO_PROPERTIES_WIN_PATH + "%.")
        else:
            print (
                "Exiting. No properties file specified in $" +
                REPO_PROPERTIES_UNIX_PATH + ".")

        sys.exit(-2)

    if status_list[index] != 200:
        print "Exiting. Unable to connect to URL: " + url_list[index]
        sys.exit(0)

    if use_gateway:
        Py4JGateway(True).startupGateway()
    else:
        n_retries = GATEWAY_ENTRYPOINT_CONNECTION_RETRY

    gateway = JavaGateway()
    entry_point = gateway.entry_point

    while True:
        if not user or not password or update_user_password:
            user, password = getCredentials()

        try:
            sys.stdout.write("\n")
            conn = entry_point.getConnectionClient(
                selected_config, user, password)
            data_operator = entry_point.getDataOperationsImpl()
            conn.createAtomSession()
            conn.getAtomSession()
            print "Connected to repository."
            if update_user_password and use_gateway:
                saveCredentials = raw_input("Remember credentials (Y/N): ")
                if saveCredentials[0].lower() == 'y':
                    new_user = EncodeAES(cipher, user)
                    new_key = EncodeAES(cipher, password)
                    fname = PROP_LOC + '.' + repo_name_list[index].replace(
                        " ", "_") + SCRIPT_EXT
                    f = codecs.open(fname, 'w', "utf-8-sig")
                    f.write(new_user + '\t' + new_key + '\n')
                    f.close()
            break
        except Exception, e:
            if not use_gateway:
                if n_retries == GATEWAY_ENTRYPOINT_CONNECTION_RETRY:
                    print "Failed to connect to repository. Retrying..."
                if n_retries > 0:
                    n_retries -= 1
                    continue
                else:
                    print ("Terminating after attempting {n} times.".format(
                        n=GATEWAY_ENTRYPOINT_CONNECTION_RETRY))
                    return
            print "Failed to connect to repository."
            retry = raw_input("Do you want to retry: (Y/N): ")
            if retry[0].lower() != 'y':
                print "Exiting."
                Py4JGateway(True).shutdownGateway()
                sys.exit(-3)
            else:
                update_user_password = True

    try:
        # sorbent_fit_folder = data_operator.getHighLevelFolder(
        # session, "Shared/SorbentFit")
        status = data_operator.createSorbentFitMetadata(
            conn, src_folder, confidence, True, external)
        messages = status.getDetailsMessage()
        lines = messages.split('\n')
        print "Upload report:"
        for line in lines:
            print line
        if not status.isOperationSuccessful():
            raise Exception(
                "Failed to upload documents from folder: " + src_folder)

    except Exception, e:
        if "Unauthorized" in str(e):
            print (
                "User is unauthorized."
                "Do you have ALFRESCO_HOME set correctly?")
        else:
            print "Unrecognized exception:\n\n", e
    finally:
        if use_gateway:
            Py4JGateway(True).shutdownGateway()
        try:
            os.remove("alfresco.log")
        except:
            pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog="DMF basic data ingester",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
        -------------------------------------------------
        The DMF basic data ingester is a standalone CLI
        that allows users to ingest data from Sorbent Fit into
        the CCSI Data Management Framework.
        -------------------------------------------------
        '''))
    parser.add_argument("src_folder", help="source files directory")
    parser.add_argument("-u", "--user", dest="user", help=argparse.SUPPRESS)
    parser.add_argument(
        "-pw", "--password", dest="password", help=argparse.SUPPRESS)
    parser.add_argument(
        "-i", "--index", dest="index", help=argparse.SUPPRESS)
    parser.add_argument(
        "-c",
        "--confidence",
        dest="confidence",
        default='experimental',
        help="confidence of the files (experimental, testing, or production)")

    args = parser.parse_args()
    src_folder = args.src_folder

    if not os.path.isdir(src_folder):
        print "Error: Path " + src_folder + " does not exist, exiting."
        sys.exit(1)

    try:
        uploadFiles(
            src_folder,
            args.confidence,
            user=args.user,
            password=args.password,
            repo_index=args.index)

    except Exception:
        print "Terminating..."
