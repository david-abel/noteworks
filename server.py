from twisted.protocols.amp import AMP
from twisted.internet.protocol import Factory

from commands import *
from objects import Objects


class ClientNote(AMP):  # notes sent from client to server, server responses
    def __init__(self):
        super(ClientNote, self).__init__(self)

    @Connect.responder
    def client_connect(self, ip):
        server = Objects.get_controller()
        cur = server.playerList + [server.pid]
        print "connected client of ip: " + ip
        if ip in server.connectedClientsIP.keys():
            # print "client already exist"
            return {"id": server.connectedClientsIP[ip], "cur": cur,"map":server.mapName}
        if len(server.map.players) != 0 and (not server.gameStarted):
            pid = server.map.players.pop()
            server.client_add_player(pid)
            server.connectedClients[pid] = ip
            server.connectedClientsIP[ip] = pid
            server.playerList.append(pid)
            # print "added player",pid
            return {"id": pid, "cur": cur, "map":server.mapName}
        # print "can't add player"
        return {"id": -1, "cur": [],"map":""}

    @BuildUnit.responder
    def client_build_unit(self,pid,tid,vid,uid,buid):
        # print "client",pid, "built unit", tid, "on", vid
        server = Objects.get_controller()
        p = server.players[pid]
        if buid != -1:
            server.build_unit(tid,p,vid=vid,builder=p.units[buid])
        else:
            server.build_unit(tid,p,vid=vid)
        return {}

    @MoveTroop.responder
    def client_move_troop(self,pid,uid,vid,path):
        # print "client",pid, "move unit", uid, "on", vid
        server = Objects.get_controller()
        server.move_unit(server.map.vertices[str(vid)],server.players[pid].units[uid],pid)
        return {}

    @RemoveUnit.responder
    def client_remove_unit(self,pid,uid):
        # print "client",pid, "remove unit", uid
        server = Objects.get_controller()
        unit = server.players[pid].units[uid]
        server.remove_unit(unit)
        return {}

    @AttackAnimation.responder
    def client_attack_unit(self,pid,uid,tpid,tuid,path):
        # print "client_attack_unit",pid,uid,tpid,tuid
        #if tuid=-1, it's a vertex,tpid is actually tvid
        server = Objects.get_controller()
        attacker = server.players[pid].units[uid]
        if tuid == -1:
            target = server.map.vertices[str(tpid)]
        else:
            target = server.players[tpid].units[tuid]
        server.attack_unit(target,attacker)
        return {}

class ClientNoteFactory(Factory):
    protocol = ClientNote




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
