/* global _:false, moment:false */
(function () {
	angular
		.module('app.services', [
			'ngMaterial'
		])
		.constant('_', _)
		.constant('moment', moment)
		.constant('oAuthParams', {
			// FIX ME: these vars aren't present when the tests run
			'client_id': window.OAUTH_SETTINGS ? window.OAUTH_SETTINGS.client_id : null,
			'api_key': window.OAUTH_SETTINGS ? window.OAUTH_SETTINGS.api_key : null,
			'immediate': true,
			'scope': [
				'email',
				'profile',
				'https://www.googleapis.com/auth/youtube',
				'https://www.googleapis.com/auth/contacts.readonly'
			]
		})

		.constant('oAuthRefreshDelay', 2700 * 1000) //45 minutes (token expires in 60mins, we want to refresh 15mins earlier)
		.run([ 'HeapService', function(HeapService){
			HeapService.engage();
		}]);
}());
