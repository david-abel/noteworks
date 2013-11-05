import math
import utils
import cocos

from cocos.actions.instant_actions import CallFuncS
from cocos.actions.interval_actions import MoveTo, Delay
from cocos.director import director
from twisted.internet.endpoints import TCP4ClientEndpoint, TCP4ServerEndpoint
from twisted.python.log import err

from clientController import ClientController, EndMenu
from commands import *
import constants
from constants import UNIT_STARTING_OPACITY, TIMER_Z
from maps import Vertex
from game_layers import InfoLayer, ActionButton,TransTimer, MenuButton
from models import *
from utils import get_action_button_clicked
from research import RESEARCH
from client import ServerNoteFactory
import music
from twisted.internet import reactor


# this deals with all the game logic, sorta replaces our old controller.py and some of player.py


class ServerController(ClientController):

    def __init__(self,mapName):
        super(ServerController, self).__init__(mapName)

        self.pid = self.map.players.pop(0)

        self.connectedClients = {}  # k:pid, v:IP of connected clients

        self.connectedClientsIP = {}  # k:IP, v:pid

        self.gameStarted = False
        # start the AI players, todo later
        
        self.curLevel = 1


    '''
    Local methods
    '''

    def on_enter(self):
        # self.gameStarted = True
        self._init_players()
        super(ServerController, self).on_enter()
        self.schedule_interval(self.update_build_status, 0.5)


    # updates the buildings' health and build status
    # called every 0.1 second
    def update_build_status(self, dt):
        for p in self.players.values():
            for uid in p.underConstruction.keys():
                unit = p.underConstruction[uid]
                unit.health += unit.maxHealth * (dt / unit.buildTime)
                self._complete_build(unit, p, uid)
                if type(unit) != CPU:
                    self.client_update_health(uid, unit.health, p.pid)

    def execute_action(self, actionName, unit):
        if actionName[0] == "B":
            if actionName[1:] == "CPU": #build CPU
                for a in self.visibleASes:
                    if self.map.AS[a].cores:
                        k, core = self.map.AS[a].cores.popitem()
                        self.map.AS[a].usedCores[k] = core
                        self.build_unit(actionName[1:],self.player,core.vid, unit)
                        break
            else:
                self.build_unit(actionName[1:], self.player, unit.curVertex.vid, unit)
        elif actionName[0] == "T":
            self.build_unit(actionName[1:], self.player, unit.curVertex.vid)
        elif actionName == "DEL":
            self.remove_unit(unit)
        elif actionName[0] == "R":
            self.perform_research(actionName,self.player,unit)
        elif actionName == "Ping":
            unit.ping(self.remove_unit)
        elif actionName == "UPingOfDeath":
            self.upgrade_unit(unit,actionName[1:])
        elif actionName == "UNMap":
            self.upgrade_unit(unit,actionName[1:])
        elif actionName == "USinkhole":
            self.upgrade_unit(unit,actionName[1:])
        elif actionName == "Shake":
            self.curAction = "Shake"
            self.selectedUnits = [unit]
        elif actionName == "Attack":
            self.curAction = "Attack"
            self.selectedUnits = [unit]
        elif actionName == "Decrypt":
            self.upgrade_unit(unit,unit.originalType)
        self.dispatch_event("click_on_action", actionName)

    '''
    Local/Network triggered methods
    '''

    def hand_shake(self,h1,h2):
        h1.shake(h2)

    def attack_unit(self,target,attacker=None):
        if attacker == None:
            if self.selectedUnits:
                attacker = self.selectedUnits.pop()
        if type(attacker) == BufferOverflow:
            # A bufferoverflow is attacking - attack all enemy troops and enemy building!
            if type(target) == Vertex:
                targetVertex = target
            else:
                targetVertex = target.curVertex

            attacker.should_attack = 0

            for troopSlot in targetVertex.troopSlots.values():
                troop = troopSlot.troop
                if troop.pid != attacker.pid: # Not sure we need this?
                    attacker.should_attack += 1
                    attacker.attack(troop,self.map)
            if targetVertex.building != None and targetVertex.building.pid != attacker.pid:
                attacker.should_attack += 1
                attacker.attack(targetVertex.building,self.map)

            if attacker.should_attack == 0:
                attacker.should_attack = 1

        else:
            # Generic attack
            attacker.attack(target,self.map)


    def build_unit(self, tid, owner, vid, builder=None,onInit=False):
        curVertex = self.map.get_vertex(vid)
        newUnit = self.build_unit_common(tid, owner, curVertex, builder=builder,onInit=onInit)

        if newUnit and not onInit:

            for pid in self.connectedClients.keys():
                d = self.connect_end_point(self.connectedClients[pid])
                def c(ampProto):
                    return ampProto.callRemote(BuildUnit, pid=owner.pid, tid=tid, vid=vid, uid=newUnit.uid,buid=-1)
                d.addCallback(c)
                d.addErrback(err)

            if newUnit.buildTime != 0:
                owner.underConstruction[newUnit.uid] = newUnit
                newUnit.update_opacity(math.floor(curVertex.visibilityState) * UNIT_STARTING_OPACITY)

        return newUnit

    def upgrade_unit(self,oldUnit,newType):

        curVertex = oldUnit.curVertex
        owner = self.players[oldUnit.pid]
        self.remove_unit(oldUnit)
        newUnit = self.build_unit(newType,owner,curVertex.vid)
        if newType == "EncryptedTroop":
            newUnit.originalType = oldUnit.__class__.__name__ #get string of name
        return newUnit


    def remove_unit(self, unit):
        if unit.isRemoved:
            # DEBUG
            # print "already removed"
            return
        unit.do(CallFuncS(self.remove_unit_common))

        for p in self.connectedClients.keys():
            d = self.connect_end_point(self.connectedClients[p])

            def c(ampProto):
                return ampProto.callRemote(RemoveUnit, pid=unit.pid, uid=unit.uid)
            d.addCallback(c)
            d.addErrback(err)
            reactor.callLater(10, d.cancel)

        

    def start_cpu(self,newUnit,owner,builder=None,researchF=None,upgradeFrom=None):
        #CPU related logic
        cpu = owner.idleCPUs.pop()
        
        timer = TransTimer(newUnit.buildTime, pos=cpu.position)

        if owner.pid == self.pid:
            action = timer.get_move_action()
            self.map.add(timer, z=TIMER_Z)
        else:
            action = Delay(newUnit.buildTime)
        cpu.action = action
        action += CallFunc(self.stop_cpu, cpu,owner)
        if builder: #building a building
            action += CallFunc(self.remove_unit,builder)
        elif researchF: #research
            action += CallFunc(self.finish_research, newUnit,owner,researchF)
        if owner.pid == self.pid:
            timer.do(action)
        else:
            self.do(action)

    def stop_cpu(self, cpu, owner):
        if owner.pid == self.pid:
            utils.play_sound("Clock_end.wav")
        owner.idleCPUs.append(cpu)

    def move_unit(self, dest, unit, pid):
        if issubclass(type(unit), Troop) and dest != unit.curVertex and dest.emptyTroopSlots and unit.isSelectable:
            
            path = self.map.get_path(unit.curVertex, dest, pid, unit)

            #check for firewall
            if not path:
                utils.play_sound("firewall.wav") 
                return

            #check for sinkhole
            sinkHoleIndex = -1
            for i in range(1,len(path)):
                vertID = path[i]
                vert = self.map.vertices[vertID]
                if vert.building != None and type(vert.building) == Sinkhole and type(unit) != EncryptedTroop and vert.building.pid != pid:
                    sinkHoleIndex = i
            if sinkHoleIndex != -1:
                dest = unit.curVertex
                t = path[:sinkHoleIndex]
                t.reverse()
                path = path[:sinkHoleIndex + 1] + t

            #set unit logical position
            unit.isSelectable = False
            unit.curVertex.remove_troop(unit)
            slot = dest.add_trans_troop(unit)
            unit.destVertex = dest
            if unit.pid == self.pid:
                self.dispatch_event("click_on_move", unit.__class__.__name__, dest.vid)

            #dispatch to client
            for p in self.connectedClients.keys():
                d = self.connect_end_point(self.connectedClients[p])

                def c(ampProto):
                    return ampProto.callRemote(MoveTroop, pid=pid, uid=unit.uid, vid=-1, path=path)
                d.addCallback(c)
                d.addErrback(err)
                reactor.callLater(10, d.cancel)

            # first vertex
            if pid == self.pid:
                utils.play_sound("Move.wav")
                action = CallFuncS(self.cm.remove_tricky)
                action += MoveTo(unit.curVertex.position, 0.2)
            else:
                action = MoveTo(unit.curVertex.position, 0.2)

            # intermediate vertices
            for i in range(1, len(path)):
                vertex = self.map.vertices[path[i]]
                action += MoveTo(vertex.position, 1 / unit.speed)
                action += CallFuncS(self.update_location, vertex.position, pid, vertex)
                if i == sinkHoleIndex:
                    action += CallFunc(utils.play_sound, "Sinkhole.wav")
                    action += CallFunc(unit.on_attack,math.ceil(unit.health/3.0),vertex.building)
                    action += Delay(1)

            # final position
            if type(dest.building) != RSA or type(unit) == EncryptedTroop or dest.building.pid != unit.pid:
                action += MoveTo(slot.position, 0.2)
                action += CallFuncS(self.update_location, slot.position, pid)
            else:
                action += CallFuncS(self.upgrade_unit,"EncryptedTroop") 
            action += CallFuncS(self.cm.add)
            unit.do(action)
            return path
        return []

    def update_location(self, unit, position, pid, vertex=None):
        if vertex:  # no vertex if moving into slot
            unit.curVertex = vertex
            if vertex.vid == unit.destVertex.vid:  # if same, use set_trans_troop instead
                vertex.set_trans_troop(unit)
            self.client_update_location(unit.uid, vertex.vid, pid)
        else:
            unit.position = position
            unit.cshape.center = position
            unit.isSelectable = True

    def perform_research(self,researchName,owner,researchFactory):
        if owner.idleCPUs:
            if owner.pid == self.pid:
                utils.play_sound("Clock.wav") 
            researchType = RESEARCH[researchName]
            researchType.on_start(owner)
            self.start_cpu(researchType, owner, researchF=researchFactory)
            return True
        return False

        

    '''
    Twisted client methods
    '''

    # connect to client
    def connect_end_point(self, ip):
        from twisted.internet import reactor
        endpoint = TCP4ClientEndpoint(reactor, ip, 8750)
        factory = ServerNoteFactory()
        return endpoint.connect(factory)

    def client_attack(self,tpid,tuid,val):
        for client_pid in self.connectedClients.keys():
            d = self.connect_end_point(self.connectedClients[client_pid])

            def c(ampProto):
                return ampProto.callRemote(Attack, tpid=tpid, tuid=tuid, val=val)
            d.addCallback(c)
            d.addErrback(err)
            reactor.callLater(10, d.cancel)

    def client_attack_animation(self,pid,uid,tpid,tuid,path):
        for client_pid in self.connectedClients.keys():
            d = self.connect_end_point(self.connectedClients[client_pid])

            def c(ampProto):
                return ampProto.callRemote(AttackAnimation, pid=pid, uid=uid, tpid=tpid,tuid=tuid,path=path)
            d.addCallback(c)
            d.addErrback(err)
            reactor.callLater(10, d.cancel)

    def client_update_health(self, uid, health, pid):
        for client_pid in self.connectedClients.keys():
            d = self.connect_end_point(self.connectedClients[client_pid])

            def c(ampProto):
                if uid in self.players[pid].underConstruction.keys():
                    u = self.players[pid].underConstruction[uid]
                else:
                    u = self.players[pid].units[uid]
                return ampProto.callRemote(UpdateHealth, pid=pid, uid=uid, h=health,tid=u.tid,vid=u.curVertex.vid)
            d.addCallback(c)
            d.addErrback(err)
            reactor.callLater(10, d.cancel)

    def client_update_location(self, uid, vid, pid):
        for p in self.connectedClients.keys():
            d = self.connect_end_point(self.connectedClients[p])

            def c(ampProto):
                return ampProto.callRemote(UpdateLocation, pid=pid, uid=uid, vid=vid)
            d.addCallback(c)
            d.addErrback(err)
            reactor.callLater(10, d.cancel)

    def client_add_player(self, newpid):
        for pid in self.connectedClients.keys():
            d = self.connect_end_point(self.connectedClients[pid])

            def c(ampProto):
                return ampProto.callRemote(AddPlayer, pid=newpid)
            d.addCallback(c)
            d.addErrback(err)
            reactor.callLater(10, d.cancel)

    def client_start_game(self):
        for pid in self.connectedClients.keys():
            d = self.connect_end_point(self.connectedClients[pid])
            def c(ampProto):
                return ampProto.callRemote(StartGame)
            d.addCallback(c)
            d.addErrback(err)
            reactor.callLater(10, d.cancel)

    '''
    helper methods
    '''

    def _move_selected_units(self, dest):
        for unit in self.selectedUnits:
            self.move_unit(dest, unit, self.pid)
        self._deselect_all_units()
