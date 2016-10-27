"""
    Defines a custom Django view handler which can read Endpoints API
    classes and serve them
"""
import json
import logging
from protorpc import protojson, message_types
from endpoints.api_config import ApiConfigGenerator
import dateutil.parser

from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from .api import greenday_api

from .dev_appserver2_endpoints import (
    api_config_manager
)

from .utils import MessageJSONEncoder


PATH_VARIABLE_PATTERN = r'([a-zA-Z_.\d]*)'


class GreendayDjangoApi(object):
    """
        Custom Django view handler to serve an Endpoints API
        using the Django request pipeline
    """
    def __init__(self):
        """
            Creates the API object.

            Reads the endpoints API config and holds a reference to
            all API methods

            Creates an `ApiConfigManager`
            used to resolve incoming requests to API methods
        """
        self.endpoints_api = greenday_api
        self.protocol = protojson.ProtoJson.get_default()
        self.dummy_path = 'greenday/v1/'
        self.config_manager = api_config_manager.ApiConfigManager()

        api_config = ApiConfigGenerator().pretty_print_config_to_json(
            self.endpoints_api.get_api_classes())

        self.config_manager.parse_api_config_response(json.dumps({
            'items': [api_config]
        }))

        self.api_methods = {}

        for api_class in self.endpoints_api.get_api_classes():
            for method_name, method in (
                    api_class.all_remote_methods().iteritems()):
                self.api_methods[
                "{0}.{1}".format(
                    api_class.__name__, method_name)] = api_class, method

    def resolve_method(self, request, path):
        """
            Returns the function to process the API request along with a
            set of parameters for it.

            request: Django request object
            path: Request path
        """
        method_name, method, params = self.config_manager.lookup_rest_method(
            self.dummy_path + path, request.method)

        return method, params

    def transform_rest_request(
            self, request, params, method_parameters, request_type):
        """
            Processes data from the path, query string and request body
            into a flat dict suitable to construct the protorpc message
            required by the API function.

            request: Django request object
            params: dict defining parameters of the API function
            method_parameters: dict defining parameters of the API function
            request_type: protorpc class that the returned dict will be used
            to construct
        """
        body_json = {}

        for key, value in params.iteritems():
            body_json[key] = [value]

        def _add_message_field(field_name, value, params):
            if '.' not in field_name:
                params[field_name] = value
                return

            root, remaining = field_name.split('.', 1)
            sub_params = params.setdefault(root, {})
            _add_message_field(remaining, value, sub_params)

        for key, value in body_json.items():
            current_parameter = method_parameters.get(key, {})
            repeated = current_parameter.get('repeated', False)

            if not repeated:
                body_json[key] = body_json[key][0]

            body_json[key] = self.convert_parameter(body_json[key], current_parameter['type'])

            message_value = body_json.pop(key)

            _add_message_field(key, message_value, body_json)

        def _update_from_dict(destination, source):
            for key, value in source.iteritems():
                destination_value = destination.get(key)
                if (isinstance(value, dict) and
                        isinstance(destination_value, dict)):
                    _update_from_dict(destination_value, value)
                elif hasattr(request_type, key):
                    field = getattr(request_type, key)

                    if isinstance(field, message_types.DateTimeField):
                        field_type = 'datetime'
                    else:
                        field_type = field.variant.name.lower()

                    destination[key] = self.convert_parameter(value, field_type)

        _update_from_dict(body_json, request.GET)

        raw_body = request.read()
        if raw_body:
            _update_from_dict(body_json, json.loads(raw_body))

        return body_json

    @staticmethod
    def convert_parameter(value, p_type):
        """
            Converts `value` to `p_type`
        """
        if p_type == 'bool':
            return value in (True, 1, 'true', '1',)

        if value is None:
            return None

        if p_type in ('int64', 'uint64'):
            return long(value)

        if p_type in ('int32', 'uint32'):
            return int(value)

        if p_type == 'float':
            return float(value)

        if p_type == 'datetime':
            return dateutil.parser.parse(value)

        return value

    def get_exception_response(self, exception):
        """
            Given an exception returns a suitable dict
            in the same structure that the cloud endpoints
            frontends return
        """
        return {
            "error": {
                "code": getattr(exception, "http_status", 500),
                "errors": [{
                    "domain": "global",
                    "message": exception.message,
                }],
                "message": exception.message
            }
        }

    @csrf_exempt
    def handler(self, request, path=None, *args, **kwargs):
        """
            Django view handler to process an API request
        """
        method_config, params = self.resolve_method(request, path)
        if not method_config:
            raise Http404

        method_params = method_config.get('request', {}).get('parameters', {})

        api_class, method = self.api_methods[method_config['rosyMethod']]

        api_service = api_class()
        api_service.request = request

        request_data = self.transform_rest_request(
            request, params, method_params, method.remote.request_type)

        request_message = method.remote.request_type(**request_data)

        try:
            response_message = method(api_service, request_message)
        except Exception as e:
            logging.exception(e)
            return HttpResponse(
                json.dumps(self.get_exception_response(e)),
                content_type='application/json',
                status=getattr(e, "http_status", 500)
            )
        else:
            response_message.check_initialized()

            response = json.dumps(response_message, cls=MessageJSONEncoder, protojson_protocol=self.protocol)
            return HttpResponse(
                response,
                content_type='application/json')


greenday_django_api = GreendayDjangoApi()
