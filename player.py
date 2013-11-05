import time
import threading
import thread
import random

from pyglet.event import EventDispatcher
from cocos.layer import *
from cocos.text import * \
    # Delete later. Just using for now to get a text version of cpu count
from cocos.scene import Scene

from constants import *
from research import RESEARCH
from models import *
from game_layers import TransTimer
from utils import *
from imageLayer import *
from controller import *

from utils import *


class Player(EventDispatcher, Layer):

    def __init__(self, ID, gameMap, colman, color, special=None):
        super(Player, self).__init__()
        self.map = gameMap
        self.cm = colman

        self.ID = ID
        self.color = PLAYER_COLOR[self.ID]
        self.special = None

        self.troops = []
        # contains all sorts of buildings (including research!)
        self.buildings = []

        # the buildings that are currently under construction
        self.underConstruction = []

        #TODO: integrate research with player default actions list
        # number ot indicate completed research
        self.completedResearch = 1
        # research we haven't completed but is avialable
        self.availableResearch = []
        # all the research available for this level
        self.allResearch = []

        self.startingLevel = 1  # starting level of research

        self.visibleAS = set()  # set of ASes that are visible
        # troops that become available after research
        self.availableTroops = []
        self.idleCPUs = []
        self.busyCPUs = []

        self.unitActionLists = DEFAULT_ACTIONS #in constants

        self.has_server = True

        self.numServers = 1

        self.aiPlayerIDs = self.map.AIPlayers

    def step(self, dt):
        # self.check_loss()
        toRemove = []
        for unit in self.underConstruction:
            unit.health += unit.maxHealth * (dt / unit.buildTime)
            if not self.ID in self.aiPlayerIDs:
                try:
                    unit.opacity = (unit.health / unit.maxHealth) * (
                    255 - UNIT_STARTING_OPACITY) + 255
                except ZeroDivisionError:
                    unit.opacity = 255 # Silly fix for encyrpt units for now.
            if unit.health >= unit.maxHealth:
                if not self.ID in self.aiPlayerIDs:
                    unit.opacity = 255
                if issubclass(type(unit), Troop):
                    self.troops.append(unit)
                elif issubclass(type(unit), Building):
                    self.buildings.append(unit)
                self.cm.add(unit)
                toRemove.append(unit)
        for unit in toRemove:
            self.underConstruction.remove(unit)
            if not self.ID in self.aiPlayerIDs:
                unit.curVertex.set_visibility_old(1, self.cm, self.map.minimap)

        pass

    def setup(self):
        # Add starting info that was loaded from the map file
        for r in self.map.startingResearch[self.ID]:  # ?
            self.completedResearch *= RESEARCH[r].uid
        for r in self.map.availResearch:
            if self.completedResearch % RESEARCH[r].dependencies == 0:
                self.availableResearch.append(r)
        self.allResearch = self.map.availResearch
        for t in self.map.startingUnits[self.ID]:
            self.availableTroops.append(t)
        for vertID in self.map.startingUnits[self.ID]:
            curVert = self.map.get_vertex(vertID)
            unitsInVert = self.map.startingUnits[self.ID][vertID]
            for strUnitType in unitsInVert:
                unitType = eval(strUnitType)
                if issubclass(unitType, Building):
                    self.add_building(unitType, vertID)
                elif issubclass(unitType, Troop):
                    self.add_troop(unitType, vertID)
            if type(curVert) == Vertex:
                self.visibleAS.add(curVert.asID)
        if self.ID not in self.aiPlayerIDs:
            self.setup_visibility()

    # in its own function for clarity
    def setup_visibility(self):
        for v in self.map.vertices.values():
            if v.asID in self.visibleAS:
                v.set_visibility_old(HALF_VISIBLE, self.cm,self.map.minimap)

    def add_troop(self, troopType, vid, oldTroop = None):
        curVertex = self.map.get_vertex(vid)
        if oldTroop != None:
            # Encrypting a troop.
            newTroop = EncryptedTroop(curVertex = oldTroop.curVertex, position = oldTroop.curVertex.position, health = oldTroop.health, pid = self.ID, speed = oldTroop.speed, originalType = type(oldTroop))
        else:
            # Just adding a new troop.
            newTroop = troopType(curVertex,pid=self.ID)
        if not self.ID in self.aiPlayerIDs:
            newTroop.opacity = UNIT_STARTING_OPACITY
        else:
            newTroop.opacity = 0
        newTroop.color = self.color
        newTroop.pid = self.ID
        newTroop.push_handlers(self.on_destruction)
        self.map.add(newTroop, TROOP_Z)
        self.underConstruction.append(newTroop)
        self.dispatch_event("player_add_troop", troopType)
        return newTroop

    def add_building(self, buildingType, vid):
        curVertex = self.map.get_vertex(vid)
        if curVertex.building is None or buildingType == CPU:
            if buildingType == RSA:
                curVertex.color = (0,0,0)
                self.map.remove(curVertex)
                self.map.add(curVertex, z = RSA_Z)
                newBuilding = buildingType(curVertex,player=self,pid=self.ID)
            else:
                newBuilding = buildingType(curVertex,pid=self.ID)

            if not self.ID in self.aiPlayerIDs:
                newBuilding.opacity = UNIT_STARTING_OPACITY
            else:
                newBuilding.opacity = 0
            newBuilding.color = self.color
            newBuilding.pid = self.ID
            self.map.add(newBuilding, z=BUILDING_Z)
            newBuilding.push_handlers(self.on_destruction)
            self.underConstruction.append(newBuilding)
            if buildingType == CPU:
                self.idleCPUs.append(newBuilding)
            return newBuilding

    # def change_troop_to_type(self, oldTroop, newType):
    #         action = CallFunc(self.player.on_destruction, troopToEncrypt)
    #         action += CallFunc(self.player.add_troop, type(oldTroop), oldTroop.curVertex, oldTroop) # this call is a bit silly but it lets us avoid making two versions of add troop
    #         self.do(action)


    def execute_build_cpu(self, vertex, builder):
        builder.opacity = 200
        cores = vertex.adjacentCores
        if cores:
            curCore = cores.pop()
            newCPU = self.add_building(CPU, curCore.vid)
            timer, action = self.start_cpu(newCPU.buildTime, newCPU)
            action += CallFunc(self.busyCPUs.remove, newCPU)
            action += CallFunc(self.on_destruction, builder)
            timer.do(action)
        else:
            pass
            # DEBUG
            # print "no cores available"

    def execute_build_building(self, buildingName, unit, selectedUnits=None):
        if buildingName == "CPU":
            # unit.oldActionList = unit.actionList # Store the old action list so we can restore it if we choose to cancel.
            # unit.actionList = ["CANCEL"]
            self.execute_build_cpu(unit.curVertex, unit)
            # self.on_destruction(unit)
        
        if len(self.idleCPUs) > 0 and unit.curVertex.building == None:
            # Determine building type to build
            unit.opacity = 200
            # unit.oldActionList = unit.actionList # Store the old action list so we can restore it if we choose to cancel.
            # unit.actionList = ["CANCEL"]

            buildingType = ALL_UNITS[buildingName]
            cpu = self.idleCPUs.pop()
            building = self.add_building(buildingType, unit.curVertex.vid)

            timer, action = self.start_cpu(building.buildTime, cpu)
            action += CallFunc(self.stop_cpu, cpu)
            action += CallFunc(self.on_destruction, unit)  # After the building is finished, destroy the builder. We should also add a cancel button to the action menu.
            self.dispatch_event("player_add_building", buildingType)
            cpu.action = action
            timer.do(action)
            return True  # Successfully built.
        else:
            # print "Building already in vertex OR no idle CPUs available"
            return False  # Failed build.

    def execute_build_troop(self, troopName, unit, selectedUnits=None):
        # Build a Troop
        if len(self.idleCPUs) > 0 and None in unit.curVertex.troops:
            troopType = ALL_UNITS[troopName]
            cpu = self.idleCPUs.pop()
            troop = self.add_troop(troopType, unit.curVertex.vid)
            timer, action = self.start_cpu(troop.buildTime, cpu)
            action += CallFunc(self.stop_cpu, cpu)
            timer.do(action)
            return True
        else:
            # print "Building already in vertex OR no idle CPUs available"
            return False

    def perform_research(self, researchChoice, researchFacility, cm):
        if len(self.idleCPUs) > 0:
            cpu = self.idleCPUs.pop()
            researchType = RESEARCH[researchChoice]
            timer, action = self.start_cpu(researchType.buildTime, cpu)
            action += CallFunc(self.stop_cpu, cpu)
            action += CallFunc(self.finish_research, researchChoice)
            action += CallFunc(self.update_research_fac_menu, researchFacility, self.map, cm)
            cpu.action = action
            timer.do(action)
            return True
        return False

    def update_research_fac_menu(self, researchFacility, gameMap, cm):
        # Clears and displays the research factory menu so that it reflects the changes made my research (otherwise can double execute research which crashes)
        if researchFacility.isSelected != False:
            menuUpdate = CallFunc(researchFacility.clear_action_menu, self.map, cm, self)
            menuUpdate += CallFunc(researchFacility.display_action_menu, self.map, cm, self)
            self.do(menuUpdate)

    def start_cpu(self, sec, cpu, action=None):
        self.busyCPUs.append(cpu)
        transTimer = TransTimer(sec, pos=cpu.position)
        cpu.transTimer = transTimer
        moveAction = transTimer.get_move_action(action)
        self.map.add(transTimer, z=TIMER_Z)
        self.unitActionLists["CPU"].append("CANCEL")
        return transTimer, moveAction

    def cancel_cpu(self, cpu):
        if cpu in self.busyCPUs:
            cpu.action.stop()
            cpu.transTimer.kill()
            self.stop_cpu(cpu)

    def stop_cpu(self, cpu):
        if cpu in self.busyCPUs:
            self.unitActionLists["CPU"].remove("CANCEL")
            self.busyCPUs.remove(cpu)
            self.idleCPUs.append(cpu)

    def unit_attack(self, attackers, targets):
        # TODO: need a for loop for multiple attackers and targets
        attacker = attackers.pop()
        target = targets.pop()
        if issubclass(type(attacker), Unit) and issubclass(type(target), Unit):
            path = self.map.get_path(attacker.curVertex, target.curVertex)
            if len(path) <= attacker.range:
                attacker.attack(target, path, self.map)
                self.dispath_event("player_unit_attack", attacker)
                return True
            else:
                print "path too long"
                return False

    def on_destruction(self, unit, selectedUnits=None, cmRemove = True):
        # Deletes this unit from the game. Note: assume the menu has been
        # cleared aleady.
        if not unit.isDestroyed:
            if issubclass(type(unit), Troop):
                unit.curVertex.remove_troop(unit)
                self.troops.remove(unit)
            else:
                unit.curVertex.building = None
                self.buildings.remove(unit)
            self.map.remove(unit)
            
            if cmRemove:
                self.cm.remove_tricky(unit)
            unit.isDestroyed = True

            if issubclass(type(unit), Server):
                self.numServers -= 1
        # Every time a unit is destroyed, check if I have lost

    def check_loss(self):
        if len(self.troops) == 0 and len(self.buildings) == 0:
            self.dispatch_event("on_loss", self)

    def switch_units_select_state(self, units, selectedUnits):
        # Switches the select state of <units>
        for unit in units:
            if unit is not None and ((issubclass(type(unit), Troop) and not unit.are_actions_running()) or issubclass(type(unit), Building)) and unit.pid == self.ID:
                unit.set_is_selected(not unit.isSelected, self.map, self.cm, self)
                if unit.isSelected:
                    selectedUnits.append(unit)
                else:
                    selectedUnits.remove(unit)

    '''MARK: Research Methods'''

    def update_research_action_button(self, researchFactory):
        researchFactory.actionList = ["DEL"]
        researchFactory.actionList += self.availableResearch

    def update_troop_action_button(self, algorithmFactory):
        algorithmFactory.actionList = ["DEL"]
        algorithmFactory.actionList += self.availableTroops

    def finish_research(self, newR):
        newResearch = RESEARCH[newR]
        newResearch.on_completion(self)
        self.completedResearch *= newResearch.uid
        # self.availableTroops += newResearch.units make this more generic
        # self.availableResearch.remove(newR) # REMOVE FOR NOW
        for s in self.allResearch:
            research = RESEARCH[s]
            if (self.completedResearch % research.dependencies) == 0 and (self.completedResearch % research.uid != 0) and (s not in self.availableResearch):
                # first cond ensures we have met dependencies
                # second cond ensures we haven't done the research already
                self.availableResearch.append(s)

    def building_complete(self, building):
        self.dispatch_event('on_building_complete')

Player.register_event_type('on_loss')
Player.register_event_type('player_add_troop')
Player.register_event_type('player_unit_attack')
Player.register_event_type('player_add_building')


class ComputerPlayer(Player):
    '''
    The premise of this AI is to use a FINITE STATE MACHINE to react "intelligently" to a human player.
    The states of this machine are defined below. An "N-Gram" will be used to collect data about player moves.
    The "A-Star" pathfinding algorithm will be employed to find the most efficient way to attack.
    '''
    def __init__(self, ID, gameMap, cm, color, enemy):
        super(ComputerPlayer, self).__init__(ID, gameMap, cm, color)
        self.aiRunning = False
        self.theMap = gameMap
        self.aiID = ID
        self.ai_levels = ["Easy", "Medium", "Hard", "Godlike"] # I wish there was an enumerator in Python.
        self.ai_level = "Easy"
        self.ai_states = ["Initial", "Waiting", "Scanning", "Researching", "Attacking", "Building", "Defending"] # Finite State Machine States.
        self.max_move_per_move = 4 # This could be better named.
        self.max_attack_per_move = 5 # Same here.
        self.enemy = enemy # That's the human.
        self.color = (70, 0, 180) # Feel free to change.
        self.ai_cur_state = "" # Always set to blank on new instance of AI!
        self.ai_troops = 0 # The number of troops available to the AI.
        self.human_troops = 0 # Number of troops available to human player.
        self.all_troops = 0 # All troops on the board.
        self.human_cpus = 1 # Will always be at least one, else AI wins.
        self.board_research_level = 1 # The level of research currently allowed on the board.
        self.discovered = False # Set to true when humans make first contact (discover) AI troops.
        self.health = 1000 # Set to what Kat decides for the top menu.
        self.human_health = 1000 # Self explanatory.
        self.adjacent_free_slots = 0 

    def scan(self):
        # Brute Force Information Gathering. 
        pass
        # print self.troops
        # print self.enemy.availableTroops

    def scan_all_vertices(self):
        # DEBUG
        # print len(self.enemy.availableTroops)
        for vertex in self.theMap.vertices.values():
            for troop in vertex.troopSlots.values():
                self.all_troops += 1
        # print "Number of Human Troops:", len(self.units) # was breaking
        # print "Number of All Troops:", self.all_troops
        #print "Number of AI Troops:", 
        self.human_troops = 0
        self.ai_troops = 0
        #print self.enemy.availableTroops

        #print self.troops
        #for vertex in self.enemy.availableTroops[0].curVertex.adjacentVertices:
            #print vertex.troopSlots

    def run_basic_ai(self):
        thread.start_new_thread(self.ai_loop, ())

    def ai_loop(self):
        # FST (Yes, it is a bunch of if statements)
        while True:
            if self.ai_cur_state == "":
                # print "[ai] cur_state is blank, setting to initial."
                self.ai_cur_state = "Initial"
            if self.ai_cur_state == "Initial":
                # print "[ai] state: Initial"
                self.scan_all_vertices()
            else:
                pass
                # DEBUG
                # print "unknown case."
            time.sleep(4)
        '''
        while True:
            time.sleep(3)
            units_left = self.max_move_per_move
            attack_left = self.max_attack_per_move
            for unit in self.troops:
                if unit.power > 0:
                    target = self.select_target(unit)
                    if target is not None:
                        if attack_left == 0:
                            break
                        path = self.map.get_path(
                            unit.curVertex, target.curVertex)
                        unit.attack(target, path, self.map)
                        attack_left -= 1
                    else:
                        if units_left == 0:
                            break
                        units_left -= 1
                        if not self.enemy.troops and not self.enemy.buildings:
                            return
                        target = random.choice(
                            self.enemy.troops + self.enemy.buildings)
                        unit.move(target.curVertex, self.map, self.cm)
        '''
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
