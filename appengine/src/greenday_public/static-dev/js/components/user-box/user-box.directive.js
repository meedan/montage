(function () {
	angular.module('components')
		.directive('userBox', userBox);

	/** @ngInject */
	function userBox($document, staticFileUrlService) {
		var directive = {
			templateUrl: 'components/user-box/user-box.html',
			restrict: 'E',
			scope: {
				user: '=',
				userStats: '=',
				thumbSize: '@',
				thumbLayout: '@',
				nameLayout: '@',
				nameLayoutAlign: '@',
				iconColour: '@'
			},
			controller: controller
		};

		function controller($scope, $element, $attrs) {
			$scope.defaultProfileImgUrl = staticFileUrlService.getFileUrl('img/gplus-default.png');
		}

		return directive;
	}
}());
