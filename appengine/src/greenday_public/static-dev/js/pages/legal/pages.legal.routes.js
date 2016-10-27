/**
 * legal routes
 */
(function () {
	angular
		.module('pages')
		.config(config);

	/** @ngInject */
	function config($routeProvider) {
		$routeProvider
			.when('/terms', {
				templateUrl: 'pages/legal/pages.legal.terms.html',
				controller: 'LegalCtrl',
				controllerAs: 'ctrl'
			})
			.when('/community-guidelines', {
				templateUrl: 'pages/legal/pages.legal.community-guidelines.html',
				controller: 'LegalCtrl',
				controllerAs: 'ctrl'
			});
	}
}());
