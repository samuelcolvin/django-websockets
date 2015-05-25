import logging
import json
import re
from django import template
from django.utils.safestring import mark_safe
from .. import settings
from ..tokens import make_token

register = template.Library()

logger = logging.getLogger(settings.LOGGER_NAME)


def get_ws_url(request):
    if settings.WS_URL:
        return settings.WS_URL
    prefix = 'wss://' if request.is_secure() else 'ws://'
    host = request.get_host()
    if settings.WS_PORT:
        host = re.sub(r':\d+$', ':' + str(settings.WS_PORT), host)
    return prefix + host + settings.WS_URL_PATH


def get_request_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@register.inclusion_tag('django_websockets/setup_script.html', takes_context=True)
def djws_setup(context, *args, **kwargs):
    if 'request' in context:
        request = context['request']
    elif 'view' in context:
        request = context['view'].request
    else:
        raise Exception('Unable to find request in context')  # TODO and solution suggestion
    # token has to be a string as it's the second argument in js Websocket method
    token = 'anon'
    if request.user.is_authenticated():
        token = make_token(request.user, get_request_ip(request))
    variables = dict(
        ws_url=get_ws_url(request),
        token=token,
    )
    setup_ctx = {
        'main_js_variable': settings.MAIN_JS_VARIABLE,
        'variables': mark_safe(json.dumps(variables))
    }
    logger.debug(setup_ctx)
    return setup_ctx
