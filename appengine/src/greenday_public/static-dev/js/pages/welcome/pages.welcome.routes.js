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
			.when('/welcome', {
				templateUrl: 'pages/welcome/pages.welcome.html',
				controller: 'WelcomePageCtrl',
				controllerAs: 'ctrl'
			});
	}
}());
