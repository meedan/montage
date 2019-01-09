(function () {
	angular.module('components')
		.directive('bifSwitch', bifSwitch);

	/** @ngInject */
	function bifSwitch() {
		var directive = {
			templateUrl: 'components/bif-switch/bif-switch.html',
			restrict: 'E',
			replace: true,
			scope: {
				title: '@',
				text: '@'
			}
		};
		return directive;
	}
}());
