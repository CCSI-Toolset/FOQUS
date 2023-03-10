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
"""drawFlowsheet.py
* Widget to display the flowsheet

John Eslick, Carnegie Mellon University, 2014
"""
from PyQt5 import QtCore
from PyQt5.QtGui import (
    QColor,
    QFont,
    QPen,
    QBrush,
    QPainter,
    QPainterPath,
    QPainterPathStroker,
)
from PyQt5.QtWidgets import (
    QGraphicsScene,
    QGraphicsView,
    QInputDialog,
    QLineEdit,
    QMessageBox,
)
from foqus_lib.framework.graph import *
import math
import types


class fsScene(QGraphicsScene):
    """
    Class for viewing and editing a flowsheet.
    """

    # Mouse Modes
    MODE_SELECT = 1
    MODE_ADDNODE = 2
    MODE_ADDEDGE = 3

    ITEM_NONE = 0
    ITEM_NODE = 1
    ITEM_EDGE = 2

    def __init__(self, parent=None):
        """
        Initialize the flowsheet display
        """
        super(fsScene, self).__init__(parent)
        # Location of mouse events and whether the mouse button is down
        self.mouseDown = False
        self.pressX = 0.0
        self.pressY = 0.0
        self.releaseX = 0.0
        self.releaseY = 0.0
        #
        self.minorGrid = 20  # Minor grid spacing
        self.majorGrid = 100  # Major grid spacing
        self.xMaxGrid = 800  # Extent of grid area up x
        self.xMinGrid = -800  # Extent of grid area lo x
        self.yMaxGrid = 600  # Extent of grid area up y
        self.yMinGrid = -600  # Extent of grid area lo y
        self.nodeSize = 20  # size of node
        self.edgeArrowSize = 16  # size of the edge arrows
        self.actNodeSize = 25  # size of an active node
        self.mode = self.MODE_SELECT  # Mouse mode
        self.p = parent  # Parent class
        self.node1 = None  # Node 1 for drawing edges
        self.node2 = None  # Node 2 for drawing edges
        self.selectedNodes = []  # Set of selected nodes
        self.selectedEdges = []  # Set of selected edges
        self.majorGridPen = None  # Pen for major grids
        self.minorGridPen = None  # Pen for minor grids
        self.edgePen = None  # Pen for edges
        self.tearEdgePen = None  # Pen for tear edges
        self.nodePen = None  # Pen for nodes
        self.activeNodePen = None  # Pen for active node
        self.selectionPen = None  # Pen for node selection markers
        self.eSelectionPen = None  # Pen for edge selection markers
        #
        # Line styles
        self.lcMajorGrid = QColor(255, 190, 240)  # minor grid color
        self.lcMinorGrid = QColor(190, 240, 255)  # major grid color
        self.ltGrid = QtCore.Qt.DashLine  # grid line type
        self.lwMinorGrid = 1  # grid line width
        self.lwMajorGrid = 1  #
        #
        self.lcEdge = QColor(0, 50, 200)
        self.ltEdge = QtCore.Qt.SolidLine
        self.lwEdge = 2
        self.lcTear = QColor(100, 200, 255)
        self.ltTear = QtCore.Qt.SolidLine
        #
        self.lcNode = QColor(0, 0, 0)
        self.ltNode = QtCore.Qt.SolidLine
        self.lwNode = 2
        self.lcActNode = QColor(0, 0, 0)
        #
        self.lcSelect = QColor(0, 255, 0)
        self.ltSelect = QtCore.Qt.SolidLine
        self.lwSelect = 4
        self.lwEdgeSelect = 10
        #
        # Set font
        self.font = None
        self.fontSize = 12
        #
        # Set Brushes
        self.nodeBrush = None
        self.actNodeBrush = None
        #
        self.fcNode = QColor(128, 128, 128)
        self.fcActNode = QColor(128, 250, 128)
        self.fpNode = QtCore.Qt.SolidPattern
        self.fpActNode = QtCore.Qt.SolidPattern
        #
        self.edgeArrowBrush = None
        self.fcEdgeArrow = QColor(0, 50, 200)
        self.fpEdgeArrow = QtCore.Qt.SolidPattern
        #
        self.whiteBrush = None
        self.fcWB = QColor(240, 240, 240)
        self.fpWB = QtCore.Qt.SolidPattern
        #
        self.loadPens()  # setup pens, brushes, and font

    def loadPens(self):
        # Create pens
        self.majorGridPen = QPen()
        self.minorGridPen = QPen()
        self.edgePen = QPen()
        self.tearEdgePen = QPen()
        self.nodePen = QPen()
        self.activeNodePen = QPen()
        self.selectionPen = QPen()
        # Set color
        self.majorGridPen.setColor(self.lcMajorGrid)
        self.minorGridPen.setColor(self.lcMinorGrid)
        self.edgePen.setColor(self.lcEdge)
        self.tearEdgePen.setColor(self.lcTear)
        self.nodePen.setColor(self.lcNode)
        self.activeNodePen.setColor(self.lcActNode)
        self.selectionPen.setColor(self.lcSelect)
        # set line style
        self.majorGridPen.setStyle(self.ltGrid)
        self.minorGridPen.setStyle(self.ltGrid)
        self.edgePen.setStyle(self.ltEdge)
        self.tearEdgePen.setStyle(self.ltTear)
        self.nodePen.setStyle(self.ltNode)
        self.activeNodePen.setStyle(self.ltNode)
        self.selectionPen.setStyle(self.ltSelect)
        # set line width
        self.majorGridPen.setWidth(self.lwMajorGrid)
        self.minorGridPen.setWidth(self.lwMinorGrid)
        self.edgePen.setWidth(self.lwEdge)
        self.tearEdgePen.setWidth(self.lwEdge)
        self.nodePen.setWidth(self.lwNode)
        self.activeNodePen.setWidth(self.lwNode)
        self.selectionPen.setWidth(self.lwSelect)
        # Set edge selection pen
        self.eSelectionPen = QPen(self.selectionPen)
        self.eSelectionPen.setWidth(self.lwEdgeSelect)
        # Set font
        self.font = QFont()
        self.font.setPixelSize(self.fontSize)
        # set up brushes
        self.nodeBrush = QBrush()
        self.actNodeBrush = QBrush()
        self.edgeArrowBrush = QBrush()
        self.whiteBrush = QBrush()
        #
        self.nodeBrush.setColor(self.fcNode)
        self.actNodeBrush.setColor(self.fcActNode)
        self.edgeArrowBrush.setColor(self.fcEdgeArrow)
        self.whiteBrush.setColor(self.fcWB)
        #
        self.nodeBrush.setStyle(self.fpNode)
        self.actNodeBrush.setStyle(self.fpActNode)
        self.edgeArrowBrush.setStyle(self.fpEdgeArrow)
        self.whiteBrush.setStyle(self.fpWB)

    def drawGrid(self):
        """
        Draw the grid for the drawing area
        """
        # Add vertical minor grids
        path = QPainterPath()
        minLoc = self.xMinGrid + self.minorGrid
        maxLoc = self.xMaxGrid
        gStep = self.minorGrid
        for i in range(minLoc, maxLoc, gStep):
            path.moveTo(i, self.yMinGrid)
            path.lineTo(i, self.yMaxGrid)
        self.addPath(path, self.minorGridPen)
        # Add horizontal minor grids
        path = QPainterPath()
        for i in range(minLoc, maxLoc, gStep):
            path.moveTo(self.xMinGrid, i)
            path.lineTo(self.xMaxGrid, i)
        self.addPath(path, self.minorGridPen)
        # Add vertical minor grids
        path = QPainterPath()
        minLoc = self.xMinGrid
        maxLoc = self.xMaxGrid
        gStep = self.majorGrid
        for i in range(minLoc, maxLoc, gStep):
            path.moveTo(i, self.yMinGrid)
            path.lineTo(i, self.yMaxGrid)
        self.addPath(path, self.majorGridPen)
        # Add vertical minor grids
        path = QPainterPath()
        for i in range(minLoc, maxLoc, gStep):
            path.moveTo(self.xMinGrid, i)
            path.lineTo(self.xMaxGrid, i)
        self.addPath(path, self.majorGridPen)

    def addTextCenteredOn(self, x, y, text):
        """
        Add text vertically and horizontally centered on (x, y)
        """
        text = self.addText(text, self.font)
        text.setPos(
            x - text.boundingRect().width() / 2.0,
            y - text.boundingRect().height() / 2.0,
        )

    def drawNode(self, x, y, nodeName, nodeType):
        """
        Draw a node centered at x,y.  Text lines are centered
        under the node for the node name and node type
        --Args--
        x: x coordinate of node
        y: y coordinate of node
        nodeName: text for the first line under the node
        nodeType: text for the second line under the node
        """
        # draw a square centered on x,y
        path = QPainterPath()
        path.addRect(
            x - self.nodeSize / 2.0,
            y - self.nodeSize / 2.0,
            self.nodeSize,
            self.nodeSize,
        )
        # If the node is selected draw it highlighted else draw it normal
        if nodeName in self.selectedNodes:
            gitem = self.addPath(path, self.selectionPen, self.nodeBrush)
        else:
            gitem = self.addPath(path, self.nodePen, self.nodeBrush)
        # Store some data about the node, so that if you click on it
        # we can determine what you clicked on
        gitem.setData(1, nodeName)  # The name of the node
        gitem.setData(2, "node")  # the fact that it is a node
        # Draw text labels
        self.addTextCenteredOn(
            x, y + self.nodeSize / 2 + self.fontSize / 2 + 4, nodeName
        )
        self.addTextCenteredOn(x, y + self.nodeSize / 2 + self.fontSize + 16, nodeType)

    def drawEdge(self, x1, y1, x2, y2, index, curve, tear=False):
        """
        Draw an edge from x1, y1 to x2, y2.  Edges connect two nodes
        --Args--
        index: the edge index
        curve: distance from center of straight edge to a point on
               curved edge (can be positive or negitive.  Used to
               keep edges from overlapping.
        tear: if true draw in tear edge style
        """
        # determine if edge conntects a node to itself.
        if abs(x1 - x2) < 0.01 and abs(y1 - y2) < 0.01:
            path = QPainterPath()
            curve = curve * 2
            path.addEllipse(x1, y1 - curve / 2.0, curve, curve)
            if tear:
                gi = self.addPath(path, self.edgePen)
            else:
                gi = self.addPath(path, self.tearEdgePen)
        else:
            # mid point of the edge if it is a straight line
            xmid = (x1 + x2) / 2.0
            ymid = (y1 + y2) / 2.0
            # get the angle of the edge and the angle perpendicular
            ang = math.atan2((y2 - y1), (x2 - x1))
            ang_perp = math.atan2((x1 - x2), (y2 - y1))
            # calculate the mid point of the curved edge
            xcurve = xmid + curve * math.cos(ang_perp)
            ycurve = ymid + curve * math.sin(ang_perp)
            # calculate control point for drawing quaratic curve
            xcontrol = 2 * xcurve - xmid
            ycontrol = 2 * ycurve - ymid
            # draw Edge
            path = QPainterPath()
            path.moveTo(x1, y1)
            path.quadTo(xcontrol, ycontrol, x2, y2)
            p2 = QPainterPathStroker()
            path = p2.createStroke(path)
            # if edge is selected draw it highlighted
            if index in self.selectedEdges:
                self.addPath(path, self.eSelectionPen)
            # if edge is a tear draw it tear style else draw it normal
            if tear:
                gi = self.addPath(path, self.tearEdgePen)
            else:
                gi = self.addPath(path, self.edgePen)
            # Add data to edge so if seleted we can determine that it
            # is an edge and which edge it is.
            gi.setData(1, index)
            gi.setData(2, "edge")
            # Draw the arrow
            path = QPainterPath()
            xs = xcurve + self.edgeArrowSize * math.cos(ang)
            ys = ycurve + self.edgeArrowSize * math.sin(ang)
            path.moveTo(xs, ys)
            path.lineTo(
                xs
                - self.edgeArrowSize * math.cos(ang)
                + self.edgeArrowSize / 2.0 * math.cos(ang_perp),
                ys
                - self.edgeArrowSize * math.sin(ang)
                + self.edgeArrowSize / 2.0 * math.sin(ang_perp),
            )
            path.lineTo(
                xs
                - self.edgeArrowSize * math.cos(ang)
                - self.edgeArrowSize / 2.0 * math.cos(ang_perp),
                ys
                - self.edgeArrowSize * math.sin(ang)
                - self.edgeArrowSize / 2.0 * math.sin(ang_perp),
            )
            path.lineTo(xs, ys)
            gi = self.addPath(path, self.edgePen, self.edgeArrowBrush)
            # Add data so selecting the arrow in like selecting the edge
            gi.setData(1, index)
            gi.setData(2, "edge")

    def nearestGrid(self, x, y):
        """
        Find the nearest minor grid to a point.
        """
        xg = round(x / self.minorGrid) * self.minorGrid
        yg = round(y / self.minorGrid) * self.minorGrid
        return xg, yg

    def deleteSelected(self):
        """
        Delete the selected nodes and edges then redraw
        the flowsheet
        """
        self.p.dat.flowsheet.deleteEdges(self.selectedEdges)
        self.selectedEdges = []
        self.p.dat.flowsheet.deleteNodes(self.selectedNodes)
        self.selectedNodes = []
        self.p.noneSelectedEmit()
        self.p.createScene()

    def mouseMoveEvent(self, evnt):
        """
        If the mouse button is held down move selected nodes
        """
        # if mouse button is down check if you want to move nodes
        if not evnt.buttons() == QtCore.Qt.LeftButton:
            return
        if self.mode != self.MODE_SELECT:
            return
        dx = evnt.scenePos().x() - self.pressX
        dy = evnt.scenePos().y() - self.pressY
        for i, node in enumerate(self.selectedNodes):
            x = self.ipos[i][0] + dx
            y = self.ipos[i][1] + dy
            x, y = self.nearestGrid(x, y)  # snap to minor grids
            self.p.dat.flowsheet.nodes[node].x = x
            self.p.dat.flowsheet.nodes[node].y = y
        self.p.createScene()
        self.p.updateFSPos.emit()  # update the flowsheet and node editor

    def mousePressEvent(
        self, evnt, dbg_x=None, dbg_y=None, dbg_mod=None, dbg_name=None
    ):
        """
        The mouse was clicked on the flowsheet editor window.  Check
        what was selected on the mouse mode and do something.
        """
        # Get the location of the mouse event
        if evnt is None:
            mod = dbg_mod
            x = dbg_x
            y = dbg_y
        else:
            mod = self.parent().parent().parent().app.keyboardModifiers()
            x = evnt.scenePos().x()
            y = evnt.scenePos().y()
        self.pressX = x
        self.pressY = y
        # Check if there is an object that was clicked on
        s_item = self.itemAt(x, y, self.parent().transform())
        if s_item is not None:
            itemIndex = s_item.data(1)
            itemType = s_item.data(2)
        else:
            itemType = None
            itemIndex = None
        # Selection Mode select nodes or edges holding shift allows
        # you to select multiple nodels and edges.
        if self.mode == self.MODE_SELECT:
            if mod != QtCore.Qt.SHIFT:
                self.selectedEdges = []
                self.selectedNodes = []
            if itemType == "edge":
                self.selectedEdges.append(itemIndex)
                self.p.edgeSelectedEmit(self.selectedEdges[-1])
            elif itemType == "node":
                self.selectedNodes.append(itemIndex)
                self.p.nodeSelectedEmit(self.selectedNodes[-1])
            elif mod != QtCore.Qt.SHIFT:
                # don't clear the selection if shift is down this
                # prevents you form selecting a bunch of stuff and
                # mistakenly clearing it all because you missed what
                # you were aiming for.
                self.selectedEdges = []
                self.selectedNodes = []
                self.p.noneSelectedEmit()
            self.p.createScene()
        # Add node mode
        elif self.mode == self.MODE_ADDNODE:
            xg, yg = self.nearestGrid(x, y)
            if dbg_name is None:
                name, ok = QInputDialog.getText(
                    self.p, "Node Name", "New node name:", QLineEdit.Normal
                )
            else:
                ok = True
                name = dbg_name
            if ok and name != "":
                if name in self.p.dat.flowsheet.nodes:
                    QMessageBox.warning(
                        self.p, "Invalid Name", "That node name is already being used."
                    )
                    return
                if " " in name:
                    QMessageBox.warning(
                        self.p,
                        "Invalid Name",
                        "Node name should not contain any spaces.",
                    )
                    return
                self.p.dat.flowsheet.addNode(name, xg, yg, 0)
                self.p.updateEdgeEditEmit()
                self.p.nodeSelectedEmit(name)
                self.p.createScene()
        # Add Edge mode
        elif self.mode == self.MODE_ADDEDGE:
            if self.selectedNodes == []:
                if itemType == "node":
                    self.node1 = self.selectedNodes.append(itemIndex)
            else:
                if len(self.selectedNodes) == 1 and itemType == "node":
                    self.selectedNodes.append(itemIndex)
                    if self.selectedNodes[0] != self.selectedNodes[1]:
                        ind = self.p.dat.flowsheet.addEdge(
                            self.selectedNodes[0], self.selectedNodes[1]
                        )
                        self.p.updateEdgeEditEmit()
                    self.selectedNodes = []
                else:
                    self.selectedNodes = []
            self.p.createScene()
        # original location of selected nodes for moving
        self.ipos = [(0, 0)] * len(self.selectedNodes)
        for i, node in enumerate(self.selectedNodes):
            self.ipos[i] = (
                self.p.dat.flowsheet.nodes[node].x,
                self.p.dat.flowsheet.nodes[node].y,
            )


class drawFlowsheet(QGraphicsView):
    """
    This is the widget for viewing a flowsheet the actual drawing
    and event handing is done by the fsSecne object contained in
    drawFlowsheet object
    """

    nodeSelected = QtCore.pyqtSignal([str])
    edgeSelected = QtCore.pyqtSignal([int])
    noneSelected = QtCore.pyqtSignal()
    updateFS = QtCore.pyqtSignal()
    updateFSPos = QtCore.pyqtSignal()
    updateEdgeEdit = QtCore.pyqtSignal()

    def __init__(self, dat, parent=None):
        """
        Initialize drawFlowsheet widget
        """
        # call __init__ form base class
        super(drawFlowsheet, self).__init__(parent)
        # create and set scene object
        self.sc = fsScene(self)
        self.setScene(self.sc)
        self.setRenderHint(QPainter.Antialiasing)
        # set session data
        self.dat = dat
        # draw the flowsheet scene
        self.createScene()

    def createScene(self):
        """
        Draw the current flowsheet state
        """
        self.scene().clear()
        self.scene().drawGrid()
        # draw nodes
        for i, edge in enumerate(self.dat.flowsheet.edges):
            n1 = self.dat.flowsheet.nodes[edge.start]
            n2 = self.dat.flowsheet.nodes[edge.end]
            self.scene().drawEdge(n1.x, n1.y, n2.x, n2.y, i, edge.curve, edge.tear)
        # draw edges
        for name, node in self.dat.flowsheet.nodes.items():
            self.scene().drawNode(node.x, node.y, name, node.modelName)
        # redraw the scene
        self.scene().update()

    def highlightSingleNode(self, name):
        print(name)
        self.scene().selectedNodes = [name]
        self.scene().selectedEdges = []
        self.createScene()

    def clearSelection(self):
        self.scene().selectedNodes = []
        self.scene().selectedEdges = []
        self.noneSelectedEmit()

    def updateEdgeEditEmit(self):
        """
        Send a signal to update the edge editor.
        """
        self.updateEdgeEdit.emit()

    def nodeSelectedEmit(self, node):
        """
        Send a signal the says and node was selected, and the name
        of the last node selected.  You can select multiple nodes
        but the editor is only displayed for the last on selected
        """
        self.nodeSelected.emit(node)

    def edgeSelectedEmit(self, edge):
        """
        Send a signal that an edge was seslected.  You can select
        multiple edges, but only the last on selected is used to
        open the edge editor
        """
        self.edgeSelected.emit(edge)

    def noneSelectedEmit(self):
        """
        Send a signal that nothing is selected, used to close node
        or edge editors
        """
        self.noneSelected.emit()

    def center(self):
        """
        Set the center on the view to the senter of the flowsheet
        The center of the flowsheet is determined from extreme
        locations of the nodes.
        """
        cp = self.dat.flowsheet.getCenter()
        self.centerOn(cp[0], cp[1])

    def setModeSelect(self):
        """
        Set the mouse mode to selection
        """
        self.scene().mode = fsScene.MODE_SELECT

    def setModeAddNode(self):
        """
        Set the mouse mode to add node
        """
        self.scene().mode = fsScene.MODE_ADDNODE

    def setModeAddEdge(self):
        """
        Set the mouse mode to add edge
        """
        self.scene().mode = fsScene.MODE_ADDEDGE

    def deleteSelected(self):
        """
        Delete selected nodes and edges, also deletes any edges
        connected to a deleted node.
        """
        self.scene().deleteSelected()
