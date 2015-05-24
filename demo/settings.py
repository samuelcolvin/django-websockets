import os
BASE_DIR = os.path.dirname(__file__)

SECRET_KEY = 'django-websockets'

TEMPLATE_DEBUG = DEBUG = True

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'django_websockets',
    'demoapp'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'urls'

WSGI_APPLICATION = 'wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': (
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages'
            )
        },
    },
]

STATIC_URL = '/static/'
STATICFILES_DIRS = ()
STATIC_ROOT = 'staticfiles'


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
