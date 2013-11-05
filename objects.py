class Objects:
    server = None
    client = None

    @classmethod
    def get_server(cls,m):
        if not cls.server:
            from serverController import ServerController
            cls.server = ServerController(m)
        return cls.server

    @classmethod
    def get_client(cls):
        if not cls.client:
            from clientController import ClientController
            cls.client = ClientController(None)
        return cls.client

    @classmethod
    def get_controller(cls): #agnostic to client or controller
        if cls.server:
            return cls.server
        if cls.client:
            return cls.client
        return None

    @classmethod
    def reset_game(cls):
        del cls.server
        del cls.client
        cls.server = None
        cls.client = None
