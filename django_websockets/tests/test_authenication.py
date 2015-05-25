import logging
from django_websockets.tokens import make_token
from functools import partial

from tornado.web import Application
from tornado.testing import AsyncHTTPTestCase
from tornado.websocket import WebSocketHandler

from django.test import TestCase
from django.contrib.auth.models import User

from django_websockets.handlers import AnonEchoHandler, all_clients, AuthEchoHandler
from .utils import WebSocketClient, AsyncHTTPTestCaseExtra

logger = logging.getLogger('test_logger')


class AnonHandlerWebSocketTest(AsyncHTTPTestCaseExtra, TestCase):
    def get_app(self):
        return Application([('/', AnonEchoHandler)])

    def test_anon_echo(self):
        """
        anonymous user connecting to anon socket
        """
        self.assertEqual(User.objects.count(), 0)
        # flag to check the connection was closed for the right reason
        # (or at least we got to the correct close statement)
        self.ws_close_properly = False
        test_case = self

        class WSClient(WebSocketClient):
            def on_open(self):
                self.write_message('hello')

            def on_message(self, data):
                test_case.delayed_assertions.extend([
                    (data, 'hello'),
                    (len(all_clients.all_clients), 1),
                    (len(all_clients.anon_clients), 1),
                    (len(all_clients.auth_clients), 0),
                ])
                test_case.ws_close_properly = True
                self.close()

            def on_close(self, code=None, reason=None):
                test_case.io_loop.add_callback(test_case.stop)

        self.io_loop.add_callback(partial(WSClient, self.get_url('/'), self.io_loop, 'anon'))
        self.wait()
        self.assertTrue(self.ws_close_properly, 'websocket not closed properly')
        test_case.assertEqual(len(all_clients.all_clients), 0)
        test_case.assertEqual(len(all_clients.anon_clients), 0)
        test_case.assertEqual(len(all_clients.auth_clients), 0)

    def test_auth_echo(self):
        """
        authenticated user connecting to anon socket
        """
        self.assertEqual(User.objects.count(), 0)
        self.ws_close_properly = False
        test_case = self

        class WSClient(WebSocketClient):
            def on_open(self):
                self.write_message('hello')

            def on_message(self, data):
                # client is anon because an authenticated user connected to an anon handler
                test_case.delayed_assertions.extend([
                    (data, 'hello'),
                    (len(all_clients.all_clients), 1),
                    (len(all_clients.anon_clients), 1),
                    (len(all_clients.auth_clients), 0),
                ])
                test_case.ws_close_properly = True
                self.close()

            def on_close(self, code=None, reason=None):
                test_case.io_loop.add_callback(test_case.stop)

        user = User.objects.create_user('testing', email='testing@example.com')
        token = make_token(user, '127.0.0.1')
        self.io_loop.add_callback(partial(WSClient, self.get_url('/'), self.io_loop, token))
        self.wait()
        self.assertTrue(self.ws_close_properly, 'websocket not closed properly')
        test_case.assertEqual(len(all_clients.all_clients), 0)
        test_case.assertEqual(len(all_clients.anon_clients), 0)
        test_case.assertEqual(len(all_clients.auth_clients), 0)


class AuthHandlerWebSocketTest(AsyncHTTPTestCaseExtra, TestCase):
    def get_app(self):
        return Application([('/', AuthEchoHandler)])

    def test_anon_client(self):
        """
        anonymous user connecting to auth socket, should be permission denied
        """
        self.assertEqual(User.objects.count(), 0)
        test_case = self

        class WSClient(WebSocketClient):
            def on_open(self):
                self.write_message('hello')

            def on_close(self, code=None, reason=None):
                test_case.delayed_assertions.extend([
                    (code, 2001),
                    (reason, 'permission denied - anonymous users not permitted to connect to this socket'),
                    (len(all_clients.all_clients), 0),
                    (len(all_clients.anon_clients), 0),
                    (len(all_clients.auth_clients), 0),
                ])
                test_case.io_loop.add_callback(test_case.stop)

        self.io_loop.add_callback(partial(WSClient, self.get_url('/'), self.io_loop, 'anon'))
        self.wait()
        test_case.assertEqual(len(all_clients.all_clients), 0)
        test_case.assertEqual(len(all_clients.anon_clients), 0)
        test_case.assertEqual(len(all_clients.auth_clients), 0)

    def test_bad_client(self):
        """
        client with bad token connecting to auth socket, should be permission denied
        """
        self.assertEqual(User.objects.count(), 0)
        test_case = self

        class WSClient(WebSocketClient):
            def on_open(self):
                self.write_message('hello')

            def on_close(self, code=None, reason=None):
                test_case.delayed_assertions.extend([
                    (code, 2002),
                    (reason, 'permission denied - invalid token'),
                    (len(all_clients.all_clients), 0),
                    (len(all_clients.anon_clients), 0),
                    (len(all_clients.auth_clients), 0),
                ])
                test_case.io_loop.add_callback(test_case.stop)

        self.io_loop.add_callback(partial(WSClient, self.get_url('/'), self.io_loop, 'this is bad!'))
        self.wait()
        test_case.assertEqual(len(all_clients.all_clients), 0)
        test_case.assertEqual(len(all_clients.anon_clients), 0)
        test_case.assertEqual(len(all_clients.auth_clients), 0)

    def test_auth_echo(self):
        """
        authenticated user connecting to anon socket
        """
        self.assertEqual(User.objects.count(), 0)
        self.ws_close_properly = False
        test_case = self

        class WSClient(WebSocketClient):
            def on_open(self):
                self.write_message('hello')

            def on_message(self, data):
                # client is anon because an authenticated user connected to an anon handler
                test_case.delayed_assertions.extend([
                    (data, 'hello'),
                    (len(all_clients.all_clients), 1),
                    (len(all_clients.anon_clients), 0),
                    (len(all_clients.auth_clients), 1),
                ])
                test_case.ws_close_properly = True
                self.close()

            def on_close(self, code=None, reason=None):
                test_case.delayed_assertions.extend([
                    (code, None),
                    (reason, None),
                ])
                test_case.io_loop.add_callback(test_case.stop)

        user = User.objects.create_user('testing', email='testing@example.com')
        token = make_token(user, '127.0.0.1')
        self.io_loop.add_callback(partial(WSClient, self.get_url('/'), self.io_loop, token))
        self.wait()
        self.assertTrue(self.ws_close_properly, 'websocket not closed properly')
        test_case.assertEqual(len(all_clients.all_clients), 0)
        test_case.assertEqual(len(all_clients.anon_clients), 0)
        test_case.assertEqual(len(all_clients.auth_clients), 0)
