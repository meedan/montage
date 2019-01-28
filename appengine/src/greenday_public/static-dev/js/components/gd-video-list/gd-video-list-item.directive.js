(function () {
	angular.module('components')
		.directive('gdVideoListItem', videoListItem);

	/** @ngInject */
	function videoListItem($timeout, ToastService) {
		var directive = {
			templateUrl: 'components/gd-video-list/gd-video-list-item.html',
			restrict: 'EA',
			controller: controller,
			controllerAs: 'ctrl',
			scope: {
				video: '='
			}
		};
		return directive;

		function controller($scope, $element, $attrs) {
			var ctrl = this;

			ctrl.sendToKeep = sendToKeep;

			function sendToKeep() {
				ctrl.isLoading = true;

				// when done:
				ctrl.isBusy = false;
				ToastService.show('“' + $scope.video.name + '” has been saved in selected Keep locations.', true);
				ToastService.closeAfter(5000);
			};

		}
	}
}());
