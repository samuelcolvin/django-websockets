from django_websockets.handlers import AnonSocketHandler, AuthSocketHandler, PingPongMixin, all_clients


class WsBase(PingPongMixin):
    def open(self):
        super(WsBase, self).open()
        self.ping_timer()
        self.safe_write_message('Clients Connected: %s' % all_clients.status)
        self.broadcast('new user connected: %s' % self.user)

    def pong_time_handler(self, response_time):
        self.safe_write_message('ping pong time: %0.2fms' % response_time)

    def on_message(self, data):
        if data == 'pingpong':
            self.ping_timer()
        elif data == 'clients':
            self.safe_write_message('Clients Connected: %s' % all_clients.status)
        else:
            if any(ord(x) > 255 for x in data[:50]):
                msg = 'binary data length %d' % len(data)
            else:
                msg = data
            self.broadcast('%s: %s' % (self.user or 'anon', msg))

    def broadcast(self, msg):
        for cli in all_clients:
            cli.safe_write_message(msg)


class AnonEchoHandler(WsBase, AnonSocketHandler):
    def open(self):
        self.user = 'anon %s' % str(hash(self))[-7:]
        super(AnonEchoHandler, self).open()


class AuthEchoHandler(WsBase, AuthSocketHandler):
    pass
