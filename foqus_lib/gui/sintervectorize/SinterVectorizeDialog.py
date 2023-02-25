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
"""SinterVectorizeDialog.py
* dialog to vectorize SimSinter (.json) files
"""
import json
import os
import sys
import subprocess
import logging
import foqus_lib.gui.helpers.guiHelpers as gh
import foqus_lib.framework.sintervectorize.SinterFileVectorize as sv
from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import (
    QMessageBox,
    QDialog,
    QInputDialog,
    QFileDialog,
    QLineEdit,
    QTextEdit,
)

mypath = os.path.dirname(__file__)
_SinterVectorizeDialogUI, _SinterVectorizeDialog = uic.loadUiType(
    os.path.join(mypath, "SinterVectorizeDialog_UI.ui")
)


class SinterVectorizeDialog(_SinterVectorizeDialog, _SinterVectorizeDialogUI):
    """
        This class provides a dialog box that allows you to vectorize a \
        SinSinter json file.
    """

    waiting = QtCore.pyqtSignal()  # signal for start waiting on long task
    notwaiting = QtCore.pyqtSignal()  # signal the task is done

    def __init__(self, parent=None):
        """
        Initialize dialog
        """
        super(SinterVectorizeDialog, self).__init__(parent=parent)
        self.setupUi(self)
        # Connect buttons
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def accept(self):
        """
        Vectorize the SimSinter file
        """
        # Get required text
        json_file = self.sinterfile.toPlainText()
        input_vectors = self.inputvectordetails.toPlainText()
        output_vectors = self.outputvectordetails.toPlainText()
        vectorized_json_file = self.sinterfilevector.toPlainText()
        sv.sintervectorize(
            json_file, input_vectors, output_vectors, vectorized_json_file
        )
        self.done(QDialog.Accepted)

    def reject(self):
        """
        If cancel just do nothing and close dialog
        """
        self.done(QDialog.Rejected)
