import os
from PyQt5 import uic
import hashlib

mypath = os.path.dirname(__file__)
_sinterConfigUI, _sinterConfig = \
        uic.loadUiType(os.path.join(mypath, "sinter_config.ui"))

class SinterConfigMainWindow(_sinterConfigUI, _sinterConfig):
    def __init__(self, parent=None,
        title="SimSinter Configuration editor", width=800, height=600):
        super().__init__(parent=None)
        self.setupUi(self)
        self.show()
