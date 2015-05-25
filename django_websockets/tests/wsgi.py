"""
used for WSGI_APPLICATION in tests
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_websockets.testsettings')

application = get_wsgi_application()
