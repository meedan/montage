(function () {
	angular.module('components')
		.directive('bifSwitch', bifSwitch);

	/** @ngInject */
	function bifSwitch() {
		var directive = {
			replace: true,
			restrict: 'E',
			templateUrl: 'components/bif-switch/bif-switch.html',
			transclude: false,
			scope: {
				title: '@',
				text: '@'
			},
		};
		return directive;
	}
}());
