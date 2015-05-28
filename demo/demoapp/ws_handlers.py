from django_websockets.handlers import AnonSocketHandler, AuthSocketHandler
from tornado.websocket import WebSocketHandler


class AnonEchoHandler(WebSocketHandler):
    def on_message(self, data):
        self.write_message(data)


class AuthEchoHandler(AuthSocketHandler):
    def on_message(self, data):
        self.write_message(data)
