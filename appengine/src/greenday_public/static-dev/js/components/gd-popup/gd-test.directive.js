(function () {
	angular.module('components.popup')
		.directive('gdTest', test);

	/** @ngInject */
	function test($log) {
		var directive = {
			restrict: 'E',
			bindToController: true,
			controller: controller,
			controllerAs: 'testCtrl',
			compile: compile,
			scope: {}
		};

		/** @ngInject */
		function controller($scope, $element, $attrs) {
			$log.debug('<gd-test>:controller');
		}

		function compile() {
			$log.debug('<gd-test>:compile');

			return function testLinkFn () {
				$log.debug('<gd-test>:link');
			};
		}

		return directive;
	}
}());
