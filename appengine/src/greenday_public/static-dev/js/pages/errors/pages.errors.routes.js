/**
 * Error page routes
 */
(function () {
	angular
		.module('pages')
		.config(config);

	/** @ngInject */
	function config($routeProvider) {
		$routeProvider
			.when('/500', {
				templateUrl: 'pages/errors/pages.500.html',
				controller: 'ErrorPageCtrl',
				controllerAs: 'ctrl'
			})
			.when('/403', {
				templateUrl: 'pages/errors/pages.403.html',
				controller: 'ErrorPageCtrl',
				controllerAs: 'ctrl'
			})
			.when('/404', {
				templateUrl: 'pages/errors/pages.404.html',
				controller: 'ErrorPageCtrl',
				controllerAs: 'ctrl'
			});
	}
}());
