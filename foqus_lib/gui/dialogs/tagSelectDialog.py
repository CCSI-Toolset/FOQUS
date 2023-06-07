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
import json
import os

from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import QTreeWidgetItem

mypath = os.path.dirname(__file__)
_tagSelectDialogUI, _tagSelectDialog = uic.loadUiType(
    os.path.join(mypath, "tagSelectDialog_UI.ui")
)


class tagSelectDialog(_tagSelectDialog, _tagSelectDialogUI):
    sendTag = QtCore.pyqtSignal()

    def __init__(self, dat, parent=None, lock=None):
        """
        Constructor for model setup dialog
        """
        super(tagSelectDialog, self).__init__(parent=parent)
        self.setupUi(self)  # Create the widgets
        self.dat = dat  # all of the session data
        self.availTags = dict()
        self.doneButton.clicked.connect(self.accept)
        self.createTagButton.clicked.connect(self.userAddTag)
        self.addTagToListButton.clicked.connect(self.sendTagFunc)
        self.tagsChanged = False
        self.loadTags()
        self.updateAvailableTags()
        self.selectedTags = []

    def userAddTag(self):
        text = self.newTagEdit.text()
        if text != "":
            self.addTag(text)
            self.updateAvailableTags()

    def sendTagFunc(self):
        tlst = self.mainTagList.selectedItems()
        if tlst == []:
            return
        tagList = [""] * len(tlst)
        for i in range(len(tlst)):
            tagList[i] = tlst[i].text(0)
        self.selectedTags = tagList
        self.sendTag.emit()

    def updateAvailableTags(self):
        self.mainTagList.clear()
        self.updateAvailableTagsRec(self.availTags, self.mainTagList)

    def updateAvailableTagsRec(self, tdict, item):
        for key in sorted(list(tdict.keys()), key=lambda s: s.lower()):
            val = tdict[key]
            i = QTreeWidgetItem(item)
            i.setText(0, key)
            if len(val):
                # set flags to make not selectable
                i.setFlags(i.flags() & ~QtCore.Qt.ItemIsSelectable)
                self.updateAvailableTagsRec(val, i)

    def saveTags(self):
        with open("tags.tgs", "w") as outfile:
            json.dump(self.availTags, outfile, indent=2)

    def loadTags(self):
        try:
            with open("tags.tgs", "r") as infile:
                self.availTags = json.load(infile)
        except:
            self.defaultTags()

    def accept(self):
        """
        Close the dialog and save the tags if there was a change
        """
        if self.tagsChanged:
            self.saveTags()
        self.done(0)

    def addTag(self, text):
        """
        Add a tag to the main tag list
        """
        self.tagsChanged = True
        hi = text.split(".")
        d = self.availTags
        for i in hi:
            r = d.get(i, None)
            if not r:
                d[i] = dict()
                d = d[i]
            else:
                d = r

    def defaultTags(self):
        """
        If there is no tags json file, then set up this default list of tags
        """
        self.availTags = dict()
        self.addTag("Heat Integration.Block Name.Block *")
        self.addTag("Heat Integration.Port Type.Port_Material_In")
        self.addTag("Heat Integration.Port Type.Port_Material_Out")
        self.addTag("Heat Integration.Port Type.Port_Heat_In")
        self.addTag("Heat Integration.Port Type.Port_Heat_Out")
        self.addTag("Heat Integration.Port Type.Blk_Var")
        self.addTag("Heat Integration.Variable Type.T")
        self.addTag("Heat Integration.Variable Type.Q")
        self.addTag("Heat Integration.Source Type.heater")
        self.addTag("Heat Integration.Source Type.HX_Hot")
        self.addTag("Heat Integration.Source Type.HX_Cold")
        self.addTag("Heat Integration.Source Type.Point_Hot")
        self.addTag("Heat Integration.Source Type.Point_Cold")
