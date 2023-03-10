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
class edgeConnect:
    # Stores information about a connection between two variables
    def __init__(self, vfrom, vto):
        self.fromName = vfrom
        self.toName = vto
        self.active = True

    def saveDict(self):
        sd = dict()
        sd["fromName"] = self.fromName
        sd["toName"] = self.toName
        sd["active"] = self.active
        return sd

    def loadDict(self, sd):
        self.fromName = sd["fromName"]
        self.toName = sd["toName"]
        self.active = sd["active"]


class edge:
    # stores information about an edge
    def __init__(self, name1, name2, curve=0.0):
        self.start = name1  # name of node to start from
        self.end = name2  # name of node at end of edge
        self.curve = curve  # curvature of edge to avoid overlap in drawing
        self.tear = False  # a stream to break for solver
        self.active = True  # true if edge is active if false ignore the edge
        self.con = []  # a list of connections from variables in the from node
        # to variables in the to node
        self.err = False

    def saveDict(self):
        sd = dict()
        sd["start"] = self.start
        sd["end"] = self.end
        sd["curve"] = self.curve
        sd["tear"] = self.tear
        try:
            sd["active"] = self.active
        except:
            sd["active"] = True
        sd["con"] = []
        for c in self.con:
            sd["con"].append(c.saveDict())

        return sd

    def loadDict(self, sd):
        self.start = sd["start"]
        self.end = sd["end"]
        self.curve = sd["curve"]
        self.tear = sd["tear"]
        self.active = sd["active"]
        self.con = []

        for c in sd["con"]:
            con = edgeConnect("", "")
            con.loadDict(c)
            self.con.append(con)

    def addConnection(self, fromName, toName, act=True):
        self.con.append(edgeConnect(fromName, toName))
        self.con[-1].active = act
        return self.con[-1]

    def removeConnection(self, index):
        del self.con[index]

    def transferInformation(self, gr):
        #
        #
        self.err = False
        n1 = gr.nodes[self.start]
        n2 = gr.nodes[self.end]
        for con in self.con:
            if con.active:
                if con.fromName in list(n1.outVars.keys()):
                    try:
                        n2.inVars[con.toName].value = n1.outVars[con.fromName].value
                    except:
                        self.err = True
                elif con.fromName in list(n1.inVars.keys()):
                    try:
                        n2.inVars[con.toName].value = n1.inVars[con.fromName].value
                    except:
                        self.err = True
                else:
                    self.err = True

    def clearConnections(self):
        self.con = []
