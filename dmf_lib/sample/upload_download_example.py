#!/usr/bin/env python
import os
import sys
import codecs
import base64
import getpass
import platform
import argparse
import textwrap
from datetime import datetime

try:
    from py4j.java_gateway import JavaGateway
except:
    print "Error: Py4j not detected. Please install Py4j."
    sys.exit(-1)

dmf_home = os.sep.join(os.getcwd().split(os.sep)[:-2]) + '/'
sys.path.insert(1, dmf_home)

from StringIO import StringIO
from Crypto.Cipher import AES

from dmf_lib.common.methods import Common
from dmf_lib.gateway.gateway import Py4JGateway
from dmf_lib.common.common import BLOCK_LENGTH
from dmf_lib.common.common import BLOCK_SIZE
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
from urllib2 import urlopen


def getCredentials():
    user = raw_input('User: ')
    password = getpass.getpass()
    return (user, password)


def uploadFiles(src_file, confidence, external):

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
                pass
            status_list.append(status_code)
            i += 1
        else:
            repo_properties.remove(repo_properties[i])

    n_repos = len(ori_repo_properties)
    if len(repo_properties) == 0:
        print "Exiting. No valid property files detected."
        sys.exit(-4)

    user = ""
    password = ""
    update_user_password = True

    if n_repos > 0:
        print
        if n_repos > 1:
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

        else:
            index = 0

        repo_properties = [PROP_LOC + p for p in repo_properties]
        selected_config = repo_properties[index]
        # get user and password
        fname = PROP_LOC + '.' + repo_name_list[index].replace(
            " ", "_") + SCRIPT_EXT
        if os.path.isfile(fname):
            f = codecs.open(fname, 'r')
            line = f.readline()
            line_split = line.split('\t')
            user = DecodeAES(cipher, line_split[0])
            password = DecodeAES(cipher, line_split[1])
            f.close()

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

    Py4JGateway(True).startupGateway()
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
            session = conn.getAtomSession()
            print "Connected to repository."
            break
        except Exception, e:
            print "Fail to connect to repository."
            print selected_config
            print e
            retry = raw_input("Do you want to retry: (Y/N): ")
            if retry[0].lower() != 'y':
                print "Exiting."
                Py4JGateway(True).shutdownGateway()
                sys.exit(-3)
            else:
                update_user_password = True

    # Main logic that does the ingest/upload and download functionality
    try:
        data_op = entry_point.getDataOperationsImpl()
        data_folder_map = gateway.jvm.ccsi.dm.data.DataFolderMap
        shared_folder = data_op.getHighLevelFolder(
            session, data_folder_map.SHARED)
        sim_folder = data_op.getTargetFolderInParentFolder(
            session, shared_folder.getPath(),
            data_folder_map.SIMULATIONS,
            True)

        display_name = "Test Simulation"
        mimetype = "some mimetype"
        confidence = "Experimental"
        isMajorVersion = True
        original_name = "Test Simulation"
        description = "This is a test"
        parents = gateway.jvm.java.util.ArrayList()
        external = None
        with open(str(src_file), "rb") as f:
            does_file_exist = data_operator.doesCmisObjectExist(
                session,
                sim_folder.getPath() +
                UNIX_PATH_SEPARATOR +
                display_name)
            print "Does file exist in repo?", does_file_exist
            if not does_file_exist:
                # Initial upload
                status = data_operator.createVersionedDocument(
                    sim_folder,
                    display_name,
                    mimetype,
                    confidence,
                    gateway.jvm.java.io.ByteArrayInputStream(
                        bytearray(f.read())),
                    isMajorVersion,
                    original_name,
                    description,
                    parents,
                    external)
                print "Initial Store Status:", status.isOperationSuccessful()
            else:
                object_path = str(
                    sim_folder.getPath() +
                    UNIX_PATH_SEPARATOR +
                    display_name)
                original_doc = data_operator.cmisObject2Document(
                    session.getObjectByPath(object_path))
                try:
                    checkout_object_id = original_doc.checkOut()
                except:
                    print "Already checked out"
                check_in_comment = "New revision"
                # Upload as new major version
                status = data_operator.uploadNewDocumentVersion(
                    sim_folder,
                    session.getObject(checkout_object_id),
                    display_name,
                    mimetype,
                    confidence,
                    isMajorVersion,
                    check_in_comment,
                    gateway.jvm.java.io.ByteArrayInputStream(
                        bytearray(f.read())),
                    original_name,
                    description,
                    parents,
                    external)
                print "Overwrite Status:", status.isOperationSuccessful()

        # Code to download
        object_path = str(
            sim_folder.getPath()) + UNIX_PATH_SEPARATOR + display_name
        doc = data_operator.cmisObject2Document(
            session.getObjectByPath(object_path))
        inputStream = doc.getContentStream().getStream()
        size = doc.getContentStreamLength()
        track = 0
        fname = "output"
        f = open(fname, 'ab')
        while track < size:
            if inputStream.available() < 0:
                break
            b = data_operator.getDocumentContentsAsByteArray(
                inputStream, BLOCK_LENGTH)
            if fname:
                f.write(b)
                f.flush()
            track += len(b)
        f.close()
        print "Downloaded to file: {f}".format(f=fname)
    except Exception, e:
        if "Unauthorized" in str(e):
            print (
                "User is unauthorized."
                "Do you have ALFRESCO_HOME set correctly?")
        else:
            print "Unrecognized exception:\n\n", e
    finally:
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
    parser.add_argument("src_file", help="source file")
    parser.add_argument(
        "-c",
        "--confidence",
        dest="confidence",
        default='experimental',
        help="confidence of the files (experimental, testing, or production)")

    args = parser.parse_args()
    src_file = args.src_file

    confidence = args.confidence

    if not os.path.exists(src_file):
        print "Error: Path " + src_file + " does not exist, exiting."
        sys.exit(1)

    try:
        uploadFiles(src_file, confidence, None)

    except Exception, e:
        print "Terminating..."
