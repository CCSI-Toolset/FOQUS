"""
 Test script for DMF libraries (Beta)
"""
import ctypes
import time
import sys
import os
import threading
import argparse
import textwrap
from PySide.QtGui import *
from PySide.QtCore import *
from py4j.java_gateway import *

try:
    # This is for running from within the DMF Browser
    from dmf_lib.test.key_map import *
    from autopy import mouse, key
except: pass # Not important for now

__author__ = 'You-Wei Cheah <ycheah@lbl.gov>'
__date__ = '4/7/15'

n_create_new_folder_tests = 2
n_create_new_file_tests = 2
n_line_width = 40

class Test():
    def __init__(self, user=None, password=None, config=None, parent=None):
        # Test initialization
        self.root = parent
        if self.root:
            self.screen_width = self.root.test_screen_width
            self.screen_height = self.root.test_screen_height
        else:
            self.user = user
            self.password = password
            self.config = config

        os.environ[DMF_HOME] = parentdir
        self.test_file_path = os.environ[DMF_HOME] \
            + UNIX_PATH_SEPARATOR + "dmf_lib" \
            + UNIX_PATH_SEPARATOR + "test" \
            + UNIX_PATH_SEPARATOR + "test_files" \
            + UNIX_PATH_SEPARATOR + "lipsum.txt"

        self.test_SorbentfitFiles = os.environ[DMF_HOME] \
            + UNIX_PATH_SEPARATOR + "dmf_lib" \
            + UNIX_PATH_SEPARATOR + "test" \
            + UNIX_PATH_SEPARATOR + "test_files" \
            + UNIX_PATH_SEPARATOR + "Data"

    def runTests(self):
        print '-'*n_line_width
        print "Running tests..."
        print '-'*n_line_width
        results = []
        results.append(self.testJAVAHOME())
        results.append(self.testDMFHOME())

        start_gateway = self.testStartGateway()
        assert(start_gateway)
        results.append(start_gateway)

        results.append(self.testJavaGatewayEntryPoint())
        results.append(self.testGetConnectionClient())
        results.append(self.testGetSharedFolder())
        for i in range(n_create_new_folder_tests):
            results.append(self.testCreateNewFolder(option=i))

        results.append(self.testIfFileExists(self.test_file_path))
        for i in range(n_create_new_file_tests):
            results.append(self.testCreateNewFile(self.test_file_path, option=i))
        results.append(self.testStopGateway())

        results.append(self.testCreateSorbentFitFiles(self.test_SorbentfitFiles))

        n_tests = len(results)
        print '-'*n_line_width
        print "%d/%d tests passed." % (sum(results), n_tests)
        print '-'*n_line_width

    def testJAVAHOME(self):
        sys.stdout.write("Testing if JAVA HOME is set.\t")
        try:
            os.environ[JAVA_HOME]
            sys.stdout.write("OK\n")
            return True
        except Exception, e:
            sys.stdout.write("ERROR\n")
            print e
            return False

    def testDMFHOME(self):
        sys.stdout.write("Testing if DMF HOME is set.\t")
        try:
            os.environ[DMF_HOME]
            sys.stdout.write("OK\n")
            return True
        except Exception, e:
            sys.stdout.write("ERROR\n")
            print e
            return False

    def testStartGateway(self):
        sys.stdout.write("Testing start Py4J Gateway.\t")
        try:
            err = Py4JGateway(True).startupGateway()
            if err == 0:
                sys.stdout.write("OK\n")
                return True
            else:
                sys.stdout.write("ERROR\n")
                return False
        except Exception, e:
            sys.stdout.write("ERROR\n")
            print e
            return False

    def testStopGateway(self):
        sys.stdout.write("Testing shutdown Py4J Gateway.\t")
        try:
            res = Py4JGateway().shutdownGateway()
            if res != 0:
                sys.stdout.write("OK\n")
                return True
            else:
                sys.stdout.write("ERROR\n")
                return False
        except Exception, e:
            sys.stdout.write("ERROR\n")
            print e
            return False

    def testJavaGatewayEntryPoint(self):
        sys.stdout.write("Testing gateway entry point.\t")
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
                sys.stdout.write("OK\n")
                return True
            except Exception, e:
                time.sleep(RETRY_SLEEP_DURATION)
                if i == GATEWAY_ENTRYPOINT_CONNECTION_RETRY - 1:
                    self.entry_point = None
                    sys.stdout.write("ERROR\n")
                    print e
                    return False
                else:
                    i += 1

    def testGetConnectionClient(self):
        sys.stdout.write("Testing connection client.\t")
        try:
            self.conn = self.entry_point.getConnectionClient(
                self.config, self.user, self.password)
            self.conn.createAtomSession()
            self.session = self.conn.getAtomSession()
            self.connURL = self.conn.getAlfrescoURL().toString()
            self.username = self.conn.getUser()
            self.password = self.conn.getPassword()
            sys.stdout.write("OK\n")
            return True
        except Exception, e:
            sys.stdout.write("ERROR\n")
            print e
            return False

    def testGetSharedFolder(self):
        sys.stdout.write("Testing getting shared folder.\t")
        try:
            self.data_operator = self.entry_point.getDataOperationsImpl()
            self.shared_folder = self.data_operator.getHighLevelFolder(
                self.session, self.data_folder_map.SHARED)
            sys.stdout.write("OK\n")
            return True
        except Exception, e:
            sys.stdout.write("ERROR\n")
            print e
            return False

    def testCreateNewFolder(self, option=None):
        sys.stdout.write("Testing create new folder.\n")
        if option is 0:
            sys.stdout.write("\tNot fixed form folder.\t")
            folder_name = "Folder" + str(option)
            description = "1 of 2 tests to test create new folder."
            fixed_form = False
        elif option is 1:
            sys.stdout.write("\tFixed form folder.\t")
            folder_name = "Folder" + str(option)
            description = "2 of 2 tests to test create new folder."
            fixed_form = True
        else:
            sys.stdout.write("ERROR\n")
            print "Unrecognized option."
            return False

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
                sys.stdout.write("ERROR\n")
                print "Fetched name (%s) is different from original (%s)" \
                    % (fetched_name, folder_name)
                return False

            if fetched_desc != description:
                sys.stdout.write("ERROR\n")
                print "Fetched description (%s) is different from original (%s)" \
                    % (fetched_desc, description)
                return False

            if fetched_fixed_form != fixed_form:
                sys.stdout.write("ERROR\n")
                print "Fetched fixed form (%s) is different from original (%s)" \
                    % (fetched_fixed_form, fixed_form)
                return False
            sys.stdout.write("OK\n")
            return True
        else:
            sys.stdout.write("ERROR\n")
            try:
                cmis_object.delete()
            finally:
                print create_folder_status.getStatusMessage()
                return False

    def testIfFileExists(self, file_path):
        sys.stdout.write("Testing if test file exists.\t")
        try:
            display_name = os.path.basename(file_path)
            does_file_exist = self.data_operator.doesCmisObjectExist(
                self.session,
                self.shared_folder.getPath() + UNIX_PATH_SEPARATOR + display_name)
            sys.stdout.write("OK\n")
            return True
        except Exception, e:
            sys.stdout.write("ERROR\n")
            print e
            return False

    def testCreateNewFile(self, file_path, option=None):
        sys.stdout.write("Testing creating new file.\n")
        try:
            display_name = os.path.basename(file_path)
            original_name = file_path
            if option is 0:
                sys.stdout.write("\tMajor version file.\t")
                isMajorVersion = True
                description = "Testing creation of new file with major version."
                external = "www.lbl.gov"
                parents = None
                mimetype = None
                confidence = "Experimental"
            elif option is 1:
                sys.stdout.write("\tMinor version file.\t")
                isMajorVersion = False
                description = "Testing creation of new file with minor version."
                external = "www.lbl.gov"
                parents = None
                mimetype = None
                confidence = "Experimental"

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
                    sys.stdout.write("ERROR\n")
                    print "Fetched display name (%s) is different from original (%s)" \
                        % (fetched_name, display_name)
                    return False
                elif fetched_desc != description:
                    sys.stdout.write("ERROR\n")
                    print "Fetched description (%s) is different from original (%s)" \
                        % (fetched_desc, description)
                    return False
                elif fetched_mimetype != mimetype:
                    sys.stdout.write("ERROR\n")
                    print "Fetched mimetype (%s) is different from original (%s)" \
                        % (fetched_mimetype, mimetype)
                    return False
                elif fetched_confidence != confidence:
                    sys.stdout.write("ERROR\n")
                    print "Fetched confidence (%s) is different from original (%s)" \
                        % (fetched_confidence, confidence)
                    return False
                elif fetched_checksum is None:
                    sys.stdout.write("ERROR\n")
                    print "Fetched checksum (%s) is:" % fetched_checksum
                    return False
                else:
                    sys.stdout.write("OK\n")
                    return True
            else:
                sys.stdout.write("ERROR\n")
                try:
                    cmis_object.delete()
                finally:
                    print self.status.getStatusMessage()
                    return False
        except Exception, e:
            sys.stdout.write("ERROR\n")
            try:
                cmis_object.delete()
            finally:
                print e
                return False

    def testCreateSorbentFitFiles(self, test_SorbentfitFiles, option=None):
        sys.stdout.write("Testing creating SorbentFit files.\n")
        try:
            if option is None:
                sys.stdout.write("\tMajor version file.\n")
                isMajorVersion = True
                description = "Testing creation SorbentFit files with major version."
                external = "www.lbl.gov"
                parents = None
                mimetype = None
                confidence = "Experimental"
            elif option is 1:
                sys.stdout.write("\tMinor version file.\t")
                isMajorVersion = False
                description = "Testing creation SorbentFit files with minor version."
                external = "www.lbl.gov"
                parents = None
                mimetype = None
                confidence = "Experimental"
   
            
            if not os.path.isdir(test_SorbentfitFiles):
               sys.stdout.write("source folder: " + test_SorbentfitFiles + " doesn't exist.\n")
               return False

            self.status = self.data_operator.createSorbentFitMetadata(self.conn, test_SorbentfitFiles, confidence, isMajorVersion, external)
            Messages = self.status.getDetailsMessage()
            lines = Messages.split("\n")
            print "\n"
            for line in lines:
                print line

            if self.status.isOperationSuccessful():
                cmis_object = self.session.getObject(self.status.getDataObjectID())
                cmis_object.delete()
                sys.stdout.write("Success create SorbentFit files from folder: " + test_SorbentfitFiles + "\n")
                return True
            else:
                sys.stdout.write("ERROR\n")
                try:
                    cmis_object.delete()
                finally:
                    print self.status.getStatusMessage()
                    return False
        except Exception, e:
            sys.stdout.write("ERROR\n")
            try:
                cmis_object.delete()
            finally:
                print e
                return False

    # ------------------------------------------------------------------------ #
    # GUI tests                                                                #
    # ------------------------------------------------------------------------ #
    def runGUITests(self):
        if self.root:
            s_w_m = self.screen_width / 2
            s_h_m = self.screen_height / 2

        self.thread = InputEventThread()
        self.t = threading.Thread(
            target=self.thread.run, args=(self.screen_width, self.screen_height))
        self.thread.finished.connect(self.onFinish)
        self.t.start()
        self.t.join(1)

    def onFinish(self):
        print "Thread is done"
        self.cleanUp()

    def cleanUp(self):
        self.thread.deleteLater()
        self.t.deleteLater()
        del self.thread
        del self.t
        self.thread = None
        self.t = None
        self.wait = False

class InputEventThread(QThread):
    finished = Signal(bool)

    def __init__(self, parent = None):
        super(InputEventThread, self).__init__(parent)
        print "Input event thread activated"
        self.root = parent
        self._stop = False
        self._finished = False
        self.buttonbar_y = 140

    def stop(self):
        self._stop = True

    def isFinished(self):
        return self._finished

    def newFolderDialogTest(self, s_w_m, s_h_m):
        cancel_button = (s_w_m, s_h_m+160)
        ok_button = (s_w_m+100, s_h_m+160)
        new_folder_button = (100, self.buttonbar_y)
        print "Empty Dialog OK test"
        time.sleep(2)
        mouse.smooth_move(new_folder_button[0], new_folder_button[1])
        time.sleep(1)
        mouse.click()
        time.sleep(1)
        mouse.smooth_move(ok_button[0], ok_button[1])
        time.sleep(1)
        print "OK Button clicked"
        mouse.click()
        time.sleep(1)
        print "Reset test: Escape Key Pressed"
        key.tap(KeyMap().ESCAPE) # Escape character

        print "Dialog Cancel test"
        mouse.smooth_move(cancel_button[0], cancel_button[1])
        time.sleep(1)
        mouse.click()

    def downloadTest(self, s_w_m, s_h_m):
        download_button = (400, self.buttonbar_y)
        print "Download test"
        time.sleep(2)
        mouse.smooth_move(download_button[0], download_button[1])
        time.sleep(1)
        mouse.click()
        time.sleep(10)
        print "Reset test: Escape Key Pressed"
        key.tap(KeyMap().ESCAPE) # Escape character

    def lockTest(self):
        lock_button = (470, self.buttonbar_y)
        print "Lock test"
        time.sleep(2)
        mouse.smooth_move(lock_button[0], lock_button[1])
        time.sleep(1)
        print "Locking..."
        mouse.click()
        time.sleep(2)
        print "Unlocking..."
        mouse.click()

    def refreshTest(self, s_w):
        refresh_button = (s_w-50, self.buttonbar_y)
        print "Refresh test"
        time.sleep(2)
        mouse.smooth_move(refresh_button[0], refresh_button[1])
        time.sleep(1)
        mouse.click()
        time.sleep(5)

    def pauseTimer(self, t=None):
        if not t:
            t=2
        time.sleep(t)
        print "Pausing",t,"seconds."

    def run(self, screen_width, screen_height, run_all=True):
        s_w_m = screen_width / 2
        s_h_m = screen_height / 2
        while not self._stop:
            try:
                print "Option:", run_all
                if type(run_all) is bool \
                        or (type(run_all) is int and run_all == 1):
                    self.newFolderDialogTest(s_w_m,s_h_m)
                    self.pauseTimer()
                if type(run_all) is bool \
                        or (type(run_all) is int and run_all == 2):
                    self.downloadTest(s_w_m,s_h_m)
                    self.pauseTimer()
                if type(run_all) is bool \
                        or (type(run_all) is int and run_all == 3):
                    self.lockTest()
                    self.pauseTimer()
                if type(run_all) is bool \
                        or (type(run_all) is int and run_all == 4):
                    self.refreshTest(screen_width)
                    self.pauseTimer()
                self.stop()
            except Exception, e:
                print "Sleeping for 2 seconds...",e
                time.sleep(2)
                self.stop()
        print "Ended"
        self.finished.emit(True)
        self._finished = True

if __name__ == "__main__":
    # This modules for use with running test.py directly
    parentdir = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
    os.sys.path.insert(0, parentdir)
    try:
        from dmf_lib.common.common import *
        from dmf_lib.common.methods import *
        from dmf_lib.gateway.gateway import *
    except Exception, e:
        print e

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
    '''))
    parser.add_argument('username', help="Alfresco login username")
    parser.add_argument('password', help="Alfresco login password")
    parser.add_argument('config', help="Properties file")
    args = parser.parse_args()

    test = Test(user=args.username,
                password=args.password,
                config=args.config,
                parent=None)
    test.runTests()
