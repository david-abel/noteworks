from cocos.scene import Scene
from cocos.layer import ColorLayer

from twisted.internet import reactor

import server

class Game(ColorLayer):
    is_event_handler=True
    
    def __init__(self,*args,**kwargs):
        super(Game,self).__init__(*args,**kwargs)
        self.server=server.Server(reactor,8007)
        #Ask for updates
        self.schedule(self.update)
        self.players = [] # array of players
    
    def on_enter(self,*args,**kwargs):
        self.server.start_hosting()
        super(Game,self).on_enter(*args,**kwargs)
        
    def on_exit(self,*args,**kwargs):
        self.server.stop_hosting()
        super(Game,self).on_exit(*args,**kwargs)
    
    def update(self,dt):
        pass
  
def get_game_scene():
    return Scene(Game( 255, 0,255,255, width=400, height=400))
