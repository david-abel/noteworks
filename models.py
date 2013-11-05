import os
import re
import time
import thread
import random
from threading import Timer

from cocos import euclid
from cocos.actions import MoveTo, Delay
from cocos.actions.instant_actions import CallFunc, Hide, Show
from cocos.sprite import *
from pyglet.resource import media
from cocos.actions import FadeOut

import utils
import objects
from constants import *
from utils import aabb_to_aa_rect

class Packet(Sprite):
    speed = 1

    def __init__(self, position):
        parity = random.choice(["0","1"])
        super(Packet, self).__init__(os.path.join("images", "packet" + parity + ".png"))
        self.position = position
        self.onMap = False


class Unit(Sprite):

    def __init__(self, image, curVertex, health=0, pid=0, buildTime=1):
        super(Unit, self).__init__(image)
        self.imageName = image
        self.imageName = image.split("/")[2]
        self.imageOutline = "images/outlines/" + self.imageName.split(".")[0] + "_outline.png"

        self.initialHealth = health

        self.pid = pid

        tid = -1  # id of type of troop

        self.maxHealth = health

        self.buildTime = buildTime/TEST_SPEEDUP

        self.playerIndicator = None

        self.curVertex = curVertex

        self.health = 1

        self.uid = -1

        self.slotIndex = -1

        self.isSelected = False

        self.menu = None

        self.isDestroyed = False

        self.isSelectable = True  # if a unit is performaing certain actions (ping), it can't be selected

        self.color = (255,255,255)

        self.selectedColor = (200,200,200)

        self.unselectedColor = self.color

        self.selectedSprite = None

        self.isRemoved = False


    def on_completion(self):
        pass

    def on_destruction(self):  # called when unit is destroyed
        pass

    def set_is_selected(self, selectedVal, gameMap, cm, player):
        # Sets the current selected value to the input param 'selectedVal' and
        # scales image accordingly.
        if selectedVal == True:
            self.curVertex.highlight_adjacents(True)
        else:
            self.curVertex.highlight_adjacents(False)

        if selectedVal == self.isSelected:
            return

        if selectedVal:
            self.scale = UNIT_SCALE_SELECTED
            self.unselectedColor = self.color
            if self.playerIndicator:
                self.playerIndicator.visible = False
            self.color = self.selectedColor
            if self.selectedSprite:
                self.add(self.selectedSprite)
            if not type(self) == CPU:
                self.display_action_menu(gameMap, cm, player)
        else:
            self.scale = UNIT_SCALE_NORMAL
            self.color = self.unselectedColor
            if self.playerIndicator:
                self.playerIndicator.visible = True
            if self.selectedSprite:
                self.remove(self.selectedSprite)
            if not type(self) == CPU:
                self.clear_action_menu(gameMap, cm, player)
        self.isSelected = selectedVal

    def display_action_menu(self, gameMap, cm, player):
        # Displays this unit's action menu (if it has one)
        # I don't know why we need to reinitialize this each time, but we need
        # to.
        from game_layers import ActionMenu
        if issubclass(type(self), Troop):
            index = self.slotIndex  # TODO, fix this for other positions
            position = self.curVertex.actionMenuSlots[index]
        elif issubclass(type(self), Building):
            position = self.position

        self.menu = ActionMenu(position[0], position[1], self.get_action_list(player), self)
        if self.actionList != []:
            gameMap.add(self.menu, z=4)
            self.menu.add_action_buttons(gameMap, cm)

    def clear_action_menu(self, gameMap, cm, player):
        # Hides this unit's action menu.
        if self.get_action_list(player) != [] and self.menu != None:
            try:
                gameMap.remove(self.menu)
                self.menu.remove_action_buttons(gameMap, cm)
            except:
                self.menu.remove_action_buttons(gameMap, cm)

    def get_action_list(self, player):
        # Returns the up to date action list for this unit (based on player research)
        self.actionList = player.unitActionLists[self.__class__.__name__]
        return self.actionList

    def on_attack(self, power, attacker):
        # attacker = the one attacking
        # self is the target being attacked

        c = objects.Objects.get_controller()
        c.client_attack(self.pid,self.uid,power)
        self.health -= power
        self.color = (self.unselectedColor[0] * float(self.health) / self.maxHealth, self.unselectedColor[1] *
                      float(self.health) / self.maxHealth, self.unselectedColor[2] * float(self.health) / self.maxHealth)
        
        if self.health <= 0:
            # Destroyed the target unit. Remove it from our set of things to attack and destroy the unit.
            if self in attacker.shouldAttack:
                attacker.shouldAttack.remove(self)
            self.shouldAttack = set()
            if not self.isDestroyed:
                self.isDestroyed = True
                self.isSelectable = False
                self.do(CallFunc(self.destroy_action))

    def client_on_attack(self,power):
        self.health -= power
        self.color = (self.unselectedColor[0] * float(self.health) / self.maxHealth, self.unselectedColor[1] *
                      float(self.health) / self.maxHealth, self.unselectedColor[2] * float(self.health) / self.maxHealth)

    def destroy_action(self):
        self.on_destruction()
        controller = objects.Objects.get_controller()
        controller.remove_unit(self)

Unit.register_event_type("on_destruction")


class Troop(Unit):

    def __init__(self, image, curVertex, health=0, pid=0, speed=0, power=0, attackRange=0, buildTime=1):

        fullImagePath = os.path.join("images", "troops", image)

        super(Troop, self).__init__(fullImagePath, curVertex, health, pid=pid, buildTime=buildTime)


        self.initialHealth = health

        self.playerIndicator = Sprite(os.path.join("images","troops", "player.png"))
        self.playerIndicator.color = PLAYER_COLORS[self.pid]
        self.playerIndicator.opacity = 0
        self.add(self.playerIndicator,z=-1)

        
        if not curVertex.add_troop(self):
            self.slotIndex = -1
            return

        self.position = curVertex.troopSlots[self.slotIndex].position
        self.cshape = aabb_to_aa_rect(self.get_AABB())
        self.cshape.center = self.position

        self.power = power

        # keep track of the destination while troop is moving
        self.destVertex = None

        self.speed = float(speed) * TEST_SPEEDUP

        self.attackRange = attackRange

        self.scale = UNIT_SCALE_NORMAL

        # the target sets this flag to False once it's died
        self.shouldAttack = set() # A set containing the enemies that this thing should attack (when empty we should stop attacking)

        self.is_attacking = False

        self.attackingPath = []

        self.packets = []

        self.targetVid = -1

        self.sourceVid = -1

        for i in range(4):
            self.packets.append(Packet(self.position))
        # a pool of packets to use when animating attacks

    def update_opacity(self,o):
        self.opacity = o
        self.playerIndicator.opacity = o

    def attack(self, target, m):
        # Already gauranteed that self.pid and target.pid !=
        if self.is_attacking and type(self) != BufferOverflow:
            # Ignore for BufferOverflow as it can attack >1 unit
            # DEBUG
            # print "already attacking"
            return
        self.shouldAttack.add(target)
        if self.can_attack(target):
            path = m.get_path(self.curVertex, target.curVertex, self.pid, self, "attack")
            
            if path and len(path) <= self.attackRange + 1:
                self.attackingPath = path
                self.is_attacking = True
                c = objects.Objects.get_controller()
                c.client_attack_animation(self.pid,self.uid,target.pid,target.uid,self.attackingPath)
                self.targetVid = target.curVertex.vid
                self.sourceVid = self.curVertex.vid
                self.schedule_interval(self.attack_action, 1, target, m)
        else:
            # Can't attack. Let the user know
            utils.play_sound("error.wav")
        return


    def client_attack(self,target,m): #only animate, no actual attack
        self.is_attacking = True
        self.schedule_interval(self.animate_packets,1,target,m)

    def can_attack(self, target):
        # Determines if this unit can attack the given target                                                                                           # CHANGE THIS 'UNIT' TO BUILDING IF WE ONLY WANT DNS TO ATTACK BUILDINGS
        if (issubclass(type(target),Unit) and type(self) != DNSPoison and type(self) != SQLInjection) or (type(self) == DNSPoison and issubclass(type(target),Unit)):
            # Either we're a normal troop attacking any Unit, or we're a DNSPoison and can only attack Buildings.

            return True
        elif type(self) == SQLInjection and issubclass(type(target),Unit) and target.curVertex.building != None and (type(target.curVertex.building) == Server or type(target.curVertex.building) == Database):
            # SQLInjection attacking an enemy unit in a vertex with a Server or Database.
            return True
        else:
            return False

    def attack_action(self, dt, target, gameMap):
        targetVid = target.curVertex.vid
        sourceVid = self.curVertex.vid
        c = objects.Objects.get_controller()
        if len(self.shouldAttack) > 0:
            if target in self.shouldAttack:
                if sourceVid != self.sourceVid:
                    self.end_attack()
                    return
                if self.targetVid != targetVid:  # target moved
                    self.attackingPath = gameMap.get_path(self.curVertex, target.curVertex, self.pid, self, action="Attack")
                    
                    if self.attackingPath == None or len(self.attackingPath) > self.attackRange:
                        self.end_attack()
                        return
                    c.client_attack_animation(self.pid,self.uid,target.pid,target.uid,self.attackingPath)
                    self.targetVid = targetVid
                target.on_attack(self.power, self)
                self.animate_packets(dt,target,gameMap)
        else:
            self.end_attack()


    def animate_packets(self,dt,target,gameMap):
        #### packet logic ###
        if self.is_attacking:
            if self.packets:
                p = self.packets.pop()
                p.position = self.position
                if not p.onMap:
                    p.onMap = True
                    gameMap.add(p, z=PACKET_Z)
                action = Show()
                action += MoveTo(gameMap.vertices[self.attackingPath[0]].position, 0.2)
                for v in self.attackingPath[1:]:
                    vertex = gameMap.vertices[v]
                    action += MoveTo(vertex.position, float(1 / p.speed))
                action += MoveTo(target.position, 0.2)
                action += Hide()
                p.do(action)
                self.packets.insert(0, p)
            ### end of packet logic ###


    def end_attack(self,isClient=False):
        for p in self.packets:
            p.stop()
            p.visible = False
        self.shouldAttack = set()
        self.is_attacking = False
        c = objects.Objects.get_controller()
        if not isClient:
            self.unschedule(self.attack_action)
            c.client_attack_animation(self.pid,self.uid,-1,-1,[])
        else:
            self.unschedule(self.animate_packets)

    def add_to_map(self, m):
        m.add(self, TROOP_Z)

Troop.register_event_type("troop_attack")


class Building(Unit):

    def __init__(self, image, curVertex, health=0, pid=0, buildTime=1):
        fullImagePath = os.path.join("images", "buildings", image)
        super(Building, self).__init__(fullImagePath, curVertex, health, pid, buildTime=buildTime)

        # flag to check if unit is busy doing something
        self.isBusy = False
        self.initialHealth = health

        
        if not curVertex.add_building(self):
            self.slotIndex = -1
            return

        if type(self) == CPU:
            self.position = curVertex.position  
        else:
            self.position = euclid.Vector2(curVertex.buildingSlot.position[0], curVertex.buildingSlot.position[1] + 10)
        self.cshape = aabb_to_aa_rect(self.get_AABB())
        self.cshape.center = self.position

    def add_to_map(self, m):
        m.add(self, BUILDING_Z)

    def update_opacity(self,o):
        self.opacity = o

class EncryptedTroop(Troop):
    def __init__(self, curVertex=None, position=None, health=24, pid=0, buildTime=0, speed=2):

        super(EncryptedTroop, self).__init__("encrypted_troop.png", curVertex, health, pid, speed=speed, buildTime=buildTime)
        self.originalType = None

class Ping(Troop):

    def __init__(self, curVertex, health=24, pid=0, speed=1.0):
        super(Ping, self).__init__('ping_gray.png', curVertex, health, pid, speed,buildTime=10)
        self.selectedSprite = Sprite("images/troops/ping.png")
        self.tid = "Ping"

    def ping(self, delete_method):
        c = objects.Objects.get_controller()
        if self.curVertex.borderVertices:
            curVertex = self.curVertex
            for asID in self.curVertex.borderVertices.keys():
                destVertexList = self.curVertex.borderVertices[asID]
                for destVertex in destVertexList:
                    if destVertex.asID not in c.visibleASes:
                        self.isSelectable = False
                        self.isDestroyed = True
                        pingAction = MoveTo(self.curVertex.position, 0.6)
                        pingAction += MoveTo(destVertex.position, 2)
                        pingAction += MoveTo(self.curVertex.position, 2)
                        pingAction += CallFunc(c._show_as, asID)
                        # pingAction += CallFunc(utils.play_sound, "Visible.wav")
                        pingAction += CallFunc(delete_method, self)
                        pingAction += CallFunc(curVertex._update_visibility)

                        self.do(pingAction)
                        self.dispatch_event("Ping")

                        utils.play_sound("ping.wav")

                        return True  # We successfully pinged. Return True.

        return False


Ping.register_event_type("Ping")


class DOS(Troop):

    def __init__(self, curVertex, health=32, pid=0, speed=1, power=2, attackRange=2):
        super(DOS, self).__init__("dos_gray.png", curVertex, health, pid, speed, power, attackRange=attackRange,buildTime=11)
        self.selectedSprite = Sprite("images/troops/dos.png")
        self.tid = "DOS"


class BufferOverflow(Troop):

    def __init__(self, curVertex, health=48, pid=0, speed=0.25, power=2, attackRange=2):
        super(BufferOverflow, self).__init__("buffer_overflow_gray.png", curVertex, health, pid, speed,power, attackRange=attackRange,buildTime=25)
        self.selectedSprite = Sprite("images/troops/buffer_overflow.png")
        self.tid = "BufferOverflow"


class SQLInjection(Troop):

    def __init__(self, curVertex, health=60, pid=0, speed=0.4, power=10, attackRange=2):
        super(SQLInjection, self).__init__("sql_injection_gray.png", curVertex, health, pid, speed,power, attackRange=attackRange,buildTime=18)
        self.selectedSprite = Sprite("images/troops/sql_injection.png")
        self.tid = "SQLInjection"


class PingOfDeath(Troop):

    def __init__(self, curVertex, health=96, pid=0, speed=0.3, power=10000, attackRange=2):
        super(PingOfDeath, self).__init__("ping_of_death_gray.png", curVertex, health, pid, speed,power, attackRange=attackRange,buildTime=20)
        self.selectedSprite = Sprite("images/troops/ping_of_death.png")
        self.tid = "PingOfDeath"

    def attack(self, target, gameMap):
        from maps import Vertex
        if type(target) == Vertex or ((issubclass(type(target), Troop) or type(target) == Firewall) and target.pid != self.pid):
            # Clicked a vertex or an enemy troop or an enemy Firewall
            if type(target) != Vertex:
                target = target.curVertex
            path = gameMap.get_path(self.curVertex, target, self.pid, self, "attack")
            if path and len(path) <= self.attackRange + 1:
                self.attackingPath = path
                self.is_attacking = True

                # Move the Ping Of Death to the dest vertex
                pingOfDeathAction = Delay(0)

                for vertexID in path:
                    vertex = gameMap.vertices[vertexID]
                    pingOfDeathAction += MoveTo(vertex.position, self.speed)

                # Execute Ping Of Death!
                pingOfDeathAction += CallFunc(self.POD, target)
                
                controller = objects.Objects.get_controller()
                pingOfDeathAction += CallFunc(controller.remove_unit, self)
                self.do(pingOfDeathAction)
                return True
        return False
        

    def POD(self, target):
        hitEnemyTroop = False

        if target.building != None and type(target.building) == Firewall and target.building.pid != self.pid:
            # DESTROY FIREWALL
            target.building.destroy_action()
            hitEnemyTroop = True
            self.isDestroyed = True

        s = objects.Objects.get_controller()
        for slot in target.troopSlots.values():
            troop = slot.troop
            if troop.pid != self.pid:
                # Halves the health of this troop
                troop.on_attack((troop.health + 1) / 2,self)
                self.isDestroyed = True
                hitEnemyTroop = True
        if self.pid == s.pid:
            if hitEnemyTroop:
                utils.play_sound("ping_of_death.wav")
            else:
                utils.play_sound("ping_of_death_fail.wav")

class DNSPoison(Troop):
    
    def __init__(self, curVertex, health=42, pid=0, speed=0.1, power=7, attackRange=2):
        super(DNSPoison, self).__init__("dns_poison_gray.png", curVertex, health, pid, speed,power, attackRange=attackRange,buildTime=28)
        self.selectedSprite = Sprite("images/troops/dns_poison.png")
        self.tid = "DNSPoison"



class Installer(Troop):

    def __init__(self, curVertex, health=32, pid=0, speed=0.5):
        super(Installer, self).__init__("constructor0.png", curVertex, health, pid, speed,buildTime=6)
        self.tid = "Installer"


class APTGet(Troop):

    def __init__(self, curVertex, health=48, pid=0, speed=0.5):
        super(APTGet, self).__init__("constructor1.png", curVertex, health, pid, speed,buildTime=6)
        self.tid = "APTGet"


class NMap(Troop):

    def __init__(self, curVertex, health=100, pid=0, speed=0.15):
        super(NMap, self).__init__("nmap.png", curVertex, health, pid, speed,buildTime=8)
        self.tid = "NMap"

class Handshake(Troop):

    def __init__(self, curVertex, health=20, pid=0, speed=0.15):
        super(Handshake, self).__init__("handshake_gray.png", curVertex, health, pid, speed,buildTime=8)
        self.selectedSprite = Sprite("images/troops/handshake.png")
        self.tid = "Handshake"

    def shake(self, other):
        # Adds an edge between this Handshakes vertex and the vertex that the destShake troop is in.
        # returns edges to draw
        c = objects.Objects.get_controller()
        source = c.map.vertices[str(self.curVertex.vid)]
        dest = c.map.vertices[str(other.curVertex.vid)]
        source_position = c.map.vertexPositions[source.vid]
        dest_position = c.map.vertexPositions[dest.vid]

        # checking whether a valid edge can be made
        if dest == source:
            print "Can't make an edge to the same vertex"
            # error sound
        else:
            # if destShake's curvertex is in your own AS make the edges
            from maps import Edge, ASEdge
            if source.asID != dest.asID:  # create asEdge
                source.borderVertices[dest.asID].append(dest)
                dest.borderVertices[source.asID].append(source)
                new_edge = ASEdge(source_position, dest_position, source, dest, AS_EDGE_COLOR, visible=True)
            else:  # create normal edge
                # DEBUG
                # print "Internal Edge Making"
                new_edge = Edge(source_position, dest_position, source, dest, EDGE_COLOR, visible=True)

            # Storing edge in approriate places and updating adjaceny vertex list, and adding it to the map
            source.adjacentVertices.append(dest)
            dest.adjacentVertices.append(source)

            source.edges.append(new_edge)
            dest.edges.append(new_edge)

            new_edge.visible = True

            c.map.edges.append(new_edge)
            c.map.add(new_edge, z=EDGE_Z)

            c.remove_unit(other)
            c.remove_unit(self)


class Spoof(Troop):

    def __init__(self, curVertex, health=50, pid=0, speed=0.5):
        super(Spoof, self).__init__("spoof_gray.png", curVertex, health, pid, speed,buildTime=5)
        self.selectedSprite = Sprite("images/troops/spoof.png")
        self.tid = "Spoof"

class SpoofedBuilding(Building):

    def __init__(self, curVertex, health=50, pid=0):

        image = random.choice(["firewall.png", "research_factory.png", "algorithm_factory.png", "sinkhole.png", "server.png", "rsa.png",
"database.png"]) # Picks a random image

        self.buildingType = {
        "firewall.png":Firewall, 
        "research_factory.png":SoftwareUpdater,
        "algorithm_factory.png":AlgorithmFactory,
        "sinkhole.png":Sinkhole,
        "server.png":Server,
        "rsa.png":RSA,
        "database.png":Database
        }[image]
        super(SpoofedBuilding, self).__init__(image, curVertex, health, pid, buildTime=7)
        self.tid = "SpoofedBuilding"

class Firewall(Building):

    def __init__(self, curVertex, health=190, pid=0):
        super(Firewall, self).__init__("firewall.png", curVertex, health, pid,buildTime=27)
        self.tid = "Firewall"

class SoftwareUpdater(Building):
    def __init__(self, curVertex, health=130, pid=0):
        super(SoftwareUpdater, self).__init__("research_factory.png", curVertex, health, pid,buildTime=12)
        self.tid = "SoftwareUpdater"

class AlgorithmFactory(Building):
    def __init__(self, curVertex, health=130, pid=0):
        super(AlgorithmFactory, self).__init__("algorithm_factory.png", curVertex, health, pid,buildTime=12)
        self.tid = "AlgorithmFactory"

class Sinkhole(Building):
    def __init__(self, curVertex, health=150, pid=0):
        super(Sinkhole, self).__init__("sinkhole.png", curVertex, health, pid,buildTime=13)
        self.tid = "Sinkhole"
        self.shouldAttack = set()

class CPU(Building):
    def __init__(self, initCore, health=90, pid=0):
        super(CPU, self).__init__("cpu.png", initCore, health, pid,buildTime=40)
        self.action = None
        self.transTimer = None
        self.tid = "CPU"

class Server(Building):
    def __init__(self, curVertex, health=220, pid=0):
        super(Server, self).__init__("server.png", curVertex, health, pid,buildTime=0)
        self.tid = "Server"


class RSA(Building):
    def __init__(self, curVertex, player=None, health=100, pid=0,buildTime=9):
        super(RSA, self).__init__("rsa.png", curVertex, health, pid)
        # DEPRECATED, use self.pid instead
        self.player = player  # Store owner so we can auto encrypt.
        self.tid = "RSA"

    def on_completion(self):
        c = objects.Objects.get_controller()
        self.curVertex.color = (0, 0, 0)
        c.map.batch_remove(self.curVertex)
        c.map.batch_add(self.curVertex, z=RSA_Z)

    def on_destruction(self):
        c = objects.Objects.get_controller()
        self.curVertex.color = (255, 255, 255)
        c.map.batch_remove(self.curVertex)
        c.map.batch_add(self.curVertex, z=VERTEX_Z)


class Database(Building):
    def __init__(self, curVertex, health=150, pid=0,buildTime=30):
        super(Database, self).__init__("database.png", curVertex, health, pid)
        self.tid = "Database"
        
    def on_completion(self):
        c = objects.Objects.get_controller()
        self.curVertex.numOfSlots = 8
        self.curVertex.draw_empty_slot_sprites(c.map)

    def on_destruction(self):
        c = objects.Objects.get_controller()
        self.curVertex.numOfSlots = 4
        self.curVertex.draw_empty_slot_sprites(c.map)


# constant for units, has to be here to avoid circular reference
ALL_UNITS = {
    "Ping": Ping,
    "PingOfDeath": PingOfDeath,
    "Installer": Installer,
    "APTGet": APTGet,
    "SQL": SQLInjection,
    "DOS": DOS,
    "DNSPoison": DNSPoison,
    "Firewall": Firewall,
    "Server": Server,
    "AlgorithmFactory": AlgorithmFactory,
    "SoftwareUpdater": SoftwareUpdater,
    "RSA": RSA,
    "Database": Database
}
