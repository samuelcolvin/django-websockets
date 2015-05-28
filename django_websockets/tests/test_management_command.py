import logging
import importlib
import io
from unittest.mock import patch, call

from django.test import TestCase
from django.core.management import call_command

# we have to import this now to avoid it messing with loggers during tests
import django_websockets.tests.wsgi  # flake8: noqa
import django_websockets.management.commands.websockets
from django_websockets import settings
from .utils import CaptureStd


class ManagementCommandTestCase(TestCase):
    def setUp(self):
        super(ManagementCommandTestCase, self).setUp()
        self.logger = logging.getLogger(settings.WS_LOGGER_NAME)
        self.logger.setLevel(logging.DEBUG)
        logging.disable(logging.NOTSET)
        self.stream = io.StringIO()
        self.handler = logging.StreamHandler(self.stream)
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)
        self.logger.addHandler(self.handler)

    def tearDown(self):
        super(ManagementCommandTestCase, self).tearDown()
        self.logger.removeHandler(self.handler)
        self.handler.close()

    @patch('tornado.ioloop.IOLoop')
    def test_cmd_vanilla(self, io_loop):
        importlib.reload(django_websockets.management.commands.websockets)
        with CaptureStd() as std:
            call_command('websockets')

        # check the io loop was called correctly
        self.assertEqual(len(io_loop.mock_calls), 4)
        # first two calls are to internal methods, just check last two
        self.assertEqual(io_loop.mock_calls[2:], [call.instance(), call.instance().start()])

        # avoid messing with versions by only checking beginning and end
        self.assertTrue(std.captured.startswith('\ndjango-websockets version'))
        self.assertIn('"django_websockets.tests.settings"\nStarting server on port 8000\n', std.captured)

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
        self.assertIn('"django_websockets.tests.settings"\nStarting server on port 8001\n', std.captured)

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
        self.assertIn('"django_websockets.tests.settings"\nStarting server on port 9876\n', std.captured)

        logs = self.stream.getvalue()
        self.assertEqual(logs, 'Creating tornado application, with the 2 handlers:\n'
                               '  "/ws/" > django_websockets.handlers.AnonEchoHandler\n'
                               '  ".*" > tornado.web.FallbackHandler\n')

    @patch('logging.Logger.addHandler')
    @patch('logging.Logger.hasHandlers')
    def test_cmd_logger(self, logging_has_handler, logging_add_handler):
        """
        Test the creation of a custom logger is called and does not throw an exception
        """
        logging_has_handler.side_effect = lambda: False
        importlib.reload(django_websockets.management.commands.websockets)
        self.assertTrue(logging_has_handler.called)
        self.assertTrue(logging_add_handler.called)
