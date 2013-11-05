from controller import GameController
from constants import WINDOW_WIDTH, WINDOW_HEIGHT, FULL_SCREEN
from cocos.director import director
from cocos.layer.base_layers import Layer
from cocos.scene import Scene
from cocos.scenes.transitions import FadeTransition
from cocos.text import Label, TextElement, RichLabel
from cocos.utils import SequenceScene
from cocos.actions.interval_actions import MoveBy, Delay
from constants import BACKGROUND_Z, WINDOW_WIDTH, WINDOW_HEIGHT, FULL_SCREEN
from imageLayer import ImageLayer
from game import *
from cocos.actions.interval_actions import FadeIn

from cocos import pygletreactor
pygletreactor.install()

director.init(width=WINDOW_WIDTH, height=WINDOW_HEIGHT, fullscreen=FULL_SCREEN)

s = Scene(MainMenu())
menu_background = ImageLayer(os.path.join("images", "backgrounds", "menu-chalkboard.png"))
menu_background.position = (0,0)
menu_background.anchor = (0.0, 0.0)
menu_background.scale = 1
s.add(menu_background)


# blank_scene = Scene()
# director.run(FadeTransition(s, 1, blank_scene))


def director_run_no_loop(scene):
    # this is the same as director.run, without the eventloop

    director.scene_stack.append(director.scene)
    director._set_scene(scene)

# trans = FadeTransition(s,2,Scene(IntroText()))

sequence = SequenceScene(Scene(IntroText()), s)

#director.run(sequence)
director_run_no_loop(sequence)

from twisted.internet import reactor
reactor.run(call_interval=0.08)
