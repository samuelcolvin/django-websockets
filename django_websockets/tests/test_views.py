import re
from django.contrib.auth.models import User
from django.test import TestCase
from django.conf.urls import url
from django.http import HttpResponse
from django.template import Template, RequestContext


def simple_view(request):
    t = Template('{% load websockets %}{% websocket_info %}')
    c = RequestContext(request, {'request': request})
    return HttpResponse(t.render(c))


urlpatterns = [
    url(r'^simple_view/$', simple_view),
]


class ViewsTestCase(TestCase):
    def test_anon_simple_view(self):
        r = self.client.get('/simple_view/')
        self.assertEqual(r.status_code, 200)
        content = r.content.decode('utf-8')
        self.assertEqual(content, '<script>\n'
                                  '  var djws = {"token": "anon", "ws_url": "ws://testserver/ws/"};\n'
                                  '</script>\n')

    def test_auth_simple_view(self):
        User.objects.create_user('testing', email='testing@example.com', password='testing')
        self.client.login(username='testing', password='testing')
        r = self.client.get('/simple_view/')
        self.assertEqual(r.status_code, 200)
        # print(r.content)
        content = re.sub('"token": ".*?"', '"token": "xyz"', r.content.decode('utf-8'))
        self.assertEqual(content, '<script>\n'
                                  '  var djws = {"token": "xyz", "ws_url": "ws://testserver/ws/"};\n'
                                  '</script>\n')
