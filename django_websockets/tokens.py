from datetime import datetime
from django.utils.crypto import salted_hmac, constant_time_compare
from django.utils.http import int_to_base36, base36_to_int


class WebSocketTokenGenerator(object):
    """
    Modified copy of django/contrib/auth/tokens.py in django 1.8.2
    """
    def make_token(self, user):
        """
        Returns a token that can be used once to do a password reset
        for the given user.
        """
        return self._make_token_with_timestamp(user, self._num_seconds(self._now()))

    def check_token(self, user, token):
        """
        Check that a websocket token is correct for a given user.
        """
        # Parse the token
        try:
            ts_b36, hash = token.split('-')
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        if not constant_time_compare(self._make_token_with_timestamp(user, ts), token):
            return False

        # Check the timestamp is within limit
        if (self._num_seconds(self._now()) - ts) > settings.PASSWORD_RESET_TIMEOUT_DAYS:
            return False

        return True

    def _make_token_with_timestamp(self, user, timestamp):
        ts_b36 = int_to_base36(timestamp)

        key_salt = 'WebSocketTokenGenerator'

        # ws_auth_key_salt allows the user's ws token to be invalidated, it should return a string,
        # changing the value it returns at all will invalid the websocket token
        no_user_key_salt = lambda: ''
        custom_key_salt = getattr(user, 'ws_auth_key_salt', no_user_key_salt)()

        value = str(user.pk) + user.password + str(custom_key_salt) + str(timestamp)
        hash = salted_hmac(key_salt, value).hexdigest()[::2]
        return '%s-%s' % (ts_b36, hash)

    def _num_seconds(self, dt):
        time_diff = dt - datetime(2015, 1, 1)
        return int(time_diff.total_seconds())

    def _now(self):
        # Used for mocking in tests
        return datetime.now()
