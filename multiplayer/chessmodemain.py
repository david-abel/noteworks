import pygletreactor # to get it: http://code.google.com/p/pyglet-twisted/
pygletreactor.install() # <- this must come before...
from twisted.internet import reactor # <- ...importing this reactor!

import pyglet
from pyglet import font

from cocos.director import director

import chessmodemenu as menu

pyglet.resource.path.append('images')
pyglet.resource.reindex()
font.add_directory('fonts')

if __name__ == '__main__':
    
    director.init(width=800, height=600,vsync=False )
    director.set_show_FPS(True)

    ## code to make pygletreactor also work with cocos
    @director.window.event
    def on_close():
        print 'closing reactor'
        reactor.callFromThread(reactor.stop) #@UndefinedVariable     
        # Return true to ensure that no other handlers
        # on the stack receive the on_close event
        return True
    
    director.replace(menu.get_menu())

    ## Start the reactor
    
    reactor.run() #@UndefinedVariable