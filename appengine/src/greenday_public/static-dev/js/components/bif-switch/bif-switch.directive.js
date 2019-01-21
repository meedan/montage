(function () {
	angular.module('components')
		// .controller('bifSwitchCtrl', bifSwitchCtrl)
		.directive('bifSwitch', bifSwitch);

	/** @ngInject */
	function bifSwitch() {
		var directive = {
			replace: true,
			restrict: 'E',
			templateUrl: 'components/bif-switch/bif-switch.html',
			transclude: false,
			scope: {
				title: '@',
				text: '@'
			},
			// controller: 'bifSwitchCtrl',
			link: function(scope, element, attrs) {
				// var switchName = element.find('.bif-switch__name');
				// switchName.bind('click', function() {
				// 	console.log(switchName);
				// })
				console.log(scope);
				console.log(element);
				console.log(attrs);
	    }
		};
		return directive;
	}

	// function bifSwitchCtrl($scope) {
	// 	// $scope.shields = []
	// 	$scope.isActive = false;
	//
	// 	this.switchOn = function() {
	// 		console.log("SWITCH ON");
	// 	};
	// 	this.switchOff = function() {
	// 		console.log("SWITCH OFF");
	// 	};
	// }

}());
