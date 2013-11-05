'''
updated version of player, to be used in multiplayer mode
'''

from pyglet.event import EventDispatcher
from cocos.layer import Layer
from models import CPU
from constants import *

class Player(EventDispatcher, Layer):

    def __init__(self, pid, special=None):
        super(Player, self).__init__()

        self.pid = pid

        self.color = PLAYER_COLORS[self.pid]

        #every unit has an id
        self.uid = 0

        self.units = {} #k: uid v: unit

        # the units that are currently under construction
        self.underConstruction = {}

        # number to indicate completed research
        self.completedResearch = 1

        # research we haven't completed but is avialable
        self.availableResearch = []

        #TODO: get rid of available research in favor of adding buttons
        self.unitActionLists = {
            "Ping": ["Ping"],
            "PingOfDeath": ["Attack"],
            "DOS": ["Attack"],
            "DNSPoison":["Attack"],
            "NMap": ["NMap"],
            "SQLInjection": ["Attack"],
            "Handshake": ["Shake"],
            "BufferOverflow": ["Attack"],
            "APTGet": [],
            "Installer": ["BAlgorithmFactory","BSoftwareUpdater"],
            "Firewall": [],
            "Sinkhole": [],
            "Server": ["TInstaller"],
            "Spoof": ["BSpoofedBuilding"],
            "SpoofedBuilding": ["DSpoof"],
            "RSA": [],
            "Database": [],
            "SoftwareUpdater": ["RPortScanner"],
            "AlgorithmFactory": ["TDOS"],
            "EncryptedTroop": ["Decrypt"],
            "CPU": []
        }

        self.idleCPUs = []

        self.busyCPUs = []

    def set_unit_uid(self,unit,uid=-1):
        #should really be called set_unit_uid
        if uid == -1: #we are the server
            unit.uid = self.uid
            self.uid += 1
        else: #server sent in the UID
            unit.uid = uid
            if self.uid <= uid:
                self.uid += 1
        return unit.uid

