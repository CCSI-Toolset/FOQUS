from PySide.QtWebKit import QWebPage

"""
 This class overwrites the default QWebPage to provide enhanced functionality
 through some hacks to pass information around. When appropriate, this should
 be investigated using addToJavaScript() and evaluateJavaScript().
"""


class DMFQWebPage(QWebPage):
    def __init__(self, parent=None):
        QWebPage.__init__(self, parent)
        self.root = parent

    # Overwrite JS alert to get variable back on D3 click
    def javaScriptAlert(self, frame, msg):
        self.setSearchText(msg)

    def setSearchText(self, msg):
        try:
            self.root.root.root.search.setText(msg)
        except:
            pass
