/**
 * gapiloader service
 *
 */
(function () {
	angular
		.module('app.services')
		.factory('GapiLoader', GapiLoader);

	/** @ngInject */
	function GapiLoader ($window, $document, $q) {
		var service = {
				load: load
			},
			gapiDeferred = $q.defer(),
			gapiPromise = gapiDeferred.promise,
			gapi = null;

		/* jshint ignore:start */
		$window['onGapiLoaded'] = onGapiLoaded;
		/* jshint ignore:end */

		return service;

		function onGapiLoaded() {
			gapi = $window.gapi;
			gapiDeferred.resolve(gapi);
			return gapi;
		}

		function load() {
			var s = $document[0].createElement('script');
			s.src = 'https://apis.google.com/js/client.js?onload=onGapiLoaded';
			$document[0].body.appendChild(s);
			return gapiPromise;
		}
	}
}());
