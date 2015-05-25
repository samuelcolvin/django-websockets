from django.shortcuts import render_to_response
from django.views.generic import TemplateView


def index(request):
    return render_to_response('base.html', {'title': 'index'})


class DebugView(TemplateView):
    template_name = 'debug.html'

    def get_context_data(self, **kwargs):
        kwargs.update(
            title='django-websocket debug',
        )
        return super(DebugView, self).get_context_data(**kwargs)

debug_view = DebugView.as_view()
