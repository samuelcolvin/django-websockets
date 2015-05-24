#!/usr/bin/env bash
export ASYNC_TEST_TIMEOUT="1"
django-admin.py test django_websockets --settings=django_websockets.testsettings --pythonpath=.
