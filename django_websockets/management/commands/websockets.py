import os
import logging
from multiprocessing import Process
from threading import Thread
from colorlog import ColoredFormatter

import tornado
import tornado.httpserver
import tornado.ioloop

import django
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command

from django_websockets import settings
from django_websockets.app import get_app

logger = logging.getLogger(settings.LOGGER_NAME)
if not logger.hasHandlers():
    formatter = ColoredFormatter(
        '%(log_color)s[%(asctime)s] %(message)s',
        datefmt='%Y-%b-%d %H:%M:%S',
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'white',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'bold_red',
        },
    )
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.propagate = False
    logger.addHandler(handler)


def main(serve_django, port):
    if port is None:
        port = os.getenv('PORT')
    if port is None:
        port = 8000 if serve_django else 8001
    print(('\ndjango-websockets version %s\n'
           'Django version %s, Tornado version %s, using settings "%s"\n'
           'Starting server on port %d') % ('<TODO>',  # TODO
                                           django.get_version(),
                                           tornado.version,
                                           os.getenv('DJANGO_SETTINGS_MODULE', 'unknown'),
                                           port))
    app = get_app(serve_django)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(port)
    main_loop = tornado.ioloop.IOLoop.instance()
    # sched = tornado.ioloop.PeriodicCallback(schedule_func, 3000, io_loop=main_loop)
    # sched.start()
    main_loop.start()


def runserver():
    """
    Execute django's runserver command.
    """
    connection.close()
    call_command('runserver', '--noreload')


class Command(BaseCommand):
    help = 'serve websockets and optionally django with tornado'

    def add_arguments(self, parser):
        parser.add_argument('--nodjango', dest='serve_django', default=True, action='store_false',
                            help='disable serving django')
        parser.add_argument('--use-runserver', dest='runserver', default=False, action='store_true',
                            help=("Use django's runserver command to serve django and tornado to serve websockets on "
                                  "port 8001. The two servers run in separate threads. "
                                  "This overrides all other options. DO NOT USE FOR PRODUCTION"))
        parser.add_argument('--port', default=None, action='store',
                            help="port to serve on, default to 8000 unless nodjango is set in which case it's 8001")

    def handle(self, *args, **options):
        try:
            if options['runserver']:
                rs_proc = Process(target=runserver)
                rs_proc.start()
                main(False, 8001)
            else:
                main(options['serve_django'], options['port'])
        except KeyboardInterrupt:
            print('KeyboardInterrupt')
