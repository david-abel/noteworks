from game_layers import MessageInstruction
from cocos.sprite import *
from cocos import euclid
from constants import CELL_SIZE
from models import Ping, Installer, AlgorithmFactory, DOS
import os


class Tutorial(object):

    def __init__(self, lvlNum, controller):
        super(Tutorial, self).__init__()
        self.curPrompt = 0
        self.lvlNum = lvlNum

        if lvlNum == 1:
            self.t = L1Tutorial()
        if lvlNum == 2:
            self.t = L2Tutorial()

        self.prompt_stats = self.t.prompt_stats
        self.prompts = self.t.prompts
        self.prompt_visual_aids = self.t.prompt_visual_aids
        self.prompt_visual_aid_stats = self.t.prompt_visual_aid_stats
        self.game_states = self.t.game_states
        self.controller = controller
        self.message = None
        self.visual_aids = None
        self.cur_vertex_highlight = None

    def next_prompt(self):
        # self.message.removeMessage()
        for visual in self.visual_aids:
            visual.remove_visual_aid()

        if self.curPrompt == 4:
            self.cur_vertex_highlight = self.highlight_vertex(4)
        
        if self.curPrompt == 6:
            self.cur_vertex_highlight = self.highlight_vertex(5)

        if self.curPrompt == 5:
            self.cur_vertex_highlight.remove_highlighted_vertex()

        if self.curPrompt == 7:
            self.cur_vertex_highlight.remove_highlighted_vertex()

        if self.curPrompt < len(self.prompts):
            # self.message = self.get_message()
            self.visual_aids = self.get_visual_aids()
            self.curPrompt += 1

        # print "calling next prompt"

    def first_prompt(self, state):
        # should only be called in on_enter
        if self.get_cur_state()[0] == state:
            # self.message = self.get_message()
            self.visual_aids = self.get_visual_aids()
            self.curPrompt += 1

    def get_message(self):
        return MessageInstruction(self.controller, self.prompts[self.curPrompt], False, *self.prompt_stats[self.curPrompt])

    def get_visual_aids(self):

        visual_aids = []
        i = 0
        for image in self.prompt_visual_aids[self.curPrompt]:
            visual_aids.append(
                TutorialVisualAid(self.controller, image, self.prompt_visual_aid_stats[
                                  self.curPrompt][i][0], self.prompt_visual_aid_stats[self.curPrompt][i][1])
            )
            i += 1

        return visual_aids

    def player_unit_attack(self, troop_type):
        # DEBUG
        # print "player_unit_attack"
        if troop_type == self.get_cur_state()[1] and self.get_cur_state()[0] == "player_unit_attack":
            self.next_prompt()

    def click_on_move(self, troop_type, destID):
        # DEBUG
        # print "click_on_move"
        curState = self.get_cur_state()
        if troop_type == curState[1] and curState[0] == "click_on_move":
            if (curState[2] == -1) or (int(curState[2]) == int(destID)):
                self.next_prompt()

    def click_on_action(self, actionName):
        # DEBUG
        # print "click_on_action"
        print actionName, self.get_cur_state()[1]
        if actionName == self.get_cur_state()[1] and self.get_cur_state()[0] == "click_on_action":
            self.next_prompt()
            # print "hello its me"

    def player_add_unit(self, troop_type):
        # print "player_add_unit"
        if  self.get_cur_state()[1] == troop_type and self.get_cur_state()[0] == "player_add_unit":
            self.next_prompt()
            # print "indicator sade in player add_unit"
            

    def get_cur_state(self):
        if self.curPrompt < len(self.game_states):
            return self.game_states[self.curPrompt]
        return [None]

    def player_add_building(self, building_type):
        if building_type == self.get_cur_state()[1] and self.get_cur_state()[0] == "player_add_building":
            self.next_prompt()

    def highlight_vertex(self, vertex_id):
        return HighlightedVertex(vertex_id, self.controller)

class TutorialVisualAid(Sprite):
    def __init__(self, layer, image, x, y):
        super(TutorialVisualAid, self).__init__(image)
        self.sprite = Sprite(image)
        self.sprite.position = x, y
        self.layer = layer
        self.layer.add(self.sprite)

    def remove_visual_aid(self):
        self.sprite.kill()

class HighlightedVertex(Sprite):
    def __init__(self, vertex_id, controller, is_active=True):
        super(HighlightedVertex, self).__init__("images/tutorial/vertex_highlighted.png")
        self.vertex_id = vertex_id
        self.controller = controller
        self.is_active = is_active
        vertex_position = self.controller.map.vertexPositions[
            str(vertex_id)]
        col = vertex_position[0]
        row = vertex_position[1]
        self.position = euclid.Vector2(col * CELL_SIZE, row * CELL_SIZE)
        self.controller.map.add(self)

    def remove_highlighted_vertex(self):
        self.kill()


class L1Tutorial():

    def __init__(self):
        #self.prompts is deprecated
        self.prompts = [
            '''To get started, first build Ping troops. Ping lets you to locate the enemy. You can't see them now but they're there!\n1. Click the server \n2. Click Ping'''
            , '''Servers can create troops called Installers that create buildings.\n1. Click the server \n2. Click the Installer'''
            , '''Build the building by moving the Installer to a new location.\n1. Left click your Installer \n2. Right click the location you want to build on.'''
            , '''Let's build an algorithm factory, it will allow you to build attack.\n1. Click the Installer\n2. Click the Algorithm Factory'''
            , '''Now you need troops that allows you to attack an enemy once you see it. Build 2 DOS troops.\n1. Click the Algorithm Factory\n2. Click the DOS troop'''
            , '''Now you need troops that allows you to attack an enemy once you see it. Build 2 DOS troops.\n1. Click the Algorithm Factory\n2. Click the DOS troop'''  # I'm duplicating this because we need to build 2 DOS
            , '''Remember Ping, now we will use it to find the enemy. Move a ping unit to the highlighted vertex.\n1. Left click Ping \n2. Right click the highlighted location'''
            , '''Let's actually use the Ping troop to see the enemy. \n1. Click Ping \n2. Click the attack button.'''
            , '''Now move your DOS troop to the location of the enemy and prepare for attack'''
            , '''You can see the enemy now, lets attack em!\n1. Click DOS and then the attack button\n2.Click on an enemy troop'''

        ]

        self.prompt_visual_aids = [
                [os.path.join("images", "tutorial", "instruction1.png")], 
                [os.path.join("images", "tutorial", "instruction2.png")], 
                [os.path.join("images", "tutorial", "instruction3.png")], 
                [os.path.join("images", "tutorial", "instruction4.png")], 
                [os.path.join("images", "tutorial", "instruction5.png")], 
                [os.path.join("images", "tutorial", "instruction6.png")], 
                [os.path.join("images", "tutorial", "instruction7.png")], 
                [os.path.join("images", "tutorial", "instruction8.png")]
        ]

        self.game_states = [["on_enter", None], 
                            ["player_add_unit", "Installer"], 
                            ["click_on_move", "Installer", -1], 
                            ["player_add_unit", "AlgorithmFactory"], 
                            ["player_add_unit", "DOS"], 
                            ["click_on_move", "Ping", 4], 
                            ["click_on_action", "Ping"], 
                            ["click_on_move", "DOS", 5], 
                            ["player_unit_attack", "DOS"]]
        
        self.prompt_stats = [(400, 450, 700, 300, 22), 
                            (350, 450, 600, 300, 22), 
                            (350, 450, 600, 300, 22), 
                            (400, 450, 700, 300, 22), 
                            (350, 450, 600, 300, 22), 
                            (350, 450, 600, 300, 22), 
                            (300, 450, 500, 300, 22), 
                            (300, 450, 500, 300, 22), 
                            (300, 450, 500, 300, 22), 
                            (300, 450, 500, 300, 22), 
                            (300, 450, 500, 300, 22), 
                            (300, 450, 500, 300, 22)]
        
        self.prompt_visual_aid_stats = [[(180, 570)], 
                                        [(180, 140)], 
                                        [(700, 560)], 
                                        [(180, 570)], 
                                        [(180, 570)], 
                                        [(180, 570)], 
                                        [(180, 140)],
                                        [(600, 560)], 
                                        [(180, 600)]]

class L2Tutorial():

    def __init__(self):
        self.prompts = []
