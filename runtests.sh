#!/usr/bin/env bash

if [ "$#" -eq 1 ]; then
  test_path="$1"
else
  test_path="django_websockets"
fi
export ASYNC_TEST_TIMEOUT="1"
export DJANGO_SETTINGS_MODULE="django_websockets.testsettings"
export PYTHONPATH=.
django-admin.py test ${test_path}
