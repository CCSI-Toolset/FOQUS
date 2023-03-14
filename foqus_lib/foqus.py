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
"""
* FOQUS Commands:
- foqus: to start FOQUS

John Eslick, Carnegie Mellon University, 2014
Keith Beattie, Lawrence Berkeley National Labs, 2020
"""

# Imports
import signal
import uuid
import sys
import argparse
import time
import json
import logging

# FOQUS imports
import foqus_lib.version.version as ver  # foqus version and other info
from foqus_lib.framework.session.session import *
from foqus_lib.framework.listen.listen import foqusListener2
from foqus_lib.gui.make_shortcut import makeShortcut

loadGUI = False
guiAvail = False
# Splash screen global variables
splash_timeout_ms = 10000  # initial Splash screen hide in ms
splashScr = [None, None]  # [0] splash timer, [1] splash screen
foqus_application = None  # The Qt application so I can show dialogs
# global variables
dat = None
PyQt5 = None


def guiImport(mpl_backend="Qt5Agg"):
    """
    Only import the GUI classes if you want the GUI
    """
    global loadGUI
    global guiAvail
    global dmf_lib
    global PyQt5
    # GUI Imports
    try:  # Check if the PySide libraries are available
        import PyQt5

        # QtWidgets, QtGui, and QtCore are used in this module,
        # but they might not be available in PyQt5 without importing them first
        # in most circumstances, they will be already imported
        # from the imports in foqus_lib.framework.session.session
        # to be on the safe side, we run these imports explicitly here, too
        import PyQt5.QtWidgets
        import PyQt5.QtGui
        import PyQt5.QtCore
        import matplotlib

        matplotlib.use(mpl_backend)
        matplotlib.rcParams["backend"] = mpl_backend
        loadGUI = True
        guiAvail = True
    except ImportError:
        logging.getLogger("foqus." + __name__).exception("Error importing PyQt")
        loadGUI = False
        guiAvail = False


def hideSplash():
    """
    Hide splash screen is called by timer, also stops the timer
    don't need timer after it hides the splash
    """
    splashScr[0].stop()  # stop the timer
    splashScr[1].hide()  # and hide the splash screen


def makeSplash():
    """
    This makes a splash screen that has the current FOQUS version
    information as well as all of the third party dependency
    information
    """
    # Load the splash screen background svg, gonna draw text over
    pixmap = PyQt5.QtGui.QPixmap(":/icons/icons/ccsiSplash2.svg")
    # Make a painter to add text to
    painter = PyQt5.QtGui.QPainter(pixmap)
    font = painter.font()  # current font for drawing text
    font.setPointSize(8)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(20, 110, "Version: {}".format(ver.version))
    font.setBold(False)
    painter.setFont(font)
    painter.drawText(
        20,
        200,
        740,
        50,
        PyQt5.QtCore.Qt.AlignTop
        | PyQt5.QtCore.Qt.AlignLeft
        | PyQt5.QtCore.Qt.TextWordWrap,
        "License: {}".format(ver.license),
    )
    painter.drawText(
        20,
        250,
        740,
        50,
        PyQt5.QtCore.Qt.AlignTop
        | PyQt5.QtCore.Qt.AlignLeft
        | PyQt5.QtCore.Qt.TextWordWrap,
        "Support: {}".format(ver.support),
    )
    painter.drawText(
        20,
        300,
        740,
        300,
        PyQt5.QtCore.Qt.AlignTop
        | PyQt5.QtCore.Qt.AlignLeft
        | PyQt5.QtCore.Qt.TextWordWrap,
        ver.copyright,
    )
    painter.end()
    splashScr[1] = PyQt5.QtWidgets.QSplashScreen(pixmap=pixmap)


def startGUI(
    showSplash=False,
    app=None,
    showUQ=True,
    showOpt=True,
    showBasicData=True,
    showSDOE=True,
    ts=None,
):
    """
    This function starts the main window of the FOQUS GUI.

    Args:
        showSplash: if false don't show splash screen
        app: if already created pyside app to show message use it
        showUQ: Show the UQ tab
        showOpt: Show the optimzation tab
        showBasicDataTab: Show the Basic Data tab
        ts: A testing script to automatiacally run when GUI starts.
    """
    import foqus_lib.gui.main.mainWindow as MW

    if app == None:
        app = PyQt5.QtWidgets.QApplication(sys.argv)
    # create main window and start application loop
    makeSplash()
    if showSplash:
        # add timer to show splash
        splashScr[0] = PyQt5.QtCore.QTimer()
        splashScr[0].timeout.connect(hideSplash)
        # splash_timeout_ms is how long to show splash in ms
        # it is set in the first code line of this file
        splashScr[0].start(splash_timeout_ms)
        splashScr[1].setWindowFlags(
            splashScr[1].windowFlags() | PyQt5.QtCore.Qt.WindowStaysOnTopHint
        )
        splashScr[1].show()

    mainWin = MW.mainWindow(
        "FOQUS",  # window title
        800,  # width
        600,  # height
        dat,  # FOQUS session data
        splashScr[1],  # splash screen to use for about
        showUQ=showUQ,
        showOpt=showOpt,
        showBasicData=showBasicData,
        showSDOE=showSDOE,
        ts=ts,
    )
    mainWin.app = app
    app.exec_()
    return mainWin


def logException(etype, evalue, etrace):
    """
    A function to assign to sys.excepthook to cause unhandled exceptions to go
    to the log file instead of stderr.  If GUI is started this will also attempt
    to show unhandled exceptions in a dialod box, so user is aware.
    """
    try:
        hideSplash()
    except:
        pass
    try:
        logging.getLogger("foqus." + __name__).critical(
            "unhandled exception", exc_info=(etype, evalue, etrace)
        )
        if foqus_application:
            # just incase the exception happend when
            # cursor was set to waiting type set to normal
            foqus_application.restoreOverrideCursor()
            # Now show error in a message box
            msgBox = PyQt5.QtWidgets.QMessageBox()
            msgBox.setWindowTitle("Error")
            msgBox.setText("Unhandled Exception:")
            msgBox.setInformativeText(
                "".join(traceback.format_exception(etype, evalue, etrace))
            )
            msgBox.exec_()
    except Exception as e:
        logging.getLogger("foqus." + __name__).exception(
            "unhandled exception: If you see this there was some"
            " problem with unhandled exception logging. "
        )


def signal_handler(signal, frame):
    """
    A signal handler to cause a siginal to raise a keyboardinterupt exception.
    Used to override a default signal like SIGINT so the FOQUS consumer process
    can shutdown cleanly. The FOQUS consumer catches the keyboardinterupt
    exception as one (slighlty unreliable) way to shut down.  Seems ctrl-c
    causes keyboard interupt exception and SIGINT signal, hense need to change
    SIGINT handler.
    """
    raise KeyboardInterrupt()


def main(args_to_parse=None):
    global dat
    exit_code = 0  # Proc exit code
    # Set up the basic logging stuff here, later after the working
    # directory is set a file handler can be added once a new foqus
    # session is created and the FOQUS settings are read.
    logFormat = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    consHand = logging.StreamHandler(stream=sys.stdout)
    consHand.setFormatter(logging.Formatter(logFormat))
    logging.getLogger("foqus").addHandler(consHand)
    logging.getLogger("turbine").addHandler(consHand)
    logging.getLogger("foqus").setLevel(logging.DEBUG)
    logging.getLogger("turbine").setLevel(logging.DEBUG)
    sys.excepthook = logException  # for unhandled exception logging
    try:
        turbine.commands._setup_logging.done = True
    except:
        logging.getLogger("foqus." + __name__).exception("Cannot finde turbine module")
    app = None  # Qt application if I need to display message boxes.
    ## Setup the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", help="Project file to load")
    parser.add_argument("-l", "--load", help="Project file to load")
    parser.add_argument("-w", "--working_dir", help="Set the working directory")
    parser.add_argument("--splash", help="Display splash", action="store_true")
    parser.add_argument("--nosplash", help="No splash", action="store_true")
    parser.add_argument(
        "--make-shortcut",
        help="Make shortcut on Desktop to start " "FOQUS then exit (Windows only)",
        action="store_true",
    )
    parser.add_argument(
        "--nogui", help="Do not start the graphical interface", action="store_true"
    )
    parser.add_argument(
        "--noopt", help="Hide the optimization interface", action="store_true"
    )
    parser.add_argument("--nouq", help="Hide the UQ interface", action="store_true")
    parser.add_argument(
        "--basic_data", help="Show the basic data tab", action="store_true"
    )
    parser.add_argument(
        "--run", help="Specify a run type and start", choices=["opt", "uq", "sim"]
    )
    parser.add_argument("-o", "--out", help="Output file for run")
    parser.add_argument(
        "--loadValues",
        help="Load flowsheet variable values from json file,"
        " Must also load the flowsheet with -l or --load",
    )
    parser.add_argument(
        "--saveValues",
        help="Save flowsheet variable values to a json file,"
        " Must also load the flowsheet with -l or --load",
    )
    parser.add_argument(
        "--listen", action="store_true", help="Listen for runs requested by client"
    )
    parser.add_argument(
        "--host", default="localhost", help="Host name, use with --listen option"
    )
    parser.add_argument(
        "--port", default=56002, type=int, help="Port, use with --listen option"
    )
    parser.add_argument(
        "--consumer", action="store_true", help="Start FOQUS as Turbine Consumer"
    )
    parser.add_argument(
        "--consumer_cleanup_error",
        action="store_true",
        help="Turn all running state FOQUS jobs to error on start up",
    )
    parser.add_argument(
        "--consumer_cleanup_rerun",
        action="store_true",
        help="Pick up and run FOQUS jobs in the running state",
    )
    parser.add_argument(
        "--consumer_delay",
        default=5,
        type=float,
        help="Time between checking for new jobs",
    )
    parser.add_argument(
        "--consumer_simulation", help="Only take jobs for a particular simulation name"
    )
    parser.add_argument(
        "--consumer_session", help="Only take jos for a particular session GUID"
    )
    parser.add_argument(
        "--consumer_only_my_id",
        action="store_true",
        help="Only take jos with own consumer Id specified",
    )
    parser.add_argument(
        "--consumer_cancel_jobs",
        action="store_true",
        help="Consumer cancels jobs instead of running them, a "
        "way to clear the TurbineLite job queue",
    )
    parser.add_argument(
        "--addTurbineApp", help="Add an application type to TurbineLite DB"
    )
    parser.add_argument(
        "--terminateConsumer", help="Terminate the consumer with the given UUID"
    )
    parser.add_argument(
        "-s", "--runUITestScript", help="Load and run a user interface test script"
    )
    args = parser.parse_args(args=args_to_parse)
    # before changing the directory get absolute path for file to load
    # this way it will be relative to where you execute foqus instead
    # or relative to the working dir
    if args.file:
        args.load = os.path.abspath(args.file[0])
    if args.load:
        args.load = os.path.abspath(args.load)
    if args.runUITestScript:
        args.runUITestScript = os.path.abspath(args.runUITestScript)
    ## Run any quick commands and exit before setting up a FOQUS session
    if args.make_shortcut:
        sys.exit(makeShortcut())
    if args.terminateConsumer:
        try:
            from foqus_lib.framework.sim.turbineLiteDB import turbineLiteDB
            from foqus_lib.framework.sim.turbineLiteDB import keepAliveTimer

            fs = generalSettings()  # foqus settings
            fs.load(logging=False)
            db = turbineLiteDB()
            db.dbFile = os.path.join(fs.turbLiteHome, "Data/TurbineCompactDatabase.sdf")
            print("terminating consumer {0}".format(args.terminateConsumer))
            db.consumer_status(args.terminateConsumer, "terminate")
            sys.exit(0)
        except Exception as e:
            logging.getLogger("foqus." + __name__).exception(
                "Error terminating turbine consumer"
            )
            sys.exit(1)
    elif args.addTurbineApp:
        try:
            from foqus_lib.framework.sim.turbineLiteDB import turbineLiteDB
            from foqus_lib.framework.sim.turbineLiteDB import keepAliveTimer

            fs = generalSettings()  # foqus settings
            fs.load(logging=False)
            db = turbineLiteDB()
            db.dbFile = os.path.join(fs.turbLiteHome, "Data/TurbineCompactDatabase.sdf")
            print(
                "Adding application '{0}' to TurbineLite database".format(
                    args.addTurbineApp
                )
            )
            db.add_new_application(args.addTurbineApp)
            sys.exit(0)
        except Exception as e:
            logging.getLogger("foqus." + __name__).exception("Error adding turbine app")
            sys.exit(1)
    if args.consumer:
        nogui = True
    elif args.listen:
        nogui = True
    elif args.run:
        nogui = True
    else:
        nogui = False
    if not nogui:
        guiImport()
    if guiAvail and not args.nogui and not nogui:
        # start up a Qt app so I can display GUI messages
        # instead of printing to console
        app = PyQt5.QtWidgets.QApplication(sys.argv)
        foqus_application = app
    else:  # if no gui, I'll fall back to print
        app = None
    ## Setup the working directory
    if args.working_dir:
        # Set working directory from command line argument
        try:
            os.chdir(args.working_dir)
            makeWorkingDirStruct()  # setup working dir, session module
            makeWorkingDirFiles()
        except Exception as e:
            logging.getLogger("foqus." + __name__).exception(
                'Could not set the working directory to "{}"'.format(args.working_dir)
            )
            sys.exit(111)
    else:
        # working directory not set on command line
        # try to get it from configuration file if not available
        # ask user, fall back on using current directory
        if not generalSettings.getUserConfigLocation():
            # don't know where config file is stored for this os
            # so just fall back on current directory, pass just
            # doesn't change directory so the working directory is
            # wherever FOQUS was started from.
            pass
        else:
            # look for FOQUS configuration file
            try:
                with open(generalSettings.getUserConfigLocation(), "r") as f:
                    s = f.read()
                settings = json.loads(s)
                os.chdir(settings["working_dir"])
            except:
                # was not able to get working dir from
                # configuration file
                if app:
                    # gui is available ask about working dir
                    # and write config file
                    settings = {"working_dir": None}
                    msg = PyQt5.QtWidgets.QMessageBox()
                    msg.setText(
                        (
                            "The user working directory has not "
                            "been specified yet. \nPlease create a FOQUS "
                            "working directory and specify its location "
                            "after pressing okay."
                        )
                    )
                    msg.exec_()
                    msg = PyQt5.QtWidgets.QFileDialog()
                    msg.setFileMode(PyQt5.QtWidgets.QFileDialog.Directory)
                    msg.setOption(PyQt5.QtWidgets.QFileDialog.ShowDirsOnly)
                    if msg.exec_():
                        dirs = msg.selectedFiles()
                        settings["working_dir"] = dirs[0]
                        os.chdir(settings["working_dir"])
                    else:
                        logging.getLogger("foqus." + __name__).error(
                            ("No working directory" " specified. FOQUS will exit")
                        )
                        msg = PyQt5.QtWidgets.QMessageBox()
                        msg.setText(
                            ("No working directory" " specified. FOQUS will exit.")
                        )
                        msg.exec_()
                        sys.exit()
                else:
                    # Fall back on current directory if no config and
                    # now GUI for file selector
                    logging.getLogger("foqus." + __name__).error(
                        "Using current directory as working directory"
                    )
    # Create working directory directory structure if is not in place
    logging.getLogger("foqus." + __name__).debug(
        "Working directory set to " + os.getcwd()
    )
    if not makeWorkingDirStruct():
        logging.getLogger("foqus." + __name__).critical(
            "Could not setup working directory, exiting"
        )
        sys.exit(9)
    # Copy files to working directory if needed. (just heat integration
    # gams files)
    makeWorkingDirFiles()
    ##
    ## create an emptpy FOQUS session
    ##
    logging.getLogger("foqus." + __name__).debug("Create Flowsheet Session")
    dat = session(useCurrentWorkingDir=True)
    ##
    ## Set some options
    ##
    # set option to show splash screen or not
    load_gui = True  # some options can disable GUI by setting this to False
    splash = False  # default is now don't show splash screen
    if args.splash:
        splash = True
    if args.nosplash or args.runUITestScript:
        splash = False
    ##
    ## Load session file if one was specified on command line
    ##
    logging.getLogger("foqus." + __name__).debug(
        "Load Flowsheet Session: %s", args.load
    )
    try:
        if args.load:
            dat.load(args.load)
    except:  # couldn't load the file
        logging.getLogger("foqus." + __name__).exception(
            "Could not load file specified with --load: " + args.load
        )
        sys.exit(10)
    ##
    ## Save the values from a flowsheet (only with load option)
    ##
    if args.saveValues:
        load_gui = False
        if not args.load:
            logging.getLogger("foqus." + __name__).error(
                "To save values you must load a flowsheet"
            )
            sys.exit(11)
        else:
            try:
                dat.saveFlowsheetValues(args.saveValues)
            except Exception as e:
                logging.getLogger("foqus." + __name__).exception(
                    'Could not save flowsheet values in: "{}"'.format(args.saveValues)
                )
                sys.exit(13)
    ##
    ## Load a set of saved values (only with load session option)
    ##
    logging.getLogger("foqus." + __name__).debug(
        "LoadValues Flowsheet: %s", args.loadValues
    )
    if args.loadValues:
        if not args.load:
            logging.getLogger("foqus." + __name__).error(
                "To load values you must load a flowsheet"
            )
            sys.exit(12)
        else:
            logging.getLogger("foqus." + __name__).debug("load values flowsheet")
            try:
                dat.loadFlowsheetValues(args.loadValues)
            except Exception as e:
                logging.getLogger("foqus." + __name__).exception(
                    'Could not load flowsheet values in: "{}"'.format(args.loadValues)
                )
                sys.exit(14)
    ## Run a single flowsheet, optimization, or eventually uq ensemble
    logging.getLogger("foqus." + __name__).debug("Run Option: %s", args.run)
    if args.run == "opt":
        # run an optimization problem from the command line
        # the optimization should previously have been setup
        load_gui = False  # not going to start gui for this
        print("Starting optimization, this may take some time...")
        print("(The GUI will not be started)")
        slvr = dat.optProblem.run(dat)
        slvr.join()  # Wait for optimization thread to finish
        dat.save(args.out)  # Save session as args.out
    elif args.run == "sim":
        load_gui = False
        print("Starting simulation, this may take some time...")
        print("(The GUI will not be started)")
        gt = dat.flowsheet.runAsThread()
        gt.join()
        if gt.res:
            dat.flowsheet.loadValues(gt.res[0])
        else:
            dat.flowsheet.errorStat = 19
        dat.saveFlowsheetValues(args.out)
    elif args.terminateConsumer:
        load_gui = False
        tliteHome = dat.foqusSettings.turbLiteHome
        DatabasePath = os.path.join(tliteHome, "Data/TurbineCompactDatabase.sdf")
        print("Terminating consumer")
    elif args.listen:
        # Open FOQUS to listen for commands on network port.
        load_gui = False
        listener = foqusListener2(dat, host=args.host, port=args.port)
        listener.start()
        listener.join()
    elif args.consumer:
        from foqus_lib.framework.sim.turbineLiteDB import turbineLiteDB
        from foqus_lib.framework.sim.turbineLiteDB import keepAliveTimer

        load_gui = False
        # Make ctrl-c do nothing but and SIGINT donothing but interupt
        # the loop
        signal.signal(signal.SIGINT, signal_handler)
        # Register consumer TurbineLite DB
        db = turbineLiteDB()
        db.dbFile = os.path.join(
            dat.foqusSettings.turbLiteHome, "Data/TurbineCompactDatabase.sdf"
        )
        logging.getLogger("foqus." + __name__).info(
            "TurbineLite Database:\n   {0}".format(db.dbFile)
        )
        # add 'foqus' app to TurbineLite DB if not already there
        db.add_new_application("foqus")
        # register the consumer in the database
        consumer_uuid = db.consumer_register()
        print("consumer_uuid: {0}".format(consumer_uuid))
        # write the time to the turbineLite db about every minute
        kat = keepAliveTimer(db, consumer_uuid, freq=60)
        kat.start()
        if args.consumer_simulation:
            onlySimName = args.consumer_simulation
        else:
            onlySimName = None
        if args.consumer_session:
            onlySession = args.consumer_session
        else:
            onlySession = None
        if args.consumer_only_my_id:
            onlyConsumer = consumer_uuid
        else:
            onlyConsumer = None

        if args.consumer_cleanup_rerun:
            cleanup = "submit"
        elif args.consumer_cleanup_error:
            cleanup = "error"
        else:
            cleanup = False
        if cleanup:
            logging.getLogger("foqus." + __name__).info(
                "FOQUS consumer moving running jobs to {0}".format(cleanup)
            )
            guid = 0
            while guid is not None:
                guid, jid, simId, reset = db.get_job_id(
                    simName=onlySimName,
                    sessionID=onlySession,
                    consumerID=onlyConsumer,
                    state="running",
                )
                if guid is not None:
                    db.job_change_status(guid, cleanup)

            logging.getLogger("foqus." + __name__).info(
                "FOQUS consumer moving setup jobs to {0}".format(cleanup)
            )
            guid = 0
            while guid is not None:
                guid, jid, simId, reset = db.get_job_id(
                    simName=onlySimName,
                    sessionID=onlySession,
                    consumerID=onlyConsumer,
                    state="setup",
                )
                if guid is not None:
                    db.job_change_status(guid, cleanup)
        try:
            logging.getLogger("foqus." + __name__).info(
                "FOQUS consumer {0} started, waiting for jobs...".format(consumer_uuid)
            )
            with open("consumer_uuid.txt", "w") as f:
                f.write(str(consumer_uuid))
            lastSim = None  # id for last foqus model ran
            i = 0
            terminate = False
            guid = None
            while not terminate:
                i += 1
                if i >= 10:  # check status, if terminate stop
                    i = 0
                    status = db.consumer_status(consumer_uuid)
                    if status == "terminate" or status == "down":
                        terminate = True
                        break
                guid, jid, simId, reset = db.get_job_id(
                    simName=onlySimName, sessionID=onlySession, consumerID=onlyConsumer
                )
                if not guid:
                    time.sleep(args.consumer_delay)
                elif args.consumer_cancel_jobs:
                    # Just switch job to cancel state
                    logging.getLogger("foqus." + __name__).info(
                        "Job {0} will be canceled".format(jid)
                    )
                    db.add_message(
                        "consumer={0}, canceling job {1}".format(consumer_uuid, jid),
                        guid,
                    )
                    db.job_change_status(guid, "cancel")
                else:
                    # Run the job
                    db.add_message(
                        "consumer={0}, starting job {1}".format(consumer_uuid, jid),
                        guid,
                    )
                    db.job_change_status(guid, "setup")
                    configContent = db.get_configuration_file(simId)
                    logging.getLogger("foqus." + __name__).info(
                        "Job {0} is submitted".format(jid)
                    )
                    db.jobConsumerID(guid, consumer_uuid)
                    db.job_prepare(guid, jid, configContent)
                    workingDirectory = os.path.join("test", str(jid))
                    # Session file to run
                    sfile = os.path.join(workingDirectory, "session.foqus")
                    # result session file to keep on record
                    rfile = os.path.join(workingDirectory, "results_session.foqus")
                    # Input values files
                    vfile = os.path.join(workingDirectory, "input_values.json")
                    # Output values file
                    ofile = os.path.join(workingDirectory, "output.json")
                    # Load the session file
                    try:
                        if reset:
                            logging.getLogger("foqus." + __name__).info(
                                "Reset = True, stopping consumers "
                                "and reloading foqus file {0}".format(sfile)
                            )
                            dat.load(sfile, stopConsumers=True)
                        elif simId != lastSim:
                            logging.getLogger("foqus." + __name__).info(
                                "Reset = False, but simulation id does not"
                                " match previous, reloading simulation"
                                " stopping consumers, {0}".format(sfile)
                            )
                            dat.load(sfile, stopConsumers=True)
                        else:
                            logging.getLogger("foqus." + __name__).info(
                                "Same simulation as prev., not reloading"
                            )
                        lastSim = simId
                        # Load the input values
                        logging.getLogger("foqus." + __name__).info(
                            "Loading input values. {0}".format(vfile)
                        )
                        dat.loadFlowsheetValues(vfile)
                        # Run graph
                        db.job_change_status(guid, "running")
                        logging.getLogger("foqus." + __name__).info(
                            "Moving job {0} to running state".format(jid)
                        )
                    except:
                        logging.getLogger("foqus." + __name__).exception(
                            "Error loading session or session inputs"
                            " for job: {0}".format(jid)
                        )
                        db.add_message(
                            "consumer={0}, job={1} error loading job or"
                            "inputs".format(consumer_uuid, jid),
                            guid,
                        )
                        with open(ofile, "w") as f:
                            json.dump({"graphError": 50}, f)
                        db.job_save_output(guid, workingDirectory)
                        db.job_change_status(guid, "error")
                        continue
                    gt = dat.flowsheet.runAsThread()
                    while gt.is_alive():
                        gt.join(10)
                        status = db.consumer_status(consumer_uuid)
                        if status == "terminate":
                            terminate = True
                            db.job_change_status(guid, "error")
                            gt.terminate()
                            break
                    if terminate:
                        break
                    if gt.res[0]:
                        logging.getLogger("foqus." + __name__).debug(
                            "GT: %s", gt.res[0]
                        )
                        dat.flowsheet.loadValues(gt.res[0])
                    else:
                        dat.flowsheet.errorStat = 19
                    dat.saveFlowsheetValues(ofile)
                    db.job_save_output(guid, workingDirectory)
                    dat.save(
                        filename=rfile,
                        updateCurrentFile=False,
                        changeLogMsg="Saved Turbine Run",
                        bkp=False,
                        indent=0,
                    )
                    if dat.flowsheet.errorStat == 0:
                        db.job_change_status(guid, "success")
                        db.add_message(
                            "consumer={0}, job {1} finished, success".format(
                                consumer_uuid, jid
                            ),
                            guid,
                        )
                        logging.getLogger("foqus." + __name__).info(
                            "Job {0} finished with success".format(jid)
                        )
                    else:
                        db.job_change_status(guid, "error")
                        db.add_message(
                            "consumer={0}, job {1} finished, error".format(
                                consumer_uuid, jid
                            ),
                            guid,
                        )
                        logging.getLogger("foqus." + __name__).info(
                            "Job {0} finished with error".format(jid)
                        )
        except KeyboardInterrupt:
            if guid:
                try:
                    db.add_message(
                        "consumer={0}, stopping consumer keyboard interupt".format(
                            consumer_uuid
                        ),
                        guid,
                    )
                except:
                    pass
            logging.getLogger("foqus." + __name__).info(
                "FOQUS Consumer stopped due to SIGINT"
            )
            try:
                gt.terminate()
            except:
                pass
            if guid:
                try:
                    db.job_change_status(guid, "error")
                except:
                    pass
        except Exception as e:
            if guid:
                try:
                    db.add_message(
                        "consumer={0}, stopping consumer exception, {1}".format(
                            consumer_uuid, str(e)
                        ),
                        guid,
                    )
                except:
                    pass
            logging.getLogger("foqus." + __name__).exception(
                "FOQUS Consumer stopped due to exception"
            )
            exit_code = 3
            try:
                gt.terminate()
            except:
                pass
            if guid:
                try:
                    db.job_change_status(guid, "error")
                except:
                    pass
        if terminate:
            if guid:
                try:
                    db.add_message(
                        "consumer={0}, stopping consumer terminate status".format(
                            consumer_uuid
                        ),
                        guid,
                    )
                    db.job_change_status(guid, "error")
                except:
                    pass
            logging.getLogger("foqus." + __name__).info(
                "Stopping FOQUS consumer '{0}' terminate status".format(consumer_uuid)
            )
        kat.terminate()
        # kat.join()
        db.consumer_status(consumer_uuid, "down")
    ##
    ## Start GUI, if needed (this is last because some options
    ## automatically disable gui, so I checked for those first
    ##
    if guiAvail and not args.nogui and load_gui:
        # Start graphical interface unless it is not
        # available or nogui flag given
        logging.getLogger("foqus." + __name__).debug("Starting GUI")
        if args.runUITestScript:
            ts = args.runUITestScript
        else:
            ts = None
        mw = startGUI(
            showSplash=splash,
            app=app,
            showOpt=not args.noopt,
            showUQ=not args.nouq,
            showBasicData=args.basic_data,
            ts=ts,
        )
        logging.getLogger("foqus." + __name__).debug("Exit GUI")
    elif not guiAvail and not args.nogui and load_gui:
        logging.getLogger("foqus." + __name__).error("PyQt5 or Qt not available")
        exit_code = 2
    ##
    ## Do clean up stuff and exit
    ##
    # stop all Turbine consumers
    dat.flowsheet.turbConfig.stopAllConsumers()
    dat.flowsheet.turbConfig.closeTurbineLiteDB()
    sys.exit(exit_code)
