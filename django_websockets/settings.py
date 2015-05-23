import sys
from django.conf import settings

# dictates how long after a websocket authentication token has been generated it will expire
TOKEN_VALIDITY_SECONDS = getattr(settings, 'TOKEN_VALIDITY_SECONDS', 86400)

LOGGER_NAME = getattr(settings, 'DJWS_LOGGER_NAME', 'websockets')

# URL of websocket connection, if None it's obtained from the domain and path below
WS_URL = getattr(settings, 'WS_URL', None)

WS_URL_PATH = getattr(settings, 'WS_SUBDIRECTORY', '/ws/')

# name of the variable used to expose info to javascript about websockets
MAIN_JS_VARIABLE = getattr(settings, 'MAIN_JS_VARIABLE', 'djws')

# port websockets are being run on this is ignored if WS_URL is set, mainly used for development
# and is set automatically below for the django development server
WS_PORT = None

if WS_URL is None and settings.DEBUG and 'runserver' in sys.argv:
    # we assume websockets are being run separately on port 8001
    WS_PORT = 8001
