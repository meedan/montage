/**
 * project list routes
 */
(function () {
	angular
		.module('pages')
		.config(config);

	/** @ngInject */
	function config($routeProvider) {
		$routeProvider
			.when('/my-projects', {
				templateUrl: 'pages/projects/pages.projects.html',
				controller: 'ProjectsPageCtrl',
				controllerAs: 'ctrl',
				reloadOnSearch: false,
				resolve: {
					/** @ngInject */
					projects: function (UserService, ProjectModel) {
						return UserService.getUser().then(function () {
							return ProjectModel.findAll(null, { bypassCache: true });
						});
					}
				}
			});
	}
}());
