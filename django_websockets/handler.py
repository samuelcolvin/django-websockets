import logging
import json
import time
import datetime
import tornado.websocket

from chat.models import Message, Conversation

ACTIONS = {
    'join': 'join_conversation',
    'msg': 'new_message'
}

handlers = []

logger = logging.getLogger('websockets')

class SocketHandler(tornado.websocket.WebSocketHandler):
    con = None
    customer = None
    operator = None

    def check_origin(self, origin):
        return True

    def select_subprotocol(self, subprotocols):
        logger.debug('subprotocols: %r', subprotocols)

    def open(self):
        logger.info('new connection')

    def on_close(self):
        logger.info('client disconnected')
        handlers.remove(self)

    def on_message(self, data):
        logger.info(data)
        self.ping_timer()

    def ping_timer(self):
        t = bytes(str(time.time()), 'ascii')
        self.ping(t)

    def on_pong(self, data):
        response_time = time.time() - float(data)
        logger.info('ping time: %0.2fms' % (response_time * 1000))
