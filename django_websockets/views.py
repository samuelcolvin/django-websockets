from django.views.generic import TemplateView
from . import settings


class DebugView(TemplateView):
    template_name = 'django_websockets/debug.html'

    def get_context_data(self, **kwargs):
        kwargs.update(
            title='django-websocket debug',
        )
        return super(DebugView, self).get_context_data(**kwargs)

debug_view = DebugView.as_view()
