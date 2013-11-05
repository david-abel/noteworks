'''
List of amp commands
'''
from twisted.protocols import amp

#client -> server
class Connect(amp.Command):
    arguments = [('ip',amp.String())]
    response = [('id',amp.Integer()),('cur',amp.ListOf(amp.Integer())),('map',amp.String())] 
    #-1 means not available,cur is list of current players

class StartGame(amp.Command):
    pass

class AddPlayer(amp.Command):
    arguments = [('pid',amp.Integer())]

#both
class BuildUnit(amp.Command):
    arguments = [('pid',amp.Integer()),('tid',amp.String()),('vid',amp.String()),('uid',amp.Integer()),('buid',amp.Integer())]
    #bUid is uid of the builder
    

class RemoveUnit(amp.Command):
    arguments = [('pid',amp.Integer()),('uid',amp.Integer())]
    
#server -> client
class UpdateHealth(amp.Command):
    # update unit health based on build status, attack status etc...
    arguments = [('pid',amp.Integer()),('uid',amp.Integer()),('h',amp.Integer()),('tid',amp.String()),('vid',amp.String())]

#both
class MoveTroop(amp.Command):
    arguments = [('pid',amp.Integer()),('uid',amp.Integer()),('vid',amp.Integer()),('path',amp.ListOf(amp.Integer()))] #can't move to core

#server -> client
class UpdateLocation(amp.Command):
    arguments = [('pid',amp.Integer()),('uid',amp.Integer()),('vid',amp.Integer())]
    #uid of unit, id of vertex

class Attack(amp.Command):
    arguments = [('tpid',amp.Integer()),('tuid',amp.Integer()),('val',amp.Integer())]

class AttackAnimation(amp.Command): #if no path, stop
    arguments = [('pid',amp.Integer()),('uid',amp.Integer()),('tpid',amp.Integer()),('tuid',amp.Integer()),('path',amp.ListOf(amp.String()))] #can't move to core

