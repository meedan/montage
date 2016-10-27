(function() {
	angular.module('components')
		.directive('gdFloatingElement', floatingElement);

	/** @ngInject */
	function floatingElement($window, floatingElementService) {

		var directive = {
			restrict: 'E',
			controller: controller,
			controllerAs: 'ctrl',
			link: link,
			scope: {},
			templateUrl: 'components/gd-floating-element/gd-floating-element.template.html',
			transclude: true
		};

		return directive;

		/** @ngInject */
		function controller($scope, $element, $attrs) {
			var ctrl = this;

			console.log('<gd-floating-element> controller', $scope);

			$scope.component = '<gd-floating-element>';
			$scope.id = $attrs.id;

			ctrl.close = function (data) {
				floatingElementService.hide($scope.id, data);
			};

			ctrl.reposition = function () {
				floatingElementService.reposition($scope.id);
			};
		}

		function link(scope, element, attrs, ctrl, transclude) {
			console.log('<gd-floating-element> link');

			/////////////////
			// DOM events
			/////////////////
			$($window).on('resize', position);

			/////////////////
			// Scope events
			/////////////////
			scope.$on('$destroy', function () {
				console.log('<gd-floating-element> $destroy');
				$($window).off('resize', position);
			});

			/////////////////
			// Private functions
			/////////////////
			function position() {
				floatingElementService.reposition(scope.id);
			}
		}
	}

})();
