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
""" #FOQUS_SURROGATE_PLUGIN

Surrogate plugins need to have the string "#FOQUS_SURROGATE_PLUGIN" near the
begining of the file (see pluginSearch.plugins() for exact character count of
text).  They also need to have a .py extension and inherit the surrogate class.

* Plugin wrapper for the BSS-ANOVA surrogate model builer.
* BSS-ANOVA is excuted in R and a working R install with the quadprog
  package is required.  The user must install R
* BSS-ANOVA Ref:

John Eslick, Carnegie Mellon University, 2014
"""

import numpy as np
import threading
import queue
import logging
import subprocess
import os
import sys
import copy
import traceback
import time
import shutil
import re
import json
from foqus_lib.framework.surrogate.surrogate import surrogate
from foqus_lib.framework.uq.SurrogateParser import SurrogateParser
from foqus_lib.framework.listen import listen
from multiprocessing.connection import Client


def checkAvailable():
    """
    Plug-ins should have this function to check availability of any
    additional required software.  If requirements are not available
    plug-in will not be available.
    """
    # Need to check for R and quadprog?
    return True


class surrogateMethod(surrogate):
    metaDataJsonString = """
    "CCSIFileMetaData":{
        "ID":"uuid",
        "CreationTime":"",
        "ModificationTime":"",
        "ChangeLog":[],
        "DisplayName":"",
        "OriginalFilename":"",
        "Application":"foqus_surrogate_plugin",
        "Description":"BSS-ANOVA FOQUS Plugin",
        "MIMEType":"application/ccsi+foqus",
        "Confidence":"testing",
        "Parents":[],
        "UpdateMetadata":True,
        "Version":""}
    """
    name = "BSS-ANOVA"

    def __init__(self, dat=None):
        """
        BSS-ANOVA interface constructor
        """
        surrogate.__init__(self, dat)
        self.ex = None
        # Information about the method
        self.methodDescription = (
            "<html>"
            "<p>BSS-ANOVA:</p>"
            "<p>The Bayesian Smoothing Spline ANOVA (BSS-ANOVA) is"
            " essentially a Bayesian version of ACOSSO.  It is"
            " Gaussian Process (GP) model with a non-conventional"
            " covariance function that borrows its form from SS-ANOVA."
            " It tackles the high dimensionality (of inputs) on two"
            " fronts: (i) variable selection to eliminate"
            " uninformative variables from the model and (ii)"
            " restricting the level of interactions involved among"
            " the variables in the model. This is done through a"
            " fully Bayesian approach which can also allow for"
            " categorical input variables with relative ease."
            " Since it is closely related to ACOSSO, it generally"
            " works well in similar settings as ACOSSO.</p>"
            "</html>"
        )
        # bssanova working directory
        self.bssanovaDir = "bssanova"
        # add options
        self.options.add(
            name="Data Filter",
            default="all",
            dtype=str,
            desc="Filter for sample data, from flowsheet data",
            validValues=["All", "None"],
        )
        self.options.add(
            name="Use Flowsheet Data",
            default="Yes",
            dtype=str,
            desc="Use data from FOQUS flowsheet or provide csv files",
            validValues=["Yes", "No"],
        )
        self.options.add(
            name="Input Data File",
            default="bssanova" + os.path.sep + "xdat.csv",
            dtype=str,
            desc="csv file containing data for model inputs",
        )
        self.options.add(
            name="Output Data File",
            default="bssanova" + os.path.sep + "ydat.csv",
            dtype=str,
            desc="csv file containing data for model outputs",
        )
        # self.options.add(
        #    name="RScript path",
        #    default=\
        #        'C:\\Program Files\\R\\R-3.1.2\\bin\\x64\\Rscript.exe',
        #    dtype=str,
        #    desc="Full path the RScript executable")
        self.options.add(
            name="Model File",
            default="bssanova_fit.rds",
            dtype=str,
            desc="BSS-ANOVA output R data file",
        )
        self.options.add(
            name="FOQUS Model (for UQ)",
            default="bssanova_surrogate_uq.py",
            dtype=str,
            desc=".py file for UQ analysis",
        )
        self.options.add(
            name="FOQUS Model (for Flowsheet)",
            default="bssanova_surrogate_fs.py",
            dtype=str,
            desc=".py file flowsheet plugin, saved to user_plugins"
            " in the working directory",
        )
        self.options.add(
            name="Burn In",
            default=0,
            dtype=int,
            desc="Number of data point to ignore from begining",
        )
        self.options.add(
            name="MCMC Iterations",
            default=1000,
            dtype=int,
            desc="Total number of MCMC iterations",
        )
        self.options.add(
            name="Record Interval",
            default=1,
            dtype=int,
            desc="How often to record a sample",
        )
        self.options.add(
            name="nterms",
            default=25,
            dtype=int,
            desc="number of eigenvalues to use to approximate BSSA-NOVA" "covariance",
        )
        self.options.add(
            name="order",
            default=2,
            dtype=int,
            validValues=[1, 2],
            desc="order of interactions to consider covariance",
        )
        self.options.add(
            name="priorprob",
            default=0.5,
            dtype=float,
            desc="prior probability that a given component is" " uninformative",
        )

    def updateOptions(self):
        filters = sorted(
            list(self.dat.flowsheet.results.filters.keys()), key=lambda s: s.lower()
        )
        self.options["Data Filter"].validValues = filters

    def setupWorkingDir(self):
        adir = self.bssanovaDir
        self.createDir(adir)
        # Copy needed files
        dest = os.path.join(adir, "bssanova_fit.R")
        if not os.path.exists(dest):
            mydir = os.path.dirname(__file__)
            src = os.path.join(mydir, "bssanova/bssanova_fit.R")
            shutil.copyfile(src, dest)

    def run(self):
        """
        This function overloads the Thread class function,
        and is called when you run start() to start a new thread.
        """
        try:
            # Get options and show some information about settings
            adir = self.bssanovaDir
            self.setupWorkingDir()
            rscriptExe = self.dat.foqusSettings.rScriptPath
            xdata = self.options["Input Data File"].value
            ydata = self.options["Output Data File"].value
            burnin = self.options["Burn In"].value
            mcmcit = self.options["MCMC Iterations"].value
            recint = self.options["Record Interval"].value
            nterms = self.options["nterms"].value
            order = self.options["order"].value
            prior = self.options["priorprob"].value
            modelFile = self.options["Model File"].value
            driverFile = self.options["FOQUS Model (for UQ)"].value
            bte = json.dumps([burnin, mcmcit, recint])
            if self.checkNumVars():
                return
            self.msgQueue.put("------------------------------------")
            self.msgQueue.put("Starting BSS-ANOVA\n")
            self.msgQueue.put("Model File:      " + str(modelFile))
            self.msgQueue.put("Py File (UQ):    " + str(driverFile))
            self.msgQueue.put("RScript Path:    " + str(rscriptExe))
            self.msgQueue.put("Sub-directory:   " + str(adir))
            self.msgQueue.put("X data file:     " + str(xdata))
            self.msgQueue.put("Y data file:     " + str(ydata))
            self.msgQueue.put("Burn In:         " + str(burnin))
            self.msgQueue.put("MCMC Iterations: " + str(mcmcit))
            self.msgQueue.put("Record Interval: " + str(recint))
            self.msgQueue.put("N. Terms:        " + str(nterms))
            self.msgQueue.put("Order:           " + str(order))
            self.msgQueue.put("Prior Prob.:     " + str(prior))
            self.msgQueue.put("bte:             " + str(bte))
            self.msgQueue.put("------------------------------------")
            # Run the R script
            if self.options["Use Flowsheet Data"].value == "Yes":
                self.msgQueue.put("Exporting Data...")
                if len(self.input) < 1:
                    self.msgQueue.put("    Must select at least 2 input variables")
                    return
                self.msgQueue.put("    Inputs: {0}".format(json.dumps(self.input)))
                self.dat.flowsheet.results.exportVarsCSV(
                    xdata, inputs=self.input, outputs=[], flat=True
                )
                if len(self.output) < 1:
                    self.msgQueue.put("    Must select an output variable")
                    return
                self.msgQueue.put("    Output: {0}".format(json.dumps(self.output)))
                self.dat.flowsheet.results.exportVarsCSV(
                    ydata, inputs=[], outputs=self.output, flat=True
                )
            self.msgQueue.put("Running BSS-ANOVA...")
            rscriptFile = os.path.basename(rscriptExe)
            process = subprocess.Popen(
                [
                    rscriptFile,
                    "bssanova_fit.R",
                    os.path.abspath(xdata),
                    os.path.abspath(ydata),
                    modelFile,
                    bte,
                    "auto",
                    str(nterms),
                    str(order),
                    str(prior),
                ],
                executable=rscriptExe,
                cwd=adir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            line = process.stdout.readline()
            while process.poll() == None or line != b"":
                if line == b"":
                    time.sleep(0.2)
                if line != b"":
                    self.msgQueue.put(line.decode("utf-8").rstrip())
                line = process.stdout.readline()
                if self.stop.isSet():
                    self.msgQueue.put("**terminated by user**")
                    process.kill()
                    break
            self.msgQueue.put("Process completed code: {0}".format(process.poll()))
            line = process.stderr.readline()
            while line != b"":
                self.msgQueue.put(line.decode("utf-8").rstrip())
                line = process.stderr.readline()
            modelFile2 = os.path.join(adir, modelFile)
            driverFile2 = os.path.join(adir, driverFile)
            rfile = os.path.join(adir, "bssanova_pred.R")
            bssAnovaData = {
                "outputNames": self.output,  # assume univariate
                "modelNames": [modelFile2],
                "rscriptPath": rscriptExe,
                "rfile": rfile,
            }
            SurrogateParser.writeBssAnovaDriver(bssAnovaData, driverFile2)
            self.msgQueue.put("Wrote Python driver file: {0}".format(driverFile2))
            self.result = "Done, see Python driver file: {0}".format(driverFile2)
            self.driverFile = driverFile2
            self.writePlugin()  # added by BN, 2/4/2016
        except Exception:
            self.ex = sys.exc_info()
            logging.getLogger("foqus." + __name__).exception(
                "Exception in BSS-ANOVA Thread"
            )

    def writePlugin(self):  # added by BN, 2/4/2016
        file_name = self.options["FOQUS Model (for Flowsheet)"].value

        # Write the standard code top, then append "main()" from the UQ driver
        s = self.writePluginTop(
            method="BSS-ANOVA", comments=["BSS-ANOVA Flowsheet Model"]
        )
        with open(os.path.join("user_plugins", file_name), "w") as f:
            f.write(s)
            lines = []
            lines.append("")
            lines.append("    def run(self):")
            lines.append("")
            lines.append("        # write input file")
            lines.append("        infileName = 'bssanova_fs.in'")
            lines.append("        f = open(infileName,'w')")
            lines.append("        nx = %d" % len(self.input))
            lines.append("        f.write('1 %d\\n' % nx)")
            lines.append("        f.write('1 ')")
            lines.append("        for val in self.inputvals:")
            lines.append("            f.write('%f ' % val)")
            lines.append("        f.write('\\n')")
            lines.append("        f.close()")
            lines.append("")
            lines.append(
                "        # for each output, invoke UQ driver based on that output"
                "s trained model"
            )
            lines.append("        for i, vname in enumerate(self.outputs):")
            lines.append("            outfileName = 'bssanova_fs.out%d' % i")
            lines.append(
                "            p = subprocess.Popen(['python', r'%s', infileName, outfileName, '{0}'.format(i)],"
                % self.driverFile
            )
            lines.append(
                "                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)"
            )
            lines.append("            stdout, stderr = p.communicate()")
            lines.append("            if stdout:")
            lines.append("                print(stdout)")
            lines.append("            if stderr:")
            lines.append("                print(stderr)")
            lines.append("")
            lines.append("            # read results and instantiate output value")
            lines.append("            ypred = numpy.loadtxt(outfileName)")
            lines.append("            self.outputs[vname].value = ypred[1]")
            lines.append("")
            f.write("\n".join(lines))

        self.dat.reloadPlugins()
