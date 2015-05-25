import logging
from unittest.mock import patch
import io

from django.test import TestCase
from django.core.management import call_command

from django_websockets import settings

# we have to import this now to avoid it message with loggers during tests
import django_websockets.tests.wsgi
from .utils import CaptureStd


class ManagementCommandTestCase(TestCase):
    def setUp(self):
        super(ManagementCommandTestCase, self).setUp()
        self.logger = logging.getLogger(settings.WS_LOGGER_NAME)
        self.logger.setLevel(logging.DEBUG)
        # self.logger.propagate = False
        self.stream = io.StringIO()
        self.handler = logging.StreamHandler(self.stream)
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)
        self.logger.addHandler(self.handler)

    def tearDown(self):
        super(ManagementCommandTestCase, self).tearDown()
        self.logger.removeHandler(self.handler)
        self.handler.close()

    @patch('django_websockets.management.commands.websockets._start_server')
    def test_cmd_vanilla(self, man_start_server):
        with CaptureStd() as std:
            call_command('websockets')
        self.assertTrue(man_start_server.called)
        # avoid messing with versions by only checking beginning and end
        self.assertTrue(std.captured.startswith('\ndjango-websockets version'))
        self.assertIn('"django_websockets.testsettings"\nStarting server on port 8000\n', std.captured)

        logs = self.stream.getvalue()
        self.assertEqual(logs, 'Creating tornado application, with the 2 handlers:\n'
                               '  "/ws/" > django_websockets.handlers.AnonEchoHandler\n'
                               '  ".*" > tornado.web.FallbackHandler\n')

    @patch('django_websockets.management.commands.websockets._start_server')
    def test_cmd_nodjango(self, man_start_server):
        with CaptureStd() as std:
            call_command('websockets', '--nodjango')
            self.assertTrue(man_start_server.called)
        self.assertTrue(std.captured.startswith('\ndjango-websockets version'))
        self.assertIn('"django_websockets.testsettings"\nStarting server on port 8001\n', std.captured)

        logs = self.stream.getvalue()
        self.assertEqual(logs, 'Creating tornado application, with the 1 handler:\n'
                               '  "/ws/" > django_websockets.handlers.AnonEchoHandler\n')

    @patch('django_websockets.management.commands.websockets._start_server')
    def test_cmd_different_port(self, man_start_server):
        with CaptureStd() as std:
            call_command('websockets', '--port', '9876')
        self.assertTrue(man_start_server.called)
        # avoid messing with versions by only checking beginning and end
        self.assertTrue(std.captured.startswith('\ndjango-websockets version'))
        self.assertIn('"django_websockets.testsettings"\nStarting server on port 9876\n', std.captured)

        logs = self.stream.getvalue()
        self.assertEqual(logs, 'Creating tornado application, with the 2 handlers:\n'
                               '  "/ws/" > django_websockets.handlers.AnonEchoHandler\n'
                               '  ".*" > tornado.web.FallbackHandler\n')

    @patch('django_websockets.management.commands.websockets._start_runserver_process')
    @patch('django_websockets.management.commands.websockets._start_server')
    def test_cmd_runserver(self, man_start_server, runserver):
        with CaptureStd() as std:
            call_command('websockets', '--runserver')
        self.assertTrue(man_start_server.called)
        self.assertTrue(runserver.called)
        # avoid messing with versions by only checking beginning and end
        self.assertTrue(std.captured.startswith('\ndjango-websockets version'))
        self.assertIn('"django_websockets.testsettings"\nStarting server on port 8001\n', std.captured)

        logs = self.stream.getvalue()
        self.assertEqual(logs, 'Creating tornado application, with the 1 handler:\n'
                               '  "/ws/" > django_websockets.handlers.AnonEchoHandler\n')
