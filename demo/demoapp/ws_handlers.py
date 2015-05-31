from django_websockets.handlers import AnonSocketHandler, AuthSocketHandler


class AnonEchoHandler(AnonSocketHandler):
    def on_message(self, data):
        self.write_message(data)


class AuthEchoHandler(AuthSocketHandler):
    def on_message(self, data):
        self.write_message(data)
