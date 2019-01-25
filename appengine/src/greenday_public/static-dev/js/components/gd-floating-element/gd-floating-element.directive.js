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
			/////////////////
			// DOM events
			/////////////////
			$($window).on('resize', position);

			/////////////////
			// Scope events
			/////////////////
			scope.$on('$destroy', function () {
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
