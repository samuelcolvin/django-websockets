import logging
from operator import attrgetter
from itertools import filterfalse
import time

import tornado.websocket

from .tokens import check_token_get_user
from . import settings

logger = logging.getLogger(settings.WS_LOGGER_NAME)


class AllClients(object):
    def __init__(self):
        self._clients = []

    def append(self, h):
        self._clients.append(h)

    def remove(self, h, lenient=False):
        try:
            self._clients.remove(h)
        except ValueError:
            if not lenient:
                raise

    @property
    def all_clients(self):
        """
        All handlers/clients connected, for consistency with properties
        below this is returned as an iterator.
        :return: client iterator
        """
        return self._clients

    @property
    def auth_clients(self):
        """
        Clients who are authenticated, eg. handlers with a user
        :return: list of clients
        """
        return list(filter(attrgetter('user'), self._clients))

    @property
    def anon_clients(self):
        """
        Clients who are anonymous, eg. handlers with no user
        :return: list of clients
        """
        return list(filterfalse(attrgetter('user'), self._clients))

    def __str__(self):
        return 'AllClients: %d auth, %d anon, %d total' % (len(self.auth_clients),
                                                           len(self.anon_clients),
                                                           len(self._clients))

# singleton containing list of all clients/handlers connected to this server.
all_clients = AllClients()


class AnonSocketHandler(tornado.websocket.WebSocketHandler):
    """
    Child of tornado.websocket.WebSocketHandler, makes the following changes:
    * allow cross origin requests if DEBUG is true so dev separate servers can be used to run django and tornado ws.
    * store all handlers in AllClients to allow easy communication between different websockets.
    """
    # user is never used in this class, it's included here for easy filtering of AllClients based on user value
    user = None
    _client_added = False
    _connection_allowed = True

    def select_subprotocol(self, subprotocols):
        logger.debug('subprotocols: %r', subprotocols)
        if subprotocols:
            # this is required to accept connection from authenticated users where the auth token
            # is supplied as a subprotocol, see below
            return subprotocols[0]

    def check_origin(self, origin):
        """
        Origin True is require when running separate dev servers since the port (and therefore domain)
        for http and ws are different.

        :return: True in DEBUG mode, else results from super
        """
        if settings.DEBUG:
            return True
        return super(AnonSocketHandler, self).check_origin(origin)

    def open(self):
        logger.debug('new connection, allowed: %r, client added: %r', self._connection_allowed, self._client_added)
        if self._connection_allowed:
            all_clients.append(self)
            self._client_added = True

    def close(self, code=None, reason=None):
        logger.debug('closing connection, close code: %r, close reason: %r', code, reason)
        return super(AnonSocketHandler, self).close(code, reason)

    def on_close(self):
        logger.debug('client disconnected, close code: %r, close reason: %r', self.close_code, self.close_reason)
        all_clients.remove(self, not self._client_added)


class AuthSocketHandler(AnonSocketHandler):
    """
    Child of AnonSocketHandler and therefore tornado.websocket.WebSocketHandler which authenticates
    the client via a token passed via a subprotocol.
    """
    _connection_allowed = False

    def select_subprotocol(self, subprotocols):
        logger.debug('subprotocols: %r', subprotocols)
        if len(subprotocols) != 1:
            self.close(1002, 'exactly one sub-protocol should be provided')
            return
        token = subprotocols[0]
        if token == '':
            # TODO, is there a better code to use?
            self.close(2000, 'permission denied - no token supplied')
            return
        if token in {'null', 'anon'}:
            # TODO, is there a better code to use?
            self.close(2001, 'permission denied - anonymous users not permitted to connect to this socket')
        # we have to do this as self.request is pretty flaky about giving up it's attributes
        # TODO fix or submit issue to tornado
        request_dict = vars(self.request)
        ip_address = request_dict['remote_ip']
        user = check_token_get_user(ip_address, token)
        if not user:
            self.close(2002, 'permission denied - invalid token')
            return
        logger.debug('new valid connection from %s at %s' % (user, ip_address))
        self.user = user
        self._connection_allowed = True
        return token


class PingPongMixin(object):
    """
    Mixin to check ping --> pong time on a websocket connection.

    Override pong_time_handler to do something with the time found (in ms).
    """
    def ping_timer(self):
        if not self.ws_connection or self.ws_connection.client_terminated:
            logger.warn('ws connection terminated, not checking ping time')
            return
        t = bytes(str(time.time()), 'ascii')
        self.ping(t)

    def on_pong(self, data):
        response_time = (time.time() - float(data)) * 1000
        self.pong_time_handler(response_time)

    def pong_time_handler(self, response_time):
        logger.info('ping pong: %0.2fms' % response_time)


class AnonEchoHandler(PingPongMixin, AnonSocketHandler):
    """
    simple echo handler with no authentication, provided for testing and to help initial setup
    """
    def open(self):
        super(AnonEchoHandler, self).open()
        self.ping_timer()

    def on_message(self, data):
        logger.info('received message: %r' % data)
        self.write_message(data)


class AuthEchoHandler(PingPongMixin, AuthSocketHandler):
    """
    simple echo handler with authentication, provided for testing and to help initial setup
    """
    def open(self):
        super(AuthEchoHandler, self).open()
        self.ping_timer()

    def on_message(self, data):
        logger.info('received message: %r' % data)
        self.write_message(data)


