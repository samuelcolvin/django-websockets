"""
Modified copy of django/contrib/auth/tokens.py

The slightly weird singleton setup has been removed and the
logic has been modified to be suitable for websocket tokens.
"""
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils.crypto import salted_hmac, constant_time_compare
from django.utils.http import int_to_base36, base36_to_int
from django.contrib.auth import get_user_model
from . import settings

User = get_user_model()


def make_token(user, ip_address):
    """
    Returns a token that can be used once to do a password reset
    for the given user.
    """
    return _make_token_with_timestamp(user, ip_address, _num_seconds(datetime.now()))


def check_token_get_user(ip_address, token):
    """
    Check that a websocket token is valid for a given ip_address.

    :return: user instance
    """
    # Parse the token
    try:
        ts_b36, uid_b36, hash = token.split('-')
    except ValueError:
        return False

    try:
        ts = base36_to_int(ts_b36)
        user_id = base36_to_int(uid_b36)
    except ValueError:
        return False

    try:
        user = User.objects.get(id=user_id)
    except (ObjectDoesNotExist, MultipleObjectsReturned):
        return False

    # Check that the timestamp/token has not been tampered with
    if not constant_time_compare(_make_token_with_timestamp(user, ip_address, ts), token):
        return False

    # Check the timestamp is within limit
    if (_num_seconds(datetime.now()) - ts) > settings.TOKEN_VALIDITY_SECONDS:
        return False
    return user


def _make_token_with_timestamp(user, ip_address, timestamp):
    ts_b36 = int_to_base36(timestamp)
    uid_b36 = int_to_base36(user.id)

    key_salt = 'WebSocketTokenGenerator'

    # ws_auth_key_salt allows the user's ws token to be invalidated, it should return a string,
    # changing that string will invalidate the websocket token
    no_user_key_salt = lambda: ''
    custom_key_salt = getattr(user, 'ws_auth_key_salt', no_user_key_salt)()

    value = uid_b36 + user.password + str(ip_address) + str(custom_key_salt) + str(timestamp)
    hash = salted_hmac(key_salt, value).hexdigest()
    return '%s-%s-%s' % (ts_b36, uid_b36, hash)


def _num_seconds(dt):
    time_diff = dt - datetime(2015, 1, 1)
    return int(time_diff.total_seconds())
