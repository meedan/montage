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
			.when('/project/:projectId', {
				templateUrl: 'pages/project/pages.project.html',
				controller: 'ProjectPageCtrl',
				controllerAs: 'ctrl',
				reloadOnSearch: false,
				resolve: {
					/** @ngInject */
					project: function ($route, UserService, ProjectModel) {
						var $routeParams = $route.current.params;
						return UserService.getUser().then(function () {
							return ProjectModel.find($routeParams.projectId, { bypassCache: true });
						});
					},
					collection: function ($q) {
						return null;
					}
				}
			})
			.when('/project/:projectId/collection/:collectionId', {
				templateUrl: 'pages/project/pages.project.html',
				controller: 'ProjectPageCtrl',
				controllerAs: 'ctrl',
				reloadOnSearch: false,
				resolve: {
					/** @ngInject */
					project: function ($route, UserService, ProjectModel) {
						var $routeParams = $route.current.params;
						return UserService.getUser().then(function () {
							return ProjectModel.find($routeParams.projectId, { bypassCache: true });
						});
					},
					collection: function ($route, UserService, CollectionModel) {
						var $routeParams = $route.current.params;
						return UserService.getUser().then(function () {
							return CollectionModel
								.find($routeParams.collectionId, {
									params: {
										project_id: $routeParams.projectId
									}
								}, { bypassCache: true });
						});
					}
				}
			});
	}
}());
