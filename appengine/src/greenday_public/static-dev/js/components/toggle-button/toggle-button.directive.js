(function () {
	angular.module('components')
		.directive('toggleButton', toggleButton);

	/** @ngInject */
	function toggleButton($document) {
		var directive = {
			templateUrl: 'components/toggle-button/toggle-button.html',
			restrict: 'E',
			scope: {
				ngModel: '=',
				trueValue: '=?',
				falseValue: '=?'
			},
			controller: controller,
			controllerAs: 'ctrl',
			link: link,
			transclude: true
		};

		return directive;

		function link(scope, element, attrs) {
			if (angular.isUndefined(scope.trueValue)) {
				scope.trueValue = true;
			}

			if (angular.isUndefined(scope.falseValue)) {
				scope.falseValue = false;
			}

		}

		/** @ngInject */
		function controller($scope, $element, $attrs) {
			var ctrl = this;

			ctrl.changeValue = changeValue;
			ctrl.checked = $scope.ngModel === $scope.trueValue;

			function changeValue() {
				ctrl.checked = !ctrl.checked;
				if (ctrl.checked) {
					$scope.ngModel = $scope.trueValue;
				} else {
					$scope.ngModel = $scope.falseValue;
				}
			}
		}
	}
}());
