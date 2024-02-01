
class CustomWebSocket:
    def __init__(self, manager, websocket):
        self.manager = manager
        self.websocket = websocket
    
    def send(self, message):
        self.manager.send_personal_message(message, self.websocket)