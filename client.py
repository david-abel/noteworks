from commands import *
from twisted.internet.protocol import Factory
from twisted.protocols.amp import AMP
from objects import Objects
from constants import UNIT_STARTING_OPACITY
import math


class ServerNote(AMP):  # client responses to server
    def __init__(self):
        super(ServerNote, self).__init__(self)

    @StartGame.responder
    def server_start_game(self):
        '''
        The client stub that gets called when the server starts the game
        '''
        client = Objects.get_client()
        client._init_players()
        client.start_game()
        return {}

    @AddPlayer.responder
    def server_add_player(self, pid):
        # print "server add player"
        client = Objects.get_client()
        client.playerList.append(pid)
        return {}

    @UpdateHealth.responder
    def server_update_health(self, pid, uid, h, tid,vid):
        # print "update_health", pid, uid, h
        client = Objects.get_client()
        player = client.players[pid]
        if uid not in player.underConstruction.keys():
            unit = client.build_unit(tid,player,vid=vid,uid=uid)
        else:
            unit = player.underConstruction[uid]
        unit.health = h
        client._complete_build(unit, player, uid)
        return {}

    @UpdateLocation.responder
    def server_update_location(self, pid, uid, vid):
        client = Objects.get_client()
        p = client.players[pid]
        curVertex = client.map.vertices[str(vid)]
        client.update_location(p.units[uid], curVertex.position, curVertex)
        return {}

    @BuildUnit.responder
    def server_build_unit(self, pid, tid, vid, uid,buid):        
        # print "building unit", pid, tid, vid, uid
        client = Objects.get_client()
        player = client.players[pid]
        if uid not in player.underConstruction.keys():
            client.build_unit(tid, player, vid=vid, uid=uid)
        return {}

    @MoveTroop.responder
    def server_move_troop(self, pid, uid, vid, path):
        # print "server move unit", pid, vid, uid, path
        client = Objects.get_client()
        path = client.move_unit(client.players[pid].units[uid], path)
        return {}

    @RemoveUnit.responder
    def client_remove_unit(self,pid,uid):
        # print "remove unit", pid, uid
        client = Objects.get_client()
        unit = client.players[pid].units[uid]
        unit.destroy_action()
        return {}

    @Attack.responder
    def server_on_attack(self,tpid,tuid,val):
        # print "server_on_attack", tpid,tuid,val
        client = Objects.get_client()
        p = client.players[tpid]
        if tuid in p.units.keys():
            p.units[tuid].client_on_attack(val)
        return {}


    @AttackAnimation.responder
    def server_animate_attack(self,pid,uid,tpid,tuid,path):
        #if no path, stop attacking
        # print "server_animate_attack",pid,uid, tpid,tuid,path
        client = Objects.get_client()

        if (uid in client.players[pid].units.keys()):
            attacker = client.players[pid].units[uid]
            if tpid == -1 or tuid == -1:
                attacker.end_attack(True)
            elif path:
                target = client.players[tpid].units[tuid]
                attacker.attackingPath = path
                if not attacker.is_attacking:
                    attacker.client_attack(target,client.map)
        return {}


class ServerNoteFactory(Factory):
    protocol = ServerNote


# send:
# user attack
# user research
# user move
# user construction
# user unit special ability
# join request

# receive, do and send
# location update in move
# end of move
# attack progress
# destruction of unit
# construction progress
# construction completion
# research progress
# research completion
