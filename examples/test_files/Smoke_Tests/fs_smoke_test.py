#################################################################################
# FOQUS Copyright (c) 2012 - 2024, by the software owners: Oak Ridge Institute
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
from PyQt5 import QtCore, QtWidgets

MAX_RUN_TIME = 90000  # Maximum time to let script run in ms.
testOutFile = "ui_test_out.txt"
with open(testOutFile, "w") as f:  # file to write test results to
    f.write("Test Results\n")
timers = {}  # mainly put all timers in a dic so I can easily stop them all


def go(sleep=0.25, MainWin=MainWin):
    """Process gui events
    Since this script is running holds up the GUI main loop, this function
    processes GUI events and checks if the stop button has been pressed. It also
    pauses for sleep seconds to let things happen.
    """
    MainWin.app.processEvents()
    time.sleep(sleep)
    return not MainWin.helpDock.stop  # Return true is stop flag is set


def getButton(w, label):
    """Get a button in window w labeled label"""
    blist = w.buttons()
    for b in blist:
        if b.text().replace("&", "") == label:
            return b
    return None


global errorCount
global errorTitle
global errorFile
errorFile = "AutoErrLog_fs.txt"
errorCount = 0


def Error_okay(MainWin=MainWin, getButton=getButton, timers=timers):
    """Close the Error dialog if Error appears in the title, stops timer once the window comes up"""
    w = MainWin.app.activeWindow()
    try:
        if "Error" in str(w.windowTitle()):
            w.close()
            global errorCount
            global errorTitle
            global errorFile
            #            timers['Error_okay'].stop()
            if errorCount == 0:
                errFile = open(errorFile, "w")
            else:
                errFile = open(errorFile, "a")
            errorCount += 1
            errFile.write(
                "############################################################################\n"
            )
            errFile.write("Error Number: " + str(errorCount) + "\n")
            errFile.write("Error Title: " + errorTitle + "\n")
            try:
                errFile.write("Error Text: " + w.text() + "\n")
            except:
                None
            try:
                errFile.write("Error Detailed Text: \n" + w.detailedText() + "\n")
            except:
                None
            try:
                errFile.write("Error Informative Text: \n" + w.informativeText() + "\n")
            except:
                None
            errFile.close()
    except:
        None


def Error_okay_text(MainWin=MainWin, getButton=getButton, timers=timers):
    """Close the Error dialog if a, stops timer once the window comes up"""
    w = MainWin.app.activeWindow()
    try:
        if "FOQUS UQ developers" in str(w.text()):
            getButton(w, "OK").click()
            global errorCount
            global errorTitle
            global errorFile
            #            timers['Error_okay_text'].stop()
            if errorCount == 0:
                errFile = open(errorFile, "w")
            else:
                errFile = open(errorFile, "a")
            errorCount += 1
            errFile.write(
                "############################################################################\n"
            )
            errFile.write("Error Number: " + str(errorCount) + "\n")
            errFile.write("Error Title: \n" + errorTitle + "\n")
            try:
                errFile.write("Error Text: \n" + w.text() + "\n")
            except:
                None
            try:
                errFile.write("Error Detailed Text: \n" + w.detailedText() + "\n")
            except:
                None
            try:
                errFile.write("Error Informative Text: \n" + w.informativeText() + "\n")
            except:
                None
            errFile.close()
    except AttributeError:
        None


def msg_okay(MainWin=MainWin, getButton=getButton, timers=timers):
    """Click OK when a msgbox pops up, stops timer once a msgbox pops up"""
    w = MainWin.app.activeWindow()
    if isinstance(w, QtWidgets.QMessageBox):
        getButton(w, "OK").click()
        timers["msg_okay"].stop()


def msg_no(MainWin=MainWin, getButton=getButton, timers=timers):
    """Click No when a msgbox pops up, stops timer once a msgbox pops up"""
    w = MainWin.app.activeWindow()
    if isinstance(w, QtWidgets.QMessageBox):
        getButton(w, "No").click()
        timers["msg_no"].stop()


def add_UQ_cancel(MainWin=MainWin, getButton=getButton, timers=timers):
    """Cancel adding a UQ ensemble, stops timer once the window comes up"""
    w = MainWin.app.activeWindow()
    print(str(type(w)))
    if "updateUQModelDialog" in str(type(w)):
        getButton(w.buttonBox, "Cancel").click()
        timers["add_UQ_cancel"].stop()


def add_UQ_okay(MainWin=MainWin, getButton=getButton, timers=timers):
    """Press OK in adding a UQ ensemble, stops timer once the window comes up"""
    w = MainWin.app.activeWindow()
    if "updateUQModelDialog" in str(type(w)):
        getButton(w.buttonBox, "OK").click()
        timers["add_UQ_okay"].stop()


def add_UQ_yes(MainWin=MainWin, getButton=getButton, timers=timers):
    """Press YES in adding a UQ ensemble, stops timer once the window comes up"""
    w = MainWin.app.activeWindow()
    if "updateUQModelDialog" in str(type(w)):
        getButton(w.buttonBox, "YES").click()
        timers["add_UQ_yes"].stop()


def uq_sampling_scheme_MC(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup up an ensemble sampling scheme with Monte Carlo, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "Monte Carlo"
    if "SimSetup" in str(type(w)):
        timers["uq_sampling_scheme_MC"].stop()
        w.distTable.cellWidget(1, 1).setCurrentIndex(1)
        ### ----------------------------------------------------------------------
        # Normal Distribution
        w.distTable.cellWidget(0, 5).setCurrentIndex(1)
        w.distTable.cellWidget(0, 6).setItem(0, 1, QtWidgets.QTableWidgetItem("1"))
        w.distTable.cellWidget(0, 7).setItem(0, 1, QtWidgets.QTableWidgetItem("2"))
        ### ----------------------------------------------------------------------
        w.samplingTabs.setCurrentIndex(1)
        items = w.schemesList.findItems("Monte Carlo", QtCore.Qt.MatchExactly)
        w.schemesList.setCurrentItem(items[0])
        w.numSamplesBox.setValue(100)
        w.generateSamplesButton.click()
        if not go(sleep=0.5):
            return  # wait long enough for samples to generate
        w.doneButton.click()


def uq_sampling_scheme_QMC(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup up an ensemble sampling scheme with Quasi Monte Carlo, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "Quasi Monte Carlo/Lognormal Dist"
    if "SimSetup" in str(type(w)):
        timers["uq_sampling_scheme_QMC"].stop()
        w.distTable.cellWidget(1, 1).setCurrentIndex(1)
        ### ---------------------------------------------------------------------- # Isn't working
        # Lognormal Distribution
        w.distTable.cellWidget(0, 5).setCurrentIndex(2)
        w.distTable.setItem(0, 3, QtWidgets.QTableWidgetItem("0"))
        w.distTable.setItem(0, 4, QtWidgets.QTableWidgetItem("30"))
        w.distTable.cellWidget(0, 6).setItem(0, 1, QtWidgets.QTableWidgetItem("1"))
        w.distTable.cellWidget(0, 7).setItem(0, 1, QtWidgets.QTableWidgetItem("2"))
        ### ----------------------------------------------------------------------
        w.samplingTabs.setCurrentIndex(1)
        items = w.schemesList.findItems("Quasi Monte Carlo", QtCore.Qt.MatchExactly)
        w.schemesList.setCurrentItem(items[0])
        w.numSamplesBox.setValue(100)
        w.generateSamplesButton.click()
        if not go(sleep=0.5):
            return  # wait long enough for samples to generate
        w.doneButton.click()


def uq_sampling_scheme_LH(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup up an ensemble sampling scheme with Latin Hypercube, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "Latin Hypercube/Triangle Distribution"
    if "SimSetup" in str(type(w)):
        timers["uq_sampling_scheme_LH"].stop()
        w.distTable.cellWidget(1, 1).setCurrentIndex(1)
        ### ----------------------------------------------------------------------
        # Triangle Distribution
        w.distTable.cellWidget(0, 5).setCurrentIndex(3)
        w.distTable.cellWidget(0, 6).setItem(0, 1, QtWidgets.QTableWidgetItem("1"))
        w.distTable.cellWidget(0, 7).setItem(0, 1, QtWidgets.QTableWidgetItem("2"))
        ### ----------------------------------------------------------------------
        w.samplingTabs.setCurrentIndex(1)
        items = w.schemesList.findItems("Latin Hypercube", QtCore.Qt.MatchExactly)
        w.schemesList.setCurrentItem(items[0])
        w.numSamplesBox.setValue(100)
        w.generateSamplesButton.click()
        if not go(sleep=0.5):
            return  # wait long enough for samples to generate
        w.doneButton.click()


def uq_sampling_scheme_OA(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup up an ensemble sampling scheme with Orthogonal Array, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "Orthogonal Array/Gamma Distribution"
    if "SimSetup" in str(type(w)):
        timers["uq_sampling_scheme_OA"].stop()
        w.distTable.cellWidget(1, 1).setCurrentIndex(1)
        ### ----------------------------------------------------------------------
        # Gamma Distribution
        w.distTable.cellWidget(0, 5).setCurrentIndex(4)
        w.distTable.cellWidget(0, 6).setItem(0, 1, QtWidgets.QTableWidgetItem("1"))
        w.distTable.cellWidget(0, 7).setItem(0, 1, QtWidgets.QTableWidgetItem("2"))
        ### ----------------------------------------------------------------------
        w.samplingTabs.setCurrentIndex(1)
        items = w.schemesList.findItems("Orthogonal Array", QtCore.Qt.MatchExactly)
        w.schemesList.setCurrentItem(items[0])
        w.numSamplesBox.setValue(99)
        w.generateSamplesButton.click()
        if not go(sleep=0.5):
            return  # wait long enough for samples to generate
        w.doneButton.click()


def uq_sampling_scheme_MD(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup up an ensemble sampling scheme with Morris Design, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "Morris Design/Beta Distribution"
    if "SimSetup" in str(type(w)):
        timers["uq_sampling_scheme_MD"].stop()
        w.distTable.cellWidget(1, 1).setCurrentIndex(1)
        ### ---------------------------------------------------------------------- # Doesn't work
        # Beta Distribution
        w.distTable.cellWidget(0, 5).setCurrentIndex(5)
        w.distTable.setItem(0, 3, QtWidgets.QTableWidgetItem("0"))
        w.distTable.setItem(0, 4, QtWidgets.QTableWidgetItem("1"))
        w.distTable.cellWidget(0, 6).setItem(0, 1, QtWidgets.QTableWidgetItem("1"))
        w.distTable.cellWidget(0, 7).setItem(0, 1, QtWidgets.QTableWidgetItem("2"))
        ### ----------------------------------------------------------------------
        w.samplingTabs.setCurrentIndex(1)
        items = w.schemesList.findItems("Morris Design", QtCore.Qt.MatchExactly)
        w.schemesList.setCurrentItem(items[0])
        w.numSamplesBox.setValue(99)
        w.generateSamplesButton.click()
        if not go(sleep=0.5):
            return  # wait long enough for samples to generate
        w.doneButton.click()


def uq_sampling_scheme_GMD(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup up an ensemble sampling scheme with Generalized Morris Design, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "Generalized Morris Design/Exponential Distribution"
    if "SimSetup" in str(type(w)):
        timers["uq_sampling_scheme_GMD"].stop()
        w.distTable.cellWidget(1, 1).setCurrentIndex(1)
        ### ---------------------------------------------------------------------- # Doesn't work
        # Exponential Distribution
        w.distTable.cellWidget(0, 5).setCurrentIndex(6)
        w.distTable.setItem(0, 3, QtWidgets.QTableWidgetItem("0"))
        w.distTable.cellWidget(0, 6).setItem(0, 1, QtWidgets.QTableWidgetItem("1"))
        ### ----------------------------------------------------------------------
        w.samplingTabs.setCurrentIndex(1)
        items = w.schemesList.findItems(
            "Generalized Morris Design", QtCore.Qt.MatchExactly
        )
        w.schemesList.setCurrentItem(items[0])
        w.numSamplesBox.setValue(99)
        w.generateSamplesButton.click()
        if not go(sleep=0.5):
            return  # wait long enough for samples to generate
        w.doneButton.click()


def uq_sampling_scheme_GS(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Setup up an ensemble sampling scheme with Gradient Sample, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "Gradient Sample/Weibull Distribution"
    if "SimSetup" in str(type(w)):
        timers["uq_sampling_scheme_GS"].stop()
        w.distTable.cellWidget(1, 1).setCurrentIndex(1)
        ### ----------------------------------------------------------------------
        # Weibull Distribution
        w.distTable.cellWidget(0, 5).setCurrentIndex(7)
        w.distTable.cellWidget(0, 6).setItem(0, 1, QtWidgets.QTableWidgetItem("0.5"))
        w.distTable.cellWidget(0, 7).setItem(0, 1, QtWidgets.QTableWidgetItem("0.5"))
        ### ----------------------------------------------------------------------
        w.samplingTabs.setCurrentIndex(1)
        items = w.schemesList.findItems("Gradient Sample", QtCore.Qt.MatchExactly)
        w.schemesList.setCurrentItem(items[0])
        w.numSamplesBox.setValue(3)
        w.generateSamplesButton.click()
        if not go(sleep=0.5):
            return  # wait long enough for samples to generate
        w.doneButton.click()


def uq_sampling_scheme_METIS(
    MainWin=MainWin, getButton=getButton, timers=timers, go=go
):
    """Setup up an ensemble sampling scheme with METIS, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "METIS"
    if "SimSetup" in str(type(w)):
        timers["uq_sampling_scheme_METIS"].stop()
        w.distTable.cellWidget(1, 1).setCurrentIndex(1)
        w.samplingTabs.setCurrentIndex(1)
        items = w.schemesList.findItems("METIS", QtCore.Qt.MatchExactly)
        w.schemesList.setCurrentItem(items[0])
        w.numSamplesBox.setValue(100)
        w.generateSamplesButton.click()
        if not go(sleep=0.5):
            return  # wait long enough for samples to generate
        w.doneButton.click()


def filter_scheme(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Open the Filters Dialog Box"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "filter_scheme"
    if "dataBrowserDialog" in str(type(w)):
        timers["filter_scheme"].stop()
        w.dataFrame.editFiltersButton.click()


#        return


def new_filter_scheme(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Adds a new filter, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "new_filter_scheme"
    if "dataFilterDialog" in str(type(w)):
        timers["new_filter_scheme"].stop()
        w.addFilter()


def filter_text_scheme(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Sets the new filter name and closes the window, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "filter_text_scheme"
    if isinstance(w, QtWidgets.QInputDialog):
        w.setTextValue("Result")
        timers["filter_text_scheme"].stop()
        w.done(1)


def add_result_scheme(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Adds the sort term into the dialog box and opens the add new filter box, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "add_result_scheme"
    if "dataFilterDialog" in str(type(w)):
        timers["add_result_scheme"].stop()
        w.sortCheck.toggle()
        w.enableSortTerm()
        w.sortTermEdit.setText('["-result"]')
        w.addFilter()


def filter_scheme_2(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Open the Filters Dialog Box"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "filter_scheme_2"
    if "dataBrowserDialog" in str(type(w)):
        timers["filter_scheme_2"].stop()
        w.dataFrame.editFiltersButton.click()


#        return


def new_filter_scheme_2(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Adds a new filter, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "new_filter_scheme_2"
    if "dataFilterDialog" in str(type(w)):
        timers["new_filter_scheme_2"].stop()
        w.addFilter()


def filter_text_scheme_2(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Sets the new filter name and closes the window, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "filter_text_scheme_2"
    if isinstance(w, QtWidgets.QInputDialog):
        w.setTextValue("ResultAndError")
        timers["filter_text_scheme_2"].stop()
        w.done(1)


def filter_text_scheme_3(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Sets the new filter name and closes the window, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "filter_text_scheme_3"
    if isinstance(w, QtWidgets.QInputDialog):
        w.setTextValue("Operation")
        timers["filter_text_scheme_3"].stop()
        w.done(1)


def add_result_scheme_2(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Adds the sort term into the dialog box and opens the add new filter box, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "add_result_scheme_2"
    if "dataFilterDialog" in str(type(w)):
        timers["add_result_scheme_2"].stop()
        w.sortTermEdit.setText('["err","-result"]')
        w.addFilter()


def operation_scheme(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Adds two conditions for sorting and adds an additional filter, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "operation_scheme"
    if "dataFilterDialog" in str(type(w)):
        timers["operation_scheme"].stop()
        w.addRuleButton.click()
        w.addOpButton.click()
        w.addRuleButton.click()
        w.sortCheck.toggle()
        w.enableSortTerm()
        table = w.ruleTable
        row1Items = [table.takeItem(0, 0), table.cellWidget(0, 1), table.takeItem(0, 2)]
        row1Items[0].setText("output.calc.z")
        row1Items[2].setText("-0.5")
        table.setItem(0, 0, row1Items[0])
        table.setItem(0, 2, row1Items[2])
        w.ruleTable.cellWidget(0, 1).setCurrentIndex(5)
        w.ruleTable.cellWidget(1, 1).setCurrentIndex(1)
        w.addFilter()


def filter_text_scheme_4(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Sets the new filter name and closes the window, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "filter_text_scheme_4"
    if isinstance(w, QtWidgets.QInputDialog):
        w.setTextValue("Operation_4")
        timers["filter_text_scheme_4"].stop()
        w.done(1)


def filter_scheme_4(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Adds one condition for sorting and adds an additional filter, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "filter_scheme_4"
    if "dataFilterDialog" in str(type(w)):
        timers["filter_scheme_4"].stop()
        w.addRuleButton.click()
        table = w.ruleTable
        row1Items = [table.takeItem(0, 0), table.cellWidget(0, 1), table.takeItem(0, 2)]
        row1Items[0].setText("input.calc.x3")
        row1Items[2].setText("0.0")
        table.setItem(0, 0, row1Items[0])
        table.setItem(0, 2, row1Items[2])
        w.ruleTable.cellWidget(0, 1).setCurrentIndex(4)
        w.addFilter()


def filter_text_scheme_5(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Sets the new filter name and closes the window, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "filter_text_scheme_5"
    if isinstance(w, QtWidgets.QInputDialog):
        w.setTextValue("Operation_5")
        timers["filter_text_scheme_5"].stop()
        w.done(1)


def filter_scheme_5(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Adds one condition for sorting and adds an additional filter, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "filter_scheme_5"
    if "dataFilterDialog" in str(type(w)):
        timers["filter_scheme_5"].stop()
        w.addRuleButton.click()
        table = w.ruleTable
        row1Items = [table.takeItem(0, 0), table.cellWidget(0, 1), table.takeItem(0, 2)]
        row1Items[0].setText("solution_time")
        row1Items[2].setText("0.0")
        table.setItem(0, 0, row1Items[0])
        table.setItem(0, 2, row1Items[2])
        w.ruleTable.cellWidget(0, 1).setCurrentIndex(3)
        w.addFilter()


def filter_text_scheme_6(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Sets the new filter name and closes the window, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "filter_text_scheme_6"
    if isinstance(w, QtWidgets.QInputDialog):
        w.setTextValue("Operation_6")
        timers["filter_text_scheme_6"].stop()
        w.done(1)


def filter_scheme_6(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Adds one condition for sorting and adds an additional filter, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "filter_scheme_6"
    if "dataFilterDialog" in str(type(w)):
        timers["filter_scheme_6"].stop()
        w.addRuleButton.click()
        table = w.ruleTable
        row1Items = [table.takeItem(0, 0), table.cellWidget(0, 1), table.takeItem(0, 2)]
        row1Items[0].setText("input.calc.x1")
        row1Items[2].setText("0.0")
        table.setItem(0, 0, row1Items[0])
        table.setItem(0, 2, row1Items[2])
        w.ruleTable.cellWidget(0, 1).setCurrentIndex(2)
        w.addFilter()


def filter_text_scheme_7(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Sets the new filter name and closes the window, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "filter_text_scheme_7"
    if isinstance(w, QtWidgets.QInputDialog):
        w.setTextValue("Operation_7")
        timers["filter_text_scheme_7"].stop()
        w.done(1)


def filter_scheme_7(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Adds one condition for sorting and adds an additional filter, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "filter_scheme_7"
    if "dataFilterDialog" in str(type(w)):
        timers["filter_scheme_7"].stop()
        w.addRuleButton.click()
        table = w.ruleTable
        row1Items = [table.takeItem(0, 0), table.cellWidget(0, 1), table.takeItem(0, 2)]
        row1Items[0].setText("err")
        row1Items[2].setText("0.0")
        table.setItem(0, 0, row1Items[0])
        table.setItem(0, 2, row1Items[2])
        w.ruleTable.cellWidget(0, 1).setCurrentIndex(1)
        w.addFilter()


def filter_text_scheme_8(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Sets the new filter name and closes the window, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "filter_text_scheme_8"
    if isinstance(w, QtWidgets.QInputDialog):
        w.setTextValue("Operation_8")
        timers["filter_text_scheme_8"].stop()
        w.done(1)


def filter_scheme_8(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Adds one condition for sorting and adds an additional filter, stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "filter_scheme_8"
    if "dataFilterDialog" in str(type(w)):
        timers["filter_scheme_8"].stop()
        w.addRuleButton.click()
        table = w.ruleTable
        row1Items = [table.takeItem(0, 0), table.cellWidget(0, 1), table.takeItem(0, 2)]
        row1Items[0].setText("err")
        row1Items[2].setText("1.0")
        table.setItem(0, 0, row1Items[0])
        table.setItem(0, 2, row1Items[2])
        w.ruleTable.cellWidget(0, 1).setCurrentIndex(1)
        w.doneButton.click()


def fs_scheme(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Cycles through all of the , stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "fs_scheme"
    if "dataBrowserDialog" in str(type(w)):
        timers["fs_scheme"].stop()
        w.dataFrame.filterSelectBox.setCurrentIndex(
            1
        )  # This one currently doesn't work
        w.dataFrame.filterSelectBox.setCurrentIndex(2)
        w.dataFrame.filterSelectBox.setCurrentIndex(3)
        w.dataFrame.filterSelectBox.setCurrentIndex(4)
        w.dataFrame.filterSelectBox.setCurrentIndex(5)
        w.dataFrame.filterSelectBox.setCurrentIndex(6)
        w.dataFrame.filterSelectBox.setCurrentIndex(7)
        w.dataFrame.filterSelectBox.setCurrentIndex(8)
        w.dataFrame.filterSelectBox.setCurrentIndex(9)
        w.dataFrame.filterSelectBox.setCurrentIndex(10)
        w.close()


def apply_filter_scheme(MainWin=MainWin, getButton=getButton, timers=timers, go=go):
    """Cycles through all of the , stops timer once window comes up"""
    w = MainWin.app.activeWindow()
    global errorTitle
    errorTitle = "apply_filter_scheme"
    if "dataBrowserDialog" in str(type(w)):
        timers["apply_filter_scheme"].stop()
        w.dataFrame.filterSelectBox.setCurrentIndex(
            1
        )  # This one currently doesn't work
        w.dataFrame.filterSelectBox.setCurrentIndex(2)
        w.dataFrame.filterSelectBox.setCurrentIndex(3)
        w.dataFrame.filterSelectBox.setCurrentIndex(4)
        w.dataFrame.filterSelectBox.setCurrentIndex(5)
        w.dataFrame.filterSelectBox.setCurrentIndex(6)
        w.dataFrame.filterSelectBox.setCurrentIndex(7)
        w.dataFrame.filterSelectBox.setCurrentIndex(8)
        w.dataFrame.filterSelectBox.setCurrentIndex(9)
        w.dataFrame.filterSelectBox.setCurrentIndex(10)
        w.close()


def addTimer(name, cb, MainWin=MainWin, timers=timers):
    """Add a timer to do something.  Timers are needed because some things like
    a modal dialog box will hold up executaion on the main UI thread, so a timer
    can be used to do something while execution of this script is held up.

    Args:
        name: string name of timer
        cb: timer call back function (timer should stop itself once it's done)
    """
    timers[name] = QtCore.QTimer(MainWin)
    timers[name].timeout.connect(cb)


def timersStop(timers=timers):
    """Stop all timers"""
    for key, t in timers.items():
        t.stop()


def timerWait(timer, sleep=0.25, n=40, go=go, timers=timers, tf=testOutFile):
    """Wait sleep*n seconds for timer to finish its job."""
    for i in range(n):
        if not go(sleep=sleep):
            return False
        if not timers[timer].isActive():
            return True
    timers[timer].stop()  # Timer never did it's thing so just shut it down
    with open(tf, "a") as f:  # file to write test results to
        f.write("ERROR: timer {} didn't stop in allotted time\n".format(timer))
    return False  # return False to stop script.  Something is wrong


# make the timers that will be needed just start and stop as needed
# need to make sure that when this script exits all timers are stopped
# or some crazy stuff may happen until you exit FOQUS.
addTimer("time_out", MainWin.helpDock.setStopTrue)  # stop script if too long
addTimer("msg_okay", msg_okay)  # click OK on mgsbox
addTimer("msg_no", msg_no)  # click No on msgbox
addTimer("add_UQ_cancel", add_UQ_cancel)  # click cancel on uq ensemble dialog
addTimer("add_UQ_okay", add_UQ_okay)  # click okay on uq ensemble dialog
addTimer("Error_okay", Error_okay)  # click okay on uq ensemble dialog
addTimer("Error_okay_text", Error_okay_text)  # click okay on uq ensemble dialog
addTimer("add_UQ_yes", add_UQ_yes)  # click yes on uq ensemble dialog
addTimer("uq_sampling_scheme_MC", uq_sampling_scheme_MC)  # do sampling scheme dialog
addTimer("uq_sampling_scheme_QMC", uq_sampling_scheme_QMC)  # do sampling scheme dialog
addTimer("uq_sampling_scheme_LH", uq_sampling_scheme_LH)  # do sampling scheme dialog
addTimer("uq_sampling_scheme_OA", uq_sampling_scheme_OA)  # do sampling scheme dialog
addTimer("uq_sampling_scheme_MD", uq_sampling_scheme_MD)  # do sampling scheme dialog
addTimer("uq_sampling_scheme_GMD", uq_sampling_scheme_GMD)  # do sampling scheme dialog
addTimer("uq_sampling_scheme_GS", uq_sampling_scheme_GS)  # do sampling scheme dialog
addTimer(
    "uq_sampling_scheme_METIS", uq_sampling_scheme_METIS
)  # do sampling scheme dialog
addTimer("filter_scheme", filter_scheme)  # do analysis scheme dialog
addTimer("new_filter_scheme", new_filter_scheme)  # do analysis scheme dialog
addTimer("filter_text_scheme", filter_text_scheme)  # do analysis scheme dialog
addTimer("add_result_scheme", add_result_scheme)  # do analysis scheme dialog
addTimer("filter_scheme_2", filter_scheme_2)  # do analysis scheme dialog
addTimer("new_filter_scheme_2", new_filter_scheme_2)  # do analysis scheme dialog
addTimer("filter_text_scheme_2", filter_text_scheme_2)  # do analysis scheme dialog
addTimer("filter_text_scheme_3", filter_text_scheme_3)  # do analysis scheme dialog
addTimer("add_result_scheme_2", add_result_scheme_2)  # do analysis scheme dialog
addTimer("operation_scheme", operation_scheme)  # do analysis scheme dialog
addTimer("filter_text_scheme_4", filter_text_scheme_4)  # do analysis scheme dialog
addTimer("filter_scheme_4", filter_scheme_4)  # do analysis scheme dialog
addTimer("filter_text_scheme_5", filter_text_scheme_5)  # do analysis scheme dialog
addTimer("filter_scheme_5", filter_scheme_5)  # do analysis scheme dialog
addTimer("filter_text_scheme_6", filter_text_scheme_6)  # do analysis scheme dialog
addTimer("filter_scheme_6", filter_scheme_6)  # do analysis scheme dialog
addTimer("filter_text_scheme_7", filter_text_scheme_7)  # do analysis scheme dialog
addTimer("filter_scheme_7", filter_scheme_7)  # do analysis scheme dialog
addTimer("filter_text_scheme_8", filter_text_scheme_8)  # do analysis scheme dialog
addTimer("filter_scheme_8", filter_scheme_8)  # do analysis scheme dialog
addTimer("apply_filter_scheme", apply_filter_scheme)  # do analysis scheme dialog
addTimer("fs_scheme", fs_scheme)  # do analysis scheme dialog

timers["time_out"].start(MAX_RUN_TIME)  # start max script time timer

try:  # Catch any exception and stop all timers before finishing up
    while 1:  # Loop and break and break as convenient way to jump to end
        # Simple Flowsheet setup
        MainWin.homeAction.trigger()
        if not go():
            break
        # Enter some information
        MainWin.dashFrame.sessionNameEdit.setText("Simple Flowsheet")
        if not go():
            break
        MainWin.dashFrame.tabWidget.setCurrentIndex(1)
        if not go():
            break
        MainWin.dashFrame.setSessionDescription("Simple Flowsheet Description Text")
        if not go():
            break
        # Make a flowsheet
        MainWin.fsEditAction.trigger()
        if not go():
            break
        MainWin.addNodeAction.trigger()
        if not go():
            break
        MainWin.flowsheetEditor.sc.mousePressEvent(
            None, dbg_x=10, dbg_y=10, dbg_name="calc"
        )
        if not go():
            break
        MainWin.toggleNodeEditorAction.trigger()
        if not go():
            break
        MainWin.nodeDock.addInput("x1")
        MainWin.nodeDock.addInput("x2")
        MainWin.nodeDock.addInput("x3")
        MainWin.nodeDock.inputVarTable.item(0, 5).setText("-2")
        MainWin.nodeDock.inputVarTable.item(0, 6).setText("30")
        MainWin.nodeDock.inputVarTable.item(1, 5).setText("-1")
        MainWin.nodeDock.inputVarTable.item(1, 6).setText("4")
        MainWin.nodeDock.inputVarTable.item(2, 5).setText("-3")
        MainWin.nodeDock.inputVarTable.item(2, 6).setText("6")
        MainWin.nodeDock.inputVarTable.item(0, 4).setText("1")
        MainWin.nodeDock.inputVarTable.item(1, 4).setText("3")
        MainWin.nodeDock.inputVarTable.item(2, 4).setText("-2")
        MainWin.nodeDock.inputVarTable.item(0, 1).setText("1")
        MainWin.nodeDock.inputVarTable.item(1, 1).setText("3")
        MainWin.nodeDock.inputVarTable.item(2, 1).setText("-2")
        MainWin.nodeDock.toolBox.setCurrentIndex(1)
        MainWin.nodeDock.addOutput("z")
        MainWin.nodeDock.tabWidget.setCurrentIndex(2)
        MainWin.nodeDock.pyCode.setPlainText("f.z = x.x1*math.sqrt(x.x2)/x.x3")
        MainWin.nodeDock.tabWidget.setCurrentIndex(0)
        if not go():
            break
        MainWin.centerAction.trigger()
        # Before running start up a timer to close completed run msgbox
        timers["msg_okay"].start(500)  # timer to push ok on a msgbox if up
        MainWin.runAction.trigger()  # run flowsheet
        while MainWin.singleRun.is_alive():
            if not go():
                MainWin.singleRun.terminate()
                break
        if not timerWait("msg_okay"):
            break
        MainWin.uqSetupAction.trigger()
        if not go():
            break

        # Add the sampling schemes
        ## -----------------Start Error Monitoring----------------------------
        timers["Error_okay"].start(1000)
        timers["Error_okay_text"].start(1000)
        ## -------------------------------------------------------------------

        timers["add_UQ_okay"].start(1000)
        timers["uq_sampling_scheme_MC"].start(500)
        MainWin.uqSetupFrame.addSimulationButton.click()
        if not timerWait("add_UQ_okay"):
            break
        if not timerWait("uq_sampling_scheme_MC"):
            break

        timers["add_UQ_okay"].start(1000)
        timers["uq_sampling_scheme_QMC"].start(500)
        MainWin.uqSetupFrame.addSimulationButton.click()
        if not timerWait("add_UQ_okay"):
            break
        if not timerWait("uq_sampling_scheme_QMC"):
            break

        timers["add_UQ_okay"].start(1000)
        timers["uq_sampling_scheme_LH"].start(500)
        MainWin.uqSetupFrame.addSimulationButton.click()
        if not timerWait("add_UQ_okay"):
            break
        if not timerWait("uq_sampling_scheme_LH"):
            break

        #        timers['add_UQ_okay'].start(1000)
        #        timers['uq_sampling_scheme_OA'].start(500) #The code currently complains about some q=10 not being a prime power
        #        MainWin.uqSetupFrame.addSimulationButton.click()
        #        if not timerWait('add_UQ_okay'): break
        #        if not timerWait('uq_sampling_scheme_OA'): break

        timers["add_UQ_okay"].start(1000)
        timers["uq_sampling_scheme_MD"].start(500)
        MainWin.uqSetupFrame.addSimulationButton.click()
        if not timerWait("add_UQ_okay"):
            break
        if not timerWait("uq_sampling_scheme_MD"):
            break

        timers["add_UQ_okay"].start(1000)
        timers["uq_sampling_scheme_GMD"].start(500)
        MainWin.uqSetupFrame.addSimulationButton.click()
        if not timerWait("add_UQ_okay"):
            break
        if not timerWait("uq_sampling_scheme_GMD"):
            break

        #        timers['add_UQ_okay'].start(1000)
        #        timers['uq_sampling_scheme_GS'].start(500) #Requires at least 9 variables to do this without
        #        MainWin.uqSetupFrame.addSimulationButton.click()
        #        if not timerWait('add_UQ_okay'): break
        #        if not timerWait('uq_sampling_scheme_GS'): break

        timers["add_UQ_okay"].start(1000)
        timers["uq_sampling_scheme_METIS"].start(500)
        MainWin.uqSetupFrame.addSimulationButton.click()
        if not timerWait("add_UQ_okay"):
            break
        if not timerWait("uq_sampling_scheme_METIS"):
            break

        # Run UQ ensembles
        try:
            MainWin.uqSetupFrame.simulationTable.cellWidget(0, 3).click()
            timers["msg_okay"].start(500)  # press okay on ensemble done msgbox
            while MainWin.uqSetupFrame.gThread.isAlive():  # while is running
                if not go():
                    MainWin.uqSetupFrame.gThread.terminate()
                    break
            if not timerWait("msg_okay"):
                break
        except Exception:
            None
        try:
            MainWin.uqSetupFrame.simulationTable.cellWidget(1, 3).click()
            timers["msg_okay"].start(500)  # press okay on ensemble done msgbox
            while MainWin.uqSetupFrame.gThread.isAlive():  # while is running
                if not go():
                    MainWin.uqSetupFrame.gThread.terminate()
                    break
            if not timerWait("msg_okay"):
                break
        except Exception:
            None
        try:
            MainWin.uqSetupFrame.simulationTable.cellWidget(2, 3).click()
            timers["msg_okay"].start(500)  # press okay on ensemble done msgbox
            while MainWin.uqSetupFrame.gThread.isAlive():  # while is running
                if not go():
                    MainWin.uqSetupFrame.gThread.terminate()
                    break
            if not timerWait("msg_okay"):
                break
        except Exception:
            None
        try:
            MainWin.uqSetupFrame.simulationTable.cellWidget(3, 3).click()
            timers["msg_okay"].start(500)  # press okay on ensemble done msgbox
            while MainWin.uqSetupFrame.gThread.isAlive():  # while is running
                if not go():
                    MainWin.uqSetupFrame.gThread.terminate()
                    break
            if not timerWait("msg_okay"):
                break
        except Exception:
            None
        try:
            MainWin.uqSetupFrame.simulationTable.cellWidget(4, 3).click()
            timers["msg_okay"].start(500)  # press okay on ensemble done msgbox
            while MainWin.uqSetupFrame.gThread.isAlive():  # while is running
                if not go():
                    MainWin.uqSetupFrame.gThread.terminate()
                    break
            if not timerWait("msg_okay"):
                break
        except Exception:
            None
        try:
            MainWin.uqSetupFrame.simulationTable.cellWidget(5, 3).click()
            timers["msg_okay"].start(500)  # press okay on ensemble done msgbox
            while MainWin.uqSetupFrame.gThread.isAlive():  # while is running
                if not go():
                    MainWin.uqSetupFrame.gThread.terminate()
                    break
            if not timerWait("msg_okay"):
                break
        except Exception:
            None
        #        MainWin.uqSetupFrame.simulationTable.cellWidget(6,3).click()
        #        timers['msg_okay'].start(500) # press okay on ensemble done msgbox
        #        while MainWin.uqSetupFrame.gThread.isAlive(): # while is running
        #            if not go():
        #                MainWin.uqSetupFrame.gThread.terminate()
        #                break
        #        if not timerWait('msg_okay'): break
        #
        #        MainWin.uqSetupFrame.simulationTable.cellWidget(7,3).click()
        #        timers['msg_okay'].start(500) # press okay on ensemble done msgbox
        #        while MainWin.uqSetupFrame.gThread.isAlive(): # while is running
        #            if not go():
        #                MainWin.uqSetupFrame.gThread.terminate()
        #                break
        #        if not timerWait('msg_okay'): break

        MainWin.fsEditAction.trigger()
        if not go():
            break

        MainWin.dataBrowserAction.trigger()
        if not go():
            break

        timers["apply_filter_scheme"].start(500)
        timers["filter_scheme_8"].start(500)
        timers["filter_text_scheme_8"].start(500)
        timers["filter_scheme_7"].start(500)
        timers["filter_text_scheme_7"].start(500)
        timers["filter_scheme_6"].start(500)
        timers["filter_text_scheme_6"].start(500)
        timers["filter_scheme_5"].start(500)
        timers["filter_text_scheme_5"].start(500)
        timers["filter_scheme_4"].start(500)
        timers["filter_text_scheme_4"].start(500)
        timers["operation_scheme"].start(500)
        timers["filter_text_scheme_3"].start(500)
        timers["add_result_scheme_2"].start(500)
        timers["filter_text_scheme_2"].start(500)
        timers["add_result_scheme"].start(500)
        timers["filter_text_scheme"].start(500)
        timers["new_filter_scheme"].start(500)
        timers["filter_scheme"].start(500)
        if not timerWait("filter_scheme"):
            break
        if not timerWait("new_filter_scheme"):
            break
        if not timerWait("filter_text_scheme"):
            break
        if not timerWait("add_result_scheme"):
            break
        if not timerWait("filter_text_scheme_2"):
            break
        if not timerWait("add_result_scheme_2"):
            break
        if not timerWait("filter_text_scheme_3"):
            break
        if not timerWait("operation_scheme"):
            break
        if not timerWait("filter_text_scheme_4"):
            break
        if not timerWait("filter_scheme_4"):
            break
        if not timerWait("filter_text_scheme_5"):
            break
        if not timerWait("filter_scheme_5"):
            break
        if not timerWait("filter_text_scheme_6"):
            break
        if not timerWait("filter_scheme_6"):
            break
        if not timerWait("filter_text_scheme_7"):
            break
        if not timerWait("filter_scheme_7"):
            break
        if not timerWait("filter_text_scheme_8"):
            break
        if not timerWait("filter_scheme_8"):
            break
        if not timerWait("apply_filter_scheme"):
            break

        ## -----------------Stop Error Monitoring----------------------------
        if not timerWait("Error_okay"):
            break
        if not timerWait("Error_okay_text"):
            break
        ## -------------------------------------------------------------------

        #        timers['fs_scheme'].start(500)
        #        if not timerWait('fs_scheme'): break

        break
except Exception as e:
    # if there is any exception make sure the timers are stopped
    # before reraising it
    print("Exception stopping script")
    timersStop()
    with open(testOutFile, "a") as f:
        f.write("ERROR: Exception: {0}\n".format(e))
timersStop()  # make sure all timers are stopped

# Try to close FOQUS
timers["msg_no"].start(1000)
MainWin.close()
timerWait("msg_no")
print("Exited Code: fs_smoke_test.py")
