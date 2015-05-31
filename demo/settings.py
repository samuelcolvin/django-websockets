# to avoid duplication most settings are imported directly from testsettings.
from django_websockets.tests.settings import *

import os
BASE_DIR = os.path.dirname(__file__)

INSTALLED_APPS += ('demoapp',)

ON_HEROKU = 'DYNO' in os.environ
DEBUG = not ON_HEROKU

ROOT_URLCONF = 'urls'

WSGI_APPLICATION = 'wsgi.application'
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'

if not ON_HEROKU:
    # to allow large numbers of connections
    import resource
    resource.setrlimit(resource.RLIMIT_NOFILE, (65536, 65536))

WS_HANDLERS = (
    ('anon', 'demoapp.ws_handlers.AnonEchoHandler'),
    ('auth', 'demoapp.ws_handlers.AuthEchoHandler'),
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'djws': {
            '()': 'colorlog.ColoredFormatter',
            'format': '%(log_color)sDJWS [%(asctime)s] %(message)s',
            'datefmt': '%Y-%b-%d %H:%M:%S',
            'reset': True,
            'log_colors': {
                'DEBUG':    'cyan',
                'INFO':     'white',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'bold_red',
            },
        }
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'djws'
        },
    },
    'loggers': {
        'websockets': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}
