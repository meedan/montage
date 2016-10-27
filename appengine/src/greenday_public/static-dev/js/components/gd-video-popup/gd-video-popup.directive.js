(function () {
	angular.module('components')
		.directive('gdVideoPopup', gdVideoPopup);

	/** @ngInject */
	function gdVideoPopup() {
		var directive = {
			restrict: 'E',
			templateUrl: 'components/gd-video-popup/gd-video-popup.html',
			link: link,
			controller: controller,
			controllerAs: 'ctrl',
			require: ['^gdVideoPopup'],
			scope: {
				video: '='
			}
		};

		return directive;

		function link(scope, element, attrs, controllers) {
			var ctrl = controllers[0];
		}

		function controller($scope) {
			var ctrl = this;
		}
	}
}());
