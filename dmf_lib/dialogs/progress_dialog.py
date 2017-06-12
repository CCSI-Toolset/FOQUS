import os
import ntpath
import threading

from PySide.QtGui import QDialog
from PySide.QtGui import QLabel
from PySide.QtGui import QProgressBar
from PySide.QtGui import QPushButton
from PySide.QtGui import QVBoxLayout
from PySide.QtGui import QLayout
from PySide.QtGui import QPalette
from PySide.QtCore import Qt
from PySide.QtCore import QThread
from PySide.QtCore import Signal
from dmf_lib.common.common import BLOCK_LENGTH
from dmf_lib.common.common import PRINT_COLON


class ProgressDialog(QDialog):
    PROGRESS_BAR_MAX = 100

    def __init__(self, parent, doc, fname, zip_len=False, auto_close=False):
        super(ProgressDialog, self).__init__(parent)
        self.doc = doc
        self.fname = fname
        self.zip_len = zip_len
        self.auto_close = auto_close
        if parent:
            self.parent = parent
            self.verbose = parent.verbose
            self.data_op = parent.data_op

        self.label = QLabel(self)
        self.label.setStyleSheet("background-color: transparent;")
        self.label.setStyleSheet("color: #FFFFFF;")

        self.progressBar = QProgressBar(self)
        self.progressBar.setRange(0, ProgressDialog.PROGRESS_BAR_MAX)
        if fname:
            self.button = QPushButton("Cancel", self)
            self.button.clicked.connect(self.onCancel)
            self.button.setMaximumWidth(100)
            self.button.setMinimumWidth(100)

        self.isFinished = False
        self.thread = DownloadThread(self)
        self.t = threading.Thread(target=self.thread.run, args=(
            self.doc, self.fname, self.data_op, self.zip_len))
        self.thread.notifyProgress.connect(self.onProgress)
        self.thread.finished.connect(self.onFinish)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.progressBar)
        layout.setAlignment(self.label, Qt.AlignCenter)
        layout.setAlignment(self.progressBar, Qt.AlignCenter)
        layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        pal = QPalette()
        pal.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(pal)
        self.setWindowOpacity(0.85)

        if fname:
            layout.addWidget(self.button)
            layout.setAlignment(self.button, Qt.AlignCenter)

        self.t.start()
        self.t.join(1)
        if fname:
            if self.zip_len:
                self.label.setText(
                    "Downloading " + ntpath.basename(self.fname) + " ...")
            else:
                self.label.setText(
                    "Downloading " + self.doc.getName() + " ...")
            self.show()
        else:
            if self.zip_len:
                self.label.setText("Loading " + fname + " ...")
            else:
                self.label.setText("Loading " + self.doc.getName() + " ...")
            self.exec_()
        self.setAttribute(Qt.WA_DeleteOnClose)  # Delete Dialog on close

    def onCancel(self):
        try:
            self.thread.stop()
            while not self.thread.isFinished():
                pass
        except Exception, e:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, e

        if not self.isFinished:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, \
                    "Download canceled. Removing file."
            try:
                os.remove(self.fname)
            except OSError:
                pass
        self.close()

    def onProgress(self, i):
        if i > ProgressDialog.PROGRESS_BAR_MAX:
            self.progressBar.setValue(ProgressDialog.PROGRESS_BAR_MAX)
        else:
            self.progressBar.setValue(i)

    def onFinish(self):
        self.isFinished = True
        if self.fname:
            self.button.setText("OK")
            if self.zip_len:
                self.label.setText(
                    "Downloaded " + ntpath.basename(self.fname) + " !")
            else:
                self.label.setText("Downloaded " + self.doc.getName() + "!")
            if self.auto_close:
                self.close()
        else:
            self.parent.setProgressDialogByteArrayStream(
                self.thread.getByteArray())
            self.close()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, \
                    "Escape key clicked."
            self.close()

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
        super(ProgressDialog, self).closeEvent(event)


class DownloadThread(QThread):
    notifyProgress = Signal(int)
    finished = Signal(bool)

    def __init__(self, parent=None):
        super(DownloadThread, self).__init__(parent)

        self._stop = False
        self._finished = False
        if parent:
            self.verbose = parent.verbose

    def stop(self):
        self._stop = True
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, \
                "Trying to stop download thread (", self.objectName, ")..."

    def isRunning(self):
        return not self._stop

    def isFinished(self):
        return self._finished

    def getByteArray(self):
        try:
            return self.b_complete
        except:
            return None

    def run(self, doc, fname, data_op, zip_len):
        self.b_complete = bytearray()
        if fname:
            f = open(fname, 'ab')
        if zip_len:
            inputStream = doc
            size = zip_len
        else:
            inputStream = doc.getContentStream().getStream()
            size = doc.getContentStreamLength()
        track = 0

        while track < size:
            if self._stop:
                if self.verbose:
                    print self.__class__.__name__, PRINT_COLON, \
                        "Stopping download thread now!"
                break
            if inputStream.available() < 0:
                break
            b = data_op.getDocumentContentsAsByteArray(
                inputStream, BLOCK_LENGTH)
            # Heuristic based on file(1)'s choices for what is
            # text and what is not.
            textchars = bytearray([7, 8, 9, 10, 12, 13, 27]) + bytearray(
                range(0x20, 0x100))
            is_binary_string = lambda bytes: bool(
                bytes.translate(None, textchars))
            if track == 0:
                is_binary = True if is_binary_string(b) else False
                if self.verbose:
                    print self.__class__.__name__, PRINT_COLON, \
                        "Binary?", is_binary
            if fname:
                f.write(b)
                f.flush()
            else:
                self.b_complete.extend(b)
            track += len(b)
            downloaded = (int)(float(track) / float(size) * 100.0)
            self.notifyProgress.emit(downloaded)
        try:
            f.close()
            inputStream.close()
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, \
                    "Closing file and input stream."
        except:
            pass
        self.finished.emit(True)
        self._finished = True
