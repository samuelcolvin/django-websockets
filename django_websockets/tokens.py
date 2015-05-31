"""
Modified copy of django/contrib/auth/tokens.py

The slightly weird singleton setup has been removed and the
logic has been modified to be suitable for websocket tokens.
"""
import logging
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils.crypto import salted_hmac, constant_time_compare
from django.utils.http import int_to_base36, base36_to_int
from django.contrib.auth import get_user_model
from . import settings

logger = logging.getLogger(settings.WS_LOGGER_NAME)

User = get_user_model()


def make_token(user, ip_address):
    """
    Returns a token that can be used once to do a password reset
    for the given user.
    :param: use to generate token for
    :param: ip_address of user's client
    :return: new token
    """
    logger.debug('generating token for user %d, ip address: %s' % (user.id, ip_address))
    return _make_token_with_timestamp(user, ip_address, _secs_since_2015())


def check_token_get_user(token, ip_address):
    """
    Check that a websocket token is valid for a given ip_address.

    :param: token to check
    :param: ip_address of client
    :return: user instance or False if invalid token
    """
    # Parse the token
    try:
        ts_b36, uid_b36, hash = token.split('-')
    except ValueError:
        logger.debug('invalid token, value error splitting token')
        return False

    try:
        ts = base36_to_int(ts_b36)
        user_id = base36_to_int(uid_b36)
    except ValueError:
        logger.debug('invalid token, value error changing base')
        return False

    try:
        user = User.objects.get(id=user_id)
    except (ObjectDoesNotExist, MultipleObjectsReturned):
        logger.debug('invalid token, unable to get user')
        return False

    # Check that the timestamp/token has not been tampered with
    if not constant_time_compare(_make_token_with_timestamp(user, ip_address, ts), token):
        logger.debug('invalid token, token not valid')
        return False

    # Check the timestamp is within limit
    if (_secs_since_2015() - ts) > settings.TOKEN_VALIDITY_SECONDS:
        logger.debug('invalid token, token expired')
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


def _secs_since_2015():
    time_diff = _now() - datetime(2015, 1, 1)
    return int(time_diff.total_seconds())


def _now():
    """
    wrap datetime.datetime.now() to allow mocking

    :return: datetime
    """
    return datetime.now()
