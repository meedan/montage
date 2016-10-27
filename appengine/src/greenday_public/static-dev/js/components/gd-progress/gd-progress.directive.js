(function () {
	angular.module('components')
		.directive('gdProgress', gdProgress);

	/** @ngInject */
	function gdProgress() {
		var directive = {
			restrict: 'E',
			templateUrl: 'components/gd-progress/gd-progress.html',
		};

		return directive;
	}
}());
