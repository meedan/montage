(function() {
	angular.module('app.services')
		.factory('staticFileUrlService', staticFileUrlService);

	/** @ngInject */
	function staticFileUrlService(DEBUG) {
		var STATIC_ROOT_DEV = '/static-dev',
			STATIC_ROOT_PROD = '/static';

		function getFileUrl(path) {
			if (path.charAt(0) !== '/') {
				path = '/' + path;
			}

			if (DEBUG) {
				return STATIC_ROOT_DEV + path;
			} else {
				return STATIC_ROOT_PROD + path;
			}
		}

		return {
			getFileUrl: getFileUrl
		};
	}
}());
