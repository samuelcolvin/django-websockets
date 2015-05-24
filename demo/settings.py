# to avoid duplication most settings are imported directly from testsettings.
from django_websockets.testsettings import *

BASE_DIR = os.path.dirname(__file__)

INSTALLED_APPS += ('demoapp',)

ROOT_URLCONF = 'urls'

WSGI_APPLICATION = 'wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

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
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'djws'
        },
    },
    'loggers': {
        'websockets': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}