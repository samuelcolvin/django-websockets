from django_websockets.handlers import AnonSocketHandler, AuthSocketHandler, PingPongMixin, all_clients


class WsBase(PingPongMixin):
    def open(self):
        super(WsBase, self).open()
        self.ping_timer()
        self.write_message('Clients Connected: %s' % all_clients.status)

    def pong_time_handler(self, response_time):
        self.write_message('ping pong time: %0.2fms' % response_time)

    def on_message(self, data):
        self.write_message('echo: %s' % data)


class AnonEchoHandler(WsBase, AnonSocketHandler):
    pass


class AuthEchoHandler(WsBase, AuthSocketHandler):
    pass
