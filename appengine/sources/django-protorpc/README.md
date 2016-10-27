# Django ProtoRPC

[![Build Status](https://travis-ci.org/nealedj/django-protorpc.svg?branch=master)](https://travis-ci.org/nealedj/django-protorpc)

A library to construct [ProtoRPC](https://code.google.com/p/google-protorpc/) messages from Django models.

Designed to help you keep your [Google Cloud Endpoints](https://cloud.google.com/appengine/docs/python/endpoints/) APIs DRY.


## Installation

[Hosted on PyPI](https://pypi.python.org/pypi/django-protorpc). Either install with:


	$ pip install django-protorpc

Or:


	$ easy_install django-protorpc

If you prefer to use the development version of it, you can clone the repository
and build it manually:

	$ git clone https://github.com/nealedj/django-protorpc.git
	$ cd django_protorpc
	$ python setup.py install

## Usage

	from django_protorpc import DjangoProtoRPCMessage

	class MockMessageOne(DjangoProtoRPCMessage):
		class Meta:
			model = MyModel
			fields = ('foo', 'bar',)

	class MockMessageTwo(DjangoProtoRPCMessage):
		class Meta:
			model = MyModel
			exclude = ('baz',)
