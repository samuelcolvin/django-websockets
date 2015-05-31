from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = 'wsconn.html'

    def get_context_data(self, **kwargs):
        if self.request.user.is_anonymous():
            last_user = User.objects.all().order_by('id').last()
            user = User.objects.create_user(username='user_%d' % (last_user.id + 1), password='anything')
            user = authenticate(username=user.username, password='anything')
            login(self.request, user)
            messages.info(self.request, 'Creating you as new user %s and logging you in' % self.request.user)
        kwargs.update(
            title='django-websockets',
            ws_url='auth'
        )
        return super(IndexView, self).get_context_data(**kwargs)

index = IndexView.as_view()


class AnonView(TemplateView):
    template_name = 'wsconn.html'

    def get_context_data(self, **kwargs):
        kwargs.update(
            title='django-websocket debug',
            ws_url='anon'
        )
        return super(AnonView, self).get_context_data(**kwargs)

anon_view = AnonView.as_view()
