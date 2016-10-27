(function () {
	angular.module('components')
		.directive('gdVideoListItem', videoListItem);

	/** @ngInject */
	function videoListItem($timeout) {
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

		function controller($scope) {
			var ctrl = this;
		}
	}
}());
