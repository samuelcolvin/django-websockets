import sys
from django.conf import settings

# re-stated here for easy access in other modules using this file for settings
DEBUG = settings.DEBUG
WSGI_APPLICATION = settings.WSGI_APPLICATION

# dictates how long after a websocket authentication token has been generated it will expire
TOKEN_VALIDITY_SECONDS = getattr(settings, 'TOKEN_VALIDITY_SECONDS', 86400)

LOGGER_NAME = getattr(settings, 'DJWS_LOGGER_NAME', 'websockets')

# URL of websocket connection, if None it's obtained from the domain and path below
WS_URL = getattr(settings, 'WS_URL', None)

# TODO rename and describe
WS_URL_PATH = getattr(settings, 'WS_URL_PATH', '/ws/')

# websocket handlers to register with the tornado app. This is how you define your websocket end points
# the tuple is passed to tornado.web.Application the only change is that fall back handler is added
# if we're serving django too and the string path references are imported. Doesn't have to be websocket handlers
# TODO add warning if this hasn't been set
WS_HANDLERS = getattr(settings, 'WS_HANDLERS', (('/ws/', 'django_websockets.handlers.AnonEchoHandler'),))

# name of the variable used to expose info to javascript about websockets
MAIN_JS_VARIABLE = getattr(settings, 'MAIN_JS_VARIABLE', 'djws')

# port websockets are being run on this is ignored if WS_URL is set, mainly used for development
# and is set automatically below for the django development server
WS_PORT = None

if WS_URL is None and DEBUG and 'runserver' in sys.argv:
    # we assume websockets are being run separately on port 8001
    WS_PORT = 8001
