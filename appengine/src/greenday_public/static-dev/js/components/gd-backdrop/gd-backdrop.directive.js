(function () {
	angular.module('components.backdrop')
		.directive('gdBackdrop', backdrop);

	/** @ngInject */
	function backdrop($document) {
		var directive = {
			restrict: 'E',
			template: '<div ng-click="ctrl.callback()"></div>',
			controller: angular.noop,
			controllerAs: 'ctrl',
			bindToController: true,
			scope: {
				callback: '&'
			}
		};

		return directive;
	}
}());
