(function () {
	angular.module('components')
		.directive('gdTagList', tagList);

	/** @ngInject */
	function tagList() {
		var directive = {
			templateUrl: 'components/gd-tag-list/gd-tag-list.html',
			restrict: 'E',
			scope: {
				flat: '@?',
				nameFilter: '@?',
				ngModel: '=',
				tagTemplate: '@',
				tagController: '=?'
			}
		};

		return directive;
	}
}());
