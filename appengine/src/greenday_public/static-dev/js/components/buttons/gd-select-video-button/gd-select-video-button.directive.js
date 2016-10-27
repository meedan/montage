(function () {
	angular.module('components.buttons')
		.directive('gdSelectVideoButton', selectVideoButton);

	/** @ngInject */
	function selectVideoButton($timeout) {
		var directive = {
			templateUrl: 'components/buttons/gd-select-video-button/gd-select-video-button.html',
			restrict: 'E',
			scope: {
				selected: '='
			},
			controller: controller,
			controllerAs: 'ctrl'
		};

		return directive;

		/** @ngInject **/
		function controller($scope) {
			var ctrl = this;

			ctrl.toggleSelect = function toggleSelected() {
				$scope.selected = !$scope.selected;
				$timeout(function () {
					$scope.$emit('video:selectedChange', $scope.selected);
				});
			};
		}
	}
}());
