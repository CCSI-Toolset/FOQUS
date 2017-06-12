#!/usr/bin/env python
'''
    dmf_browser.py

    * The main script to start Data Management Framework components

    You-Wei Cheah, Lawrence Berkeley National Laboratory, 2015

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

import re
import os
import sys
import json
import time
import codecs
import base64
import datetime
import calendar
import platform
import getpass
import subprocess
import logging
import traceback

from PySide.QtGui import (
    QDialog,
    QIcon,
    QVBoxLayout,
    QPixmap,
    QPainter,
    QDesktopWidget
)

from PySide.QtCore import Qt
from dmf_lib.filesystem.alfresco import AlfrescoFileSystem
from dmf_lib.filesystem.local import LocalFileSystem

from dmf_lib.common.common import (
    DMF_HOME,
    JAVA_HOME,
    JAVA_JAR_PATH,
    WINDOWS,
    REQUESTS_TIMEOUT,
    KEYS_EXT,
    TMP_KEYS_EXT,
    SHARE_LOGIN_EXT,
    REPO_PROPERTIES_WIN_PATH,
    REPO_PROPERTIES_UNIX_PATH,
    WIN_PATH_SEPARATOR,
    UNIX_PATH_SEPARATOR,
    PRINT_COLON,
    BROWSER_MODE,
    OPEN_MODE,
    SAVE_MODE,
    BLOCK_SIZE,
    PADDING,
    MAIN_BROWSER_HEIGHT,
    MAIN_BROWSER_WIDTH,
    MAIN_BROWSER_MIN_HEIGHT,
    MAIN_BROWSER_MIN_WIDTH,
    SC_DESC,
    SC_DEP_APP,
    SC_FILE_DESG,
    SC_GENERIC_SIM,
    SC_MODEL,
    SC_TITLE,
    SPLASH_FORMAT_STR,
    UTF8
)

from dmf_lib.common.methods import Common
from dmf_lib.gateway.gateway import Py4JGateway
from dmf_lib.gui.path import (
    SPLASH_PATH,
    CCSI
)

from dmf_lib.dialogs.login import LoginDialog
from dmf_lib.gui.splash.splash_screen import SplashScreen
from dmf_lib.dialogs.status_dialog import StatusDialog
from urllib2 import urlopen

try:
    from Crypto.Cipher import AES
except:
    pass

if platform.system().startswith(WINDOWS):
    try:
        import win32process
    except:
        pass


__author__ = 'You-Wei Cheah <ycheah@lbl.gov>'
__version__ = '2016.06.06'
__min_java_version__ = '1.8.0'


class DMFBrowser(QDialog):
    IS_OPEN_MODE = False
    IS_BROWSER_MODE = False
    USE_EXTERNAL_GATEWAY = False
    EXIT_FLAG = True

    def __init__(
            self,
            config,
            repo,
            mode=None,
            use_external_gateway=True,
            verbose=False,
            app=None,
            user=None,
            key=None):
        QDialog.__init__(self)
        self.verbose = verbose  # For debugging purposes
        self.app = app
        self.has_min_java = False
        self.repo_fname = repo.replace(' ', '_')
        if self.verbose:
            init_start_millis = int(round(time.time() * 1000))
            print "Verbose mode:", self.verbose
        try:
            os.environ[JAVA_HOME]
            if platform.system().startswith(WINDOWS):  # We are on Windows
                PROP_LOC = (os.environ[REPO_PROPERTIES_WIN_PATH] +
                            WIN_PATH_SEPARATOR)
                java_ver_output = subprocess.check_output(
                    ["java", "-version"], stderr=subprocess.STDOUT,
                    creationflags=win32process.CREATE_NO_WINDOW)
            else:
                PROP_LOC = (os.environ[REPO_PROPERTIES_UNIX_PATH] +
                            UNIX_PATH_SEPARATOR)
                java_ver_output = subprocess.check_output(
                    ["java", "-version"], stderr=subprocess.STDOUT)
            self.has_min_java = True
            java_ver = re.findall(r'"(.*?)"', java_ver_output)
            if java_ver:
                java_ver = java_ver[0]
            java_ver_split = java_ver.split('_')
            java_ver_major = java_ver_split[0]
            if java_ver_major < __min_java_version__:
                self.has_min_java = False
                warning_msg = (
                    "JAVA_HOME has version: " + java_ver_major + "\n" +
                    "Minimum Java version is: " + __min_java_version__)
                if config:
                    StatusDialog.displayStatus(warning_msg)
                    self.close()
                    if not use_external_gateway:
                        sys.exit(-1)
                    else:
                        return
                elif mode == BROWSER_MODE:
                    StatusDialog.displayStatus(
                        warning_msg +
                        "\nUpload to DMF Server function will be disabled.")
            else:
                self.has_min_java = True
        except:
            pass

        self.has_dependencies = True
        full_jar_path = os.environ[DMF_HOME] + JAVA_JAR_PATH
        if not os.path.exists(full_jar_path):
            self.has_dependencies = False

        if config and not self.has_dependencies:
            StatusDialog.displayStatus(
                "Please compile Java dependencies "
                "before using DMF components.")
            self.close()
            if not use_external_gateway:
                sys.exit(-1)
            else:
                return

        # Extra check to see if repo is reachable
        if config:
            is_valid, return_vals = Common().validateAndGetKeyProps(
                config, verbose=False)
            try:
                response = urlopen(
                    return_vals[1] + SHARE_LOGIN_EXT,
                    timeout=REQUESTS_TIMEOUT)
                status_code = response.getcode()
                response.close()
            except:
                status_code = 500

            if status_code != 200:
                StatusDialog.displayStatus(
                    "Repo is inaccessible!\n(URL:" + return_vals[1] + ')')
                self.close()
                if not use_external_gateway:
                    sys.exit(-1)
                else:
                    return

            keys = [
                f for f in os.listdir(PROP_LOC)
                if os.path.isfile(os.path.join(PROP_LOC, f)) and
                (f.endswith(self.repo_fname + KEYS_EXT) or
                 f.endswith(self.repo_fname + TMP_KEYS_EXT))]
            fname_no_ext = PROP_LOC + '.' + self.repo_fname
            platform_win32 = ''.join(platform.win32_ver())
            secret = ''.join(
                platform.machine()
                + platform.version()
                + platform_win32)[:BLOCK_SIZE]
            pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
            cipher = AES.new(secret)
            self.EncodeAES = lambda c, s: base64.urlsafe_b64encode(
                c.encrypt(pad(s)))
            self.DecodeAES = lambda c, e: c.decrypt(
                base64.urlsafe_b64decode(e)).rstrip(PADDING)

            if self.verbose:
                print "Secret:", secret
        while True:
            if user and key:
                self.user = user
                self.password = key
                continue
            elif not config:
                self.user = getpass.getuser()
                self.password = None
            elif len(keys) == 0:
                self.user, self.password = self.login(fname_no_ext, cipher)
            else:
                fname = PROP_LOC + keys[0]
                ctime = os.path.getctime(fname)
                created_datetime = datetime.datetime.strptime(
                    time.ctime(), "%a %b %d %H:%M:%S %Y")
                expiration = time.mktime(
                    self.addOneMonth(created_datetime).timetuple())
                if self.verbose:
                    print self.__class__.__name__, \
                        PRINT_COLON, expiration - ctime
                if expiration - ctime > 0:
                    f = open(fname, 'r')
                    line = f.readline()
                    line_split = line.split('\t')
                    self.user = self.DecodeAES(cipher, line_split[0])
                    self.password = self.DecodeAES(cipher, line_split[1])
                    f.close()
                else:
                    try:
                        os.remove(fname)
                        StatusDialog.displayStatus(
                            "Saved credentials have expired, please reenter.")
                        if self.verbose:
                            print self.__class__.__name__, \
                                PRINT_COLON, "Removed saved credentials."
                    except OSError, e:
                        if self.verbose:
                            print e
                    self.user, self.password = self.login(fname_no_ext, cipher)

            if mode == OPEN_MODE:
                self.IS_OPEN_MODE = True
                if self.verbose:
                    print "Using Open mode."
            elif mode == BROWSER_MODE:
                self.IS_BROWSER_MODE = True
                if self.verbose:
                    print "Using Browser mode."
            else:
                self.IS_OPEN_MODE = False
                self.IS_BROWSER_MODE = False

            self.USE_EXTERNAL_GATEWAY = True if use_external_gateway else False
            self.EXIT_FLAG = False if self.USE_EXTERNAL_GATEWAY else True

            self.WINDOW_TITLE = repo
            if self.user == '' and self.password == '':
                self.EXIT_FLAG = False if self.USE_EXTERNAL_GATEWAY else True
                self.close()
                return

            if mode == BROWSER_MODE:
                self.initSplash()
            if not self.USE_EXTERNAL_GATEWAY and (
                    self.has_min_java and self.has_dependencies):
                dmf_startup_err = Py4JGateway().startupGateway()
                if dmf_startup_err == 0:
                    if self.verbose:
                        print self.__class__.__name__, \
                            PRINT_COLON, "Started DMF gateway."
                else:
                    if self.verbose:
                        print self.__class__.__name__, \
                            PRINT_COLON, "Error starting DMF gateway."
                    # If gateway fails when using with server, kill immediately
                    if config:
                        if self.IS_BROWSER_MODE:
                            StatusDialog.displayStatus(
                                "Error starting DMF gateway.")
                        self.close()
                        return

            if self.IS_BROWSER_MODE:
                self.setGeometry(0, 0, MAIN_BROWSER_WIDTH, MAIN_BROWSER_HEIGHT)
                self.setMinimumSize(
                    MAIN_BROWSER_MIN_WIDTH, MAIN_BROWSER_MIN_HEIGHT)
                self.setWindowFlags(
                    Qt.CustomizeWindowHint
                    | Qt.WindowMinMaxButtonsHint
                    | Qt.WindowCloseButtonHint)
                # self.showMaximized()
            else:
                self.setWindowFlags(
                    Qt.CustomizeWindowHint | Qt.WindowMaximizeButtonHint)
                self.setGeometry(0, 0, MAIN_BROWSER_WIDTH, MAIN_BROWSER_HEIGHT)
                self.resize(MAIN_BROWSER_WIDTH, MAIN_BROWSER_HEIGHT)
                self.setMinimumSize(
                    MAIN_BROWSER_MIN_WIDTH, MAIN_BROWSER_MIN_HEIGHT)

            self.center()
            self.setWindowTitle(self.WINDOW_TITLE)
            self.setWindowIcon(QIcon(os.environ[DMF_HOME] + CCSI))
            self.checkEnvironmentVariables()

            self.config = config
            try:
                if config:
                    self.filesystem = AlfrescoFileSystem(self)
                    if self.filesystem.session is None:
                        if not self.USE_EXTERNAL_GATEWAY:
                            continue
                else:
                    self.filesystem = LocalFileSystem(self)
                vbox = QVBoxLayout()
                vbox.addWidget(self.filesystem)
                self.setLayout(vbox)
            except Exception, e:
                if self.verbose:
                    print self.__class__.__name__, \
                        PRINT_COLON, "Error:", e
            break

        if mode == BROWSER_MODE:
            self.splash.hide()
            self.splash.close()
            self.showMaximized()
        if self.verbose:
            init_end_millis = int(round(time.time() * 1000))
            print "Initialize duration: ", \
                (init_end_millis - init_start_millis)

    def initSplash(self):
        if self.verbose:
            print self.__class__.__name__, \
                PRINT_COLON, "Showing splashscreen..."
        x_indent = 30
        # Load the splash screen background svg, gonna draw text over
        pixmap = QPixmap(os.environ[DMF_HOME] + SPLASH_PATH)
        # Make a painter to add text to splash
        painter = QPainter(pixmap)
        font = painter.font()  # current font for drawing text
        font.setPointSize(12)
        painter.setFont(font)
        # Add dmf information next to splash graphic
        y_dmf_ver = 100
        painter.drawText(x_indent, y_dmf_ver, "version: " + __version__)
        y_dmf_email = 120
        painter.drawText(
            x_indent,
            y_dmf_email,
            "ccsi-support@acceleratecarboncapture.org")
        painter.end()
        self.splash = SplashScreen(pixmap)
        self.updateSplash("Loading...")
        self.splash.show()

    def updateSplash(self, message):
        if self.IS_BROWSER_MODE:
            self.splash.clearMessage()
            self.splash.showMessage(SPLASH_FORMAT_STR+message)
            self.splash.repaint()
            self.app.processEvents()

    def login(self, fname_no_ext, cipher):
        self.user = ''
        self.password = ''
        user_label = None
        password_label = None
        while True:
            self.user, self.password, is_info_save, result = \
                LoginDialog.getCredentials(
                    self.user,
                    self.password,
                    user_label,
                    password_label,
                    parent=self)
            if not result:
                return '', ''
            if self.user != '' and self.password != '':
                break
            else:
                if self.user == '':
                    user_label = "<font color='Red'>Username:*</font>"
                else:
                    user_label = None
                if self.password == '':
                    password_label = "<font color='Red'>Password:*</font>"
                else:
                    password_label = None

        if is_info_save:
            # Save credentials
            new_user = self.EncodeAES(cipher, self.user)
            new_key = self.EncodeAES(cipher, self.password)
            fname = fname_no_ext + KEYS_EXT
            f = codecs.open(fname, 'w', "utf-8-sig")
            f.write(new_user + '\t' + new_key + '\n')
            f.close()
        else:
            new_user = self.EncodeAES(cipher, self.user)
            new_key = self.EncodeAES(cipher, self.password)
            fname = fname_no_ext + TMP_KEYS_EXT
            f = codecs.open(fname, 'w', "utf-8-sig")
            f.write(new_user + '\t' + new_key + '\n')
            f.close()

        return self.user, self.password

    def addOneMonth(self, source):
        month = source.month
        year = source.year + month / 12
        month = month % 12 + 1
        day = min(source.day, calendar.monthrange(year, month)[1])
        return datetime.date(year, month, day)

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width()-size.width())/2,
            (screen.height()-size.height())/2)

    def tabClicked(self):
        if self.verbose:
            print "Tab clicked"

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            if self.verbose:
                print self.__class__.__name__, \
                    PRINT_COLON, "Escape key clicked."
            self.close()

    def closeEvent(self, event):
        if self.verbose:
            print self.__class__.__name__, \
                PRINT_COLON, "Close event invoked."
        try:
            self.filesystem.wait_loop
            if self.filesystem.wait_loop.isRunning():
                if self.verbose:
                    print self.__class__.__name__, \
                        PRINT_COLON, "Ignoring close event."
                StatusDialog.displayStatus(
                    "Please wait until upload is completed before exiting.")
                event.ignore()
                return
        except:
            pass
        super(DMFBrowser, self).closeEvent(event)
        if not self.USE_EXTERNAL_GATEWAY and self.has_min_java:
            Py4JGateway().shutdownGateway()
            Common().deleteCachedCredentials()
        if self.IS_BROWSER_MODE:
            try:
                # Splash screen may still be on
                self.splash.close()
            except:
                pass
            try:
                # self.filesystem may not be completely initialized
                self.filesystem.closeRootDialog()
            except:
                pass
            if self.EXIT_FLAG:
                try:
                    sys.exit(0)
                except Exception, e:
                    print self.__class__.__name__, PRINT_COLON, e
                    (type, value, tb) = sys.exc_info()
                    sys.excepthook(type, value, tb)
                    time.sleep(2)  # Wait awhile before exit
                    sys.exit(0)

    def checkEnvironmentVariables(self):
        if self.verbose:
            print 'Checking if environment variables are present...',
        try:
            os.environ[DMF_HOME]
            os.environ[DMF_HOME] = os.environ[DMF_HOME].replace(
                '"', '').replace('\\', '/')
        except KeyError:
            print "Please set the environment for", DMF_HOME
            sys.exit(1)
        if self.verbose:
            print 'OK'

    @staticmethod
    def getSession(self, config, repo):
        try:
            frame = DMFBrowser(config, repo, mode=OPEN_MODE)
            try:
                frame.filesystem
                frame.exec_()
                return frame.filesystem.getSession()
            except:
                return (None, ) * 2
        except:
            pass

    @staticmethod
    def getByteArrayStreamById(self, config, repo, dmf_id):
        try:
            dmf = DMFBrowser(config, repo)
            try:
                dmf.filesystem
                return dmf.filesystem.getByteArrayStreamById(dmf_id)
            except:
                return None
        except Exception, e:
            print e
            return None

    @staticmethod
    def getSimFileByteArrayStreamByName(self, config, repo, name):
        try:
            dmf = DMFBrowser(config, repo)
            return dmf.filesystem.getSimFileByteArrayStreamByName(name)
        except Exception, e:
            print e
            return None

    @staticmethod
    def saveByteArrayStream(
            self,
            b,
            parents,
            config,
            update_comment=None,
            repo=None,
            mode=SAVE_MODE):
        try:
            frame = DMFBrowser(config, repo, mode)
            frame.filesystem.setUpdateComment(update_comment)
            frame.filesystem.setByteArrayStream(b)
            frame.filesystem.setParents(parents)
            frame.exec_()
            return frame.filesystem.getSavedMetadata()
        except Exception, e:
            _, _, tb = sys.exc_info()
            logging.getLogger("foqus." + __name__).error(
                "Exception at line {n}: {e}".format(
                    n=traceback.tb_lineno(tb),
                    e=str(e)))

    @staticmethod
    def doFilesExist(self, config, repo, dmf_id_list):
        try:
            frame = DMFBrowser(config, repo)
            result = []
            for id in dmf_id_list:
                result.append(frame.filesystem.doesFileExist(id))
            return result
        except:
            return None

    @staticmethod
    def isLatestVersion(self, config, repo, dmf_id):
        try:
            frame = DMFBrowser(config, repo)
            return frame.filesystem.isLatestVersion(dmf_id)
        except:
            return None

    @staticmethod
    def uploadSimulation(
            self,
            config,
            repo,
            sim_bytestream,
            sim_id,
            sim_name,
            update_comment,
            confidence,
            sinter_config_bytestream=None,
            sinter_config_name=None,
            resource_bytestream_list=None,
            resource_name_list=None,
            description=None):
        try:
            sc_json = json.loads(sinter_config_bytestream.decode(UTF8))
            description = sc_json.get(SC_DESC, None)
            if sc_json.get(SC_MODEL, None):
                sim_name = sc_json[SC_MODEL][SC_FILE_DESG]
            else:
                print "No simulation specified in sinter config."
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
            dmf = DMFBrowser(config, repo)
            return dmf.filesystem.uploadSimulationFiles(
                sinter_config_bytestream,
                sinter_config_name,
                update_comment,
                confidence,
                sim_bytestream,
                sim_id,
                sim_name,
                resource_bytestream_list,
                resource_name_list,
                version_reqs=ver_req,
                sim_title=sim_title,
                description=description)
        except Exception, e:
            _, _, tb = sys.exc_info()
            logging.getLogger("foqus." + __name__).exception(str(e))
            return (None, ) * 3

    @staticmethod
    def downloadZipFolderByPath(self, config, repo, folder_path, target_path):
        isSuccess = True
        try:
            dmf = DMFBrowser(config, repo)
            dmf.filesystem.downloadFolderByPath(folder_path, target_path)
        except Exception, e:
            print e
            isSuccess = False
        return isSuccess

    @staticmethod
    def getSimulationList(self, config, repo):
        try:
            dmf = DMFBrowser(config, repo)
            return dmf.filesystem.getSimulationList()
        except Exception, e:
            print e

    @staticmethod
    def turbineSync(self, config, repo, turbine_config, session_sim_list,
                    turbine_sim_list):
        try:
            dmf = DMFBrowser(config, repo)
            return dmf.filesystem.turbineSync(
                turbine_config, session_sim_list, turbine_sim_list)
        except Exception, e:
            print e

    @staticmethod
    def getSimIDByName(self, config, repo, sim_name):
        try:
            dmf = DMFBrowser(config, repo)
            return dmf.filesystem.getSimIDByName(sim_name)
        except Exception, e:
            print e
