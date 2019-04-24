"""
Prototype SimSinter Confiuration Writer, at this point focusing on gPROMS.
"""
import sys
from PyQt5.QtWidgets import QApplication
from foqus_lib.gui.sinter import SinterConfigMainWindow

if __name__ == '__main__':
    print("gPROMS SimSinter Configuration File Writer...")
    app = QApplication(sys.argv)
    mainWin = SinterConfigMainWindow("SinterConfigEditor", 1024, 768)
    app.exec_()
    print("...goodbye.")
