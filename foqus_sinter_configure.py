#################################################################################
# FOQUS Copyright (c) 2012 - 2025, by the software owners: Oak Ridge Institute
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
Prototype SimSinter Configuration Writer, at this point focusing on gPROMS.
"""
import sys
from PyQt5.QtWidgets import QApplication
from foqus_lib.gui.sinter import SinterConfigMainWindow

if __name__ == "__main__":
    print("gPROMS SimSinter Configuration File Writer...")
    app = QApplication(sys.argv)
    mainWin = SinterConfigMainWindow("SinterConfigEditor", 1024, 768)
    app.exec_()
    print("...goodbye.")
