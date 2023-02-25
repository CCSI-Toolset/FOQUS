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
"""session.py

* Some functions to setup FOQUS environment
* Class to store FOQUS session information
* Class for genral FOQUS settings

John Eslick, Carnegie Mellon University, 2014
"""
import json
import os
import shutil
import collections
import sys
import logging
import uuid
from foqus_lib.framework.graph.graph import *
from foqus_lib.framework.graph.node import nodeModelTypes
import foqus_lib.framework.optimizer.problem as oprob
from foqus_lib.framework.sim.turbineConfiguration import *
from foqus_lib.framework.plugins import pluginSearch
from foqus_lib.framework.ml_ai_models import mlaiSearch
from foqus_lib.framework.surrogate import surrogate
from foqus_lib.framework.optimizer import problem
from foqus_lib.framework.pymodel import pymodel
from foqus_lib.framework.uq.Model import *
from foqus_lib.framework.uq.SampleData import *
from foqus_lib.framework.uq.LocalExecutionModule import *
from foqus_lib.framework.sampleResults.results import Results

# these are just imported so py2exe will pick them up since they
# are used only in plugins
from foqus_lib.framework.optimizer.optimization import optimization as junk
from foqus_lib.framework.surrogate.surrogate import surrogate as junk2

# Before the session class there are a few functions to help set up the
# FOQUS environment.

DEFAULT_FOQUS_CLOUD_URL = (
    "https://b7x9ucxadg.execute-api.us-east-1.amazonaws.com/development/"
)
DEFAULT_FOQUS_CLOUD_WEBSOCKET = (
    "wss://du6p1udafi.execute-api.us-east-1.amazonaws.com/Development"
)


def getTimeStamp():
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def whereInstalled():
    """
    This function returns the path where the FOQUS framework is
    installed this can be used to copy data files from the install
    location to somewhere useful.
    """
    thisFilePath = os.path.abspath(__file__)  # path to this file
    # take off file name, and the session subdirectory before return
    return os.path.dirname(os.path.dirname(thisFilePath))


def exePath():
    """
    This returns the path where foqus.py is, in windows installer
    this is the directory where the exe files are.
    """
    return os.path.dirname(os.path.dirname(whereInstalled()))


def createDir(reldir):
    """
    Create a new directory in the working director only if it
    doesn't exist.
    reldir: path to new directory relative to the working directory
    """
    wdir = os.path.abspath(os.getcwd())
    dir = os.path.join(wdir, reldir)
    if not os.path.exists(dir):
        os.makedirs(dir)


def copyFiles(files, fromDir, toDir, overWrite=False):
    """
    Copy a list of files from a directory to another only if the
    files exists in the the first directory.  Will only overwrite
    files if overwrite is true
    files: a list of file names
    fromDir: the directory to copy files from (abs or relative)
    toDir:   the directory to copy files to (abs or relative)
    overWrite: if False don't overwrite existing files
    """
    for name in files:
        fullNameFrom = os.path.join(fromDir, name)
        fullNameTo = os.path.join(toDir, name)
        if (
            os.path.isfile(fullNameFrom)
            and not os.path.isfile(fullNameTo)
            and not overWrite
        ):
            shutil.copy(fullNameFrom, toDir)
        elif os.path.isfile(fullNameFrom) and overWrite:
            shutil.copy(fullNameFrom, toDir)


def makeWorkingDirStruct(wdir=None):
    """
    This function sets up a working directory with sub directories
    for different things.

    wdir: new working directory (if none use current directory)
    """
    try:
        if wdir != None:
            os.chdir(wdir)
        createDir("logs")
        createDir("gams")
        createDir("temp")
        createDir("test")
        createDir("user_plugins")
        createDir("user_ml_ai_models")
        createDir("ouu")
        open("user_plugins/__init__.py", "a").close()
        open("user_ml_ai_models/__init__.py", "a").close()
    except:
        logging.getLogger("foqus." + __name__).exception(
            "Error creating working directory structure"
        )
        return False
    return True


def makeWorkingDirFiles():
    """
    This functions copies needed files to the working directory.
    """
    wdir = os.path.abspath(os.getcwd())
    try:
        tc = TurbineConfiguration("turbine.cfg")
        tc.writeConfig(overwrite=False)
    except:
        logging.getLogger("foqus." + __name__).exception(
            "Couldn't write default turbine.cfg"
        )
    try:
        tc = TurbineConfiguration("turbine_aws.cfg")
        tc.address = DEFAULT_FOQUS_CLOUD_URL
        tc.notification = DEFAULT_FOQUS_CLOUD_WEBSOCKET
        tc.turbVer = "Remote"
        tc.writeConfig(overwrite=False)
    except:
        logging.getLogger("foqus." + __name__).exception(
            "Couldn't write default turbine_aws.cfg"
        )

    try:
        dir = os.path.join(whereInstalled(), "gams")
        dir2 = os.path.join(wdir, "gams")
        copyFiles(os.listdir(dir), dir, dir2, overWrite=True)
    except Exception as e:
        logging.getLogger("foqus." + __name__).exception(
            "Not able to copy GAMS files.  "
            + "This is only a problem with heat integration. From: "
            + dir
            + " To: "
            + dir2
            + " Exception: "
            + str(e)
        )


class session:
    """
    This class stores information for a session.  Includes the
    flowsheet and optimization parameters. It also provides methods
    to load and save information to a file.
    """

    def __init__(self, useCurrentWorkingDir=False):
        """
        Initialize the session by calling the new function.
        """
        self.flowsheet = None
        # Get to the general foqus settings through the FOQUS session,
        # but the setting are stored in a seperate file not in the
        # FOQUS session file.  Its just here to make things easier,
        # since general FOQUS settings where a late addition.
        self.foqusSettings = generalSettings()
        self.foqusSettings.load(useCurrentWorkingDir)
        self.foqusSettings.new_working_dir = self.foqusSettings.working_dir
        self.settingUseCWD = useCurrentWorkingDir
        # Get the log file and location for log file viewer
        self.currentLog = os.path.join("logs", self.foqusSettings.foqusLogFile)
        try:
            with open(self.currentLog, "r") as f:
                f.seek(0, 2)
                self.logSeek = f.tell()
            self.currentLog = os.path.abspath(self.currentLog)
        except:
            logging.getLogger("foqus." + __name__).exception(
                "Session init, error opening log file"
            )
            self.currentLog = None
            self.logSeek = 0
        logging.getLogger("foqus." + __name__).debug(
            "Initializing session, Log file: {0}, Position: {1}".format(
                self.currentLog, self.logSeek
            )
        )
        # Set up a blank FOQUS session
        self.loadPlugins()
        self.loadMLAIModels()
        self.turbineChkFreq = 10  # frequency to check remote Turbine for
        # results
        self.resubMax = 0
        self.new()

    def runDebugCode(self, pythonCode, MainWin=None):
        res = ""
        exec(pythonCode)
        return res

    def produceTurbineFOQUSTestInput(self, filename="test_input.json"):
        out = [
            {
                "Simulation": "FoqusTest",
                "Input": [self.flowsheet.saveValues()["input"]],
                "Reset": False,
            }
        ]
        with open(filename, "w") as f:
            json.dump(out, f)

    def setRemoteTurbineFreq(self, t):
        self.turbineChkFreq = t
        self.flowsheet.turbchkfreq = t

    def setRemoteReSub(self, t):
        self.resubMax = t
        self.flowsheet.resubMax = t

    def new(self, stopConsumers=True):
        """
        Create a new clean session object
        """
        tc = None
        if stopConsumers:
            try:
                self.flowsheet.turbConfig.stopAllConsumers()
            except:
                pass
        else:
            # if not stoppoing consumers then reuse them
            tc = self.flowsheet.turbConfig
        self.name = ""
        self.originalFileName = ""
        self.uid = uuid.uuid4().hex
        self.creationTime = ""
        self.changeLog = {}
        self.parents = []
        self.version = "00.00"
        self.confidence = "experimental"
        try:
            self.flowsheet.turbConfig.closeTurbineLiteDB()
        except:
            pass
        self.flowsheet = Graph()  # meta-flowsheet linking sims
        if tc is not None:
            # keeping the consumers around and reusing them
            # for the simulation I'm opening.
            self.flowsheet.turbConfig = tc
        self.flowsheet.turbConfig.dat = self
        self.flowsheet.turbConfig.updateSettings()
        self.flowsheet.turbchkfreq = self.turbineChkFreq
        self.flowsheet.resubMax = self.resubMax
        self.description = "None"  # description of the session
        self.currentFile = ""  # path for current session file
        self.date = ""  # date that a session file was saved
        self.optProblem = oprob.problem()  # optimization problems
        self.optProblem.dat = self
        self.surrogateProblem = {}  # saved dict of surrogate setup
        self.surrogateCurrent = None
        self.uqSimList = []  # list of UQ simulation ensembles
        self.uqFilterResultsList = []  # list of UQ filter results
        self.sdoeSimList = []  # list of SDOE simulation ensembles
        self.odoeCandList = []  # list of ODOE candidate sets
        self.odoeEvalList = []  # list of ODOE evaluation sets
        self.sdoeFilterResultsList = []  # list of SDOE filter results
        self.ID = time.strftime("Session_%y%m%d%H%M%S")  # session id
        self.archiveFolder = os.path.join(os.getcwd(), "%s_files" % self.ID)
        self.newArchiveItemsSinceLastSave = []
        # add the pymodel plugin and ml_ai_model lists to the flowsheet so
        # the node make instances of pymodels to run.  the nodes don't have
        # access to the session object
        self.flowsheet.pymodels = self.pymodels
        self.flowsheet.pymodels_ml_ai = self.pymodels_ml_ai

    def loadSettings(self):
        self.foqusSettings.load(self.settingUseCWD)
        self.flowsheet.turbConfig.updateSettings()
        self.setRemoteTurbineFreq(self.foqusSettings.turbineRemoteCheckFreq)
        self.setRemoteReSub(self.foqusSettings.turbineRemoteReSub)

    def saveSettings(self):
        self.foqusSettings.save()

    def reloadPlugins(self):
        self.surrogateMethods.importPlugins()
        self.optSolvers.importPlugins()
        self.pymodels.importPlugins()

    def loadPlugins(self):
        """
        Search for plugins
        """
        prefix = "#s?FOQUS_"
        self.surrogateMethods = pluginSearch.plugins(
            # \s? matches 0 or 1 whitespace characters
            idString="#\s?FOQUS_SURROGATE_PLUGIN",
            pathList=[
                os.path.join(os.getcwd(), "user_plugins"),
                os.path.dirname(surrogate.__file__),
            ],
        )
        self.optSolvers = pluginSearch.plugins(
            idString="#\s?FOQUS_OPT_PLUGIN",
            pathList=[
                os.path.join(os.getcwd(), "user_plugins"),
                os.path.dirname(problem.__file__),
            ],
        )
        self.pymodels = pluginSearch.plugins(
            idString="#\s?FOQUS_PYMODEL_PLUGIN",
            pathList=[
                os.path.join(os.getcwd(), "user_plugins"),
                os.path.dirname(pymodel.__file__),
            ],
        )
        try:
            self.flowsheet.pymodels = self.pymodels
        except:
            pass

    def reloadMLAIModels(self):
        self.pymodels_ml_ai.getMLAIList()

    def loadMLAIModels(self):
        """
        Search for ml_ai_models
        """
        self.pymodels_ml_ai = mlaiSearch.ml_ai_models(
            pathList=[
                os.path.join(os.getcwd(), "user_ml_ai_models"),
                os.path.dirname(surrogate.__file__),
            ]
        )
        try:
            self.flowsheet.pymodels_ml_ai = self.pymodels_ml_ai
        except:
            pass

    def saveFlowsheetValues(self, filename, indent=0):
        """
        Save only the values of flowsheet varaibles to a json file
        This is mostly for running flowsheets from the command line,
        where you already loaded a session, and you don't need all
        the other junk in a sesssion file.  The values file is much
        smaller.
        """
        with open(filename, "w") as f:
            if indent <= 0:
                json.dump(self.flowsheet.saveValues(), f, separators=(",", ":"))
            else:
                json.dump(self.flowsheet.saveValues(), f, indent=indent)

    def loadFlowsheetValues(self, filename):
        """
        Load only the values of flowsheet varaibles to a json file
        This is mostly for running flowsheets from the command line,
        where you already loaded a session, and you don't need all
        the other junk in a sesssion file.  The values file is much
        smaller.
        """
        with open(filename, "r") as f:
            sd = json.load(f)
        self.flowsheet.loadValues(sd)

    def save(
        self,
        filename=None,
        updateCurrentFile=True,
        changeLogMsg="",
        bkp=True,
        indent=0,
        keepData=True,
    ):
        """
        Save an optimization framework session to a file
        filename: path to a session file to save
            if filename == None no file is saved but the
            dictionary that was created is still returned
        updateCurrentFile == True: changes the current FOQUS session
            file to filename (only if filenale != None)
        changeLogMsg: A change log entry
        confidence: Confidence in the qulity of the session
        bkp: save two files so you have a backup to keep tarck of
            all saved versions.
        """
        if bkp == "Settings":
            if self.foqusSettings.backupSession:
                bkp = True
            else:
                bkp = False
        if indent == "Settings":
            if self.foqusSettings.compactSession:
                indent = 0
            else:
                indent = 2
        # Create a new ID
        self.uid = uuid.uuid4().hex
        # Time code for save
        self.date = getTimeStamp()
        if self.creationTime == "":
            self.creationTime = self.date
            self.originalFileName = ".".join([self.name, "json"])
            self.changeLog = {}
        self.modTime = self.date
        self.changeLog[self.date] = [self.version, self.uid, self.name, changeLogMsg]
        metaData = {
            "ID": self.uid,
            "CreationTime": self.creationTime,
            "ModificationTime": self.modTime,
            "ChangeLog": self.changeLog,
            "DisplayName": self.name,
            "OriginalFilename": self.originalFileName,
            "Application": "foqus",
            "Description": self.description,
            "MIMEType": "application/ccsi+foqus",
            "Confidence": self.confidence,
            "Parents": self.parents,
            "Role": "Input",
            "UpdateMetadata": True,
            "Version": self.version,
        }
        sd = dict()
        sd["CCSIFileMetaData"] = metaData
        sd["Type"] = "FOQUS_Session"
        sd["ID"] = self.ID
        sd["flowsheet"] = self.flowsheet.saveDict(keepData)
        sd["optProblem"] = self.optProblem.saveDict()
        sd["surrogateProblem"] = self.surrogateProblem
        sd["surrogateCurrent"] = self.surrogateCurrent
        # Save UQ sim list
        sd["uqSimList"] = []
        for sim in self.uqSimList:
            sd["uqSimList"].append(sim.saveDict())
        sd["uqFilterResultsList"] = []
        for filter in self.uqFilterResultsList:
            sd["uqFilterResultsList"].append(filter.saveDict())
        # Save SDOE sim list
        sd["sdoeSimList"] = []
        for sim in self.sdoeSimList:
            sd["sdoeSimList"].append(sim.saveDict())
        sd["sdoeFilterResultsList"] = []
        for filter in self.sdoeFilterResultsList:
            sd["sdoeFilterResultsList"].append(filter.saveDict())
        # Save ODOE cand list
        sd["odoeCandList"] = []
        for sim in self.odoeCandList:
            sd["odoeCandList"].append(sim.saveDict())

        # Save ODOE eval list
        sd["odoeEvalList"] = []
        for sim in self.odoeEvalList:
            sd["odoeEvalList"].append(sim.saveDict())

        if filename:
            # write two copies of the file one is backup you can keep
            # forever, one is the specified file name with most recent
            if bkp:
                bkppath, bkpfilename = os.path.split(filename)
                bkpfilename = os.path.join(
                    bkppath, "{0}.{1}".format(self.name, self.uid)
                )
                with open(bkpfilename, "w") as f:
                    if indent <= 0:
                        json.dump(sd, f, separators=(",", ":"))
                    else:
                        json.dump(sd, f, indent=indent)
            # Write the session file
            with open(filename, "w") as f:
                if indent <= 0:
                    json.dump(sd, f, separators=(",", ":"))
                else:
                    json.dump(sd, f, indent=indent)
            # set the current file to one just saved
            if updateCurrentFile:
                self.currentFile = os.path.abspath(filename)
        # Clear new archive folders since last save
        # so they won't be deleted later
        self.newArchiveItemsSinceLastSave = []
        return sd

    def load(self, filename, stopConsumers=True):
        """
        Load a session file
        filename: path to a session file to load
        """
        with open(filename, "r") as f:
            sd = json.load(f, object_pairs_hook=collections.OrderedDict)
        self.loadDict(sd, filename, stopConsumers=stopConsumers)
        self.currentFile = os.path.abspath(filename)
        # UQ Archive Stuff
        fullFile = os.path.abspath(filename)
        pathName, baseName = os.path.split(fullFile)
        base, ext = os.path.splitext(baseName)
        self.ID = sd.get("ID", base + time.strftime("_%y%m%d%H%M%S"))
        dirname = os.path.dirname(os.path.abspath(filename))
        if os.access(dirname, os.W_OK):
            self.archiveFolder = os.path.join(dirname, "%s_files" % self.ID)
        else:
            self.archiveFolder = os.path.join(os.getcwd(), "%s_files" % self.ID)
        self.newArchiveItemsSinceLastSave = []

    def loadDict(self, sd, filename, stopConsumers=True):
        """
        Load a session from a string
        """
        # Clear session information
        self.new(stopConsumers=stopConsumers)
        # Read metaData information
        metaData = sd.get("CCSIFileMetaData", None)
        if metaData:  # Read information from meta data if it exists
            self.description = metaData.get("Description", "None")
            self.creationTime = metaData.get("CreationTime", "")
            self.changeLog = metaData.get("ChangeLog", {})
            self.parents = metaData.get("Parents", [])
            self.originalFileName = metaData.get("OriginalFilename", "")
            self.date = metaData.get("ModificationTime", "")
            self.version = metaData.get("Version", "00.00")
            self.name = metaData.get("DisplayName", "")
            self.uid = metaData.get("ID", self.uid)
            self.confidence = metaData.get("Confidence", "experimental")
        else:  # Older session files read data from old locations
            self.description = sd.get("description", "None")
            self.date = sd.get("date", "")
        # Read flowsheet
        self.flowsheet.loadDict(sd["flowsheet"])
        # Read ID for UQ archives, should prob get rid of this and use
        # metadata ID
        fullFile = os.path.abspath(filename)
        pathName, baseName = os.path.split(fullFile)
        base, ext = os.path.splitext(baseName)
        self.ID = sd.get("ID", self.ID)
        self.archiveFolder = os.path.join(
            os.path.dirname(os.path.abspath(filename)), "%s_files" % self.ID
        )

        # Load the surrogate model settings
        self.surrogateProblem = sd.get("surrogateProblem", {})
        self.surrogateCurrent = sd.get("surrogateCurrent", None)
        # Load the optimization problem if exists
        self.optProblem = oprob.problem()
        self.optProblem.dat = self
        p = sd.get("optProblem", None)
        if p:
            self.optProblem.loadDict(p)
        # Load UQ Stuff
        self.uqSimList = []
        if "uqSimList" in sd:
            for simDict in sd["uqSimList"]:
                model = Model()
                model.loadDict(simDict["model"])
                sim = SampleData(model)
                sim.setSession(self)
                sim.loadDict(simDict)
                self.uqSimList.append(sim)
        self.uqFilterResultsList = []
        if "uqFilterResultsList" in sd:
            for filterDict in sd["uqFilterResultsList"]:
                filterResults = Results()
                filterResults.loadDict(filterDict)
                self.uqFilterResultsList.append(filterResults)
        # Load SDOE Stuff
        self.sdoeSimList = []
        if "sdoeSimList" in sd:
            for simDict in sd["sdoeSimList"]:
                model = Model()
                model.loadDict(simDict["model"])
                sim = SampleData(model)
                sim.setSession(self)
                sim.loadDict(simDict)
                self.sdoeSimList.append(sim)
        self.sdoeFilterResultsList = []
        if "sdoeFilterResultsList" in sd:
            for filterDict in sd["sdoeFilterResultsList"]:
                filterResults = Results()
                filterResults.loadDict(filterDict)
                self.sdoeFilterResultsList.append(filterResults)
        # Load ODOE Stuff
        self.odoeCandList = []
        if "odoeCandList" in sd:
            for simDict in sd["odoeCandList"]:
                model = Model()
                model.loadDict(simDict["model"])
                sim = SampleData(model)
                sim.setSession(self)
                sim.loadDict(simDict)
                self.odoeCandList.append(sim)

        self.odoeEvalList = []
        if "odoeEvalList" in sd:
            for simDict in sd["odoeEvalList"]:
                model = Model()
                model.loadDict(simDict["model"])
                sim = SampleData(model)
                sim.setSession(self)
                sim.loadDict(simDict)
                self.odoeEvalList.append(sim)

        self.currentFile = None

    def removeArchive(self):
        shutil.rmtree(self.archiveFolder)

    def moveArchive(self, destFolder):
        if os.path.exists(self.archiveFolder):
            shutil.copytree(self.archiveFolder, destFolder)
        self.archiveFolder = destFolder
        # Delete new stuff from old folder

    def archiveFile(self, fileName, folderStructure=None):
        if folderStructure is None:
            folderStructure = []
        fileName = os.path.abspath(fileName)
        if isinstance(folderStructure, str):
            dirs = folderStructure.split(os.sep)
            if len(dirs) == 1:
                folderStructure = [folderStructure]
            else:
                folderStructure = dirs

        destFolder = self.archiveFolder
        if not os.path.exists(destFolder):
            os.mkdir(destFolder)
            self.newArchiveItemsSinceLastSave.append(destFolder)
        for folder in folderStructure:
            destFolder = os.path.join(destFolder, folder)
            if not os.path.exists(destFolder):
                os.mkdir(destFolder)
                self.newArchiveItemsSinceLastSave.append(destFolder)
        self.newArchiveItemsSinceLastSave.append(
            os.path.join(destFolder, os.path.basename(fileName))
        )
        shutil.copy(fileName, destFolder)

    def restoreFromArchive(self, fileName, folderStructure=None):
        if folderStructure is None:
            folderStructure = []
        if isinstance(folderStructure, str):
            dirs = folderStructure.split(os.sep)
            if len(dirs) == 1:
                folderStructure = [folderStructure]
            else:
                folderStructure = dirs
        destFolder = self.archiveFolder
        for folder in folderStructure:
            destFolder = os.path.join(destFolder, folder)
        srcFile = os.path.join(destFolder, fileName)
        shutil.copy(srcFile, os.curdir)
        return os.path.join(os.curdir, fileName)

    def existsInArchive(self, fileName, folderStructure=None):
        if folderStructure is None:
            folderStructure = []
        if isinstance(folderStructure, str):
            dirs = folderStructure.split(os.sep)
            if len(dirs) == 1:
                folderStructure = [folderStructure]
            else:
                folderStructure = dirs
        destFolder = self.archiveFolder
        for folder in folderStructure:
            destFolder = os.path.join(destFolder, folder)
        srcFile = os.path.join(destFolder, fileName)
        return os.path.exists(srcFile)

    def removeArchiveFile(self, fileName, folderStructure=None):
        if folderStructure is None:
            folderStructure = []
        if isinstance(folderStructure, str):
            dirs = folderStructure.split(os.sep)
            if len(dirs) == 1:
                folderStructure = [folderStructure]
            else:
                folderStructure = dirs
        destFolder = self.archiveFolder
        for folder in folderStructure:
            destFolder = os.path.join(destFolder, folder)
        fileName = os.path.join(destFolder, fileName)
        if os.path.exists(fileName):
            os.remove(fileName)

    def removeArchiveFolder(self, folderStructure=None):
        if folderStructure is None:
            folderStructure = []
        if isinstance(folderStructure, str):
            dirs = folderStructure.split(os.sep)
            if len(dirs) == 1:
                folderStructure = [folderStructure]
            else:
                folderStructure = dirs
        destFolder = self.archiveFolder
        for folder in folderStructure:
            destFolder = os.path.join(destFolder, folder)
        if os.path.exists(destFolder):
            shutil.rmtree(destFolder)

    def removeNewArchiveItems(self):
        for item in self.newArchiveItemsSinceLastSave:
            if os.path.exists(item):
                if os.path.isdir(item):
                    shutil.rmtree(item)
                else:
                    os.remove(item)
        self.newArchiveItemsSinceLastSave = []


class generalSettings:
    """
    This class stores foqus general settings that are not
    specific to a particular session.

    There are two important settings file locations

    1) The main settings file provide a set of default settings
       when starting FOQUS.  This file is stored in
       %APPDATA%\.foqus.cfg on Windows or in $HOME/.foqus.cfg on
       other operating systems.

    2) The settings file in the working directory overrides the
       main settings file.  This is foqus.cfg in the working
       direcotry.  The option to override settings by storing a
       settings file in the working directory is mainly to allow
       multiple copies of FOQUS to run at the same time without
       haveing conficts if the user wants to change settings.

    The reason the main settings file exists is for starting FOQUS
    from the Windows start menu.  It provide the working directory
    to use.  If you want to run more than one copy of FOQUS at a
    time it is best to start addtional copies from the command line
    specifying the working directory as a command line option.
    """

    def __init__(self):
        self.numRecentFiles = 5
        self.working_dir_override = False
        self.working_dir = ""
        self.new_working_dir = ""
        self.simsinter_path = "C:/Program Files (x86)/CCSI/SimSinter"
        self.psuade_path = "C:/Program Files (x86)/psuade_project 1.7.5/bin/psuade.exe"
        self.turbConfig = "turbine.cfg"
        self.turbConfigCluster = "turbine_aws.cfg"
        self.alamo_path = ""
        self.foqusLogLevel = logging.DEBUG  # FOQUS log level
        self.turbLogLevel = logging.WARNING  # Turbine client log level
        self.foqusLogToConsole = True  # send FOQUS log to console?
        self.turbLogToConsole = True  # send turbine log to console?
        self.foqusLogToFile = True  # send FOQUS log to file?
        self.turbLogToFile = True  # send turbine log to file?
        self.foqusLogFile = "foqus.log"  # foqus log file
        self.turbineLogFile = "turbine.log"  # turbine client log file
        self.turbineRemoteCheckFreq = 10  # seconds between checking for
        # results on remote run
        self.turbineRemoteReSub = 0  # number of times to resubmit failed
        # jobs to Turbine when running remote
        self.aspenVersion = 2  # 0 = none, 1 = 7.3, 2 = 7.3.2 or higher
        self.turbLiteHome = "C:\\Program Files (x86)\\Turbine\\Lite"
        self.rScriptPath = "C:\\Program Files\\R\\R-3.1.2\\bin\\x64\\Rscript.exe"
        self.logFormat = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        self.logRotate = False
        self.maxLogSize = 5
        self.compactSession = True
        self.backupSession = False
        self.runFlowsheetMethod = 0  # 0 local, 1 through turbine
        self.settingsNormpath()
        self.recentlyOpenedFiles = []
        self.settingsInWDir = False
        # A list of attributes to save in the settings file
        self.directCopy = [
            "working_dir",
            "simsinter_path",
            "psuade_path",
            "foqusLogLevel",
            "turbLogLevel",
            "foqusLogToConsole",
            "turbLogToConsole",
            "foqusLogToFile",
            "turbLogToFile",
            "foqusLogFile",
            "turbineLogFile",
            "logFormat",
            "alamo_path",
            "aspenVersion",
            "turbLiteHome",
            "logRotate",
            "maxLogSize",
            "compactSession",
            "backupSession",
            "rScriptPath",
            "recentlyOpenedFiles",
            "turbConfig",
            "turbConfigCluster",
            "runFlowsheetMethod",
            "settingsInWDir",
            "numRecentFiles",
            "turbineRemoteCheckFreq",
            "turbineRemoteReSub",
        ]

    def addRecentlyOpenedFile(self, fname):
        """
        Add fname to the list of recently opened files.
        """
        fname = os.path.abspath(fname)
        if fname in self.recentlyOpenedFiles:
            self.recentlyOpenedFiles.remove(fname)
        self.recentlyOpenedFiles.insert(0, fname)
        if len(self.recentlyOpenedFiles) > self.numRecentFiles:
            self.recentlyOpenedFiles.pop()

    def checkRecentlyOpenedFiles(self):
        """
        Check the list of recently owned files for:
        1) files exist
        2) <= number of files to track limit
        3) remove duplicates
        """
        files = []
        for fn in self.recentlyOpenedFiles:
            if len(files) > self.numRecentFiles:
                break
            if fn not in files:
                if os.path.isfile(fn):
                    files.append(fn)
        self.recentlyOpenedFiles = files
        return files

    def getRecentlyOpendFiles(self):
        """
        Just returns the list of files.  This is here in case
        we deside to add some validation step.
        """
        return self.recentlyOpenedFiles

    def settingsNormpath(self):
        """
        Make sure all the seperators match and go the right way for
        the OS
        """
        if self.working_dir:
            self.working_dir = os.path.normpath(self.working_dir)
        if self.new_working_dir:
            self.new_working_dir = os.path.normpath(self.new_working_dir)
        if self.simsinter_path:
            self.simsinter_path = os.path.normpath(self.simsinter_path)
        if self.psuade_path:
            self.psuade_path = os.path.normpath(self.psuade_path)
        if self.turbConfig:
            self.turbConfig = os.path.normpath(self.turbConfig)
        if self.turbConfigCluster:
            self.turbConfigCluster = os.path.normpath(self.turbConfigCluster)
        if self.alamo_path:
            self.alamo_path = os.path.normpath(self.alamo_path)
        if self.turbLiteHome:
            self.turbLiteHome = os.path.normpath(self.turbLiteHome)

    @staticmethod
    def getUserConfigLocation():
        """
        Get a location to store a FOQUS configuration file.  This
        should work with Windows, Linux, OSX, Unix. It may fail on
        other platforms, but who knows what those would be.
        Returns None if it cant get a configuration location.
        """
        if os.name == "nt":  # Windows
            return os.path.join(os.environ["APPDATA"], ".foqus.cfg")
        else:  # any other OS
            return os.path.join(os.environ["HOME"], ".foqus.cfg")

    def chdir(self):
        """
        Change the working directory to the working directory
        setting and make file structure
        """
        os.chdir(self.working_dir)
        makeWorkingDirStruct()
        makeWorkingDirFiles()

    def loadDict(self, sd, sdLocal, useCurrentWorkingDir=False, logging=True):
        """
        Load the settings from a dictionary, and apply them
        some setting changes may require a FOQUS restart though and
        are handeled when FOQUS starts.
        """
        curWdir = os.getcwd()
        for att in self.directCopy:  # reads settings from appdata
            if sd.get(att, None) != None:
                self.__dict__[att] = sd.get(att, "")
        for att in self.directCopy:  # reads settings from working dir
            if sdLocal.get(att, None) != None:
                self.__dict__[att] = sdLocal.get(att, "")
        if self.working_dir == "" or useCurrentWorkingDir:
            self.working_dir = curWdir
        if logging:
            self.applyLogSettings()
            self.chdir()
        self.settingsNormpath()
        self.checkRecentlyOpenedFiles()

    def saveDict(self, newWdir=False):
        """
        Save the settings to a dictionary
        """
        sd = dict()
        for att in self.directCopy:
            sd[att] = copy.deepcopy(self.__dict__[att])
        if newWdir:
            sd["working_dir"] = self.new_working_dir
        return sd

    def save(self, ignoreWDirSetting=False, newWdir=False):
        """
        Save the setting in json format to a file specified by the
        getUserConfigLocation() function or a settings file in the
        working directory

        ignoreWDirSetting: allows the settings file to be saved in
            the $HOME or %APPDATA% location regaurdless of the
            setting to save the options in the working directory.
            this allows FOQUS to create a main settings file if
            it doesn't exist.  Asside from that the
            ignoreWDirSetting argument is pretty useless
        """
        d = self.saveDict(newWdir=newWdir)
        if self.settingsInWDir and not ignoreWDirSetting:
            fn = "foqus.cfg"
        else:
            fn = self.getUserConfigLocation()
        with open(fn, "w") as f:
            json.dump(d, f, indent=2)
        LocalExecutionModule.writePsuadePath(self.psuade_path)

    def load(self, useCurrentWorkingDir=False, logging=True):
        """
        Load the setting in json format from a file specified by the
        getUserConfigLocation() function
        """
        fn = self.getUserConfigLocation()
        fnLocal = "foqus.cfg"
        if not os.path.exists(fn):
            self.save(ignoreWDirSetting=True)
        with open(fn, "r") as f:
            d = json.load(f)
        try:
            with open(fnLocal, "r") as f:
                dLocal = json.load(f)
        except:
            dLocal = {}
        self.loadDict(
            d, dLocal, useCurrentWorkingDir=useCurrentWorkingDir, logging=logging
        )

    def applyLogSettings(self):
        """
        Take the log settings from the session and set up logging
        """
        # There are two log files. one for FOQUS and
        # one for Turbine Client
        flog = logging.getLogger("foqus")
        tlog = logging.getLogger("turbine")
        # Close all log handlers and clear
        for h in flog.handlers:
            h.close()
        for h in tlog.handlers:
            h.close()
        flog.handlers = []
        tlog.handlers = []
        # Setting for whether to send FOQUS log messages to file
        if self.foqusLogToFile:
            if self.logRotate:
                flogFH = logging.handlers.RotatingFileHandler(
                    filename=os.path.join("logs", self.foqusLogFile),
                    maxBytes=self.maxLogSize * 1000000,
                    backupCount=5,
                )
            else:
                flogFH = logging.FileHandler(
                    filename=os.path.join("logs", self.foqusLogFile)
                )
            flogFH.setFormatter(logging.Formatter(self.logFormat))
        # Setting for whether to send Turbine client log msgs to file
        if self.turbLogToFile:
            if self.logRotate:
                tlogFH = logging.handlers.RotatingFileHandler(
                    filename=os.path.join("logs", self.turbineLogFile),
                    maxBytes=self.maxLogSize * 1000000,
                    backupCount=5,
                )
            else:
                tlogFH = logging.FileHandler(
                    filename=os.path.join("logs", self.turbineLogFile)
                )
            tlogFH.setFormatter(logging.Formatter(self.logFormat))
        # Setting for sending FOQUS log messages to stdout
        if self.foqusLogToConsole:
            flogCH = logging.StreamHandler(stream=sys.stdout)
            flogCH.setFormatter(logging.Formatter(self.logFormat))
        # Setting for sending Turbine client log messages to stdout
        if self.turbLogToConsole:
            tlogCH = logging.StreamHandler(stream=sys.stdout)
            tlogCH.setFormatter(logging.Formatter(self.logFormat))
        # Create log handlers
        if self.foqusLogToFile:
            flog.addHandler(flogFH)
        if self.turbLogToFile:
            tlog.addHandler(tlogFH)
        if self.foqusLogToConsole:
            flog.addHandler(flogCH)
        if self.turbLogToConsole:
            tlog.addHandler(tlogCH)
        # If neither file or stdout set null handler
        if len(flog.handlers) == 0:
            flog.addHandler(logging.NullHandler())
        if len(tlog.handlers) == 0:
            tlog.addHandler(logging.NullHandler())
        # Set the logging level
        flog.setLevel(self.foqusLogLevel)
        tlog.setLevel(self.turbLogLevel)
