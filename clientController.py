import cocos
import cocos.euclid as eu
import utils
import math
import twisted
import random
from twisted.internet.endpoints import TCP4ClientEndpoint, TCP4ServerEndpoint
from twisted.python.log import err
from twisted.internet.error import *
from twisted.internet import reactor

from cocos import collision_model
from cocos.director import director
from cocos.layer import Layer
from cocos.layer.scrolling import ScrollingManager
from cocos.actions.instant_actions import CallFuncS
from cocos.actions.interval_actions import Delay


from pyglet.event import EventDispatcher
from pyglet.window import key

import constants
from commands import *
from constants import *
from imageLayer import ImageLayer
from maps import Map, Vertex
from models import *
from player_new import Player

from utils import get_action_button_clicked
from playerai import ComputerPlayer
from research import RESEARCH
from game_layers import StatusMenu, InfoLayer, SettingsLayer,ActionButton,TransTimer, MenuButton, HotkeysLayer, StickyNote, TutorialXButton
import music
from game import EndMenu
from tutorial import *
from server import ClientNoteFactory
from client import ServerNoteFactory

class ClientController(Layer,EventDispatcher):
    is_event_handler = True

    def __init__(self,mapName):
        super(ClientController, self).__init__()

        if mapName: #if there's no mapName, the server's passing it in at some point
            self.map = self._init_map_and_cm(mapName)
        
        if SHOW_TUTORIAL:
            self._add_tutorial(mapName)
        else:
            self.tutorial = None


        self.curLevel = 1

        self.curAction = None

        self.selectedUnits = []  # units selected by the current player

        self.players = {}  # k:pid, v: player object

        self.player = None  # the player on this computer

        self.playerList = []  # list of pid for all players

        self.pid = -1

        self.arrow_flags = {key.LEFT: 0, key.RIGHT: 0, key.UP: 0, key.DOWN: 0}

        self.mouse_flags = {"x": 0, "y": 0}

        self.ip = ""  # ip address, lazily instentiated

        self.serverStarted = False

        self.connectedToServer = False

        self.endpoint = None

        self.visibleASes = set()

        self.isControlDown = False # For Hotkeying

        self.hotKeyedUnits = {
            key._0 : None,
            key._1 : None,
            key._2 : None,
            key._3 : None,
            key._4 : None,
            key._5 : None,
            key._6 : None,
            key._7 : None,
            key._8 : None,
            key._9 : None
            }

    def _add_tutorial(self, mapName):
        if mapName == "level1":
            self.tutorial = Tutorial(1,self)
            return
        elif mapName[:-1] == "level" and mapName[-1] in [str(i) for i in range(2,6)]:
            # Adds the sticky note for levels 2-5
            self.tutorial = None
            self.stickyNote = StickyNote(mapName[-1])
            self.stickyXButton = TutorialXButton(self.stickyNote)
            self.map.add(self.stickyNote)
            self.map.add(self.stickyXButton)
            self.cm.add(self.stickyXButton)

    def _init_map_and_cm(self,mapName):
        if mapName == "srandom" or mapName == "sRandom" or mapName == "sr" or mapName == "sR":
            # Single player random -> adds AI
            self.mapName = str(random.randint(100,10000))
            m = Map("random", numPlayers = 2, AIPlayers = ["1"], seed = int(self.mapName))
        elif mapName == "random" or mapName == "Random" or mapName == "r" or mapName == "R":
            # Multi player random -> doesn't add AI
            self.mapName = str(random.randint(100,10000))
            m = Map("random", numPlayers = 2, seed = int(self.mapName))
        elif mapName.isdigit():
            m = Map("random", numPlayers = 2, seed = int(mapName))
            self.mapName = mapName
        else:
            m = Map(os.path.join("maps", mapName + ".map"))
            self.mapName = mapName
        # self.map = Map(os.path.join("maps", "random", "random487.map"))
        self.cm = collision_model.CollisionManagerGrid(
            -BLEED, m.w * CELL_SIZE + BLEED, -BLEED, m.h * CELL_SIZE + BLEED, CELL_SIZE / 2, CELL_SIZE / 2)
        m.cm = self.cm
        self.scroller = ScrollingManager(viewport=director.window)
        self.scroller.add(m)

        self.h = CELL_SIZE * m.h
        if self.h < WINDOW_HEIGHT:
            self.h = WINDOW_HEIGHT

        self.w = CELL_SIZE * m.w
        if self.w < WINDOW_WIDTH:
            self.w = WINDOW_WIDTH

        return m

    def on_enter(self):
        super(ClientController, self).on_enter()
        if constants.MUSIC:
            music.theme_player.play()
        if self.tutorial:
            self.tutorial.first_prompt("on_enter")
            self.push_handlers(
                self.tutorial.player_add_unit, self.tutorial.player_unit_attack)
            self.push_handlers(
                self.tutorial.click_on_move, self.tutorial.click_on_action)
        self.schedule(self.step)
        self.infoLayer = InfoLayer(self.map, self.scroller, self.pid)
        self.settingsMenu = SettingsLayer()
        self.statusMenu = StatusMenu(self.settingsMenu,self.player)
        self.hotkeysLayer = HotkeysLayer(self.hotKeyedUnits,self.scroller)
        self.hotkeysLayer.toggle_hotkeys_menu()
        self.add(self.statusMenu,z=1)
        self.add(self.infoLayer,z=1)
        self.add(self.settingsMenu,z=2)
        self.add(self.hotkeysLayer,z=2)


    def end_game(self, didWin):
        self.stop_server()
        if constants.MUSIC:
            music.theme_player.stop()
        
        for child in self.map.get_children():
            child.stop()

        if didWin:
            s = cocos.scene.Scene(EndMenu("Won",self.curLevel))
        else:
            s = cocos.scene.Scene(EndMenu("Lost",self.curLevel))
        s.add(ImageLayer(os.path.join("images", "backgrounds", "menu-chalkboard.png")),z=-1)
        cocos.director.director.replace(s)


    def stop_server(self):
        try:
            self.serverStarted = False
            d = self.endpoint.stopListening()  # returns deferred
            d.addBoth(err, err)
        except:
            pass

    def step(self, dt):
        # scrolling logic
        if self.mouse_flags["x"] == 0 and self.mouse_flags["y"] == 0:
            # keyboard scrolling
            buttons = self.arrow_flags
            move_dir = eu.Vector2(buttons[key.RIGHT] - buttons[key.LEFT],
                                  buttons[key.UP] - buttons[key.DOWN])
        else:
            # mouse scrolling
            move_dir = eu.Vector2(self.mouse_flags['x'], self.mouse_flags['y'])
        newPos = move_dir.normalize() * dt * MAP_MOUSE_SCROLL_SPEED
        newx, newy = self.clamp(newPos)
        self.scroller.set_focus(newx, newy)

    def clamp(self, pos):
        x, y = pos
        newx = self.scroller.fx + x
        newy = self.scroller.fy + y
        if newx <= -BLEED:
            newx = -BLEED
        elif newx >= self.w - WINDOW_WIDTH + BLEED:
            newx = self.w - WINDOW_WIDTH + BLEED
        if newy <= -BLEED:
            newy = -BLEED
        elif newy >= self.h - WINDOW_HEIGHT + BLEED:
            newy = self.h - WINDOW_HEIGHT + BLEED
        return newx, newy

    '''
    Methods responding to local events
    '''
    def on_mouse_motion(self, x, y, dx, dy):
        if x <= 1:
            self.mouse_flags["x"] = -1.0
            self.mouse_flags["y"] = float(y - (WINDOW_HEIGHT /
                                               2)) / WINDOW_HEIGHT
        elif x >= WINDOW_WIDTH - 1:
            self.mouse_flags["x"] = 1.0
            self.mouse_flags["y"] = float(y - (WINDOW_HEIGHT /
                                               2)) / WINDOW_HEIGHT
        elif y <= 1:
            self.mouse_flags["y"] = -1.0
            self.mouse_flags["x"] = float(x - (WINDOW_WIDTH / 2)) / WINDOW_WIDTH
        elif y >= WINDOW_HEIGHT - 1:
            self.mouse_flags["y"] = 1.0
            self.mouse_flags["x"] = float(x - (WINDOW_WIDTH / 2)) / WINDOW_WIDTH
        else:
            self.mouse_flags["x"] = 0
            self.mouse_flags["y"] = 0

    def on_key_press(self, k, modifiers):
        if k == key.ESCAPE:
            self.end_game(False)
            return True

        # If the 'N' key was pressed, toggle selection to the next troop that belongs to this player in the vertex.
        if k == key.N and self.selectedUnits != []:
            vert = self.selectedUnits[0].curVertex
            if len(vert.troopSlots) > 1 or (issubclass(type(self.selectedUnits[0]), Building) and len(vert.troopSlots) > 0):
                if (issubclass(type(self.selectedUnits[0]), Building)):
                    # Selected unit is a building, so we want to grab the first Troop (that belongs to this player) that we find.
                    getNextTroop = True
                else:
                    getNextTroop = False

                i = 0
                troopSlotIndex = vert.troopSlots.keys()[i]
                haveNotChangedTroop = True

                # Find a suitable troop
                while haveNotChangedTroop:
                    troop = vert.troopSlots[troopSlotIndex].troop
                    if troop != None:
                        if getNextTroop and troop == self.selectedUnits[0]:
                            # Looped around and did not find any of our units in this vertex, so break.
                            break
                        elif getNextTroop and troop.pid == self.selectedUnits[0].pid and troop != self.selectedUnits[0]:
                            # Found one of this players units in this vertex. Select it and break.
                            self._deselect_all_units()
                            troop.set_is_selected(True, self.map, self.cm, self.player)
                            self.selectedUnits = [troop]
                            break
                        elif troop.isSelected:
                            getNextTroop = True

                    # Reset index
                    i = (i + 1) % len(vert.troopSlots.keys())
                    troopSlotIndex = vert.troopSlots.keys()[i]

        # If the 'B' key was pressed, toggle selection to the building that belongs to this player in the vertex.
        if k == key.B and self.selectedUnits != []:
            vert = self.selectedUnits[0].curVertex
            if vert.building != None and vert.building.pid == self.selectedUnits[0].pid and vert.building != self.selectedUnits[0]:
                self._deselect_all_units()
                vert.building.set_is_selected(True, self.map, self.cm, self.player)
                self.selectedUnits = [vert.building]


        if k == key.LCTRL or k == key.RCTRL:
            # Set so we can select the units we hotkeyed.
            self.isControlDown = True


        if k in self.hotKeyedUnits.keys():
            if self.isControlDown:
                # We're hotkeying a new unit.
                if len(self.selectedUnits) > 0:
                    # Check to ensure we have selected something first.
                    self.hotKeyedUnits[k] = self.selectedUnits[0]
                    self.hotkeysLayer.update_hotkeys_menu()

            elif self.hotKeyedUnits[k] != None:
                # print "m", self.hotKeyedUnits[k].isMoving
                # We want to go to the location of the troop.
                if issubclass(type(self.hotKeyedUnits[k]), Unit) or self.hotKeyedUnits[k].isSelectable:
                    self._deselect_all_units()
                    self.hotKeyedUnits[k].set_is_selected(True, self.map, self.cm, self.player)
                    self.selectedUnits = [self.hotKeyedUnits[k]]
                    self.hotkeysLayer.update_hotkeys_menu()
                self._set_focus_to_unit(self.hotKeyedUnits[k])


        # scrolling logic
        if k in self.arrow_flags.keys():
            self.arrow_flags[k] = 1
            return True

        return False

    def on_key_release(self, k, m):
        # Determine the type of units we've selected so we can assign hotkeys
        # appropriately
        selType = None

        # scrolling logic
        if k in self.arrow_flags.keys():
            self.arrow_flags[k] = 0

        if k == key.LCTRL or k == key.RCTRL:
            # Reset so we can select the units we hotkeyed.
            self.isControlDown = False

        # Delete the selected unit.
        if k == key.BACKSPACE:
            if len(self.selectedUnits) > 0:
                temp = list(self.selectedUnits)
                self._deselect_all_units()
                for unit in temp:
                    utils.play_sound("delete.wav")
                    unit.destroy_action()

        if len(self.selectedUnits) > 0:
            selType = type(self.selectedUnits[0])
        actNum = None
        if selType and issubclass(selType, Troop):
            actNum = TROOP_HOTKEYS.get(k, None)
        elif selType and issubclass(selType, Building):
            actNum = BUILDING_HOTKEYS.get(k, None)

        if actNum != None:
            for unit in self.selectedUnits:
                if actNum < len(unit.actionList):
                    self._deselect_all_units()
                    self.execute_action(unit.get_action_list(self.player)[actNum], unit)
                    break


        return True

    def on_mouse_release(self, x, y, buttons, modifiers):

        x, y = self.scroller.pixel_from_screen(x, y)
        if self.infoLayer.miniMapToggled and self.infoLayer.miniMap.cshape.touches_point(x,y):
            return

        #I'm not sure why we need this, please talk to me - Robert
        # if self.statusMenu.menuButton.cshape.touches_point(x,y):
        #     director.pop()

        clicked_units = self.cm.objs_touching_point(x, y)
        temp_units = []
        actionButton = None

        for unit in clicked_units:
            if type(unit) == ActionButton:
                    actionButton = unit
                    break
            if unit.opacity == 255: # Using opacity to check unit is visible and finished building
                if issubclass(type(unit),Unit) and not unit.isSelectable:
                    continue
                temp_units.append(unit)
            if type(unit) == TutorialXButton:
                # Delete the sticky note.

                self.map.remove(self.stickyNote)
                self.map.remove(self.stickyXButton)
                self.cm.remove_tricky(self.stickyXButton)
                utils.play_sound("delete.wav")

                if self.stickyNote.levelFiveCounter in [1,2]:
                    # Adds the sticky note for levels 2-5
                    self.stickyNote = StickyNote("5", self.stickyNote.levelFiveCounter)
                    self.stickyXButton = TutorialXButton(self.stickyNote)
                    self.map.add(self.stickyNote)
                    self.map.add(self.stickyXButton)
                    self.cm.add(self.stickyXButton)

        clicked_units = temp_units[:1]

        if buttons == 1:  # left button
            if self.curAction:
                if self.curAction == "Shake":
                    for unit in list(clicked_units):
                        if type(unit) == Handshake and unit.pid == self.pid:
                            self.hand_shake(unit,self.selectedUnits.pop())

                elif self.curAction == "Attack":
                    for unit in list(clicked_units):
                        if (issubclass(type(unit), Unit) and unit.pid != self.pid) or issubclass(type(unit), Vertex):
                            if self.selectedUnits:
                                self.dispatch_event("player_unit_attack", self.selectedUnits[0])
                                attacker = self.selectedUnits.pop()
                                if type(self) == ClientController:
                                    self.server_attack_unit(attacker,unit)
                                else:
                                    self.attack_unit(unit,attacker)

                self.curAction = None
                return
        
            self._deselect_all_units()
            if actionButton:
                self.execute_action(actionButton.name, actionButton.unitParent)
            else:
                self._select_units(clicked_units)

        if buttons == 4:  # right button
            if not self.selectedUnits:
                return
            for unit in list(clicked_units):
                if type(unit) == Vertex:
                    self._move_selected_units(unit)
                    return

    def _move_selected_units(self, dest):
        for unit in self.selectedUnits:
            self.server_move_troop(unit.uid, dest.vid)
        self._deselect_all_units()

    def execute_action(self, actionName, unit):
        if actionName[0] == "B":
            if actionName[1:] == "CPU": #build CPU
                for a in self.visibleASes:
                    if self.map.AS[a].cores:
                        k, core = self.map.AS[a].cores.popitem()
                        self.map.AS[a].usedCores[k] = core
                        self.server_build_unit(actionName[1:],core.vid, unit)
                        break
            else:
                self.server_build_unit(actionName[1:], unit.curVertex.vid, unit)
        elif actionName[0] == "T":
            self.server_build_unit(actionName[1:], unit.curVertex.vid, None)
        elif actionName == "DEL":
            self.server_remove_unit(unit)
        elif actionName[0] == "R":
            self.perform_research(actionName, unit)
        elif actionName == "Ping":
            unit.ping(self.server_remove_unit)
        elif actionName == "UPingOfDeath":
            self.upgrade_unit(unit,actionName[1:])
        elif actionName == "UNMap":
            self.upgrade_unit(unit,actionName[1:])
        elif actionName == "USinkhole":
            self.upgrade_unit(unit,actionName[1:])
        elif actionName == "Shake":
            self.curAction = "Shake"
            self.selectedUnits = [unit]
        elif actionName == "Attack" or actionName == "Decimate" or actionName == "Inject":
            self.curAction = "Attack"
            self.selectedUnits = [unit]
        elif actionName == "Decrypt":
            self.upgrade_unit(unit,unit.originalType)

    '''
    Methods responding to local/network events
    '''

    def update_location(self, unit, position, vertex=None):
        
        unit.curVertex = vertex
        if vertex.vid == unit.destVertex.vid:  # if same, use set_trans_troop instead
            slot = vertex.add_troop(unit)
            # final position
            if slot:
                action = MoveTo(slot.position, 0.2)
                action += CallFuncS(self._update_cshape, slot.position)
                action += CallFuncS(self.cm.add)
                unit.do(action)


    def build_unit(self, tid, owner, vid=-1, uid=-1,onInit=False):
        # print "in client build unit"
        curVertex = self.map.get_vertex(vid)
        newUnit = self.build_unit_common(tid, owner, curVertex, uid=uid,onInit=onInit)
        if newUnit:
            if not onInit and newUnit.buildTime != 0:
                owner.underConstruction[newUnit.uid] = newUnit
                newUnit.update_opacity(math.floor(curVertex.visibilityState) * UNIT_STARTING_OPACITY)
        return newUnit

    def remove_unit(self, unit):
        self.remove_unit_common(unit)

    def perform_research(self,researchName,researchFactory):
        utils.play_sound("Clock.wav") 
        researchType = RESEARCH[researchName]
        researchType.on_start(self.player)
        action = Delay(researchType.buildTime)
        action += CallFunc(self.finish_research,researchType,self.player,None)
        self.do(action)

    def finish_research(self, newResearch,owner,researchFactory):
        newResearch.on_completion(owner)
        '''
        #DEPRECATED
        owner.completedResearch *= newResearch.uid
        for s in self.map.availResearch:
            research = RESEARCH[s]
            if (owner.completedResearch % research.dependencies) == 0 and (owner.completedResearch % research.uid != 0) and (s not in owner.availableResearch):
                # first cond ensures we have met dependencies
                # second cond ensures we haven't done the research already
                owner.availableResearch.append(s)
        '''

    def move_unit(self, unit, path):
        dest = self.map.vertices[str(path[-1])]
        if dest != unit.destVertex: #if this gets called after update location
            unit.curVertex.remove_troop(unit)
            unit.destVertex = dest
            self.cm.remove_tricky(unit)

            # first vertex
            if unit.pid == self.pid:
                utils.play_sound("Move.wav")
            action = MoveTo(unit.curVertex.position, 0.2)

            # intermediate vertices
            for i in range(1, len(path)):
                vertex = self.map.vertices[str(path[i])]
                action += MoveTo(vertex.position, 1 / unit.speed)
            unit.do(action)

    def _update_cshape(self, unit, position):
        unit.cshape.center = position

    def _set_focus_to_unit(self, unit):
        self.scroller.set_focus(unit.position[0] - WINDOW_WIDTH / 2, unit.position[1] - WINDOW_HEIGHT / 2)

    '''
    Twisted client methods
    '''

    def connect_end_point(self):
        from twisted.internet import reactor
        endpoint = TCP4ClientEndpoint(reactor, SERVER_IP, 8750)
        factory = ClientNoteFactory()
        return endpoint.connect(factory)

    def upgrade_unit(self,oldUnit,newType):
        curVertex = oldUnit.curVertex
        owner = self.players[oldUnit.pid]
        self.server_remove_unit(oldUnit)
        self.server_build_unit(newType,curVertex.vid,None)

    def server_attack_unit(self,attacker,target):
        # print "server_attack_unit", attacker, target
        d = self.connect_end_point()
        def c(ampProto):
            if type(target) == Vertex:
                return ampProto.callRemote(AttackAnimation, pid=attacker.pid,uid=attacker.uid,tpid=int(target.vid),tuid=-1,path=[])
            else:
                return ampProto.callRemote(AttackAnimation, pid=attacker.pid,uid=attacker.uid,tpid=target.pid,tuid=target.uid,path=[])

        d.addCallback(c)
        d.addErrback(err)
        reactor.callLater(10, d.cancel)
 

    def server_build_unit(self, unitName, vid,builder):
        d = self.connect_end_point()
        def c(ampProto):
            if builder:
                u = int(builder.uid)
                return ampProto.callRemote(BuildUnit, pid=self.pid, tid=unitName, vid=vid, uid=-1,buid=u)
            else:
                return ampProto.callRemote(BuildUnit, pid=self.pid, tid=unitName, vid=vid, uid=-1,buid=-1)
        d.addCallback(c)
        d.addErrback(err)
        reactor.callLater(10, d.cancel)

    def server_remove_unit(self, unit):
        d = self.connect_end_point()

        def c(ampProto):
            return ampProto.callRemote(RemoveUnit, pid=unit.pid, uid=unit.uid)
        d.addCallback(c)
        d.addErrback(err)
        reactor.callLater(10, d.cancel)

    def server_move_troop(self, uid, vid):
        # add the destination to troop.destVertex, to be used in update location
        d = self.connect_end_point()

        def c(ampProto):
            return ampProto.callRemote(MoveTroop, pid=self.pid, uid=uid, vid=vid, path=[])
        d.addCallback(c)
        d.addErrback(err)
        reactor.callLater(10, d.cancel)


    def server_connect(self):
        if self.ip:
            return False
        self.ip = str(utils.get_ip())
        if (not self.ip) or self.ip == SERVER_IP or self.connectedToServer:
            print "no connection to the network"
            return False
        d = self.connect_end_point()
        def c(ampProto):
            return ampProto.callRemote(Connect, ip=self.ip)
        d.addCallback(c)
        d.addErrback(err)
        reactor.callLater(10, d.cancel)


        def connected_server(args):
            pid = args['id']
            otherPids = args['cur']
            mapName = args['map']
            # callback for after connection, arg:pid of self and server
            if pid != -1:  # check no error
                print "my pid is ", pid
                self.pid = pid
                self.playerList = otherPids
                self.map = self._init_map_and_cm(mapName)
            else:
                print "Connected server but can't play game, map is full or game already started"
        d.addCallback(connected_server)
        d.addErrback(err)
        reactor.callLater(10, d.cancel)

        return True

    '''
    Helper methods
    '''

    def remove_unit_common(self, unit):
        p = self.players[unit.pid]
        p.units.pop(unit.uid)
        if issubclass(type(unit), Building):
            unit.curVertex.remove_building()
        else:
            unit.curVertex.remove_troop(unit)
        self.map.remove(unit)
        if unit.pid == self.pid and unit in self.cm.known_objs():
            self.cm.remove_tricky(unit)
        unit.isRemoved = True
        if len(p.units) <= 0:
            if p.pid == self.pid:
                self.end_game(False)
            else:
                self.end_game(True)

    def build_unit_common(self, tid, owner, curVertex=None, uid=-1, builder=None, onInit=False):
        # print "build unit common", tid, owner.pid
        #check for valid conditions
        if owner.idleCPUs or tid == "CPU":
            #create the unit
            unitType = eval(tid)
            newUnit = unitType(curVertex, pid=owner.pid)

            #no empty slot
            if newUnit.slotIndex == -1:
                print "vertex full"
                if newUnit.pid == self.pid:
                    utils.play_sound("error.wav")
                return None

            #add to map and set uid
            newUnit.add_to_map(self.map)
            uid = owner.set_unit_uid(newUnit, uid)

            #tutorial
            if newUnit.pid == self.pid:
                self.dispatch_event("player_add_unit", tid) 

            if newUnit.buildTime == 0 or onInit: #instentaneous upgrade to encrypted
                newUnit.health = newUnit.maxHealth
                self._complete_build(newUnit, owner, newUnit.uid,onInit=onInit)

            #start building unit and tell client
            if not onInit:
                if tid != "CPU":
                    self.start_cpu(newUnit, owner, builder)
                elif builder:
                    self.remove_unit(builder)
                if owner == self.player:
                    utils.play_sound("Clock.wav")

            # set visibility
            if type(curVertex) == Vertex and owner.pid == self.pid:
                self._show_as(curVertex.asID)

            return newUnit

        print "no idle CPU"
        if owner.pid == self.pid and not onInit:
            utils.play_sound("error.wav")
        return None

    def _select_units(self, units):
        for unit in units:
            if issubclass(type(unit), Unit) and unit.pid == self.pid:
                utils.play_sound("click_troop.wav")
                unit.set_is_selected(True, self.map, self.cm, self.player)
                self.selectedUnits.append(unit)

    def _deselect_all_units(self):
        for unit in self.selectedUnits:
            unit.set_is_selected(False, self.map, self.cm, self.player)
        self.selectedUnits = []

    def _show_as(self, ASid):
        if ASid not in self.visibleASes:
            self.visibleASes.add(ASid)
            for v in self.map.AS[ASid].vertices.values():
                v._update_visibility()
                self.cm.add(v)
            for v in self.map.AS[ASid].cores.values():
                v._update_visibility()
            for v in self.map.AS[ASid].usedCores.values():
                v._update_visibility()

    def start_cpu(self, newUnit, owner, builder):
        pass

    def start_server(self): #start the server on the server/client side
        if self.serverStarted:
            return False
        if type(self) != ClientController:
            pf = ClientNoteFactory()
        else:
            pf = ServerNoteFactory()

        from twisted.internet import reactor
        endpoint = TCP4ServerEndpoint(reactor, 8750)
        d = endpoint.listen(pf)
        def c(port):
            self.endpoint = port
        d.addCallback(c)
        d.addErrback(err)
        print "started server"
        self.serverStarted = True
        return True


    def _init_players(self):
        self.map.pid = self.pid
        self.map.draw_map()

        # init human player
        for pid in self.playerList:
            self.players[pid] = Player(pid)
        self.players[self.pid] = Player(self.pid)
        self.player = self.players[self.pid]  # convenience


        for pid in self.map.AIPlayers:
            self.players[pid] = ComputerPlayer(pid)

        for p in self.players.keys():
            self.init_units(p)
            ai = self.players[p]
            if type(ai) == ComputerPlayer and type(self)!= ClientController:
                # Yasin's note: This is where the AI gets commented out. Note: Do. Not. Mess. With. This. 
                # Any. More. Thanks. 
                if not self.tutorial:
                    self.schedule_interval(ai.ai_loop, 1)
                    pass
        # DEBUG
        # print "finish init players"
        
    #DEPRECATED, see the research class
    def init_research(self, pid):
        p = self.players[pid]
        # add starting research
        for r in self.map.startingResearch[pid]:
            p.completedResearch *= RESEARCH[r].uid
        # add available research
        for r in self.map.availResearch:
            if p.completedResearch % RESEARCH[r].dependencies == 0:
                p.availableResearch.append(r)

    def init_units(self, pid):
        # add starting units
        p = self.players[pid]
        focus = None
        for vid in reversed(sorted(self.map.startingUnits[pid])): #ensures CPU built first
            for t in self.map.startingUnits[pid][vid]:
                newUnit = self.build_unit(t, p, vid=vid, onInit=True)
                if t == "Server" and pid == self.pid:
                    focus = newUnit.position
                if t == "CPU":
                    c = self.map.AS[newUnit.curVertex.asID].cores.pop(vid)
                    self.map.AS[newUnit.curVertex.asID].usedCores[vid] = c
        if focus:
            self.scroller.set_focus(focus[0] - WINDOW_WIDTH / 2, focus[1] - WINDOW_HEIGHT / 2)

    def start_game(self):
        g = cocos.scene.Scene(self.map, self)
        g.add(ImageLayer(os.path.join("images", "backgrounds", "notebook-paper.png")), z=BACKGROUND_Z)
        self.connectedToServer = True
        cocos.director.director.push(g)

    # add unit to cm, player's units and set visibility
    def _complete_build(self, unit, p, uid,onInit=False):
        if unit.health >= unit.maxHealth:
            unit.health = unit.maxHealth
            self.cm.add(unit)
            if unit.buildTime != 0 and not onInit:
                del p.underConstruction[uid]
            if type(unit) == CPU:
                p.idleCPUs.append(unit)
            else:
                p.units[uid] = unit
            unit.on_completion()  # gets called when a unit is built
        unit.update_opacity(((float(unit.health) / unit.maxHealth) * (
                    255 - UNIT_STARTING_OPACITY) + UNIT_STARTING_OPACITY) * math.floor(unit.curVertex.visibilityState))


ClientController.register_event_type("click_on_move")
ClientController.register_event_type("click_on_action")
ClientController.register_event_type('player_unit_attack')
ClientController.register_event_type('player_add_unit')
