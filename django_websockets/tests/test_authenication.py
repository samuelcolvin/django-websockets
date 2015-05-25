import inspect
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

    def test_anon_echo(self):
        self.assertEqual(User.objects.count(), 0)
        # currently no way to know if the connection was caused to do an error or correct so use this flag
        self.ws_close_properly = False
        self.assertions = []
        self_test_case = self

        class WSClient(WebSocketClient):
            def on_open(self):
                self.write_message('hello')

            def on_message(self, data):
                self_test_case.assertions.extend([
                    (data, 'hello'),
                    (len(all_clients.all_clients), 1),
                    (len(all_clients.anon_clients), 1),
                    (len(all_clients.auth_clients), 0),
                ])
                self_test_case.ws_close_properly = True
                self.close()

            def on_close(self):
                self_test_case.io_loop.add_callback(self_test_case.stop)

        self.io_loop.add_callback(partial(WSClient, self.get_url('/'), self.io_loop))
        self.wait()
        self.assertTrue(self.ws_close_properly, 'websocket not closed properly')
        self.delayed_assertion_check()
        self_test_case.assertEqual(len(all_clients.all_clients), 0)
        self_test_case.assertEqual(len(all_clients.anon_clients), 0)
        self_test_case.assertEqual(len(all_clients.auth_clients), 0)

    def delayed_assertion_check(self):
        for i, args in enumerate(self.assertions):
            msg = 'delayed assertion error on assertion %i in %s' % (i + 1, inspect.stack()[1][3])
            if len(args) == 2:
                args += (msg,)
            elif len(args) == 3:
                args = (args[0], args[1], '%s: %s' % (msg, args[2]))
            self.assertEqual(*args)

    # def test_basic_echo2(self):
    #     self.assertEqual(User.objects.count(), 0)
