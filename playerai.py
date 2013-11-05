import time
import threading
import thread
import random

from random import choice, randint
from pyglet.event import EventDispatcher
from cocos.layer import *
from cocos.text import *
from cocos.scene import Scene
from cocos.actions.interval_actions import Delay
from constants import *
from research import RESEARCH
from models import *
from maps import Core
from game_layers import TransTimer
from utils import *
from imageLayer import *
from player_new import Player
from utils import *
import objects

'''
AI TODO: Non Gratum Anus Rodentum: Yasin Dara

- [DONE] Need to prevent crashing by preventing "move" and "attack" from being called too rapidly. (check if action is being performed, cocos method)
- [DONE] Need to figure out how to make the AI detect TYPES of troops/units so that we don't try to attack with a server or something stupid like that.
- [DONE] Also need to figure out how to read from the map file directly to "cheat" and make the AI knowledgeable about all starting locations of Servers.
- [DONE (Fix Swarm)] Heatmap: AI needs to prioritize attacking groups of four human units that are on a single vertex.
- [DEFERRED] N-Gram
- [DONE] Yasin just discovered the need for spoof.
- [DONE] Build a function called "Swarm" that does exactly what you think it does. }:-)
- [DONE] Trigger AI only after 60 seconds or when AI AS is invaded.
- [DONE] Randomly attack troops and buildings with free range AI troops to add variety to AI movement and gameplay.
- [DEFERRED] Allow the AI to use different attack strategies for different types of troops and units.  

      .o.       ooooo 
     .888.      `888' 
    .8"888.      888  
   .8' `888.     888  
  .88ooo8888.    888  
 .8'     `888.   888  
o88o     o8888o o888o 
 , _                                    _       
/|/ \                                  | |      
 |   |   __ _|_  _           __   ,_   | |   ,  
 |   |  /  \_|  |/  |  |  |_/  \_/  |  |/_) / \_
 |   |_/\__/ |_/|__/ \/ \/  \__/    |_/| \_/ \/ 

(C) Carleton College 2013

'''


class ComputerPlayer(Player):
    '''
    The premise of this AI is to use a FINITE STATE MACHINE to react "intelligently" to a human player.
    The states of this machine are defined below. An "N-Gram" will be used to collect data about player moves.
    The "A-Star" pathfinding algorithm will be employed to find the most efficient way to attack. The AI will
    prioritize vertices containing human-built troops based on a "heatmap", which allows the AI to prioritize 
    resources and its own troops. 
    '''
    def __init__(self, ID):
        super(ComputerPlayer, self).__init__(ID)
        self.server = objects.Objects.get_controller()
        self.totalTime = 0
        self.aiRunning = False
        self.theMap = self.server.map
        self.aiID = ID
        self.aiLevels = ["Easy", "Medium", "Hard", "Godlike"]  # I wish there was an enumerator in Python.
        self.aiLevel = "Easy"  # Don't mess with this, it isn't implemented yet.
        self.aiStates = ["Initial", "Waiting", "Scanning", "Researching", "Attacking", "Building", "Defending",
                        "Determining"]  # Finite State Machine States.
        self.maxMovePerMove = 1  # This could be better named.
        self.maxAttackPerMove = 3  # Same here.
        self.enemy = self.server.players  # That's the human.
        self.color = (70, 0, 180)  # Feel free to change.
        self.ai_cur_state = ""  # Always set to blank on new instance of AI!
        self.ai_prev_state = "Initial" # Always set to initial on new instance of AI!
        self.aiTroops = 0  # The number of troops available to the AI.
        self.humanTroops = 0  # Number of troops available to human player.
        self.allTroops = 0  # All troops on the board.
        self.humanCpus = 1  # Will always be at least one, else AI wins.
        self.boardResearchLevel = 1  # The level of research currently allowed on the board.
        self.discovered = False  # Set to true when humans make first contact (discover) AI troops.
        self.health = 1000  # Set to what Kat decides for the top menu.
        self.humanHealth = 1000  # Self explanatory.
        self.adjacentFreeSlots = 0 # To a vertex.
        self.genericCounter = 0  # Used as a makeshift timer, sometimes.
        self.numUnitsToBuild = 0  # This is just here.
        self.enemyBuildingVertices = []  # Will be filled in by scan function.
        self.enemyTroopVertices = []  # Will be filed in by scan function.
        self.highPriorityEnemyVertices = []  # If four troops are in a vertex, it becomes a higher priority than the server.
        self.aiTroopVertices = []  # Will keep track of ai troops [unit, unit.curVertex]
        self.defensePriorityOneLocation = [] # [unit, vid] Location (vid) of my server! Defend at all costs!
        self.timeWaited = 0 # Self explanatory. Add "dt" to this periodically to get the total time waited since the AI was first called.
        self.swarmCompletion = 0 # Number of units already built into a partially completed "swarm". 1 swarm = 4 units on 1 vertex.
        self.swarmVertices = [] # Vertices with available swarms.
        self.swarmVertex = None # The current vertex where a swarm is being built. 
        self.swarmNumber = 0 # The number of the current swarm that we are about to marshall as our troops.
        self.troopvertex = None # A counter to keep track of unit delegation within a swarm. 
        self.lastAttackTroop = None # if this is still moving, then we can't ask it to attack!
        self.troopsPOWMIA = [] # Troops that have been sent off on their duty. These might be destroyed!
        self.troopsAtTheReady = [] # Troops that we have at the ready!
        self.troopsPoised = [] # The AI can't issue an attack command right away. These units are in position to attack on the next loop.
        self.threatVertices = [] # Vertices that are within 2 distance of our Server. 
        self.respondingTroops = [] # Troops designated as currently attacking or moving towards a unit to attack.
        self.myASes = [] # A list of the AI ASes.
        self.aiVertices = [] # A list of the vertices that I own.
        self.buildLimit = 0 # The number of troops that I am allowed to build for this level.
        self.numTroopsBuilt = 0 # The number of troops that the AI has built.
        self.triggerTime = 120 # The number of seconds the AI waits before attacking.  

    def scan(self):
        pass

    def scan_all_vertices(self):

        for player in self.server.players.values():
            if player.pid != self.pid:
                listOfUnits = player.units.values()
                self.humanTroops = len(listOfUnits)
            if player.pid == self.pid:
                listOfUnits = player.units.values()
                self.aiTroops = len(listOfUnits)

        # Where is my server?
        for unit in player.units.values():
            if issubclass(type(unit), Building) == True:
                # # /print "The type of this unit is: ", str(type(unit)), "and the type of that is ", type(type(unit))
                if type(unit) == Server:
                    # if str(type(unit)) == "<class 'models.Server'>": # OH GOD WHY.
                    # # /print "My server is located at ", unit.curVertex.vid
                    self.defensePriorityOneLocation = [unit, int(unit.curVertex.vid)]

        # Where are the enemy servers?
        self.enemyBuildingVertices = []  # Reset "global" list.
        for vertex in self.server.map.vertices.values():
            if type(vertex.building) == Server and vertex.building.pid != self.pid:
                # # /print "There is an enemy server located at: ", vertex.vid
                self.enemyBuildingVertices.append(int(vertex.vid))
        # # /print "This is the list containing enemy servers: ", self.enemyBuildingVertices

        # Where are my troops?
        self.aiTroopVertices = []  # Reset "global" list.
        for unit in player.units.values():
            # print unit, type(unit), issubclass(type(unit), Troop)
            if issubclass(type(unit), Troop) == True and unit.pid == self.pid:
                if unit.power > 0:
                    self.aiTroopVertices.append([unit, unit.curVertex.vid])
        # # /print "My (AI) Troops: ", self.aiTroopVertices

        # Where are the enemy troops?
        self.enemyTroopVertices = []
        for player in self.server.players.values():
            if player.pid != self.pid:
                for unit in player.units.values():
                    if issubclass(type(unit), Troop) == True:
                        self.enemyTroopVertices.append([unit, unit.curVertex.vid])
        # # /print "Enemy Troops: ", self.enemyTroopVertices

        # What should we prioritize?
        # Logic: If there are 4 troops clustered somewhere, attack this first, then the server.
        # The above may be flawed logic, but no AI is perfect.
        self.highPriorityEnemyVertices = []
        for vertex in self.server.map.vertices.values():
            priorityCounter = 0
            for slot in vertex.troopSlots.values():
                if issubclass(type(slot.troop), Troop) and slot.troop.pid != self.pid:
                    priorityCounter += 1
            if priorityCounter > 3:
                self.highPriorityEnemyVertices.append(vertex)
        # # /print "Enemy Vertices with 4 Troops: ", self.highPriorityEnemyVertices

        # Where are my ASes? And where are my vertices?
        self.myASes = []
        self.aiVertices = []
        for vertex in self.server.map.vertices.values():
            if vertex.building != None and vertex.building.pid == self.pid:
                self.myASes.append(vertex.asID)
        for myvertex in self.server.map.vertices.values():
            if myvertex.asID in self.myASes:
                self.aiVertices.append(myvertex)

        # Set build limit. 
        self.buildLimit = 4 * len(self.aiVertices)
        # print "INITIAL BUILD LIMIT: ", self.buildLimit

        '''
        # DISCARDED CODE ---------------------------------------------------------------------------------
        #for slot in vertex.troopSlots.values():
        #for slot in vertex.troopSlots.values():
        ## /print "At vertex ", vertex.vid, " there is a ", vertex.building, " with this stuff ", slot.troop

        # A GOOD SET OF TROOPS: DOS,2 DOS,2 DOS,18 DOS,18 Ping,31 DOS,17 Ping,35 DOS,14 DOS,14 DOS,14 DOS,14 Ping,35 Ping,35 Ping,35 Ping,33 Ping,33

        #self.human_troops = 0
        #self.ai_troops = 0

        #print self.troops
        #for vertex in self.enemy.availableTroops[0].curVertex.adjacentVertices:
            #print vertex.troopSlots
        '''
    def trigger(self):
        if len(self.aiVertices) > 0:
            for vertex in self.aiVertices:
                for slot in vertex.troopSlots.values():
                    if slot.troop != None:
                        if slot.troop.pid != self.pid:
                            #print "[AI] TRIGGERED!!!", slot.troop, slot.troop.curVertex.vid
                            return True
        return False


    def mathematical_probability(self, boundary=50):
        randomInt = randint(1,100)
        if randomInt <= boundary:
            return True
        else:
            return False 

    # Pick a unit that isn't in a swarm, choose something random on the map to attack, and send if off!
    def random_search_and_destroy(self):
        #Attack with Poised Units
        attackingUnit = None
        if len(self.troopsPoised) > 0:
            for poisedTroop in self.troopsPoised:
                self.perform_single_target_attack(poisedTroop[0],poisedTroop[1])
                # /print "[ai] A random attack against", poisedTroop[0], "by", poisedTroop[1], "from", poisedTroop[1].curVertex.vid, "to", poisedTroop[0].curVertex.vid
                if poisedTroop in self.troopsPoised:
                    self.troopsPoised.remove(poisedTroop)
                ## /print "LIST OF THINGS GETTING ATTACKED:", self.troopsPoised

        if len(self.troopsAtTheReady) == 0:
            for unit in self.units.values():
                #print "[AI] ALL AI UNITS", unit
                if unit.curVertex != self.swarmVertex and unit.curVertex.vid not in self.swarmVertices and issubclass(type(unit), DOS) == True:
                    #print "[AI] FREE RANGE UNIT: ", unit
                    attackingUnit = unit
                    self.troopsAtTheReady.append(attackingUnit)
                    # /print "[ai] AVAILABLE FREE RANGE TROOPS: ", self.troopsAtTheReady
        else:
            for unit in self.troopsAtTheReady:
                attackingUnit = unit
    
        #print "[AI] ATTACKING UNIT MUST BE DEFINED: ", attackingUnit
        if attackingUnit == None:
            #print "[AI] There are no free range units left. Cannot attack!"
            self.reassign_troops()
            return
        #Randomly Assign a Target


        if self.mathematical_probability(50) == True:
            #Attack Building
            for vertex in self.server.map.vertices.values():
                if vertex.building != None and vertex.building.pid != self.pid:
                    attackFrom = self.get_closest_safe_adjacent_vertex(vertex.vid, False)
                    if attackingUnit.isSelectable == True and attackFrom != None:
                        #print "[AI] Moving troop to attack building: ", attackingUnit
                        self.perform_single_target_random_move(attackFrom, attackingUnit)
                        self.troopsPoised.append([vertex.building, attackingUnit])
                        if attackingUnit in self.troopsAtTheReady:
                            self.troopsAtTheReady.remove(attackingUnit)
                    
        else:
            #Attack Troop
            for player in self.server.players.values():
                if player.pid != self.pid:
                    for eunit in player.units.values():
                        if issubclass(type(eunit), Troop) == True:
                            # /print "UNIT GETTING ATTACKED: ", eunit, "at", eunit.curVertex.vid
                            attackFrom = self.get_closest_safe_adjacent_vertex(eunit.curVertex.vid, False)
                            if attackingUnit.isSelectable == True and attackFrom != None:
                                #print "[AI] Moving troop to attack troop: ", attackingUnit
                                self.perform_single_target_random_move(attackFrom, attackingUnit)
                                self.troopsPoised.append([eunit, attackingUnit])
                                if attackingUnit in self.troopsAtTheReady:
                                    self.troopsAtTheReady.remove(attackingUnit)

                ## /print "Available Units: ", unit, "at", unit.curVertex.vid  
                #for swarmVid in self.swarmVertices:
                ## /print "THINGS NOT TO INCLUDE!", swarmVid, self.server.map.vertices[str(swarmVid)]
                #if unit.curVertex != self.server.map.vertices[str(swarmVid)]:
                          
    # Builds a swarm vertex (i.e. fills a vertex with DOS troops belonging to AI)
    def swarm_vertex(self, swarmCompletion, swarmVertex=None):
        if swarmVertex == None:
            self.swarmVertex = self.get_closest_empty_vertex()
        returnVal = self.build_a_troop("DOS", self.swarmVertex.vid)
        if returnVal != None:
            self.swarmCompletion += 1
            if self.swarmCompletion == 4:
                self.swarmCompletion = 0
                self.swarmVertices.append(returnVal.curVertex.vid)
                # /print "[ai] A new swarm is available: ", self.swarmVertices
                self.swarmVertex = None
        else:
            return self.swarmCompletion
        return self.swarmCompletion
        

    # Builds a DOS at a specified location. TODO: Update this function to build more than DOS troops.
    def build_a_troop(self, unitType, locationVid):
        # /print "[ai] Building a ", unitType," at location ", locationVid
        # print "CUR BUILD LIMIT BEFORE ATTEMPT TO BUILD: ", self.buildLimit, self.numTroopsBuilt
        if self.numTroopsBuilt > self.buildLimit:
            returnVal = None
            return returnVal
        else:
            returnVal = self.server.build_unit("DOS", self, locationVid)
            self.numTroopsBuilt += 1
            return returnVal

    # Finds a fully empty vertex on the map and returns it. Checks for both buildings and troops.
    def get_closest_empty_vertex(self):
        for vertex in self.server.map.vertices.values():
            ## /print "SUBCLASSING VERTICES: ", type(vertex)
            if not type(vertex) == Core and vertex.building == None and vertex.troopSlots.values() == []:
                return vertex

    # DEPRECATED.
    def grab_inactive_troop(self):
        pass

    # Move troops accordingly, and attack with them...
    # A swarm consists of 4 DOS units that work as a unit.
    def marshall_troops(self, swarmNumber=0):
        numTroopsToActivate = 0
        if swarmNumber != 0:
            swarmNumber = self.swarmNumber
        if len(self.swarmVertices) != 0 and len(self.highPriorityEnemyVertices) != 0:
            marshallVertex = self.swarmVertices[swarmNumber]
            attackersPosition = self.highPriorityEnemyVertices[swarmNumber]
            attackFromPosition = self.get_closest_safe_adjacent_vertex(attackersPosition.vid, safe=False)
            ## /print "ATTACKING FROM", attackFromPosition.vid
            ## /print "ATTACKING THIS VERTEX", attackersPosition.vid
            ## /print "NUMBER OF TROOPS THAT YOU CAN SEND", 4 - len(attackFromPosition.troopSlots.values())
            ## /print "THE TROOP THAT YOU'RE MOVING", self.server.map.vertices[str(self.swarmVertices[swarmNumber])].troopSlots.values()[troopvertex].troop
            ## /print "THE TROOP THAT YOU'RE ATTACKING", self.highPriorityEnemyVertices[swarmNumber].troopSlots.values()[troopvertex].troop
            numTroopsToActivate = 4 - len(attackFromPosition.troopSlots.values())
            ## /print "SWARMNUMBER", swarmNumber

            #Move!
            ## /print "UNIT 1", self.server.map.vertices[str(self.swarmVertices[swarmNumber])].troopSlots.values()[].troop
            ## /print "UNIT 2", self.server.map.vertices[str(self.swarmVertices[swarmNumber])].troopSlots.values()[].troop
            ## /print "UNIT 3", self.server.map.vertices[str(self.swarmVertices[swarmNumber])].troopSlots.values()[].troop
            ## /print "UNIT 4", self.server.map.vertices[str(self.swarmVertices[swarmNumber])].troopSlots.values()[].troop
            ## /print "ATTEMPTING TO MOVE -----------------------------------------------------------"
            for key in self.server.map.vertices[str(self.swarmVertices[swarmNumber])].troopSlots.keys():
                attackTroop = self.server.map.vertices[str(self.swarmVertices[swarmNumber])].troopSlots[key].troop
                self.perform_single_target_random_move(attackFromPosition, attackTroop)          

            #self.perform_single_target_random_move(attackFromPosition, self.server.map.vertices[str(self.swarmVertices[swarmNumber])].troopSlots.values()[0].troop)
            #self.perform_single_target_random_move(attackFromPosition, self.server.map.vertices[str(self.swarmVertices[swarmNumber])].troopSlots.values()[1].troop)
            #self.perform_single_target_random_move(attackFromPosition, self.server.map.vertices[str(self.swarmVertices[swarmNumber])].troopSlots.values()[0].troop)
            #self.perform_single_target_random_move(attackFromPosition, self.server.map.vertices[str(self.swarmVertices[swarmNumber])].troopSlots.values()[0].troop)
            
            #Attack!
            #self.perform_single_target_attack(self.highPriorityEnemyVertices[swarmNumber].troopSlots.values()[troopvertex].troop, self.server.map.vertices[str(self.swarmVertices[swarmNumber])].troopSlots.values()[troopvertex].troop)
            ## /print "[ai] MOVED AND ATTACKED -----------------------------------------------------------"             
            self.highPriorityEnemyVertices.pop(0)
            self.swarmVertices.pop(0) 
            # /print "[ai] A high priority vertex has been swarmed!"
            self.troopvertex = attackFromPosition
            self.lastAttackTroop = attackTroop
            return 
        else: 
            # /print "[ai] No swarm ready, or no high priority vertices."
            return 0

    def swarm_attack(self, attackFromPosition):
        # /print "[ai] NOW ATTACKING !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        if self.lastAttackTroop.isSelectable == False:
            # /print "[ai] STILL MOVING! DAMMIT!"
            return
        else:
            pass
            # /print "[ai] ATTACK OK"
        attackTroops = []
        victimTroops = []
        for key in attackFromPosition.troopSlots.keys():
            attackTroops.append(attackFromPosition.troopSlots[key].troop)
        if len(self.highPriorityEnemyVertices) > 0:
            vertexOfInterest = self.highPriorityEnemyVertices[0]
            if vertexOfInterest == None:
                #print "[AI] Couldn't locate any high priority vertices."
                return
            for key in vertexOfInterest.troopSlots.keys():
                victimTroops.append(vertexOfInterest.troopSlots[key].troop) 
            for i in range(4):
                self.perform_single_target_attack(victimTroops[i], attackTroops[i])
            self.troopvertex = None
            self.highPriorityEnemyVertices.remove(vertexOfInterest) # We don't care if attack was successful.
        else: 
            #print "[AI] An enemy swarm was detected but troops are not available to respond yet."
            return



        # Returns an empty vertex (a vertex with no enemy troops or one enemy troop)
        # that is near a vertex of interest.
    def get_closest_safe_adjacent_vertex(self, vidOfInterest, safe=True):
        vertexOfInterest = self.server.map.vertices[str(vidOfInterest)]
        if safe == False:
            for vertex in self.server.map.vertices.values():
                if vertexOfInterest in vertex.adjacentVertices:
                    ## /print "[ai] The adjacent vertex is: ", vertex.vid
                    return vertex
        elif safe == True:
            for vertex in self.server.map.vertices.values():
                if vertexOfInterest in vertex.adjacentVertices:
                    if vertex.troopSlots.values() == []:
                        ## /print "[ai] The safest vertex is: ", vertex.vid
                        return vertex

    def check_if_valid_for_attack(self, attacker, victim):
        # /print "[ai] Check if this unit is a valid attacker: ", attacker
        return issubclass(type(attacker), Troop) and attacker.power > 0

    def perform_single_target_attack(self, victim="void", attacker="void"):
        if victim == "void":
            for player in self.server.players.values():
                if player.pid != self.pid:
                    listOfUnits = player.units.values()
                    victim = choose(listOfUnits)
                    break
        if attacker == "void":
            listOfUnits = self.units.values()
            attacker = choose(listOfUnits)
        if self.check_if_valid_for_attack(attacker, victim):
            # # /print "Attacker: ", attacker
            # # /print "Victim: ", victim
            self.server.attack_unit(victim, attacker)
        else:
            # /print "[ai] can't attack"
            pass

    def perform_single_target_random_move(self, destination=0, troopToMove=0):
        if destination == 0 or troopToMove == 0:
            for unit in self.units.values():
                thesource = unit.curVertex
                thedest = choice(unit.curVertex.adjacentVertices)
                thetroop = unit
                thepid = self.pid
                ## /print "[ai] self.pid", self.pid
                # thepath = self.server.map.get_path(thesource, thedest, thepid, thetroop) # WTF, Don't look at client controller.
                # # /print "thepath", thepath # We apparently don't need a dijkstra's path. I don't know why, but who cares.
                if not thetroop.are_actions_running():
                    returnVal = self.server.move_unit(thedest, thetroop, thepid)
                    thesource = ""
                    thedest = ""
                    thetroop = ""
                    thepid = ""
                    thepath = ""
                    ## /print "[ai] I have moved a unit! ", returnVal
        elif not troopToMove.are_actions_running():
            returnVal = self.server.move_unit(destination, troopToMove, self.pid)
            ## /print "[ai] Path: ", returnVal
            # # /print "[ai] Execute Action: I've moved a unit!"

    # Check if there is an enemy unit that has a coincident vertex with one of our units.
    # This is flawed: Careful players will craftily attack from one vertex away.
    def check_defenses(self):
        for player in self.server.players.values():
            if player.pid != self.pid:
                enemyUnits = player.units.values()
        for enemyUnit in enemyUnits:
            for aiUnit in self.units.values():
                if aiUnit.curVertex == enemyUnit.curVertex:
                    # /print "[ai] The two coincident units are: ", aiUnit, " at ", aiUnit.curVertex.vid, " and ", enemyUnit, " at ", enemyUnit.curVertex.vid
                    return True
        return False

    # If there is an enemy troop within 2 distance of our server, just kill it using Free Range troops.
    # The AI is smart enough to realize that if you handshake to the server's vertex, it will defend the
    # server from units located at the new vertex as well. 
    def defend_our_server(self):
        #print "[AI] defend_our_server function called."
        threateningTroops = []
        serverVid = self.defensePriorityOneLocation[1]
        serverUnit = self.defensePriorityOneLocation[0]
        serverVertex = self.server.map.vertices[str(serverVid)]
        #print "SERVER VERTEX", serverVertex, serverVertex.vid
        #print "SERVER VERTEX ADJACENT VERTICES", serverVertex.adjacentVertices
        for adjVertex in serverVertex.adjacentVertices:
            if adjVertex not in self.threatVertices:
                self.threatVertices.append(adjVertex)
            for distantVertex in adjVertex.adjacentVertices:
                if distantVertex not in self.threatVertices:
                    self.threatVertices.append(distantVertex)
        #print "THREAT VERTICES: ", self.threatVertices
        for player in self.server.players.values():
            if player.pid != self.pid:
                enemyUnits = player.units.values()
        #print "ENEMY UNITS: ", enemyUnits
        for eUnit in enemyUnits:
            for vertex in self.threatVertices: 
                if eUnit.curVertex == vertex:
                    threateningTroops.append(eUnit)
        #print "[AI] Detected troops close to or attacking our server:"
        #for item in threateningTroops:
            #print "[AI] <Detected> ", item, item.curVertex.vid
        self.attack_with_list_of_troops(threateningTroops)
        

    def attack_with_list_of_troops(self, victimList):
        for victim in victimList:
            availableTroops = self.get_units_within_attacking_distance(victim.curVertex)
            if len(availableTroops) > 0:
                attackingTroop = choice(availableTroops)
                self.perform_single_target_attack(victim, attackingTroop)
                self.respondingTroops.append(attackingTroop)
            else:
                #print "[AI] No troops within range to respond to threat. Building."
                responseVertex = self.get_closest_safe_adjacent_vertex(victim.curVertex.vid)
                if responseVertex == None:
                    #print "[AI] Troop has already been taken care of, no need to build."
                    return
                self.build_a_troop("DOS", responseVertex.vid)



    def get_units_within_attacking_distance(self, passVertex):
        #print "PASSVERTEX", passVertex.vid
        theAdjacentVertices = [passVertex]
        theAttackingTroops = []
        for adjVertex in passVertex.adjacentVertices:
            theAdjacentVertices.append(adjVertex)
            for distantVertex in adjVertex.adjacentVertices:
                theAdjacentVertices.append(distantVertex)
        for searchVertex in theAdjacentVertices:
            for key in searchVertex.troopSlots.keys():
                if searchVertex.troopSlots[key].troop.pid == self.pid and searchVertex.troopSlots[key].troop not in self.respondingTroops:
                     theAttackingTroops.append(searchVertex.troopSlots[key].troop)
        #print "[AI] Troops available to respond to threat:", theAttackingTroops
        return theAttackingTroops 

    def reassign_troops(self):
        #print "[AI] Reassigning Troops"
        for unit in self.units.values():
            if issubclass(type(unit), DOS) == True and not unit.is_attacking:
                if unit in self.respondingTroops:
                    self.respondingTroops.remove(unit)
                    #print "[AI] Unit designated as no longer responding: ", unit, unit.curVertex.vid
                if unit not in self.troopsAtTheReady:
                    self.troopsAtTheReady.append(unit)
                    #print "[AI] Unit designated as at the ready: ", unit, unit.curVertex.vid  

    # DEPRECATED. Keep here for reference to how the AI reacts to things. 
    def perform_defensive_reaction(self):
        # If an exploratory human troop comes to rest in a vertex with one of our troops in it:
        # Our troop (the AI troop) will immediately start attacking the incoming troop.
        for player in self.server.players.values():
            if player.pid != self.pid:
                listOfUnits = player.units.values()
        for unit in self.units.values():
            for enemyUnit in listOfUnits:
                if unit.curVertex == enemyUnit.curVertex:
                    # destination = self.server.map.vertices[str(self.enemyBuildingVertices[0])]
                    #destination = self.get_closest_safe_adjacent_vertex(unit.curVertex.vid, False)
                    destination = self.server.map.vertices[str(self.enemyBuildingVertices[0])]
                    # /print "[ai] The troop we're marshalling: ", self.aiTroopVertices[0][0], " and location ", destination.vid
                    for defender in self.units.values():
                        if issubclass(type(defender), DOS) == True and defender.pid == self.pid and not defender.are_actions_running():
                            if defender.power > 0:
                                returnVal = self.server.move_unit(destination, self.aiTroopVertices[0][0], self.pid)
                                ## /print "Are actions running: ", self.aiTroopVertices[0][0].are_actions_running()
                                if not self.aiTroopVertices[0][0].are_actions_running():
                                    self.perform_single_target_attack(enemyUnit, self.aiTroopVertices[0][0])
                                    return


    # FSM [Finite State Machine]
    def ai_loop(self, dt):
        self.totalTime += dt
        
        if self.ai_cur_state == "":
            #print "[AI] cur_state is blank, setting to initial."
            # print "[AI] is ON."
            self.ai_cur_state = "Initial"

        if self.ai_cur_state == "Initial":
            #print "[AI] state: Initial"
            self.scan_all_vertices()
            self.ai_cur_state = "Waiting"

        if self.ai_cur_state == "Waiting":
            #print "[AI] state: Waiting"
            self.timeWaited += dt
            if self.timeWaited < self.triggerTime and not self.trigger():
                #print "[AI] The AI is being patient: Elapsed Time: ", self.timeWaited, "Time Limit: ", self.triggerTime
                return
            self.timeWaited = 0
            self.genericCounter += 1
            self.ai_cur_state = "Determining"  # Change state to scannning always at the end of waiting.

        if self.ai_cur_state == "Researching":
            # # /print "[ai] state: Researching"
            pass

        if self.ai_cur_state == "Scanning":
            # /print "[ai] state: Scanning"
            self.scan_all_vertices()
            self.ai_prev_state = "Scanning"

        if self.ai_cur_state == "Determining":
            #print "[AI] state: Determining (an action to take)"
            if self.ai_prev_state == "Initial":
                self.ai_prev_state = "Building"
                #print "[AI] Set To Build..."
                return

            #print "[AI] NOW ai_cur_state", self.ai_cur_state
            #print "[AI] NOW ai_prev_state", self.ai_prev_state

            if self.ai_prev_state == "Building":
                self.ai_cur_state = "Attacking"
            if self.ai_prev_state == "Attacking":
                self.ai_cur_state = "Defending"
            if self.ai_prev_state == "Defending":
                self.ai_cur_state = "Building"

            if self.troopvertex != None:
                #print "PROBLEM VERTEX: ", self.troopvertex, self.troopvertex.vid
                self.swarm_attack(self.troopvertex)
           
            if self.check_defenses() == True:
                #print "[AI] <<< Detected Enemy Attack >>> "
                pass

        if self.ai_cur_state == "Building":
            #print "[AI] state: Building"
            if len(self.swarmVertices) > 2:
                self.swarm_vertex(self.swarmCompletion, self.swarmVertex)
                self.ai_prev_state = "Building"
                self.ai_cur_state = "Determining"
                return
            else:
                self.ai_prev_state = "Building"
                self.ai_cur_state = "Determining"
                return

        if self.ai_cur_state == "Attacking":
            #print "[AI] state: Attacking"
            self.random_search_and_destroy()
            self.marshall_troops(self.swarmNumber)
            self.reassign_troops()
            self.ai_prev_state = "Attacking"
            self.ai_cur_state = "Determining"
            return

        if self.ai_cur_state == "Defending":
            #print "[AI] state: Defending"
            self.defend_our_server()
            self.ai_prev_state = "Defending"
            self.ai_cur_state = "Determining"
            return

    # Deprecated. Keep for reference.
    def select_target(self, unit):
        for vertex in unit.curVertex.adjacentVertices + [unit.curVertex]:
            for troop in vertex.troops:
                # have to incorporate range somehow, can't just look at adjacent vertices
                # implement something like objs_within_range
                if troop is not None and troop.pid != self.ID:
                    return troop
                if vertex.building != None:
                    return vertex.building
        return None
