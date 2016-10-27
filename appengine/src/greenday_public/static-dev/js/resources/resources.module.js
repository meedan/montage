/* global _:false, moment:false, JSData */
(function () {
	angular
		.module('app.resources', ['js-data'])
		.config(resourceConfig)
		.run(resourceRun)
		.constant('_', _)
		.constant('API_BASE_URL', window.API_BASE)
		.constant('COMPOUND_KEY_SEPARATOR', ':')
		.constant('moment', moment)
		.service('getEndpoint', getEndpoint);

	/** @ngInject */
	function resourceConfig(DSHttpAdapterProvider, $httpProvider, API_BASE_URL, _) {
		DSHttpAdapterProvider.defaults.basePath = API_BASE_URL;

		DSHttpAdapterProvider.defaults.deserialize = function (resource, data) {
			if (data.data.is_list === true && !data.data.items) {
				// We have a completely empty object,
				// we *assume* that it's an empty array
				data.data.items = [];
			}
			return data.data.items ? data.data.items : data.data;
		};

		angular.extend($httpProvider.defaults, {
			headers: {
				common: {
					'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val(),
					'Content-Type': 'application/json'
				}
			}
		});

		$httpProvider.interceptors.push(function() {
			return {
				responseError: function(response) {
					if (!(200 <= response.status && response.status < 300)) {
						// Handle errors
						if (response.data && response.data.error) {
							extractErrorCode(response.data.error);
							angular.forEach(response.data.error.errors, function (err) {
								extractErrorCode(err);
							});
						}
					}

					return response;
				}
			};
		});
	}

	/** @ngInject */
	function resourceRun(DSHttpAdapter) {
		DSHttpAdapter.getPath = function (method, resourceConfig, id, options) {
			var _this = this;
			var args;
			var DSUtils = JSData.DSUtils;
			var isString = DSUtils.isString;
			var isNumber = DSUtils.isNumber;
			var makePath = DSUtils.makePath;
			var idParts;

			options = options || {};

			args = [
				options.basePath || _this.defaults.basePath || resourceConfig.basePath,
				resourceConfig.getEndpoint((isString(id) || isNumber(id) || method === 'create') ? id : null, options)
			];

			if (method === 'find' || method === 'update' || method === 'destroy') {
				// Handle compound keys for video resource.
				// See https://github.com/js-data/js-data/issues/116
				if (isString(id) && id.indexOf(':')) {
					idParts = id.split(':');
					id = idParts[idParts.length-1];
				}

				args.push(id);
			}

			return makePath.apply(DSUtils, args);
		};
	}

	/** @ngInject */
	function getEndpoint(DS, DSUtils) {

		return function _getEndpoint(id, options) {
			options.params = options.params || {};
			var def = this;
			var definitions = DS.definitions;
			var item;
			var parentKey = def.parentKey;
			var endpoint = options.hasOwnProperty("endpoint") ? options.endpoint : def.endpoint;
			var parentField = def.parentField;
			var parentDef = definitions[def.parent];
			var parentId = options.params[parentKey];
			var parentIdParts;
			var backendParentId;

			if (parentId === false || !parentKey || !parentDef) {
				if (parentId === false) {
					delete options.params[parentKey];
				}
				return endpoint;
			} else {
				delete options.params[parentKey];

				if (DSUtils._sn(id)) {
					item = def.get(id);
				} else if (DSUtils._o(id)) {
					item = id;
				}

				if (item) {
					parentId = parentId || item[parentKey] || (item[parentField] ? item[parentField][parentDef.idAttribute] : null);
				}

				if (parentId) {
					var _ret2 = (function () {
						delete options.endpoint;
						var _options = {};
						backendParentId = parentId;

						if (DSUtils.isString(parentId)) {
							parentIdParts = parentId.split(':');
							backendParentId = parentIdParts[parentIdParts.length-1];
						}

						DSUtils.forOwn(options, function (value, key) {
							_options[key] = value;
						});

						return {
							v: DSUtils.makePath(parentDef.getEndpoint(parentId, DSUtils._(parentDef, _options)), backendParentId, endpoint)
						};
					})();

					if (typeof _ret2 === "object") return _ret2.v;
				} else {
					return endpoint;
				}
			}
		};
	}

	function extractErrorCode(obj) {
		var parts,
			propertyName = 'error_code';

		// If there is no message we have nothing to extract.
		if (!angular.isDefined(obj.message)) {
			return;
		}

		parts = obj.message.split('|');

		// Extract the error code onto it's own property
		if (angular.isDefined(obj[propertyName])) {
			throw new Error('Response object already contains property: ' +
				propertyName);
		}

		obj[propertyName] = parseInt(parts[0], 10);
		parts.splice(0, 1);

		// Remove the error code from the message. We use join on
		// the remaining message incase the "|" character was used
		// in the message itself (although that would be a
		// bit weird.)
		obj.message = parts.join('');
	}
}());
