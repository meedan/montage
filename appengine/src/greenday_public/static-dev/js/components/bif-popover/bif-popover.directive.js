(function () {
	angular.module('components')
		.directive('bifPopover', bifPopover);

	/** @ngInject */
	function bifPopover() {
		var directive = {
			replace: true,
			restrict: 'E',
			templateUrl: 'components/bif-popover/bif-popover.html',
			transclude: true,
			scope: {
				content: "@"
			},
			link: function(scope, el, attrs, ctrl, transclude) {
	      el.find('.bif-popover__content').append(transclude());
	    }
		};
		return directive;
	}
}());
