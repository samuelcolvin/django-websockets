import logging
import json
from pprint import pprint
import time
import datetime
from django_websockets.tokens import check_token_get_user
import tornado.websocket

from . import settings

ACTIONS = {
    'join': 'join_conversation',
    'msg': 'new_message'
}

handlers = []

logger = logging.getLogger(settings.LOGGER_NAME)


class SocketHandler(tornado.websocket.WebSocketHandler):
    user = None

    def check_origin(self, origin):
        return True

    def select_subprotocol(self, subprotocols):
        logger.info('subprotocols: %r', subprotocols)
        if len(subprotocols) != 1:
            self.close(1002, 'exactly one sub-protocol should be provided')
            return
        token = subprotocols[0]
        if token in {'', 'null'}:
            self.close(2000, 'permission denied - no token supplied')
            return
        request_dict = vars(self.request)
        ip = request_dict['remote_ip']
        user = check_token_get_user(ip, token)
        if not user:
            self.close(2001, 'permission denied - invalid token')
            return
        self.user = user
        return token

    def open(self):
        logger.info('new connection')

    def on_close(self):
        logger.info('client disconnected, close code: %r, close reason: %r', self.close_code, self.close_reason)
        try:
            handlers.remove(self)
        except ValueError:
            pass

    def on_message(self, data):
        logger.info(data)
        self.ping_timer()

    def ping_timer(self):
        t = bytes(str(time.time()), 'ascii')
        self.ping(t)

    def on_pong(self, data):
        response_time = time.time() - float(data)
        logger.info('ping time: %0.2fms' % (response_time * 1000))
