import threading

from PySide.QtGui import QDialog
from PySide.QtGui import QLabel
from PySide.QtGui import QLayout
from PySide.QtGui import QPalette
from PySide.QtGui import QVBoxLayout
from PySide.QtCore import Qt
from PySide.QtCore import QThread
from PySide.QtCore import Signal
from dmf_lib.common.common import PRINT_COLON


class SaveFileHandlerDialog(QDialog):
    def __init__(
            self,
            parent,
            byte_array_stream,
            folder,
            display_name,
            original_name,
            description,
            mimetype,
            external,
            version_req,
            confidence,
            parents,
            isMajorVersion,
            pwc=None,
            check_in_comment=None,
            display_status=True,
            refresh_at_end=True):
        super(SaveFileHandlerDialog, self).__init__(parent)
        if parent:
            self.root = parent
            self.verbose = parent.verbose
            self.data_operator = parent.data_op
            self.session = parent.session
            self.gateway = parent.gateway
        self.display_status = display_status
        self.display_name = display_name
        self.refresh_at_end = refresh_at_end
        self.status = None

        self.isFinished = False

        self.label = QLabel(self)
        self.label.setStyleSheet("background-color: transparent;")
        self.label.setStyleSheet("color: #FFFFFF;")

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.label)
        self.layout.setAlignment(self.label, Qt.AlignCenter)
        self.layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        pal = QPalette()
        pal.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(pal)
        self.setWindowOpacity(0.85)

        self.thread = SaveThread(self)
        self.t = threading.Thread(target=self.thread.run, args=(
            byte_array_stream,
            folder,
            display_name,
            original_name,
            description,
            mimetype,
            external,
            version_req,
            confidence,
            parents,
            isMajorVersion,
            pwc,
            check_in_comment
        ))
        self.thread.finished.connect(self.onFinish)
        self.label.setText("Uploading file " + display_name + " ...")

        self.t.start()
        self.t.join(1)
        if self.display_status:
            self.setModal(True)
            self.show()
        self.setAttribute(Qt.WA_DeleteOnClose)  # Delete Dialog on close

    def onFinish(self):
        self.isFinished = True
        self.status = self.thread.status
        if self.display_status:
            self.hide()
            if self.refresh_at_end:
                self.root.tree_ops.refreshTree()
        self.root.wait_loop.exit(0)
        self.close()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, \
                    "Escape key clicked."
            event.ignore()

    def closeEvent(self, event):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Close event invoked."
        if self.isFinished:
            try:
                self.t.join()
                if self.verbose:
                    print self.__class__.__name__, PRINT_COLON, \
                        "Thread already finished executing."
            except Exception, e:
                # Potential that thread is garbage collected.
                if self.verbose:
                    print self.__class__.__name__, PRINT_COLON, e
        else:
            try:
                self.thread.stop()
                while not self.thread.isFinished():
                    pass
                else:
                    self.t.join()
                    if self.verbose:
                        print self.__class__.__name__, PRINT_COLON, \
                            "Safe quitting download thread."
            except Exception, e:
                print self.__class__.__name__, e

        # Note: Attempt to prevent QThread errors, looks like it works?
        try:
            self.thread.deleteLater()
            self.t.deleteLater()
        except:
            pass
        super(SaveFileHandlerDialog, self).closeEvent(event)


class SaveThread(QThread):
    notifyProgress = Signal(int)
    finished = Signal(bool)

    def __init__(self, parent=None):
        super(SaveThread, self).__init__(parent)

        self._stop = False
        self._finished = False
        self.status = None
        if parent:
            self.verbose = parent.verbose
            self.session = parent.session
            self.data_operator = parent.data_operator
            self.gateway = parent.gateway

    def stop(self):
        self._stop = True
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, \
                "Trying to stop download thread (", self.objectName, ")..."

    def isFinished(self):
        return self._finished

    def run(self,
            byte_array_stream,
            folder,
            display_name,
            original_name,
            description,
            mimetype,
            external,
            version_req,
            confidence,
            parents,
            isMajorVersion=False,
            pwc=None,
            check_in_comment=None):

        try:
            if pwc is None:
                self.status = self.data_operator.createVersionedDocument(
                    folder,
                    display_name,
                    mimetype,
                    confidence,
                    self.gateway.jvm.java.io.ByteArrayInputStream(
                        byte_array_stream),
                    isMajorVersion,
                    original_name,
                    description,
                    parents,
                    external,
                    version_req)
            else:
                self.status = self.data_operator.uploadNewDocumentVersion(
                    folder,
                    pwc,
                    display_name,
                    mimetype,
                    confidence,
                    isMajorVersion,
                    check_in_comment,
                    self.gateway.jvm.java.io.ByteArrayInputStream(
                        byte_array_stream),
                    original_name,
                    description,
                    parents,
                    external,
                    version_req)
        except Exception, e:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, e

        self.finished.emit(True)
        self._finished = True
