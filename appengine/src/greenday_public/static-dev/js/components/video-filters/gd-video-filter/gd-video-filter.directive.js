(function () {
	angular.module('components')
		.directive('gdVideoFilter', videoFilter);

	/** @ngInject */
	function videoFilter() {
		var directive = {
			templateUrl: 'components/video-filters/gd-video-filter/gd-video-filter.html',
			restrict: 'E',
			scope: {
				title: '@',
				type: '@',
				isOpen: '=?',
				ngModel: '='
			},
			link: link,
			require: ['^gdVideoFilterSet', '^gdVideoFilter'],
			controller: controller,
			controllerAs: 'filterCtrl',
			transclude: true
		};

		return directive;

		function link(scope, element, attrs, controllers) {
			var filterSetCtrl = controllers[0],
				filterCtrl = controllers[1];

			filterCtrl.filterData = filterSetCtrl.filterData;

			filterCtrl.setTitle(scope.title);
		}

		function controller($scope) {
			var filterCtrl = this;

			filterCtrl.setTitle = function (newTitle) {
				if (!newTitle || angular.isString(newTitle) || !newTitle.items.length) {
					newTitle = {
						items: [],
						titleKey: 'name',
						offset: 0
					};
					filterCtrl.filterTitle = $scope.title;
				} else {
					filterCtrl.filterTitle = '';
				}
				filterCtrl.titleObj = newTitle;
			};

			filterCtrl.onClick = function() {
				$scope.isOpen = !$scope.isOpen;
			};
		}

	}
}());
