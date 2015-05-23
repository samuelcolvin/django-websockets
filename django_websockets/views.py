from django.views.generic import TemplateView
from django.conf import settings


def get_ws_url(request):
    # always import site for reliability
    prefix = 'https://' if request.is_secure() else 'http://'
    ws_url = prefix + request.get_host() + '/ws/'
    return settings.WS_URL or ws_url


class DebugView(TemplateView):
    template_name = 'django_websockets/debug.html'

    def get_context_data(self, **kwargs):
        kwargs.update(
            title='django-websocket debug',
            ws_url=get_ws_url(self.request),
        )
        return super(DebugView, self).get_context_data(**kwargs)

debug_view = DebugView.as_view()
