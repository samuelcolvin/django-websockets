import logging
from multiprocessing import Process
from threading import Thread

import tornado.wsgi
import tornado.web
import tornado.httpserver
import tornado.ioloop

from colorlog import ColoredFormatter

from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string
from django.db import connection
from django.core.management import call_command
from django.conf import settings

from django_websockets.handler import SocketHandler

logger = logging.getLogger('websockets')
if not logger.hasHandlers():
    formatter = ColoredFormatter(
        '%(log_color)sDJWS [%(asctime)s] %(levelname)-8s %(message)s',
        datefmt='%Y-%b-%d %H:%M:%S',
        reset=True,
        log_colors={
            'DEBUG':    'bold_black',
            'INFO':     'cyan',
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
    handlers = [('/ws/', SocketHandler)]
    if serve_django:
        django_app = import_string(settings.WSGI_APPLICATION)
        wsgi_app = tornado.wsgi.WSGIContainer(django_app)
        dj_handler = ('.*', tornado.web.FallbackHandler, {'fallback': wsgi_app})
        handlers.append(dj_handler)
    app = tornado.web.Application(handlers)
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
                default_port = 8000 if options['serve_django'] else 8001
                port = options['port'] or default_port
                main(options['serve_django'], port)
        except KeyboardInterrupt:
            print('KeyboardInterrupt')
