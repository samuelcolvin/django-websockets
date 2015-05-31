from tornado.websocket import WebSocketClosedError
from django_websockets.handlers import AnonSocketHandler, AuthSocketHandler, PingPongMixin, all_clients


class WsBase(PingPongMixin):
    def open(self):
        super(WsBase, self).open()
        self.ping_timer()
        try:
            self.write_message('Clients Connected: %s' % all_clients.status)
            self.write_message('connection user: %s' % self.user)
        except WebSocketClosedError:
            # this happens on authenticated connection due to selecting subprotocol (I assume?)
            # we can safely ignore it
            pass

    def pong_time_handler(self, response_time):
        self.write_message('ping pong time: %0.2fms' % response_time)

    def on_message(self, data):
        if data == 'pingpong':
            self.ping_timer()
        elif data == 'clients':
            self.write_message('Clients Connected: %s' % all_clients.status)
        else:
            msg = 'msg from %s: %s' % (self.user, data)
            for cli in all_clients:
                if cli.ws_connection is not None:
                    cli.write_message(msg)


class AnonEchoHandler(WsBase, AnonSocketHandler):
    pass


class AuthEchoHandler(WsBase, AuthSocketHandler):
    pass
