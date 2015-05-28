import logging
import tornado.wsgi
import tornado.web
from django.utils.module_loading import import_string
from django.contrib.staticfiles.handlers import StaticFilesHandler
from . import settings

logger = logging.getLogger(settings.WS_LOGGER_NAME)


def convert_handler_definition(uri, handler, *args):
    """
    Evaluate the second argument of a handler definition with import_string if necessary, otherwise
    tuple is left unchanged.
    """
    if isinstance(handler, str):
        handler = import_string(handler)
    return (uri, handler) + args


def describe_handler(handler_def):
    """
    Fairly ugly attempt to describe a tornado handler definition.
    :return: string describing handler
    """
    path = handler_def[0]
    # this is the least ugly way I can find of getting the dotted path of a class
    get_class_path = lambda c: str(c).split("'")[1]
    handler_str = get_class_path(handler_def[1])
    return '"%s" > %s' % (path, handler_str)


def get_app(serve_django, handler_defs=settings.WS_HANDLERS, serve_static_files=settings.DEBUG):
    """
    Get tornado app suitable for serving with tornado.httpserver.HTTPServer

    :param serve_django: whether to serve django as a fallback handler at '.*'
    :param handler_defs: other handlers to serve, omit to use settings.WS_HANDLERS
    :param serve_static_files:  whether to serve static files with django's StaticFilesHandler,
        if omitted uses settings.DEBUG is used to decide.
    :return:
    """
    handlers = [convert_handler_definition(*hd) for hd in handler_defs]

    if serve_django:
        assert settings.WSGI_APPLICATION is not None, 'WSGI_APPLICATION maybe not be None or omitted'
        django_app = import_string(settings.WSGI_APPLICATION)
        if serve_static_files:
            django_app = StaticFilesHandler(django_app)
        wsgi_app = tornado.wsgi.WSGIContainer(django_app)
        dj_handler = ('.*', tornado.web.FallbackHandler, {'fallback': wsgi_app})
        handlers.append(dj_handler)

    # log summary of handlers being started
    no_handlers = len(handlers)
    s = '' if no_handlers == 1 else 's'
    logger.info('Creating tornado application, with the %d handler%s:', no_handlers, s)
    for h in handlers:
        logger.info('  %s', describe_handler(h))
    tornado_settings = dict(
        debug=settings.DEBUG
    )
    return tornado.web.Application(handlers, **tornado_settings)
