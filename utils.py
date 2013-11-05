'''
utils.py
global util functions that compute distance, size, etc
'''
import os
import math
from pyglet.resource import media 
from cocos import collision_model, euclid
from music import theme_player
from constants import SLOT_RADIUS, ANGLE_MULTIPLIER
import constants

# a set of utility methods


def aabb_to_aa_rect(rect):
    half_width = abs(rect.left - rect.right) / 2
    half_height = abs(rect.top - rect.bottom) / 2
    return collision_model.AARectShape(euclid.Vector2(*rect.center), half_width, half_height)


def get_action_button_clicked(clicked_units):
    # Returns an action button if one was clicked. Else, returns False.
    pass


def set_slots(num, x, y):
    return [euclid.Vector2(x + SLOT_RADIUS * math.cos(ANGLE * math.pi / ANGLE_MULTIPLIER), y + SLOT_RADIUS * math.sin(ANGLE * math.pi / ANGLE_MULTIPLIER)) for ANGLE in range(3, 3 + num)]

def get_action_menu_slots(num, x, y):
    # num should be 4
    # return [euclid.Vector2(x - 133,y - 40*(slot - 1) + 10) for slot in range(num)]

    if num == 4:
        return [euclid.Vector2(x - 104, y + 67),
         euclid.Vector2(x - 127, y + 22),
         euclid.Vector2(x  - 127, y - 27),
         euclid.Vector2(x - 108, y - 72)]
    elif num == 8:
        return [euclid.Vector2(x - 104, y + 67),
         euclid.Vector2(x - 127, y + 22),
         euclid.Vector2(x  - 127, y - 27),
         euclid.Vector2(x - 108, y - 72),
         euclid.Vector2(x - 88, y - 90),
         euclid.Vector2(x + 118, y - 78),
         euclid.Vector2(x + 148, y - 30),
         euclid.Vector2(x + 158, y + 8)]

    
    # return [euclid.Vector2(x + SLOT_RADIUS * math.cos(ANGLE * math.pi / ANGLE_MULTIPLIER), y + SLOT_RADIUS * math.sin(ANGLE * math.pi / ANGLE_MULTIPLIER)) for ANGLE in range(3, 3 + num)]


def play_sound(filename):
    if constants.SOUND and not constants.MULTIPLAYER:
        sound = media(os.path.join('sounds', filename), streaming=False)
        sound.play()
    

def play_theme_song():
    theme_player.play()

def get_ip():
    import netifaces

    for i in netifaces.interfaces():
        a = netifaces.ifaddresses(i)
        if 2 in a.keys() and 'addr' in a[2][0].keys():
            if a[2][0]['addr'][:3] == "137":
                return a[2][0]['addr']
    return None


