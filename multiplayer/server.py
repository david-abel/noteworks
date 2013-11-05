from twisted.internet.protocol import Factory
from twisted.protocols import basic
from twisted.internet.endpoints import TCP4ServerEndpoint


class QOTD(basic.LineReceiver):
    'dummy Protocol, that will send a quote and disconnect the client'
    
    def __init__(self, factory):
        self.factory = factory
    
    def connection_made(self):
        self.factory.clients.add(self)
        self.transport.write("Hello world\r\n") 
        #self.transport.loseConnection()

    def connection_lost(self, reason):
        self.factory.clients.remove(self)

    def line_received(self, line):
        for c in self.factory.clients:
            c.sendLine("<{}> {}".format(self.transport.getHost(), line))

class QOTDFactory(Factory):
    def __init__(self):
        self.clients = set()
        
    def close_connections(self):
        'disconnects every client'
        for c in self.clients :
            c.transport.write("bye bye")
            c.transport.loseConnection()
            
    def buildProtocol(self, addr):
        return QOTD(self)

class Server(object):    
    def __init__(self,reactor,port=8007):
        self.endpoint = TCP4ServerEndpoint(reactor, port)
        self.factory = QOTDFactory()
        self.listening=None
        
    def start_hosting(self):
        '''starts hosting'''
        if not self.listening:
            deferred=self.endpoint.listen(self.factory)
            deferred.addCallback(self.is_listening)
        else :
            print 'already hosting'
            
    def stop_hosting(self):
        '''ends the hosting for now'''
        if self.listening:
            self.listening.stopListening()
            self.factory.close_connections()
            self.listening=None
            print 'stop listening'
        else : 
            print "wasn't listening anyway!"

    def is_listening(self,*args,**kwargs):
        '''server is really up and running
        this is called when start_hosting's deferred has really fired'''
        print 'hosting'
        self.listening=args[0]