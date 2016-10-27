GAE Defer Manager (ALPHA)
========================

[![Build Status](https://travis-ci.org/nealedj/gae_defer_manager.svg?branch=master)](https://travis-ci.org/nealedj/gae_defer_manager)

## A library to wrap deferring tasks on the Google App Engine Taskqueue API

gae_defer_manager is a wrapper for the deferred library in the Google App Engine SDK to expose the following functionality:

* Task status
* Task ETA
* Allows prevention on duplicate tasks from being added based on an arbitrary reference key


## Setup

Include the deferred_manager folder in your project.

Add the following handlers to your app.yaml file (and any other module config files as required):

```yaml
handlers:
  - url: /_ah/queue/deferred
    script: deferred_manager.handler.application
    login: admin
    secure: always

  - url: /_ah/deferredconsole/static/
    static_dir: deferred_manager/static
    expiration: 1d

  - url: /_ah/deferredconsole.*
    script: deferred_manager.application
    login: admin
    secure: always
```

Change any calls to `google.appengine.ext.deferred.defer` to `deferred_manager.defer`

## Usage

Pass arguments to `defer()` in the same way as you would to the GAE defer function.

Optionally, you can pass the following arguments:

- **task_reference**: an arbitrary reference to allow you to identify the task
- **unique_until**: a datetime object. If passed then no other tasks with the same task_reference will be allowed to be deferred until after this datetime.

## Task console

The task console can be found at /_ah/deferredconsole/static/index.html

## Limitations

Adding deferred tasks is limited to one task per second per queue. This is because a datastore entity is saved to persist the task state. It is kept in an entity group to ensure that it returned when the task actually runs.

Screenshots
-----------

![screenshot1](/../screenshots/_screenshots/1.png?raw=true)
![screenshot1](/../screenshots/_screenshots/2.png?raw=true)
![screenshot1](/../screenshots/_screenshots/3.png?raw=true)
![screenshot1](/../screenshots/_screenshots/4.png?raw=true)
![screenshot1](/../screenshots/_screenshots/5.png?raw=true)
![screenshot1](/../screenshots/_screenshots/6.png?raw=true)
![screenshot1](/../screenshots/_screenshots/7.png?raw=true)
![screenshot1](/../screenshots/_screenshots/8.png?raw=true)
