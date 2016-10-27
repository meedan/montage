/**
 * Filter Utils service
 *
 */
(function () {
	angular
		.module('app.services')
		.factory('FilterUtils', FilterUtils);

	/** @ngInject */
	function FilterUtils (_, moment) {

		var service = {
				objToUrl: objToUrl,
				urlToObj: urlToObj,
				generateCacheKeyFromFilters: generateCacheKeyFromFilters,
				cleanFilters: cleanFilters,
				getB64FilterUrl: getB64FilterUrl,
				getLocalQuerySyntax: getLocalQuerySyntax
			},
			rbracket = /\[\]$/,
			r20 = /%20/g;

		return service;

		function getLocalQuerySyntax(filterSet) {
			var localQuerySyntax = {},
				dateOnlyFormat = 'YYYY-MM-DD';

			angular.forEach(filterSet.filters, function (filter, filterType) {
				var key,
					operator,
					parts;

				if (filter) {
					switch (filterType) {
						case 'date':
							parts = filter.split('__');
							key = 'c_' + parts[0];
							localQuerySyntax[key] = {};

							switch (parts[1]) {
								case 'false':
									localQuerySyntax[key]['=='] = undefined;
									break;
								case 'exact':
									localQuerySyntax[key]['=='] = parts[2];
									break;
								case 'before':
									localQuerySyntax[key]['<'] = parts[2];
									break;
								case 'after':
									localQuerySyntax[key]['>'] = parts[2];
									break;
								case 'between':
									localQuerySyntax[key]['>'] = parts[2];
									localQuerySyntax[key]['<'] = parts[3];
									break;
								case 'notbetween':
									localQuerySyntax[key]['|<'] = parts[2];
									localQuerySyntax[key]['|>'] = parts[3];
									break;
							}
							break;
					}
				}
			});

			return { where: localQuerySyntax };
		}

		function getB64FilterUrl(filters) {
			return objToUrl(filters);
		}

		/**
		 * Converts an object to a url and base64 encodes it
		 * @param  {object|Array} obj The object to be converted
		 * @return {string} The converted url string
		 */
		function objToUrl(obj) {
			if (!obj) {
				return '';
			}
			return btoa(encodeURIComponent(JSON.stringify(obj)));
		}

		/**
		 * Converts a base64 encoded url string to an object
		 * @param  {string} str The string to be converted
		 * @return {object|Array} The converted object
		 */
		function urlToObj(str) {
			if (!str) {
				return {};
			}
			return JSON.parse(decodeURIComponent(atob(str)));
		}

		function generateCacheKeyFromFilters(obj) {
			var result = _.transform(obj, function (result, value, key) {
					result[key] = {key: key, value: value};
				}),
				resultArr = [];

			result = _.toArray(result);
			result = _.sortBy(result, 'key');

			angular.forEach(result, function (obj) {
				resultArr.push(obj.key + '=' + obj.value);
			});

			return resultArr.join('&');
		}

		function cleanFilters(filters) {
			var cleanedFilters = {};
			angular.forEach(filters, function (filterValue, key) {
				if (filterValue || !_.isEmpty(filterValue)) {
					cleanedFilters[key] = filterValue;
				}
			});
			return cleanedFilters;
		}
	}
}());
