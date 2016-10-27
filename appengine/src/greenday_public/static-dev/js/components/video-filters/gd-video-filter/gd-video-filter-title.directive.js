(function () {
	angular.module('components')
		.directive('gdVideoFilterTitle', videoFilterTitle);

	/** @ngInject */
	function videoFilterTitle($filter) {
		var directive = {
			templateUrl: 'components/video-filters/gd-video-filter/gd-video-filter-title.html',
			restrict: 'E',
			scope: {
				ngModel: '='
			},
			link: link,
			controller: controller,
			controllerAs: 'titleCtrl'
		};

		return directive;

		function link(scope, element, attrs, controllers) {
			var limit = $filter('limitTo');
			scope.$watch('ngModel', function (newItems) {
				if (newItems) {
					if (scope.ngModel.offset) {
						scope.titleItems = limit(scope.ngModel.items, scope.ngModel.offset);
					} else {
						scope.titleItems = scope.ngModel.items;
					}
					scope.totalItems = scope.ngModel.items.length;
				}
			}, true);
		}

		function controller($scope) {
			var titleCtrl = this;
		}

	}
}());
