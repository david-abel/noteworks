'''
controller.py

contrains the game controller
to play the game, run game.py
'''

from cocos.director import director
from cocos.layer import *
from cocos import collision_model
from pyglet.window import key
from cocos import audio
import cocos.euclid as eu
from cocos import tiles

from constants import *
from models import *
from maps import Vertex, Map
from utils import *
from imageLayer import *
from game_layers import *
from player import *
from tutorial import *

from music import theme_player

import os

options = {
    "humanPlayerNum": 1,
    "aiPlayerNum": 1
}

class GameController(Layer, EventDispatcher):
    is_event_handler = True

    def __init__(self):
        super(GameController, self).__init__()
        self.selectedUnits = []  # Stores units that have been selected

        self.map = Map(os.path.join("maps", "level1.map"))
        self.map.draw_map()
        self.cm = collision_model.CollisionManagerGrid(
            0.0, self.map.w * CELL_SIZE, 0.0, self.map.h * CELL_SIZE, 32.0, 32.0)
        self.map.cm = self.cm

        self.scroller = ScrollingManager(viewport=director.window)
        self.scroller.add(self.map)

        # Arbitrary starting location. I suggest this is info be stored in each map file.

        self.scroller.set_focus((self.map.w * CELL_SIZE) /
                                16, (self.map.h * CELL_SIZE) / 16)
        self.infoLayer = InfoLayer(self.map, self.scroller, None)
        self.statusMenu = StatusMenu()
        self.add(self.infoLayer)

        self.curAction = None

        self.level = 1
        self.tutorial = Tutorial(self.level, self)

        self.horizontalSize = CELL_SIZE * self.map.w
        self.verticalSize = CELL_SIZE * self.map.h
        # self.mouseClickGraphic = Sprite(os.path.join("images", "menus",
        # "mouse_click_graphic.png"))
        
        #Handshake
        self.is_shake_selected = False
        self.source_handshake = None
        self.handshake_units_selected = []


        if self.horizontalSize < WINDOW_WIDTH:
            self.horizontalSize = WINDOW_WIDTH
        if self.verticalSize < WINDOW_HEIGHT:
            self.verticalSize = WINDOW_HEIGHT

    def on_enter(self):
        super(GameController, self).on_enter()

        # TODO: this will at somepoint be an array of players
        # but it will go in the server code for multiplayer
        self.player = Player(0, self.map, self.cm, PLAYER_COLORS[0])
        self.player.setup(
        )  # Adds starting troops/buildings/research from the map file.

        self.ai = ComputerPlayer(
            1, self.map, self.cm, PLAYER_COLORS[1], self.player)
        self.ai.setup(
        )  # Adds starting troops/buildings/research from the map file.

        self.players = [self.player, self.ai]
        self.infoLayer.player = self.player.ID
        self.ai.run_basic_ai()

        # tutorial stuff
        if SHOW_TUTORIAL:
            self.tutorial.first_prompt("on_enter")
            self.player.push_handlers(
                self.tutorial.player_add_troop, self.tutorial.player_unit_attack, self.tutorial.player_add_building)
            self.push_handlers(
                self.tutorial.click_on_move, self.tutorial.click_on_action)

        self.player.push_handlers(self.on_loss)
        self.ai.push_handlers(self.on_loss)

        for player in self.players:
            self.schedule(player.step)
        self.schedule(self.step)

        self.bindings = {  # key constant : button name
            key.LEFT: 'left',
            key.RIGHT: 'right',
            key.UP: 'up',
            key.DOWN: 'down'
        }

        self.buttons = {  # button name : current value, 0 not pressed, 1 pressed
            'left': 0,
            'right': 0,
            'up': 0,
            'down': 0
        }

        self.mouse_flag = {
            'x': 0,
            'y': 0
        }

    def on_loss(self, loser):
        if loser.ID == 0:
            director.push(Scene(self.lost))
        else:
            director.push(Scene(self.won))

    def step(self, dt):
        # step is called every frame
        if self.mouse_flag["x"] == 0 and self.mouse_flag["y"] == 0:  # keyboard scrolling
            buttons = self.buttons
            move_dir = eu.Vector2(buttons['right'] - buttons['left'],
                                  buttons['up'] - buttons['down'])
        else:  # mouse scrolling
            move_dir = eu.Vector2(self.mouse_flag['x'], self.mouse_flag['y'])
        newPos = move_dir.normalize() * dt * MAP_SCROLL_SPEED
        newx, newy = self.clamp(newPos)
        self.scroller.set_focus(newx, newy)

    def clamp(self, pos):
        x, y = pos
        newx = self.scroller.fx + x
        newy = self.scroller.fy + y
        if newx <= 1:
            newx = 1.0
        elif newx >= self.horizontalSize - WINDOW_WIDTH:
            newx = self.horizontalSize - WINDOW_WIDTH + 1.0
        if newy <= 1:
            newy = 1.0
        elif newy >= self.verticalSize - WINDOW_HEIGHT:
            newy = self.verticalSize - WINDOW_HEIGHT + 1.0
        return newx, newy

    def on_mouse_motion(self, x, y, dx, dy):
        # x,y = self.scroller.pixel_from_screen(x,y)
        if x == 0:
            self.mouse_flag["x"] = -1.0
            self.mouse_flag["y"] = float(y - (WINDOW_HEIGHT /
                                         2)) / WINDOW_HEIGHT
        elif x == WINDOW_WIDTH or x == WINDOW_WIDTH - 1:
            self.mouse_flag["x"] = 1.0
            self.mouse_flag["y"] = float(y - (WINDOW_HEIGHT /
                                         2)) / WINDOW_HEIGHT
        elif y == 0:
            self.mouse_flag["y"] = -1.0
            self.mouse_flag["x"] = float(x - (WINDOW_WIDTH / 2)) / WINDOW_WIDTH
        elif y == WINDOW_HEIGHT or y == WINDOW_HEIGHT - 1:
            self.mouse_flag["y"] = 1.0
            self.mouse_flag["x"] = float(x - (WINDOW_WIDTH / 2)) / WINDOW_WIDTH
        else:
            self.mouse_flag["x"] = 0
            self.mouse_flag["y"] = 0

    def on_key_press(self, k, modifiers):
        if k == key.ESCAPE:
            theme_player.fadeout()

        binds = self.bindings
        if k in binds:
            self.buttons[binds[k]] = 1
            return True
        return False

    def on_key_release(self, k, m):
        # Determine the type of units we've selected so we can assign hotkeys
        # appropriately

        selType = None

        if len(self.selectedUnits) > 0:
            selType = type(self.selectedUnits[0])

        actNum = None
        if selType != None and issubclass(selType, Troop):
            actNum = {
                key.A: 0,  # A
                key.S: 1,  # S
                key.D: 2  # D
            }.get(k, None)
        elif selType != None and issubclass(selType, Building):
            actNum = {
                key.Q: 7,  # Q
                key.W: 3,  # W
                key.E: 5,  # E
                key.A: 1,  # A
                key.D: 0,  # D
                key.Z: 6,  # Z
                key.X: 2,  # X
                key.C: 4,  # C
            }.get(k, None)

        if actNum != None:
            # Loop through selected units and execute action associated with
            # hotkey.

            for unit in self.selectedUnits:
                # Make sure this unit has the action we're trying to execute
                # with the hotkey
                if actNum < len(unit.actionList):
                    # Execute the action. Also deselects the unit (all actions
                    # automatically deselect)

                    self.execute_action(unit.actionList[actNum], unit)

        # scrolling logic
        binds = self.bindings
        if k in binds:
            self.buttons[binds[k]] = 0
            return True
        return False

    # def on_mouse_press(self, x, y, buttons, modifiers):
    #     # Add the mouse down sprite to the map where the mouse was pressed.
    #     x, y = self.scroller.pixel_from_screen(x, y)
    #     self.mouseClickGraphic.position = euclid.Vector2(x, y)
    #     self.map.add(self.mouseClickGraphic, z = 10)

    def on_mouse_release(self, x, y, buttons, modifiers):
        # Mouse clicked. Perform unit selection, check for button presses, and executes actions.
        # Check if we clicked the minimap - if so, don't perform any selection logic on units behind the map.
        # for i in range(1000,1,-0.25):
            # self.mouseClickGraphic.scale = 0.001 * i
        # self.map.remove(self.mouseClickGraphic)
        if self.statusMenu.cm.objs_touching_point(x,y):
            director.pop()

        if self.infoLayer.miniMapToggled:
            # First check to see if the minimap is toggled to save our CM from
            # checking collisions if the minimap isn't up.
            minimap = self.infoLayer.cm.objs_touching_point(
                x - self.infoLayer.position[0], y - self.infoLayer.position[1])
            if self.infoLayer.miniMap in minimap:
                return
        x, y = self.scroller.pixel_from_screen(x, y)
        clicked_units = self.cm.objs_touching_point(x, y)

        for unit in clicked_units:
            if type(unit) == SurrenderButton:
                director.push(Scene(self.lost))

        # Set selectedUnits. If a vertex is clicked on, all troops in the
        # vertex are selected/unselected
        if buttons == 1:  # Left button clicked
            # Did we click on an action button?
            actionButton = get_action_button_clicked(clicked_units)
            if actionButton:
                # Clicked on an action button. Execute the action.
                self.execute_action(actionButton.name, actionButton.unitParent)
            elif clicked_units:
                if self.curAction:
                    # Attack
                    self.player.unit_attack(self.selectedUnits, clicked_units)
                    self.curAction = None
                else:
                    # If clicked on vertex or clicked on a single unit, switch
                    # select state of all units in vertex
                    self.select_units(clicked_units)
                    if constants.SOUND:
                        self.play_sound("click_troop.wav")
        # Move
        if clicked_units != set([]) and self.selectedUnits != []:
            if buttons == 4:  # Button == 4 means right click
                # Perform move action.
                self.execute_move(clicked_units)
            return True

    def __deselect_units_of_type(self, units, unitType):
        # Deselect buildings if we're selecting Troops.
        unitsToDeselect = []
        for unit in self.selectedUnits:
            if issubclass(type(unit), unitType):
                unitsToDeselect.append(unit)
        if unitsToDeselect != []:
            self.player.switch_units_select_state(
                unitsToDeselect, self.selectedUnits)

    def select_units(self, clicked_units):
        # Performs all selection logic. Sets the select state (inverts it) of
        # units that were just clicked on.
        if len(clicked_units) >= 1:
            clicked = None
            for item in clicked_units:
                if type(item) == Vertex:
                    clicked = item
                    break
                else:
                    clicked = item
            
            #Handshake
            if type(clicked) == Handshake:
                #seeing if the shake action is enabled
                if(self.source_handshake != None):
                    if  self.source_handshake == clicked:
                        self.is_shake_selected = False
                
                if self.is_shake_selected:
                    #constructing a list of vids
                    adjacency_vid_list = []
                    for vertex in self.source_handshake.curVertex.adjacentVertices:
                        adjacency_vid_list.append(vertex.vid)

                    #checking to see if edge exists already
                    if clicked.curVertex.vid not in adjacency_vid_list:
                        dest_handshake = clicked
                        edge = self.source_handshake.shake(dest_handshake, self.map)
                        self.cm.remove_tricky(self.source_handshake)
                        self.cm.remove_tricky(dest_handshake)
                        self.is_shake_selected = False
                        self.source_handshake = None
                    else:
                        utils.play_sound("error.wav")
                        self.player.switch_units_select_state(
                        [clicked], self.selectedUnits) 
                        self.is_shake_selected = False
                        pass
            else:
                self.is_shake_selected = False
                self.source_handshake = None


            if type(clicked) == Vertex:
                # Deselect all buildings if we're selecting troops.
                self.__deselect_units_of_type(self.selectedUnits, Building)
                self.player.switch_units_select_state(
                    clicked.troops, self.selectedUnits)
        
            elif issubclass(type(clicked), Unit) and clicked.pid == 0:
                # Deselect all troops if we're selecting a building, and vice
                # versa.
                #TODO: use Dave's player building and troop action list instead
                if issubclass(type(clicked), Building):
                    if type(clicked) == SoftwareUpdater:
                        self.player.update_research_action_button(clicked)
                    if type(clicked) == AlgorithmFactory:
                        self.player.update_troop_action_button(clicked)
                    self.__deselect_units_of_type(self.selectedUnits, Troop)
                elif issubclass(type(clicked), Troop):
                    self.__deselect_units_of_type(self.selectedUnits, Building)

                self.player.switch_units_select_state(
                    [clicked], self.selectedUnits)

        else:
            # More than one thing clicked on. Switch select state of all of
            # them.
            self.player.switch_units_select_state(
                clicked_units, self.selectedUnits)  # We COULD change this so only the unit with the higehst Z value get selected.

    def execute_move(self, clickedUnits):
        # Moves the selected troops (self.selectedUnits) to the destination
        # vertex (which is in clickedUnits)
        dest = None
        while type(dest) != Vertex and clickedUnits != ():
            dest = clickedUnits.pop()
        if type(dest) == Vertex:
            for selectedUnit in self.selectedUnits:
                if issubclass(type(selectedUnit), Troop):
                    if selectedUnit.player_move(dest, self.map, self.cm) == True and constants.SOUND:
                        # If we successfully moved, play the move sound.
                        self.play_sound("Move.wav")
                    selectedUnit.set_is_selected(False, self.map, self.cm, self.player)
                    self.selectedUnits = []
                    self.dispatch_event("click_on_move", type(selectedUnit), dest.vid)

    def execute_action(self, actionName, unit):
        # ActionButton <actionButton> clicked. Execute the action associated
        # with the button/building/vertex
        self.curAction = None
        # Need to add conditional to account for resource availability.
        self.player.switch_units_select_state([unit], self.selectedUnits)
        if actionName[0] == "B":
            # BUILD A BUILDING (also deselects the troop)
            if self.player.execute_build_building(actionName[1:], unit, self.selectedUnits) and constants.SOUND:
                self.play_sound("Clock.wav")
        elif actionName[0] == "T":
            # BUILD A TROOP (also deselects the building)
            if self.player.execute_build_troop(actionName[1:], unit, self.selectedUnits) and constants.SOUND:
                self.play_sound("Clock.wav")
        elif actionName[0] == "R":
            # RESEARCH
            if self.player.perform_research(actionName, unit, self.cm) and constants.SOUND:
                self.play_sound("Clock.wav")
        # BEGIN UPGRADES
        elif actionName == "USinkhole":
            unit.upgrade_to_sinkhole(self.player)
        elif actionName == "UPingOfDeath":
            unit.upgrade_to_pod(self.player)
        elif actionName == "UNMap":
            unit.upgrade_to_nmap(self.player)
        # BEGIN UTILITY
         #Handshake
        elif actionName == "Shake":
            self.is_shake_selected = True
            self.source_handshake = unit            
                #if type(troop) == Handshake and troop != unit:
                    #self.source_handshake = troop
                    #print "GOT ME A TROOP TO SELECT"
                    # Got the other selected handshake to shake with
                    #self.source_handshake = troop
                    #print self.source_handshake.pid
                    #print "MY SELECTED HANDSHAKE",troop
                    #unit.shake(troop)
                    # PLAY HANDSHAKE SOUND
                    #break
        elif actionName == "DEL":
            # TODO: we could have multple servers
            if issubclass(type(unit), Server):
                if self.player.numServers == 1:
                    self.add_surrender_button(unit)
            if constants.SOUND:
                self.play_sound("Eraser.wav")
            self.player.on_destruction(unit, self.selectedUnits)
        elif actionName == "CANCEL":
            self.player.cancel_cpu(unit)
        elif actionName == "Encrypt":
            unit.encrypt(unit.curVertex.troops, self.player)
        elif actionName == "Decrypt":
            unit.decrypt(self.player)
        elif actionName == "Ping":
            unit.ping(self.player.on_destruction, self.map, self.cm)

        else:
            self.curAction = actionName
            # dummy array, because we don't want to change self.selectedUnit
        self.dispatch_event("click_on_action", actionName)

    def play_sound(self, filename):
        sound = pyglet.resource.media('sounds/' + filename, streaming=False)
        sound.play()

    # No image, crash game
    def add_surrender_button(self, actionButton):
        self.player.has_server = False
        x = actionButton.position[0]
        y = actionButton.position[1]
        surrender = SurrenderButton(x, y)
        self.map.add(surrender, z=10)
        self.cm.add(surrender)
        # Yasin was here.

GameController.register_event_type("click_on_move")
GameController.register_event_type("click_on_action")
