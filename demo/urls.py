from django.conf.urls import url, include
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    url(r'^$', 'demoapp.views.index', name='index'),
    url(r'^anon/$', 'demoapp.views.anon_view', name='anon'),
    url(r'^admin/', include(admin.site.urls)),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
