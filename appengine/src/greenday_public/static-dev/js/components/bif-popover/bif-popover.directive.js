(function () {
	angular.module('components')
		// .controller('bifPopoverCtrl', bifPopoverCtrl)
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
			// controller: 'bifPopoverCtrl',
			link: function(scope, element, attrs) {
				console.log(scope);
				console.log(element);
				console.log(attrs);
	    }
		};
		return directive;
	}

	// function bifPopoverCtrl($scope) {
	//
	// 	// $scope.shields = []
	// 	$scope.isActive = false;
	//
	// 	this.show = function() {
	// 		console.log("SHOW POPOVER");
	// 	};
	// 	this.hide = function() {
	// 		console.log("HIDE POPOVER");
	// 	};
	//
	// }

}());
