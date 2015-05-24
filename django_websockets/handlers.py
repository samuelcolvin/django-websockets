import logging
from operator import attrgetter
from itertools import filterfalse
import time

import tornado.websocket

from .tokens import check_token_get_user
from . import settings

logger = logging.getLogger(settings.LOGGER_NAME)


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
        return iter(self._clients)

    @property
    def auth_clients(self):
        """
        Clients who are authenticated, eg. handlers with a user
        :return: client iterator
        """
        return filter(attrgetter('user'), self._clients)

    @property
    def anon_clients(self):
        """
        Clients who are anonymous, eg. handlers with no user
        :return: client iterator
        """
        return filterfalse(attrgetter('user'), self._clients)

# singleton containing list of all clients/handlers connected to this server.
all_clients = AllClients()


class AnonSocketHandler(tornado.websocket.WebSocketHandler):
    """
    Child of tornado.websocket.WebSocketHandler, makes the following changes:
    * allow cross origin requests if DEBUG is true so dev separate servers can be used to run django and tornado ws.
    * store all handlers in HANDLERS to allow easy communication between different websockets.
    """
    # user is never used in this class, it's included here for easy filtering of HANDLERS based on
    # whether they are authenticated eg
    user = None

    def select_subprotocol(self, subprotocols):
        logger.debug('subprotocols: %r', subprotocols)
        if subprotocols:
            # this is required to accept connection from authenticated users where the auth token
            # is supplied as a subprotool, see below
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
        logger.debug('new connection')
        all_clients.append(self)

    def on_close(self):
        logger.debug('client disconnected, close code: %r, close reason: %r', self.close_code, self.close_reason)
        all_clients.remove(self)


class AuthSocketHandler(AnonSocketHandler):
    """
    Child of AnonSocketHandler and therefore tornado.websocket.WebSocketHandler which authenticates
    the client via a token passed via a subprotocol.
    """

    def select_subprotocol(self, subprotocols):
        logger.debug('subprotocols: %r', subprotocols)
        if len(subprotocols) != 1:
            self.close(1002, 'exactly one sub-protocol should be provided')
            return
        token = subprotocols[0]
        if token in {'', 'null'}:
            # TODO, is there a better code to use?
            self.close(2000, 'permission denied - no token supplied')
            return
        # we have to do this as self.request is pretty flaky about giving up it's attributes
        # TODO fix or submit issue to tornado
        request_dict = vars(self.request)
        ip_address = request_dict['remote_ip']
        user = check_token_get_user(ip_address, token)
        if not user:
            self.close(2001, 'permission denied - invalid token')
            return
        logger.debug('new connection from %s at %s' % (user, ip_address))
        self.user = user
        return token


class PingPongMixin(object):
    """
    Mixin to check ping --> pong time on a websocket connection.

    Override pong_time_handler to do something with the time found (in ms).
    """
    def ping_timer(self):
        t = bytes(str(time.time()), 'ascii')
        self.ping(t)

    def on_pong(self, data):
        response_time = (time.time() - float(data)) * 1000
        self.pong_time_handler(response_time)

    def pong_time_handler(self, response_time):
        logger.info('ping pong: %0.2fms' % response_time)


class AnonEchoHandler(PingPongMixin, AnonSocketHandler):
    def open(self):
        super(AnonEchoHandler, self).open()
        self.ping_timer()

    def on_message(self, data):
        logger.info('received message: %r' % data)
        self.write_message(data)

