(function () {
	angular.module('components')
		.directive('stats', stats);

	/** @ngInject */
	function stats() {
		var directive = {
			templateUrl: 'components/stats/stats.html',
			restrict: 'E',
			replace: true,
			scope: {
				icon: '@',
				itemsText: '@',
				oneItemText: '@',
				noItemsText: '@',
				count: '='
			}
		};

		return directive;
	}
}());
