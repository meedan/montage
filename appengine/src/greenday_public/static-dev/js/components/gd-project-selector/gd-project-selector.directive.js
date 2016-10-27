(function () {
	angular.module('components')
		.directive('gdProjectSelector', gdProjectSelector);

	/** @ngInject */
	function gdProjectSelector(ProjectModel, UserService) {
		var directive = {
			restrict: 'E',
			templateUrl: 'components/gd-project-selector/gd-project-selector.html',
			controller: controller,
			controllerAs: 'ctrl',
			require: 'ngModel',
			scope: {
				ngModel: '='
			}
		};

		return directive;

		function controller($scope) {
			var ctrl = this;

			ctrl.setProject = function (project) {
				$scope.ngModel = project;
			};

			UserService.getUser().then(function () {
				ProjectModel.findAll();
			});

			ProjectModel.bindAll({}, $scope, 'ctrl.projects');
		}
	}
}());
