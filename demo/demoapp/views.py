from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = 'wsconn.html'

    def get_context_data(self, **kwargs):
        if self.request.user.is_anonymous():
            last_user = User.objects.all().order_by('id').last()
            if last_user is None:
                new_id = 1
            else:
                new_id = last_user.id + 1
            user = User.objects.create_user(username='user_%d' % new_id, password='anything')
            user = authenticate(username=user.username, password='anything')
            login(self.request, user)
            messages.info(self.request, 'Creating you as new user %s and logging you in' % self.request.user)
        else:
            user = self.request.user
        kwargs.update(
            title='django-websockets authenticated users',
            ws_url='auth',
            user=user
        )
        return super(IndexView, self).get_context_data(**kwargs)

index = IndexView.as_view()


class AnonView(TemplateView):
    template_name = 'wsconn.html'

    def get_context_data(self, **kwargs):
        kwargs.update(
            title='django-websocket anonymous users',
            ws_url='anon'
        )
        return super(AnonView, self).get_context_data(**kwargs)

anon_view = AnonView.as_view()
