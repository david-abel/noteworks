import os
import pyglet

from cocos.director import director
from cocos.actions import ScaleTo
from cocos.scene import Scene
from cocos.menu import *

from menu_layers import *
from constants import *
from imageLayer import *
from controller import GameController

import chessmodegame as game
#Loading the font directory
pyglet.font.add_directory('fonts')


def zoom_in():
    return ScaleTo(1.3, duration=0.2)


def zoom_out():
    return ScaleTo(1.0, duration=0.2)

class MainMenu(Menu):
    def __init__(self):
        super(MainMenu, self).__init__('Internetization')

        self.font_title['font_name'] = 'Rabiohead'
        self.font_title['font_size'] = 84
        #self.font_title['color'] = (0, 72, 49, 200)

        self.font_item['font_name'] = 'Rabiohead'
        self.font_item['font_size'] = 32
        #self.font_item['color'] = (48, 32, 48, 200)

        self.font_item_selected['font_name'] = 'Rabiohead'
        self.font_item_selected['font_size'] = 32
        #self.font_item_selected['color'] = (32, 16, 32, 255)

        self.menu_valign = CENTER
        self.menu_halign = CENTER

        self.intro = Intro()

        # then add the items
        items = [
            (MenuItem('Instructions', self.on_intro)),
            (MenuItem('Host game', self.on_host)),
            (MenuItem('Play game', self.on_join)),
            (MenuItem('Exit', self.on_quit)),
        ]

        self.create_menu(items, zoom_in(), zoom_out())

        #self.intro = Intro()
    def on_intro(self):
        director.push(Scene(self.intro))

    def on_host(self):
        director.push(game.get_game_scene())

    def on_enter(self):
        super(MainMenu, self).on_enter()
        self.children[0][1].do(
            self.children[0][1].selected_effect)  # making first item selected

    def on_join(self):
        director.push(game.get_game_scene)
        player = game.player.add()
        game.factory.clients.append(player)

    def on_join_regular(self):
        global game_controller
        game_controller = GameController()
        main_scene = Scene(
            game_controller.map, game_controller)
        director.push(main_scene)

        #adding a background layer that lies below all layers
        background_layer = ImageLayer(
            os.path.join("images", "backgrounds", "notebook-paper.png"))
        main_scene.add(background_layer, z=-1)

    def on_quit(self):
        director.pop()


def get_menu():
    """returns a menu Scene that will go to host or join_scene"""
    menu_scene = Scene(MainMenu())
    menu_scene.add(MenuBackground(), z=-1, name='background')
    return menu_scene


def main():
    director.init(
        width=WINDOW_WIDTH, height=WINDOW_HEIGHT, fullscreen=FULL_SCREEN)
    s = Scene(MainMenu())
    director.run(s)

if __name__ == '__main__':
    main()
