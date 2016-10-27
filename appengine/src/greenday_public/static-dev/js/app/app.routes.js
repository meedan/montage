/**
 * homepage routes
 */

(function () {
	angular
		.module('app')
		.config(config);

	/** @ngInject */
	function config($routeProvider) {
		$routeProvider
			.otherwise({redirectTo: '/my-projects'});
	}
}());
