/**
 * welcome page routes
 */
(function () {
	angular
		.module('pages')
		.config(config);

	/** @ngInject */
	function config($routeProvider) {
		$routeProvider
			.when('/accept-nda', {
				templateUrl: 'pages/accept-nda/pages.accept-nda.html',
				controller: 'AcceptNDACtrl',
				controllerAs: 'ctrl'
			})
			.when('/accept-terms', {
				templateUrl: 'pages/accept-nda/pages.accept-nda.html',
				controller: 'AcceptNDACtrl',
				controllerAs: 'ctrl'
			});
	}
}());
