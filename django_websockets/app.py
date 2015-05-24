import logging

import tornado.wsgi
import tornado.web

from django.utils.module_loading import import_string

from . import settings

logger = logging.getLogger(settings.LOGGER_NAME)


def convert_handler_definition(uri, h_str, *args):
    """
    Just evaluate the second argument of a handler definition with import_string and return
    """
    return (uri, import_string(h_str)) + args


def describe_handler_def(handler_def):
    """
    Fairly ugly attempt to describe a tornado handler definition.
    :return: string describing handler
    """
    path = handler_def[0]
    # this is the least ugly way I can find of getting the dotted path of a class
    get_class_path = lambda c: str(c).split("'")[1]
    handler_str = get_class_path(handler_def[1])
    return '"%s" > %s' % (path, handler_str)


def get_app(serve_django):
    handlers = [convert_handler_definition(*hd) for hd in settings.WS_HANDLERS]

    if serve_django:
        django_app = import_string(settings.WSGI_APPLICATION)
        wsgi_app = tornado.wsgi.WSGIContainer(django_app)
        dj_handler = ('.*', tornado.web.FallbackHandler, {'fallback': wsgi_app})
        handlers.append(dj_handler)

    # log summary of handlers being started
    logger.info('Creating tornado application, with the following handlers:')
    for h in handlers:
        logger.info('  %s', describe_handler_def(h))
    tornado_settings = dict(
        debug=settings.DEBUG
    )
    return tornado.web.Application(handlers, **tornado_settings)
