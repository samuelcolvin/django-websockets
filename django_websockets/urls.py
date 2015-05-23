from django.conf.urls import include, url
from django.contrib import admin
from .views import debug_view

urlpatterns = [
    url(r'^debug/$', debug_view, name='debug'),
]
