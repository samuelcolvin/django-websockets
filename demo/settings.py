# to avoid duplication most settings are imported directly from testsettings.
from django_websockets.testsettings import *

import os
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
