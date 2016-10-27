(function () {
	angular.module('components.backdrop')
		.directive('gdBackdropRoot', backdropRoot);

	/** @ngInject */
	function backdropRoot(gdFloatingMenuService) {
		var directive = {
			restrict: 'A',
			controller: controller,
			controllerAs: 'backdropRootCtrl'
		};

		return directive;

		/** @ngInject */
		function controller($scope, $element, $attrs) {
			this.component = '<gd-backdrop-root>';
			this.element = $element;
		}
	}
}());
