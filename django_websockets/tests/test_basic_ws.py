"""
Test that utils.WebSocketClient and successfully connect to tornado and exchange messages.

No actual testing of django-websockets is performed here.
"""
import json
import logging
from functools import partial

from tornado.web import Application, RequestHandler
from tornado.testing import AsyncHTTPTestCase
from tornado.websocket import WebSocketHandler

from .utils import WebSocketClient


class EchoWebSocketHandler(WebSocketHandler):
    def on_message(self, message):
        self.write_message(message)


class SimpleHandler(RequestHandler):
    def get(self):
        self.write('hello'.encode('utf-8'))


class SimpleWebSocketTest(AsyncHTTPTestCase):
    def get_app(self):
        return Application([
            ('/', SimpleHandler),
            ('/ws/', EchoWebSocketHandler),
        ])

    def test_basic(self):
        response = self.fetch('/')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, b'hello')

    def test_basic_echo(self):
        self_test_case = self

        class WSClient(WebSocketClient):
            def on_open(self):
                self.write_message('hello')

            def on_message(self, data):
                self_test_case.assertEquals(data, 'hello')
                self_test_case.io_loop.add_callback(self_test_case.stop)

        self.io_loop.add_callback(partial(WSClient, self.get_url('/ws/'), self.io_loop))
        self.wait()


class GetSubprotocolSocketHandler(WebSocketHandler):
    """
    ws which responds the subprotocol it was called with as well as he message sent
    """
    subp = None

    def on_message(self, message):
        self.write_message(json.dumps({'message': message, 'subprotocol': self.subp}))

    def select_subprotocol(self, subprotocols):
        assert len(subprotocols) == 1
        self.subp = subprotocols[0]
        return self.subp


class SubprotocolWebSocketTest(AsyncHTTPTestCase):
    def get_app(self):
        return Application([('/', GetSubprotocolSocketHandler)])

    def test_no_subprotocol(self):
        self_test_case = self

        class WSClient(WebSocketClient):
            def on_open(self):
                self.write_message('testing')

            def on_message(self, data):
                self_test_case.assertEquals(json.loads(data), {'message': 'testing', 'subprotocol': ''})
                self_test_case.io_loop.add_callback(self_test_case.stop)

        self.io_loop.add_callback(partial(WSClient, self.get_url('/'), self.io_loop))
        self.wait()

    def test_with_subprotocol(self):
        self_test_case = self

        class WSClient(WebSocketClient):
            def on_open(self):
                self.write_message('testing')

            def on_message(self, data):
                self_test_case.assertEquals(json.loads(data), {'message': 'testing', 'subprotocol': 'sub-proto'})
                self_test_case.io_loop.add_callback(self_test_case.stop)

        self.io_loop.add_callback(partial(WSClient, self.get_url('/'), self.io_loop, 'sub-proto'))
        self.wait()


class BrokenSocketHandler(WebSocketHandler):
    def on_message(self, message):
        # technically this exception is required as all we're testing below is that stop isn't called
        # and therefore wait times out, just not echoing the message would have the same effect
        raise Exception('intentional test exception')
        self.write_message(message)


class ServerErrorWebSocketTest(AsyncHTTPTestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)
        super(ServerErrorWebSocketTest, self).setUp()

    def tearDown(self):
        super(ServerErrorWebSocketTest, self).tearDown()
        logging.disable(logging.NOTSET)

    def get_app(self):
        return Application([('/', BrokenSocketHandler)])

    def connect_to_server(self):
        self_test_case = self

        class WSClient(WebSocketClient):
            def on_open(self):
                self.write_message('testing')

            def on_message(self, data):
                self_test_case.io_loop.add_callback(self_test_case.stop)

        self.io_loop.add_callback(partial(WSClient, self.get_url('/'), self.io_loop))
        self.wait(timeout=0.01)

    def test_no_subprotocol(self):
        self.assertRaises(AssertionError, self.connect_to_server)
