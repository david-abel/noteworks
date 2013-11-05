from cocos.actions.interval_actions import ScaleTo
from cocos.director import director
from cocos.layer.base_layers import Layer
from cocos.menu import CENTER, Menu, MenuItem, EntryMenuItem
from cocos.scene import Scene
from cocos.sprite import *
from cocos.text import RichLabel
from cocos.actions.interval_actions import MoveBy, Delay, FadeOut, FadeIn
from constants import BACKGROUND_Z
from imageLayer import ImageLayer
from pyglet.resource import media, image
from pyglet.window import *
from objects import Objects
from poem import POEM
from music import menu_player, intro_sound_player
from cocos.layer import Layer
from pyglet.gl.gl import glColor4ub, glPushMatrix, glPopMatrix
from cocos import collision_model
from game_layers import MessageInstruction
from instructionButtons import *
from cocos.actions.instant_actions import CallFunc
import os
import pyglet.font
import utils
import constants

# Loading the font directory
pyglet.font.add_directory('fonts')


def zoom_in():
    return ScaleTo(1.3, duration=0.2)


def zoom_out():
    return ScaleTo(1.0, duration=0.2)


def set_menu_theme(menu):
    menu.font_title['font_name'] = 'ChalkDust'
    menu.font_title['font_size'] = 64
    menu.font_title['color'] = (255, 255, 255, 255)

    menu.font_item['font_name'] = 'ChalkDust'
    menu.font_item['font_size'] = 27
    menu.font_item['color'] = (255, 255, 255, 255)

    menu.font_item_selected['font_name'] = 'ChalkDust'
    menu.font_item_selected['font_size'] = 27
    menu.font_item_selected['color'] = (255, 255, 255, 255)

    menu.menu_valign = CENTER
    menu.menu_halign = CENTER

class LevelMenu(Menu):
    activate_sound = media(
        os.path.join('sounds', "Menu.wav"), streaming=False)
    select_sound = media(
        os.path.join('sounds', "Menu.wav"), streaming=False)

    def __init__(self,txt):
        super(LevelMenu, self).__init__("Select Level")


class EndMenu(Menu):
    activate_sound = media(
        os.path.join('sounds', "Menu.wav"), streaming=False)
    select_sound = media(
        os.path.join('sounds', "Menu.wav"), streaming=False)

    def __init__(self,txt,curLevel):
        super(EndMenu, self).__init__("Game Over, You " + txt)
        
        self.levelName = ""
        self.level = curLevel
        
        set_menu_theme(self)

        self.ok = MenuItem("Back to Main Menu",director.pop)

        if txt == "Lost":
            self.retry = MenuItem("Retry Level", self.on_retry)
            items = [(self.ok),(self.retry)]
            self.levelName = "level"+str(curLevel)
        elif curLevel <= 5:
            self.win = MenuItem("Next Level", self.on_win)
            items = [(self.ok),(self.win),]
            self.levelName = "level"+str(curLevel+1)
        else:
            self.end_scene = MenuItem("You Fired Mr Winely!",director.pop)
            items = [(self.ok),self.end_scene]

        self.create_menu(items,ScaleTo(1.3, duration=0.2),ScaleTo(1.0, duration=0.2))

    
    def on_win(self):
        Objects.reset_game()
        server = Objects.get_server(self.levelName)
        server.curLevel = self.level+1
        utils.play_sound("Enter.wav")
        game = Scene(server.map, server)
        game.add(ImageLayer(os.path.join("images", "backgrounds", "notebook-paper.png")), z=BACKGROUND_Z)
        director.push(game)
        menu_player.stop()
        self.game_started = True

    def on_retry(self):
        Objects.reset_game()
        server = Objects.get_server(self.levelName)
        server.curLevel = self.level
        utils.play_sound("Enter.wav")
        game = Scene(server.map, server)
        game.add(ImageLayer(os.path.join("images", "backgrounds", "notebook-paper.png")), z=BACKGROUND_Z)
        director.push(game)
        menu_player.stop()
        self.game_started = True

    def on_quit(self):
        director.pop()


class MainMenu(Menu):
    activate_sound = media(
        os.path.join('sounds', "Menu.wav"), streaming=False)
    select_sound = media(
        os.path.join('sounds', "Menu.wav"), streaming=False)

    def __init__(self):
        super(MainMenu, self).__init__('Noteworks')

        set_menu_theme(self)

        self.levelName = constants.DEFAULT_MAP
        # then add the items
        self.instructions = MenuItem('Instructions', self.on_intro)
        self.space1 = MenuItem('', self.on_intro)
        self.single = MenuItem('Single-Player', self.on_single_player)
        self.space2 = MenuItem('', self.on_intro)
        self.mult = MenuItem("Multi-Player", self.on_multi)
        self.space3 = MenuItem('', self.on_intro)
        self.level = EntryMenuItem("Level Name:",self.on_level,self.levelName)
        self.space4 = MenuItem('', self.on_intro)
        self.ip = EntryMenuItem("Server IP:",self.on_ip,constants.SERVER_IP)
        self.space4 = MenuItem('', self.on_intro)
        self.exit = MenuItem('Exit', self.on_quit)

        self.items = [
            (self.instructions),
            #(self.space1),
            (self.single),
            #(self.space2),
            (self.mult),
            #(self.space3),
            (self.level),
            #(self.space4),
            self.ip,
            (self.exit),
        ]

        self.create_menu(self.items, zoom_in(), zoom_out())
        self.game_started = False

    def on_intro(self):
        utils.play_sound("Enter.wav")
        image = os.path.join("images", "backgrounds", "notebook-paper.png")
        director.push(Scene(Intro(image)))

    def on_level(self,val):
        self.levelName = str(val)

    def on_ip(self,val):
        constants.SERVER_IP = str(val)

    def on_enter(self):
        super(MainMenu, self).on_enter()
        constants.MUSIC = True
        menu_player.set_volume(2)
        if self.game_started:
            Objects.reset_game()
            self.game_started = False
        # buggy
        # self.children[0][1].do(self.children[0][1].selected_effect)  # making first item selected

    def on_single_player(self):
        Objects.get_server(self.levelName)
        server = Objects.get_controller()

        utils.play_sound("Enter.wav")
        game = Scene(server.map, server)
        game.add(ImageLayer(
                 os.path.join("images", "backgrounds", "notebook-paper.png")), z=BACKGROUND_Z)


        director.push(game)
        menu_player.stop()
        self.game_started = True

        # play_intro_animation(page_turn) #this is taking 2-3 seconds to load --Robert
        # director.replace( FadeTransition(main_scene,2,page_turn) )

    def on_quit(self):
        from twisted.internet import reactor
        reactor.stop()
        director.pop()

    def on_multi(self):
        utils.play_sound("Enter.wav")
        s = Scene(MultiplayerMenu(self.levelName))
        s.add(ImageLayer(os.path.join("images", "backgrounds", "menu-chalkboard.png")))
        director.push(s)


def play_intro_animation(scene):

    image_frames = []
    for i in range(86):
        if(i <= 9):
            image_frames.append(os.path.join(
                'images', 'intro_animation', 'intro_0000' + str(i) + '.png'))
        else:
            image_frames.append(os.path.join(
                'images', 'intro_animation', 'intro_000' + str(i) + '.png'))

    image_frames = tuple(image_frames)
    images = map(lambda img: pyglet.image.load(img), image_frames)
    animation = pyglet.image.Animation.from_image_sequence(
        images, 0.05, False)
    sprite_name = Sprite(animation)
    sprite_name.position = 350, 350
    scene.add(sprite_name)
    return sprite_name


class IntroText(Layer):
    is_event_handler = True

    def __init__(self):
        super(IntroText, self).__init__()
        self.poem = RichLabel(text=POEM, position=(100, 300), multiline=True, width=300, font_name='ChalkDust', font_size=27)        
        self.introZora = Sprite(os.path.join("images","intro_images","zora.png"), position=(750, 400), scale=1, opacity=0)
        self.introTownmap = Sprite(os.path.join("images","intro_images","town-map.png"), position=(830, 400), scale=.75,opacity=0)
        self.introNetmap = Sprite(os.path.join("images","intro_images","network-map.png"), position=(800, 400), scale=.75,opacity=0)
        self.introNotebook = Sprite(os.path.join("images","intro_images","notebook.png"), position=(780, 400), scale=.75,opacity=0)
        self.background = ImageLayer(os.path.join("images","backgrounds","chalkboard_align_topleft.png"))
        self.background.position=(0, 0)
        self.background.scale=1
        self.background.anchor=(0.0, 0.0)
        self.background.z=1
        self.add(self.poem)
        self.add(self.introZora)
        self.add(self.introTownmap)
        self.add(self.introNetmap)
        self.add(self.introNotebook)
        self.add(self.poem)
        self.add(self.background)
        self.help = RichLabel(text="Help Zora take down the school's network!", halign='center',position=(100, 500), multiline=True, width=700, font_name='ChalkDust', font_size=40)
        self.help.opacity = 1
        self.add(self.help,z=1)

    def on_enter(self):
        super(IntroText, self).on_enter()
        menu_player.play()
        menu_player.set_volume(1)
        intro_sound_player.play()
        intro_sound_player.set_volume(2)
        intro_sound_player.player.eos_action = pyglet.media.Player.EOS_STOP

        a = Delay(2)
        a += MoveBy((0, 6300), 100)
        a += Delay(3)
        a += CallFunc(self.on_quit)

        b = Delay(101)
        b += FadeIn(1)

        #Story images
        c = Delay(5)
        c += FadeIn(1)
        c += Delay(11)
        c += FadeOut(1)

        d = Delay(20)
        d += FadeIn(1)
        d += Delay(5)
        d += FadeOut(1)

        e = Delay(28)
        e += FadeIn(1)
        e += Delay(13)
        e += FadeOut(1)

        f = Delay(44)
        f += FadeIn(1)
        f += Delay(51)
        f += FadeOut(3)


        self.poem.do(a)
        self.help.do(b)
        self.introZora.do(c)
        self.introTownmap.do(d)
        self.introNetmap.do(e)
        self.introNotebook.do(f)

    def on_key_press(self, k, m):
        if k == pyglet.window.key.ENTER or k == pyglet.window.key.ESCAPE:
            intro_sound_player.stop()
            self.on_quit()
        return True

    def on_quit(self):
        if intro_sound_player.is_playing():
            intro_sound_player.stop()
        self.poem.stop()
        director.pop()
        return True



class HelpZoraScene(Layer):
    is_event_handler = True

    def __init__(self):
        super(HelpZoraScene, self).__init__()
        self.background = ImageLayer(os.path.join("images","backgrounds","chalkboard_align_topleft.png"))
        self.background.position=(0, 0)
        self.background.scale=1
        self.background.anchor=(0.0, 0.0)
        self.background.z=1
        self.poem = RichLabel(text="Help Zora!", position=(500, 500), width=300, font_name='Rabiohead', font_size=27)
        self.image = Sprite(os.path.join("images","maps","surrender.png"),position=(700, 500),scale=0.4)

        self.add(self.background)
        self.add(self.poem)
        self.add(self.image)

    def on_enter(self):
        super(HelpZoraScene, self).on_enter()
        intro_sound_player.stop()

        menu_player.set_volume(3)
        a = Delay(3)
        a += CallFunc(self.on_quit)
        self.poem.do(a)


    def on_key_press(self, k, m):
        if k == pyglet.window.key.ENTER or k == pyglet.window.key.ESCAPE:
            self.on_quit()
        return True

    def on_quit(self):
        self.poem.stop()
        director.pop()
        return True


class Intro(Layer):
    #class works in conjunction to instructions.py
    is_event_handler = True

    def __init__(self, img):
        super(Intro, self).__init__()
        self.img = image(img)
        self.collision_manager = collision_model.CollisionManagerBruteForce()
        self.load_instructions()

    def load_instructions(self):
        MessageInstruction(self, "Press Esc: Home Menu", False, 300,550, 500,300,21)
        MessageInstruction(self, "Instructions", False, 500,500, 500,300,90)
        #adding buttons
        unit_detail_button = UnitDetailsButton(500,400)
        unit_detail_button.scale = .7
        unit_detail_button.postion = 100,100
        self.add(unit_detail_button, z=1)
        self.collision_manager.add(unit_detail_button)

        controls_button = ControlsButton(500,300)
        controls_button.postion = 100,100
        controls_button.scale = .7
        self.add(controls_button, z=1)
        self.collision_manager.add(controls_button)

        tt_button = TechTreeButton(500,200)
        tt_button.postion = 100,100
        tt_button.scale = .7
        self.add(tt_button, z=1)
        self.collision_manager.add(tt_button)

    def load_controls(self):
        self.clear_panel(self.get_children())
        resource_troops_panel = Sprite(os.path.join("images", "instructions", "controls_panel.png"))
        resource_troops_panel.position = 580,400
        self.add(resource_troops_panel, z=1)

        back_button = BackButton(130,75)
        self.add(back_button, z=1)
        self.collision_manager.add(back_button)

    def load_tech_tree(self):
        self.clear_panel(self.get_children())
        resource_troops_panel = Sprite(os.path.join("images", "instructions", "techtree_panel.png"))
        resource_troops_panel.position = 500,400
        self.add(resource_troops_panel, z=1)

        back_button = BackButton(130,75)
        self.add(back_button, z=1)
        self.collision_manager.add(back_button)
    
    def load_overview_panel(self):
        overview_panel = Sprite(os.path.join("images", "instructions", "overview_text.png"))
        overview_panel.position = 500,400
        overview_panel.scale = .8
        self.add(overview_panel, z=1)

        back_button = BackButton(100,75)
        back_button.scale = .8
        self.add(back_button, z=1)
        self.collision_manager.add(back_button)
        
        #adding buttons
        building_button = BuildingsDetailsButton(180,225)
        self.add(building_button, z=1)
        self.collision_manager.add(building_button)

        resource_button = ResourceDetailsButton(850,225)
        self.add(resource_button, z=1)
        self.collision_manager.add(resource_button)

        utility_troop_button = UtilityTroopDetailsButton(390,120)
        self.add(utility_troop_button, z=1)
        self.collision_manager.add(utility_troop_button)

        attack_troop_button = AttackTroopDetailsButton(650,120)
        self.add(attack_troop_button, z=1)
        self.collision_manager.add(attack_troop_button)

    def load_building_panel(self):
        self.clear_panel(self.get_children())
        building_panel = Sprite(os.path.join("images", "instructions", "building_panel.png"))
        building_panel.position = 500,400
        self.add(building_panel, z=1)

        back_button = BackButtonUD(300,150)
        self.add(back_button, z=1)
        self.collision_manager.add(back_button)

    def load_utility_troops_panel(self):
        self.clear_panel(self.get_children())
        utility_troop_panel = Sprite(os.path.join("images", "instructions", "utility_troop_panel.png"))
        utility_troop_panel.position = 500,380
        self.add(utility_troop_panel, z=1)


        back_button = BackButtonUD(300,80)
        self.add(back_button, z=1)
        self.collision_manager.add(back_button)
        
    def load_attack_troops_panel(self):
        self.clear_panel(self.get_children())
        attack_troop_panel = Sprite(os.path.join("images", "instructions", "attack_troop_panel.png"))
        attack_troop_panel.position = 500,400
        self.add(attack_troop_panel, z=1)


        back_button = BackButtonUD(300,80)
        back_button.postion = 390,50
        self.add(back_button, z=1)
        self.collision_manager.add(back_button)

    def load_resource_troops_panel(self):
        self.clear_panel(self.get_children())
        resource_troops_panel = Sprite(os.path.join("images", "instructions", "resource_panel.png"))
        resource_troops_panel.position = 500,400
        self.add(resource_troops_panel, z=1)

        back_button = BackButtonUD(300,80)
        self.add(back_button, z=1)
        self.collision_manager.add(back_button)

    def draw(self):
        glColor4ub(255, 255, 255, 255)
        glPushMatrix()
        self.transform()
        self.img.blit(0, 0)
        glPopMatrix()

    def clear_panel(self, panel_item_list):
        for panel_item in panel_item_list:
            if(type(panel_item) == BackButton or type(panel_item) == BackButtonUD 
                or type(panel_item) == AttackTroopDetailsButton
                or type(panel_item) == UtilityTroopDetailsButton
                or type(panel_item) == BuildingsDetailsButton
                or type(panel_item) == ResourceDetailsButton
                or type(panel_item) == UnitDetailsButton
                or type(panel_item) == ControlsButton
                or type(panel_item) == TechTreeButton):
                self.collision_manager.remove_tricky(panel_item)
            panel_item.kill()

    def on_mouse_release(self, x, y, buttons, modifiers):
        clicked_units = self.collision_manager.objs_touching_point(x, y)

        if(len(clicked_units) > 0):
            clicked = clicked_units.pop()
            if type(clicked) == BuildingsDetailsButton:
                utils.play_sound("Enter.wav")
                self.load_building_panel()
            elif type(clicked) == UtilityTroopDetailsButton:
                utils.play_sound("Enter.wav")
                self.load_utility_troops_panel()
            elif type(clicked) == AttackTroopDetailsButton:
                utils.play_sound("Enter.wav")
                self.load_attack_troops_panel()
            elif type(clicked) == ResourceDetailsButton:
                utils.play_sound("Enter.wav")
                self.load_resource_troops_panel()
            elif type(clicked) == BackButtonUD:
                utils.play_sound("Enter.wav")
                self.clear_panel(self.get_children())
                self.load_overview_panel()
            elif type(clicked) == BackButton:
                utils.play_sound("Enter.wav")
                self.clear_panel(self.get_children())
                self.load_instructions()
            elif type(clicked) == UnitDetailsButton:
                utils.play_sound("Enter.wav")
                self.clear_panel(self.get_children())
                self.load_overview_panel()
            elif type(clicked) == ControlsButton:
                utils.play_sound("Enter.wav")
                self.clear_panel(self.get_children())
                self.load_controls()
            elif type(clicked) == TechTreeButton:
                utils.play_sound("Enter.wav")
                self.clear_panel(self.get_children())
                self.load_tech_tree()
        else:
            pass        
class MultiplayerMenu(Menu):
    activate_sound = media(
        os.path.join('sounds', "Menu.wav"), streaming=False)
    select_sound = media(
        os.path.join('sounds', "Menu.wav"), streaming=False)

    def __init__(self,levelName):
        super(MultiplayerMenu, self).__init__('Multi-Player')
        self.host = MenuItem("Start Server and Wait", self.new_game)
        self.start = MenuItem("Finish Waiting, Start Game", self.start_game)
        self.join = MenuItem("Join Game", self.join_game)
        self.back = MenuItem("Back", self.on_quit)
        self.levelName = levelName
        items = [
            (self.host),
            (self.start),
            (self.join),
            (self.back),
        ]

        set_menu_theme(self)

        self.create_menu(items, zoom_in(), zoom_out())

        self.game_started = False

    def on_enter(self):
        super(MultiplayerMenu, self).on_enter()
        if self.game_started:
            Objects.reset_game()
            self.game_started = False

    def new_game(self):
        constants.MULTIPLAYER = True
        utils.play_sound("Enter.wav")
        Objects.get_server(self.levelName).start_server()
        # start server and wait

    def start_game(self):
        constants.MULTIPLAYER = True
        server = Objects.get_controller()
        server.client_start_game()
        if server.serverStarted:
            utils.play_sound("Enter.wav")
            game = Scene(server.map, server)
            menu_player.stop()
            game.add(ImageLayer(
                     os.path.join("images", "backgrounds", "notebook-paper.png")), z=BACKGROUND_Z)
            director.push(game)
            self.game_started = True

        else:
            print "start server first"

    def join_game(self):
        constants.MULTIPLAYER = True
        utils.play_sound("Enter.wav")
        c = Objects.get_client()
        c.start_server()  # start client server
        connection = c.server_connect()  # connect to game server
        if not connection:
            c.stop_server()
        menu_player.stop()
        self.game_started = True

    def on_quit(self):
        director.pop()

if __name__ == '__main__':
    print "Please run python net-game.py instead, sorry for inconvenience!"
