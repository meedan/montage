(function () {
	angular.module('components.buttons')
		.directive('gdArchiveVideoButton', archiveVideoButton);

	/** @ngInject */
	function archiveVideoButton($timeout, VideoModel) {
		var directive = {
			templateUrl: 'components/buttons/gd-archive-video-button/gd-archive-video-button.html',
			restrict: 'E',
			scope: {
				video: '='
			},
			controller: controller,
			controllerAs: 'ctrl'
		};

		return directive;

		/** @ngInject **/
		function controller($scope) {
			var ctrl = this;

			ctrl.toggleArchived = function toggleArchived() {
				var promise = $scope.video.setArchived(!!$scope.video.archived_at);
				ctrl.isBusy = true;

				promise.then(function () {
					ctrl.isBusy = false;
				});

				return promise;
			};
		}
	}
}());
