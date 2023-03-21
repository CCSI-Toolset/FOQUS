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
import sys
import os
import re
import shutil
import subprocess
import tempfile
import time
import platform
import logging
import io

try:
    from PyQt5 import QtGui, QtCore, QtWidgets

    usePyside = True
except:
    usePyside = False

if usePyside:
    obj = QtCore.QObject
else:
    obj = object


class Common(obj):
    dialog = None

    if usePyside:

        class textDialog(QtWidgets.QDialog):
            def __init__(self, parent=None):
                super(Common.textDialog, self).__init__(parent)
                self.setWindowTitle("Calculating...")
                self.resize(600, 400)
                self.gridLayout = QtWidgets.QGridLayout(self)
                self.textedit = QtWidgets.QTextEdit()
                self.textedit.setReadOnly(True)
                self.textedit.setWordWrapMode(QtGui.QTextOption.NoWrap)
                self.gridLayout.addWidget(self.textedit)
                # self.doneButton = QtGui.QPushButton(self)
                # self.doneButton.setText('Done')
                # self.doneButton.setEnabled(False)
                # self.doneButton.clicked.connect(self.close)
                # self.gridLayout.addWidget(self.doneButton)

            def showError(self, error, out=None):
                msgBox = QtWidgets.QMessageBox()
                msgBox.setIcon(QtWidgets.QMessageBox.Critical)
                msgBox.setText(
                    error + "\nPlease consult the FOQUS UQ developers for assistance."
                )
                if out is not None:
                    msgBox.setDetailedText(out)

    @staticmethod
    def getPsuadePath():  ### OBSOLETE in this release
        # Brenda's version of getPsuadePath(), superceded by LocalExecutionModule.getPsuadePath()
        fname = os.getcwd() + os.path.sep + "PSUADEPATH"
        if not os.path.exists(fname):
            error = "%s does not exist." % fname
            Common.showError(error)
            return None

        f = open(fname, "r")
        path = f.readline()
        f.close()
        return path.rstrip()

    @staticmethod
    def initFolder(dname, deleteFiles=True):
        if os.path.exists(dname):
            #            shutil.rmtree(dname)
            if deleteFiles:
                for the_file in os.listdir(dname):
                    file_path = os.path.join(dname, the_file)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        print(e)
        else:
            os.mkdir(dname)
        return None

    @staticmethod
    def getFileNameRoot(fname):
        base = os.path.basename(fname)
        fnameRoot = base.split(".")[0]  # split on '.'
        return fnameRoot

    @staticmethod
    def getLocalFileName(dname, fname, suffix):
        fnameRoot = Common.getFileNameRoot(fname)
        outfile = "%s%s%s%s" % (dname, os.path.sep, fnameRoot, suffix)
        return outfile

    @staticmethod
    def showError(error, out=None, showDeveloperHelpMessage=True):
        if out is not None and "Regression ERROR: true rank of sample " in out:
            error = "The selected regression response surface does not work with the data. \nPlease select a different response surface.\n\n"
            showDeveloperHelpMessage = False
        if not usePyside or QtWidgets.QApplication.instance() is None:
            print(error)
        else:
            msgBox = QtWidgets.QMessageBox()
            msgBox.setIcon(QtWidgets.QMessageBox.Critical)
            if showDeveloperHelpMessage:
                msgBox.setText(
                    error + "\nPlease consult the FOQUS UQ developers for assistance."
                )
            else:
                msgBox.setText(error)
            if out is not None:
                msgBox.setDetailedText(out)
            msgBox.exec_()

    @staticmethod
    # Pass a filename as a string to use as input file (e.g. "psuade ps.in")
    #   Requires a psuade formatted file
    # Pass a file handle to use it as a script (e.g.  "psuade < script")
    def invokePsuade(
        arg1,
        arg2=None,
        printOutputToScreen=False,
        textDialog=None,
        dialogShowSignal=None,
        dialogCloseSignal=None,
        textInsertSignal=None,
        ensureVisibleSignal=None,
        showErrorSignal=None,
        plotOuuValuesSignal=None,
    ):
        from .LocalExecutionModule import LocalExecutionModule

        psuadePath = LocalExecutionModule.getPsuadePath()
        if psuadePath is None:
            return (None, None)

        scriptHandle = None
        psFileName = ""

        if isinstance(arg1, io.IOBase) or isinstance(
            arg1, tempfile.SpooledTemporaryFile
        ):  # script
            scriptHandle = arg1
            if arg2 is not None:
                if isinstance(arg2, str):
                    psFileName = arg2
                elif isinstance(arg2, bool):
                    printOutputToScreen = arg2
                else:
                    raise TypeError(
                        "Second argument is not psuade input filename nor True/False for printing output to screen"
                    )
        elif isinstance(arg1, str):
            psFileName = arg1
            if arg2 is not None:
                if isinstance(arg2, io.IOBase) or isinstance(
                    arg1, tempfile.SpooledTemporaryFile
                ):  # script
                    scriptHandle = arg2
                elif isinstance(arg2, bool):
                    printOutputToScreen = arg2
                else:
                    raise TypeError(
                        "Second argument is not script file handle nor True/False for printing output to screen"
                    )

        return Common.runCommandInWindow(
            psuadePath + " " + psFileName,
            "psuadelog",
            scriptHandle,
            printOutputToScreen,
            textDialog,
            dialogShowSignal,
            dialogCloseSignal,
            textInsertSignal,
            ensureVisibleSignal,
            showErrorSignal,
            plotOuuValuesSignal,
        )

    @staticmethod
    def runCommandInWindow(
        command,
        logFile,
        scriptHandle=subprocess.PIPE,
        printOutputToScreen=False,
        textDialog=None,
        dialogShowSignal=None,
        dialogCloseSignal=None,
        textInsertSignal=None,
        ensureVisibleSignal=None,
        showErrorSignal=None,
        plotOuuValuesSignal=None,
    ):

        executable = None
        if platform.system() == "Linux":
            executable = "/bin/bash"
        p = subprocess.Popen(
            command,
            stdin=scriptHandle,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            executable=executable,
            shell=True,
        )

        logFile = open(logFile, "w")

        if usePyside and QtWidgets.QApplication.instance() is not None:
            if textDialog is None:
                Common.dialog = Common.textDialog()
                Common.dialog.show()
            else:
                Common.dialog = textDialog
                dialogShowSignal.emit()

        out = ""
        count = 0
        startTime = time.time()
        readChars = False
        iteration = 1
        grabx = False  # set to True when listening for input values
        grabz = False  # set to True when listening for objective values
        while True:
            if p.poll() is None:
                sleepTime = 0.01
            else:
                sleepTime = 0.0001
            time.sleep(sleepTime)
            if time.time() - startTime > 0.2:
                if usePyside:
                    QtCore.QCoreApplication.processEvents()
                startTime = time.time()
            # Reading chars is used so iteration % can be displayed
            # without having to read whole line
            if readChars:
                nextline = p.stdout.read(1)
                # If character is a letter, switch back to reading lines
                value = ord(nextline)
                if value >= ord("A") and value <= ord("Z"):
                    readChars = False
            else:
                nextline = p.stdout.readline()
                if not "OUU" in nextline.decode(
                    "utf-8"
                ) and "iteration = " in nextline.decode("utf-8"):
                    readChars = True
            out += nextline.decode("utf-8")
            if nextline.decode("utf-8") == "" and p.poll() is not None:
                break
            logFile.write(nextline.decode("utf-8"))
            if printOutputToScreen:
                # print nextline.strip()
                sys.stdout.write(nextline.decode("utf-8"))
            if usePyside and QtWidgets.QApplication.instance() is not None:
                textedit = Common.dialog.textedit
                if textInsertSignal is None:
                    textedit.insertPlainText(nextline.decode("utf-8"))
                else:
                    # print 'insert signal'
                    textInsertSignal.emit(nextline.decode("utf-8"))
                if ensureVisibleSignal is None:
                    textedit.ensureCursorVisible()
                else:
                    ensureVisibleSignal.emit()
                count += 1
                if count == 10 or time.time() - startTime > 0.5:
                    QtCore.QCoreApplication.processEvents()
                    count = 0
                    startTime = time.time()
                # Common.dialog.repaint()
            if plotOuuValuesSignal is not None:
                if not grabz:
                    pat = "Outer optimization iteration = ([0-9]*)"
                    regex = re.findall(pat, nextline.decode("utf-8"))
                    if regex:
                        grabz = False
                        grabx = True
                        x = []
                        i = int(regex[0])
                        x.append(i)
                        continue
                if grabx:
                    pat = "Current Level 1 input \s*[0-9]* = (.*)"
                    regex = re.findall(pat, nextline.decode("utf-8"))
                    if regex:
                        x.append(float(regex[0]))  # input value
                        continue

                pat = "computing objective .* nFuncEval = (.*)"
                regex = re.findall(pat, nextline.decode("utf-8"))
                if regex:
                    grabx = False
                    grabz = True
                    z = []
                    i = int(regex[0])
                    z.append(i)
                    continue

                if grabz:
                    pat = "computed  objective .* = (.*)\."
                    regex = re.findall(pat, nextline.decode("utf-8"))
                    if regex:
                        z.append(float(regex[0]))
                        grabz = False
                        plotValues = {}
                        plotValues["input"] = x
                        plotValues["objective"] = (z[0], z[1])
                        plotOuuValuesSignal.emit(plotValues)
                        continue
            iteration += 1
        if printOutputToScreen:
            print("\n\n")

        logFile.close()

        # process error
        out2, error = p.communicate()
        error = error.decode("utf-8")
        try:
            p.terminate()
        except:
            logging.getLogger("foqus." + __name__).exception(
                "Error terminating PSUADE process, this may be okay"
                "but not sure so logged it (JCE)"
            )
        if error:
            if showErrorSignal is None:
                Common.showError(error, out)
            else:
                showErrorSignal.emit(error, out)

        if usePyside and QtWidgets.QApplication.instance() is not None:
            if dialogCloseSignal is None:
                Common.dialog.close()
            else:
                dialogCloseSignal.emit()

        return (out, error)

    @staticmethod
    def getUserRegressionOutputName(outName, userRegressionFile, data):
        # check input names have nodes
        labelsLine = None
        with open(userRegressionFile) as regF:
            lines = regF.readlines()
            for line in lines:
                print(line)
                if line.strip().lower().startswith("labels") and "".join(
                    line.lower().split()
                ).startswith("labels="):
                    labelsLine = line
                    break

        useNodeNames = False
        if labelsLine:  # labels line found. Check them
            exec(labelsLine)
            newName = outName.replace(
                ".", "_"
            )  # Input name that includes node name in the variable name
            if newName in labelsLine:
                useNodeNames = True
                outName = newName
        if not useNodeNames and data.getNamesIncludeNodes():
            index = outName.index(".")
            outName = outName[index + 1 :]
        return outName
