(function () {
	angular.module('components')
		.directive('bifPopover', bifPopover);

	/** @ngInject */
	function bifPopover() {
		var directive = {
			templateUrl: 'components/bif-popover/bif-popover.html',
			restrict: 'E',
			replace: true,
			scope: {
				name: '@',
			}
		};
		return directive;
	}
}());
