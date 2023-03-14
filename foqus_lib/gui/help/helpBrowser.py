#################################################################################
# FOQUS Copyright (c) 2012 - 2023, by the software owners: Oak Ridge Institute
# for Science and Education (ORISE), TRIAD National Security, LLC., Lawrence
# Livermore National Security, LLC., The Regents of the University of
# California, through Lawrence Berkeley National Laboratory, Battelle Memorial
# Institute, Pacific Northwest Division through Pacific Northwest National
# Laboratory, Carnegie Mellon University, West Virginia University, Boston
# University, the Trustees of Princeton University, The University of Texas at
# Austin, URS Energy & Construction, Inc., et al.  All rights reserved.
#
# Please see the file LICENSE.md for full copyright and license information,
# respectively. This file is also available online at the URL
# "https://github.com/CCSI-Toolset/FOQUS".
#################################################################################
""" turbineConfiguration.py

* This class contains Turbine configuration profiles and  functions for
  interacting with Turbine
* trying to move turbine related stuff into one place so fixes and
  improvements to the Turbine interaction are easier

Joshua Boverhof, Lawrence Berkeley National Lab
John Eslick, Carnegie Mellon University, 2014
"""

import os
import time
import logging
import base64
import json
import threading
from datetime import datetime
from foqus_lib.framework.sim.turbineConfiguration import TurbineConfiguration
import websocket
from typing import Optional
from foqus_lib.help.helpPath import *
from foqus_lib.gui.pysyntax_hl.pysyntax_hl import *
from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox, QTextBrowser
from PyQt5.QtWidgets import QMainWindow

mypath = os.path.dirname(__file__)
_helpBrowserDockUI, _helpBrowserDock = uic.loadUiType(
    os.path.join(mypath, "helpBrowser_UI.ui")
)
from foqus_lib.framework.session.session import session as _session


class helpBrowserDock(_helpBrowserDock, _helpBrowserDockUI):
    # showHelpTopic = QtCore.pyqtSignal([types.StringType])
    showAbout = QtCore.pyqtSignal()
    hideHelp = QtCore.pyqtSignal()

    def __init__(
        self, parent: Optional[QMainWindow] = None, dat: Optional[_session] = None
    ):
        """
        Node view/edit dock widget constructor
        """
        assert (
            isinstance(dat, _session) or dat is None
        ), "parameter dat is %s, expecting %s" % (type(dat), _session)
        assert (
            isinstance(parent, QMainWindow) or parent is None
        ), "parameter parent is %s, expecting %s" % (type(parent), QMainWindow)
        super(helpBrowserDock, self).__init__(parent=parent)
        self.setupUi(self)
        self.dat = dat
        self.mw = parent
        self._cloud_notification = None
        self.aboutButton.clicked.connect(self.showAbout.emit)
        # self.contentsButton.clicked.connect(self.showContents)
        self.licenseButton.clicked.connect(self.showLicense)
        self.ccsidepButton.clicked.connect(self.showCCSIDep)
        self.textBrowser = QTextBrowser(self.tabWidget.widget(0))
        self.webviewLayout.addWidget(self.textBrowser)
        self.helpPath = os.path.join(helpPath(), "html")
        self.showLicense()
        self.execButton.clicked.connect(self.runDebugCode)
        self.stopButton.clicked.connect(self.setStopTrue)
        self.loadButton.clicked.connect(self.loadDbgCode)
        self.saveButton.clicked.connect(self.saveDbgCode)
        self.ccButton.clicked.connect(self.clearCode)
        self.crButton.clicked.connect(self.clearRes)
        self.clearLogButton.clicked.connect(self.clearLogView)
        self.statusCloudButton.clicked.connect(self.clearCloudLogView)
        self.synhi = PythonHighlighter(self.pycodeEdit.document())
        self.stop = False
        self.timer = None

    def getWidget(self):
        w = self.mw.app.focusWidget()
        return w

    def getPopupWidget(self):
        w = self.mw.app.activePopupWidget()
        return w

    def getWindow(self):
        w = self.mw.app.activeWindow()
        return w

    def getButton(self, w, label):
        blist = w.buttons()
        for b in blist:
            if b.text().replace("&", "") == label:
                return b
        return None

    def closeMessageBox(self):
        w = self.getWindow()
        if isinstance(w, QMessageBox):
            w.close()

    def pressButton(self, w, label):
        b = self.getButton(w, label)
        if b is not None:
            b.click()
        else:
            print("{0} has no button {1}".format(w, label))

    def msgBoxOK(self):
        w = self.getWindow()
        if isinstance(w, QMessageBox):
            self.pressButton(w, "OK")
            return True
        return False

    def msgBoxYes(self):
        w = self.getWindow()
        if isinstance(w, QMessageBox):
            self.pressButton(w, "Yes")

    def msgBoxNo(self):
        w = self.getWindow()
        if isinstance(w, QMessageBox):
            self.pressButton(w, "No")

    def msgBoxCancel(self):
        w = self.getWindow()
        if isinstance(w, QMessageBox):
            self.pressButton(w, "Cancel")

    def dailogNotModal(self):
        w = self.getWindow()
        if isinstance(w, QDialog):
            w.setModal(False)

    def setStopTrue(self):
        self.stop = True
        print("Stopping dbg")

    def loadDbgCode(self, fileName=None):
        if fileName is None:
            fileName, filtr = QFileDialog.getOpenFileName(
                self, "Open File", "", "Python files (*.py);;All Files (*)"
            )
        if fileName:
            self.clearCode()
            with open(fileName, "r") as f:
                code = f.read()
            self.pycodeEdit.setPlainText(code)

    def saveDbgCode(self):
        fileName, filtr = QFileDialog.getOpenFileName(
            self, "Save File", "", "Python files (*.py);;All Files (*)"
        )
        if fileName:
            s = self.pycodeEdit.plainText()
            with open(fileName, "r") as f:
                f.write(s)

    def showContents(self):
        self.setPage(os.path.join(self.helpPath, "content.html"))

    def showLicense(self):
        self.setPage(os.path.join(self.helpPath, "license.html"))

    def showCCSIDep(self):
        self.setPage(os.path.join(self.helpPath, "ccsiDependencies.html"))

    def setPage(self, page):
        with open(page, "r") as f:
            s = f.read()
        self.textBrowser.setHtml(s)

    def clearCode(self):
        self.pycodeEdit.clear()

    def clearRes(self):
        self.resEdit.clear()

    def runDebugCode(self):
        self.stop = False
        pycode = self.pycodeEdit.toPlainText()
        r = self.dat.runDebugCode(pycode, self.mw)
        self.resEdit.appendPlainText(str(r))
        self.stop = False

    def showHelp(self):
        self.updateLogView()
        self.startTimer()

    def closeEvent(self, ev):
        self.stopTimer()
        self.hideHelp.emit()

    def startTimer(self):
        """
        Start the timer to update the log file viewer
        """
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.updateLogView)
        self.timer.start(1000)

    def stopTimer(self):
        """
        Stop the timer to update the log file viewer
        """
        try:
            self.timer.stop()
            del self.timer
            self.timer = None
        except Exception as e:
            print("error stopping timer: {0}".format(e))

    def clearLogView(self):
        """
        Clear the log text
        """
        self.logView.clear()

    def clearCloudLogView(self):
        """
        Clear the Cloud log text
        """
        self.CloudLogView.clear()
        self.showStatus()

    def timerCB(self):
        """
        Function called by the timer to ubdate log display.
        """
        if self.logView.isVisible():
            self.updateLogView()

    def updateLogView(self, maxRead=1000, delay=1000):
        """
        Update the log viewer text box
        maxRead = the maximum number of lines to read from the log
            at one time
        """
        lr = 0
        if self.timer is not None:
            self.timer.stop()
        try:
            done = False
            with open(self.dat.currentLog, "r") as f:
                f.seek(0, 2)
                if self.dat.logSeek > f.tell():
                    self.dat.logSeek = 0
                f.seek(self.dat.logSeek)
                while lr < maxRead:
                    line = f.readline()
                    self.dat.logSeek = f.tell()
                    if not line:
                        done = True
                        break
                    else:
                        lr += 1
                        self.logView.append(line.strip())
            if self.timer is not None:
                if done:
                    self.timer.start(delay)  # no more to read wait a sec
                else:
                    self.timer.start(10)  # more to read don't wait long
        except:
            logging.getLogger("foqus." + __name__).exception(
                "Error opening log file for log viewer, " "stopping the update timer"
            )

        if (
            self._cloud_notification is None
            and self.dat.foqusSettings.runFlowsheetMethod == 1
        ):
            # Cloud View
            self._cloud_notification = False
            if not self.dat.flowsheet.turbConfig.notification:
                self.CloudLogView.append("==> Disabled")
                return
            self.CloudLogView.append("==> Start")
            try:
                self._cloud_notification = WebSocketApp(
                    self.CloudLogView, self.dat.flowsheet.turbConfig
                )
            except ValueError as e:
                logging.getLogger("foqus." + __name__).info(str(e))
                self.CloudLogView.append("Cloud Notifcations: OFF")
                self.CloudLogView.append(
                    "turbine configuration section Application, key notification"
                )
            else:
                self._cloud_notification.signalUpdateStatus.connect(self.showStatus)
                self._cloud_notification.start()

    def showStatus(self):
        logging.getLogger("foqus." + __name__).info("on_message")
        self.widget = self.CloudLogView
        self.widget.clear()
        self.widget.append("%s>" % (datetime.now().isoformat()))
        d = json.loads(self._cloud_notification.message)
        if "sqs" in d:
            self.widget.append("== SQS Job Queue:")
            for k, v in d["sqs"].get("Attributes", {}).items():
                self.widget.append("  %s: %s" % (k, v))
        if "autoscale" in d:
            self.widget.append("== AutoScale:")
            for group in d["autoscale"].get("AutoScalingGroups", []):
                self.widget.append("  %s" % (group["AutoScalingGroupName"]))
                for key in ["MinSize", "MaxSize", "DesiredCapacity"]:
                    self.widget.append("    %s: %s" % (key, group[key]))
        if "ec2" in d:
            self.widget.append("== EC2:")
            for reservation in d["ec2"].get("Reservations", []):
                for inst in reservation["Instances"]:
                    logging.getLogger("foqus." + __name__).info(inst)
                    tag_name = "NO NAME"
                    for tag in filter(lambda a: a["Key"] == "Name", inst["Tags"]):
                        tag_name = tag["Value"]
                    self.widget.append("  %s" % (tag_name))
                    for key in ["InstanceType", "Platform", "State"]:
                        self.widget.append("    %s: %s" % (key, inst[key]))


# class WebSocketApp(threading.Thread):
class WebSocketApp(QtCore.QThread):
    signalUpdateStatus = QtCore.pyqtSignal()

    def __init__(self, widget: QTextBrowser, config: TurbineConfiguration):
        # threading.Thread.__init__(self)
        super().__init__()
        self.stop = threading.Event()
        self.daemon = True
        assert type(widget) is QTextBrowser, type(widget)
        assert type(config) is TurbineConfiguration, type(config)
        websocket.enableTrace(True)
        wss_url = config.notification
        if not wss_url.startswith("wss://"):
            raise ValueError("Require Web Sockets Secure (wss) protocol")
        usertok = "%s:%s" % (config.user, config.pwd)
        token = base64.b64encode(bytes(usertok, "utf-8")).decode("ascii")
        header = "Authorization: Basic {0}".format(token)
        self.ws = websocket.WebSocketApp(
            wss_url,
            header=[header],
            on_message=self.on_message,
            on_open=self.on_open,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        self.widget = widget
        self.config = config
        self.url = wss_url

    def on_message(self, wsapp, message):
        self.message = message
        self.signalUpdateStatus.emit()

    def on_error(self, wsapp, error):
        logging.getLogger("foqus." + __name__).error(error)
        self.widget.append("Notification error: %s" % (error))

    def on_close(self, wsapp):
        logging.getLogger("foqus." + __name__).info("WSS closed")

    def on_open(self, wsapp):
        logging.getLogger("foqus." + __name__).debug("WSS open: %s" % self.url)
        self.ws.send('{"action":"status"}')

    def run(self):
        logging.getLogger("foqus." + __name__).info("run_forever")
        self.ws.run_forever()
