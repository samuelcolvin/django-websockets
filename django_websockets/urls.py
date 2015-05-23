from django.conf.urls import url
from .views import debug_view

urlpatterns = [
    url(r'^debug/$', debug_view, name='debug'),
]
