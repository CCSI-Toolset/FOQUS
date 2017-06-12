"""
 Test script for DMF libraries (Beta)
"""
import ctypes
import time
import sys
import os
import argparse
import textwrap
import unittest
from PySide.QtGui import *
from PySide.QtCore import *
from py4j.java_gateway import *

parentdir = os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
os.environ['DMF_HOME'] = parentdir
os.sys.path.insert(0, parentdir)
try:
    from dmf_lib.common.common import *
    from dmf_lib.common.methods import *
    from dmf_lib.gateway.gateway import *
except Exception, e:
    print e

__author__ = 'You-Wei Cheah <ycheah@lbl.gov>'
__date__ = '5/7/15'


class Test(unittest.TestCase):

    def setUp(self):
        self.__user = cmd_line_params.username
        self.__password = cmd_line_params.password
        self.__config = cmd_line_params.config
        self.__verbose = cmd_line_params.verbose
        self.__test_file_path = os.environ[DMF_HOME] \
            + UNIX_PATH_SEPARATOR + "dmf_lib" \
            + UNIX_PATH_SEPARATOR + "test" \
            + UNIX_PATH_SEPARATOR + "test_files" \
            + UNIX_PATH_SEPARATOR + "lipsum.txt"
        self.checkJAVAHOME()
        self.checkDMFHOME()
        self.startGateway()
        self.getJavaGatewayEntryPoint()
        self.getConnectionClient()

    def tearDown(self):
        self.stopGateway()

    def checkJAVAHOME(self):
        if self.__verbose:
            sys.stdout.write("\nChecking if JAVA HOME is set.\t")
        try:
            os.environ[JAVA_HOME]
            if self.__verbose:
                sys.stdout.write("OK\n")
            return True
        except Exception, e:
            if self.__verbose:
                sys.stdout.write("ERROR\n")
            print e
            return False

    def checkDMFHOME(self):
        if self.__verbose:
            sys.stdout.write("Checking if DMF HOME is set.\t")
        try:
            os.environ[DMF_HOME]
            if self.__verbose:
                sys.stdout.write("OK\n")
            return True
        except Exception, e:
            if self.__verbose:
                sys.stdout.write("ERROR\n")
            print e
            return False

    def startGateway(self):
        if self.__verbose:
            sys.stdout.write("Starting up Py4J Gateway.\t")
        try:
            err = Py4JGateway(True).startupGateway()
            if err == 0:
                if self.__verbose:
                    sys.stdout.write("OK\n")
                return True
            else:
                if self.__verbose:
                    sys.stdout.write("ERROR\n")
                return False
        except Exception, e:
            if self.__verbose:
                sys.stdout.write("ERROR\n")
            print e
            return False

    def stopGateway(self):
        if self.__verbose:
            sys.stdout.write("Shutting down Py4J Gateway.\t")
        try:
            res = Py4JGateway().shutdownGateway()
            if res != 0:
                if self.__verbose:
                    sys.stdout.write("OK\n")
                return True
            else:
                if self.__verbose:
                    sys.stdout.write("ERROR\n")
                return False
        except Exception, e:
            if self.__verbose:
                sys.stdout.write("ERROR\n")
                print e
            return False


    def getJavaGatewayEntryPoint(self):
        if self.__verbose:
            sys.stdout.write("Getting gateway entry point.\t")
        i = 0
        while i < GATEWAY_ENTRYPOINT_CONNECTION_RETRY:  # Retry a number of times until gateway is activated
            try:
                self.gateway = JavaGateway()
                self.entry_point = self.gateway.entry_point
                self.data_model_vars = self.gateway.jvm.ccsi.dm.data.DataModelVars
                self.data_folder_map = self.gateway.jvm.ccsi.dm.data.DataFolderMap
                self.property_ids = self.gateway.jvm.org.apache.chemistry.opencmis.commons.PropertyIds
                self.basetype_id = self.gateway.jvm.org.apache.chemistry.opencmis.commons.enums.BaseTypeId
                self.basic_permissions = self.gateway.jvm.org.apache.chemistry.opencmis.commons.BasicPermissions
                self.role = self.gateway.jvm.ccsi.alfresco.accesscontrol.Role
                self.CMIS_FOLDER = str(self.basetype_id.CMIS_FOLDER)
                self.CMIS_DOCUMENT = str(self.basetype_id.CMIS_DOCUMENT)
                if self.__verbose:
                    sys.stdout.write("OK\n")
                return True
            except Exception, e:
                time.sleep(RETRY_SLEEP_DURATION)
                if i == GATEWAY_ENTRYPOINT_CONNECTION_RETRY - 1:
                    self.entry_point = None
                    if self.__verbose:
                        sys.stdout.write("ERROR\n")
                        print e
                    return False
                else:
                    i += 1

    def getConnectionClient(self):
        if self.__verbose:
            sys.stdout.write("Getting connection client.\t")
        try:
            self.conn = self.entry_point.getConnectionClient(
                self.__config, self.__user, self.__password)
            self.conn.createAtomSession()
            self.session = self.conn.getAtomSession()
            self.connURL = self.conn.getAlfrescoURL()
            self.username = self.conn.getUser()
            self.password = self.conn.getPassword()
            if self.__verbose:
                sys.stdout.write("OK\n")
            return True
        except Exception, e:
            if self.__verbose:
                sys.stdout.write("ERROR\n")
                print e
            return False

    def testGetSharedFolder(self):
        if self.__verbose:
            sys.stdout.write("Testing getting shared folder.\n")
        self.data_operator = self.entry_point.getDataOperationsImpl()
        try:
            self.shared_folder = self.data_operator.getHighLevelFolder(
                self.session, self.data_folder_map.SHARED)
            if self.__verbose:
                sys.stdout.write("OK\n")
            result = True
        except Exception, e:
            if self.__verbose:
                print e
            result = False
        self.assertTrue(result)

    def testCreateNotFixedNewFolder(self):
        if self.__verbose:
            sys.stdout.write("Testing create new non-fixed folder.\n")
        self.assertTrue(self.folder_test("Not fixed"))

    def testCreateFixedNewFolder(self, option=None):
        if self.__verbose:
            sys.stdout.write("Testing create new fixed folder.\n")
        self.assertTrue(self.folder_test("Fixed"))

    def folder_test(self, option=None):
        if option == "Not fixed":
            folder_name = "Folder" + str(option)
            description = "1 of 2 tests to test create new folder."
            fixed_form = False
        elif option == "Fixed":
            folder_name = "Folder" + str(option)
            description = "2 of 2 tests to test create new folder."
            fixed_form = True
        else:
            if self.__verbose:
                print "Error: Uncrecognized option."
            return False

        self.data_operator = self.entry_point.getDataOperationsImpl()
        self.shared_folder = self.data_operator.getHighLevelFolder(
            self.session, self.data_folder_map.SHARED)

        create_folder_status = self.data_operator.createFolder(self.shared_folder, folder_name, description, fixed_form)

        if create_folder_status.isOperationSuccessful():
            cmis_object = self.session.getObject(create_folder_status.getDataObjectID())
            fetched_name = cmis_object.getName()
            fetched_desc = self.data_operator.getSinglePropertyAsString(
                cmis_object.getProperty(self.data_model_vars.CM_DESCRIPTION))
            fetched_fixed_form = Common().convertJavaBool2PyBool(
                self.data_operator.getSinglePropertyAsString(cmis_object.getProperty(self.data_model_vars.CCSI_FIXED_FORM)))
            cmis_object.delete()

            if fetched_name != folder_name:
                if self.__verbose:
                    print "Fetched name (%s) is different from original (%s)" \
                        % (fetched_name, folder_name)
                result = False

            if fetched_desc != description:
                if self.__verbose:
                    print "Fetched description (%s) is different from original (%s)" \
                        % (fetched_desc, description)
                result = False

            if fetched_fixed_form != fixed_form:
                if self.__verbose:
                    print "Fetched fixed form (%s) is different from original (%s)" \
                        % (fetched_fixed_form, fixed_form)
                result = False
            result = True
        else:
            try:
                cmis_object.delete()
            finally:
                if self.__verbose:
                    print create_folder_status.getStatusMessage()
                    result = False
        return result

    def testCreateMajorVersionFile(self):
        if self.__verbose:
            sys.stdout.write("Testing create new major version file.\n")
        self.assertTrue(self.file_create_test(self.__test_file_path, "Major"))

    def testCreateMinorVersionFile(self):
        if self.__verbose:
            sys.stdout.write("Testing create new minor version file.\n")
        self.assertTrue(self.file_create_test(self.__test_file_path, "Minor"))

    def file_create_test(self, file_path, option=None):
        if self.__verbose:
            sys.stdout.write("Testing creating new file.\n")
        try:
            display_name = os.path.basename(file_path)
            original_name = file_path
            if option == "Major":
                if self.__verbose:
                    sys.stdout.write("\tMajor version file.\t")
                isMajorVersion = True
                description = "Testing creation of new file with major version."
                external = "www.lbl.gov"
                parents = None
                mimetype = None
                confidence = "Experimental"
            elif option == "Minor":
                if self.__verbose:
                    sys.stdout.write("\tMinor version file.\t")
                isMajorVersion = False
                description = "Testing creation of new file with minor version."
                external = "www.lbl.gov"
                parents = None
                mimetype = None
                confidence = "Experimental"

            self.data_operator = self.entry_point.getDataOperationsImpl()
            self.shared_folder = self.data_operator.getHighLevelFolder(
                self.session, self.data_folder_map.SHARED)

            with open(str(file_path), 'rb') as f:
                self.status = self.data_operator.createVersionedDocument(
                    self.shared_folder,
                    display_name,
                    mimetype,
                    confidence,
                    self.gateway.jvm.java.io.ByteArrayInputStream(bytearray(f.read())),
                    isMajorVersion,
                    original_name,
                    description,
                    parents,
                    external)
            if self.status.isOperationSuccessful():
                cmis_object = self.session.getObject(self.status.getDataObjectID())
                fetched_name = cmis_object.getName()
                fetched_desc = self.data_operator.getSinglePropertyAsString(
                    cmis_object.getProperty(self.data_model_vars.CM_DESCRIPTION))
                fetched_original_name = self.data_operator.getSinglePropertyAsString(
                    cmis_object.getProperty(self.data_model_vars.CM_TITLE))
                fetched_mimetype = self.data_operator.getSinglePropertyAsString(
                    cmis_object.getProperty(self.data_model_vars.CCSI_MIMETYPE))
                fetched_confidence = self.data_operator.getSinglePropertyAsString(
                    cmis_object.getProperty(self.data_model_vars.CCSI_CONFIDENCE))
                fetched_checksum = self.data_operator.getSinglePropertyAsString(
                    cmis_object.getProperty(self.data_model_vars.CCSI_CHECKSUM))

                cmis_object.delete()

                if fetched_name != display_name:
                    if self.__verbose:
                        sys.stdout.write("ERROR\n")
                        print "Fetched display name (%s) is different from original (%s)" \
                            % (fetched_name, display_name)
                    return False
                elif fetched_desc != description:
                    if self.__verbose:
                        sys.stdout.write("ERROR\n")
                        print "Fetched description (%s) is different from original (%s)" \
                            % (fetched_desc, description)
                    return False
                elif fetched_mimetype != mimetype:
                    if self.__verbose:
                        sys.stdout.write("ERROR\n")
                        print "Fetched mimetype (%s) is different from original (%s)" \
                            % (fetched_mimetype, mimetype)
                    return False
                elif fetched_confidence != confidence:
                    if self.__verbose:
                        sys.stdout.write("ERROR\n")
                        print "Fetched confidence (%s) is different from original (%s)" \
                            % (fetched_confidence, confidence)
                    return False
                elif fetched_checksum is None:
                    if self.__verbose:
                        sys.stdout.write("ERROR\n")
                        print "Fetched checksum (%s) is:" % fetched_checksum
                    return False
                else:
                    if self.__verbose:
                        sys.stdout.write("OK\n")
                    return True
            else:
                if self.__verbose:
                    sys.stdout.write("ERROR\n")
                try:
                    cmis_object.delete()
                finally:
                    if self.__verbose:
                        print self.status.getStatusMessage()
                    return False
        except Exception, e:
            if self.__verbose:
                sys.stdout.write("ERROR\n")
            try:
                cmis_object.delete()
            finally:
                if self.__verbose:
                    print e
                return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
    '''))
    parser.add_argument('username', help="Alfresco login username")
    parser.add_argument('password', help="Alfresco login password")
    parser.add_argument('config', help="Properties file")
    parser.add_argument('-v', '--verbose', action="store_true", help="Verbose option")
    args = parser.parse_args()
    cmd_line_params = args
    del sys.argv[1:]
    unittest.main()
