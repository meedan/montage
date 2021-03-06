#!/bin/bash
while ! mysqladmin ping -h"mysql" --silent; do sleep 1; done
. GREENDAY/bin/activate
echo Running database migrations...
./bin/manage.py migrate --settings=greenday_core.settings.local
echo Serving the app...
./bin/dev_appserver appengine/dispatch.yaml appengine/app.yaml appengine/long-poller.yaml appengine/worker.yaml appengine/publisher.yaml
