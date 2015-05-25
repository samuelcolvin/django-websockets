import logging
from functools import partial

from tornado.web import Application
from tornado.testing import AsyncHTTPTestCase
from tornado.websocket import WebSocketHandler

from django.test import TestCase
from django.contrib.auth.models import User

from django_websockets.handlers import AnonSocketHandler, all_clients
from .utils import WebSocketClient

logger = logging.getLogger('test_logger')


class TestAnonSocketHandler(AnonSocketHandler):
    def on_message(self, message):
        self.write_message(message)


class SimpleWebSocketTest(AsyncHTTPTestCase, TestCase):
    def get_app(self):
        return Application([('/', TestAnonSocketHandler)])

    def test_basic_echo(self):
        self.assertEqual(User.objects.count(), 0)
        self_test_case = self

        class WSClient(WebSocketClient):
            def on_open(self):
                self.write_message('hello')

            def on_message(self, data):
                self_test_case.assertEquals(data, 'hello')
                self_test_case.assertEqual(len(all_clients.all_clients), 1)
                self_test_case.assertEqual(len(all_clients.anon_clients), 1)
                self_test_case.assertEqual(len(all_clients.auth_clients), 0)
                self.close()

            def on_close(self):
                self_test_case.io_loop.add_callback(self_test_case.stop)

        self.io_loop.add_callback(partial(WSClient, self.get_url('/'), self.io_loop))
        self.wait()
        self_test_case.assertEqual(len(all_clients.all_clients), 0)
        self_test_case.assertEqual(len(all_clients.anon_clients), 0)
        self_test_case.assertEqual(len(all_clients.auth_clients), 0)

    # def test_basic_echo2(self):
    #     self.assertEqual(User.objects.count(), 0)
