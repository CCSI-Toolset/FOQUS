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

John Eslick, Carnegie Mellon University, 2014
"""
import os
import os.path
import configparser
import json
import re
import time
import random
import ssl
import urllib.parse
import urllib.request
import logging
import traceback
import subprocess
import socket
import imp
import foqus_lib.framework.sim.process_management as _pm

_log = logging.getLogger("foqus." + __name__)
from collections import OrderedDict


if os.name == "nt":
    import win32process

    try:
        from . import turbineLiteDB
    except Exception:
        _log.exception("Problem importing turbineLiteDB")

from foqus_lib.framework.foqusException.foqusException import *
import turbine.commands.turbine_application_script as _tapp
import turbine.commands.turbine_session_script as _tsess
import turbine.commands.turbine_simulation_script as _tsim
import turbine.commands.turbine_job_script as _tjob
import turbine.commands.turbine_consumer_script as _tcon
import turbine.commands
from turbine.commands.requests_base import (
    HTTPStatusCode,
    read_configuration,
    get_page_by_url,
    post_page_by_url,
    delete_page,
)
from turbine.commands import turbine_session_result_script


class TurbineInterfaceEx(foqusException):
    """
    This is an exception class for FOQUS interaction with Turbine, it also tries
    to sort out exactly what the problem is if there is any trouble connecting to
    Turbine.
    """

    def __init__(self, code=0, msg="", e=None, tb=None):
        foqusException.__init__(self, code=code, msg=msg, tb=tb)
        if code == 0 and e:
            # If no code was given, but an original exception is given
            # try to convert the original exception into something I can
            # understand
            if isinstance(e, urllib.request.HTTPError):
                if e.code == 401:
                    self.code = 11
                elif e.code == 404:
                    self.code = 12
                else:
                    self.code = 10
            elif isinstance(e, urllib.request.URLError):
                if isinstance(e.reason, ssl.SSLError):
                    self.code = 5
                elif isinstance(e.reason, str):
                    self.code = 1
                elif e.reason.errno == 10060:
                    # connection timeout
                    self.code = 2
                elif e.reason.errno == 10054:
                    # forcible reset
                    self.code = 3
                else:
                    self.code = 1
            elif isinstance(e, socket.error):
                if e.errno == 10054:
                    self.code = 3
                elif e.reason.errno == 10060:
                    # connection timeout
                    self.code = 2
                else:
                    self.code = 7

    def setCodeStrings(self):
        self.codeString[0] = "Unknown Error"
        self.codeString[1] = "Unknown gateway URL error"
        self.codeString[2] = (
            "Gateway did not respond (maybe a bad address, "
            "network problem, or gateway is down)"
        )
        self.codeString[3] = "Forcible connection reset by Gateway"
        self.codeString[5] = "Gateway SSL error (probably wrong address)"
        self.codeString[7] = "Unknown Socket Error"
        self.codeString[10] = "Gateway unknown http error"
        self.codeString[
            11
        ] = "Gateway 401 authentication error (bad user name or password)"
        self.codeString[12] = "Gateway 404 page not found error"
        self.codeString[13] = "Gateway 403 access forbidden"
        self.codeString[14] = "Gateway 400 bad request"
        self.codeString[15] = "Gateway 500 server error"
        self.codeString[151] = "Could not start Turbine consumer"
        self.codeString[152] = "Cound not get consumer ID"
        self.codeString[153] = (
            "Will not start consumer for non-Lite Turbine, check local"
            " Turbine config file."
        )
        self.codeString[201] = "Could not read turbine configuration"
        self.codeString[202] = "Could not write turbine configuration"
        self.codeString[300] = "Unknown error uploading a simulation on Turbine"
        self.codeString[301] = (
            "Uploading or updating simulation, simulation name can "
            "contain only letters, numbers, and _"
        )
        self.codeString[302] = (
            "Uploading or updating simulation, could not open "
            "SimSinter configuration file"
        )
        self.codeString[303] = (
            "Uploading or updating simulation, could not parse "
            "SimSinter configuration file"
        )
        self.codeString[304] = (
            "Uploading or updating simulation, could not find "
            "model file path in SimSinter configuration"
        )
        self.codeString[305] = (
            "Uploading or updating simulation, could not find "
            "model file specified in SimSinter configuration"
        )
        self.codeString[306] = (
            "Uploading or updating simulation, unrecognized " "model file extension"
        )
        self.codeString[307] = (
            "Uploading or updating simulation, resource type found "
            "from model file extension does not match the "
            "SimSinter configuration"
        )
        self.codeString[308] = (
            "Uploading or updating simulation, application not " "available on Turbine"
        )
        self.codeString[309] = (
            "Uploading or updating simulation, simulation already "
            "exists and update is not set to True"
        )
        self.codeString[310] = "Could not update simulation, it does not exist"
        self.codeString[350] = "Job failed"
        self.codeString[
            351
        ] = "Job failed to converge (may have also been another error)"
        self.codeString[352] = "Job failed due to run timeout"
        self.codeString[353] = "Job failed due to max wait timeout"
        self.codeString[354] = "Job failed could not get status"
        self.codeString[355] = "Job failed thread terminated"
        self.codeString[356] = "Job failed because consumer stopped"
        self.codeString[360] = "Could not find simulation"


class ConsumerInfo:
    def __init__(self, cid=None, location=0, proc=None):
        self.cid = cid
        self.proc = proc
        self.location = location  # 0 local, 1 remote


class TurbineConfiguration:
    """
    This class stores the information needed to write a turbine
    configuration file it may also store other parameters related to
    turbine. It also contains functions to interact with Turbine.
    I'm trying to move all the Turbine calls to one place to make
    it easier to find any turbine related bugs or add improvements
    as Turbine is update.
    """

    resourceNames = {
        "Excel": "spreadsheet",
        "ACM": "aspenfile",
        "GProms": "model",
        "AspenPlus": "aspenfile",
        "FOQUS-User-Plugin": "plugin",
    }
    appExtensions = {
        ".xls": "Excel",
        ".xlsx": "Excel",
        ".xlsm": "Excel",
        ".acmf": "ACM",
        ".gENCRYPT": "GProms",
        ".gencrypt": "GProms",
        ".bkp": "AspenPlus",
        ".apw": "AspenPlus",
        ".apwz": "AspenPlus",
        ".py": "FOQUS-User-Plugin",
    }

    def __init__(self, path="turbine.cfg"):
        """
        constructor
        """
        self.path = path
        self.aspenVersion = 2
        # error code of things that may work if retried
        self.retryErrors = [2, 3, 5, 10, 11]
        self.address = "http://localhost:8000/TurbineLite"
        self.__wss_notification_url = ""
        self.user = ""
        self.pwd = ""
        self.turbVer = "Lite"  # Lite, Remote or ....
        self.turbineLiteHome = "C:\\Program Files (x86)\\Turbine\\Lite"
        self.consumers = {}
        self.consumerCountDict = {}
        self.reloadTurbine()
        self.aspenVersion = 2
        self.dat = None
        self.tldb = None
        # WHY: setting these directly in makeCopy without defining them as attributes here
        # triggers no-member errors in pylint 2.14.1
        self.configExt = None
        self.subDir = None

    @property
    def notification(self):
        return self.__wss_notification_url

    @notification.setter
    def notification(self, url):
        assert type(url) is str and url.startswith("wss://"), (
            "Require WebSocket Secure URL:  %s" % url
        )
        self.__wss_notification_url = url

    def getTurbineLiteDB(self):
        if self.tldb is None:
            db = turbineLiteDB.turbineLiteDB()
            db.dbFile = os.path.join(
                self.dat.foqusSettings.turbLiteHome, "Data/TurbineCompactDatabase.sdf"
            )
            self.tldb = db
        return self.tldb

    def closeTurbineLiteDB(self):
        if self.tldb is not None:
            self.tldb.closeConnection()
        self.tldb = None

    def updateSettings(self, altConfig=None):
        """
        try to get updated settings from the foqus settings
        """
        try:
            if self.dat:
                if self.dat.foqusSettings.runFlowsheetMethod == 0:
                    if altConfig is not None:
                        self.path = altConfig
                    else:
                        self.path = self.dat.foqusSettings.turbConfig
                    self.aspenVersion = self.dat.foqusSettings.aspenVersion
                    self.turbineLiteHome = self.dat.foqusSettings.turbLiteHome
                else:
                    self.path = self.dat.foqusSettings.turbConfigCluster
                    self.aspenVersion = self.dat.foqusSettings.aspenVersion
                    self.turbineLiteHome = self.dat.foqusSettings.turbLiteHome
            self.readConfig()
            self.reloadTurbine()
        except:
            _log.exception("Could not load FOQUS settings.")
            raise RuntimeError("Failed to load FOQUS Settings")

    def makeCopy(self):
        """
        Make a copy of the turbine config instance
        """
        newCopy = TurbineConfiguration(self.getFile())
        newCopy.configExt = self.configExt
        newCopy.subDir = self.subDir
        newCopy.address = self.address
        newCopy.user = self.user
        newCopy.pwd = self.pwd
        return newCopy

    def getSimApplication(self, simName):
        try:
            l = _tsim.main_list([self.getFile()], None)
            for i in l:
                if i["Name"] == simName:
                    return i["Application"]
            raise TurbineInterfaceEx(
                code=360,
                msg="Could not find simulation: {0}".format(simName),
                tb=traceback.format_exc(),
            )
        except Exception as e:
            _log.exception("Error getting simulation application")
            raise TurbineInterfaceEx(
                code=0,
                msg="Error getting simulation application",
                e=e,
                tb=traceback.format_exc(),
            )

    def startConsumer(self, nodeName, simName):
        _log.debug("Starting simulation consumer...")
        if self.turbVer != "Lite":
            raise TurbineInterfaceEx(code=153)
        if self.checkConsumer(nodeName):
            # consumer already exists so just return it
            # if you want to restart explicitly stop the consumer
            # first
            return self.consumers[nodeName]
        # Consumer will be started so zero the use counter
        self.consumerCountZero(nodeName)
        app = self.getSimApplication(simName)
        if app == "ACM" or app == "AspenPlus":
            # Start aspen consumer
            if self.aspenVersion == 1:
                f = "{0}\\Clients\\AspenSinter73ConsumerConsole.exe".format(
                    self.turbineLiteHome
                )
            else:
                f = "{0}\\Clients\\AspenSinterConsumerConsole.exe".format(
                    self.turbineLiteHome
                )
        elif app == "Excel":
            # Start aspen consumer
            f = "{0}\\Clients\\ExcelSinterConsumerConsole.exe".format(
                self.turbineLiteHome
            )
        elif app == "gPROMS" or app == "GProms":
            f = "{0}\\Clients\\GPromsSinterConsumerConsole.exe".format(
                self.turbineLiteHome
            )
        else:
            _log.error("no consumer for app = {0}".format(app))
            return None
            _log.debug("  Exe: {0}".format(f))

        sinter_process_log = open("%s_sinter_log.txt" % app, "a")
        sinter_process_log.write("starting consumer\n")
        proc = subprocess.Popen(
            [f],
            stdout=sinter_process_log,
            stderr=subprocess.STDOUT,
            stdin=None,
            creationflags=win32process.CREATE_NO_WINDOW,
        )
        if proc is None:
            raise TurbineInterfaceEx(code=151)
        # get consumer id from db
        db = self.getTurbineLiteDB()
        cid = None
        for i in range(40):
            _log.debug("  Waiting for consumer to register in DB...")
            time.sleep(2)
            cid = db.consumer_id(proc.pid)
            if cid is not None:

                break
        if cid is not None:
            self.consumers[nodeName] = ConsumerInfo(cid, 0, proc)
            _log.debug("Started consumer for {0}, id: {1}".format(app, cid))
        else:
            raise TurbineInterfaceEx(code=151)
        return proc

    def consumerID(self, nodeName):
        ci = self.consumers.get(nodeName, None)
        if ci is None:
            return None
        cid = ci.cid
        if cid is None:
            return 0
        return cid

    def consumerCountZero(self, nodeName):
        """
        Set the consumer use counter to 0
        """
        self.consumerCountDict[nodeName] = 0

    def consumerCount(self, nodeName):
        """
        Get the number of times a consumer has been used
        """
        return self.consumerCountDict.get(nodeName, 0)

    def consumerCountInc(self, nodeName):
        """
        Add incriment consumer count
        """
        count = self.consumerCountDict.get(nodeName, None)
        if count == None:
            self.consumerCountZero(nodeName)
            return 0
        self.consumerCountDict[nodeName] = count + 1
        return self.consumerCountDict[nodeName]

    def checkConsumer(self, name):
        """
        Check that the consumer is still running
        """
        ci = self.consumers.get(name, None)
        if ci is None:
            return None
        if ci.location == 0:
            if ci.proc.poll() is not None:
                del self.consumers[name]
                return None
            else:
                return ci.proc
        if ci.location == 1:
            # need to write this is just a place holder.
            return True
        return None

    def stopConsumer(self, name, maxWait=150):
        """
        Stop the consumer for node name
        """
        ci = self.consumers.get(name, None)
        if ci is not None and ci.location == 1:
            return
        proc = self.checkConsumer(name)
        if proc != None:
            kw = dict()
            cp = self.turbineConfigParse()
            url, auth, params = read_configuration(cp, _tcon.SECTION, **kw)
            try:
                is_stopping = _tcon.post_consumer_stop(url, auth, str(ci.cid))
                _log.info("Stop Consumer {} Requested: {}".format(ci.cid, is_stopping))
                swt = time.time()
                while proc.poll() is None:
                    # wait for consumer to go down
                    if time.time() - swt > maxWait:
                        _log.error(
                            "Error stopping consumer {} "
                            "Subprocess still running?".format(ci.cid)
                        )
                        break
                    time.sleep(1.0)
            except Exception as e:
                _log.exception("Error stopping consumer {}".format(ci.cid))
                raise TurbineInterfaceEx(
                    code=0,
                    msg="Failed to stop consumer: {0}".format(ci.cid),
                    e=e,
                    tb=traceback.format_exc(),
                )
            _pm.clean()
        try:
            del self.consumers[name]
        except:
            pass

    def stopAllConsumers(self):
        """
        Stop all the consumers that were started by FOQUS
        """
        names = list(self.consumers.keys())
        for name in names:
            self.stopConsumer(name)
        _log.debug("Stopped all running consumers")
        _pm.clean()

    def reloadTurbine(self):
        """
        Turbine Client tends to store some stuff like results of
        authentication and it is hard to change the password and
        try again this reloads turbine so it doesn't store anything
        and you can change the configuration.
        """
        imp.reload(turbine.commands)
        # make sure turbine doesn't change my log settings by telling it
        # the log settings have already been done and not to change them
        turbine.commands._setup_logging.done = True

    def checkAddress(self):
        """
        Catch some things to try to make sure the turbine address is
        in the right form I don't expect and ending / or \ so remove
        those.  Maybe could add more checks later
        """
        if self.address[-1] == "/":
            self.address = self.address[:-1]
        elif self.address[-1] == "\\":
            self.address = self.address[:-1]

    def retryFunction(self, maxTries, waitTime, waitPow, function, *args, **kwargs):
        """
        This retries a function maxTries times.  You can ether check
        in even intervals, increase the wait linearly or add a power
        the formula is (waitTime)*(interval number)**(waitPower)

        function is the function pointer and args and kwargs are the
        ordered and keyword arguments for the function.
        """
        # Only retry on errors I expect could possibly resolve with time
        # (could be caused by a temprary network/sever problem)
        retryList = self.retryErrors  # actually I gave up on this, there
        # are too many weird unexpected
        # errors that work on second attempt
        for i in range(maxTries):
            try:
                # if successful just return results
                return function(*args, **kwargs)
            except TurbineInterfaceEx as e:
                if not e.code in retryList:
                    # Not using this anymore just pass and retry anything
                    pass
                elif e.code == 11:
                    self.reloadTurbine()
                else:
                    # retry
                    pass
                rt = waitTime * (i + 1) ** waitPow
                _log.exception(
                    "Turbine Interface Error: Retry {} in {}s.".format(i + 1, rt)
                )
            time.sleep(rt)
        # If ran out of tries re-raise last exception
        raise e

    def getFile(self):
        """
        Return the path to the turbine
        configuration file for this profile.
        """
        return self.path

    def readConfigPeek(self, path):
        """
        Peek at the address in a Turbine config file, without
        using the information to update the current Turbine config
        information.
        """
        config = configparser.ConfigParser()
        config.optionxform = str  # makes options case sensitive
        try:
            config.read(path)
            address = config.get("Job", "url")
            address = address[:-5]
        except Exception as e:
            raise TurbineInterfaceEx(code=201, msg=path + " " + str(e))
        return address

    def readConfig(self, address=True, logging=False):
        """
        FOQUS will write the turbine configuration files.  The user
        name and password are not stored though so this can be used
        to read them from a previously stored file.  Setting address
        to True will also try to read the address from the previous
        configuration file.
        """
        path = self.getFile()
        _log.debug('turbine configuration="%s"', path)
        config = configparser.ConfigParser()
        config.optionxform = str  # makes options case sensitive
        try:
            config.read(path)
            self.user = config.get("Authentication", "username")
            self.pwd = config.get("Authentication", "password")
            if config.has_option("Notification", "url"):
                self.notification = config.get("Notification", "url")
            if address:
                # args = config.get("Job",  "url")
                args = config.get("Application", "url")
                _log.debug('turbine configuration application url="%s"', args)
                assert args != "", "Missing Application URL"
                args = args.split("/")
                self.address = None
                while self.address is None:
                    item = args.pop()
                    if item.lower() == "application":
                        self.address = "/".join(args)
                        break
                _log.debug('turbine configuration url="%s"', self.address)
            self.checkAddress()
            if self.address[-4:] in ["Lite", "lite", "LITE"]:
                self.turbVer = "Lite"
            else:
                self.turbVer = "Remote"
            if self.address.startswith("http://"):
                # as username and password here will stop foqus dead
                # due to a sys.exit() in turbine client so make sure
                # that doesn't happen
                if self.user or self.pwd:
                    self.user = ""
                    self.pwd = ""
            self.writeConfig()
        except Exception as e:
            raise TurbineInterfaceEx(code=201, msg=path + " " + str(e))

    def writeConfig(self, overwrite=True):
        """
        Write the Turbine configuration file
        """
        path = self.getFile()
        if overwrite == True or not os.path.isfile(path):
            try:
                config = self.turbineConfigParse()
                with open(path, "w") as configfile:
                    config.write(configfile)
            except Exception as e:
                raise TurbineInterfaceEx(code=202, msg=" ".join([path, str(e)]))

    def turbineConfigParse(self):
        """
        Create a turbine configuration parse object
        (this can be used to write the configuration file)
        """
        self.checkAddress()
        config = configparser.ConfigParser()
        config.optionxform = str  # makes options case sensitive
        config.add_section("Consumer")
        config.add_section("Job")
        config.add_section("Simulation")
        config.add_section("Session")
        config.add_section("Application")
        config.add_section("Authentication")
        address = self.address
        config.set("Consumer", "url", address + "/consumer/")
        config.set("Job", "url", address + "/job/")
        config.set("Simulation", "url", address + "/simulation/")
        config.set("Session", "url", address + "/session/")
        config.set("Application", "url", address + "/application/")
        config.set("Authentication", "username", self.user)
        config.set("Authentication", "password", self.pwd)
        if self.turbVer == "Remote":
            config.set("Simulation", "SignedUrl", "True")
        if self.notification:
            config.add_section("Notification")
            config.set("Notification", "url", self.notification)
        return config

    def getApplicationList(self):
        """
        This function gives a list of applications supported
        by the Turbine gateway
        """
        try:
            l = _tapp.main_list([self.getFile()], None)
            l = [i["Name"] for i in l]
            return l
        except Exception as e:
            raise TurbineInterfaceEx(
                code=0, msg="Error getting application", e=e, tb=traceback.format_exc()
            )

    def getSimulationList(self):
        """
        This function provides a list of simulation names for
        simulations stored on Turbine
        """
        try:
            l = _tsim.main_list([self.getFile()], None)
            l = [i["Name"] for i in l]
            return l
        except Exception as e:
            _log.exception("Error getting list of simulation from Turbine")
            raise TurbineInterfaceEx(
                code=0,
                msg="Error getting simulation list",
                e=e,
                tb=traceback.format_exc(),
            )

    def deleteSimulation(self, simName):
        """
        This function deletes a simulation
        """
        try:
            l = _tsim.main_delete([simName, self.getFile()], None)
        except Exception as e:
            raise TurbineInterfaceEx(
                code=0, msg="Error deleting simulation", e=e, tb=traceback.format_exc()
            )

    def getSimResource(self, simName, resource="configuration", fname=None):
        try:
            if fname == None:
                r = _tsim.main_get(["-r", resource, simName, self.getFile()], None)
                return r
            else:
                _tsim.main_get(
                    ["-r", resource, simName, self.getFile(), "-s", fname], None
                )
        except Exception as e:
            raise TurbineInterfaceEx(
                code=0,
                msg="".join(
                    ["Failed simulation resource: {0}".format(resource), simName]
                ),
                e=e,
                tb=traceback.format_exc(),
            )

    def getSinterConfig(self, simName):
        """
        This function gets the SimSinter configuration file for a
        simulation named simName
        """
        r = self.getSimResource(simName, resource="configuration")
        try:
            config = json.loads(r, object_pairs_hook=OrderedDict)
            return config
        except Exception as e:
            raise TurbineInterfaceEx(
                code=0,
                msg="".join(
                    ["Failed to download sinter config for simulation ", simName]
                ),
                e=e,
                tb=traceback.format_exc(),
            )

    def getSessionList(self):
        """
        This function provides a list of Turbine session ids
        already created on the gateway
        """
        try:
            l = _tsess.main_list([self.getFile()])
            return l
        except Exception as e:
            raise TurbineInterfaceEx(
                code=0,
                msg="Error getting session list. ",
                e=e,
                tb=traceback.format_exc(),
            )

    # def getSessionStatus(self, sid):
    #     """
    #     This function gets the status of jobs in a session
    #     """
    #     try:
    #         l = turbine.commands.turbine_session_script.main_jobs_status(
    #             [sid, self.getFile()], None
    #         )
    #         return l
    #     except Exception as e:
    #         raise TurbineInterfaceEx(
    #             code=0,
    #             msg="Error getting session staus. ",
    #             e=e,
    #             tb=traceback.format_exc(),
    #         )

    def createSession(self):
        """
        Create a new turbine session ID
        """
        try:
            return _tsess.create_session(self.turbineConfigParse())
        except Exception as e:
            _log.exception("Error creating session")
            raise TurbineInterfaceEx(
                code=0,
                msg="Error creating Turbine session ",
                e=e,
                tb=traceback.format_exc(),
            )

    def createJobsInSession(self, sid, inputData):
        """
        Create jobs on turbine.
        """
        try:
            return json.loads(
                _tsess.create_jobs(self.turbineConfigParse(), sid, inputData)
            )
        except Exception as e:
            _log.exception("Error creating jobs in session")
            raise TurbineInterfaceEx(
                code=0,
                msg="Error creating Turbine jobs. Session id: {0}".format(sid),
                e=e,
                tb=traceback.format_exc(),
            )

    def startSession(self, sid):
        try:
            output = _tsess.start_jobs(self.turbineConfigParse(), sid)
            return json.loads(output)
        except Exception as e:
            _log.exception("Error starting session")
            raise TurbineInterfaceEx(
                code=0,
                msg="".join(["Error starting session. ", " Session id: ", sid]),
                e=e,
                tb=traceback.format_exc(),
            )

    def sessionExists(self, sid):
        """
        Determine if a session id exists on the Turbine gateway
        """
        l = self.getSessionList()
        return sid in l

    def killSession(self, sid):
        """
        Terminate or cancel all jobs in a particular session.
        This is useful if you want to kill a whole set of
        simulations
        """
        if sid == "" or not sid:
            return
        try:
            _tsess.kill_jobs(self.turbineConfigParse(), sid)
        except Exception as e:
            _log.exception("Error killing session")
            raise TurbineInterfaceEx(
                code=0,
                msg="".join(["Failed to kill session id: ", sid]),
                e=e,
                tb=traceback.format_exc(),
            )

    def getCompletedJobGen(self, sid):
        """
        Get a generator that returns jobs that have completed since
        last call.
        """
        return "00000000-0000-0000-0000-000000000000"

    def getCompletedJobPage(self, sid, gen):
        """
        Make and return a page with finished jobs since last call
        """
        cp = self.turbineConfigParse()
        kw = dict()
        url, auth, params = read_configuration(cp, _tsess.SECTION, **kw)
        try:
            _log.debug("Getting results post url: {}".format(url))
            page = turbine_session_result_script.post_session_result(
                url, auth, sid, gen
            )
        except HTTPStatusCode as e:
            if e.code == 404:
                return -1  # no more jobs to get
            elif e.code == 400:
                # Jobs but they are paused or otherwise in a state that
                # indicates they will not be running.
                _log.debug("400 getting result page.")
                return -2
            else:
                _log.exception("Failed to get completed job page")
                raise TurbineInterfaceEx(
                    code=0,
                    msg="Failed to get job page: {}".format(url),
                    e=e,
                    tb=traceback.format_exc(),
                )
        except urllib.request.URLError as e:
            raise TurbineInterfaceEx(
                code=0,
                msg="".join(["URLError Failed to get completed job page: ", url]),
                e=e,
                tb=traceback.format_exc(),
            )
        except Exception as e:
            raise TurbineInterfaceEx(
                code=0,
                msg="".join(["Exception Failed to get completed job page: ", url]),
                e=e,
                tb=traceback.format_exc(),
            )
        return int(page)

    def getCompletedJobs(self, sid, gen, page, maxJobs=2000):
        """
        Make and return a page with finished jobs since last call
        """
        kw = dict()
        if maxJobs > 0:
            kw["rpp"] = maxJobs
        cp = self.turbineConfigParse()
        url, auth, params = read_configuration(cp, _tsess.SECTION, **kw)
        result_url = "%s%s/result/%s/%s" % (url, str(sid), str(gen), str(page))
        _log.debug("GET Session Results from URL: {0}".format(result_url))
        try:
            jobs = get_page_by_url(result_url, auth, **params)
        except Exception as e:
            _log.exception("Failed to get jobs from: {}".format(result_url))
            raise TurbineInterfaceEx(
                code=0,
                msg="Failed to get jobs from: {}".format(result_url),
                e=e,
                tb=traceback.format_exc(),
            )
        return json.loads(jobs)

    def getJobStatus(self, jobID, verbose=False, suppressLog=False):
        """
        Get the status of the job given by jobID
        """
        if verbose:
            args = ["--verbose", "-j", str(jobID), self.getFile()]
        else:
            args = ["-j", str(jobID), self.getFile()]
        try:
            return _tjob.main(args, None)
        except Exception as e:
            if suppressLog:
                _log.exception("Error job status")
            raise TurbineInterfaceEx(
                code=0,
                msg="Failed to get job status, job id: {}".format(jobID),
                e=e,
                tb=traceback.format_exc(),
            )

    def simResourceList(self, sim):
        """Get a list of resources for a simualtion"""
        kw = {}
        cp = self.turbineConfigParse()
        url, auth, params = read_configuration(cp, _tsim.SECTION, **kw)
        result_url = "/".join([url, sim, "input"])
        _log.debug("GET Simulation Inputs from URL: {0}".format(result_url))
        try:
            r = get_page_by_url(result_url, auth, **params)
            r = json.loads(r)
        except Exception as e:
            _log.exception("Error getting simulation resources")
            raise TurbineInterfaceEx(
                code=0,
                msg="Failed to get simulation resources",
                e=e,
                tb=traceback.format_exc(),
            )
        return r

    def killJob(self, jobID, state=None):
        """
        Kill a job on Turbine, allow you to pass in state of job
        just in case you just checked the job status, it would be
        a waste to check it again right away
        """
        if not state:
            res = self.getJobStatus(jobID)
            state = res["State"]
        kw = dict()
        cp = self.turbineConfigParse()
        url, auth, params = read_configuration(cp, _tjob.SECTION, **kw)
        try:
            success = _tjob.post_job_terminate(url, auth, jobID)
            _log.info("Terminating Job {}: {}".format(jobID, success))
        except Exception as e:
            _log.exception("Error terminating job: {} state: {}".format(jobID, state))
            raise TurbineInterfaceEx(
                code=0,
                msg="Error terminating job: {} state: {}".format(jobID, state),
                e=e,
                tb=traceback.format_exc(),
            )

    def monitorJob(
        self,
        jobID,
        maxWaitTime=72000.0,
        maxRunTime=600.0,
        minCheckInt=5.0,
        maxCheckInt=None,
        stopFlag=None,
        nodeName=None,
        simName=None,
        allowWarnings=True,
        app=None,
        checkConsumer=True,
    ):
        """
        This function monitors a job submitted to Turbine and
        returns the result when the job is finished.  If a job takes
        too long it is terminated and a simulation error is returned.
        The time between checking the status is a random number
        between the min and max check interval, this is just to
        stagger the the status checks if there are a
        lot of jobs started by different threads at the same time.
        ---Arguments---
        jobID: tubine job id to monitor
        maxWaitTime: maximum amount of time to wait for job
                     results after monitoring starts in seconds
        maxRunTime: maximum amount of time to wait after a job
                    starts running in seconds
        minCheckInt: The minimum amount of time to wait between
                     checking a jobs status in seconds
        maxCheckInt: The maximum amount of time to wait between
                     checking a jobs status in seconds
        sotpFlag: a flag that when set means to stop monitoring and
                  terminate the job
        """
        # if exception is thrown I'll still stick
        # the results here if possible still may be useful
        res = None
        self.res = None
        #
        if maxCheckInt == None:
            checkInt = minCheckInt
        elif maxCheckInt - minCheckInt < 0.1:
            checkInt = minCheckInt
        else:
            checkInt = random.uniform(minCheckInt, maxCheckInt)
        # Set start times
        start = time.process_time()  # Time monitoring started
        runStart = None  # Time job started running on Turbine
        setupStart = None
        timeout = False
        failure = False
        success = False
        comProb = False
        res = None
        state = "submit"  # initial state of the job
        failedStates = ["error", "expired", "cancel", "terminate"]
        succesStates = ["success", "warning"]
        while True:  # start status checking loop
            # wait checkInt seconds wait before checking first time,
            # probably started the job, and it won't finish instantly
            time.sleep(checkInt)
            # Check that consumer is still running, had trouble with it
            # stopping for unknwn reasons, so I'll keep an eye on it.
            if checkConsumer:
                proc = self.checkConsumer(nodeName)
                if proc == None:
                    _log.error("Apparently the consumer died, job failed")
                    try:
                        self.killJob(jobID, state)
                    except Exception as e:
                        _log.exception(
                            "Job {} timeout failed to terminate".format(jobID)
                        )
                    raise TurbineInterfaceEx(code=356)
            # Now check job results form Turbine
            try:
                # Check status of job
                # -1 is not done
                # 0 is okay,
                # 2 warning,
                # anything else is an error
                res = self.getJobStatus(jobID, verbose=False)
                state = res.get("State", None)
                if (
                    not allowWarnings
                    and state == "success"
                    and res.get("Status", 1) == 2
                ):
                    state = "error"
                failure = state in failedStates
                success = state in succesStates
                # Check for the run start time instead of the state just
                # in case job started and completed between checks
                if not setupStart and state == "setup":
                    setupStart = time.process_time()
                if not runStart and res.get("Running", False):
                    runStart = time.process_time()
                    _log.info("Job " + str(jobID) + " Started Running")
            except TurbineInterfaceEx as e:
                # sometimes there is a temporary network disruption just
                # let the timeout handle this could be another error too
                if e.code not in self.retryErrors + [12]:
                    failure = True
                    comProb = True
                    _log.exception("Job {} failed".format(jobID))
                elif e.code == 12:
                    # this is a 404 error there is a good chance that
                    # I'm checking the job status too fast and the job
                    # page has not bee created yet
                    if time.process_time() - start < 20:
                        # started less than 20 sec ago give it some time
                        _log.exception(
                            "Job {} status check failed retrying".format(jobID)
                        )
                    else:
                        # started more than 20 seconds ago
                        # probably something wrong job failed
                        failure = True
                        comProb = True
                        _log.exception("Failed Job: {}".format(jobID))
                else:
                    # If error was in list of errors that could be
                    # temporary, will keep trying.
                    _log.debug(
                        "Job "
                        + str(jobID)
                        + " failed to check status will retry, Ex: "
                        + str(e)
                    )
            except Exception as e:
                # if it is some other exception give up and log it
                failure = True
                comProb = True
                _log.info(
                    "Job "
                    + str(jobID)
                    + " failed, Exception: "
                    + str(e)
                    + "\n "
                    + traceback.format_exc()
                )
            # Have the job status, figure out what to do next
            if success:
                # Return the job results if success
                self.res = res
                return res
            elif failure:
                # get results again with more detailed messages that
                # may help show why the job failed.
                try:
                    res = self.getJobStatus(jobID, verbose=True)
                    self.res = res
                except:
                    pass
                if comProb:
                    raise TurbineInterfaceEx(
                        code=354, msg="".join(["Results: ", str(res)])
                    )
                else:
                    raise TurbineInterfaceEx(
                        code=350, msg="".join(["Results: ", str(res)])
                    )
            elif time.process_time() - start > maxWaitTime:
                # Jobs not done but I'm not waiting any more (timeout)
                try:
                    self.killJob(jobID, state)
                except Exception:
                    _log.exception(
                        "Job " + str(jobID) + " Wait time-out, failed to terminate"
                        " job on Turbine\n"
                    )
                finally:
                    raise TurbineInterfaceEx(
                        code=353, msg="".join(["Results: ", str(res)])
                    )
            elif runStart and time.process_time() - runStart > maxRunTime:
                try:
                    self.killJob(jobID, state)
                except Exception:
                    _log.exception(
                        "Job " + str(jobID) + " Run time-out, failed to terminate"
                        " job on Turbine\n"
                    )
                finally:
                    raise TurbineInterfaceEx(
                        code=352, msg="".join(["Results: ", str(res)])
                    )
            elif stopFlag != None and stopFlag.isSet():
                try:
                    self.killJob(jobID, state)
                except Exception:
                    _log.exception(
                        "Job " + str(jobID) + " Graph thread terminate, failed to"
                        " terminate job on Turbine\n"
                    )
                finally:
                    raise TurbineInterfaceEx(code=355)

    def getAppByExtension(self, modelFile):
        junk, modelExt = os.path.splitext(modelFile)  # get model ext
        app = self.appExtensions.get(modelExt, None)
        if not app:  # unknown extension type
            raise TurbineInterfaceEx(code=306, msg="Extension: " + modelExt)
        else:
            resourceType = self.resourceNames[app]
        return app, resourceType

    def getModelFileFromSinterConfigDict(self, sinterConfData):
        if sinterConfData.get("model", None):
            modelFile = sinterConfData.get("model", None)
            # will figure Turbine resource type by modelFile extension
        elif sinterConfData.get("aspenfile", None):
            modelFile = sinterConfData.get("aspenfile", None)
        elif sinterConfData.get("spreadsheet", None):
            modelFile = sinterConfData.get("spreadsheet", None)
        elif sinterConfData.get("Type", None) == "FOQUS_Session":
            resourceType = None
            app = "foqus"
            modelFile = (None, app)
        # WHY the undefined-variable errors reported by pylint look like true positive
        # this suggests that the code branches where the underfined variables are used are not run
        else:
            # if no model file found it is probably not a sinter
            # configuration file or FOQUS is out of sync with
            # simSinter development
            raise TurbineInterfaceEx(
                # TODO pylint: disable=undefined-variable
                code=304,
                msg="Path: " + sinterConfigPath,
            )
        if isinstance(modelFile, dict):
            modelFile = modelFile.get("file", None)
            if modelFile is None:
                # No model file found
                raise TurbineInterfaceEx(
                    # TODO pylint: disable=undefined-variable
                    code=304,
                    msg="Path: " + sinterConfigPath,
                )
        return modelFile

    def sinterConfigGetResource(self, sinterConfigPath, checkExists=True):
        """
        Get the simulation file and resource type by reading sinter
        config file.
        """
        other = None
        if not os.path.isfile(sinterConfigPath):
            raise TurbineInterfaceEx(code=302, msg="Path: " + sinterConfigPath)
        with open(sinterConfigPath, "r") as f:
            try:
                sinterConfData = json.load(f)
            except Exception as e:
                raise TurbineInterfaceEx(
                    code=303, msg="Path: {0}, msg: {1}".format(sinterConfigPath, e)
                )
        # Look through the list of known model file types and try to
        # pick the model file path out of the sinter configuration file
        modelFile = self.getModelFileFromSinterConfigDict(sinterConfData)
        if isinstance(modelFile, tuple):
            app = modelFile[1]
            modelFile = None
            resourceType = None
        # Get the full path of the model file and make sure it exists
        # assume model is in the same directory as sinter config
        if modelFile is not None:
            dir = os.path.dirname(os.path.abspath(sinterConfigPath))
            modelFile = os.path.join(dir, modelFile)
            if not os.path.isfile(modelFile) and checkExists:
                raise TurbineInterfaceEx(code=305, msg="Path: " + sinterConfigPath)
            # Check the model file extension to determine the application
            # type and make sure it matches the resource type in the sinter
            # configuration file.
            app, resourceType = self.getAppByExtension(modelFile)
            # Now get anyother extra input files
            other = sinterConfData.get("input-files", [])
        return (modelFile, resourceType, app, other)

    def updateResource(self, simName, resourceName, fileName):
        """
        Update a resource on turbine:
        args:
            simName: Name of simulation to update resource of
            resourceName: the resource to update
            fileName: the file to update resource with
        """
        simList = self.getSimulationList()
        if not simName in simList:
            raise TurbineInterfaceEx(code=310, msg=simName)
        try:
            _tsim.main_update(["-r", resourceName, simName, fileName, self.getFile()])
        except Exception as e:
            _log.exception("Error updating sim: {}, {}".format(simName, resourceName))
            raise TurbineInterfaceEx(
                code=0,
                msg="Error updating sim: {}, {}".format(simName, resourceName),
                e=e,
                tb=traceback.format_exc(),
            )

    def uploadSimulation(
        self, simName, sinterConfigPath, update=True, guid=None, otherResources=[]
    ):
        """
        This function uploads a new simulation to Turbine.  The name
        of the simulation files are set in the sinter configuration
        file.  It is also assumed that the simulation files are in
        the same directory as the sinter configuration file.  It
        update == True files for an existing model will be updated.
        If update is false and model exist return a model already
        exists error.

        guid -- optional value to set Simulation.Id
        """
        # Check that the simulation name only contains:
        # letters, numbers, and _
        name = simName
        if not re.match("^([A-Za-z0-9_]+$)", name):
            raise TurbineInterfaceEx(code=301, msg="Simulation name: " + name)
        # Get model info from sinter config
        modelFile, resourceType, app, oth = self.sinterConfigGetResource(
            sinterConfigPath
        )
        _log.debug(
            "Uploading simulation to turbine.\n"
            "modelFile: {0}\n"
            "resourceType: {1}\n"
            "app: {2}\n"
            "oth: {3}\n".format(modelFile, resourceType, app, oth)
        )
        # Check that application is available on Turbine
        appList = self.getApplicationList()
        if app not in appList:
            raise TurbineInterfaceEx(
                code=308,
                msg="".join(
                    ["Application: ", app, " Available applications: ", str(appList)]
                ),
            )
        # Get a list of models already on turbine and check if the
        # specified model name matches one already on turbine.  Return
        # if model exists and update is false
        simList = self.getSimulationList()
        simListLower = []
        for s in simList:
            simListLower.append(s.lower())
        exists = name.lower() in simListLower
        if exists and not update:
            raise TurbineInterfaceEx(code=309, msg="Simulation: " + name)
            return [
                9,
                "The simulation "
                + name
                + " already exists and the update flag is not set to true",
            ]
        # Create a new model if needed
        elif not exists:
            args = [name, app, self.getFile()]
            if guid:
                args = ["-s", name, guid, app, self.getFile()]
            try:
                _tsim.main_create(args)
            except Exception as e:
                raise TurbineInterfaceEx(
                    code=0,
                    msg="Could not create new simulation on Turbine ",
                    e=e,
                    tb=traceback.format_exc(),
                )
        # Upload the sinter configuration file
        args = ["-r", "configuration", name, sinterConfigPath, self.getFile()]
        try:
            _tsim.main_update(args)
        except Exception as e:
            raise TurbineInterfaceEx(
                code=0,
                msg="Could not upload sinter configuration file",
                e=e,
                tb=traceback.format_exc(),
            )
        # upload model file
        try:
            if modelFile != None:
                if resourceType in ["aspenfile", "plugin"]:
                    resourceType = os.path.split(modelFile)[-1]
                    _log.debug("Upload resourceType=%s", resourceType)
                _tsim.main_update(["-r", resourceType, name, modelFile, self.getFile()])
        except Exception as e:
            raise TurbineInterfaceEx(
                code=0,
                msg="Could not upload model file",
                e=e,
                tb=traceback.format_exc(),
            )
        for r in otherResources:
            try:
                _tsim.main_update(["-r", r[0], name, r[1], self.getFile()])
            except Exception as e:
                raise TurbineInterfaceEx(
                    code=0,
                    msg="Could not upload resource: {0} {1}".format(r[0], r[1]),
                    e=e,
                    tb=traceback.format_exc(),
                )
        # if you made it this far everything worked fine
        return

    def testConfig(self, reloadTurbine=True, writeConfig=True):
        """
        This tests that the turbine configuration works.  If it
        doesn't work a list of errors is returned, which will
        hopefully allow you to quickly track down the problem.
        """
        if reloadTurbine:
            self.reloadTurbine()
        cp = self.turbineConfigParse()
        username = cp.get("Authentication", "username", raw=True)
        password = cp.get("Authentication", "password", raw=True)
        errList = []
        # Check that user name and password are filled in
        # for TurbineLite I Just use None, None you don't have to enter
        # anything, so for TurbineLite this should pass
        if not isinstance(username, str) or username == "":
            if not self.address.startswith("http://"):
                errList.append("empty username")
        if not isinstance(password, str) or password == "":
            if not self.address.startswith("http://"):
                errList.append("empty password")
        n = None
        # Check URL Formatting to make sure it is as expected
        sections = ["Application", "Session", "Job", "Simulation", "Consumer"]
        for section in sections:
            url = cp.get(section, "url")
            scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(url)
            if scheme != "https" and scheme != "http":
                errList.append("section %s URL should be https or http" % section)
            if params != "":
                errList.append("expecting empty params in url %s" % url)
            if query != "":
                errList.append("expecting empty query in url %s" % url)
            if fragment != "":
                errList.append("expecting empty fragment in url %s" % url)
            if n == None:
                n = netloc
            if n != netloc:
                errList.append("expecting same network location for all URLs")
        # If the user name, password, and URLs are entered correctly,
        # test the connection.  If the connection fails it could be for
        # a number of reasons to we'll just report the exception and
        # hopefully that gives enough info to get a good idea
        if len(errList) == 0:
            if writeConfig:
                self.writeConfig()
            try:
                # test by requesting list of applications
                self.getApplicationList()
            except TurbineInterfaceEx as e:
                errList.append(str(e))
            except Exception as e:
                errList.append(str(e))
            except:
                errList.append("Unknown error in Turbine configuration")
        # Add test results to the log
        if errList:
            _log.debug("Configuration has errors\n{}".format(str(errList)))
        else:
            _log.debug("Configuration seems okay")
        return errList
