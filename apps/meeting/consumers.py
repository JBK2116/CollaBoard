import json
from channels.generic.websocket import WebsocketConsumer 

class ChatConsumer(WebsocketConsumer):
    def connect(self) -> None:
        self.accept()

    def disconnect(self, code: int) -> None:
        pass

    def receive(self, text_data: str | None = None, bytes_data: bytes | None = None) -> None:
        if text_data:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']

            self.send(text_data=json.dumps({
                'message': message
            }))