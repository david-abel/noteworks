from cocos import euclid, collision_model
from cocos.director import director
from cocos.actions import Show, MoveTo, Hide
from cocos.layer.base_layers import Layer
from cocos.sprite import Sprite
from cocos.text import Label
from constants import ACTION_BUTTON_WIDTH, MENU_BUTTON_Z, ACTIONMENU_X_OFFSET, \
    ACTIONMENU_Y_OFFSET, TIMER_X_OFFSET, TIMER_Y_OFFSET, TIMER_SCALE, WINDOW_WIDTH, \
    WINDOW_HEIGHT, MINMAP_CIRCLE_Z, STATUS_BAR_HEIGHT, SOUND, MUSIC
from imageLayer import ImageLayer
from maps import MiniMap, MiniMapCircle
from constants import *
import objects
from utils import aabb_to_aa_rect
import os
import pyglet
from music import theme_player
import pyglet.window
import constants
import cocos.rect as rect
from cocos.menu import CENTER, Menu, MenuItem, EntryMenuItem
from pyglet.resource import media, image
from cocos.actions.interval_actions import ScaleTo


# Loading the font directory
pyglet.font.add_directory('fonts')


class StatusMenu(Layer):
    is_event_handler = True

    def __init__(self,settingsLayer,player):
        super(StatusMenu,self).__init__()
        self.position = (0,WINDOW_HEIGHT-STATUS_BAR_HEIGHT)
        self.controller = objects.Objects.get_controller()
        self.cm = collision_model.CollisionManagerBruteForce()
        self.settingsMenu = settingsLayer
        self.player = player

    def on_enter(self):
        super(StatusMenu,self).on_enter()
        self.add(Sprite(os.path.join("images","background.png"),scale=2,position=(500,30)),z=-1)
        #self.add(Sprite(os.path.join("images","background.png"),scale=2,opacity=255,position=(500,30)),z=-1) #changed the sprite to be darker
        #self.add(Sprite(os.path.join("images","background.png"),scale=2,opacity=255,position=(500,30)),z=-1)
        text1 = Label(text="# Units: ",font_name='Rabiohead',anchor_y='center',position=(20,STATUS_BAR_HEIGHT/2),font_size=27,color=(255,255,255,255),multiline=False)
        self.add(text1)
        text2 = Label(text="# Idle CPUs: ",font_name='Rabiohead',anchor_y='center',position=(195,STATUS_BAR_HEIGHT/2),font_size=27,color=(255,255,255,255),multiline=False)
        self.add(text2)

        self.selectedUnitText = ""

        self.selectedUnitLabel = Label(text="Selected Unit: " + self.selectedUnitText,font_name='Rabiohead',anchor_y='center',position=(440,STATUS_BAR_HEIGHT/2),font_size=24,color=(255,255,255,255),multiline=False)
        self.add(self.selectedUnitLabel)
        # self.health = Label(text="Health: ",font_name="Rabiohead",anchor_y="center",position=(20,STATUS_BAR_HEIGHT/2),font_size=27,color=(255,255,255,255),multiline=False)
        # self.add(self.health)
        # health = 0
        # totalhealth = 0
        # for building in self.player.units:
        #     health += self.player.units[building].health
        #     totalhealth += self.player.units[building].health
        # self.curHealth = int((float(health) / totalhealth) * 100.0)
        # self.curHealthLabel = Label(text=str(self.curHealth) + "%",font_name='Rabiohead',anchor_y='center',position=(130,STATUS_BAR_HEIGHT/2),font_size=27,color=(255,255,255,255),multiline=False)
        # self.add(self.curHealthLabel)
        self.menuButton = MenuButton(960,10)
        self.add(self.menuButton,z=1)
        self.cm.add(self.menuButton)
        self.musicButton = ToggleMusicButton(885,18)
        self.add(self.musicButton,z=1)
        self.cm.add(self.musicButton)
        self.soundButton = ToggleSoundButton(820,15)
        self.add(self.soundButton,z=1)
        self.cm.add(self.soundButton)
        
        self.oldunitCount = len(self.controller.player.units)
        self.oldCpuCount = len(self.controller.player.idleCPUs)
        self.unitCountLabel = Label(text=str(self.oldunitCount),font_name='Rabiohead',anchor_y='center',position=(130,STATUS_BAR_HEIGHT/2),font_size=27,color=(255,255,255,255),multiline=False)
        self.cpuCountLabel = Label(text=str(self.oldCpuCount),font_name='Rabiohead',anchor_y='center',position=(390,STATUS_BAR_HEIGHT/2),font_size=27,color=(255,255,255,255),multiline=False)
        self.add(self.unitCountLabel)
        self.add(self.cpuCountLabel)
        self.schedule(self.step)
        self.soundX = Label(text="X",font_name='Rabiohead',anchor_y='center',position=(795,37),font_size=50,bold=True,color=(255,255,255,255),multiline=False)
        self.musicX = Label(text="X",font_name='Rabiohead',anchor_y='center',position=(867,37),font_size=50,bold=True,color=(255,255,255,255),multiline=False)
        if self.settingsMenu.settingsMenuOn:
            self.add(settingsMenu)

    def on_mouse_release(self, x, y, buttons, modifiers):
        # Mouse released
        clicked_objects = self.cm.objs_touching_point(x, WINDOW_HEIGHT - y)
        for item in clicked_objects:
            if type(item) == MenuButton:
                self.settingsMenu.toggle_settings_menu()

            elif type(item) == ToggleSoundButton:
                if constants.SOUND:
                    self.add(self.soundX,z=2)
                else:
                    self.remove(self.soundX)
                constants.SOUND = not constants.SOUND

            elif type(item) == ToggleMusicButton:
                constants.MUSIC = not constants.MUSIC
                if not constants.MUSIC:
                    theme_player.stop()
                    self.add(self.musicX,z=2)
                else:
                    theme_player.play()
                    self.remove(self.musicX)

    def step(self,dt):
        from models import Server
        if len(self.controller.player.units) != self.oldunitCount:
            self.oldunitCount = len(self.controller.player.units)
            self.remove(self.unitCountLabel)
            self.unitCountLabel = Label(text=str(self.oldunitCount),font_name='Rabiohead',anchor_y='center',position=(130,STATUS_BAR_HEIGHT/2),font_size=27,color=(255,255,255,255),multiline=False)
            self.add(self.unitCountLabel)

        if len(self.controller.player.idleCPUs) != self.oldCpuCount:
            self.oldCpuCount = len(self.controller.player.idleCPUs)
            self.remove(self.cpuCountLabel)
            self.cpuCountLabel = Label(text=str(self.oldCpuCount),font_name='Rabiohead',anchor_y='center',position=(390,STATUS_BAR_HEIGHT/2),font_size=27,color=(255,255,255,255),multiline=False)
            self.add(self.cpuCountLabel)

        if len(self.controller.selectedUnits) > 0:
            self.remove(self.selectedUnitLabel)
            self.selectedUnitText = str(self.controller.selectedUnits[0].__class__.__name__)
            self.selectedUnitLabel = Label(text="Selected Unit: " + self.selectedUnitText,font_name='Rabiohead',anchor_y='center',position=(440,STATUS_BAR_HEIGHT/2),font_size=24,color=(255,255,255,255),multiline=False)
            self.add(self.selectedUnitLabel)
            self.selectedUnitText = ""
        elif self.selectedUnitText == "":
            self.remove(self.selectedUnitLabel)
            self.selectedUnitLabel = Label(text="Selected Unit: " + self.selectedUnitText,font_name='Rabiohead',anchor_y='center',position=(440,STATUS_BAR_HEIGHT/2),font_size=24,color=(255,255,255,255),multiline=False)
            self.selectedUnitText = "0"
            self.add(self.selectedUnitLabel)



        # health = 0
        # totalHealth = 0
        # for building in self.player.units:
        #     health += self.player.units[building].health
        #     totalHealth += self.player.units[building].initialHealth
        # try:
        #     healthPercent = int(float(health) / totalHealth * 100)
        # except:
        #     pass

        # if healthPercent != self.curHealth:
        #     self.remove(self.curHealthLabel)
        #     self.curHealthLabel = Label(text=str(self.curHealth) + "%",font_name='Rabiohead',anchor_y='center',position=(130,STATUS_BAR_HEIGHT/2),font_size=27,color=(255,255,255,255),multiline=False)
        #     self.add(self.curHealthLabel)
        #     self.curHealth = healthPercent

class SettingsMenuSprite(Sprite):
    def __init__(self,x,y):
        super(SettingsMenuSprite, self).__init__(os.path.join("images",
                                                   "maps", "minimap_bg.png"))
        self.position = euclid.Vector2(x,y)
        self.opacity = 255
        self.scale = 0.6
        self.cshape = aabb_to_aa_rect(self.get_AABB())


def set_menu_theme(menu):
    menu.font_title['font_name'] = 'Rabiohead'
    menu.font_title['font_size'] = 50
    menu.font_title['color'] = (0, 0, 0, 255)

    menu.font_item['font_name'] = 'Rabiohead'
    menu.font_item['font_size'] = 18
    menu.font_item['color'] = (0, 0, 0, 255)

    menu.font_item_selected['font_name'] = 'Rabiohead'
    menu.font_item_selected['font_size'] = 18
    menu.font_item_selected['color'] = (0, 0, 0, 255)

    menu.menu_valign = CENTER
    menu.menu_halign = CENTER

def zoom_in():
    return ScaleTo(1.2, duration=0.2)


def zoom_out():
    return ScaleTo(1.0, duration=0.2)

class SettingsMenu(Menu):
    activate_sound = media(
        os.path.join('sounds', "Menu.wav"), streaming=False)
    select_sound = media(
        os.path.join('sounds', "Menu.wav"), streaming=False)

    def __init__(self):
        super(SettingsMenu, self).__init__()

        set_menu_theme(self)

        # then add the items
        self.home = MenuItem('Home', self.on_home)
        self.fullscreen = MenuItem('Toggle Full Screen', self.on_fullscreen)
        self.tutorial = MenuItem('Toggle Tutorial', self.on_tutorial)

        self.items = [
            (self.home),
            (self.fullscreen),
            (self.tutorial),
        ]

        self.create_menu(self.items, zoom_in(), zoom_out())

    def on_home(self):
        if constants.MUSIC:
            theme_player.stop()
        director.pop()

    def on_fullscreen(self):
        director.window.set_fullscreen(not director.window.fullscreen)


    def on_tutorial(self):
        constants.SHOW_TUTORIAL = not constants.SHOW_TUTORIAL


class SettingsLayer(Layer):
    is_event_handler = True

    def __init__(self):
        super(SettingsLayer, self).__init__()
        self.cm = collision_model.CollisionManagerBruteForce()
        self.settingsMenuOn = False
        self.settingsMenu = SettingsMenu()
        self.settingsMenuSprite = SettingsMenuSprite(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
        # self.homeButton = HomeButton(WINDOW_WIDTH / 2 - 30, WINDOW_HEIGHT / 2 + 60)
        # self.toggleTutorialButton = ToggleTutorialButton(WINDOW_WIDTH / 2 - 50, WINDOW_HEIGHT / 2, 'Toggle Tutorial On')
        # self.toggleFullScreenButton = ToggleFullScreenButton(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 60, 'Toggle Full Screen On')

    def toggle_settings_menu(self):
        # Toggles the settings on/off
        if self.settingsMenuOn:
            self.remove(self.settingsMenu)
            self.remove(self.settingsMenuSprite)
            # print "menu on"
            # self.remove(self.settingsMenu)
            # self.remove(self.homeButton)
            # self.remove(self.toggleTutorialButton)
            # self.remove(self.toggleFullScreenButton)
            # self.cm.remove_tricky(self.settingsMenu)
            # self.cm.remove_tricky(self.homeButton)
            # self.cm.remove_tricky(self.toggleTutorialButton)
            # self.cm.remove_tricky(self.toggleFullScreenButton)

        else:
            self.add(self.settingsMenu,z=25)
            # print "menu off"
            self.add(self.settingsMenuSprite,z=20)
            # self.add(self.homeButton,z=25)
            # self.add(self.toggleTutorialButton,z=20)
            # self.add(self.toggleFullScreenButton,z=20)
            # self.cm.add(self.settingsMenu)
            # self.cm.add(self.homeButton)
            # self.cm.add(self.toggleTutorialButton)
            # self.cm.add(self.toggleFullScreenButton)

        self.settingsMenuOn = not self.settingsMenuOn

    def on_key_press(self, key, modifiers):
        if key == pyglet.window.key.SPACE:
            self.toggle_settings_menu()

    def on_mouse_release(self, x, y, buttons, modifiers):
        # Mouse released - check to see if we clicked on the menu and need
        # to set screen focus.
        if self.settingsMenuOn:
            clicked_objects = self.cm.objs_touching_point(
                x - self.position[0], y - self.position[1])
            for item in clicked_objects:
                if type(item) == HomeButton:
                    if constants.MUSIC:
                        theme_player.stop()
                    director.pop()
                elif type(item) == ToggleTutorialButton:
                    print "Tutorial Toggled"
                    constants.SHOW_TUTORIAL = not constants.SHOW_TUTORIAL
                elif type(item) == ToggleFullScreenButton:
                    print "Full Screen Toggled"
                    director.window.set_fullscreen(not director.window.fullscreen)

class ActionButton(Sprite):

    def __init__(self, x, y, name, unitParent):
        fontSize = 8
        self.is_text = False

        try:
            image = os.path.join("images", "menus", BUTTON_DICTIONARY[name])
        except:
            image = os.path.join("images", "menus", "unit_action_button.png")
            self.is_text = True
        textOffsetX = 13
        textOffsetY = -5
        super(ActionButton, self).__init__(image)

        # Calculate action time in number of seconds. We could also add this
        # info to the name (or to self.actionList some other way)
        self.actionTime = {
            "DEL": 3,
            "TPING": 8,
            "TCONS": 15,
            "BDB": 10,
            "BCPU": 20
        }.get(name, None)

        decryptType = ""
        if name == "Decrypt":
            decryptType = str(unitParent.originalType.__class__.__name__)
    
        self.buttonName = {
            "TPing":"Create Ping",
            "TAPTGet":"Create APT-Get",
            "TDOS":"Create DOS",
            "TInstaller":"Create Installer",
            "TSQLInjection":"Create SQLInjection",
            "TDNSPoison":"Create DNSPoison",
            "THandshake":"Create Handshake",
            "TSpoof":"Create Spoof",
            "TBufferOverflow":"Create Buffer Overflow",
            "BDB":"Install Database",
            "BCPU":"Program FPGA",
            "BDatabase":"Install Database",
            "BAlgorithmFactory":"Allocate Algorithms",
            "BSoftwareUpdater":"Download Software Updater",
            "BFirewall":"Enable Firewall",
            "BRSA":"Write RSA",
            "BHandshake":"Build Handshake",
            "BDNSPoison":"Build DNS Poison",
            "BSpoofedBuilding": "Build Spoofed Building",
            "UPingOfDeath":"Upgrade to Ping of Death",
            "UNMap":"Upgrade to NMap",
            "USinkhole":"Upgrade to Sinkhole",
            "RPortScanner":"Port Scanner",
            "RHandshake":"Research Handshake",
            "RBigData":"Research Big Data",
            "RAdvancedAlgorithms":"Research Advanced Algorithms",
            "RPingResearch": "Advanced Ping",
            "RNetworkTopology": "Research Network Topology",
            "RFPGA":"Research FPGA",
            "RRSA":"Research RSA",
            "ROverclocking":"Research Overclocking",
            "ROverflow":"Research Overflow",
            "DSpoof":"Spoofed Building",
            "Attack":"Attack",
            "Shake":"Shake",
            "Encrypt":"Encrypt",
            "Decrypt":"Decrypt To " + decryptType,
            "GenKey":"Generate Key",
            "Ping":"Execute Ping",
            "NMap":"Perform NMap"
        }.get(name, []) # Determine the name to display on the button

        if self.buttonName == []:
            quit()

        self.position = euclid.Vector2(x, y)
        self.text = Label(self.buttonName, position=(
        x - textOffsetX, y - textOffsetY), color=(50, 50, 116, 255), font_size=fontSize, multiline = True, font_name='Rabiohead', width=ACTION_BUTTON_WIDTH - 5)
        self.name = name
        self.cshape = aabb_to_aa_rect(self.get_AABB())
        self.unitParent = unitParent
        # self.cshape.center = self.position

    def add(self, game_map, cm):
        game_map.add(self, z=MENU_BUTTON_Z)
        if self.is_text == True:
            game_map.add(self.text, z=MENU_BUTTON_Z)
        cm.add(self)

    def remove(self, game_map, cm):
        game_map.remove(self)
        if self.is_text == True:
            game_map.remove(self.text)
        cm.remove_tricky(self)
# This is the sprite for the background to the action menu - I'm making a
# primitive version of this that we will need to change once final visuals
# are added.

class ActionMenu(Sprite):

    def __init__(self, x, y, actions, unitParent):
        from models import Troop
        if issubclass(type(unitParent), Troop):
            image = os.path.join("images", "menus", "unit_action_menu.png")
            # x = x - ACTIONMENU_X_OFFSET
            # y = y - ACTIONMENU_Y_OFFSET
        # elif type(unitParent) == SpoofedBuilding:
        #     image = os.path.join("images", "menus", "spoofed_building_action_menu.png")
        else:
            image = os.path.join("images", "menus", "building_action_menu.png")
        super(ActionMenu, self).__init__(image)
        self.position = euclid.Vector2(x, y)
        self.actionNames = actions
        self.cshape = aabb_to_aa_rect(self.get_AABB())
        self.actionList = []
        self.unitParent = unitParent

        if issubclass(type(unitParent), Troop):
            self.slots = [euclid.Vector2(x - 43, y),
                          euclid.Vector2(x + 0, y),
                          euclid.Vector2(x + 43, y)]  # HOW MANY SLOTS SHOULD TROOPS HAVE? 3?
        else:
            self.slots = [euclid.Vector2(x + 50, y - 0),
                          euclid.Vector2(x - 50, y - 0),
                          euclid.Vector2(x - 0, y - 50),
                          euclid.Vector2(x - 0, y + 50),
                          euclid.Vector2(x + 35.11, y - 35.11),
                          euclid.Vector2(x + 35.11, y + 35.11),
                          euclid.Vector2(x - 35.11, y - 35.11),
                          euclid.Vector2(x - 35.11, y + 35.11)]

        # (Easily Changed)
        self.make_action_buttons()

    def make_action_buttons(self):
        x = self.position[0]
        y = self.position[1]

        for i in range(len(self.actionNames)):
            action = ActionButton(self.slots[i][0], self.slots[
                                  i][1], self.actionNames[i], self.unitParent)
            self.actionList.append(action)

    def add_action_buttons(self, game_map, cm):
        for button in self.actionList:
            button.add(game_map, cm)

    def remove_action_buttons(self, game_map, cm):
        for button in self.actionList:
            button.remove(game_map, cm)


class TransTimer(Sprite):
    def __init__(self, sec, pos, opacity=1):
        super(TransTimer, self).__init__(os.path.join("images",
                                                      "maps", "transtimer.png"))
        self.position = euclid.Vector2(
            pos[0] - TIMER_X_OFFSET, pos[1] - TIMER_Y_OFFSET)
        self.scale = TIMER_SCALE
        self.opacity = opacity * 255
        self.duration = float(sec)

    def get_move_action(self, action=None):
        x, y = self.position
        y = y + 40
        theLocation = euclid.Vector2(x, y)
        if action == None:
            moveAction = Show()
        else:
            moveAction = action + Show()

        moveAction += MoveTo(theLocation, self.duration / 4)
        x = x + 40
        theLocation = euclid.Vector2(x, y)
        moveAction += MoveTo(theLocation, self.duration / 4)
        y = y - 40
        theLocation = euclid.Vector2(x, y)
        moveAction += MoveTo(theLocation, self.duration / 4)
        x = x - 40
        theLocation = euclid.Vector2(x, y)
        moveAction += MoveTo(theLocation, self.duration / 4)
        moveAction += Hide()

        return moveAction

class MenuButton(Sprite):
    def __init__(self, x, y):
        super(MenuButton, self).__init__(os.path.join(
            "images", "maps", "home.png"))
        self.visible = True
        self.scale = 1

        self.position = euclid.Vector2(x,y)
        self.cshape = aabb_to_aa_rect(self.get_AABB())
        self.cshape.center = self.position

class HomeButton(Label):
    def __init__(self, x, y):
        super(HomeButton, self).__init__(text='Home',font_name='Rabiohead', font_size=24)
        self.visible = True
        self.scale = 1
        width = 50
        height = 20
        self.rect = rect.Rect(x - width/2, - height/2, x + width/2, x + height/2)

        self.position = euclid.Vector2(x,y)
        self.cshape = aabb_to_aa_rect(self.rect)
        self.cshape.center = self.position

class ToggleFullScreenButton(Label):
    def __init__(self, x, y, text):
        super(ToggleFullScreenButton, self).__init__(text=text,font_name='Rabiohead', font_size=24)
        self.visible = True
        self.scale = 1
        width = 50
        height = 20
        self.rect = rect.Rect(x - width/2, - height/2, x + width/2, x + height/2)
        self.position = euclid.Vector2(x,y)
        self.cshape = aabb_to_aa_rect(self.rect)
        self.cshape.center = self.position

class StickyNote(Sprite):
    def __init__(self, levelNumber, levelFiveCounter = 0):

        notePosition = {
        "2":euclid.Vector2(320,1080),
        "3":euclid.Vector2(350,1700),
        "4":euclid.Vector2(400,1270),
        "5":euclid.Vector2(10,1000)
        }[levelNumber]

        self.levelFiveCounter = levelFiveCounter

        if levelNumber == "5":
            self.levelFiveCounter += 1
        else:
            self.levelFiveCounter = ""


        super(StickyNote, self).__init__(os.path.join("images", "tutorial", "level" + levelNumber + "_instruction" + str(self.levelFiveCounter) + ".png"), position = notePosition)

class TutorialXButton(Sprite):
    def __init__(self, stickyNoteParent):
        super(TutorialXButton, self).__init__(os.path.join("images", "tutorial", "x.png"))
        x = stickyNoteParent.position[0] + 84
        y = stickyNoteParent.position[1] + 112
        self.position = euclid.Vector2(x, y)
        self.stickyNoteParent = stickyNoteParent
        self.cshape = aabb_to_aa_rect(self.get_AABB())
        self.cshape.center = self.position



class ToggleTutorialButton(Label):
    def __init__(self, x, y, text):
        super(ToggleTutorialButton, self).__init__(text=text,font_name='Rabiohead',font_size=24)
        self.visible = True
        self.scale = 1
        width = 50
        height = 20
        self.rect = rect.Rect(x - width/2, - height/2, x + width/2, x + height/2)
        self.position = euclid.Vector2(x,y)
        self.cshape = aabb_to_aa_rect(self.rect)
        self.cshape.center = self.position


class ToggleSoundButton(Sprite):
    def __init__(self, x, y):

        super(ToggleSoundButton, self).__init__(os.path.join(
            "images", "maps", "speaker.png"))
        self.visible = True
        self.scale = 1

        self.position = euclid.Vector2(x,y)
        self.cshape = aabb_to_aa_rect(self.get_AABB())
        self.cshape.center = self.position


class ToggleMusicButton(Sprite):
    def __init__(self, x, y):
        super(ToggleMusicButton, self).__init__(os.path.join(
            "images", "maps", "music.png"))
        self.visible = True
        self.scale = 1

        self.position = euclid.Vector2(x,y)
        self.cshape = aabb_to_aa_rect(self.get_AABB())
        self.cshape.center = self.position



class SurrenderButton(Sprite):
    def __init__(self, x, y, isVisible=True):
        super(SurrenderButton, self).__init__(os.path.join(
            "images", "maps", "surrender.png"))
        self.visible = isVisible
        self.position = euclid.Vector2(x, y)
        self.cshape = aabb_to_aa_rect(self.get_AABB())
        self.cshape.center = self.position
        self.scale = 0.2  # Arbitrary

class MessageInstruction(object):
    def __init__(self, parent_layer, message, has_image_background, x, y, width, height, font):
        self.parent_layer = parent_layer
        self.background_layer = ImageLayer(os.path.join('images','tutorial','background.png'))
        self.message = message
        self.has_image_background = has_image_background
        self.message_label = Label(
            self.message, font_name='Rabiohead', font_size=font,
            width=width, height=height,
            color=(0, 0, 0, 255),
            anchor_x='center', anchor_y='center', multiline = True)

        if(self.has_image_background == True):
            # Position needs to be worked out
            self.background_layer.postition = 300, 500
            self.parent_layer.add(self.background_layer)
            self.message_label.position = 50, 50
            self.background_layer.add(self.message_label)
        else:
            self.message_label.position = x, y
            self.parent_layer.add(self.message_label)

    def removeMessage(self):
        if(self.has_image_background == True):
            self.parent_layer.kill()
        else:
            self.message_label.kill()


class MessageAlert(Layer):
    def __init__(self, parent_layer, message, image):
        super(MessageAlert, self).__init__()
        self.message_layer = ImageLayer(image)
        self.message_layer_height = 400  # sets the constants
        self.message_layer_width = 300  # set the constants
        self.parent_layer = parent_layer
        self.message = message
        self.message_label = Label(
            self.message, font_name='Rabiohead', font_size=26,
            x=self.message_layer_width / 2, y=self.message_layer_height / 2,
            width=self.message_layer_width - 100, height=self.message_layer_height - 100,
            color=(0, 0, 0, 255),
            anchor_x='center', anchor_y='center', multiline = True)

        # added text to specified parent layer(should be the
        # self.game_controller_layer of controller.py)
        self.message_label.position = 30, -240
        self.message_layer.add(self.message_label)
        self.message_layer.position = 0, 0
        self.parent_layer.add(self.message_layer)

    def removeMessage(self):
        self.message_layer.kill()


class InfoLayer(Layer):
    is_event_handler = True

    def __init__(self, gameMap, scroller,player):
        super(InfoLayer, self).__init__()
        self.map = gameMap
        self.scroller = scroller
        self.cm = collision_model.CollisionManagerBruteForce(
        )  # Grid having problems...
        self.miniMapToggled = False
        self.player = player
        # Also hard coded.
        self.position = (3 * WINDOW_WIDTH / 4.0 + 90, WINDOW_HEIGHT / 4.0 - 20)
        self.visibleCircles = []
        # Define the minimap rectangle sprite that we toggle on/off.
        self.miniMap = MiniMap(
            self.map.AS, self.map.w, self.map.h, self.map.edges, self.player)
        self.map.minimap = self.miniMap  # adds this MiniMap instance to the map

    def toggle_mini_map(self):
        # Toggles the minimap on/off
        if self.miniMapToggled:
            self.remove(self.miniMap)
            for circle in self.visibleCircles:
                self.remove(circle)
                self.cm.remove_tricky(circle)
            self.visibleCircles = []

                    #if curVertex.building:
                     #   self.remove(self.miniMap.minimapBuildings[vid])
                    # self.cm.remove_tricky(self.miniMap.minimapBuildings[vid])

        else:
            self.add(self.miniMap)
            for vid in self.miniMap.miniMapCircles:
                curVertex = self.map.vertices[vid]
                if curVertex.visibilityState != 0:
                    circle = self.miniMap.miniMapCircles[vid]
                    self.add(circle, z=MINMAP_CIRCLE_Z)
                    self.visibleCircles.append(circle)
                    self.cm.add(circle)

                    #if self.map.vertices[vid].building:
                        #building = Sprite(os.path.join('images', 'maps', 'minimap_building.png'), scale=0.1,position=euclid.Vector2(float(self.miniMap.miniMapCircles[vid].position[0]), float(self.miniMap.miniMapCircles[vid].position[1])))
                        #self.add(building, z=MINMAP_CIRCLE_Z)
                        #self.miniMap.minimapBuildings[vid] = building
                        # self.cm.add(building)

        self.miniMapToggled = not self.miniMapToggled

    def on_key_press(self, key, modifiers):
        if key == 65289:
            # Pressed tab. Toggle minimap.
            self.toggle_mini_map()

    def on_mouse_release(self, x, y, buttons, modifiers):
        # Mouse released - check to see if we clicked on the menu and need
        # to set screen focus.
        if self.miniMapToggled:
            clicked_objects = self.cm.objs_touching_point(
                x - self.position[0], y - self.position[1])
            for item in clicked_objects:
                if type(item) == MiniMapCircle:
                    self.scroller.set_focus(
                        item.asPosition[0] - WINDOW_WIDTH / 2.0,
                        item.asPosition[1] - WINDOW_HEIGHT / 2.0)


keyboard = key.KeyStateHandler()

class HotkeysLayer(Layer):
    is_event_handler = True

    def __init__(self, hotkeys, scroller):
        super(HotkeysLayer, self).__init__()
        self.scroller = scroller
        self.cm = collision_model.CollisionManagerBruteForce()
        self.hotkeysMenuOn = False
        self.hotkeys = hotkeys
        # self.hotkeysMenu = HotkeysMenu(self.hotkeys, 190, 200)
        self.hotkeysList = []
        self.keyNumList = []

    def update_hotkeys_menu(self):
        # Toggles the hotkeys menu on/off

        if self.hotkeysMenuOn:
            for key in self.keyNumList:
                self.remove(key)
            for key in self.hotkeysList:
                self.remove(key)
                self.cm.remove_tricky(key)
            self.keyNumList = []
            self.hotkeysList = []
            x = 10
            y = 600
            for hotkey in self.hotkeys:
                if self.hotkeys[hotkey]:
                    y -= 50
                    keyNum = hotkey - 48
                    newKey = Label(text="%s:" % keyNum,font_name='Rabiohead',anchor_y='center',position=(x,y),font_size=14,color=(0,0,0,255),multiline=False)
                    x+=40
                    newLabel = HotkeyLabel((x,y),self.hotkeys[hotkey])
                    self.hotkeysList.append(newLabel)
                    self.cm.add(newLabel)
                    self.keyNumList.append(newKey)
                    self.add(newLabel,z=25)
                    self.add(newKey,z=25)
                    x -= 40


    def toggle_hotkeys_menu(self):
        # Toggles the hotkeys menu on/off

        if self.hotkeysMenuOn:
            # self.remove(self.hotkeysMenu)
            # self.remove(self.title)

            for key in self.hotkeysList:
                self.remove(key)
                self.cm.remove_tricky(key)
            for num in self.keyNumList:
                self.remove(num)
            self.hotkeysList = []
            self.keyNumList = []

        else:
            # self.add(self.hotkeysMenu,z=20)
            # self.title = Label(text="Hotkeys:",font_name='Rabiohead',anchor_y='center',position=(10,630),font_size=20,color=(0,0,0,255),multiline=False)
            # self.add(self.title,z=25)
            x = 10
            y = 600
            for hotkey in self.hotkeys:
                if self.hotkeys[hotkey]:
                    y -= 50
                    keyNum = hotkey - 48
                    newKey = Label(text="Key: %s" % keyNum,font_name='Rabiohead',anchor_y='center',position=(x,y),font_size=12,color=(0,0,0,255),multiline=False)
                    x+=70
                    newLabel = HotkeyLabel((x,y),self.hotkeys[hotkey])
                    self.hotkeysList.append(newLabel)
                    self.cm.add(newLabel)
                    self.keyNumList.append(newKey)
                    self.add(newLabel,z=25)
                    self.add(newKey,z=25)
                    x -= 70

        self.hotkeysMenuOn = not self.hotkeysMenuOn

    def on_key_press(self, key, modifiers):
        if key == pyglet.window.key.SLASH and modifiers == pyglet.window.key.MOD_SHIFT:
            self.toggle_hotkeys_menu()

    def on_mouse_release(self, x, y, buttons, modifiers):
        # Mouse released - check to see if we clicked on the menu and need
        # to set screen focus.
        if self.hotkeysMenuOn:
            clicked_objects = self.cm.objs_touching_point(x, y)
            for item in clicked_objects:
                if type(item) == HotkeyLabel:
                    self.scroller.set_focus(
                        item.hotkeyPos[0] - WINDOW_WIDTH / 2.0,
                        item.hotkeyPos[1] - WINDOW_HEIGHT / 2.0)


class HotkeysMenu(Sprite):
    def __init__(self, hotkeys, x, y):
        super(HotkeysMenu, self).__init__(os.path.join("images",
                                                   "maps", "minimap_bg.png"))
        self.hotkeys = hotkeys
        self.position = euclid.Vector2(float(x), float(y))
        self.opacity = 255
        self.scale = 0.6
        self.cshape = aabb_to_aa_rect(self.get_AABB())

    def setup(self):
        pass


class HotkeyLabel(Sprite):
    def __init__(self, position, hotkey):
        super(HotkeyLabel, self).__init__(hotkey.imageOutline)
        self.hotkeyPos = hotkey.position
        self.scale = 0.7
        self.position = euclid.Vector2(float(position[0]), float(position[1]))
        self.cshape = collision_model.CircleShape(
            euclid.Vector2(x=self.position[0], y=self.position[1]), 14)


class HotkeyUnit(Sprite):
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
