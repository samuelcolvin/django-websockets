#!/usr/bin/env bash

if [ "$#" -eq 1 ]; then
  test_path="$1"
else
  test_path="django_websockets"
fi
django_admin=$(which django-admin.py)
export ASYNC_TEST_TIMEOUT="1"
export DJANGO_SETTINGS_MODULE="django_websockets.testsettings"
export PYTHONPATH=.
time coverage run --source=django_websockets $django_admin test $test_path
