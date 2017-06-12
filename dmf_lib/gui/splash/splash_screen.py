from PySide.QtGui import *
from PySide.QtCore import *

class SplashScreen(QSplashScreen):

    def __init__(self, pixmap, parent=None):
        QSplashScreen.__init__(self, pixmap)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

    def mousePressEvent(self, mouseEvent):
        # Ignore mouse press events
        pass
