from PySide.QtGui import QDialog
from PySide.QtGui import QImage
from PySide.QtGui import QLabel
from PySide.QtGui import QComboBox
from PySide.QtGui import QWidget
from PySide.QtGui import QHBoxLayout
from PySide.QtGui import QVBoxLayout
from PySide.QtGui import QSizePolicy
from PySide.QtGui import QPixmap
from PySide.QtCore import Qt
from dmf_lib.common.common import PWC
from dmf_lib.common.common import PRINT_COLON
from dmf_lib.graph.graph_viewer import GraphViewer


class DetailedInfoDialog(QDialog):
    def __init__(self, parent=None):
        super(DetailedInfoDialog, self).__init__(parent)

        self.root = parent
        self.verbose = self.root.verbose
        self.DMF_HOME = self.root.DMF_HOME

        self.setAutoFillBackground(True)
        self.layout = QVBoxLayout(self)
        indent = 20

        self.image = QImage()
        self.preview = QLabel(self)
        self.preview.setVisible(False)
        self.preview.setFixedSize(80, 100)
        self.name = QLabel(self)
        self.name.setStyleSheet(
            "font-size: 25pt;"
            "background-color: white;"
            "qproperty-wordWrap: true;")

        self.ver_list_label = QLabel(self)
        self.ver_list_label.setText("Version")
        self.ver_list_label.setStyleSheet(
            "font-size: 15pt;"
            "background-color: white;"
            "color: #6183A6;")
        self.ver_list_label.setVisible(False)
        self.ver_list = QComboBox(self)
        self.ver_list.currentIndexChanged['QString'].connect(
            self.handleComboBoxChange)
        self.ver_list.setVisible(False)

        header = QWidget(self)
        headerLayout = QHBoxLayout()
        headerText = QWidget(self)
        versionText = QWidget(self)
        versionText.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        headerTextLayout = QVBoxLayout()
        versionTextLayout = QHBoxLayout()
        headerText.setLayout(headerTextLayout)
        versionText.setLayout(versionTextLayout)
        headerLayout.addWidget(self.preview)
        headerLayout.addWidget(headerText)
        headerTextLayout.addWidget(self.name)
        headerTextLayout.addWidget(versionText)
        versionTextLayout.addWidget(self.ver_list_label)
        versionTextLayout.addWidget(self.ver_list)
        header.setLayout(headerLayout)

        self.description = QLabel(self)
        self.description.setVisible(False)
        self.description.setStyleSheet(
            "background-color: white;"
            "qproperty-wordWrap: true;")

        self.original_name_label = QLabel(self)
        self.original_name_label.setText("Original Name")
        self.original_name_label.setVisible(False)
        self.original_name = QLabel(self)
        self.original_name.setVisible(False)
        self.original_name.setStyleSheet(
            "background-color: white;"
            "qproperty-wordWrap: true;")
        self.original_name_label.setStyleSheet("color: #767676;")
        self.original_name.setIndent(indent)

        self.mimetype_label = QLabel(self)
        self.mimetype_label.setText("Mimetype")
        self.mimetype_label.setVisible(False)
        self.mimetype = QLabel(self)
        self.mimetype.setVisible(False)
        self.mimetype.setStyleSheet(
            "background-color: white;"
            "qproperty-wordWrap: true;")
        self.mimetype_label.setStyleSheet("color: #767676;")
        self.mimetype.setIndent(indent)

        self.external_label = QLabel(self)
        self.external_label.setText("External URL")
        self.external_label.setVisible(False)
        self.external = QLabel(self)
        self.external.setVisible(False)
        self.external.setStyleSheet(
            "background-color: white;"
            "qproperty-wordWrap: true;")
        self.external_label.setStyleSheet("color: #767676;")
        self.external.setIndent(indent)

        self.version_req_label = QLabel(self)
        self.version_req_label.setText("Version Requirements")
        self.version_req_label.setVisible(False)
        self.version_req = QLabel(self)
        self.version_req.setVisible(False)
        self.version_req.setStyleSheet(
            "background-color: white;"
            "qproperty-wordWrap: true;")
        self.version_req_label.setStyleSheet("color: #767676;")
        self.version_req.setIndent(indent)

        self.confidence_label = QLabel(self)
        self.confidence_label.setText("Confidence")
        self.confidence_label.setVisible(False)
        self.confidence = QLabel(self)
        self.confidence.setVisible(False)
        self.confidence.setStyleSheet(
            "background-color: white;"
            "qproperty-wordWrap: true;")
        self.confidence_label.setStyleSheet("color: #767676;")
        self.confidence.setIndent(indent)

        self.creator_label = QLabel(self)
        self.creator_label.setText("Creator")
        self.creator_label.setVisible(False)
        self.creator = QLabel(self)
        self.creator.setVisible(False)
        self.creator.setStyleSheet(
            "background-color: white;"
            "qproperty-wordWrap: true;")
        self.creator_label.setStyleSheet("color: #767676;")
        self.creator.setIndent(indent)

        self.creation_date_label = QLabel(self)
        self.creation_date_label.setText("Creation Date")
        self.creation_date_label.setVisible(False)
        self.creation_date = QLabel(self)
        self.creation_date.setVisible(False)
        self.creation_date_label.setStyleSheet("color: #767676;")
        self.creation_date.setStyleSheet(
            "background-color: white;"
            "qproperty-wordWrap: true;")
        self.creation_date.setIndent(indent)

        self.last_modified_date_label = QLabel(self)
        self.last_modified_date_label.setText("Modified Date")
        self.last_modified_date_label.setVisible(False)
        self.last_modified_date = QLabel(self)
        self.last_modified_date.setVisible(False)

        self.last_modified_date_label.setStyleSheet("color: #767676;")
        self.last_modified_date.setStyleSheet(
            "background-color: white;"
            "qproperty-wordWrap: true;")
        self.last_modified_date.setIndent(indent)
        self.last_modified_date.setIndent(indent)

        self.layout.addWidget(header)
        self.layout.addWidget(self.description)
        self.layout.addWidget(self.original_name_label)
        self.layout.addWidget(self.original_name)
        self.layout.addWidget(self.mimetype_label)
        self.layout.addWidget(self.mimetype)
        self.layout.addWidget(self.external_label)
        self.layout.addWidget(self.external)
        self.layout.addWidget(self.confidence_label)
        self.layout.addWidget(self.confidence)
        self.layout.addWidget(self.version_req_label)
        self.layout.addWidget(self.version_req)
        self.layout.addWidget(self.creator_label)
        self.layout.addWidget(self.creator)
        self.layout.addWidget(self.creation_date_label)
        self.layout.addWidget(self.creation_date)
        self.layout.addWidget(self.last_modified_date_label)
        self.layout.addWidget(self.last_modified_date)

        if self.root.IS_BROWSER_MODE:
            self.view = GraphViewer(self)
            self.layout.addWidget(self.view)
        else:
            self.view = None

        self.layout.addStretch(1)
        #  Delete Dialog on close
        self.setAttribute(Qt.WA_DeleteOnClose)

    def activate(self, parent=None):
        self.show()

    def setData(self,
                display_name,
                original_name,
                description,
                mimetype,
                external,
                version_req,
                confidence,
                creator,
                creation_date,
                last_modified_date,
                ver_list,
                preview,
                update_ver_list=True):
        if preview is not None and "Error" not in preview:
            self.image.loadFromData(preview)
            self.preview.setPixmap(QPixmap(self.image))
            self.preview.setVisible(True)
        else:
            self.preview.setVisible(False)

        if display_name is not None:
            self.name.setText(display_name)

        if original_name is not None and \
                original_name != "" and \
                not original_name.isspace():
            self.original_name.setText(original_name)
            self.original_name.setVisible(True)
            self.original_name_label.setVisible(True)
        else:
            self.original_name.setText('')
            self.original_name.setVisible(False)
            self.original_name_label.setVisible(False)

        if description is not None and \
                description != "" and \
                not description.isspace():
            self.description.setText("\n" + description + "\n")
            self.description.setVisible(True)
        else:
            self.description.setText('')
            self.description.setVisible(False)

        if mimetype is not None:
            self.mimetype.setText(mimetype)
            self.mimetype.setVisible(True)
            self.mimetype_label.setVisible(True)
        else:
            self.mimetype.setText('')
            self.mimetype.setVisible(False)
            self.mimetype_label.setVisible(False)

        if external is not None and \
                external != "" and \
                not external.isspace():
            self.external.setText(external)
            self.external.setVisible(True)
            self.external_label.setVisible(True)
        else:
            self.external.setText('')
            self.external.setVisible(False)
            self.external_label.setVisible(False)

        if version_req is not None:
            self.version_req.setText(version_req)
            self.version_req.setVisible(True)
            self.version_req_label.setVisible(True)
        else:
            self.version_req.setText('')
            self.version_req.setVisible(False)
            self.version_req_label.setVisible(False)

        if confidence is not None:
            self.confidence.setText(confidence)
            self.confidence.setVisible(True)
            self.confidence_label.setVisible(True)
        else:
            self.confidence.setText('')
            self.confidence.setVisible(False)
            self.confidence_label.setVisible(False)

        if creator is not None:
            self.creator.setText(creator)
            self.creator.setVisible(True)
            self.creator_label.setVisible(True)
        else:
            self.creation_date.setText('')
            self.creation_date.setVisible(False)
            self.creation_date_label.setVisible(False)

        if creation_date is not None:
            self.creation_date.setText(creation_date)
            self.creation_date.setVisible(True)
            self.creation_date_label.setVisible(True)
        else:
            self.creation_date.setText('')
            self.creation_date.setVisible(False)
            self.creation_date_label.setVisible(False)

        if last_modified_date is not None:
            self.last_modified_date.setText(last_modified_date)
            self.last_modified_date.setVisible(True)
            self.last_modified_date_label.setVisible(True)
        else:
            self.last_modified_date.setText('')
            self.last_modified_date.setVisible(False)
            self.last_modified_date_label.setVisible(False)

        if update_ver_list:
            self.ver_list.clear()
            if ver_list is not None:
                for ver in ver_list:
                    if ver != PWC:
                        self.ver_list.addItem(ver, ver)

                self.ver_list.setVisible(True)
                self.ver_list_label.setVisible(True)
            else:
                self.ver_list.setVisible(False)
                self.ver_list_label.setVisible(False)

        self.repaint()
        self.adjustSize()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, \
                    "Escape button clicked."

    def closeEvent(self, event):
        if self.verbose:
            print self.__class__.__name__, PRINT_COLON, "Close event invoked."
        super(DetailedInfoDialog, self).closeEvent(event)
        self.root.close()

    def handleComboBoxChange(self, text):
        if self.ver_list.count() > 0:
            self.root.changeDetailedInfoVersion(text)
