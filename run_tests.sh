#!/bin/bash

if [ "$1" != "" ]; then
    spec=$1
else
    spec="greenday_api greenday_core greenday_public greenday_channel"
fi

find . -name "*.pyc" -exec rm -rf {} \; && ./bin/manage.py test $spec --settings=greenday_core.settings.test_settings
