import datetime
import logging
from unittest.mock import patch
from functools import partial

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.http import base36_to_int, int_to_base36

from django_websockets.handlers import AnonEchoHandler, all_clients, AuthEchoHandler
from django_websockets.app import get_app
from django_websockets.tokens import make_token, check_token_get_user
from django_websockets import settings
from .utils import WebSocketClient, AsyncHTTPTestCaseExtra

logger = logging.getLogger('test_logger')


class LowLevelAuthTestCase(TestCase):
    ip = '127.0.0.1'

    def test_null_token(self):
        self.assertFalse(check_token_get_user('null', self.ip))

    def test_valid_token(self):
        user = User.objects.create_user('testing', email='testing@example.com')
        token = make_token(user, self.ip)
        self.assertEqual(check_token_get_user(token, self.ip), user)

    def test_invalid_time_stamp_token(self):
        user = User.objects.create_user('testing', email='testing@example.com')
        token = make_token(user, self.ip)
        secs, uid, hash = token.split('-')
        new_secs = base36_to_int(secs) - 10
        new_secs = int_to_base36(new_secs)
        wrong_token = '%s-%s-%s' % (new_secs, uid, hash)
        self.assertFalse(check_token_get_user(wrong_token, self.ip))

    def test_invalid_user_token(self):
        user = User.objects.create_user('testing', email='testing@example.com')
        token = make_token(user, self.ip)
        secs, uid, hash = token.split('-')
        wrong_token = '%s-%s-%s' % (secs, int_to_base36(user.id + 42), hash)
        self.assertFalse(check_token_get_user(wrong_token, self.ip))

    def test_invalid_base64_token(self):
        user = User.objects.create_user('testing', email='testing@example.com')
        token = make_token(user, self.ip)
        secs, uid, hash = token.split('-')
        wrong_token = '%s-%s-%s' % (secs, '@;[]_+.', hash)
        self.assertFalse(check_token_get_user(wrong_token, self.ip))

    def test_ip_change_token(self):
        user = User.objects.create_user('testing', email='testing@example.com')
        token = make_token(user, self.ip)
        self.assertFalse(check_token_get_user(token, '127.0.0.2'))

    @patch('django_websockets.tokens._now')
    def test_expired_token(self, now_func):
        n = datetime.datetime.now()
        now_func.side_effect = [n, n + datetime.timedelta(seconds=settings.TOKEN_VALIDITY_SECONDS + 60)]

        user = User.objects.create_user('testing', email='testing@example.com')
        token = make_token(user, self.ip)
        self.assertFalse(check_token_get_user(token, self.ip))

    @patch('django_websockets.tokens._now')
    def test_nearly_expired_token(self, now_func):
        n = datetime.datetime.now()
        now_func.side_effect = [n, n + datetime.timedelta(seconds=settings.TOKEN_VALIDITY_SECONDS - 60)]

        user = User.objects.create_user('testing', email='testing@example.com')
        token = make_token(user, self.ip)
        self.assertEqual(check_token_get_user(token, self.ip), user)


class AnonHandlerWebSocketTest(AsyncHTTPTestCaseExtra, TestCase):
    def get_app(self):
        return get_app(False, [('/', AnonEchoHandler)])

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

        self.io_loop.add_callback(partial(WSClient, self.get_url('/ws/'), self.io_loop, 'anon'))
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
                    (str(all_clients), 'AllClients: 0 auth, 1 anon, 1 total')
                ])
                test_case.ws_close_properly = True
                self.close()

            def on_close(self, code=None, reason=None):
                test_case.io_loop.add_callback(test_case.stop)

        user = User.objects.create_user('testing', email='testing@example.com')
        token = make_token(user, '127.0.0.1')
        self.io_loop.add_callback(partial(WSClient, self.get_url('/ws/'), self.io_loop, token))
        self.wait()
        self.assertTrue(self.ws_close_properly, 'websocket not closed properly')
        test_case.assertEqual(len(all_clients.all_clients), 0)
        test_case.assertEqual(len(all_clients.anon_clients), 0)
        test_case.assertEqual(len(all_clients.auth_clients), 0)


class AuthHandlerWebSocketTest(AsyncHTTPTestCaseExtra, TestCase):
    def get_app(self):
        return get_app(False, [('/', AuthEchoHandler)])

    def test_anon_client(self):
        """
        anonymous user connecting to auth socket, should be permission denied
        """
        self.assertEqual(User.objects.count(), 0)
        test_case = self

        class WSClient(WebSocketClient):
            def on_close(self, code=None, reason=None):
                test_case.delayed_assertions.extend([
                    (code, 2001),
                    (reason, 'permission denied - anonymous users not permitted to connect to this socket'),
                    (len(all_clients.all_clients), 0),
                    (len(all_clients.anon_clients), 0),
                    (len(all_clients.auth_clients), 0),
                ])
                test_case.io_loop.add_callback(test_case.stop)

        self.io_loop.add_callback(partial(WSClient, self.get_url('/ws/'), self.io_loop, 'anon'))
        self.wait()
        test_case.assertEqual(len(all_clients.all_clients), 0)
        test_case.assertEqual(len(all_clients.anon_clients), 0)
        test_case.assertEqual(len(all_clients.auth_clients), 0)

    def test_no_subprotocol_client(self):
        """
        anonymous user (no subprotocol) connecting to auth socket, should be permission denied
        """
        self.assertEqual(User.objects.count(), 0)
        test_case = self

        class WSClient(WebSocketClient):
            def on_close(self, code=None, reason=None):
                test_case.delayed_assertions.extend([
                    (code, 2000),
                    (reason, 'permission denied - no token supplied'),
                    (len(all_clients.all_clients), 0),
                    (len(all_clients.anon_clients), 0),
                    (len(all_clients.auth_clients), 0),
                ])
                test_case.io_loop.add_callback(test_case.stop)

        self.io_loop.add_callback(partial(WSClient, self.get_url('/ws/'), self.io_loop))
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
            def on_close(self, code=None, reason=None):
                test_case.delayed_assertions.extend([
                    (code, 2002),
                    (reason, 'permission denied - invalid token'),
                    (len(all_clients.all_clients), 0),
                    (len(all_clients.anon_clients), 0),
                    (len(all_clients.auth_clients), 0),
                ])
                test_case.io_loop.add_callback(test_case.stop)

        self.io_loop.add_callback(partial(WSClient, self.get_url('/ws/'), self.io_loop, 'this is bad!'))
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
        self.io_loop.add_callback(partial(WSClient, self.get_url('/ws/'), self.io_loop, token))
        self.wait()
        self.assertTrue(self.ws_close_properly, 'websocket not closed properly')
        test_case.assertEqual(len(all_clients.all_clients), 0)
        test_case.assertEqual(len(all_clients.anon_clients), 0)
        test_case.assertEqual(len(all_clients.auth_clients), 0)
