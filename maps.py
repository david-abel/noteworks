import heapq
import math
import os
import re
import sys
import random

from collections import defaultdict

from cocos.batch import BatchableNode
from cocos import euclid, collision_model
from cocos.draw import Line
from cocos.layer import scrolling
from cocos.actions.interval_actions import Delay
from cocos.actions.instant_actions import CallFunc
from cocos.sprite import Sprite
import constants
from constants import TROOP_SLOT_SCALE, CELL_SIZE, NUM_OF_SLOTS, AS_OPACITY, \
    SLOT_Z, BUILD_OFFSET_X, BUILD_OFFSET_Y, AS_EDGE_WIDTH, AS_COLORS, AS_SCALE, \
    VERTEX_Z, AS_CIRCLE_Z, EDGE_COLOR, AS_EDGE_COLOR, EDGE_Z, MINIMAPCIRCLE_OPACITY, \
    HALF_VISIBLE, PLAYER_COLORS
from heapItem import HeapItem
import objects
from utils import aabb_to_aa_rect, set_slots, get_action_menu_slots
from models import *

class EmptyTroopSlot(Sprite):
    def __init__(self, x, y, opacity=0):
        super(EmptyTroopSlot, self).__init__(os.path.join("images",
                                                          "maps", "empty_slot.png"))
        self.position = euclid.Vector2(x, y)
        self.scale = TROOP_SLOT_SCALE
        self.opacity = opacity
        self.troop = None


class EmptyBuildingSlot(Sprite):
    def __init__(self, x, y, opacity=0):
        super(EmptyBuildingSlot, self).__init__(
            os.path.join("images", "maps", "empty_building_slot.png"))
        self.position = euclid.Vector2(x, y)
        self.opacity = opacity


class Vertex(Sprite):

    def __init__(self, col, row, vid, asID, visibilityState=0, pid=0,image=None):
        if not image:
            super(Vertex, self).__init__(os.path.join("images", "maps",
                                                  "vertex.png"))
        else:
            super(Vertex, self).__init__(image) #init core

        self.position = euclid.Vector2(col * CELL_SIZE, row * CELL_SIZE)
        self.cshape = aabb_to_aa_rect(self.get_AABB())
        self.cshape.center = self.position
        self.visibilityState = visibilityState

        self.pid = pid  # pid of the human player

        self.numOfSlots = NUM_OF_SLOTS

        self.slotPositions = []

        self.edges = []
            # array of edge objects attached to this vertex. key is edgeNum,
            # val is Edge object.

        self.building = None

        self.vid = vid

        self.asID = asID

        self.asCircle = None

        self.adjacentVertices = []

        self.actionMenuSlots = get_action_menu_slots(4, self.position[0], self.position[1])
        self.borderVertices = defaultdict(list)
        # This will contain all of the Vertices that this vertex is connected to
        # that are in a different AS. k: asID v: list of vertices in that AS
        self.emptySlots = []
        self.emptyTroopSlots = {}

        self.transTroopSlots = {}  # for booking slots while unit is moving
        #value is a tuple of index,slot

        self.troopSlots = {}

        self.buildingSlot = None

        self.opacity = visibilityState * 255

        # for Djiskstra
        self.heapItem = None

    def is_blocking_troop(self, troop, action=None):
        # TODO: flush this out to include encrypted unit, ping, db, firewall etc...
        if action == "attack": #an attack
            # bool1 = (type(troop) == SQLInjection and self.building and (type(self.building) != Database or type(self.building) != Server) and troop.pid != self.building.pid)
            # print "RETURNING in is_blocking_troop", bool1
            return False,False
        bool2 =  (self.building and type(self.building) == Firewall and type(troop) != EncryptedTroop and self.building.pid != troop.pid)
        is_firewall = (type(self.building) == Firewall and self.building.pid != troop.pid)
        return bool2, is_firewall

    def add_troop(self, troop):
        if not self.emptyTroopSlots:
            return False
        i, slot = self.emptyTroopSlots.popitem()
        slot.troop = troop
        troop.slotIndex = i
        self.troopSlots[i] = slot
        troop.update_opacity(255 * math.floor(troop.curVertex.visibilityState))
        if troop.pid == self.pid:
            self._update_visibility()   
            self.set_neighbors_visibility()
        return slot

    def add_building(self, building):
        if self.building:
            return False
        building.slotIndex = 0
        self.building = building
        building.opacity = 255 * math.floor(building.curVertex.visibilityState)
        self.buildingSlot.color = PLAYER_COLORS[self.building.pid]
        if self.building.pid == self.pid:
            self._update_visibility()
            self.set_neighbors_visibility()
        return True

    def remove_building(self):
        if not self.building:
            return False
        self.buildingSlot.color = (255,255,255)
        if self.building.pid == self.pid:
            self._update_visibility()
            self.set_neighbors_visibility()
        

        if type(self.building) == Database:
            self.numOfSlots = 4
            self.actionMenuSlots = get_action_menu_slots(self.numOfSlots, self.position[0], self.position[1])
            for troopSlot in self.troopSlots.keys()[4:]:
                troop = self.troopSlots[troopSlot].troop
                self.remove_troop(troop) # Why isn't this working?
        self.building = None
        return True


    # books a slot at the dest index when troop starts moving
    # returns index and slot
    def add_trans_troop(self, troop):
        if self.emptyTroopSlots:
            i, slot = self.emptyTroopSlots.popitem()
            self.transTroopSlots[troop] = (i, slot)
            return slot

    # move troop from trans to troop once done moving
    def set_trans_troop(self, troop):
        index, slot = self.transTroopSlots.pop(troop)
        slot.troop = troop
        troop.slotIndex = index
        self.troopSlots[index] = slot
        troop.update_opacity(255 * math.floor(troop.curVertex.visibilityState))
        if troop.pid == self.pid:
            self._update_visibility()
            self.set_neighbors_visibility()


    def remove_troop(self, troop):
        if troop.slotIndex in self.troopSlots.keys():
            slot = self.troopSlots.pop(troop.slotIndex)
        elif troop not in self.transTroopSlots.keys():
            # Silly bug fix
            return
        else:
            slot = self.transTroopSlots.pop(troop.slotIndex)
        slot.troop = None
        self.emptyTroopSlots[troop.slotIndex] = slot
        if troop.pid == self.pid:
            self._update_visibility()
            self.set_neighbors_visibility()


    def _update_visibility(self):
        visible=0
        c = objects.Objects.get_controller()
        if self.asID in c.visibleASes:
            visible = HALF_VISIBLE
        for v in self.adjacentVertices + [self]:
            if v.asID == self.asID:
                for slot in v.troopSlots.values():
                    if slot.troop.pid == self.pid:
                        visible = 1
                        break
                if v.building and v.building.pid == self.pid:
                    visible = 1
        self.set_visibility(visible)

    def set_neighbors_visibility(self):
        for neighbor in self.adjacentVertices:
            if neighbor.asID == self.asID:
                neighbor._update_visibility()

    def set_visibility(self, visibilityState, minimap=None):
        if self.visibilityState == visibilityState:
            return
        self.visibilityState = visibilityState

        for slot in self.troopSlots.values():
            slot.opacity = math.floor(visibilityState) * 255
            slot.troop.update_opacity(math.floor(visibilityState) * 255)

        for slot in self.transTroopSlots.values():
            slot[1].opacity = math.floor(visibilityState) * 255

        for slot in self.emptyTroopSlots.values():
            slot.opacity = math.floor(visibilityState) * 255


        self.opacity = math.ceil(visibilityState) * 255
        self.buildingSlot.opacity = math.floor(visibilityState) * 255
        if self.building:
            self.building.opacity = math.floor(visibilityState) * 255
        for edge in self.edges:
            edge.visible = bool(math.ceil(visibilityState))
        self.asCircle.opacity = math.ceil(visibilityState) * 255 * AS_OPACITY

    def highlight_adjacents(self, isHighlighted):
        if isHighlighted:
            for edge in self.edges:
                edge.old_stroke_width = edge.stroke_width
                edge.stroke_width = edge.stroke_width + 3
                # edge.color = ADJ_EDGE_COLOR
            # for vertex in self.adjacentVertices:
            #     if vertex.opacity == 255:
            #         vertex.color = HIGHLIGHTED_VERTEX_COLOR
        else:
            for edge in self.edges:
                edge.stroke_width = edge.old_stroke_width
                # edge.color = EDGE_COLOR
            # for vertex in self.adjacentVertices:
            #         vertex.color = VERTEX_COLOR



    def draw_empty_slot_sprites(self, gameMap):
        # This gets called on init and when a Database is added/removed. This
        # if accounts for both cases.

        curTroops = []
        curBuilding = None
        # remove current slots

        for slot in self.emptyTroopSlots.values():
            gameMap.batch_remove(slot)

        for slot in self.troopSlots.values():
            curTroops.append(slot.troop)
            gameMap.batch_remove(slot)   
            self.remove_troop(slot.troop)

        for slot in self.transTroopSlots.values():
            curTroops.append(slot.troop)
            gameMap.batch_remove(slot)   
            self.remove_troop(slot.troop)

        if self.buildingSlot:
            gameMap.batch_remove(self.buildingSlot)

        self.slotPositions = set_slots(self.numOfSlots, self.position[0], self.position[1])

        # add troop slots
        for i in range(self.numOfSlots):
            emptySlot = EmptyTroopSlot(
                self.slotPositions[i][0], self.slotPositions[i][1], self.opacity)
            gameMap.batch_add(emptySlot, z=SLOT_Z)
            self.emptyTroopSlots[i] = emptySlot

        self.actionMenuSlots = get_action_menu_slots(self.numOfSlots, self.position[0], self.position[1])

        # add building slot
        self.buildingSlot = EmptyBuildingSlot(
            self.position[0] + BUILD_OFFSET_X, self.position[1] + BUILD_OFFSET_Y, self.opacity)
        gameMap.batch_add(self.buildingSlot, z=SLOT_Z)
        self._update_visibility()

        for t in curTroops:
            self.add_troop(t)


class Core(Vertex):
    def __init__(self, col, row, vid, adjacentVertices, visibilityState=0, pid=0):
        super(Core, self).__init__(col, row, vid, adjacentVertices, visibilityState=0, pid=0,image=os.path.join("images", "maps", "core.png"))
        self.color = (255,255,255)

    def add_building(self, building):
        if self.building:
            return False
        building.slotIndex = 0
        self.building = building
        if building.pid == self.pid:
            self._update_visibility()
        return True

    def remove_building(self):
        if not self.building:
            return False
        self.building = None
        if building.pid == self.pid:
            self._update_visibility()
        return True

    def set_visibility(self, visibilityState, minimap=None):
        if visibilityState == self.visibilityState:
            return
        self.visibilityState = visibilityState
        self.opacity = 255 * math.ceil(visibilityState)
        if self.building:
            self.building.opacity = 255 * math.floor(visibilityState)

    def is_blocking_troop(self, troop, action):
        return False, False # this second return value is to deal with the firewall sound

    def _update_visibility(self):
        if self.building and self.building.pid == self.pid:
            self.set_visibility(1)
        else:
            self.set_visibility(HALF_VISIBLE)

    def set_neighbors_visibility(self):
        pass


class Edge(Line):
    def __init__(self, sourcePos, destPos, sourceV, destV, color, strokeWidth=3, visible=False):
        # Note: sourcePos and destPos are coordinates from the map file, NOT
        # points.
        start = (sourcePos[0] * CELL_SIZE, sourcePos[1] * CELL_SIZE)
        end = (destPos[0] * CELL_SIZE, destPos[1] * CELL_SIZE)
        super(Edge, self).__init__(start, end, color, strokeWidth)
        self.visible = visible
        self.color = color
        self.stroke_width = strokeWidth
        self.v1 = sourceV
        self.v2 = destV


class ASEdge(Edge):
    def __init__(self, sourcePoint, destPoint, sourceV, destV, color, strokeWidth=AS_EDGE_WIDTH, visible=False, speed=0.1):
        # sourcePoint and destPoints are Points (x,y)
        super(ASEdge, self).__init__(
            sourcePoint, destPoint, sourceV, destV, color, strokeWidth)
        self.visible = visible
        self.color = color
        self.speed = speed  # Used for AS edges.
        self.stroke_width = strokeWidth
        self.v1 = sourceV
        self.v2 = destV


class AS(object):
    def __init__(self, asID, vids, position=None, opacity=0):
        self.circles = {}  # vid is the key, asCircle object is the value.
        self.asID = int(asID)
        self.vids = vids
        self.vertices = {}
        self.cores = {}
        self.usedCores = {}
        self.position = position
        self.opacity = opacity * 255
        self.color = AS_COLORS[self.asID]


class ASCircle(Sprite):
    def __init__(self, position, color, scale=AS_SCALE, opacity=0):
        super(ASCircle, self).__init__(os.path.join("images",
                                                    "maps", "as_circle.png"))
        self.color = color
        self.scale = scale
        self.opacity = opacity
        self.position = euclid.Vector2(position[0], position[1])


class Map(scrolling.ScrollableLayer):

    def __init__(self, mapFileName, cm=None, numPlayers = None, AIPlayers = None, seed = None):
        super(Map, self).__init__()
        self.cm = cm

        self.batchableNode = BatchableNode()
        self.batchableNode.position = 0,0
        self.add(self.batchableNode,z=VERTEX_Z)

        # Initiliaze variables - these will be set in parse_map_file.
        self.vertexPositions = {}
        self.edgePositions = defaultdict(
            list)  # key: vid of one end, v: vid of other end

        self.AS = {}  # we can get list of vertices from here
        self.cores = {}  # k: just the cores
        self.vertices = {}  # k: all vertices and cores
        self.edges = []  # list of all edges

        self.startingUnits = defaultdict(lambda: defaultdict(list))
        self.startingResearch = defaultdict(list)
        self.availResearch = []

        self.w = - 1
        # Width of map in terms of num of cells. set in parse_map_file
        self.h = - 1
        # Height of map in terms of num of cells. set in parse_map_file

        self.players = []  # list of pids
        self.AIPlayers = []
        self.pid = 0
        if mapFileName == "random":
            # Generate a random map. Creates a map and writes it to the /maps/ directory. Returns the file name.
            # Set the seed.
            random.seed(seed)
            # Map Dimensions
            numRows = int(random.randint(6 * numPlayers, 14 * numPlayers)) # if 2 players, min of 12x12, max of 28x28
            numCols = int(random.randint(6 * numPlayers, 14 * numPlayers))
         
            # Number of ASes
            numASes = int(math.ceil((numCols * numRows) / 140.0)) # If 2 players, min of 2 ASes, max of 6.

            # Verts per AS
            minVertsPerAS = 2
            maxVertsPerAS = 4

            playerStartUnits = {0:[],1:[]}
            playerResearch = {0:[],1:[]}

            maxCoresPerAS = 2

            mapFileName = self.generate_random_map(numPlayers, numCols, numRows, playerStartUnits, playerResearch, minVertsPerAS, maxVertsPerAS, numASes, maxCoresPerAS, AIPlayers, seed)

        # Parses the map file and sets all relevant information.
        self.parse_map_file(mapFileName)
        
        self.minimap = None  # Starts as None. Eventually stores the instance of MiniMap built off this Map (happens in controller)

    def batch_add(self,cocosNode,z=1):
        self.batchableNode.add(cocosNode,z=z)

    def batch_remove(self,cocosNode):
        self.batchableNode.remove(cocosNode)

    def parse_map_file(self, mapFileName):

        with open(mapFileName, 'r') as f:
            row = 0  # updated when size found in map file
            isCellInfo = False
            for line in f:
                line = line.split()
                if len(line) == 0 or line[0] == "#":
                    continue
                elif line[0] == "MAP":
                    isCellInfo = True
                    self.w = int(line[1]) - 1
                    self.h = int(line[2]) - 1
                elif line[0] == "ENDMAP":
                    isCellInfo = False  # Rot to the end of cell info
                elif line[0] == "EDGES:" or line[0] == "CORE_EDGES:":
                    edgeList = []
                    for edge in line[1:]:
                        formattedEdge = re.findall("[0-9]+|[a-z]+", edge)
                        edgeList.append(formattedEdge)
                    for edge in edgeList:
                        self.edgePositions[edge[0]
                                           ].append(edge[1])  # edge[0] is key
                        self.edgePositions[edge[1]
                                           ].append(edge[0])  # edge[1] is key
                elif line[0] == "AS":
                    vertsInAS = []
                    for i in range(2, len(line)):  # Loop through info in AS line to grab relevant vertices, if only one, do a "n-n"
                        r = re.split('\-', line[i])
                        if r[0].isdigit():
                            vertsInAS += [str(v) for v in range(int(r[0]), int(r[1]) + 1)]
                        else: #add core
                            vertsInAS += [r[0]]
                    self.AS[int(line[1])] = AS(int(line[1]), vertsInAS)  # key is AS's ID
                elif "PLAYER" == line[0]:
                    # Loop through starting units and add them to the
                    # self.playerStartingUnits
                    pid = int(line[1])
                    self.players.append(pid)
                    for unit in line[2:]:
                        unit = unit.split(",")
                        unitType = unit[0]  # For clarity.
                        unitVert = unit[1]
                        self.startingUnits[pid][unitVert].append(unitType)
                elif line[0] == "AI":  
                    self.AIPlayers = line[1:]
                    self.AIPlayers = [int(i) for i in self.AIPlayers]
                    for p in self.AIPlayers:
                        self.players.remove(p)
                elif line[0] == "STARTRESEARCH":
                    pid = int(line[1])
                    for research in line[2:]:
                        self.startingResearch[pid].append(research)
                elif line[0] == "AVAILRESEARCH":
                    for research in line[1:]:
                        self.availResearch.append(research)
                elif isCellInfo == True:
                    col = 0
                    for cell in line:
                        if cell.isalpha() or cell.isdigit():
                            r = self.h - row
                            self.vertexPositions[cell] = (col, r)
                        col += 1
                    row += 1
        f.close()

    def draw_map(self):
        for asID in self.AS.keys():
            curAS = self.AS[asID]

            # create vertices
            for vid in curAS.vids:
                position = self.vertexPositions[str(vid)]
                if vid.isalpha():
                    v = Core(position[0], position[1], vid, asID, pid=self.pid)
                    self.cores[vid] = v
                    self.vertices[vid] = v
                    curAS.cores[vid] = v
                else:
                    v = Vertex(position[0], position[1], vid, asID, pid=self.pid)
                    v.asCircle = ASCircle(v.position, curAS.color)
                    v.color = curAS.color
                    curAS.circles[vid] = v.asCircle
                    v.draw_empty_slot_sprites(self)
                    curAS.vertices[vid] = v
                    self.vertices[vid] = v
                    #selfbatch_add(v.asCircle, z=AS_CIRCLE_Z)
                self.batch_add(v, z=VERTEX_Z)
        for v1, v2s in self.edgePositions.items():
            for v2 in v2s:
                position1 = self.vertexPositions[v1]
                position2 = self.vertexPositions[v2]
                vert1 = self.vertices[v1]
                vert2 = self.vertices[v2]
                if v1.isalpha() or (v2.isdigit() and (int(v1) > int(v2))):
                    # create edges
                    if vert1.asID != vert2.asID:  # create asEdge
                        vert1.borderVertices[vert2.asID].append(vert2)
                        vert2.borderVertices[vert1.asID].append(vert1)
                        edge = ASEdge(
                            position1, position2, vert1, vert2, AS_EDGE_COLOR)
                    else:  # create normal edge
                        edge = Edge(
                            position1, position2, vert1, vert2, EDGE_COLOR)
                    vert1.edges.append(edge)
                    vert2.edges.append(edge)
                    if not v1.isalpha():
                        vert1.adjacentVertices.append(vert2)
                        vert2.adjacentVertices.append(vert1)
                    self.edges.append(edge)

        # draw edges
        for v in self.edges:
            self.add(v, z=EDGE_Z)
            pass

    def generate_random_map(self, numPlayers, numCols, numRows, playerStartUnits, playerResearch, minVertsPerAS, maxVertsPerAS, numASes, maxCoresPerAS, AIPlayers, seed):
        # ---Add vertices and cores to each AS---
        ASvertices, AScores = self.add_verts_and_cores(numRows, numCols, minVertsPerAS, maxVertsPerAS, numASes, maxCoresPerAS)


        # ---Generate the map lines (cells)---
        mapLines, numCols, numRows, ASvertices, AScores = self.create_map_lines(numCols, numRows, ASvertices, AScores, maxVertsPerAS)

        # ---Generate edges in ASes and between ASes---
        edges, coreEdges = self.make_edges(numCols, numRows, ASvertices, AScores)

        # ---Write the map info to a file---
        playerStartUnits = [["Server","CPU"],["Server","CPU"]]
        fullMapName = self.write_map_info_to_file(mapLines, ASvertices, AScores, edges, coreEdges, numPlayers, playerStartUnits, playerResearch, AIPlayers)

        return fullMapName

    def add_verts_and_cores(self, numRows, numCols, minVertsPerAS, maxVertsPerAS, numASes, maxCoresPerAS):
        # Adds vertices and cores to each AS based on random info above.
        # RETURNS: tuple: (ASvertices (list), AScores (list))
        endVert = random.randint(minVertsPerAS, maxVertsPerAS)
        ASvertices = [range(0,endVert + 1)]  # Fill first AS with vertices so we start at 0. This is used for attaching vertex ID to each AS.

        for i in range(1, numASes):
            # Add one here since we are using range to generate the list.
            ASvertices.append(range(endVert + 1, 1 + random.randint(endVert + 2, endVert + 2 + random.randint(minVertsPerAS, maxVertsPerAS))))
            endVert = ASvertices[i][-1]

        endCore = 'b' # First AS will have 'a' and 'b'

        valList = range(ord('a'), ord(endCore) + 1)
        for j in range(len(valList)):
                valList[j] = chr(valList[j])

        # Generate CORES
        AScores = [valList]
        nextDigit = ''
        for i in range(1, numASes):
            # Fill AScores with cores.

            # Generate int list that corresponds to ASCII vals of chars
            lowerVal = ord(endCore[-1]) + 1
            upperVal = ord(endCore[-1]) + 1 + random.randint(1,maxCoresPerAS)
            if upperVal > 122 and nextDigit == '':
                # TODO: fix this! We have too many cores. Add an a to the '26' digit slot to start going into two digit core count.
                nextDigit = 'a'
                upperVal = (upperVal % 122) + 97
            elif upperVal > 122 and nextDigit != '':
                # We have too many cores. Increment our '26' digit slot.
                nextDigit = chr(ord(nextDigit) + 1)
                upperVal = (upperVal % 122) + 97
            valList = range(lowerVal, upperVal)
            
            # Convert int list to char list
            for j in range(len(valList)):
                valList[j] = nextDigit + chr(valList[j])
            AScores.append(valList)
            endCore = AScores[i][-1]

        return ASvertices, AScores

    def create_map_lines(self, numCols, numRows, ASvertices, AScores, maxVertices):
        # Generate map grid of proper dimensions
        # RETURNS: mapLines (list of lists of chars)
        mapLines = [["-" for i in range(int(numCols))] for j in range(int(numRows))]

        # Figure out where to place the ASes -> Use a bounding box to isolate AS locations
        numASes = len(ASvertices)
        # SET BOUNDING BOX SIZE -> If we want to change how 'spread out' ASes are, this is where to do it!!!
        dimensionFacilitator = maxVertices + 2
        boundingBoxWidth = random.randint(3,dimensionFacilitator)
        dimensionFacilitator -= boundingBoxWidth
        boundingBoxHeight = random.randint(3,min(max(3,dimensionFacilitator),maxVertices))

        # Define initial bounding box
        topLeft = (0,0)
        botRight = (topLeft[0] + boundingBoxWidth, topLeft[1] + boundingBoxHeight)

        # Define boundingBoxes
        boundingBoxes = [(topLeft,botRight)] # stores a tuple of topLeft, bottomRight points that define a boundingBox.

        # Populate the list <boundingBoxes> with the coordinates of all possible boundingBoxes for ASes
        boxesPlaced = 0
        while boxesPlaced < (numASes + numASes):
            # While guarantees we have placed sufficient boundingBoxes.
            if botRight[0] + boundingBoxWidth > numCols:
                # We're at the right edge of mapLines and can't fit another box, so wrap around.
                topLeft = (1,botRight[1] + 3) # +3 so we don't overlap. and to spread the ASes out a bit
            else:
                # Set topLeft to be the next boundingBox over
                topLeft = (botRight[0] + 3, topLeft[1]) # +3 so we don't overlap. and to spread the ASes out a bit
            if (botRight[1] + boundingBoxHeight) > numRows:
                # We're at the bottom and haven't added enough bounding boxes yet. Expand the map a bit.
                numCols += 1
                numRows += 1
                for i in range(len(mapLines)):
                    row = mapLines[i]
                    row.append("-")
                    mapLines[i] = row
                mapLines.append(["-" for row in range(int(numCols))])
            else:
                # Set bottomRight point to be the topLeft point, + boundBoxWidth and + boundBoxHeight
                botRight = (topLeft[0] + boundingBoxWidth, topLeft[1] + boundingBoxHeight)
                boundingBoxes.append((topLeft,botRight))
                boxesPlaced += 1

        # Loop through each AS and add its vertices and cores to a bounding box.
        for i in range(numASes):
            # For clarity
            nextASverts = ASvertices[i]
            nextAScores = AScores[i]

            # Pick a bounding box. Remove the boundingBox from <boundingBoxes>.
            try:
                topLeft, botRight = random.choice(boundingBoxes)
                boundingBoxes.remove((topLeft, botRight))
            except:
                # We've used every bounding box! Can't place any more ASes
                break

            # Add vertices to the AS bounding box.
            vertIndex = 0
            while vertIndex < len(nextASverts):
                vert = nextASverts[vertIndex]
                vertRow = random.randint(topLeft[0], max(min(len(mapLines) - 1, botRight[0]),topLeft[0] + 1)) # Pick a ROW
                vertCol = random.randint(topLeft[1], max(min(len(mapLines[-1]) - 1, botRight[1]),topLeft[1] + 1)) # Pick a COLUMN
                try:
                    while mapLines[vertRow][vertCol] != "-":
                        # Slot we picked was already taken. Look for an empty slot.
                        vertRow = random.randint(topLeft[0], min(len(mapLines) - 1, botRight[0])) # Pick a ROW
                        vertCol = random.randint(topLeft[1], min(len(mapLines[-1]) - 1, botRight[1])) # Pick a COLUMN
                    # Found an empty slot in the bounding box. Place the vertex.
                    mapLines[vertRow][vertCol] = vert
                    vertIndex += 1
                except:
                    ASvertices[i].remove(vert)

                    # Decrement vertices we haven't added yet.
                    for j in range(len(ASvertices[i])):
                        if ASvertices[i][j] > vert:
                            ASvertices[i][j] -= 1
                    # Don't increment our index, we just want to redo the next vert since we removed..

            try:
                # Add cores to the AS bounding box.
                for core in nextAScores:
                    coreRow = random.randint(topLeft[0], max(min(len(mapLines) - 1, botRight[0]),topLeft[0] + 1)) # Pick a ROW
                    coreCol = random.randint(topLeft[1], max(min(len(mapLines[-1]) - 1, botRight[1]),topLeft[1] + 1)) # Pick a COLUMN
                    while mapLines[coreRow][coreCol] != "-":
                        # Slot we picked was already taken. Look for an empty slot.
                        coreRow = random.randint(topLeft[0], min(len(mapLines) - 1, botRight[0])) # Pick a ROW
                        coreCol = random.randint(topLeft[1], min(len(mapLines[-1]) - 1, botRight[1])) # Pick a COLUMN
                    # Found an empty slot in the bounding box. Place the vertex.
                    mapLines[coreRow][coreCol] = core
            except:
                AScores[i].remove(core)

        return mapLines, numCols, numRows, ASvertices, AScores

    def make_edges(self, numCols, numRows, ASvertices, AScores):
        # Randomizes edges between the vertices. Ensures they are connected.
        # RETURNS: <tuple> (edgeList, coreEdgeList)

        edgeList = []
        coreEdgeList = []

        # Generate edge for each individual AS
        for AS in ASvertices:
            # Loop through each AS to get the list of vertices in that AS.
            vertList = sorted(list(AS)) # Copies the vertices in AS to vertList (need to do this since we will end up destroying vertList)
            
            # Generate  a random prufer seq based on the vertices.
            pruferSeq = self.generate_prufer_seq(sorted(list(AS)))
            
            edgeList += self.generate_mst(pruferSeq, vertList)

        # Connect the ASes
        asBorderRouters = []
        for AS in ASvertices:
            if len(AS) > 0:
                asBorderRouters.append(random.choice(AS))

        ASpruferSeq = self.generate_prufer_seq(list(asBorderRouters)) # Once again, have to list() asBorderRouters so it doesn't destroy it.
        
        edgeList += self.generate_mst(ASpruferSeq, asBorderRouters)

        # Generate core edges. # TODO: IMPROVE
        for i in range(len(AScores)):
            for j in range(len(AScores[i])):
                if len(ASvertices[i]) > 0:
                    core = AScores[i][j]
                    randomVertInSameAS = random.choice(ASvertices[i])
                    coreEdgeList.append([randomVertInSameAS, core])

        return edgeList, coreEdgeList

    def generate_prufer_seq(self, vertList):
        # Given a list of vertices, generates a random prufer code.

        # Take lowest and put it in to exhausted.
        if len(vertList) == 0:
            return []
        exhausted = [vertList.pop(0)]
        pruferSeq = []

        while len(vertList) > 0:
            try:
                randVert = random.choice(exhausted)
                pruferSeq.append(randVert)
                new = vertList.pop(0) # remove from vertList and add it to exhausted
                exhausted.append(new)
            except:
                # Handles corner cases.
                break

        return pruferSeq

    def generate_mst(self, pruferSeq, vertList):
        # Build an MST from prufer code.
        if len(pruferSeq) == 0:
            return []
        vertList.remove(pruferSeq[0])
        edgeList = []
        while True:
            if len(pruferSeq) == 1:
                edgeList.append([vertList[0], pruferSeq[0]])
                break
            elif len(vertList) == 2:
                # Done.
                edgeList.append([vertList[0], pruferSeq[0]])
                edgeList.append([vertList[1], pruferSeq[1]])
                break
            else:
                nextVert = None
                for vert in vertList:
                    if vert != pruferSeq[0]:
                        nextVert = vert
                        vertList.remove(vert)
                        break
                otherVert = pruferSeq.pop(0)
                edgeList.append([nextVert, otherVert])
        return edgeList

    def write_map_info_to_file(self, mapLines, ASvertices, AScores, edges, coreEdges, numPlayers, playerStartUnits, playerResearch, AIPlayers):
        # Writes a map file based on the randomized information.
        mapName = "random" + str(random.randint(1, 1000)) + ".map"
        numRows = len(mapLines)
        numCols = len(mapLines[0])
        # DEBUG print "mapName: ", mapName
        fullMapName = os.path.join("maps", "random", mapName)
        newMapFile = file(fullMapName, "w")

        # Add edges
        edgeString = " "
        for edge in edges:
            temp = str(edge).replace(" ", "")  # Remove the space to work with the parser.
            edgeString += temp + " "
        
        # Add coreEdges
        coreEdgeString = " "
        for coreEdge in coreEdges:
            temp = str(coreEdge).replace(" ", "").replace("\'","")  # Remove the space to work with the parser.
            coreEdgeString += temp + " "
        newMapFile.write("EDGES:" + edgeString + "\n")
        newMapFile.write("CORE_EDGES:" + coreEdgeString + "\n")

        for index in range(len(ASvertices)):
            AS = ASvertices[index]
            # Format cores to write
            AScoreList = ""
            for core in AScores[index]:
                AScoreList += core + " "
            # Write the cores and vertices to the AS line
            if len(AS) > 0:
                newMapFile.write("AS " + str(index) + " " + str(AS[0]) + "-" + str(AS[-1]) + " " + AScoreList + "\n")

        newMapFile.write("\n")
        # Write dimensions to the map
        newMapFile.write("MAP " + str(numCols) + " " + str(numRows) + "\n")

        # Write the mapLines
        for line in mapLines:
            newMapFile.write(self.list_to_string(line) + "\n")
        newMapFile.write("ENDMAP\n")
        newMapFile.write("\n")

        # Add player units
        for i in range(0,numPlayers):
            nextUnitString = ""
            for j in range(len(playerStartUnits[i])):
                if len(ASvertices[i]) > 0:
                    # Assign a vertex and/or core to each unit/cpu. 
                    if playerStartUnits[i][j] != "CPU":
                        nextUnitString += playerStartUnits[i][j] + "," + str(random.choice(ASvertices[i])) + " "
                    elif len(AScores) > 0:
                        nextUnitString += playerStartUnits[i][j] + "," + str(random.choice(AScores[i])) + " "
            if len(ASvertices[i]) > 0: 
                newMapFile.write("PLAYER " + str(i) + " " + str(nextUnitString) + "\n")
        if AIPlayers != None:
            newMapFile.write("\n")
            for AI in AIPlayers:
                AIstring = str(AI)
                newMapFile.write("AI " + AIstring + "\n")
        newMapFile.write("\n")
        newMapFile.close()
        return fullMapName

    def list_to_string(self, l):
        # Takes a list and converts its contents to a string. (basically a custom list-> string casting function)
        s = ""
        for item in l:
            s += str(item) + " "
        return s

    def get_path(self, source, dest, pid, troop, action=None):
        '''
            Djikstra's Algorithm from Wikipedia:
            http://en.wikipedia.org/wiki/Dijkstra's_algorithm
        '''

        vertices = []

        for vertex in self.vertices.values():
            if not vertex.is_blocking_troop(troop, action)[0]:
                h = HeapItem(vertex, sys.maxint)
                vertex.heapItem = h
                vertices.append(h)
                if vertex == source:
                    h.depth = 0

        heapq.heapify(vertices)

        while vertices:
            u = heapq.heappop(vertices)
            if u.vertex == dest and u.depth != sys.maxint:
                # Bingo
                path = []
                while u:
                    path.append(u.vertex.vid)
                    u = u.parent
                path.reverse()
                return path

            for vertex in u.vertex.adjacentVertices:
                if not vertex.is_blocking_troop(troop, action)[0]:
                    v = vertex.heapItem

                    alt = u.depth + 1
                    if alt < v.depth:
                        v.depth = alt
                        v.parent = u
                        vertices.append(v)
                        # TODO: make this more efficient, can't use siftdown because of garbage collector
                        heapq.heapify(vertices)
            
        return None

    # DEPRECATED FOR MULTIPLAYER, use get_path instead
    def get_moveable_path(self, sourceVertex, destVertex, pid, troop=None):
        # Returns the shortest path of vertices to get from sourceVertex to destVertex that the player can move to (cannot use vertices where opponent has a FireWall, or invisible vertices)
        # NOTE: only works for PLAYER move. We need to write account for enemy moving into invisible vertices (changes movability logic)
        # |-> should change this so it works for both. just don't allow exploration beyond an AS if the AS hasn't been discovered yet.
        vertices = sourceVertex.adjacentVertices

        if (type(troop) != EncryptedTroop) and (type(destVertex.building) == Firewall or type(destVertex.building) == Database) and destVertex.building.pid != pid:
            return False

        head = HeapItem(sourceVertex, 0)

        heapVertices = []
        for vertex in vertices:
            # CONSOLIDATE THIS INTO A vertex.isBlocked property
            if vertex.visibilityState > 0 and (type(troop) == EncryptedTroop or type(vertex.building) != Firewall or vertex.building.pid == pid):
                heapVertex = HeapItem(vertex, 1, head)
                heapq.heappush(heapVertices, heapVertex)
            else:
                pass
        numVerticesInMap = len(self.vertices)
        # So we don't have to calculate this each time through the loop.
        deadVerts = []
        while head.vertex != destVertex:
            if len(deadVerts) > numVerticesInMap:
                # NOTE: This condition is really bad... We should probably fix
                # it.
                return False

            head = heapq.heappop(heapVertices)
            newMoves = head.vertex.adjacentVertices

            for vertex in newMoves:
                if vertex.visibilityState > 0 and (type(troop) == EncryptedTroop or type(vertex.building) != Firewall or vertex.building.pid == pid):
                    # Only add a vertex to the path if it's visible, or if it
                    # does not have an Enemy Firewall in the way.
                    heapVertex = HeapItem(vertex, head.depth + 1, head)
                    # Don't add the vertex if we've already found it, or if it
                    # contains an Enemy firewall | BUT we might want to check
                    # to see if we've gotten to that vertex with less depth.
                    if heapVertex.vertex.vid not in [heapVert.vertex.vid for heapVert in heapVertices] and heapVertex.vertex not in deadVerts:
                        # or (heapVertex.vertex in [heapVert.vertex for
                        # heapVert in heapVertices] and heapVertex.head.depth <
                        # heapVertices[heapVertices.indexOf(heapVertex)].head.depth)
                        heapq.heappush(heapVertices, heapVertex)
                else:
                    deadVerts.append(vertex)

        path = []
        while head.getParent():
            path.insert(0, head.vertex)
            head = head.getParent()
        path.insert(0, head.vertex)
        return path

    def get_vertex(self, vid):
        if vid.isalpha():
            return self.cores[vid]
        return self.vertices[vid]


class MiniMap(Sprite):
    def __init__(self, ASes, numMapCols, numMapRows, edges, player):
        super(MiniMap, self).__init__(os.path.join("images",
                                                   "maps", "minimap_bg.png"))
        self.edges = edges
        self.minimapBuildings = {}
        self.minimapTroops = {}
        self.opacity = 255
        self.scale = 0.6
        self.mapCellWidth = numMapCols * CELL_SIZE
        self.mapCellHeight = numMapRows * CELL_SIZE
        self.ASes = ASes
        self.cshape = aabb_to_aa_rect(self.get_AABB())
        self.player = player
        self.setup()

    def setup(self):
        self.miniMapCircles = {}
        self.edgeList = []
        for asID in self.ASes:
            for vid in self.ASes[asID].circles.keys():
                # NOTE: these two lines will DEFINITELY need to change if we
                # change the size of the minimap, or its location!!!!
                # HARDCODED.
                circ = self.ASes[asID].circles[vid]
                newX = self.get_rect().width * circ.position[0] / self.mapCellWidth - 124
                newY = self.get_rect().height * circ.position[1] / self.mapCellHeight - 142

                newPosition = (newX, newY)
                color = circ.color
                self.miniMapCircles[vid] = MiniMapCircle(
                    newPosition, circ.position, color, 1)
        # for edge in self.edges:
        #     edgeStart = None
        #     edgeEnd = None
        #     if type(edge.v1) == Vertex:
        #         edgeStart = self.miniMapCircles[edge.v1.vid]
        #     if type(edge.v2) == Vertex:
        #         edgeEnd = self.miniMapCircles[edge.v2.vid]
        #     if edgeStart and edgeEnd:
        #         # coords: 615 138
        #         # coords: 594 99
        #         edge = MiniMapEdge((615, 138), (594, 99),
        #                           (615, 138), (594, 99), EDGE_COLOR)
        #         self.edgeList.append(edge)

# Silly fix for now.


class MiniMapEdge(Line):
    def __init__(self, miniCircleSourcePos, miniCircleDestPos, sourceV, destV, color, strokeWidth=1):
        # Note: start and end are endpoints
        start = miniCircleSourcePos
        end = miniCircleDestPos
        super(MiniMapEdge, self).__init__(start, end, color, strokeWidth)
        self.color = color
        self.stroke_width = strokeWidth
        self.v1 = sourceV
        self.v2 = destV


class MiniMapCircle(Sprite):
    def __init__(self, position, asPosition, color, scale, building=False):
        super(MiniMapCircle, self).__init__(os.path.join("images",
                                                         "maps", "minimap_circle.png"))
        self.color = color
        self.scale = scale
        self.position = euclid.Vector2(float(position[0]), float(position[1]))
        self.asPosition = asPosition  # position of AS associated with this circle
        # self.cshape = aabb_to_aa_rect(self.get_AABB())
        self.cshape = collision_model.CircleShape(
            euclid.Vector2(x=self.position[0], y=self.position[1]), 14)
        if building:
            self.building = Sprite(os.path.join(
                'images', 'maps', 'minimap_building.png'), position=euclid.Vector2(float(position[0]), float(position[1])))
            # self.batch_add(circle, z=MINMAP_CIRCLE_Z) Circle is undefined
